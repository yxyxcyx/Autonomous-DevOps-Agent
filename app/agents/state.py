"""State management for the LangGraph agent."""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
import operator


class AgentState(TypedDict):
    """
    The state that flows through the agent graph.
    Each node can read and update this state.
    """
    # Core task information
    task_id: str
    bug_description: str
    repository_url: str
    branch: str
    test_command: Optional[str]
    language: str
    
    # Execution tracking
    current_step: str
    attempts: int
    max_attempts: int
    
    # Generated artifacts
    analysis: Optional[str]  # Bug analysis from Manager
    proposed_fix: Optional[str]  # Code fix from Coder
    review_feedback: Optional[str]  # Feedback from Reviewer
    
    # Patches and test results
    patches: Annotated[List[Dict[str, Any]], operator.add]
    test_results: Annotated[List[Dict[str, Any]], operator.add]
    
    # Final outputs
    final_patch: Optional[Dict[str, Any]]
    final_status: Optional[str]  # "success", "failed", "timeout"
    
    # Logging and debugging
    error_messages: Annotated[List[str], operator.add]
    logs: Annotated[List[str], operator.add]
    execution_history: Annotated[List[Dict[str, Any]], operator.add]
    
    # LLM interaction history
    llm_calls: Annotated[List[Dict[str, Any]], operator.add]
    total_tokens_used: int
    
    # Flags for control flow
    should_continue: bool
    needs_human_review: bool
    is_security_issue: bool


def create_initial_state(task_id: str, request: Dict[str, Any]) -> AgentState:
    """Create the initial agent state from a bug fix request."""
    return AgentState(
        task_id=task_id,
        bug_description=request.get("issue_description", ""),
        repository_url=request.get("repository_url", ""),
        branch=request.get("branch", "main"),
        test_command=request.get("test_command"),
        language=request.get("language", "python"),
        current_step="initialize",
        attempts=0,
        max_attempts=3,
        analysis=None,
        proposed_fix=None,
        review_feedback=None,
        patches=[],
        test_results=[],
        final_patch=None,
        final_status=None,
        error_messages=[],
        logs=[],
        execution_history=[],
        llm_calls=[],
        total_tokens_used=0,
        should_continue=True,
        needs_human_review=False,
        is_security_issue=False
    )
