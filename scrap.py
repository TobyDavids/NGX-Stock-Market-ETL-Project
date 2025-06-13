import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import resend
import base64

# Define base directory
home_dir = os.getcwd()

# Ensure required directories exist
log_dir = os.path.join(home_dir, "logs")
data_dir = os.path.join(home_dir, "data")
os.makedirs(data_dir, exist_ok=True)  # Create 'data' if it doesn't exist

os.makedirs(log_dir, exist_ok=True)  # Create 'log' if it doesn't exist

# Define log file path
log_file = os.path.join(log_dir, "web_scrap_log.txt")

# Time format and timestamp
time_format = "%Y-%m-%d %H:%M:%S"
now = datetime.now()
time_str = now.strftime("%Y-%m-%d")

# Define target URL and output CSV filename
url = "https://ngxgroup.com/exchange/data/equities-price-list/"
filename = os.path.join(data_dir, f"data_{time_str}.csv")

# ChromeDriver path
# driver_dir = "/Users/user/Downloads/chromedriver-mac-arm64/chromedriver"
driver_dir = "/usr/local/bin/chromedriver"

with open(log_file, "w") as f:
    f.write(f"{time_str} - Log cleared\n")


def log_message(time_str, message):
    with open(log_file, "a") as f:
        f.write(f"{time_str} - {message}\n")


def send_email(attachment_path):
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")

        with open(attachment_path, "rb") as f:
            attachment_content = f.read()
            # Encode the content in base64
            attachment_content = base64.b64encode(attachment_content).decode(
                "utf-8"
            )

        # HTML email template
        html_content = f"""
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
                        <p style="color: #7f8c8d; margin: 10px 0 0 0; font-size: 16px;">Generated on {time_str}</p>
                    </div>
                    
                    <div style="background-color: #f8f9fa; border-radius: 6px; padding: 20px; margin-bottom: 30px;">
                        <h2 style="color: #2c3e50; margin: 0 0 15px 0; font-size: 18px;">Report Summary</h2>
                        <p style="color: #34495e; margin: 0; line-height: 1.6;">
                            Please find attached the latest stock data report. This report contains the most up-to-date information from the Nigerian Stock Exchange.
                        </p>
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

        params = {
            "from": "Stocks Automation <no-reply@dataengineeringcommunity.com>",
            "to": ["chideraozigbo@gmail.com"],
            "subject": f"Stock Data Report - {time_str}",
            "html": html_content,
            "attachments": [
                {
                    "filename": os.path.basename(attachment_path),
                    "content": attachment_content,
                }
            ],
        }

        email = resend.Emails.send(params)
        log_message(time_str, f"Email sent successfully: {email}")
        return True
    except Exception as e:
        log_message(time_str, f"Error sending email: {e}")
        return False


def handle_cookie_consent(driver, wait):
    try:
        # Wait for cookie consent button and click it
        cookie_button = wait.until(
            EC.element_to_be_clickable((By.ID, "cookie_action_close_header"))
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        log_message(time_str, "Closed cookie consent popup")
        time.sleep(1)  # Wait for popup to close
    except Exception as e:
        log_message(
            time_str,
            f"No cookie consent popup found or error handling it: {e}",
        )


def scrape_data():
    service = Service(driver_dir)
    log_message(time_str, "Starting Chrome WebDriver service.")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    # Memory optimization
    options.add_argument("--disk-cache-size=1")
    options.add_argument("--media-cache-size=1")
    options.add_argument("--incognito")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--aggressive-cache-discard")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)  # Increased timeout to 20 seconds
    log_message(time_str, f"Navigating to URL: {url}")
    driver.get(url)

    for attempt in range(3):
        try:
            log_message(
                time_str, f"Attempt {attempt+1}: Waiting for table to load."
            )

            # Handle cookie consent first
            handle_cookie_consent(driver, wait)

            # Wait for table to be present
            wait.until(
                EC.presence_of_element_located(
                    (By.ID, "latestdiclosuresEquities_wrapper")
                )
            )

            # Wait a bit for any overlays to disappear
            time.sleep(2)

            log_message(time_str, "Clicking filter button.")
            filter_button = driver.find_element(
                By.CLASS_NAME, "dataTables_length"
            )
            #  click the button
            filter_button.click()
            log_message(time_str, "Filter button clicked.")
            time.sleep(1)

            log_message(time_str, "Selecting filter option for more rows.")
            filter_option = driver.find_element(
                By.XPATH,
                "//*[@id='latestdiclosuresEquities_length']/label/select/option[4]",
            )
            #  click the option
            filter_option.click()
            log_message(time_str, "Filter option selected.")
            time.sleep(2)  # Increased wait time after selection

            log_message(time_str, "Extracting table HTML.")
            table = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "latestdiclosuresEquities")
                )
            )
            table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, "html.parser")

            # Extract table header
            log_message(time_str, "Extracting table header.")
            table_head = soup.find("thead")
            headers = []
            if table_head:
                header_cells = table_head.find_all("th")
                headers = [cell.get_text(strip=True) for cell in header_cells]
            log_message(time_str, f"Extracted headers: {headers}")

            # Extract table body
            log_message(time_str, "Extracting table body.")
            table_body = soup.find("tbody")
            data = []
            if table_body:
                rows = table_body.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        data.append(row_data)
            log_message(
                time_str, f"Extracted {len(data)} rows from table body."
            )

            # Save to CSV if data is found
            if headers and data:
                log_message(time_str, "Creating DataFrame and saving to CSV.")
                df = pd.DataFrame(data, columns=headers)
                # Clean the 'Company' column to remove text in square brackets
                if "Company" in df.columns:
                    df["Company"] = (
                        df["Company"]
                        .str.replace(r"\s*\[.*?\]", "", regex=True)
                        .str.strip()
                    )
                df.to_csv(filename, index=False)
                log_message(time_str, f"Data saved to {filename}")

                # # Send email with the CSV file
                # log_message(time_str, "Sending email with CSV attachment.")
                # if send_email(filename):
                #     log_message(time_str, "Email sent successfully")
                # else:
                #     log_message(time_str, "Failed to send email")
            else:
                log_message(time_str, "No data found to save.")
            driver.quit()
            log_message(time_str, "Browser closed. Scraping complete.")
            break
        except Exception as e:
            log_message(time_str, f"Error: {e}")
            if attempt < 2:
                log_message(time_str, "Retrying")
                time.sleep(2)  # Increased wait time between retries
                continue
            driver.quit()
            log_message(time_str, "Browser closed after error.")


if __name__ == "__main__":
    scrape_data()
