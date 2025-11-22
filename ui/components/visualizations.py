"""Visualization components for the UI."""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
import plotly.graph_objects as go


def render_status_badge(status: str) -> str:
    """
    Render a status badge with appropriate styling.
    
    Args:
        status: Task status
        
    Returns:
        HTML string for the badge
    """
    status_lower = status.lower()
    
    # Status to emoji and color mapping
    status_config = {
        'pending': ('⏳', '#FFA500', 'Pending'),
        'processing': ('', '#2196F3', 'Processing'),
        'success': ('', '#4CAF50', 'Success'),
        'failed': ('', '#F44336', 'Failed'),
        'cancelled': ('', '#9E9E9E', 'Cancelled'),
        'unknown': ('', '#757575', 'Unknown')
    }
    
    emoji, color, label = status_config.get(
        status_lower,
        status_config['unknown']
    )
    
    return f'''
    <span style="
        background-color: {color}20;
        color: {color};
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85em;
        display: inline-block;
    ">
        {emoji} {label}
    </span>
    '''


def render_progress_bar(state: Dict[str, Any]) -> None:
    """
    Render agent progress visualization.
    
    Args:
        state: Agent state dictionary
    """
    current_step = state.get("current_step", "initialize")
    attempts = state.get("attempts", 0)
    max_attempts = state.get("max_attempts", 3)
    
    steps = ["analysis", "coding", "review", "testing"]
    step_names = {
        "initialize": " Initializing",
        "analysis": " Analyzing Bug",
        "coding": " Generating Fix",
        "review": " Reviewing Code",
        "testing": " Running Tests"
    }
    
    # Calculate progress percentage
    progress_map = {
        "initialize": 0,
        "analysis": 25,
        "coding": 50,
        "review": 75,
        "testing": 90,
        "complete": 100
    }
    
    progress = progress_map.get(current_step, 0)
    
    # Display progress bar
    st.progress(progress / 100)
    
    # Current step indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"<h3 style='text-align: center;'>{step_names.get(current_step, current_step.title())}</h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='text-align: center;'><strong>Attempt {attempts} of {max_attempts}</strong></p>",
            unsafe_allow_html=True
        )
    
    # Step timeline
    st.markdown("### Timeline")
    timeline_cols = st.columns(len(steps))
    
    for idx, (col, step) in enumerate(zip(timeline_cols, steps)):
        with col:
            if steps.index(current_step) >= idx if current_step in steps else False:
                st.success(f" {step.title()}")
            else:
                st.info(f"⏳ {step.title()}")


def render_agent_thinking(logs: List[str], execution_history: List[Dict[str, Any]]) -> None:
    """
    Render the agent's thought process.
    
    Args:
        logs: List of log messages
        execution_history: List of execution history entries
    """
    st.markdown("###  Agent Thought Process")
    
    if not logs and not execution_history:
        st.info("Waiting for agent to start...")
        return
    
    # Create a scrollable container for logs
    log_container = st.container()
    
    with log_container:
        for i, log in enumerate(logs[-10:]):  # Show last 10 logs
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Determine log type and styling
            if "Manager" in log or "Analyzing" in log:
                icon = ""
                color = "#2196F3"
            elif "Coder" in log or "Generating" in log:
                icon = ""
                color = "#FF9800"
            elif "Reviewer" in log or "Review" in log:
                icon = ""
                color = "#9C27B0"
            elif "TestRunner" in log or "Test" in log:
                icon = ""
                color = "#4CAF50"
            elif "passed" in log.lower() or "success" in log.lower():
                icon = ""
                color = "#43A047"
            elif "failed" in log.lower() or "error" in log.lower():
                icon = ""
                color = "#E53935"
            else:
                icon = "ℹ️"
                color = "#757575"
            
            st.markdown(
                f"""
                <div style="
                    padding: 8px 12px;
                    margin: 4px 0;
                    border-left: 3px solid {color};
                    background-color: {color}10;
                    border-radius: 4px;
                ">
                    <strong>{icon} {timestamp}</strong><br>
                    {log}
                </div>
                """,
                unsafe_allow_html=True
            )


def render_metrics(result: Dict[str, Any]) -> None:
    """
    Render metrics dashboard.
    
    Args:
        result: Task result dictionary
    """
    st.markdown("###  Task Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        attempts = result.get('attempts', 0)
        st.metric(
            "Attempts",
            attempts,
            delta=None if attempts <= 1 else f"+{attempts - 1}"
        )
    
    with col2:
        patches_count = len(result.get('patches', []))
        st.metric(
            "Patches Generated",
            patches_count,
            delta="Good" if patches_count > 0 else None
        )
    
    with col3:
        tokens = result.get('total_tokens_used', 0)
        st.metric(
            "LLM Tokens Used",
            f"{tokens:,}",
            delta=None
        )
    
    with col4:
        test_results = result.get('test_results', [])
        if test_results:
            success_count = sum(1 for t in test_results if t.get('success'))
            success_rate = (success_count / len(test_results) * 100)
            st.metric(
                "Test Success Rate",
                f"{success_rate:.0f}%",
                delta="Pass" if success_rate >= 100 else "Fail"
            )
        else:
            st.metric("Test Success Rate", "N/A")


def create_task_timeline_chart(execution_history: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a timeline chart for task execution.
    
    Args:
        execution_history: List of execution history entries
        
    Returns:
        Plotly figure object
    """
    if not execution_history:
        return None
    
    # Prepare data
    steps = []
    start_times = []
    durations = []
    
    for i, entry in enumerate(execution_history):
        steps.append(entry.get('action', f'Step {i+1}'))
        timestamp = entry.get('timestamp', 0)
        start_times.append(datetime.fromtimestamp(timestamp))
        
        # Calculate duration (use next timestamp or estimate)
        if i < len(execution_history) - 1:
            next_timestamp = execution_history[i + 1].get('timestamp', timestamp)
            duration = next_timestamp - timestamp
        else:
            duration = 5  # Default duration for last step
        durations.append(duration)
    
    # Create Gantt chart
    fig = go.Figure()
    
    for i, (step, start, duration) in enumerate(zip(steps, start_times, durations)):
        fig.add_trace(go.Bar(
            name=step,
            x=[duration],
            y=[step],
            orientation='h',
            marker=dict(
                color=f'rgb({50 + i * 30}, {100 + i * 20}, {150 + i * 10})'
            ),
            showlegend=False,
            hovertemplate='%{y}<br>Duration: %{x}s<extra></extra>'
        ))
    
    fig.update_layout(
        title="Task Execution Timeline",
        xaxis_title="Duration (seconds)",
        yaxis_title="Steps",
        height=400,
        barmode='stack'
    )
    
    return fig


def render_error_details(errors: List[str]) -> None:
    """
    Render error details in a formatted way.
    
    Args:
        errors: List of error messages
    """
    if not errors:
        return
    
    st.markdown("### ️ Error Details")
    
    for i, error in enumerate(errors, 1):
        with st.expander(f"Error {i}", expanded=i == 1):
            st.error(error)
            
            # Try to parse and format if it's a traceback
            if "Traceback" in error:
                st.code(error, language="python")
