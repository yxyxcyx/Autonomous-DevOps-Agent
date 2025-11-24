"""Data models for the DevOps Agent API."""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BugFixRequest(BaseModel):
    """Request model for bug fix tasks."""
    repository_url: str = Field(..., description="Git repository URL")
    branch: str = Field("main", description="Target branch")
    issue_description: str = Field(..., description="Description of the bug")
    test_command: Optional[str] = Field(None, description="Command to run tests")
    language: str = Field("python", description="Programming language")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str
    status: TaskStatus
    created_at: datetime
    message: str


class TaskResult(BaseModel):
    """Result model for completed tasks."""
    task_id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    execution_steps: List[Dict[str, Any]] = []


# AgentState removed - Using TypedDict definition in agents/state.py for LangGraph compatibility
