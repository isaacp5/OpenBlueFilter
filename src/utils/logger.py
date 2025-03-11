import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger():
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".openbluefilter" / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Format for logs
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # File handler for debug logs
    file_handler = RotatingFileHandler(
        log_dir / "openbluefilter.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Console handler for info+ logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger 