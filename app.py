from flask import Flask, request, jsonify, session, send_from_directory, send_file
from werkzeug.wsgi import wrap_file
from flask_cors import CORS
from urllib.parse import unquote
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
import mimetypes

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'your-secret-key-change-this'
CORS(app)

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_EMAIL = 'abc23072009@gmail.com'
SMTP_PASSWORD = 'iola wved aacq lhcb'

# Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'student_protect.db')
QUIZ_QUESTIONS_PATH = os.path.join(BASE_DIR, 'quiz_questions.json')

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
    
    # SOS Reports (for admin to track)
    c.execute('''CREATE TABLE IF NOT EXISTS sos_reports (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT,
        student_email TEXT,
        student_phone TEXT,
        student_class TEXT,
        location TEXT,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved BOOLEAN DEFAULT 0,
        resolved_at TIMESTAMP,
        dismissed_by_admin BOOLEAN DEFAULT 0,
        dismissed_at TIMESTAMP
    )''')
    
    # Add new columns if they don't exist (for existing databases)
    try:
        c.execute('ALTER TABLE sos_reports ADD COLUMN dismissed_by_admin BOOLEAN DEFAULT 0')
    except:
        pass
    try:
        c.execute('ALTER TABLE sos_reports ADD COLUMN dismissed_at TIMESTAMP')
    except:
        pass
    
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


