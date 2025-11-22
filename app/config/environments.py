"""Environment-specific configuration management."""

from typing import Dict, Any
from dataclasses import dataclass, fields
from pathlib import Path
import json
import os
import structlog


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    
    # Environment name
    name: str
    
    # Debug and logging
    debug: bool = False
    log_level: str = "INFO"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = False
    
    # Security settings
    cors_origins: list = None
    enable_rate_limiting: bool = False
    
    # Performance settings
    docker_timeout: int = 300
    docker_memory: str = "512m"
    docker_cpu: float = 0.5
    
    # LLM settings
    llm_temperature: float = 0.1
    llm_max_retries: int = 3
    
    # Workflow settings
    max_attempts: int = 3
    enable_llm_logging: bool = True
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


logger = structlog.get_logger()
PRESET_FILE = Path(__file__).with_name("environment_presets.json")


DEFAULT_PRESETS = {
        "development": {
            "debug": True,
            "log_level": "DEBUG",
            "api_host": "127.0.0.1",
            "api_port": 8000,
            "api_workers": 1,
            "api_reload": True,
            "cors_origins": ["*"],
            "enable_rate_limiting": False,
            "docker_timeout": 300,
            "docker_memory": "512m",
            "docker_cpu": 0.5,
            "llm_temperature": 0.1,
            "llm_max_retries": 3,
            "max_attempts": 3,
            "enable_llm_logging": True
        },
        "testing": {
            "debug": False,
            "log_level": "WARNING",
            "api_host": "127.0.0.1",
            "api_port": 8001,
            "api_workers": 1,
            "api_reload": False,
            "cors_origins": ["http://localhost:3000"],
            "enable_rate_limiting": False,
            "docker_timeout": 180,
            "docker_memory": "256m",
            "docker_cpu": 0.3,
            "llm_temperature": 0.0,
            "llm_max_retries": 1,
            "max_attempts": 1,
            "enable_llm_logging": False
        },
        "staging": {
            "debug": False,
            "log_level": "INFO",
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "api_workers": 2,
            "api_reload": False,
            "cors_origins": ["https://staging.example.com"],
            "enable_rate_limiting": True,
            "docker_timeout": 600,
            "docker_memory": "1g",
            "docker_cpu": 1.0,
            "llm_temperature": 0.1,
            "llm_max_retries": 3,
            "max_attempts": 5,
            "enable_llm_logging": True
        },
        "production": {
            "debug": False,
            "log_level": "WARNING",
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "api_workers": 4,
            "api_reload": False,
            "cors_origins": ["https://app.example.com"],
            "enable_rate_limiting": True,
            "docker_timeout": 900,
            "docker_memory": "2g",
            "docker_cpu": 2.0,
            "llm_temperature": 0.0,
            "llm_max_retries": 5,
            "max_attempts": 3,
            "enable_llm_logging": False
        }
}


def _load_environment_presets() -> Dict[str, Dict[str, Any]]:
    """Load preset definitions from JSON, falling back to defaults if needed."""
    if PRESET_FILE.exists():
        try:
            with PRESET_FILE.open("r", encoding="utf-8") as preset_file:
                data = json.load(preset_file)
                if isinstance(data, dict):
                    return data
                logger.warning(
                    "Environment preset file is malformed; expected object.",
                    path=str(PRESET_FILE)
                )
        except Exception as exc:
            logger.warning(
                "Failed to load environment presets; falling back to defaults.",
                path=str(PRESET_FILE),
                error=str(exc)
            )
    return DEFAULT_PRESETS.copy()


def _build_environment_configs() -> Dict[str, EnvironmentConfig]:
    """Construct EnvironmentConfig objects from preset data."""
    presets = _load_environment_presets()
    allowed_fields = {field.name for field in fields(EnvironmentConfig)}

    environments: Dict[str, EnvironmentConfig] = {}
    for name, config_data in presets.items():
        config_kwargs = {"name": name}
        if isinstance(config_data, dict):
            for key, value in config_data.items():
                if key in allowed_fields and key != "name":
                    config_kwargs[key] = value
        else:
            logger.warning(
                "Skipping environment preset due to invalid structure.",
                environment=name
            )
            continue

        environments[name] = EnvironmentConfig(**config_kwargs)

    return environments or {
        name: EnvironmentConfig(name=name)
        for name in ["development", "testing", "staging", "production"]
    }


class EnvironmentManager:
    """Manages environment-specific configurations."""
    
    # Predefined environment configurations
    ENVIRONMENTS: Dict[str, EnvironmentConfig] = _build_environment_configs()
    
    @classmethod
    def get_environment_config(cls, environment: str = None) -> EnvironmentConfig:
        """Get configuration for the specified environment."""
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        if environment not in cls.ENVIRONMENTS:
            # Fallback to development if unknown environment
            environment = "development"
        
        return cls.ENVIRONMENTS[environment]
    
    @classmethod
    def register_environment(cls, name: str, config: EnvironmentConfig):
        """Register a custom environment configuration."""
        cls.ENVIRONMENTS[name] = config
    
    @classmethod
    def list_environments(cls) -> list:
        """List all available environments."""
        return list(cls.ENVIRONMENTS.keys())
    
    @classmethod
    def apply_environment_overrides(cls, settings_obj: Any, environment: str = None):
        """Apply environment-specific overrides to settings object."""
        env_config = cls.get_environment_config(environment)
        
        # Apply overrides based on the structure of the settings object
        if hasattr(settings_obj, 'api'):
            settings_obj.api.debug = env_config.debug
            settings_obj.api.host = env_config.api_host
            settings_obj.api.port = env_config.api_port
            settings_obj.api.workers = env_config.api_workers
            settings_obj.api.reload = env_config.api_reload
            settings_obj.api.cors_origins = env_config.cors_origins
            settings_obj.api.rate_limit_enabled = env_config.enable_rate_limiting
        
        if hasattr(settings_obj, 'docker'):
            settings_obj.docker.timeout = env_config.docker_timeout
            settings_obj.docker.max_memory = env_config.docker_memory
            settings_obj.docker.max_cpu = env_config.docker_cpu
        
        if hasattr(settings_obj, 'llm'):
            settings_obj.llm.temperature = env_config.llm_temperature
            settings_obj.llm.max_retries = env_config.llm_max_retries
        
        if hasattr(settings_obj, 'workflow'):
            settings_obj.workflow.max_attempts = env_config.max_attempts
            settings_obj.workflow.enable_llm_logging = env_config.enable_llm_logging
            settings_obj.workflow.log_level = env_config.log_level
        
        return settings_obj


# Global environment manager
environment_manager = EnvironmentManager()


def get_environment_config(environment: str = None) -> EnvironmentConfig:
    """Get the current environment configuration."""
    return environment_manager.get_environment_config(environment)


def is_development() -> bool:
    """Check if running in development mode."""
    return get_environment_config().name == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return get_environment_config().name == "production"


def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_environment_config().name == "testing"
