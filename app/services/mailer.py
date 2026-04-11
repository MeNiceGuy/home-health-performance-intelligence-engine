import smtplib
from email.message import EmailMessage
from app.core.config import MAIL_FROM, SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

def send_email(to_email: str, subject: str, body: str):
    if not SMTP_HOST:
        return {"status": "skipped", "reason": "SMTP not configured"}

    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

    return {"status": "sent"}
