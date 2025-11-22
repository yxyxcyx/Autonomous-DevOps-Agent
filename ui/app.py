"""
Streamlit UI for the Autonomous DevOps Agent.

This is a refactored, modular version of the UI application.
"""

import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.api_client import APIClient
from ui.pages.submit import render_submit_page
from ui.pages.monitor import render_monitor_page
from ui.pages.history import render_history_page
from ui.components.styles import apply_custom_styles

# Page configuration
st.set_page_config(
    page_title="Autonomous DevOps Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/devops-agent',
        'Report a bug': 'https://github.com/yourusername/devops-agent/issues',
        'About': 'AI-powered automated bug fixing and security patching system'
    }
)


def initialize_session_state():
    """Initialize session state variables."""
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Submit Bug Fix'
    
    if 'api_client' not in st.session_state:
        st.session_state['api_client'] = APIClient()
    
    if 'recent_tasks' not in st.session_state:
        st.session_state['recent_tasks'] = []


def render_sidebar(api_client: APIClient):
    """
    Render the sidebar with navigation and status.
    
    Args:
        api_client: API client instance
    """
    with st.sidebar:
        # Title and description
        st.markdown("# DevOps Agent")
        st.markdown("**Automated Bug Fixing System**")
        st.markdown("---")
        
        # Navigation
        st.markdown("### Navigation")
        
        # Navigation buttons
        current_page = st.session_state.get('page', 'Submit Bug Fix')
        
        if st.button(
            "NEW REQUEST", 
            use_container_width=True,
            type="primary" if current_page == 'Submit Bug Fix' else "secondary"
        ):
            st.session_state['page'] = 'Submit Bug Fix'
            st.rerun()
        
        if st.button(
            "MONITOR TASKS", 
            use_container_width=True,
            type="primary" if current_page == 'Task Monitor' else "secondary"
        ):
            st.session_state['page'] = 'Task Monitor'
            st.rerun()
            
        if st.button(
            "TASK HISTORY", 
            use_container_width=True,
            type="primary" if current_page == 'Task History' else "secondary"
        ):
            st.session_state['page'] = 'Task History'
            st.rerun()
        
        st.markdown("---")
        
        # API Status
        st.markdown("### System Status")
        if api_client.check_health():
            st.success("API: Connected")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", "Online")
            with col2:
                st.metric("Health", "Good")
        else:
            st.error("API: Disconnected")
            st.warning("Please ensure the backend services are running")
        
        # Info section
        st.markdown("---")
        st.markdown("### Information")
        
        info_container = st.container()
        with info_container:
            st.info(
                "**Quick Tips:**\n\n"
                "• Submit code via repo URL, direct paste, or file upload\n"
                "• Monitor task progress in real-time\n"
                "• View complete history of all fixes"
            )
        
        # Recent tasks
        if 'recent_tasks' in st.session_state and st.session_state['recent_tasks']:
            st.markdown("---")
            st.markdown("### Recent Tasks")
            for task_id in st.session_state['recent_tasks'][:5]:
                task_short = task_id[:8] if len(task_id) > 8 else task_id
                if st.button(f"Task: {task_short}...", key=f"task_{task_id}", use_container_width=True):
                    st.session_state['active_task_id'] = task_id
                    st.session_state['page'] = 'Task Monitor'
                    st.rerun()
        
        # Footer
        st.markdown("---")
        st.caption("Version 2.0")
        st.caption("Powered by Google Gemini AI")
        st.caption("[Documentation](https://github.com/yourusername/devops-agent) | [Support](https://github.com/yourusername/devops-agent/issues)")


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Apply custom styles
    apply_custom_styles()
    
    # Get API client
    api_client = st.session_state['api_client']
    
    # Check API health
    if not api_client.check_health():
        st.error(
            "️ **Cannot connect to API**\n\n"
            "Please ensure the backend services are running:\n"
            "```bash\n"
            "docker-compose up -d\n"
            "```"
        )
        st.stop()
    
    # Render sidebar
    render_sidebar(api_client)
    
    # Display current page in main area
    page = st.session_state.get('page', 'Submit Bug Fix')
    
    # Page header
    if page == 'Submit Bug Fix':
        render_submit_page(api_client)
    elif page == 'Task Monitor':
        render_monitor_page(api_client)
    elif page == 'Task History':
        render_history_page(api_client)
    else:
        st.error(f"Unknown page: {page}")


if __name__ == "__main__":
    main()
