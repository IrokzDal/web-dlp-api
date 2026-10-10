"""
Utility functions for validation, rate limiting, and logging.
"""
import re
import time
from collections import defaultdict
from typing import Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web-dlp')

# Rate limiting storage (IP -> list of timestamps)
rate_limit_storage: Dict[str, list] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX = 5  # 5 requests per minute


def is_valid_youtube_url(url: str) -> bool:
    """
    Validate if the URL is a valid YouTube URL.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid YouTube URL, False otherwise
    """
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+',
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False


def check_rate_limit(ip_address: str) -> bool:
    """
    Check if the IP has exceeded the rate limit.
    
    Args:
        ip_address: Client IP address
    
    Returns:
        True if within limits, False if exceeded
    """
    current_time = time.time()
    
    # Clean old entries
    rate_limit_storage[ip_address] = [
        timestamp for timestamp in rate_limit_storage[ip_address]
        if current_time - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limit_storage[ip_address]) >= RATE_LIMIT_MAX:
        return False
    
    # Add new request
    rate_limit_storage[ip_address].append(current_time)
    return True


def get_file_age(timestamp: float) -> float:
    """
    Calculate the age of a file in seconds.
    
    Args:
        timestamp: File creation timestamp
    
    Returns:
        Age in seconds
    """
    return time.time() - timestamp


def log_info(message: str):
    """Log info message."""
    logger.info(message)


def log_error(message: str):
    """Log error message."""
    logger.error(message)


def log_warning(message: str):
    """Log warning message."""
    logger.warning(message)
