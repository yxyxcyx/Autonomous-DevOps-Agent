"""Agent nodes for the DevOps workflow."""

from typing import Dict, Any
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import json
import time

from app.agents.state import AgentState
from app.sandbox.executor import DockerSandboxExecutor
from app.config import settings

logger = structlog.get_logger()


class BaseNode:
    """Base class for all agent nodes."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.GEMINI_API_KEY
        )
    
    def log_llm_call(self, state: AgentState, prompt: str, response: str, tokens: int):
        """Log LLM interaction to state."""
        state["llm_calls"].append({
            "timestamp": time.time(),
            "node": self.__class__.__name__,
            "prompt": prompt[:500],  # Truncate for storage
            "response": response[:500],
            "tokens": tokens
        })
        state["total_tokens_used"] += tokens
    
    def update_execution_history(self, state: AgentState, action: str, result: Any):
        """Update execution history in state."""
        state["execution_history"].append({
            "timestamp": time.time(),
            "step": state["current_step"],
            "action": action,
            "result": result
        })


class ManagerNode(BaseNode):
    """
    Manager node: Analyzes bugs and creates action plans.
    """
    
    def process(self, state: AgentState) -> AgentState:
        """
        Analyze the bug and create an action plan.
        """
        logger.info("Manager: Analyzing bug", task_id=state["task_id"])
        
        state["current_step"] = "analysis"
        
        # Construct analysis prompt
        prompt = f"""
You are a senior software engineer analyzing a bug report.

Bug Description:
{state["bug_description"]}

Repository: {state["repository_url"]}
Branch: {state["branch"]}
Language: {state["language"]}
Test Command: {state.get("test_command", "Not specified")}

Please analyze this bug and provide:
1. Root cause analysis
2. Potential security implications
3. Suggested fix approach
4. Files that likely need modification
5. Test scenarios to validate the fix

Format your response as a JSON object with these keys:
- root_cause: string
- security_risk: boolean
- fix_approach: string
- affected_files: list of strings
- test_scenarios: list of strings
"""
        
        try:
            # Call LLM for analysis
            messages = [
                SystemMessage(content="You are an expert bug analyzer."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            analysis_text = response.content
            
            # Log the LLM call
            self.log_llm_call(
                state,
                prompt,
                analysis_text,
                response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            )
            
            # Parse JSON response
            try:
                analysis_data = json.loads(analysis_text)
                state["is_security_issue"] = analysis_data.get("security_risk", False)
                
                # Format analysis for next steps
                state["analysis"] = f"""
Root Cause: {analysis_data.get('root_cause', 'Unknown')}
Security Risk: {'Yes' if analysis_data.get('security_risk') else 'No'}
Fix Approach: {analysis_data.get('fix_approach', 'Standard debugging')}
Affected Files: {', '.join(analysis_data.get('affected_files', []))}
Test Scenarios: {', '.join(analysis_data.get('test_scenarios', []))}
"""
            except json.JSONDecodeError:
                # If JSON parsing fails, use raw text
                state["analysis"] = analysis_text
            
            state["logs"].append(f"Manager: Bug analysis completed")
            self.update_execution_history(state, "analyze_bug", state["analysis"])
            
        except Exception as e:
            logger.error(f"Manager analysis failed: {str(e)}")
            state["error_messages"].append(f"Analysis error: {str(e)}")
            state["analysis"] = "Failed to analyze bug"
        
        return state


class CoderNode(BaseNode):
    """
    Coder node: Writes code to fix bugs.
    """
    
    def process(self, state: AgentState) -> AgentState:
        """
        Generate code fix based on analysis and feedback.
        """
        logger.info("Coder: Generating fix", task_id=state["task_id"])
        
        state["current_step"] = "coding"
        state["attempts"] += 1
        
        # Build context from previous attempts
        context = ""
        if state.get("test_results"):
            last_test = state["test_results"][-1]
            if not last_test.get("success"):
                context = f"\nPrevious attempt failed with error:\n{last_test.get('error', 'Unknown error')}\n"
        
        if state.get("review_feedback"):
            context += f"\nReviewer feedback:\n{state['review_feedback']}\n"
        
        # Construct coding prompt
        prompt = f"""
You are an expert programmer fixing a bug.

Bug Analysis:
{state.get("analysis", "No analysis available")}

{context}

Language: {state["language"]}
Repository: {state["repository_url"]}

Generate a complete, working code patch to fix this bug.
The code should be production-ready and include:
1. The fix implementation
2. Error handling
3. Comments explaining the fix

