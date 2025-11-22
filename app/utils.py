"""Utility functions to reduce code duplication across the application."""

import json
import structlog
from typing import Any, Dict, Optional, TypeVar, Callable
from functools import wraps
import time
from app.constants import MAX_LOG_DISPLAY_LENGTH

logger = structlog.get_logger()

T = TypeVar('T')


def parse_json_response(text: str, fallback: Any = None) -> Any:
    """
    Safely parse JSON response with fallback.
    
    Args:
        text: JSON string to parse
        fallback: Value to return if parsing fails
        
    Returns:
        Parsed JSON object or fallback value
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {str(e)[:100]}")
        return fallback if fallback is not None else text


def log_agent_action(state: Dict[str, Any], node_name: str, action: str, **kwargs):
    """
    Standardized logging for agent actions.
    
    Args:
        state: Agent state dictionary
        node_name: Name of the node performing the action
        action: Action being performed
        **kwargs: Additional logging parameters
    """
    log_data = {
        "task_id": state.get("task_id"),
        "node": node_name,
        "action": action,
        "attempt": state.get("attempts", 0),
        **kwargs
    }
    logger.info(f"{node_name}: {action}", **log_data)


def truncate_text(text: str, max_length: int = MAX_LOG_DISPLAY_LENGTH) -> str:
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on exception with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)[:100]}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def validate_required_fields(data: Dict[str, Any], required_fields: list, context: str = ""):
    """
    Validate that required fields are present and non-empty.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context string for error messages
        
    Raises:
        ValueError: If any required field is missing or empty
    """
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field]:
            empty_fields.append(field)
    
    errors = []
    if missing_fields:
        errors.append(f"Missing fields: {', '.join(missing_fields)}")
    if empty_fields:
        errors.append(f"Empty fields: {', '.join(empty_fields)}")
    
    if errors:
        error_msg = f"{context + ': ' if context else ''}{'; '.join(errors)}"
        raise ValueError(error_msg)


def safe_dict_get(dictionary: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation.
    
    Args:
        dictionary: Dictionary to search
        key_path: Dot-separated path to key (e.g., "user.profile.name")
        default: Default value if key not found
        
    Returns:
        Value at key_path or default
    """
    keys = key_path.split('.')
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    
    return value


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format an error message with context for logging.
    
    Args:
        error: The exception to format
        context: Additional context about where the error occurred
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"[{context}] {error_type}: {error_msg}"
    return f"{error_type}: {error_msg}"


def batch_process(items: list, batch_size: int, processor: Callable):
    """
    Process items in batches.
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        processor: Function to process each batch
        
    Returns:
        List of results from each batch
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        try:
            result = processor(batch)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch processing failed for batch {i//batch_size}: {str(e)}")
            results.append(None)
    
    return results


def create_execution_result(
    success: bool,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized execution result dictionary.
    
    Args:
        success: Whether the execution was successful
        data: Result data if successful
        error: Error message if failed
        metadata: Additional metadata
        
    Returns:
        Standardized result dictionary
    """
    result = {
        "success": success,
        "timestamp": time.time(),
        "data": data or {},
        "error": error,
        "metadata": metadata or {}
    }
    
    return result


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, name: str = "Operation"):
        """
        Initialize timer.
        
        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and log the duration."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.name} took {duration:.2f} seconds")
        
    @property
    def elapsed(self) -> float:
        """Get elapsed time."""
        if self.start_time is None:
            return 0
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
