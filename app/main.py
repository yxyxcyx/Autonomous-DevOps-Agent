"""FastAPI Gateway for the Autonomous DevOps Agent."""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from app.models import BugFixRequest, TaskResponse, TaskResult, TaskStatus
from app.config import settings
from app.celery_app import celery_app
from app.tasks import process_bug_fix
from app.storage import task_storage
from app.logging_config import get_logger, LogContext
from app.utils import validate_required_fields, format_error_message, Timer

logger = get_logger(__name__)


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
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    logger.warning(
        "Request validation failed",
        path=request.url.path,
        errors=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging."""
    logger.warning(
        "HTTP exception occurred",
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    error_id = str(uuid.uuid4())
    logger.error(
        "Unexpected error occurred",
        error_id=error_id,
        path=request.url.path,
        error=format_error_message(exc)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error_id": error_id
        }
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    """
    Health check endpoint.
    
    Returns:
        Dictionary with service status and version
    """
    try:
        # Check if Redis is accessible
        task_count = task_storage.get_task_count()
        redis_healthy = task_count >= 0
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_healthy = False
    
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "service": "Autonomous DevOps Agent",
        "version": "1.0.0",
        "components": {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "api": "healthy"
        }
    }


@app.post(
    "/api/v1/fix_bug",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def fix_bug(request: BugFixRequest):
    """
    Submit a bug fix request to the agent.
    
    This endpoint queues the task for async processing by Celery workers.
    
    Args:
        request: Bug fix request details
        
    Returns:
        TaskResponse with task ID and status
        
    Raises:
        HTTPException: If validation fails or task creation fails
    """
    task_id = str(uuid.uuid4())
    
    # Validate request
    try:
        validate_required_fields(
            request.dict(),
            ["repository_url", "issue_description"],
            context="Bug fix request"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    with LogContext(task_id=task_id, repository=request.repository_url):
        logger.info("Received bug fix request")
        
        try:
            # Queue the task for async processing
            task = process_bug_fix.apply_async(
                args=[task_id, request.dict()],
                task_id=task_id
            )
            
            # Store initial task status in Redis
            initial_task = TaskResult(
                task_id=task_id,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                completed_at=None,
                result=None,
                error=None,
                execution_steps=[]
            )
            
            if not task_storage.store_task(initial_task):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to store task. Storage service may be unavailable."
                )
            
            return TaskResponse(
                task_id=task_id,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                message=f"Bug fix task queued successfully. Track progress at /api/v1/tasks/{task_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create task: {format_error_message(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task. Please try again."
            )


@app.get(
    "/api/v1/tasks/{task_id}",
    response_model=TaskResult,
    responses={
        404: {"description": "Task not found"},
        503: {"description": "Storage service unavailable"}
    }
)
async def get_task_status(task_id: str):
    """
    Get the status and result of a bug fix task.
    
    Args:
        task_id: Unique task identifier
        
    Returns:
        TaskResult with current status and details
        
    Raises:
        HTTPException: If task not found or service unavailable
    """
    with Timer(f"Get task {task_id}"):
        try:
            # Get task from storage
            task_result = task_storage.get_task(task_id)
            
            if not task_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            # Check Celery task state
            try:
                celery_task = celery_app.AsyncResult(task_id)
                
                # Update status based on Celery task state
                if celery_task.state == 'PENDING':
                    task_result.status = TaskStatus.PENDING
                elif celery_task.state == 'STARTED':
                    task_result.status = TaskStatus.PROCESSING
                elif celery_task.state == 'SUCCESS':
                    task_result.status = TaskStatus.SUCCESS
                    task_result.completed_at = datetime.utcnow()
                    if celery_task.result:
                        task_result.result = celery_task.result
                elif celery_task.state == 'FAILURE':
                    task_result.status = TaskStatus.FAILED
                    task_result.completed_at = datetime.utcnow()
                    task_result.error = str(celery_task.info)
                
                # Save updated status to storage
                task_storage.store_task(task_result)
                
            except Exception as e:
                logger.warning(f"Failed to check Celery status: {str(e)}")
                # Continue with data from storage
            
            return task_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get task status: {format_error_message(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to retrieve task status. Storage service may be unavailable."
            )


@app.delete(
    "/api/v1/tasks/{task_id}",
    responses={
        200: {"description": "Task cancelled successfully"},
        404: {"description": "Task not found"},
        409: {"description": "Task already completed"}
    }
)
async def cancel_task(task_id: str):
    """
    Cancel a running bug fix task.
    
    Args:
        task_id: Unique task identifier
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If task not found or already completed
    """
    try:
        # Check storage for task
        task_result = task_storage.get_task(task_id)
        
        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        # Check if task is already completed
        if task_result.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task {task_id} is already {task_result.status.value}"
            )
        
        # Revoke the Celery task
        try:
            celery_task = celery_app.AsyncResult(task_id)
            celery_task.revoke(terminate=True)
        except Exception as e:
            logger.warning(f"Failed to revoke Celery task: {str(e)}")
        
        # Update task status in storage
        if not task_storage.update_task_status(task_id, TaskStatus.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to update task status"
            )
        
        logger.info("Task cancelled", task_id=task_id)
        
        return {
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id,
            "status": TaskStatus.CANCELLED.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {format_error_message(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task"
        )


@app.get(
    "/api/v1/tasks",
    responses={
        200: {"description": "List of tasks"},
        503: {"description": "Storage service unavailable"}
    }
)
async def list_tasks(
    limit: int = settings.API_PAGINATION_DEFAULT_LIMIT,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    List all bug fix tasks with pagination.
    
    Args:
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        status: Optional status filter
        
    Returns:
        Dictionary with tasks list and pagination metadata
        
    Raises:
        HTTPException: If storage service is unavailable
    """
    # Validate pagination parameters
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be positive"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset cannot be negative"
        )
    
    # Apply maximum limit
    if limit > settings.API_PAGINATION_MAX_LIMIT:
        limit = settings.API_PAGINATION_MAX_LIMIT
    
    try:
        # Get tasks from storage
        task_list = task_storage.list_tasks(limit=limit, offset=offset)
        total_tasks = task_storage.get_task_count()
        
        # Apply status filter if provided
        if status:
            try:
                status_enum = TaskStatus(status.lower())
                task_list = [t for t in task_list if t.status == status_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid values: {[s.value for s in TaskStatus]}"
                )
        
        return {
            "total": total_tasks,
            "limit": limit,
            "offset": offset,
            "filter": {"status": status} if status else None,
            "tasks": task_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tasks: {format_error_message(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve tasks. Storage service may be unavailable."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
