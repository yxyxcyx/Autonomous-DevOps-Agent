"""Redis-based task storage for the DevOps Agent."""

import json
import redis
from typing import Dict, Optional, List, Any
from datetime import datetime

from app.config import settings
from app.models import TaskResult, TaskStatus
from app.interfaces.storage import ITaskStorage
from app.logging_config import get_logger
from app.utils import retry_on_exception

logger = get_logger(__name__)


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
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        
    @retry_on_exception(max_retries=3, delay=0.5)
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
            data = task_result.dict()
            
            # Convert datetime objects to ISO format for JSON serialization
            if data.get('created_at'):
                data['created_at'] = data['created_at'].isoformat()
            if data.get('completed_at'):
                data['completed_at'] = data['completed_at'].isoformat()
                
            self.redis_client.setex(
                key, 
                settings.TASK_STORAGE_TTL, 
                json.dumps(data)
            )
            
            # Also add to task list for pagination (will update score if exists)
            self.redis_client.zadd(
                "tasks_by_time",
                {task_result.task_id: datetime.utcnow().timestamp()}
            )
            
            logger.info("Task stored in Redis", task_id=task_result.task_id)
            return True
            
        except Exception as e:
            logger.error("Failed to store task in Redis", task_id=task_result.task_id, error=str(e))
            return False
    
    @retry_on_exception(max_retries=3, delay=0.5)
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
            
        except Exception as e:
            logger.error("Failed to retrieve task from Redis", task_id=task_id, error=str(e))
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
            
        except Exception as e:
            logger.error("Failed to update task status", task_id=task_id, error=str(e))
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
            
        except Exception as e:
            logger.error("Failed to list tasks from Redis", error=str(e))
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
            
            logger.info("Task deleted from Redis", task_id=task_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete task from Redis", task_id=task_id, error=str(e))
            return False
    
    def get_task_count(self) -> int:
        """
        Get total number of tasks.
        
        Returns:
            Total count of tasks
        """
        try:
            return self.redis_client.zcard("tasks_by_time")
        except Exception as e:
            logger.error("Failed to get task count", error=str(e))
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
