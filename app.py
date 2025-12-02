from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.wsgi import wrap_file
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import random
import string
from datetime import datetime, timedelta
import sqlite3
import hashlib
import json

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'your-secret-key-change-this'
CORS(app)

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_EMAIL = 'abc23072009@gmail.com'
SMTP_PASSWORD = 'iola wved aacq lhcb'

# Database
DB_PATH = 'student_protect.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT,
        verified BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # OTP table
    c.execute('''CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        code TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )''')
    
    # Mail logs
    c.execute('''CREATE TABLE IF NOT EXISTS mail_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT NOT NULL,
        recipient_email TEXT NOT NULL,
        subject TEXT,
        body TEXT,
        mail_type TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # SOS alerts
    c.execute('''CREATE TABLE IF NOT EXISTS sos_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        user_role TEXT NOT NULL,
        alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def send_email(recipient_email, subject, body, mail_type='info'):
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_EMAIL
        msg['To'] = recipient_email

        # HTML template
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #E0F2FE;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #0EA5E9; border-bottom: 2px solid #BFE7F8; padding-bottom: 10px;">
                        HappyEdu VN - {subject}
                    </h2>
                    <div style="margin: 20px 0; color: #333;">
                        {body.replace(chr(10), '<br>')}
                    </div>
                    <hr style="border: none; border-top: 1px solid #BFE7F8; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        Đây là thông báo tự động từ hệ thống HappyEdu VN. Vui lòng không trả lời email này.
                    </p>
                </div>
            </body>
        </html>
        """

        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True, 'Email sent successfully'
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False, str(e)

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def generate_user_id(role='student'):
    """Generate unique user ID format: HSXXXXXX or GVXXXXXX"""
    digits = ''.join(random.choices(string.digits, k=6))
    prefix = 'HS' if role == 'student' else 'GV'
    return f"{prefix}{digits}"

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Routes - Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory('.', filename)
    except Exception as e:
        print(f"Error serving {filename}: {e}")
        return {'error': 'File not found'}, 404

# API Routes
@app.route('/api/auth/login-init', methods=['POST'])
def login_init():
    """Send OTP for login"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email và mật khẩu là bắt buộc'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, password, verified FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': 'Email không tồn tại trong hệ thống'}), 404

    user_id, hashed_pwd, verified = user
    if hash_password(password) != hashed_pwd:
        return jsonify({'success': False, 'message': 'Mật khẩu không chính xác'}), 401

    if not verified:
        return jsonify({'success': False, 'message': 'Tài khoản chưa được xác thực'}), 403

    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO otp_codes (email, code, type, expires_at) VALUES (?, ?, ?, ?)',
              (email, otp_code, 'login', expires_at))
    conn.commit()
    conn.close()

    # Send OTP email
    success, msg = send_email(email, 'Mã OTP Đăng Nhập', f'Mã OTP của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.')
    
    if success:
        session['pending_login_email'] = email
        return jsonify({'success': True, 'email': email, 'message': 'Mã OTP đã được gửi'})
    else:
        return jsonify({'success': False, 'message': f'Không thể gửi OTP: {msg}'}), 500

@app.route('/api/auth/login-complete', methods=['POST'])
def login_complete():
    """Verify OTP and complete login"""
    data = request.json
    otp_code = data.get('otp_code')
    email = session.get('pending_login_email')

    if not email or not otp_code:
        return jsonify({'success': False, 'message': 'Dữ liệu không đầy đủ'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT code, expires_at FROM otp_codes WHERE email = ? AND type = ? ORDER BY created_at DESC LIMIT 1',
              (email, 'login'))
    otp_record = c.fetchone()
    conn.close()

    if not otp_record:
        return jsonify({'success': False, 'message': 'Mã OTP không tìm thấy'}), 404

    code, expires_at = otp_record
    if code != otp_code:
        return jsonify({'success': False, 'message': 'Mã OTP không chính xác'}), 401

    if datetime.fromisoformat(expires_at) < datetime.now():
        return jsonify({'success': False, 'message': 'Mã OTP đã hết hạn'}), 401

    # Get user info
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, role, name FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if user:
        user_id, role, name = user
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_role'] = role
        session['user_name'] = name
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'user_id': user_id,
            'user_name': name,
            'user_role': role,
            'user_email': email
        })
    else:
        return jsonify({'success': False, 'message': 'Người dùng không tìm thấy'}), 404

