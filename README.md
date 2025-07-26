# NGX Stock Market ETL DAG

This Airflow DAG scrapes stock market data from the NGX Group website, sends the data via email, and cleans up temporary files.

## DAG Structure

```
start >> scrape_ngx_data >> send_email_with_attachment >> cleanup_files >> end
```

## Tasks

1. **scrape_ngx_data**: Scrapes stock market data from NGX Group website and saves to CSV
2. **send_email_with_attachment**: Sends the CSV file via email using the notification system
3. **cleanup_files**: Deletes the temporary CSV file after email is sent

## Notifications

The DAG includes comprehensive email notifications:
- **Task Success/Failure Alerts**: Automatic notifications when tasks succeed or fail
- **Data Reports**: Beautiful HTML emails with attached CSV files
- **Centralized Email System**: All email functionality uses a single, reusable system

## Configuration

### Airflow Variables Setup

The DAG uses Airflow Variables for secure configuration. Set these in the Airflow UI (Admin > Variables):

**Required Variables:**
- `email_sender`: Your email address
- `email_password`: Your email password or app password  
- `ngx_data_receiver_email`: Email to receive NGX data reports

**Optional Variables (have defaults):**
- `MAIL_SERVER`: SMTP server (default: smtp.gmail.com)
- `email_port`: SMTP port (default: 587)
- `default_alert_email`: Alert email (default: chideraozigbo@gmail.com)

For Gmail users:
- Use an App Password instead of your regular password
- Enable 2-factor authentication
- Generate an App Password in Google Account settings

### ChromeDriver Configuration

Update the ChromeDriver path in `dags/config/scraping_functions.py`:

```python
driver_dir = "/path/to/your/chromedriver"
```

## Setup Instructions

1. **Install Dependencies**: Make sure all required packages are installed in your Airflow environment:
   ```bash
   pip install selenium beautifulsoup4 pandas requests
   ```

2. **Install ChromeDriver**: Download and install ChromeDriver for your system
   - Download from: https://chromedriver.chromium.org/
   - Update the path in the scraping functions

3. **Configure Email**: Update the email configuration in `dags/config/email_config.py`

4. **Deploy DAG**: Place the DAG files in your Airflow `dags` folder

## Schedule

The DAG is scheduled to run at 9 AM on weekdays (Monday-Friday):
```python
schedule_interval='0 9 * * 1-5'
```

## File Structure

```
dags/
├── ngx_stock_market_dag.py          # Main DAG file
├── config/
│   ├── __init__.py                  # Package init
│   ├── scraping_functions.py        # Core scraping functions
│   ├── email_config.py              # Email configuration utilities
│   └── logging_config.py            # Logging configuration
├── notifications/
│   ├── __init__.py                  # Package init
│   └── email_notifications.py       # Email notification functions
└── README.md                        # This file
```

## Data Flow

1. **Scraping**: The DAG scrapes data from https://ngxgroup.com/exchange/data/equities-price-list/
2. **Processing**: Data is cleaned and saved as a CSV file
3. **Email**: The CSV file is attached to an email and sent
4. **Cleanup**: The temporary CSV file is deleted

## Error Handling

- The scraping task retries up to 3 times if it fails
- Email failures are logged and the DAG will fail
- File cleanup continues even if email fails

## Monitoring

- Check Airflow UI for task status and logs
- **Structured Logging**: All operations are logged using Python's built-in logging package
- **Daily Log Files**: Logs are written to `logs/ngx_scraper_YYYY-MM-DD.log`
- **Console Output**: Real-time logging to console during execution
- **Log Levels**: INFO, WARNING, ERROR with proper formatting
- Data files are temporarily stored in `data/` directory

### Log Format
```
2024-01-15 10:30:15 - ngx_scraper - INFO - ============================================================
2024-01-15 10:30:15 - ngx_scraper - INFO - Starting NGX Stock Market Data Scraping Process
2024-01-15 10:30:15 - ngx_scraper - INFO - Setup: ChromeDriver path: /usr/local/bin/chromedriver
2024-01-15 10:30:16 - ngx_scraper - INFO - Chrome WebDriver: Starting service
2024-01-15 10:30:17 - ngx_scraper - INFO - Navigation: Navigating to URL: https://ngxgroup.com/...
2024-01-15 10:30:18 - ngx_scraper - INFO - Attempt 1/3: Processing...
2024-01-15 10:30:19 - ngx_scraper - INFO - Table loading: Waiting for table to load
2024-01-15 10:30:20 - ngx_scraper - INFO - Cookie consent: Closed cookie consent popup
2024-01-15 10:30:25 - ngx_scraper - INFO - Filter: Clicking filter button
2024-01-15 10:30:26 - ngx_scraper - INFO - Data extraction: Extracting table HTML
2024-01-15 10:30:27 - ngx_scraper - INFO - Data extraction: Extracted 150 rows from table body
2024-01-15 10:30:28 - ngx_scraper - INFO - Data processing: Data saved to /path/to/data_2024-01-15.csv
2024-01-15 10:30:28 - ngx_scraper - INFO - Cleanup: Browser closed
2024-01-15 10:30:28 - ngx_scraper - INFO - Scraping completed successfully. Extracted 150 rows of data.
2024-01-15 10:30:28 - ngx_scraper - INFO - ============================================================
```

## Security Notes

- Store email credentials securely (consider using Airflow Variables or environment variables)
- ChromeDriver should be properly secured and updated regularly
- Consider using a dedicated service account for email sending 