import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Define a standard structured format for log messages
# TIMESTAMP | LEVEL | FILE:LINE | MESSAGE
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
formatter = logging.Formatter(LOG_FORMAT)

# Setup console output handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# Setup rotating file output handler (maximum 10MB per file, keeping 5 backups)
file_handler = RotatingFileHandler(
    "logs/vizicheck.log",
    maxBytes=10485760,  # 10MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)
