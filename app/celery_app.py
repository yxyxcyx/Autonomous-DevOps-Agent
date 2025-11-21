"""Celery application configuration for async task processing."""

from celery import Celery
from app.config import settings
import structlog

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "devops_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes
    task_soft_time_limit=1500,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1,
    result_expires=3600,  # 1 hour
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "Celery is working!"}


if __name__ == "__main__":
    celery_app.start()
