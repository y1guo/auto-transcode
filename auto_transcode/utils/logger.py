import logging
import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()

LOG_FILE = os.getenv("LOG_FILE")


class CustomFormatter(logging.Formatter):
    green = "\x1b[32m"
    grey = "\x1b[37m"
    cyan = "\x1b[36m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bg_red = "\x1b[41m"
    reset = "\x1b[0m"
    time_format = "%(asctime)s "
    log_format = "%(levelname)s - %(processName)s - %(filename)s:%(lineno)d - %(message)s"

    FORMATS = {
        logging.DEBUG: green + time_format + reset + grey + log_format + reset,
        logging.INFO: green + time_format + reset + cyan + log_format + reset,
        logging.WARNING: green + time_format + reset + yellow + log_format + reset,
        logging.ERROR: green + time_format + reset + red + log_format + reset,
        logging.CRITICAL: green + time_format + reset + bg_red + log_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


formatter = "%(asctime)s - %(processName)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s"


def get_logger(logger_name: Optional[str] = None):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())

    # Add the handler to the logger
    logger.addHandler(console_handler)

    if LOG_FILE:
        # Create a file handler that logs even debug messages
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        fh_format = logging.Formatter(formatter)
        file_handler.setFormatter(fh_format)

        # Add the handler to the logger
        logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
    print()

    for i in range(128):
        print(f"\x1b[{i}m{i:03}\x1b[0m", end=" " if (i + 1) % 16 != 0 else "\n")
    print()

    for i in range(256):
        print(f"\x1b[38;5;{i}m{i:03}\x1b[0m", end=" " if (i + 1) % 16 != 0 else "\n")
    print()

    for i in range(256):
        print(f"\x1b[48;5;{i}m{i:03}\x1b[0m", end=" " if (i + 1) % 16 != 0 else "\n")
    print()
