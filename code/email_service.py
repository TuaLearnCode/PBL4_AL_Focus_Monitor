import smtplib
from email.mime.text import MIMEText

EMAIL = "xxx@gmail.com"
APP_PASSWORD = "xxxx xxxx xxxx xxxx"


def send_reset_email(to_email, otp):
    msg = MIMEText(f"""
Mã OTP đặt lại mật khẩu của bạn là:

    {otp}

Mã có hiệu lực trong 5 phút.
""")

    msg["Subject"] = "Reset mật khẩu"
    msg["From"] = EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)
