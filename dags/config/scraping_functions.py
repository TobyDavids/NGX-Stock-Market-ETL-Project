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
from notifications.email_notifications import send_ngx_data_email
from .logging_config import (
    get_logger,
    log_scraping_start,
    log_scraping_end,
    log_attempt,
    log_error,
    log_step,
)


def setup_directories():
    """Setup required directories for the scraping process."""
    home_dir = os.getcwd()
    log_dir = os.path.join(home_dir, "logs")
    data_dir = os.path.join(home_dir, "data")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    return home_dir, log_dir, data_dir


def handle_cookie_consent(driver, wait, logger):
    """Handle cookie consent popup if present."""
    try:
        cookie_button = wait.until(
            EC.element_to_be_clickable((By.ID, "cookie_action_close_header"))
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        log_step(logger, "Cookie consent", "Closed cookie consent popup")
        time.sleep(1)
    except Exception as e:
        log_step(logger, "Cookie consent", f"No popup found or error: {e}")


def create_chrome_driver(driver_path, logger):
    """Create Chrome WebDriver with proper configuration and error handling."""
    try:
        # Create service with explicit timeout settings
        service = Service(
            executable_path=driver_path,
            service_args=["--verbose"],
        )

        # Configure Chrome options
        options = Options()
        options.binary_location = "/opt/chrome/chrome"
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")

        log_step(logger, "WebDriver", "Creating Chrome WebDriver instance")

        # Create driver with explicit timeout handling
        driver = webdriver.Chrome(service=service, options=options)

        # Set timeouts after driver creation
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        log_step(logger, "WebDriver", "Chrome WebDriver created successfully")
        return driver

    except Exception as e:
        log_error(
            logger, f"Failed to create Chrome WebDriver: {str(e)}", retry=False
        )
        raise


def scrape_ngx_data(**context):
    """Main scraping function for NGX stock market data."""
    # Setup logger
    logger = get_logger("ngx_scraper")

    # Setup directories
    home_dir, log_dir, data_dir = setup_directories()

    # Define variables
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d")

    url = "https://ngxgroup.com/exchange/data/equities-price-list/"
    filename = os.path.join(data_dir, f"data_{time_str}.csv")

    # ChromeDriver path
    driver_dir = "/opt/chrome/bin/chromedriver"

    # Start logging
    log_scraping_start(logger)
    log_step(logger, "Setup", f"ChromeDriver path: {driver_dir}")

    # Initialize driver with improved error handling
    driver = None
    try:
        driver = create_chrome_driver(driver_dir, logger)
        wait = WebDriverWait(driver, 20)

        log_step(logger, "Navigation", f"Navigating to URL: {url}")
        driver.get(url)

    except Exception as e:
        if driver:
            driver.quit()
        log_error(
            logger, f"Failed to initialize Chrome WebDriver: {e}", retry=False
        )
        raise Exception(f"Chrome WebDriver initialization failed: {e}")

    for attempt in range(3):
        try:
            log_attempt(logger, attempt + 1, 3)
            log_step(logger, "Table loading", "Waiting for table to load")

            # Handle cookie consent first
            handle_cookie_consent(driver, wait, logger)

            # Wait for table to be present
            wait.until(
                EC.presence_of_element_located(
                    (By.ID, "latestdiclosuresEquities_wrapper")
                )
            )

            # Wait a bit for any overlays to disappear
            time.sleep(2)

            log_step(logger, "Filter", "Clicking filter button")
            filter_button = driver.find_element(
                By.CLASS_NAME, "dataTables_length"
            )
            filter_button.click()
            log_step(logger, "Filter", "Filter button clicked")
            time.sleep(1)

            log_step(logger, "Filter", "Selecting filter option for more rows")
            filter_option = driver.find_element(
                By.XPATH,
                "//*[@id='latestdiclosuresEquities_length']/label/select/option[4]",
            )
            filter_option.click()
            log_step(logger, "Filter", "Filter option selected")
            time.sleep(2)

            log_step(logger, "Data extraction", "Extracting table HTML")
            table = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "latestdiclosuresEquities")
                )
            )
            table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, "html.parser")

            # Extract table header
            log_step(logger, "Data extraction", "Extracting table header")
            table_head = soup.find("thead")
            headers = []
            if table_head:
                header_cells = table_head.find_all("th")
                headers = [cell.get_text(strip=True) for cell in header_cells]
            log_step(
                logger, "Data extraction", f"Extracted headers: {headers}"
            )

            # Extract table body
            log_step(logger, "Data extraction", "Extracting table body")
            table_body = soup.find("tbody")
            data = []
            if table_body:
                rows = table_body.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        data.append(row_data)
            log_step(
                logger,
                "Data extraction",
                f"Extracted {len(data)} rows from table body",
            )

            # Save to CSV if data is found
            if headers and data:
                log_step(
                    logger,
                    "Data processing",
                    "Creating DataFrame and saving to CSV",
                )
                df = pd.DataFrame(data, columns=headers)
                # Clean the 'Company' column to remove text in square brackets
                if "Company" in df.columns:
                    df["Company"] = (
                        df["Company"]
                        .str.replace(r"\s*\[.*?\]", "", regex=True)
                        .str.strip()
                    )
                df.to_csv(filename, index=False)
                log_step(
                    logger, "Data processing", f"Data saved to {filename}"
                )

                # Store file path in XCom for next task
                context["task_instance"].xcom_push(
                    key="csv_file_path", value=filename
                )
                context["task_instance"].xcom_push(
                    key="data_rows", value=len(data)
                )

            else:
                log_error(logger, "No data found to save", retry=False)
                raise Exception("No data extracted from the website")

            driver.quit()
            log_step(logger, "Cleanup", "Browser closed")
            log_scraping_end(logger, success=True, data_rows=len(data))
            break

        except Exception as e:
            log_error(logger, str(e), retry=(attempt < 2))
            if attempt < 2:
                log_step(logger, "Retry", "Retrying in 2 seconds")
                time.sleep(2)
                continue
            if driver:
                driver.quit()
            log_step(logger, "Cleanup", "Browser closed after error")
            log_scraping_end(logger, success=False)
            raise Exception(f"Failed to scrape data after 3 attempts: {e}")


