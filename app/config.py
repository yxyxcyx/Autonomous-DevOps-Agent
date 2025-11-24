"""Configuration management for the DevOps Agent."""

from pydantic_settings import BaseSettings
from typing import Optional
import os
import sys
import structlog
from app.constants import (
    DEFAULT_REDIS_HOST, DEFAULT_REDIS_PORT, DEFAULT_REDIS_DB,
    DEFAULT_API_HOST, DEFAULT_API_PORT, DEFAULT_REDIS_URL,
    DEFAULT_DOCKER_TIMEOUT, DEFAULT_DOCKER_MAX_MEMORY, DEFAULT_DOCKER_MAX_CPU,
    DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE, DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_TASK_STORAGE_TTL, DEFAULT_PAGINATION_LIMIT, MAX_PAGINATION_LIMIT,
    DEFAULT_TASK_TIME_LIMIT, DEFAULT_TASK_SOFT_TIME_LIMIT,
    DEFAULT_WORKER_PREFETCH_MULTIPLIER, DEFAULT_WORKER_MAX_TASKS_PER_CHILD,
    DEFAULT_RESULT_EXPIRES, DEFAULT_UI_API_BASE_URL, DEFAULT_UI_REFRESH_INTERVAL,
    DEFAULT_UI_TASK_HISTORY_LIMIT
)

logger = structlog.get_logger()