Format your response as a JSON object with:
- filename: string (main file to patch)
- code: string (complete fixed code)
- dependencies: object (e.g., {{"requirements.txt": "package==version"}})
- explanation: string (what was fixed and why)
"""
        
        try:
            messages = [
                SystemMessage(content="You are an expert programmer who writes clean, secure code."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            code_text = response.content
            
            # Log the LLM call
            self.log_llm_call(
                state,
                prompt,
                code_text,
                response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            )
            
            # Parse JSON response
            try:
                code_data = json.loads(code_text)
                
                # Create patch object
                patch = {
                    "attempt": state["attempts"],
                    "timestamp": time.time(),
                    "filename": code_data.get("filename", "main.py"),
                    "code": code_data.get("code", ""),
                    "dependencies": code_data.get("dependencies", {}),
                    "explanation": code_data.get("explanation", "")
                }
                
                state["patches"].append(patch)
                state["proposed_fix"] = code_data.get("code", "")
                
            except json.JSONDecodeError:
                # Fallback: treat entire response as code
                patch = {
                    "attempt": state["attempts"],
                    "timestamp": time.time(),
                    "filename": f"fix.{state['language']}",
                    "code": code_text,
                    "dependencies": {},
                    "explanation": "Generated fix"
                }
                state["patches"].append(patch)
                state["proposed_fix"] = code_text
            
            state["logs"].append(f"Coder: Fix generated (attempt {state['attempts']})")
            self.update_execution_history(state, "generate_fix", patch)
            
        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            state["error_messages"].append(f"Code generation error: {str(e)}")
            state["proposed_fix"] = None
        
        return state


class ReviewerNode(BaseNode):
    """
    Reviewer node: Reviews code for quality and security.
    """
    
    def process(self, state: AgentState) -> AgentState:
        """
        Review the proposed code fix.
        """
        logger.info("Reviewer: Reviewing code", task_id=state["task_id"])
        
        state["current_step"] = "review"
        
        if not state.get("proposed_fix"):
            state["review_feedback"] = "No code to review"
            state["logs"].append("Reviewer: No code provided")
            return state
        
        # Get latest patch
        latest_patch = state["patches"][-1] if state["patches"] else None
        
        if not latest_patch:
            state["review_feedback"] = "No patch available"
            return state
        
        # Construct review prompt
        prompt = f"""
You are a senior code reviewer performing a security and quality review.

Original Bug:
{state["bug_description"]}

Proposed Fix:
```{state["language"]}
{latest_patch.get("code", "")}
```

Explanation: {latest_patch.get("explanation", "None provided")}

Review this code for:
1. Correctness: Does it fix the bug?
2. Security: Any vulnerabilities introduced?
3. Performance: Any performance issues?
4. Best Practices: Does it follow language conventions?
5. Edge Cases: Are edge cases handled?

Provide your review as a JSON object with:
- status: "approved" or "rejected"
- security_issues: list of security concerns
- quality_issues: list of quality concerns
- suggestions: list of improvement suggestions
- risk_level: "low", "medium", or "high"
"""
        
        try:
            messages = [
                SystemMessage(content="You are a meticulous code reviewer focused on security and quality."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            review_text = response.content
            
            # Log the LLM call
            self.log_llm_call(
                state,
                prompt,
                review_text,
                response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            )
            
            # Parse review response
            try:
                review_data = json.loads(review_text)
                
                # Check if human review is needed
                if review_data.get("risk_level") == "high" or review_data.get("security_issues"):
                    state["needs_human_review"] = True
                
                # Format feedback
                status = review_data.get("status", "rejected")
                state["review_feedback"] = f"""
Status: {status}
Risk Level: {review_data.get("risk_level", "unknown")}
Security Issues: {', '.join(review_data.get("security_issues", [])) or "None"}
Quality Issues: {', '.join(review_data.get("quality_issues", [])) or "None"}
Suggestions: {', '.join(review_data.get("suggestions", [])) or "None"}
"""
                
            except json.JSONDecodeError:
                # Use raw text as feedback
                state["review_feedback"] = review_text
            
            state["logs"].append(f"Reviewer: Code review completed")
            self.update_execution_history(state, "review_code", state["review_feedback"])
            
        except Exception as e:
            logger.error(f"Code review failed: {str(e)}")
            state["error_messages"].append(f"Review error: {str(e)}")
            state["review_feedback"] = "Review failed"
        
        return state


class TestRunnerNode(BaseNode):
    """
    TestRunner node: Executes code in Docker sandbox.
    """
    
    def __init__(self):
        """Initialize with Docker executor."""
        super().__init__()
        self.executor = DockerSandboxExecutor()
    
    def process(self, state: AgentState) -> AgentState:
        """
        Run tests in sandboxed environment.
        """
        logger.info("TestRunner: Executing tests", task_id=state["task_id"])
        
        state["current_step"] = "testing"
        
        # Get latest patch
        latest_patch = state["patches"][-1] if state["patches"] else None
        
        if not latest_patch:
            state["test_results"].append({
                "success": False,
                "error": "No patch to test",
                "timestamp": time.time()
            })
            return state
        
        try:
            # Execute code in sandbox
            success, stdout, stderr = self.executor.execute_code(
                code=latest_patch.get("code", ""),
                language=state["language"],
                test_command=state.get("test_command"),
                dependencies=latest_patch.get("dependencies", {}),
                files={}  # Additional files if needed
            )
            
            # Record test results
            test_result = {
                "attempt": state["attempts"],
                "success": success,
                "stdout": stdout[:1000],  # Truncate for storage
                "stderr": stderr[:1000],
                "error": stderr if not success else None,
                "timestamp": time.time()
            }
            
            state["test_results"].append(test_result)
            
            if success:
                state["final_patch"] = latest_patch
                state["final_status"] = "success"
                state["logs"].append("TestRunner: Tests passed successfully!")
            else:
                state["logs"].append(f"TestRunner: Tests failed - {stderr[:200]}")
            
            self.update_execution_history(state, "run_tests", test_result)
            
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            state["error_messages"].append(f"Test execution error: {str(e)}")
            state["test_results"].append({
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
        
        # Check if we've exhausted attempts
        if state["attempts"] >= state["max_attempts"] and not state.get("final_status"):
            state["final_status"] = "failed"
            state["logs"].append("TestRunner: Max attempts reached")
        
        return state