@app.route('/api/auth/register-init', methods=['POST'])
def register_init():
    """Send OTP for registration"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400

    # Check if email already exists
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Email này đã được đăng ký'}), 409

    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)

    c.execute('INSERT INTO otp_codes (email, code, type, expires_at) VALUES (?, ?, ?, ?)',
              (email, otp_code, 'register', expires_at))
    conn.commit()
    conn.close()

    # Send OTP email
    success, msg = send_email(email, 'Mã OTP Đăng Ký', f'Mã OTP của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.')
    
    if success:
        session['pending_register'] = {'email': email, 'password': password, 'name': name}
        return jsonify({'success': True, 'email': email, 'message': 'Mã OTP đã được gửi'})
    else:
        return jsonify({'success': False, 'message': f'Không thể gửi OTP: {msg}'}), 500

    return jsonify({
        'success': True,
        'message': 'Đăng ký thành công',
        'user_id': user_id,
        'user_name': pending['name'],
        'user_role': 'student',
        'user_email': email
    })


@app.route('/api/auth/finalize-register', methods=['POST'])
def finalize_register():
    """Finalize registration after OTP verification"""
    pending = session.get('pending_register')
    
    if not pending:
        return jsonify({'success': False, 'message': 'Không có dữ liệu đang chờ xử lý'}), 400

    email = pending.get('email')
    password = pending.get('password')
    name = pending.get('name')
    role = pending.get('role', 'student')

    if not all([email, password, name]):
        return jsonify({'success': False, 'message': 'Dữ liệu không đầy đủ'}), 400

    # Create user
    user_id = generate_user_id(role=role)
    hashed_password = hash_password(password)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (id, email, password, role, name, verified) VALUES (?, ?, ?, ?, ?, ?)',
                  (user_id, email, hashed_password, role, name, 1))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Email này đã được đăng ký'}), 400
    finally:
        conn.close()

    # Clear session
    session.pop('pending_register', None)

    return jsonify({
        'success': True,
        'message': 'Đăng ký thành công',
        'user_id': user_id,
        'user_name': name,
        'user_role': role,
        'user_email': email
    })

@app.route('/api/mail/send', methods=['POST'])
def send_mail():
    """Send mail to recipient"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401

    data = request.json
    recipient_email = data.get('recipient_email')
    subject = data.get('subject')
    body = data.get('body')
    mail_type = data.get('mail_type', 'info')

    if not recipient_email or not subject or not body:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400

    if len(body) < 10:
        return jsonify({'success': False, 'message': 'Nội dung phải ít nhất 10 ký tự'}), 400

    # Send email
    success, msg = send_email(recipient_email, subject, body, mail_type)

    if success:
        # Log to database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO mail_logs (sender_id, recipient_email, subject, body, mail_type) VALUES (?, ?, ?, ?, ?)',
                  (session['user_id'], recipient_email, subject, body, mail_type))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Email đã được gửi thành công'})
    else:
        return jsonify({'success': False, 'message': f'Không thể gửi email: {msg}'}), 500

@app.route('/api/sos/send', methods=['POST'])
def send_sos():
    """Send SOS alert"""
    data = request.json
    user_id = data.get('user_id')
    user_role = data.get('user_role')

    if not user_id:
        return jsonify({'success': False, 'message': 'Missing user_id'}), 400

    # Log SOS alert
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO sos_alerts (user_id, user_role) VALUES (?, ?)', (user_id, user_role))
    conn.commit()
    conn.close()

    # Send alert email to admin/teachers
    alert_message = f"""SOS ALERT!

User ID: {user_id}
Role: {user_role}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please respond immediately!
"""
    
    send_email(SMTP_EMAIL, 'URGENT: SOS Alert Received', alert_message)

    return jsonify({'success': True, 'message': 'Cảnh báo SOS đã được gửi'})

