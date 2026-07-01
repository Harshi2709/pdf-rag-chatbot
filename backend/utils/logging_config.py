
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import os


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_filename: str = None
) -> logging.Logger:
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp if not provided
    if log_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_filename = f"rag_chatbot_{timestamp}.log"
    
    log_file_path = log_path / log_filename
    
    # Create logger
    logger = logging.getLogger("rag_chatbot")
    
    # Set log level
    log_level_value = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(log_level_value)
    
    # Remove existing handlers to prevent duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File Handler - Detailed logging with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5  # Keep 5 backup files
    )
    file_handler.setLevel(logging.DEBUG)  # File captures all levels
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console Handler - Less verbose formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level_value)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(module_name: str = None) -> logging.Logger:
    if module_name:
        return logging.getLogger(f"rag_chatbot.{module_name}")
    return logging.getLogger("rag_chatbot")
