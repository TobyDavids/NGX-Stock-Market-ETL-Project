"""
Logging configuration for NGX Stock Market ETL DAG

This module provides a centralized logging configuration using Python's built-in logging package.
"""

import logging
import os
from datetime import datetime


def setup_logger(name="ngx_scraper", log_level=logging.INFO):
    """
    Setup and configure logger for NGX scraping operations.

    Args:
        name (str): Logger name
        log_level: Logging level (default: INFO)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # File handler - daily log file
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"ngx_scraper_{today}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name="ngx_scraper"):
    """
    Get a configured logger instance.

    Args:
        name (str): Logger name

    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)

    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        logger = setup_logger(name)

    return logger


def log_scraping_start(logger):
    """Log the start of scraping process."""
    logger.info("=" * 60)
    logger.info("Starting NGX Stock Market Data Scraping Process")
    logger.info("=" * 60)


def log_scraping_end(logger, success=True, data_rows=0):
    """Log the end of scraping process."""
    if success:
        logger.info(
            f"Scraping completed successfully. Extracted {data_rows} rows of data."
        )
    else:
        logger.error("Scraping failed.")
    logger.info("=" * 60)


def log_attempt(logger, attempt_number, max_attempts=3):
    """Log scraping attempt."""
    logger.info(f"Attempt {attempt_number}/{max_attempts}: Processing...")


def log_error(logger, error_msg, retry=True):
    """Log error with retry information."""
    if retry:
        logger.warning(f"Error occurred: {error_msg} - Will retry...")
    else:
        logger.error(f"Final error: {error_msg}")


def log_step(logger, step_name, details=""):
    """Log a processing step."""
    if details:
        logger.info(f"{step_name}: {details}")
    else:
        logger.info(step_name)
