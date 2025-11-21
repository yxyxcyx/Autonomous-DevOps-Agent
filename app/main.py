"""FastAPI Gateway for the Autonomous DevOps Agent."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from typing import Dict
import uuid
from datetime import datetime

from app.models import BugFixRequest, TaskResponse, TaskResult, TaskStatus
from app.config import settings
from app.celery_app import celery_app
from app.tasks import process_bug_fix

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting DevOps Agent API")
    yield
    logger.info("Shutting down DevOps Agent API")


app = FastAPI(
    title="Autonomous DevOps Agent",
    description="AI-powered system for automated bug fixing and security patching",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task storage (replace with Redis in production)
tasks_db: Dict[str, TaskResult] = {}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Autonomous DevOps Agent",
        "version": "1.0.0"
    }


@app.post("/api/v1/fix_bug", response_model=TaskResponse)
async def fix_bug(request: BugFixRequest):
    """
    Submit a bug fix request to the agent.
    
    This endpoint queues the task for async processing by Celery workers.
    """
    task_id = str(uuid.uuid4())
    
    logger.info(
        "Received bug fix request",
        task_id=task_id,
        repository=request.repository_url,
        branch=request.branch
    )
    
    # Queue the task for async processing
    task = process_bug_fix.apply_async(
        args=[task_id, request.dict()],
        task_id=task_id
    )
    
    # Store initial task status
    tasks_db[task_id] = TaskResult(
        task_id=task_id,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
        completed_at=None,
        result=None,
        error=None,
        execution_steps=[]
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
        message=f"Bug fix task queued successfully. Track progress at /api/v1/tasks/{task_id}"
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResult)
async def get_task_status(task_id: str):
    """
    Get the status and result of a bug fix task.
    """
    # Check Celery task status
    task = celery_app.AsyncResult(task_id)
    
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task_result = tasks_db[task_id]
    
    # Update status based on Celery task state
    if task.state == 'PENDING':
        task_result.status = TaskStatus.PENDING
    elif task.state == 'STARTED':
        task_result.status = TaskStatus.PROCESSING
    elif task.state == 'SUCCESS':
        task_result.status = TaskStatus.SUCCESS
        task_result.completed_at = datetime.utcnow()
        if task.result:
            task_result.result = task.result
    elif task.state == 'FAILURE':
        task_result.status = TaskStatus.FAILED
        task_result.completed_at = datetime.utcnow()
        task_result.error = str(task.info)
    
    return task_result


@app.delete("/api/v1/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running bug fix task.
    """
    task = celery_app.AsyncResult(task_id)
    
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Revoke the Celery task
    task.revoke(terminate=True)
    
    # Update task status
    tasks_db[task_id].status = TaskStatus.CANCELLED
    tasks_db[task_id].completed_at = datetime.utcnow()
    
    logger.info("Task cancelled", task_id=task_id)
    
    return {"message": f"Task {task_id} cancelled successfully"}


@app.get("/api/v1/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """
    List all bug fix tasks with pagination.
    """
    task_list = list(tasks_db.values())
    task_list.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "total": len(task_list),
        "limit": limit,
        "offset": offset,
        "tasks": task_list[offset:offset + limit]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
