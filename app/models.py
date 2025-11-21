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


class AgentState(BaseModel):
    """State model for the agent execution."""
    bug_description: str
    repository_url: str
    branch: str
    test_command: Optional[str]
    current_step: str = "initialize"
    attempts: int = 0
    max_attempts: int = 3
    patches: List[Dict[str, Any]] = []
    test_results: List[Dict[str, Any]] = []
    final_patch: Optional[Dict[str, Any]] = None
    error_messages: List[str] = []
    logs: List[str] = []
