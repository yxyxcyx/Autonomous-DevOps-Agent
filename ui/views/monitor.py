"""Monitor page for tracking task progress."""

import streamlit as st
import os
import sys
from datetime import datetime
import pytz
from dateutil import tz
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.constants import DEFAULT_UI_REFRESH_INTERVAL
from ui.api_client import APIClient
from ui.components.visualizations import (
    render_status_badge,
    render_progress_bar,
    render_agent_thinking,
    render_metrics
)
from ui.components.code_display import render_code_diff, render_test_results


def render_monitor_page(api_client: APIClient):
    """
    Render the task monitoring page.
    
    Args:
        api_client: API client instance for backend communication
    """
    st.markdown("##  Task Monitor")
    
    # Task ID input
    col1, col2 = st.columns([3, 1])
    with col1:
        task_id = st.text_input(
            "Task ID",
            value=st.session_state.get('active_task_id', ''),
            placeholder="Enter task ID to monitor",
            label_visibility="visible"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        auto_refresh = st.checkbox("Auto-refresh", value=True)
    
    if not task_id:
        st.info("ℹ️ Enter a task ID to monitor its progress")
        
        # Show recent tasks as suggestions
        recent_tasks = st.session_state.get('recent_tasks', [])
        if recent_tasks:
            st.markdown("### Recent Tasks")
            for recent_task_id in recent_tasks[:5]:
                if st.button(f" {recent_task_id}", key=f"recent_{recent_task_id}"):
                    st.session_state['active_task_id'] = recent_task_id
                    st.rerun()
        return
    
    # Auto-refresh placeholder - can be implemented with JavaScript injection
    # or by using a refresh button
    if auto_refresh:
        if st.button(" Refresh Now", key="manual_refresh"):
            st.rerun()
    
    # Fetch task status
    task_data = api_client.get_task_status(task_id)
    
    if not task_data:
        st.error(f" Task {task_id} not found")
        return
    
    # Store in recent tasks
    if 'recent_tasks' not in st.session_state:
        st.session_state['recent_tasks'] = []
    if task_id not in st.session_state['recent_tasks']:
        st.session_state['recent_tasks'].insert(0, task_id)
        st.session_state['recent_tasks'] = st.session_state['recent_tasks'][:10]
    
    # Status header
    status = task_data.get('status', 'unknown')
    st.markdown(f"### Status: {render_status_badge(status)}", unsafe_allow_html=True)
    
    # Task metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        created_at = task_data.get('created_at')
        if created_at:
            # Convert UTC to local timezone
            utc_time = datetime.fromisoformat(created_at.replace('Z', '+00:00') if 'Z' in created_at else created_at)
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
            local_time = utc_time.astimezone(tz.tzlocal())
            st.metric("Created", local_time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    with col2:
        completed_at = task_data.get('completed_at')
        if completed_at:
            # Convert UTC to local timezone
            utc_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00') if 'Z' in completed_at else completed_at)
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
            local_time = utc_time.astimezone(tz.tzlocal())
            st.metric("Completed", local_time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    with col3:
        if created_at and completed_at:
            duration = (datetime.fromisoformat(completed_at) - 
                       datetime.fromisoformat(created_at)).total_seconds()
            st.metric("Duration", f"{duration:.1f}s")
    
    result = task_data.get('result', {})
    
    # Metrics dashboard
    if result:
        st.markdown("---")
        render_metrics(result)
        st.markdown("---")
    
    # Progress visualization
    if status == "processing":
        st.markdown("##  Live Progress")
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
        
        # Agent thought process
        render_agent_thinking(logs, execution_history)
    
    # Results tabs
    st.markdown("---")
    
    tabs = st.tabs([
        " Analysis",
        " Code Patches",
        " Test Results",
        " Execution Log",
        " Raw Data"
    ])
    
    with tabs[0]:
        if result and result.get('analysis'):
            st.markdown("### Bug Analysis")
            st.markdown(result['analysis'])
        else:
            st.info("Analysis not yet available")
    
    with tabs[1]:
        if result:
            render_code_diff(result.get('patches', []))
        else:
            st.info("No patches generated yet")
    
    with tabs[2]:
        if result:
            render_test_results(result.get('test_results', []))
        else:
            st.info("No test results yet")
    
    with tabs[3]:
        if result:
            st.markdown("### Execution History")
            execution_history = result.get('execution_history', [])
            if execution_history:
                for entry in execution_history:
                    timestamp = datetime.fromtimestamp(
                        entry.get('timestamp', 0)
                    ).strftime("%H:%M:%S")
                    
                    with st.expander(f"⏱️ {timestamp} - {entry.get('action', 'Unknown action')}"):
                        st.json(entry.get('result', {}))
            else:
                st.info("No execution history available")
        else:
            st.info("Execution history not available")
    
    with tabs[4]:
        if st.checkbox("Show raw JSON data"):
            st.json(task_data)
    
    # Final result section
    if status in ["success", "failed"]:
        st.markdown("---")
        st.markdown("##  Final Result")
        
        if status == "success":
            st.success(" Bug fix completed successfully!")
            if result and result.get('final_patch'):
                final_patch = result['final_patch']
                st.markdown(f"**Fixed File:** `{final_patch.get('filename')}`")
                st.code(final_patch.get('code', ''), language='python')
                
                # Download button
                st.download_button(
                    label=" Download Patch",
                    data=final_patch.get('code', ''),
                    file_name=final_patch.get('filename', 'patch.py'),
                    mime="text/plain"
                )
        else:
            st.error(" Bug fix failed")
            errors = result.get('error_messages', []) if result else []
            if errors:
                st.markdown("### Error Details")
                for error in errors:
                    st.error(error)
            
            # Retry button
            if st.button(" Retry Task"):
                # TODO: Implement retry logic
                st.info("Retry functionality coming soon")
