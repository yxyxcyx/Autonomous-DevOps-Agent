"""Storage interface for abstracting storage backends."""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models import TaskResult, TaskStatus


class ITaskStorage(ABC):
    """Abstract interface for task storage."""
    
    @abstractmethod
    def store_task(self, task_result: TaskResult) -> bool:
        """
        Store a task result.
        
        Args:
            task_result: Task result to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskResult]:
        """
        Retrieve a task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskResult if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus, 
        completed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update task status.
        
        Args:
            task_id: Task identifier
            status: New status
            completed_at: Completion timestamp
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_tasks(self, limit: int = 10, offset: int = 0) -> List[TaskResult]:
        """
        List tasks with pagination.
        
        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of TaskResult objects
        """
        pass
    
    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_task_count(self) -> int:
        """
        Get total number of tasks.
        
        Returns:
            Total count of tasks
        """
        pass


class ICacheStorage(ABC):
    """Abstract interface for cache storage."""
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a cache value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a cached value.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        pass
