"""
Logger configuration for the AWS Service Quotas Comparison Tool.
"""
import sys
import logging
from pathlib import Path
import datetime

def setup_logger():
    """Configure and return the application logger."""
    # Configure logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Use a single log file per day instead of per session
    log_file = log_dir / f"quota_app_{datetime.datetime.now().strftime('%Y%m%d')}.log"

    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ])

    # Create a logger for this application
    logger = logging.getLogger('aws_quota_replicator')
    logger.info("Application starting")
    logger.info(f"Log file: {log_file}")
    
    return logger

# Create a global logger instance
logger = setup_logger()
