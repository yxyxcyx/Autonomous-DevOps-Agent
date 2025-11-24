"""Error recovery strategies for the DevOps agent."""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
import structlog
from app.constants import (
    MAX_LOG_DISPLAY_LENGTH,
    MAX_STDOUT_DISPLAY_LENGTH, 
    MAX_STDERR_DISPLAY_LENGTH,
    DEFAULT_LLM_MAX_RETRIES
)

logger = structlog.get_logger()


class ErrorRecoveryStrategy:
    """Handles error recovery with fallback strategies."""
    
    def __init__(self):
        self.recovery_actions = {
            "llm_error": self._handle_llm_error,
            "docker_error": self._handle_docker_error,
            "repository_error": self._handle_repository_error,
            "timeout_error": self._handle_timeout_error,
            "validation_error": self._handle_validation_error
        }
    
    def recover(self, error_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to recover from an error.
        
        Args:
            error_type: Type of error that occurred
            context: Error context and state information
            
        Returns:
            Recovery result with suggested actions
        """
        recovery_func = self.recovery_actions.get(
            error_type, 
            self._handle_generic_error
        )
        
        try:
            return recovery_func(context)
        except Exception as e:
            logger.error(f"Recovery failed: {str(e)}")
            return {
                "recovered": False,
                "action": "abort",
                "message": f"Recovery failed: {str(e)}"
            }
    
    def _handle_llm_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LLM-related errors."""
        error_msg = context.get("error", "")
        attempts = context.get("attempts", 0)
        
        if "rate_limit" in error_msg.lower():
            return {
                "recovered": True,
                "action": "retry_with_backoff",
                "delay": min(60 * (2 ** attempts), 300),  # Exponential backoff up to 5 min
                "message": "Rate limit hit, will retry with backoff"
            }
        
        if "timeout" in error_msg.lower():
            return {
                "recovered": True,
                "action": "retry_with_simpler_prompt",
                "message": "LLM timeout, simplifying prompt"
            }
        
        if attempts < DEFAULT_LLM_MAX_RETRIES:
            return {
                "recovered": True,
                "action": "retry",
                "message": f"LLM error, retry {attempts + 1}/{DEFAULT_LLM_MAX_RETRIES}"
            }
        
        return {
            "recovered": False,
            "action": "fallback_to_simple",
            "message": "LLM failures exceeded, using simple fallback"
        }
    
    def _handle_docker_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Docker-related errors."""
        error_msg = context.get("error", "")
        
        if "connection refused" in error_msg.lower():
            return {
                "recovered": False,
                "action": "use_simple_executor",
                "message": "Docker not available, using simple executor"
            }
        
        if "no space left" in error_msg.lower():
            return {
                "recovered": True,
                "action": "cleanup_and_retry",
                "message": "Disk space issue, cleaning up containers"
            }
        
        if "timeout" in error_msg.lower():
            return {
                "recovered": True,
                "action": "increase_timeout",
                "new_timeout": context.get("timeout", 30) * 2,
                "message": "Execution timeout, increasing limit"
            }
        
        return {
            "recovered": False,
            "action": "skip_sandboxing",
            "message": "Docker error, skipping sandboxed execution"
        }
    
    def _handle_repository_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle repository-related errors."""
        error_msg = context.get("error", "")
        
        if "authentication" in error_msg.lower():
            return {
                "recovered": False,
                "action": "request_credentials",
                "message": "Repository requires authentication"
            }
        
        if "not found" in error_msg.lower():
            return {
                "recovered": False,
                "action": "verify_url",
                "message": "Repository not found, check URL"
            }
        
        if "timeout" in error_msg.lower():
            return {
                "recovered": True,
                "action": "retry_shallow_clone",
                "message": "Clone timeout, trying shallow clone"
            }
        
        return {
            "recovered": True,
            "action": "proceed_without_repo",
            "message": "Repository access failed, proceeding with limited context"
        }
    
    def _handle_timeout_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timeout errors."""
        task_type = context.get("task_type", "")
        
        if task_type == "test_execution":
            return {
                "recovered": True,
                "action": "simplify_tests",
                "message": "Test timeout, running subset of tests"
            }
        
        return {
            "recovered": True,
            "action": "extend_timeout",
            "new_timeout": context.get("timeout", 30) * 1.5,
            "message": "Extending timeout and retrying"
        }
    
    def _handle_validation_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors."""
        return {
            "recovered": False,
            "action": "request_clarification",
            "message": "Input validation failed, need clarification"
        }
    
    def _handle_generic_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic/unknown errors."""
        attempts = context.get("attempts", 0)
        
        if attempts < 3:
            return {
                "recovered": True,
                "action": "retry",
                "delay": 5 * attempts,
                "message": f"Generic error, retry {attempts + 1}/3"
            }
        
        return {
            "recovered": False,
            "action": "abort",
            "message": "Unrecoverable error after multiple attempts"
        }


def with_recovery(error_type: str = "generic"):
    """
    Decorator for functions with error recovery.
    
    Args:
        error_type: Type of error to handle
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery = ErrorRecoveryStrategy()
            attempts = 0
            max_attempts = 3
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logger.error(
                        f"Function {func.__name__} failed",
                        error=str(e),
                        attempt=attempts
                    )
                    
                    context = {
                        "error": str(e),
                        "attempts": attempts,
                        "function": func.__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100]
                    }
                    
                    result = recovery.recover(error_type, context)
                    
                    if not result["recovered"]:
                        logger.error(f"Recovery failed: {result['message']}")
                        raise
                    
                    if result["action"] == "retry":
                        delay = result.get("delay", 5)
                        logger.info(f"Retrying in {delay} seconds")
                        time.sleep(delay)
                        continue
                    
                    if result["action"] == "abort":
                        raise
                    
                    # For other actions, return the recovery result
                    return result
            
            raise Exception(f"Max attempts ({max_attempts}) exceeded")
        
        return wrapper
    return decorator


def truncate_output(text: str, output_type: str = "log") -> str:
    """
    Truncate output text based on type.
    
    Args:
        text: Text to truncate
        output_type: Type of output (log, stdout, stderr)
        
    Returns:
        Truncated text with indicator if truncated
    """
    limits = {
        "log": MAX_LOG_DISPLAY_LENGTH,
        "stdout": MAX_STDOUT_DISPLAY_LENGTH,
        "stderr": MAX_STDERR_DISPLAY_LENGTH
    }
    
    limit = limits.get(output_type, MAX_LOG_DISPLAY_LENGTH)
    
    if len(text) <= limit:
        return text
    
    return f"{text[:limit]}... [truncated, showing first {limit} characters]"
