"""Centralized logging configuration for the application."""

import logging
import structlog
import os
from pathlib import Path
from app.constants import DEFAULT_LOG_LEVEL, LOG_FORMAT


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    json_logs: bool = False
):
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_logs: Whether to output logs in JSON format
    """
    # Use environment variable or default
    log_level = log_level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    
    # Configure Python logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=LOG_FORMAT
    )
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(file_handler)
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for temporary logging context."""
    
    def __init__(self, **kwargs):
        """
        Initialize log context.
        
        Args:
            **kwargs: Key-value pairs to bind to logger
        """
        self.context = kwargs
        self.logger = None
        
    def __enter__(self):
        """Enter context and bind values."""
        self.logger = structlog.get_logger()
        for key, value in self.context.items():
            self.logger = self.logger.bind(**{key: value})
        return self.logger
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and unbind values."""
        if self.logger:
            for key in self.context:
                self.logger = self.logger.unbind(key)


# Initialize logging on module import
setup_logging()
