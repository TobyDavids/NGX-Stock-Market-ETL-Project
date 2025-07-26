import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from notifications.email_notifications import send_ngx_data_email


def setup_directories():
    """Setup required directories for the scraping process."""
    home_dir = os.getcwd()
    log_dir = os.path.join(home_dir, "logs")
    data_dir = os.path.join(home_dir, "data")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    return home_dir, log_dir, data_dir


def handle_cookie_consent(driver, wait):
    """Handle cookie consent popup if present."""
    try:
        cookie_button = wait.until(
            EC.element_to_be_clickable((By.ID, "cookie_action_close_header"))
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        print("Cookie consent: Closed cookie consent popup")
        time.sleep(1)
    except Exception as e:
        print(f"Cookie consent: No popup found or error: {e}")


def scrape_ngx_data(**context):
    """Main scraping function for NGX stock market data."""
    # Setup directories
    home_dir, log_dir, data_dir = setup_directories()

    # Define variables
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d")

    url = "https://ngxgroup.com/exchange/data/equities-price-list/"
    filename = os.path.join(data_dir, f"data_{time_str}.csv")

    # Start logging
    print("=" * 60)
    print("Starting NGX Stock Market Data Scraping Process")

    # Initialize driver with improved error handling
    driver = None
    try:
        options = Options()
        
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--window-size=1920,1080")

        print("WebDriver: Creating Remote Chrome WebDriver instance")

        # Use environment variable or default to selenium container
        selenium_url = "http://selenium:4444/wd/hub"
        print(f"WebDriver: Using Selenium URL: {selenium_url}")

        # Test connection to selenium server first
        try:
            import requests

            response = requests.get(f"{selenium_url}/status", timeout=10)
            if response.status_code == 200:
                print("WebDriver: Selenium server is ready")
            else:
                print(
                    f"WebDriver: Selenium server responded with status {response.status_code}"
                )
        except Exception as conn_error:
            print(
                f"WebDriver: Warning - Could not connect to selenium server: {conn_error}"
            )

        # Create WebDriver with explicit timeout settings
        driver = webdriver.Remote(
            command_executor=selenium_url, options=options
        )

        # Set page load timeout
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        wait = WebDriverWait(driver, 20)

        print(f"Navigation: Navigating to URL: {url}")
        driver.get(url)

    except Exception as e:
        if driver:
            driver.quit()
        print(f"Failed to initialize Chrome WebDriver: {e}")
        print(f"WebDriver error details: {type(e).__name__}: {str(e)}")
        raise Exception(f"Chrome WebDriver initialization failed: {e}")

    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}/3: Processing")
            print("Table loading: Waiting for table to load")

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

            print("Filter: Clicking filter button")
            filter_button = driver.find_element(
                By.CLASS_NAME, "dataTables_length"
            )
            filter_button.click()
            print("Filter: Filter button clicked")
            time.sleep(1)

            print("Filter: Selecting filter option for more rows")
            filter_option = driver.find_element(
                By.XPATH,
                "//*[@id='latestdiclosuresEquities_length']/label/select/option[4]",
            )
            filter_option.click()
            print("Filter: Filter option selected")
            time.sleep(2)

            print("Data extraction: Extracting table HTML")
            table = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "latestdiclosuresEquities")
                )
            )
            table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, "html.parser")

            # Extract table header
            print("Data extraction: Extracting table header")
            table_head = soup.find("thead")
            headers = []
            if table_head:
                header_cells = table_head.find_all("th")
                headers = [cell.get_text(strip=True) for cell in header_cells]
            print(f"Data extraction: Extracted headers: {headers}")

            # Extract table body
            print("Data extraction: Extracting table body")
            table_body = soup.find("tbody")
            data = []
            if table_body:
                rows = table_body.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        data.append(row_data)
            print(
                f"Data extraction: Extracted {len(data)} rows from table body"
            )

            # Save to CSV if data is found
            if headers and data:
                print("Data processing: Creating DataFrame and saving to CSV")
                df = pd.DataFrame(data, columns=headers)
                # Clean the 'Company' column to remove text in square brackets
                if "Company" in df.columns:
                    df["Company"] = (
                        df["Company"]
                        .str.replace(r"\s*\[.*?\]", "", regex=True)
                        .str.strip()
                    )
                df.to_csv(filename, index=False)
                print(f"Data processing: Data saved to {filename}")

                # Store file path in XCom for next task
                context["task_instance"].xcom_push(
                    key="csv_file_path", value=filename
                )
                context["task_instance"].xcom_push(
                    key="data_rows", value=len(data)
                )

            else:
                print("No data found to save")
                raise Exception("No data extracted from the website")

            driver.quit()
            print("Cleanup: Browser closed")
            print(
                f"Scraping completed successfully. Extracted {len(data)} rows of data."
            )
            print("=" * 60)
            break

        except Exception as e:
            print(f"Error occurred: {str(e)} - Will retry")
            if attempt < 2:
                print("Retry: Retrying in 2 seconds")
                time.sleep(2)
                continue
            if driver:
                driver.quit()
            print("Cleanup: Browser closed after error")
            print("Scraping failed.")
            print("=" * 60)
            raise Exception(f"Failed to scrape data after 3 attempts: {e}")


def send_email_with_attachment(**context):
    """Send email with the scraped CSV file as attachment."""
    # Get file path from previous task
    csv_file_path = context["task_instance"].xcom_pull(
        task_ids="scrape_ngx_data", key="csv_file_path"
    )
    data_rows = context["task_instance"].xcom_pull(
        task_ids="scrape_ngx_data", key="data_rows"
    )

    if not csv_file_path or not os.path.exists(csv_file_path):
        print("CSV file not found or path not available")
        raise Exception("CSV file not found or path not available")

    # Send email using the notification system
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Email sending: Sending email with {data_rows} rows of data")

    success = send_ngx_data_email(csv_file_path, data_rows, date_str)

    if not success:
        print("Failed to send email with attachment")
        raise Exception("Failed to send email with attachment")

    print(
        f"Email sending: Email sent successfully with attachment: {csv_file_path}"
    )


def cleanup_files(**context):
    """Delete the CSV file after email has been sent."""
    csv_file_path = context["task_instance"].xcom_pull(
        task_ids="scrape_ngx_data", key="csv_file_path"
    )

    if csv_file_path and os.path.exists(csv_file_path):
        try:
            os.remove(csv_file_path)
            print(f"File cleanup: Successfully deleted file: {csv_file_path}")
        except Exception as e:
            print(f"Could not delete file {csv_file_path}: {e}")
    else:
        print("File cleanup: No file to delete or file not found")
