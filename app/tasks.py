"""Celery tasks for async bug fix processing."""

from celery import Task
from app.celery_app import celery_app
from app.agents.orchestrator import DevOpsAgentOrchestrator
import structlog
import asyncio
from typing import Dict, Any

logger = structlog.get_logger()


class CallbackTask(Task):
    """Base task with callbacks."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Success callback."""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback."""
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(bind=True, base=CallbackTask, name="process_bug_fix")
def process_bug_fix(self, task_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a bug fix request asynchronously.
    
    Args:
        task_id: Unique task identifier
        request_data: Bug fix request details
        
    Returns:
        Result dictionary with patches and test results
    """
    try:
        logger.info(
            "Starting bug fix task",
            task_id=task_id,
            repository=request_data.get("repository_url")
        )
        
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "current": "Initializing agent",
                "total": 100,
                "status": "Running bug analysis..."
            }
        )
        
        # Create orchestrator
        orchestrator = DevOpsAgentOrchestrator()
        
        # Run async workflow using asyncio.run() - cleaner and safer
        try:
            result = asyncio.run(
                orchestrator.execute_fix(task_id, request_data)
            )
        except RuntimeError as e:
            # Handle case where event loop is already running
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                # Use nest_asyncio as a fallback
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    orchestrator.execute_fix(task_id, request_data)
                )
            else:
                raise
        
        logger.info(
            "Bug fix task completed",
            task_id=task_id,
            status=result.get("status"),
            attempts=result.get("attempts")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Bug fix task failed: {str(e)}")
        
        # Return error result
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "patches": [],
            "test_results": []
        }


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """
    Periodic task to clean up old task results.
    """
    logger.info("Running cleanup of old tasks")
    # Implementation would clean up Redis/database entries older than X days
    pass


@celery_app.task(name="health_check")
def health_check() -> Dict[str, str]:
    """
    Health check task for monitoring.
    """
    return {
        "status": "healthy",
        "worker": "active"
    }
