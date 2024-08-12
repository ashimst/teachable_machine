import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Gmail SMTP server configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "testproject616@gmail.com"
smtp_password = "ktuk llak xjbq tbqc"

def generate_otp(length=6):
    """
    Generates a random OTP of specified length (default: 6)
    """
    characters = string.digits
    otp = ''.join(random.choice(characters) for _ in range(length))
    return otp

def send_otp_email(recipient_email, otp):
    """
    Sends the OTP to the recipient's email address
    """
    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Your One-Time Password (OTP)"
    msg['From'] = smtp_username
    msg['To'] = recipient_email

    # Create the plain text and HTML versions of the message
    text = f"Your OTP is: {otp}"
    html = f"""\
    <html>
      <body>
        <p>Your OTP is: <strong>{otp}</strong></p>
      </body>
    </html>
    """

    # Attach the plain text and HTML versions to the message
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipient_email, msg.as_string())