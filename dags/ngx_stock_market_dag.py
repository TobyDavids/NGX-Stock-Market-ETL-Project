"""
NGX Stock Market ETL DAG

This DAG scrapes stock market data from NGX Group website,
sends the data via email, and cleans up temporary files.

Author: Chidera Ozigbo
Date: 2025
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator as DummyOperator
from config.scraping_functions import (
    scrape_ngx_data,
    send_email_with_attachment,
    cleanup_files,
)
from notifications.email_notifications import task_state_alert

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 7, 25),
    "email_on_failure": False,  
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": task_state_alert,
    "on_success_callback": task_state_alert,
}

# DAG definition
dag = DAG(
    "ngx_stock_market_etl",
    default_args=default_args,
    description="Scrape NGX stock market data and send via email",
    schedule_interval="0 17 * * 1-5",  # Runs at 5 PM  (Nigeria time), Monday to Friday
    catchup=False,
    tags=["ngx", "stock-market", "etl", "scraping"],
)

# Define tasks
start_task = DummyOperator(
    task_id="start",
    dag=dag,
)

scrape_task = PythonOperator(
    task_id="scrape_ngx_data",
    python_callable=scrape_ngx_data,
    dag=dag,
)

send_email_task = PythonOperator(
    task_id="send_email_with_attachment",
    python_callable=send_email_with_attachment,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id="cleanup_files",
    python_callable=cleanup_files,
    dag=dag,
)

end_task = DummyOperator(
    task_id="end",
    dag=dag,
)

# Define task dependencies
start_task >> scrape_task >> send_email_task >> cleanup_task >> end_task
