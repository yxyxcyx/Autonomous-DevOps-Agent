"""API client for backend communication."""

import requests
import streamlit as st
from typing import Dict, Any, Optional, List
from app.constants import DEFAULT_UI_API_BASE_URL, HTTP_OK
import os


class APIClient:
    """Client for communicating with the backend API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for the API (uses environment variable if not provided)
        """
        self.base_url = base_url or os.getenv("API_BASE_URL", DEFAULT_UI_API_BASE_URL)
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def check_health(self) -> bool:
        """
        Check if the API is healthy.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/",
                timeout=2
            )
            return response.status_code == HTTP_OK
        except Exception as e:
            st.error(f"API health check failed: {str(e)}")
            return False
    
    def submit_bug_fix(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submit a bug fix request.
        
        Args:
            data: Bug fix request data
            
        Returns:
            Response data if successful, None otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/fix_bug",
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error(" Cannot connect to the API. Please ensure the backend is running.")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. The API might be overloaded.")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task data if found, None otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                timeout=10
            )
            
            if response.status_code == HTTP_OK:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                st.error(f"Error fetching task: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching task: {str(e)}")
            return None
    
    def get_all_tasks(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all tasks with pagination.
        
        Args:
            limit: Maximum number of tasks to retrieve
            offset: Number of tasks to skip
            status: Optional status filter
            
        Returns:
            Dictionary with tasks and metadata
        """
        try:
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if status:
                params["status"] = status
            
            response = self.session.get(
                f"{self.base_url}/api/v1/tasks",
                params=params,
                timeout=10
            )
            
            if response.status_code == HTTP_OK:
                return response.json()
            else:
                st.error(f"Error fetching tasks: {response.status_code}")
                return {"tasks": [], "total": 0}
                
        except Exception as e:
            st.error(f"Error fetching tasks: {str(e)}")
            return {"tasks": [], "total": 0}
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                timeout=10
            )
            
            if response.status_code == HTTP_OK:
                st.success(f"Task {task_id} cancelled successfully")
                return True
            elif response.status_code == 404:
                st.error(f"Task {task_id} not found")
                return False
            elif response.status_code == 409:
                st.warning("Task is already completed and cannot be cancelled")
                return False
            else:
                st.error(f"Failed to cancel task: {response.status_code}")
                return False
                
        except Exception as e:
            st.error(f"Error cancelling task: {str(e)}")
            return False
    
    def get_api_docs(self) -> Optional[str]:
        """
        Get API documentation URL.
        
        Returns:
            Documentation URL if available
        """
        return f"{self.base_url}/docs"
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection and return detailed status.
        
        Returns:
            Dictionary with connection status and details
        """
        try:
            response = self.session.get(
                f"{self.base_url}/",
                timeout=2
            )
            
            if response.status_code == HTTP_OK:
                data = response.json()
                return {
                    "connected": True,
                    "status": data.get("status", "unknown"),
                    "version": data.get("version", "unknown"),
                    "components": data.get("components", {})
                }
            else:
                return {
                    "connected": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {
                "connected": False,
                "error": type(e).__name__,
                "message": str(e)
            }
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