@app.route('/api/auth/teacher-login', methods=['POST'])
def teacher_login():
    """Teacher login with email, password and code"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    teacher_code = data.get('teacher_code')

    if not email or not password or not teacher_code:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400

    # Check teacher code
    TEACHER_CODE = 'abc123'
    if teacher_code != TEACHER_CODE:
        return jsonify({'success': False, 'message': 'Mã giáo viên không chính xác'}), 401

    # Check if user exists
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, password, role, name FROM users WHERE email = ? AND role = ?', (email, 'teacher'))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': 'Tài khoản giáo viên không tồn tại'}), 404

    user_id, hashed_pwd, role, name = user
    if hash_password(password) != hashed_pwd:
        return jsonify({'success': False, 'message': 'Mật khẩu không chính xác'}), 401

    # Create session for teacher
    session['user_id'] = user_id
    session['user_email'] = email
    session['user_role'] = role
    session['user_name'] = name
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'user_email': email,
        'user_role': role,
        'user_name': name,
        'message': 'Đăng nhập thành công'
    })

@app.route('/api/auth/teacher-register', methods=['POST'])
def teacher_register():
    """Teacher registration with email, password and code"""
    data = request.json
    teacher_name = data.get('teacher_name')
    email = data.get('email')
    password = data.get('password')
    teacher_code = data.get('teacher_code')

    if not teacher_name or not email or not password or not teacher_code:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400

    TEACHER_CODE = 'abc123'
    if teacher_code != TEACHER_CODE:
        return jsonify({'success': False, 'message': 'Mã giáo viên không chính xác'}), 401

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Email này đã được đăng ký'}), 400

    user_id = generate_user_id(role='teacher')
    hashed_password = hash_password(password)

    try:
        c.execute('INSERT INTO users (id, email, password, role, name, verified) VALUES (?, ?, ?, ?, ?, ?)',
                  (user_id, email, hashed_password, 'teacher', teacher_name, 1))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Email này đã được đăng ký'}), 400
    finally:
        conn.close()

    session['user_id'] = user_id
    session['user_email'] = email
    session['user_role'] = 'teacher'
    session['user_name'] = teacher_name

    return jsonify({
        'success': True,
        'message': 'Đăng ký thành công',
        'user_id': user_id,
        'user_name': teacher_name,
        'user_role': 'teacher',
        'user_email': email
    })

@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    """Get current user info"""
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user_id': session.get('user_id'),
            'email': session.get('user_email'),
            'role': session.get('user_role'),
            'name': session.get('user_name')
        })
    return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for registration"""
    data = request.json
    email = data.get('email')
    role = data.get('role', 'student')

    if not email:
        return jsonify({'success': False, 'message': 'Email là bắt buộc'}), 400

    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=10)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO otp_codes (email, code, type, expires_at) VALUES (?, ?, ?, ?)',
              (email, otp_code, 'register', expires_at))
    conn.commit()
    conn.close()

    # Send OTP email
    subject = 'Mã xác thực HappyEdu VN'
    body = f"""Mã xác thực của bạn là: {otp_code}

Mã này có hiệu lực trong 10 phút.

Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này."""

    success, msg = send_email(email, subject, body, 'otp')
    
    if success:
        return jsonify({'success': True, 'message': 'Mã OTP đã được gửi'})
    else:
        return jsonify({'success': False, 'message': f'Không thể gửi OTP: {msg}'}), 500

@app.route('/api/auth/verify-register-otp', methods=['POST'])
def verify_register_otp():
    """Verify OTP for registration"""
    data = request.json
    email = data.get('email')
    otp_code = data.get('otp_code')

    if not email or not otp_code:
        return jsonify({'success': False, 'message': 'Dữ liệu không đầy đủ'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT code, expires_at FROM otp_codes WHERE email = ? AND type = ? ORDER BY created_at DESC LIMIT 1',
              (email, 'register'))
    otp_record = c.fetchone()
    conn.close()

    if not otp_record:
        return jsonify({'success': False, 'message': 'Mã OTP không tìm thấy'}), 404

    code, expires_at = otp_record
    if code != otp_code:
        return jsonify({'success': False, 'message': 'Mã OTP không chính xác'}), 401

    if datetime.fromisoformat(expires_at) < datetime.now():
        return jsonify({'success': False, 'message': 'Mã OTP đã hết hạn'}), 401

    return jsonify({'success': True, 'message': 'OTP xác thực thành công'})


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send OTP for password reset"""
    data = request.json or {}
    email = data.get('email') or session.get('user_email')

    if not email:
        return jsonify({'success': False, 'message': 'Email là bắt buộc'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': 'Không tìm thấy tài khoản'}), 404

    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=10)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO otp_codes (email, code, type, expires_at) VALUES (?, ?, ?, ?)',
              (email, otp_code, 'forgot', expires_at))
    conn.commit()
    conn.close()

    subject = 'Mã OTP đổi mật khẩu'
    body = f"""Mã OTP đổi mật khẩu của bạn là: {otp_code}

Mã này có hiệu lực trong 10 phút.

Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này."""

    success, msg = send_email(email, subject, body, 'otp')
    if success:
        session['pending_reset_email'] = email
        return jsonify({'success': True, 'message': 'Mã OTP đã được gửi'})
    return jsonify({'success': False, 'message': f'Không thể gửi OTP: {msg}'}), 500


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    email = data.get('email') or session.get('pending_reset_email') or session.get('user_email')
    otp_code = data.get('otp_code')

    if not email or not otp_code:
        return jsonify({'success': False, 'message': 'Dữ liệu không đầy đủ'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT code, expires_at FROM otp_codes WHERE email = ? AND type = ? ORDER BY created_at DESC LIMIT 1',
              (email, 'forgot'))
    otp_record = c.fetchone()
    conn.close()

    if not otp_record:
        return jsonify({'success': False, 'message': 'Mã OTP không tìm thấy'}), 404

    code, expires_at = otp_record
    if code != otp_code:
        return jsonify({'success': False, 'message': 'Mã OTP không chính xác'}), 401

    if datetime.fromisoformat(expires_at) < datetime.now():
        return jsonify({'success': False, 'message': 'Mã OTP đã hết hạn'}), 401

    return jsonify({'success': True, 'message': 'OTP xác thực thành công'})


if __name__ == '__main__':
    init_db()
    print("Starting HappyEdu VN Server...")
    print("Listening on http://localhost:5000")
    print("Press CTRL+C to stop")
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)


