"""Streamlit UI for the Autonomous DevOps Agent."""

import streamlit as st
import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Configuration
API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 2000  # 2 seconds

# Page configuration
st.set_page_config(
    page_title="Autonomous DevOps Agent",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .step-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    .step-planning {
        background-color: #e3f2fd;
        border-color: #2196f3;
    }
    .step-coding {
        background-color: #fff3e0;
        border-color: #ff9800;
    }
    .step-reviewing {
        background-color: #f3e5f5;
        border-color: #9c27b0;
    }
    .step-testing {
        background-color: #e8f5e9;
        border-color: #4caf50;
    }
    .step-complete {
        background-color: #c8e6c9;
        border-color: #43a047;
    }
    .step-failed {
        background-color: #ffcdd2;
        border-color: #e53935;
    }
    .code-block {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-pending {
        background-color: #fff3e0;
        color: #f57c00;
    }
    .status-processing {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .status-success {
        background-color: #e8f5e9;
        color: #388e3c;
    }
    .status-failed {
        background-color: #ffebee;
        color: #d32f2f;
    }
</style>
""", unsafe_allow_html=True)


def get_api_health() -> bool:
    """Check if the API is accessible."""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def submit_bug_fix(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Submit a bug fix request to the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/fix_bug",
            json=data,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get the status of a task."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/tasks/{task_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching task: {str(e)}")
        return None


def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all tasks."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/tasks?limit=50",
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("tasks", [])
        return []
    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
        return []


def render_status_badge(status: str) -> str:
    """Render a status badge."""
    badge_class = f"status-{status.lower()}"
    return f'<span class="status-badge {badge_class}">{status.upper()}</span>'


def render_progress_bar(state: Dict[str, Any]) -> None:
    """Render agent progress visualization."""
    current_step = state.get("current_step", "initialize")
    attempts = state.get("attempts", 0)
    max_attempts = state.get("max_attempts", 3)
    
    steps = ["analysis", "coding", "review", "testing"]
    step_names = {
        "initialize": "Initializing",
        "analysis": "Analyzing Bug",
        "coding": "Generating Fix",
        "review": "Reviewing Code",
        "testing": "Running Tests"
    }
    
    # Progress calculation
    if current_step == "initialize":
        progress = 0
    elif current_step == "analysis":
        progress = 25
    elif current_step == "coding":
        progress = 40
    elif current_step == "review":
        progress = 65
    elif current_step == "testing":
        progress = 85
    else:
        progress = 100
    
    # Display progress
    st.progress(progress / 100)
    
    # Current step indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"### Current Step: {step_names.get(current_step, current_step.title())}")
        st.markdown(f"**Attempt {attempts} of {max_attempts}**")


def render_agent_thinking(logs: List[str], execution_history: List[Dict[str, Any]]) -> None:
    """Render the agent's thought process."""
    st.markdown("### Agent Thought Process")
    
    if not logs and not execution_history:
        st.info("Waiting for agent to start...")
        return
    
    # Create timeline
    for i, log in enumerate(logs[-10:]):  # Show last 10 logs
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine step type based on log content
        step_class = "step-box"
        if "Manager" in log or "Analyzing" in log:
            step_class += " step-planning"
            icon = "[PLAN]"
        elif "Coder" in log or "Generating" in log:
            step_class += " step-coding"
            icon = "[CODE]"
        elif "Reviewer" in log or "Review" in log:
            step_class += " step-reviewing"
            icon = "[REVIEW]"
        elif "TestRunner" in log or "Test" in log:
            step_class += " step-testing"
            icon = "[TEST]"
        elif "passed" in log.lower() or "success" in log.lower():
            step_class += " step-complete"
            icon = "[PASS]"
        elif "failed" in log.lower() or "error" in log.lower():
            step_class += " step-failed"
            icon = "[FAIL]"
        else:
            icon = "[INFO]"
        
        st.markdown(f"""
        <div class="{step_class}">
            <strong>{icon} {timestamp}</strong><br>
            {log}
        </div>
        """, unsafe_allow_html=True)


def render_code_diff(patches: List[Dict[str, Any]]) -> None:
    """Render code patches."""
    st.markdown("### Generated Patches")
    
    if not patches:
        st.info("No patches generated yet...")
        return
    
    for i, patch in enumerate(patches):
        with st.expander(f"Attempt {patch.get('attempt', i+1)} - {patch.get('filename', 'unknown')}"):
            st.markdown(f"**Explanation:** {patch.get('explanation', 'N/A')}")
            
            # Code display
            code = patch.get('code', '')
            st.code(code, language=patch.get('language', 'python'))
            
            # Dependencies
            if patch.get('dependencies'):
                st.markdown("**Dependencies:**")
                for dep_file, content in patch['dependencies'].items():
                    st.text(f"{dep_file}:\n{content}")


def render_test_results(test_results: List[Dict[str, Any]]) -> None:
    """Render test execution results."""
    st.markdown("### Test Results")
    
    if not test_results:
        st.info("No test results yet...")
        return
    
    for i, result in enumerate(test_results):
        success = result.get('success', False)
        attempt = result.get('attempt', i+1)
        
        status_icon = "[PASS]" if success else "[FAIL]"
        status_text = "PASSED" if success else "FAILED"
        
        with st.expander(f"{status_icon} Attempt {attempt} - {status_text}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Standard Output:**")
                stdout = result.get('stdout', 'No output')
                st.code(stdout, language='text')
            
            with col2:
                st.markdown("**Standard Error:**")
                stderr = result.get('stderr', 'No errors')
                if stderr and stderr != 'No errors':
                    st.code(stderr, language='text')
                else:
                    st.success("No errors!")


def render_metrics(result: Dict[str, Any]) -> None:
    """Render metrics dashboard."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Attempts", result.get('attempts', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        patches_count = len(result.get('patches', []))
        st.metric("Patches Generated", patches_count)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        tokens = result.get('total_tokens_used', 0)
        st.metric("LLM Tokens Used", f"{tokens:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        test_results = result.get('test_results', [])
        success_rate = sum(1 for t in test_results if t.get('success')) / len(test_results) * 100 if test_results else 0
        st.metric("Test Success Rate", f"{success_rate:.0f}%")
        st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application."""
    
    # Header
    st.markdown('<h1 class="main-header">Autonomous DevOps Agent</h1>', unsafe_allow_html=True)
    st.markdown("AI-powered system for automated bug fixing and security patching")
    
    # Check API health
    if not get_api_health():
        st.error("[WARNING] Cannot connect to API. Please ensure the backend is running at " + API_BASE_URL)
        st.code("docker-compose up -d", language="bash")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("## Navigation")
        page = st.radio(
            "Select View",
            ["Submit Bug Fix", "Task Monitor", "Task History"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### API Status")
        st.success("Connected")
        
        st.markdown("---")
        st.markdown("### Quick Actions")
        if st.button("Refresh Data"):
            st.rerun()
    
    # Main content
    if page == "Submit Bug Fix":
        render_submit_page()
    elif page == "Task Monitor":
        render_monitor_page()
    else:
        render_history_page()


def render_submit_page():
    """Render the bug fix submission page."""
    st.markdown("## Submit New Bug Fix Request")
    
    with st.form("bug_fix_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            repository_url = st.text_input(
                "Repository URL",
                value="https://github.com/example/repo",
                help="Git repository URL"
            )
            
            branch = st.text_input(
                "Branch",
                value="main",
                help="Target branch"
            )
            
            language = st.selectbox(
                "Programming Language",
                ["python", "javascript", "typescript", "java", "go", "rust"],
                help="Primary language of the codebase"
            )
        
        with col2:
            test_command = st.text_input(
                "Test Command (Optional)",
                placeholder="pytest tests/",
                help="Command to run tests"
            )
            
            st.markdown("**Bug Priority**")
            priority = st.radio(
                "Priority",
                ["Low", "Medium", "High", "Critical"],
                horizontal=True,
                label_visibility="collapsed"
            )
        
        issue_description = st.text_area(
            "Bug Description",
            height=150,
            placeholder="Describe the bug in detail...",
            help="Provide a clear description of the bug, including expected vs actual behavior"
        )
        
        submitted = st.form_submit_button("Submit Bug Fix Request", use_container_width=True)
        
        if submitted:
            if not issue_description:
                st.error("Please provide a bug description")
                return
            
            # Prepare request data
            request_data = {
                "repository_url": repository_url,
                "branch": branch,
                "issue_description": issue_description,
                "test_command": test_command if test_command else None,
                "language": language,
                "additional_context": {
                    "priority": priority.lower()
                }
            }
            
            # Submit request
            with st.spinner("Submitting bug fix request..."):
                result = submit_bug_fix(request_data)
            
            if result:
                st.success("Bug fix request submitted successfully!")
                task_id = result.get('task_id')
                
                st.markdown(f"""
                ### Task Created
                **Task ID:** `{task_id}`
                
                Your bug fix is being processed in the background. 
                Switch to the "Task Monitor" page to track progress.
                """)
                
                # Store in session state for monitoring
                st.session_state['active_task_id'] = task_id


def render_monitor_page():
    """Render the task monitoring page."""
    st.markdown("## Task Monitor")
    
    # Task ID input
    col1, col2 = st.columns([3, 1])
    with col1:
        task_id = st.text_input(
            "Task ID",
            value=st.session_state.get('active_task_id', ''),
            placeholder="Enter task ID to monitor"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        auto_refresh = st.checkbox("Auto-refresh", value=True)
    
    if not task_id:
        st.info("Enter a task ID to monitor its progress")
        return
    
    # Auto-refresh
    if auto_refresh:
        st_autorefresh(interval=REFRESH_INTERVAL, key="task_monitor_refresh")
    
    # Fetch task status
    task_data = get_task_status(task_id)
    
    if not task_data:
        st.error(f"Task {task_id} not found")
        return
    
    # Status header
    status = task_data.get('status', 'unknown')
    st.markdown(f"### Status: {render_status_badge(status)}", unsafe_allow_html=True)
    
    result = task_data.get('result', {})
    
    # Metrics
    if result:
        render_metrics(result)
        st.markdown("---")
    
    # Progress visualization
    if status == "processing":
        st.markdown("## Live Progress")
        # Mock state for progress (in real scenario, this would come from the API)
        logs = result.get('logs', []) if result else []
        execution_history = result.get('execution_history', []) if result else []
        
        # Progress bar
        if result:
            render_progress_bar({
                'current_step': logs[-1].split(':')[0].lower() if logs else 'initialize',
                'attempts': result.get('attempts', 0),
                'max_attempts': 3
            })
        
        st.markdown("---")
        
        # Thought process
        render_agent_thinking(logs, execution_history)
    
    # Results
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Analysis", "Code Patches", "Test Results", "Execution Log"])
    
    with tab1:
        if result and result.get('analysis'):
            st.markdown("### Bug Analysis")
            st.markdown(result['analysis'])
        else:
            st.info("Analysis not yet available")
    
    with tab2:
        if result:
            render_code_diff(result.get('patches', []))
        else:
            st.info("No patches generated yet")
    
    with tab3:
        if result:
            render_test_results(result.get('test_results', []))
        else:
            st.info("No test results yet")
    
    with tab4:
        if result:
            st.markdown("### Execution History")
            execution_history = result.get('execution_history', [])
            if execution_history:
                for entry in execution_history:
                    timestamp = datetime.fromtimestamp(entry.get('timestamp', 0)).strftime("%H:%M:%S")
                    st.markdown(f"**{timestamp}** - {entry.get('action', 'Unknown action')}")
                    with st.expander("Details"):
                        st.json(entry.get('result', {}))
            else:
                st.info("No execution history available")
        else:
            st.info("Execution history not available")
    
    # Final result
    if status in ["success", "failed"]:
        st.markdown("---")
        st.markdown("## Final Result")
        
        if status == "success":
            st.success("Bug fix completed successfully!")
            if result and result.get('final_patch'):
                final_patch = result['final_patch']
                st.markdown(f"**Fixed File:** `{final_patch.get('filename')}`")
                st.code(final_patch.get('code', ''), language='python')
        else:
            st.error("Bug fix failed")
            errors = result.get('error_messages', []) if result else []
            for error in errors:
                st.error(error)


def render_history_page():
    """Render the task history page."""
    st.markdown("## Task History")
    
    # Fetch all tasks
    tasks = get_all_tasks()
    
    if not tasks:
        st.info("No tasks found")
        return
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    total_tasks = len(tasks)
    success_tasks = sum(1 for t in tasks if t.get('status') == 'success')
    failed_tasks = sum(1 for t in tasks if t.get('status') == 'failed')
    pending_tasks = sum(1 for t in tasks if t.get('status') in ['pending', 'processing'])
    
    with col1:
        st.metric("Total Tasks", total_tasks)
    with col2:
        st.metric("Successful", success_tasks)
    with col3:
        st.metric("Failed", failed_tasks)
    with col4:
        st.metric("In Progress", pending_tasks)
    
    st.markdown("---")
    
    # Task list
    for task in tasks:
        task_id = task.get('task_id', 'Unknown')
        status = task.get('status', 'unknown')
        created_at = task.get('created_at', '')
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**Task ID:** `{task_id[:16]}...`")
            if task.get('result'):
                bug_desc = task['result'].get('bug_description', 'N/A')
                st.caption(bug_desc[:100] + "..." if len(bug_desc) > 100 else bug_desc)
        
        with col2:
            st.markdown(render_status_badge(status), unsafe_allow_html=True)
        
        with col3:
            if st.button("View", key=f"view_{task_id}"):
                st.session_state['active_task_id'] = task_id
                st.rerun()
        
        st.markdown("---")


if __name__ == "__main__":
    main()
