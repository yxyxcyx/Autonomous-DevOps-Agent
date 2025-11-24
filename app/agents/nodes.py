"""Agent nodes for the bug fixing workflow."""

import json
import time
from typing import Dict, Any, Optional, List
import structlog

from app.agents.state import AgentState
from app.interfaces.llm import LLMMessage
from app.providers.gemini_llm import GeminiLLMProvider
from app.repo_handler import RepositoryHandler
from app.sandbox.executor import DockerSandboxExecutor
from app.sandbox.simple_executor import SimpleExecutor
from app.config import settings
from app.constants import DEFAULT_LLM_MODEL, MAX_LOG_DISPLAY_LENGTH

logger = structlog.get_logger()


class BaseNode:
    """Base class for all agent nodes."""
    
    def __init__(self):
        """Initialize the LLM provider with centralized configuration."""
        self.llm = GeminiLLMProvider(
            model=DEFAULT_LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.GEMINI_API_KEY
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
    
    def __init__(self):
        super().__init__()
        self.repo_handler = RepositoryHandler()
    
    def process(self, state: AgentState) -> AgentState:
        """
        Analyze the bug and create an action plan.
        """
        logger.info("Manager: Analyzing bug", task_id=state["task_id"])
        
        state["current_step"] = "analysis"
        
        # Clone and analyze repository
        repo_context = ""
        repo_analysis = {}
        
        if state.get("repository_url"):
            logger.info("Cloning repository for analysis")
            success, repo_path, error = self.repo_handler.clone_repository(
                state["repository_url"],
                state.get("branch", "main")
            )
            
            if success:
                state["repo_path"] = repo_path  # Store for other nodes
                repo_analysis = self.repo_handler.analyze_repository(repo_path)
                
                # Search for relevant code based on bug description
                search_terms = state["bug_description"].split()[:5]  # Key words
                relevant_files = []
                
                for term in search_terms:
                    if len(term) > 3:  # Skip short words
                        search_results = self.repo_handler.search_code(
                            repo_path, term, max_results=10
                        )
                        for result in search_results:
                            if result["file"] not in relevant_files:
                                relevant_files.append(result["file"])
                
                # Build context from repository
                repo_context = f"""

Repository Analysis:
- Total files: {repo_analysis.get('file_count', 0)}
- Total lines: {repo_analysis.get('total_lines', 0)}
- Main languages: {', '.join(list(repo_analysis.get('languages', {}).keys())[:5])}
- Test files found: {len(repo_analysis.get('test_files', []))}

Potentially relevant files based on bug description:
{chr(10).join(f'- {f}' for f in relevant_files[:10])}

README excerpt:
{repo_analysis.get('readme_content', 'Not found')[:500]}
"""
                state["logs"].append(f"Repository cloned and analyzed: {repo_path}")
            else:
                state["error_messages"].append(f"Failed to clone repository: {error}")
                state["logs"].append("Warning: Proceeding without repository context")
        
        # Construct analysis prompt with real context
        prompt = f"""
You are a senior software engineer analyzing a bug report.

Bug Description:
{state["bug_description"]}

Repository: {state["repository_url"]}
Branch: {state["branch"]}
Language: {state["language"]}
Test Command: {state.get("test_command", "Not specified")}
{repo_context}

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
            messages: List[LLMMessage] = [
                LLMMessage(role="system", content="You are an expert bug analyzer."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm.generate_with_retry(messages)
            analysis_text = response.content

            token_count = response.tokens_used or self.llm.count_tokens(prompt + analysis_text)

            self.log_llm_call(
                state,
                prompt,
                analysis_text,
                token_count
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
    
    def __init__(self):
        super().__init__()
        self.repo_handler = RepositoryHandler()
    
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
        
        # Get actual code context if repository was cloned
        code_context = ""
        if state.get("repo_path"):
            # Parse affected files from analysis
            affected_files = []
            try:
                if state.get("analysis"):
                    # Extract affected files from analysis
                    for line in state["analysis"].split('\n'):
                        if "Affected Files:" in line:
                            files_str = line.split("Affected Files:")[1].strip()
                            affected_files = [f.strip() for f in files_str.split(',')]
                            break
            except:
                pass
            
            # Read actual code from affected files
            if affected_files:
                code_snippets = []
                for file_path in affected_files[:3]:  # Limit to 3 files
                    content = self.repo_handler.get_file_content(
                        state["repo_path"], file_path
                    )
                    if content:
                        code_snippets.append(f"\n=== {file_path} ===\n{content[:1000]}")
                
                if code_snippets:
                    code_context = f"\n\nActual code from repository:{chr(10).join(code_snippets)}"
        
        # Construct coding prompt with real code
        prompt = f"""
You are an expert programmer fixing a bug.

Bug Analysis:
{state.get("analysis", "No analysis available")}

{context}
{code_context}

Language: {state["language"]}
Repository: {state["repository_url"]}

Generate a complete, working code patch to fix this bug.
The code should be production-ready and include:
1. The fix implementation
2. Error handling
3. Comments explaining the fix

IMPORTANT: Base your fix on the actual code shown above, not assumptions.

Format your response as a JSON object with:
- filename: string (main file to patch)
- code: string (complete fixed code)
- dependencies: object (e.g., {{"requirements.txt": "package==version"}})
- explanation: string (what was fixed and why)
"""
        
        try:
            messages: List[LLMMessage] = [
                LLMMessage(role="system", content="You are an expert programmer who writes clean, secure code."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm.generate_with_retry(messages)
            code_text = response.content

            token_count = response.tokens_used or self.llm.count_tokens(prompt + code_text)

            self.log_llm_call(
                state,
                prompt[:MAX_LOG_DISPLAY_LENGTH],
                code_text[:MAX_LOG_DISPLAY_LENGTH],
                token_count
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
            messages: List[LLMMessage] = [
                LLMMessage(role="system", content="You are a meticulous code reviewer focused on security and quality."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm.generate_with_retry(messages)
            review_text = response.content

            token_count = response.tokens_used or self.llm.count_tokens(prompt + review_text)

            self.log_llm_call(
                state,
                prompt,
                review_text,
                token_count
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
        """Initialize with executor (Docker or simple fallback)."""
        super().__init__()
        try:
            # Try to use Docker sandbox
            self.executor = DockerSandboxExecutor()
            logger.info("Using Docker sandbox executor")
        except Exception as e:
            # Fall back to simple executor if Docker is not available
            logger.warning(f"Docker not available ({str(e)}), using simple executor")
            self.executor = SimpleExecutor()
        
        # Initialize repository executor for testing against real code
        from app.sandbox.repository_executor import RepositoryExecutor
        self.repo_executor = RepositoryExecutor()
    
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
        
        success = False
        stdout = ""
        stderr = ""
        
        try:
            # Check if we have a repository to test against
            if state.get("repo_path") and state.get("test_command"):
                # Test against actual repository
                logger.info("Testing patch against actual repository")
                
                # Prepare patch data
                patch_data = {
                    latest_patch["filename"]: latest_patch["code"]
                }
                
                # Add any additional files from the patch
                if latest_patch.get("files"):
                    patch_data.update(latest_patch["files"])
                
                success, stdout, stderr = self.repo_executor.execute_with_repository(
                    repo_path=state["repo_path"],
                    patch_data=patch_data,
                    test_command=state["test_command"],
                    language=state["language"]
                )
            else:
                # Fall back to isolated execution
                logger.info("No repository context, running isolated test")
                test_cmd = state.get("test_command")
                
                success, stdout, stderr = self.executor.execute(
                    code=latest_patch["code"],
                    language=state["language"],
                    test_command=test_cmd,
                    files=latest_patch.get("files"),
                    dependencies=latest_patch.get("dependencies")
                )
            
            # Record test results
            from app.constants import MAX_STDOUT_DISPLAY_LENGTH, MAX_STDERR_DISPLAY_LENGTH
            test_result = {
                "attempt": state["attempts"],
                "success": success,
                "stdout": stdout[:MAX_STDOUT_DISPLAY_LENGTH],  # Use constant
                "stderr": stderr[:MAX_STDERR_DISPLAY_LENGTH],  # Use constant
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
