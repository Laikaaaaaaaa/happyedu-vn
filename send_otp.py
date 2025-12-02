import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Gmail credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "abc23072009@gmail.com"
SMTP_PASSWORD = "iola wved aacq lhcb"

# Store OTPs temporarily (in production, use Redis or database)
otp_storage = {}

def generate_otp(length=6):
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email, otp_code):
    """Send OTP to email address"""
    try:
        # Create email message
        message = MIMEMultipart()
        message['From'] = SMTP_EMAIL
        message['To'] = to_email
        message['Subject'] = 'Mã xác thực HappyEdu VN'

        # Email body
        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f0f9ff;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <h2 style="color: #1F2937; margin-bottom: 20px;">Xác thực Email - HappyEdu VN</h2>
                    
                    <p style="color: #6B7280; font-size: 16px; margin-bottom: 20px;">
                        Bạn đã yêu cầu đăng ký tài khoản hoặc đặt lại mật khẩu. 
                        Vui lòng sử dụng mã xác thực dưới đây:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="font-size: 32px; font-weight: bold; color: #2563EB; letter-spacing: 5px; background-color: #EFF6FF; padding: 20px; border-radius: 8px; margin: 0;">
                            {otp_code}
                        </p>
                    </div>
                    
                    <p style="color: #6B7280; font-size: 14px; margin: 20px 0;">
                        Mã này có hiệu lực trong <strong>10 phút</strong>.
                    </p>
                    
                    <p style="color: #6B7280; font-size: 14px; margin: 20px 0;">
                        Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 20px 0;">
                    
                    <p style="color: #9CA3AF; font-size: 12px; text-align: center;">
                        © 2025 HappyEdu VN. Tất cả quyền được bảo lưu.
                    </p>
                </div>
            </body>
        </html>
        """

        message.attach(MIMEText(email_body, 'html'))

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(message)

        # Store OTP with expiration time (10 minutes)
        otp_storage[to_email] = {
            'otp': otp_code,
            'expires': datetime.now() + timedelta(minutes=10)
        }

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_otp(email, otp_code):
    """Verify OTP for email"""
    if email not in otp_storage:
        return False, "OTP không tồn tại"
    
    stored = otp_storage[email]
    
    # Check expiration
    if datetime.now() > stored['expires']:
        del otp_storage[email]
        return False, "Mã OTP đã hết hạn"
    
    # Check OTP code
    if stored['otp'] != otp_code:
        return False, "Mã OTP không chính xác"
    
    # Remove OTP after successful verification
    del otp_storage[email]
    return True, "Xác thực thành công"

if __name__ == "__main__":
    # Test
    test_email = "abc23072009@gmail.com"
    otp = generate_otp()
    print(f"Generated OTP: {otp}")
    
    if send_otp_email(test_email, otp):
        print(f"OTP sent to {test_email}")
    else:
        print("Failed to send OTP")