def send_email_with_attachment(**context):
    """Send email with the scraped CSV file as attachment."""
    logger = get_logger("ngx_email")

    # Get file path from previous task
    csv_file_path = context["task_instance"].xcom_pull(
        task_ids="scrape_ngx_data", key="csv_file_path"
    )
    data_rows = context["task_instance"].xcom_pull(
        task_ids="scrape_ngx_data", key="data_rows"
    )

    if not csv_file_path or not os.path.exists(csv_file_path):
        log_error(
            logger, "CSV file not found or path not available", retry=False
        )
        raise Exception("CSV file not found or path not available")

    # Send email using the notification system
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_step(
        logger, "Email sending", f"Sending email with {data_rows} rows of data"
    )

    success = send_ngx_data_email(csv_file_path, data_rows, date_str)

    if not success:
        log_error(logger, "Failed to send email with attachment", retry=False)
        raise Exception("Failed to send email with attachment")

    log_step(
        logger,
        "Email sending",
        f"Email sent successfully with attachment: {csv_file_path}",
    )


def cleanup_files(**context):
    """Delete the CSV file after email has been sent."""
    logger = get_logger("ngx_cleanup")

    csv_file_path = context["task_instance"].xcom_pull(
        task_ids="scrape_ngx_data", key="csv_file_path"
    )

    if csv_file_path and os.path.exists(csv_file_path):
        try:
            os.remove(csv_file_path)
            log_step(
                logger,
                "File cleanup",
                f"Successfully deleted file: {csv_file_path}",
            )
        except Exception as e:
            log_error(
                logger,
                f"Could not delete file {csv_file_path}: {e}",
                retry=False,
            )
    else:
        log_step(logger, "File cleanup", "No file to delete or file not found")
