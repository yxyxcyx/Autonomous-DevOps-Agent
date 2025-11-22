"""Application-wide constants and default values."""

# Default Network Configuration
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0
DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8000

# Default URLs
DEFAULT_REDIS_URL = f"redis://{DEFAULT_REDIS_HOST}:{DEFAULT_REDIS_PORT}/{DEFAULT_REDIS_DB}"
DEFAULT_UI_API_BASE_URL = f"http://localhost:{DEFAULT_API_PORT}"

# Default Domains
DEFAULT_STAGING_DOMAIN = "staging.example.com"
DEFAULT_PRODUCTION_DOMAIN = "app.example.com"
DEFAULT_TESTING_CORS = "http://localhost:3000"

# Task Configuration
DEFAULT_TASK_STORAGE_TTL = 86400  # 24 hours
DEFAULT_PAGINATION_LIMIT = 10
MAX_PAGINATION_LIMIT = 100

# Celery Configuration
DEFAULT_TASK_TIME_LIMIT = 1800  # 30 minutes
DEFAULT_TASK_SOFT_TIME_LIMIT = 1500  # 25 minutes
DEFAULT_WORKER_PREFETCH_MULTIPLIER = 1
DEFAULT_WORKER_MAX_TASKS_PER_CHILD = 1
DEFAULT_RESULT_EXPIRES = 3600  # 1 hour

# Docker Configuration
DEFAULT_DOCKER_TIMEOUT = 300
DEFAULT_DOCKER_MAX_MEMORY = "512m"
DEFAULT_DOCKER_MAX_CPU = 0.5
DOCKER_CLEANUP_TIMEOUT = 5

# LLM Configuration
DEFAULT_LLM_MODEL = "gemini-1.5-flash"
DEFAULT_LLM_TEMPERATURE = 0.1
DEFAULT_LLM_MAX_RETRIES = 3

# UI Configuration
DEFAULT_UI_REFRESH_INTERVAL = 2000  # milliseconds
DEFAULT_UI_TASK_HISTORY_LIMIT = 50

# Logging Configuration
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Text Truncation Limits
MAX_LOG_DISPLAY_LENGTH = 500
MAX_STDOUT_DISPLAY_LENGTH = 1000
MAX_STDERR_DISPLAY_LENGTH = 1000

# Agent Configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_LANGUAGE = "python"
DEFAULT_BRANCH = "main"

# Docker Language Mappings
DOCKER_IMAGES = {
    "python": "python:3.9-slim",
    "javascript": "node:18-slim",
    "typescript": "node:18-slim",
    "java": "openjdk:11-slim",
    "go": "golang:1.21-alpine",
    "rust": "rust:slim",
    "ruby": "ruby:3.1-slim",
    "php": "php:8.1-cli"
}

CODE_EXTENSIONS = {
    "python": "main.py",
    "javascript": "main.js",
    "typescript": "main.ts",
    "java": "Main.java",
    "go": "main.go",
    "rust": "main.rs",
    "ruby": "main.rb",
    "php": "main.php"
}

EXEC_COMMANDS = {
    "python": "python {filename}",
    "javascript": "node {filename}",
    "typescript": "npx ts-node {filename}",
    "java": "javac {filename} && java Main",
    "go": "go run {filename}",
    "rust": "rustc {filename} && ./main",
    "ruby": "ruby {filename}",
    "php": "php {filename}"
}

# API Response Status Codes
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

# Example Repository URL (for UI forms)
EXAMPLE_REPO_URL = "https://github.com/example/repo"
