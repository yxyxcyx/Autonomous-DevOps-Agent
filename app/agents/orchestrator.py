"""LangGraph orchestrator for the DevOps agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
import structlog
from typing import Dict, Any

from app.agents.state import AgentState, create_initial_state
from app.agents.nodes import (
    ManagerNode,
    CoderNode,
    ReviewerNode,
    TestRunnerNode
)

logger = structlog.get_logger()


class DevOpsAgentOrchestrator:
    """
    Orchestrates the bug-fixing workflow using LangGraph.
    Manages state transitions and coordinates between different agent nodes.
    """
    
    def __init__(self):
        """Initialize the orchestrator with agent nodes and graph."""
        self.manager_node = ManagerNode()
        self.coder_node = CoderNode()
        self.reviewer_node = ReviewerNode()
        self.test_runner_node = TestRunnerNode()
        
        # Build the state graph
        self.graph = self._build_graph()
        self.memory = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.memory)
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        Flow:
        1. Manager analyzes the bug
        2. Coder writes a fix
        3. Reviewer validates the fix
        4. TestRunner executes tests in sandbox
        5. Loop back to Coder if tests fail (up to max_attempts)
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("manager", self.manager_node.process)
        workflow.add_node("coder", self.coder_node.process)
        workflow.add_node("reviewer", self.reviewer_node.process)
        workflow.add_node("test_runner", self.test_runner_node.process)
        
        # Define edges
        workflow.set_entry_point("manager")
        
        # Manager -> Coder (always)
        workflow.add_edge("manager", "coder")
        
        # Coder -> Reviewer (always)
        workflow.add_edge("coder", "reviewer")
        
        # Reviewer -> Test Runner or END
        workflow.add_conditional_edges(
            "reviewer",
            self._reviewer_decision,
            {
                "test": "test_runner",
                "reject": "coder",
                "end": END
            }
        )
        
        # Test Runner -> Coder or END
        workflow.add_conditional_edges(
            "test_runner",
            self._test_runner_decision,
            {
                "retry": "coder",
                "success": END,
                "failure": END
            }
        )
        
        return workflow
    
    def _reviewer_decision(self, state: AgentState) -> str:
        """
        Decide next step after code review.
        
        Returns:
            - "test": Code approved, run tests
            - "reject": Code rejected, back to coder
            - "end": Critical issue or max attempts reached
        """
        if state.get("needs_human_review"):
            logger.info("Human review required, ending workflow")
            return "end"
        
        review_feedback = state.get("review_feedback", "")
        
        if "approved" in review_feedback.lower():
            logger.info("Code review passed, proceeding to tests")
            return "test"
        elif "rejected" in review_feedback.lower():
            # Stop only after exhausting all configured attempts
            if state.get("attempts", 0) >= state.get("max_attempts", 3):
                logger.warning("Max attempts reached via Reviewer rejection")
                return "end"
            logger.info("Code review failed, returning to coder")
            return "reject"
        else:
            # Default to testing if review is inconclusive
            return "test"
    
    def _test_runner_decision(self, state: AgentState) -> str:
        """
        Decide next step after running tests.
        
        Returns:
            - "retry": Tests failed, try again
            - "success": Tests passed, fix complete
            - "failure": Max attempts or critical failure
        """
        test_results = state.get("test_results", [])
        
        if not test_results:
            logger.error("No test results found")
            return "failure"
        
        latest_result = test_results[-1]
        
        if latest_result.get("success"):
            logger.info("Tests passed! Bug fix successful")
            return "success"
        
        attempts = state.get("attempts", 0)
        max_attempts = state.get("max_attempts", 3)
        
        if attempts < max_attempts:
            logger.info(f"Tests failed, retrying (attempt {attempts + 1}/{max_attempts})")
            return "retry"
        else:
            logger.warning("Max attempts reached, marking as failure")
            return "failure"
    
    async def execute_fix(self, task_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the bug fix workflow.
        
        Args:
            task_id: Unique task identifier
            request: Bug fix request details
            
        Returns:
            Final state with results
        """
        try:
            # Create initial state
            initial_state = create_initial_state(task_id, request)
            
            logger.info(
                "Starting bug fix workflow",
                task_id=task_id,
                bug=request.get("issue_description", "")[:100]
            )
            
            # Run the graph with memory checkpoint
            config = {"configurable": {"thread_id": task_id}}
            
            # Stream execution for real-time updates
            async for event in self.app.astream(initial_state, config=config):
                for node_name, node_state in event.items():
                    logger.info(
                        f"Node {node_name} completed",
                        current_step=node_state.get("current_step"),
                        attempts=node_state.get("attempts")
                    )
            
            # Get final state
            final_state = await self.app.aget_state(config)
            
            logger.info(
                "Bug fix workflow completed",
                task_id=task_id,
                status=final_state.values.get("final_status"),
                attempts=final_state.values.get("attempts")
            )
            
            return self._format_result(final_state.values)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "patches": [],
                "test_results": []
            }
    
    def _format_result(self, state: AgentState) -> Dict[str, Any]:
        """Format the final state into a result dictionary."""
        return {
            "task_id": state.get("task_id"),
            "status": state.get("final_status", "unknown"),
            "analysis": state.get("analysis"),
            "final_patch": state.get("final_patch"),
            "patches": state.get("patches", []),
            "test_results": state.get("test_results", []),
            "attempts": state.get("attempts", 0),
            "error_messages": state.get("error_messages", []),
            "execution_history": state.get("execution_history", []),
            "total_tokens_used": state.get("total_tokens_used", 0),
            "needs_human_review": state.get("needs_human_review", False)
        }
