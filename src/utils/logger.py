"""
Logging Utility Module
Provides structured logging for the application
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger as loguru_logger


def setup_logger(
    name: str = "posiva",
    log_file: Optional[str] = None,
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "1 week"
) -> loguru_logger:
    """
    Set up structured logging with loguru
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: Log rotation size
        retention: Log retention period
        
    Returns:
        Configured logger instance
    """
    # Remove default handler
    loguru_logger.remove()
    
    # Add console handler with colors
    loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    return loguru_logger


# Create default logger
logger = setup_logger()


class LoggerAdapter:
    """Adapter to make loguru work with standard logging interface"""
    
    def __init__(self, logger_instance):
        self.logger = logger_instance
    
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg)
    
    def info(self, msg, *args, **kwargs):
        self.logger.info(msg)
    
    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg)
    
    def error(self, msg, *args, **kwargs):
        self.logger.error(msg)
    
    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg)
    
    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg)


def get_logger(name: str = "posiva") -> LoggerAdapter:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger adapter instance
    """
    return LoggerAdapter(loguru_logger.bind(name=name))
