"""
Email notifications for NGX Stock Market ETL DAG

This module contains email notification functions for task alerts and general email sending.
"""

import os
from config.email_config import send_email


def notification_email(context, state):
    """
    This function sends notification of a failed DAG task
    """
    task_instance = context.get("task_instance")
    dag = task_instance.dag_id
    task = task_instance.task_id
    exec_date = task_instance.start_date
    log = task_instance.log_url

    # Get the DAG object
    dag_obj = context.get("dag") or task_instance.dag

    # Get owner from DAG's default_args
    dag_owner = "Airflow User"
    if hasattr(dag_obj, "default_args") and "owner" in dag_obj.default_args:
        dag_owner = dag_obj.default_args["owner"]

    # Get email from DAG's default_args
    email_receiver = None
    if hasattr(dag_obj, "default_args") and "email" in dag_obj.default_args:
        email_receiver = dag_obj.default_args["email"]

    # If no email is found, use a default from Variables
    if not email_receiver:
        email_receiver = "chideraozigbo@gmail.com"

    if isinstance(email_receiver, list):
        email_receiver = ", ".join(email_receiver)

    subject = f"Airflow Alert: Task in DAG '{dag}' has {state.upper()}"
    body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>Airflow Task Notification</title>
        </head>
        <body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #2c3e50; margin: 0; font-size: 24px;">Airflow Task Notification</h1>
                        <p style="color: #7f8c8d; margin: 10px 0 0 0; font-size: 16px;">DAG: <strong>{dag}</strong></p>
                    </div>
                    <div style="background-color: #f8f9fa; border-radius: 6px; padding: 20px; margin-bottom: 30px;">
                        <h2 style="color: #2c3e50; margin: 0 0 15px 0; font-size: 18px;">Task Details</h2>
                        <p style="color: #34495e; margin: 0; line-height: 1.6;">
                            <strong>Task:</strong> {task}<br>
                            <strong>State:</strong> <span style='color: {'#e74c3c' if state.lower() == 'failed' else '#27ae60'}; font-weight: bold;'>{state.upper()}</span><br>
                            <strong>Run Date:</strong> {exec_date}<br>
                            <strong>Owner:</strong> {dag_owner}
                        </p>
                    </div>
                    <div style="background-color: #e8f4f8; border-radius: 6px; padding: 20px; margin-bottom: 30px;">
                        <h2 style="color: #2c3e50; margin: 0 0 15px 0; font-size: 18px;">Log URL</h2>
                        <p style="color: #34495e; margin: 0; line-height: 1.6;">
                            <a href='{log}' style='color: #2980b9; text-decoration: underline;'>{log}</a>
                        </p>
                    </div>
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="color: #7f8c8d; margin: 0; font-size: 14px;">
                            This is an automated notification from your Airflow server.<br>
                            Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    return send_email(email_receiver, subject, body, content_type="html")


def task_state_alert(context):
    """
    This function sends notification of a DAG task based on its state
    """
    task_instance = context.get("task_instance")
    if task_instance:
        state = task_instance.state
        if state in ("success", "failed"):
            notification_email(context, state)


def send_ngx_data_email(csv_file_path, data_rows, date_str):
    """
    Send NGX stock market data email with attachment.

    Args:
        csv_file_path (str): Path to the CSV file
        data_rows (int): Number of rows in the data
        date_str (str): Date string for the report

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get receiver email from Variables
        receiver_email = "chideraozigbo@gmail.com"

        subject = f"NGX Stock Market Data - {date_str}"

        # HTML body template
        body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Data Report</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2c3e50; margin: 0; font-size: 24px;">Stock Data Report</h1>
                <p style="color: #7f8c8d; margin: 10px 0 0 0; font-size: 16px;">Generated on {date_str}</p>
            </div>
            
            <div style="background-color: #f8f9fa; border-radius: 6px; padding: 20px; margin-bottom: 30px;">
                <h2 style="color: #2c3e50; margin: 0 0 15px 0; font-size: 18px;">Report Summary</h2>
                <p style="color: #34495e; margin: 0; line-height: 1.6;">
                    Please find attached the latest stock data report. This report contains the most up-to-date information from the Nigerian Stock Exchange.
                </p>
                <div style="margin-top: 15px; padding: 15px; background-color: #ffffff; border-radius: 4px; border-left: 4px solid #3498db;">
                    <p style="color: #34495e; margin: 0; font-size: 14px;">
                        <strong>Data Summary:</strong><br>
                        • Date: {date_str}<br>
                        • Total rows extracted: {data_rows}<br>
                        • File: {os.path.basename(csv_file_path)}
                    </p>
                </div>
            </div>

            <div style="background-color: #e8f4f8; border-radius: 6px; padding: 20px; margin-bottom: 30px;">
                <h2 style="color: #2c3e50; margin: 0 0 15px 0; font-size: 18px;">Attachment</h2>
                <p style="color: #34495e; margin: 0; line-height: 1.6;">
                    The report is attached to this email in CSV format. You can open it with any spreadsheet application.
                </p>
            </div>

            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="color: #7f8c8d; margin: 0; font-size: 14px;">
                    This is an automated report. Please do not reply to this email.
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        return send_email(
            receiver_email, subject, body, csv_file_path, content_type="html"
        )

    except Exception as e:
        print(f"Failed to send NGX data email: {str(e)}")
        return False
