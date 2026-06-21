import os
import smtplib

from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email(to_email, subject, html_body):

    try:

        msg = MIMEMultipart()

        msg["From"] = GMAIL_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(
            MIMEText(html_body, "html")
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            GMAIL_EMAIL,
            GMAIL_APP_PASSWORD
        )

        server.send_message(msg)

        server.quit()

        return True

    except Exception as e:

        print(f"Email Error: {e}")

        return False