@app.route('/video/<path:filename>')
def serve_video(filename):
    """Serve video files with proper headers"""
    try:
        # Decode URL-encoded filename (e.g., videoplayback%20(1).mp4 -> videoplayback (1).mp4)
        filename = unquote(filename)
        
        video_dir = os.path.join(os.getcwd(), 'video')
        file_path = os.path.join(video_dir, filename)
        
        print(f"Attempting to serve video: {file_path}")
        print(f"Filename received (decoded): {repr(filename)}")
        
        # Security check: ensure file is in video directory
        abs_file_path = os.path.abspath(file_path)
        abs_video_dir = os.path.abspath(video_dir)
        
        if not abs_file_path.startswith(abs_video_dir):
            print(f"Security: Attempted to access file outside video directory: {file_path}")
            return {'error': 'Access denied'}, 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Video file not found: {file_path}")
            # List available files for debugging
            if os.path.exists(video_dir):
                available_files = os.listdir(video_dir)
                print(f"Available files: {available_files}")
            return {'error': 'Video not found'}, 404
        
        print(f"Serving video: {file_path}")
        
        # Determine MIME type
        mime_type = 'video/mp4'
        if filename.lower().endswith('.webm'):
            mime_type = 'video/webm'
        elif filename.lower().endswith('.mp4'):
            mime_type = 'video/mp4'
        
        print(f"MIME type: {mime_type}")
        
        # Use send_file directly for better compatibility with Windows paths
        return send_file(file_path, mimetype=mime_type, as_attachment=False)
        
    except Exception as e:
        print(f"Error serving video {filename}: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}, 500


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
    """Send SOS alert with full details"""
    try:
        data = request.get_json()
        
        student_id = data.get('student_id', '').strip()
        student_name = data.get('student_name', '').strip()
        student_email = data.get('student_email', '').strip()
        student_phone = data.get('student_phone', '').strip()
        student_class = data.get('student_class', '').strip()
        location = data.get('location', 'Không xác định').strip()
        message = data.get('message', 'Báo cáo khẩn').strip()
        
        # Validate required fields with better error messages
        if not student_id:
            return jsonify({'success': False, 'error': 'Thiếu ID người dùng. Vui lòng đăng nhập lại.'}), 400
        if not student_email:
            return jsonify({'success': False, 'error': 'Thiếu email người dùng. Vui lòng đăng nhập lại.'}), 400
        
        # Reject test/dummy values
        if student_id == 'Unknown' or student_email == 'unknown@email.com':
            return jsonify({'success': False, 'error': 'Thông tin đăng nhập không hợp lệ. Vui lòng đăng nhập lại.'}), 401
        
        # Generate SOS report ID
        sos_id = f"SOS_{student_id}_{int(datetime.now().timestamp())}"
        
        # Save to database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''INSERT INTO sos_reports 
            (id, student_id, student_name, student_email, student_phone, student_class, location, message, timestamp, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (sos_id, student_id, student_name, student_email, student_phone, student_class, location, message, 
             datetime.now().isoformat(), 0))
        
        conn.commit()
        conn.close()
        
        # Try to send email to admins
        try:
            subject = f"🚨 CẢNH BÁO SOS từ {student_name}"
            body = f"""
Một báo cáo SOS mới đã được gửi!

Thông tin người gửi:
- Tên: {student_name}
- Email: {student_email}
- Điện thoại: {student_phone or 'N/A'}
- Lớp/Phòng: {student_class or 'N/A'}
- Địa chỉ: {location}

Nội dung báo cáo: {message}

Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Vui lòng truy cập vào trang admin để xem chi tiết và xử lý!
            """
            send_email(SMTP_EMAIL, subject, body, 'sos_alert')
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        return jsonify({
            'success': True, 
            'message': 'SOS report sent successfully',
            'report_id': sos_id
        }), 200
        
    except Exception as e:
        print(f"Error in send_sos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    except Exception as e:
        print(f"SOS send error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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


@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    """Login as admin with password"""
    data = request.json or {}
    password = data.get('password')
    
    # Default admin password
    ADMIN_PASSWORD = 'abc12345'
    
    if not password:
        return jsonify({'success': False, 'error': 'Vui lòng nhập mật khẩu'}), 400
    
    # Verify password
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Mật khẩu không chính xác'}), 401
    
    # Set admin session - password is correct
    session['admin_logged_in'] = True
    session['user_role'] = 'AD'
    
    return jsonify({'success': True, 'message': 'Đăng nhập quản trị viên thành công'})


@app.route('/api/sos/reports', methods=['GET'])
def get_sos_reports():
    """Get all SOS reports for admin (excluding dismissed ones)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''SELECT id, student_id, student_name, student_email, student_phone, 
                     student_class, location, message, timestamp, resolved, resolved_at,
                     COALESCE(dismissed_by_admin, 0) as dismissed_by_admin, dismissed_at
                     FROM sos_reports 
                     WHERE COALESCE(dismissed_by_admin, 0) = 0
                     ORDER BY timestamp DESC''')
        
        reports = []
        for row in c.fetchall():
            reports.append({
                'id': row[0],
                'student_id': row[1],
                'student_name': row[2],
                'student_email': row[3],
                'student_phone': row[4],
                'student_class': row[5],
                'location': row[6],
                'message': row[7],
                'timestamp': row[8],
                'resolved': bool(row[9]),
                'resolved_at': row[10],
                'dismissed_by_admin': bool(row[11]),
                'dismissed_at': row[12]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': reports
        }), 200
        
    except Exception as e:
        print(f"Get SOS reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sos/resolve/<sos_id>', methods=['POST'])
def resolve_sos(sos_id):
    """Mark SOS report as resolved"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''UPDATE sos_reports SET resolved = 1, resolved_at = ? WHERE id = ?''',
                 (datetime.now().isoformat(), sos_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'SOS report marked as resolved'
        }), 200
        
    except Exception as e:
        print(f"Resolve SOS error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sos/dismiss/<sos_id>', methods=['POST'])
def dismiss_sos(sos_id):
    """Dismiss SOS report - admin marks as dismissed (won't show in popup again)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''UPDATE sos_reports SET dismissed_by_admin = 1, dismissed_at = ? WHERE id = ?''',
                 (datetime.now().isoformat(), sos_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'SOS report dismissed'
        }), 200
        
    except Exception as e:
        print(f"Dismiss SOS error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get dashboard statistics - count of students, teachers, parents"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count users by role
        c.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        results = c.fetchall()
        
        # Extract counts
        stats = {
            'students': 0,
            'teachers': 0,
            'parents': 0,
            'total': 0
        }
        
        for role, count in results:
            if role == 'HS':
                stats['students'] = count
            elif role == 'GV':
                stats['teachers'] = count
            elif role == 'PH':
                stats['parents'] = count
            stats['total'] += count
        
        # Get SOS statistics
        c.execute("SELECT COUNT(*) as total, SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as unresolved FROM sos_reports")
        sos_data = c.fetchone()
        stats['sos_total'] = sos_data[0] or 0
        stats['sos_unresolved'] = sos_data[1] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    """Get users filtered by role - for admin accounts page"""
    try:
        role = request.args.get('role', 'HS')  # Default to students
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get users by role, ordered by creation date (newest first)
        c.execute("""
            SELECT id, name, email, created_at 
            FROM users 
            WHERE role = ? 
            ORDER BY created_at DESC
        """, (role,))
        
        rows = c.fetchall()
        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        }), 200
        
    except Exception as e:
        print(f"Error getting admin users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/list', methods=['GET'])
def get_video_list():
    """Get list of videos from video directory"""
    try:
        video_dir = os.path.join(os.getcwd(), 'video')
        
        print(f"Looking for videos in: {video_dir}")
        print(f"Directory exists: {os.path.exists(video_dir)}")
        
        # Check if video directory exists
        if not os.path.exists(video_dir):
            print("Video directory not found, creating fallback response")
            return jsonify({
                'success': True,
                'videos': [],
                'message': 'Video directory not found'
            }), 200
        
        # Get all video files (webm, mp4)
        video_extensions = ('.webm', '.mp4')
        videos = []
        
        try:
            all_files = os.listdir(video_dir)
            print(f"Files in video directory: {all_files}")
            
            for filename in sorted(all_files):
                if filename.lower().endswith(video_extensions):
                    # Use /video/ endpoint instead of relative path for Heroku compatibility
                    video_path = f'/video/{filename}'
                    videos.append(video_path)
                    print(f"Added video: {video_path}")
        except OSError as e:
            print(f"Error reading video directory: {e}")
        
        print(f"Total videos found: {len(videos)}")
        
        return jsonify({
            'success': True,
            'videos': videos,
            'count': len(videos)
        }), 200
        
    except Exception as e:
        print(f"Error getting video list: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'videos': []
        }), 500




@app.route('/api/quiz/questions/<role>', methods=['GET'])
def get_quiz_questions(role):
    """Get quiz questions for a specific user role"""
    try:
        # Role mapping: HS = học sinh, GV = giáo viên, PH = phụ huynh
        if role not in ['HS', 'GV', 'PH']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        # Read from quiz_questions.json
        with open(QUIZ_QUESTIONS_PATH, 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
        
        if role not in quiz_data:
            return jsonify({'success': False, 'error': 'No questions for this role'}), 404
        
        role_questions = quiz_data[role]
        print(f"Returning {role_questions['total_questions']} questions for role {role}")
        
        return jsonify({
            'success': True,
            'role': role,
            'total_questions': role_questions['total_questions'],
            'max_score': role_questions['max_score'],
            'categories': role_questions['categories']
        }), 200
        
    except Exception as e:
        print(f"Error loading quiz questions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    init_db()
    print("Starting HappyEdu VN Server...")
    print("Listening on http://localhost:5000")
    print("Press CTRL+C to stop")
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)


