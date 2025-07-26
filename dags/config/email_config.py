import os
from airflow.sdk import Variable
import resend


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
        resend_api_key = Variable.get("RESEND_API_KEY")
        resend.api_key = resend_api_key

        # Prepare parameters for Resend
        params: resend.Emails.SendParams = {
            "from": email_sender,
            "to": [receiver] if isinstance(receiver, str) else receiver,
            "subject": subject,
            "html" if content_type == "html" else "text": body,
        }

        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                file_data = attachment.read()
                import base64

                encoded_content = base64.b64encode(file_data).decode("utf-8")
                params["attachments"] = [
                    {
                        "filename": os.path.basename(attachment_path),
                        "content": encoded_content,
                    }
                ]

        # Send email using Resend
        email = resend.Emails.send(params)
        if getattr(email, "id", None):
            print(f"Email sent successfully to {receiver}")
            return True
        else:
            print(f"Failed to send email: {email}")
            return False

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False
