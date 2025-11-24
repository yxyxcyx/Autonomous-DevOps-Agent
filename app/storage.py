"""Redis-based task storage for the DevOps Agent."""

import json
import redis
from typing import Dict, Optional, List, Any
from datetime import datetime

from app.config import settings
from app.models import TaskResult, TaskStatus
from app.interfaces.storage import ITaskStorage

# Note: Removed structlog logger and retry decorators to prevent recursion issues


class RedisTaskStorage(ITaskStorage):
    """Redis-based storage for task results."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize Redis connection.
        
        Args:
            redis_client: Optional Redis client instance (for testing)
        """
        if redis_client:
            self.redis_client = redis_client
        else:
            # Use connection pool for better performance and resource management
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=50,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client = redis.Redis(connection_pool=pool)
        
    def store_task(self, task_result: TaskResult) -> bool:
        """
        Store a task result in Redis.
        
        Args:
            task_result: Task result to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"task:{task_result.task_id}"
            
            # Manually construct data dict to avoid Pydantic serialization issues
            data = {
                'task_id': task_result.task_id,
                'status': task_result.status.value if hasattr(task_result.status, 'value') else str(task_result.status),
                'created_at': task_result.created_at.isoformat() if task_result.created_at else None,
                'completed_at': task_result.completed_at.isoformat() if task_result.completed_at else None,
                'result': task_result.result if task_result.result else {},
                'error': task_result.error if task_result.error else None,
                'execution_steps': task_result.execution_steps if task_result.execution_steps else []
            }
            
            # Simple JSON serialization with string fallback
            json_data = json.dumps(data, default=str)
                
            self.redis_client.setex(
                key, 
                settings.TASK_STORAGE_TTL, 
                json_data
            )
            
            # Also add to task list for pagination
            self.redis_client.zadd(
                "tasks_by_time",
                {task_result.task_id: datetime.utcnow().timestamp()}
            )
            
            return True
            
        except Exception:
            # Silent failure - don't log to avoid recursion
            return False
    
    def get_task(self, task_id: str) -> Optional[TaskResult]:
        """
        Retrieve a task from Redis.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskResult if found, None otherwise
        """
        try:
            key = f"task:{task_id}"
            data = self.redis_client.get(key)
            
            if not data:
                return None
                
            task_dict = json.loads(data)
            
            # Convert ISO format back to datetime
            if task_dict.get('created_at'):
                task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
            if task_dict.get('completed_at'):
                task_dict['completed_at'] = datetime.fromisoformat(task_dict['completed_at'])
                
            return TaskResult(**task_dict)
            
        except Exception:
            return None
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update task status in Redis.
        
        Args:
            task_id: Task identifier
            status: New status
            completed_at: Optional completion timestamp
            
        Returns:
            True if successful, False otherwise
        """
        try:
            task = self.get_task(task_id)
            if not task:
                return False
                
            task.status = status
            if completed_at:
                task.completed_at = completed_at
            elif status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.utcnow()
                
            return self.store_task(task)
            
        except Exception:
            return False
    
    def list_tasks(self, limit: int = 10, offset: int = 0) -> List[TaskResult]:
        """
        List tasks with pagination.
        
        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of TaskResult objects
        """
        try:
            # Get task IDs sorted by timestamp (newest first)
            task_ids = self.redis_client.zrevrange("tasks_by_time", offset, offset + limit - 1)
            
            tasks = []
            for task_id in task_ids:
                task = self.get_task(task_id)
                if task:
                    tasks.append(task)
                    
            return tasks
            
        except Exception:
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from Redis.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"task:{task_id}"
            self.redis_client.delete(key)
            self.redis_client.zrem("tasks_by_time", task_id)
            return True
            
        except Exception:
            return False
    
    def get_task_count(self) -> int:
        """
        Get total number of tasks.
        
        Returns:
            Total count of tasks
        """
        try:
            return self.redis_client.zcard("tasks_by_time")
        except Exception:
            return 0


# Factory function for creating storage instances
def create_task_storage(storage_type: str = "redis", **kwargs) -> ITaskStorage:
    """
    Create a task storage instance.
    
    Args:
        storage_type: Type of storage (currently only "redis")
        **kwargs: Storage-specific parameters
        
    Returns:
        ITaskStorage implementation
        
    Raises:
        ValueError: If storage type is not supported
    """
    if storage_type == "redis":
        return RedisTaskStorage(**kwargs)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")

# Global storage instance
task_storage = create_task_storage("redis")