class Settings(BaseSettings):
    """Application settings."""
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", DEFAULT_REDIS_HOST)
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", str(DEFAULT_REDIS_PORT)))
    REDIS_DB: int = int(os.getenv("REDIS_DB", str(DEFAULT_REDIS_DB)))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", DEFAULT_REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", DEFAULT_REDIS_URL)
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", DEFAULT_API_HOST)
    API_PORT: int = int(os.getenv("API_PORT", str(DEFAULT_API_PORT)))
    
    # Docker Configuration
    DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", str(DEFAULT_DOCKER_TIMEOUT)))
    DOCKER_MAX_MEMORY: str = os.getenv("DOCKER_MAX_MEMORY", DEFAULT_DOCKER_MAX_MEMORY)
    DOCKER_MAX_CPU: float = float(os.getenv("DOCKER_MAX_CPU", str(DEFAULT_DOCKER_MAX_CPU)))
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", str(DEFAULT_LLM_TEMPERATURE)))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", str(DEFAULT_LLM_MAX_RETRIES)))
    
    # Task Storage Configuration
    TASK_STORAGE_TTL: int = int(os.getenv("TASK_STORAGE_TTL", str(DEFAULT_TASK_STORAGE_TTL)))
    
    # API Configuration
    API_CORS_ORIGINS: list = os.getenv("API_CORS_ORIGINS", "*").split(",") if os.getenv("API_CORS_ORIGINS") else ["*"]
    API_PAGINATION_DEFAULT_LIMIT: int = int(os.getenv("API_PAGINATION_DEFAULT_LIMIT", str(DEFAULT_PAGINATION_LIMIT)))
    API_PAGINATION_MAX_LIMIT: int = int(os.getenv("API_PAGINATION_MAX_LIMIT", str(MAX_PAGINATION_LIMIT)))
    
    # Celery Configuration
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", str(DEFAULT_TASK_TIME_LIMIT)))
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", str(DEFAULT_TASK_SOFT_TIME_LIMIT)))
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", str(DEFAULT_WORKER_PREFETCH_MULTIPLIER)))
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = int(os.getenv("CELERY_WORKER_MAX_TASKS_PER_CHILD", str(DEFAULT_WORKER_MAX_TASKS_PER_CHILD)))
    CELERY_RESULT_EXPIRES: int = int(os.getenv("CELERY_RESULT_EXPIRES", str(DEFAULT_RESULT_EXPIRES)))
    
    # UI Configuration
    UI_API_BASE_URL: str = os.getenv("UI_API_BASE_URL", DEFAULT_UI_API_BASE_URL)
    UI_REFRESH_INTERVAL: int = int(os.getenv("UI_REFRESH_INTERVAL", str(DEFAULT_UI_REFRESH_INTERVAL)))
    UI_TASK_HISTORY_LIMIT: int = int(os.getenv("UI_TASK_HISTORY_LIMIT", str(DEFAULT_UI_TASK_HISTORY_LIMIT)))
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_configuration(self) -> bool:
        """Validate critical configuration settings."""
        errors = []
        
        # Validate required API key
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required for LLM functionality")
        
        # Validate Redis configuration
        if not (1 <= self.REDIS_PORT <= 65535):
            errors.append("REDIS_PORT must be between 1 and 65535")
        
        # Validate API configuration
        if not (1 <= self.API_PORT <= 65535):
            errors.append("API_PORT must be between 1 and 65535")
        
        # Validate Docker configuration
        if self.DOCKER_TIMEOUT <= 0:
            errors.append("DOCKER_TIMEOUT must be positive")
        
        if self.DOCKER_MAX_CPU <= 0 or self.DOCKER_MAX_CPU > 1:
            errors.append("DOCKER_MAX_CPU must be between 0 and 1")
        
        # Validate LLM configuration
        if not (0 <= self.LLM_TEMPERATURE <= 2):
            errors.append("LLM_TEMPERATURE must be between 0 and 2")
        
        if self.LLM_MAX_RETRIES <= 0:
            errors.append("LLM_MAX_RETRIES must be positive")
        
        # Validate pagination limits
        if self.API_PAGINATION_DEFAULT_LIMIT <= 0:
            errors.append("API_PAGINATION_DEFAULT_LIMIT must be positive")
        
        if self.API_PAGINATION_MAX_LIMIT <= 0:
            errors.append("API_PAGINATION_MAX_LIMIT must be positive")
        
        if self.API_PAGINATION_DEFAULT_LIMIT > self.API_PAGINATION_MAX_LIMIT:
            errors.append("API_PAGINATION_DEFAULT_LIMIT cannot exceed API_PAGINATION_MAX_LIMIT")
        
        # Validate Celery configuration
        if self.CELERY_TASK_TIME_LIMIT <= 0:
            errors.append("CELERY_TASK_TIME_LIMIT must be positive")
        
        if self.CELERY_TASK_SOFT_TIME_LIMIT <= 0:
            errors.append("CELERY_TASK_SOFT_TIME_LIMIT must be positive")
        
        if self.CELERY_TASK_SOFT_TIME_LIMIT >= self.CELERY_TASK_TIME_LIMIT:
            errors.append("CELERY_TASK_SOFT_TIME_LIMIT must be less than CELERY_TASK_TIME_LIMIT")
        
        # Validate UI configuration
        if self.UI_REFRESH_INTERVAL <= 0:
            errors.append("UI_REFRESH_INTERVAL must be positive")
        
        if self.UI_TASK_HISTORY_LIMIT <= 0:
            errors.append("UI_TASK_HISTORY_LIMIT must be positive")
        
        if errors:
            for error in errors:
                logger.error("Configuration validation error", error=error)
            return False
        
        logger.info("Configuration validation passed")
        return True


try:
    settings = Settings()
    
    # Validate configuration on import
    if not settings.validate_configuration():
        logger.warning("Configuration validation failed - some features may not work properly")
        
        # Check for critical missing configuration
        if not settings.GEMINI_API_KEY:
            logger.error("CRITICAL: GEMINI_API_KEY is not set. Please set it in your .env file or environment variables.")
            sys.stderr.write("ERROR: GEMINI_API_KEY is required. Set it in your .env file.\n")
except Exception as e:
    logger.error(f"Failed to load settings: {str(e)}")
    sys.stderr.write(f"ERROR: Failed to load configuration: {str(e)}\n")
    raise
