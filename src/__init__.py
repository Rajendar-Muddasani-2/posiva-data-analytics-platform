"""
POSIVA Analytics Platform
Enterprise-grade data analytics for post-silicon validation
"""

__version__ = "0.1.0"
__author__ = "Rajendar Muddasani"
__email__ = "your.email@example.com"

from src.utils.config import Config
from src.utils.logger import setup_logger

# Initialize default logger
logger = setup_logger()

__all__ = ["Config", "logger", "__version__"]
