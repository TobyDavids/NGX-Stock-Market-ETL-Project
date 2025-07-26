import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from airflow.models import Variable
import os


def send_email(
    receiver, subject, body, attachment_path=None, content_type="html"
):
    """
    Generic function to send emails with optional attachments.

    Args:
        receiver (str): Email address of the recipient
        subject (str): Email subject
        body (str): Email body content
        attachment_path (str, optional): Path to file to attach
        content_type (str): Content type - "plain" or "html"

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get email configuration from Variables
        email_sender = "notifications@dataengineeringcommunity.com"
        email_password = Variable.get("email_password")
        mail_server = Variable.get("MAIL_SERVER")
        email_port = int(Variable.get("email_port"))

        # Create message
        msg = MIMEMultipart()
        msg["From"] = email_sender
        msg["To"] = receiver
        msg["Subject"] = subject

        # Attach body
        msg.attach(MIMEText(body, content_type))

        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        # Send email
        with smtplib.SMTP(mail_server, email_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)

        print(f"Email sent successfully to {receiver}")
        return True

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

