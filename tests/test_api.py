"""Tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.models import TaskStatus

client = TestClient(app)


def test_root_endpoint():
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Autonomous DevOps Agent"


def test_fix_bug_endpoint():
    """Test submitting a bug fix request."""
    with patch("app.main.process_bug_fix.apply_async") as mock_task:
        # Mock the Celery task
        mock_task.return_value = MagicMock(id="test-task-123")
        
        request_data = {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "issue_description": "Test bug description",
            "test_command": "pytest",
            "language": "python"
        }
        
        response = client.post("/api/v1/fix_bug", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert "message" in data
        
        # Verify Celery task was called
        mock_task.assert_called_once()


def test_get_task_status():
    """Test retrieving task status."""
    # First, create a task
    with patch("app.main.process_bug_fix.apply_async") as mock_task:
        mock_task.return_value = MagicMock(id="test-task-456")
        
        request_data = {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "issue_description": "Test bug",
            "language": "python"
        }
        
        response = client.post("/api/v1/fix_bug", json=request_data)
        task_id = response.json()["task_id"]
    
    # Now get its status
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_result.return_value = MagicMock(
            state="SUCCESS",
            result={"status": "completed", "patches": []}
        )
        
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] in [s.value for s in TaskStatus]


def test_get_nonexistent_task():
    """Test retrieving a non-existent task."""
    response = client.get("/api/v1/tasks/nonexistent-task-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_cancel_task():
    """Test cancelling a running task."""
    # First, create a task
    with patch("app.main.process_bug_fix.apply_async") as mock_task:
        mock_task.return_value = MagicMock(id="test-task-789")
        
        request_data = {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "issue_description": "Test bug",
            "language": "python"
        }
        
        response = client.post("/api/v1/fix_bug", json=request_data)
        task_id = response.json()["task_id"]
    
    # Cancel the task
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_revoke = MagicMock()
        mock_result.return_value = MagicMock(revoke=mock_revoke)
        
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert "cancelled successfully" in response.json()["message"]
        
        # Verify revoke was called
        mock_revoke.assert_called_once_with(terminate=True)


def test_list_tasks():
    """Test listing all tasks with pagination."""
    response = client.get("/api/v1/tasks?limit=5&offset=0")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "limit" in data
    assert data["limit"] == 5
    assert "offset" in data
    assert data["offset"] == 0
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
