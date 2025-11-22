"""History page for viewing all tasks."""

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.api_client import APIClient
from ui.components.visualizations import render_status_badge


def render_history_page(api_client: APIClient):
    """
    Render the task history page.
    
    Args:
        api_client: API client instance for backend communication
    """
    st.markdown("##  Task History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "processing", "success", "failed", "cancelled"],
            index=0
        )
    
    with col2:
        sort_order = st.selectbox(
            "Sort Order",
            ["Newest First", "Oldest First"],
            index=0
        )
    
    with col3:
        page_size = st.selectbox(
            "Items per Page",
            [10, 25, 50, 100],
            index=0
        )
    
    # Fetch all tasks
    tasks = api_client.get_all_tasks(
        limit=page_size,
        status=None if status_filter == "All" else status_filter
    )
    
    if not tasks or not tasks.get('tasks'):
        st.info(" No tasks found")
        return
    
    task_list = tasks.get('tasks', [])
    total_count = tasks.get('total', 0)
    
    # Summary statistics
    st.markdown("###  Summary Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate stats
    stats = calculate_task_statistics(task_list)
    
    with col1:
        st.metric("Total Tasks", total_count)
    with col2:
        st.metric(" Successful", stats['success'])
    with col3:
        st.metric(" Failed", stats['failed'])
    with col4:
        st.metric(" In Progress", stats['in_progress'])
    with col5:
        success_rate = (stats['success'] / total_count * 100) if total_count > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    st.markdown("---")
    
    # Task list display options
    display_mode = st.radio(
        "Display Mode",
        ["Card View", "Table View", "Detailed View"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if display_mode == "Card View":
        render_card_view(task_list, api_client)
    elif display_mode == "Table View":
        render_table_view(task_list)
    else:
        render_detailed_view(task_list, api_client)
    
    # Pagination
    if total_count > page_size:
        st.markdown("---")
        render_pagination(total_count, page_size, api_client)


def calculate_task_statistics(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate statistics from task list.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        'success': 0,
        'failed': 0,
        'in_progress': 0,
        'pending': 0,
        'cancelled': 0
    }
    
    for task in tasks:
        status = task.get('status', 'unknown')
        if status == 'success':
            stats['success'] += 1
        elif status == 'failed':
            stats['failed'] += 1
        elif status in ['pending', 'processing']:
            stats['in_progress'] += 1
        elif status == 'cancelled':
            stats['cancelled'] += 1
    
    return stats


def render_card_view(tasks: List[Dict[str, Any]], api_client: APIClient):
    """
    Render tasks as cards.
    
    Args:
        tasks: List of task dictionaries
        api_client: API client instance
    """
    for task in tasks:
        task_id = task.get('task_id', 'Unknown')
        status = task.get('status', 'unknown')
        created_at = task.get('created_at', '')
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**Task ID:** `{task_id[:16]}...`")
                if task.get('result'):
                    bug_desc = task['result'].get('bug_description', 'N/A')
                    st.caption(bug_desc[:100] + "..." if len(bug_desc) > 100 else bug_desc)
            
            with col2:
                st.markdown(render_status_badge(status), unsafe_allow_html=True)
            
            with col3:
                if st.button("️ View", key=f"view_{task_id}"):
                    st.session_state['active_task_id'] = task_id
                    st.session_state['page'] = 'Task Monitor'
                    st.rerun()
            
            st.markdown("---")


def render_table_view(tasks: List[Dict[str, Any]]):
    """
    Render tasks as a table.
    
    Args:
        tasks: List of task dictionaries
    """
    # Prepare data for DataFrame
    data = []
    for task in tasks:
        data.append({
            'Task ID': task.get('task_id', '')[:16] + '...',
            'Status': task.get('status', 'unknown'),
            'Created': datetime.fromisoformat(task.get('created_at', '')).strftime("%Y-%m-%d %H:%M")
            if task.get('created_at') else 'N/A',
            'Completed': datetime.fromisoformat(task.get('completed_at', '')).strftime("%Y-%m-%d %H:%M")
            if task.get('completed_at') else 'N/A',
        })
    
    df = pd.DataFrame(data)
    
    # Style the DataFrame
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Task ID": st.column_config.TextColumn("Task ID", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Created": st.column_config.TextColumn("Created", width="medium"),
            "Completed": st.column_config.TextColumn("Completed", width="medium"),
        }
    )


def render_detailed_view(tasks: List[Dict[str, Any]], api_client: APIClient):
    """
    Render tasks with detailed information.
    
    Args:
        tasks: List of task dictionaries
        api_client: API client instance
    """
    for task in tasks:
        task_id = task.get('task_id', 'Unknown')
        status = task.get('status', 'unknown')
        
        with st.expander(f"Task: {task_id[:16]}... - {status}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Full ID:** `{task_id}`")
                st.markdown(f"**Status:** {render_status_badge(status)}", unsafe_allow_html=True)
                
                created_at = task.get('created_at')
                if created_at:
                    st.markdown(f"**Created:** {datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M:%S')}")
                
                completed_at = task.get('completed_at')
                if completed_at:
                    st.markdown(f"**Completed:** {datetime.fromisoformat(completed_at).strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                if task.get('result'):
                    result = task['result']
                    st.markdown(f"**Attempts:** {result.get('attempts', 0)}")
                    st.markdown(f"**Patches:** {len(result.get('patches', []))}")
                    st.markdown(f"**Tests:** {len(result.get('test_results', []))}")
                
                if st.button(" View Details", key=f"detail_{task_id}"):
                    st.session_state['active_task_id'] = task_id
                    st.session_state['page'] = 'Task Monitor'
                    st.rerun()
            
            if task.get('error'):
                st.error(f"Error: {task['error']}")


def render_pagination(total: int, page_size: int, api_client: APIClient):
    """
    Render pagination controls.
    
    Args:
        total: Total number of items
        page_size: Items per page
        api_client: API client instance
    """
    total_pages = (total + page_size - 1) // page_size
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        page = st.number_input(
            f"Page (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1
        )
        
        st.markdown(f"Showing page {page} of {total_pages} ({total} total items)")
