"""Submit page for bug fix requests."""

import streamlit as st
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.constants import DEFAULT_BRANCH, DEFAULT_LANGUAGE
from ui.api_client import APIClient


def render_submit_page(api_client: APIClient):
    """
    Render the bug fix submission page with multiple input methods.
    
    Args:
        api_client: API client instance for backend communication
    """
    st.markdown("# Bug Fix Request Submission")
    st.markdown("Submit your code for automated bug analysis and fixing")
    st.markdown("---")
    
    # Input method selection
    input_method = st.selectbox(
        "**Select Input Method**",
        ["Repository URL", "Direct Code Input", "File Upload"],
        help="Choose how you want to provide your code"
    )
    
    st.markdown("---")
    
    # Initialize variables
    repository_url = None
    branch = DEFAULT_BRANCH
    language = DEFAULT_LANGUAGE
    filename = None
    code_input = None
    uploaded_files = None
    
    # Method-specific inputs
    if input_method == "Repository URL":
        st.markdown("### Repository Details")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            repository_url = st.text_input(
                "Repository URL *",
                placeholder="https://github.com/username/repository",
                help="Enter the Git repository URL"
            )
        with col2:
            branch = st.text_input(
                "Branch",
                value=DEFAULT_BRANCH,
                placeholder="main",
                help="Target branch (default: main)"
            )
        
        language = st.selectbox(
            "Primary Language *",
            options=["python", "javascript", "typescript", "java", "go", "rust", "cpp", "c", "csharp", "php", "ruby"],
            index=0,
            help="Select the primary programming language"
        )
        
    elif input_method == "Direct Code Input":
        st.markdown("### Code Details")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            filename = st.text_input(
                "Filename *",
                placeholder="example.py, main.js, App.java",
                help="Enter the filename with extension"
            )
        with col2:
            language = st.selectbox(
                "Language *",
                options=["python", "javascript", "typescript", "java", "go", "rust", "cpp", "c", "csharp", "php", "ruby"],
                index=0,
                help="Programming language"
            )
        
        code_input = st.text_area(
            "Code *",
            height=400,
            placeholder="Paste your complete code here...\n\n# Example:\ndef calculate_total(items):\n    # This function has a bug\n    total = 0\n    for item in items:\n        total = item  # Bug: should be += not =\n    return total",
            help="Paste the complete code that contains the bug"
        )
        
        if code_input:
            st.text(f"Code length: {len(code_input)} characters, {len(code_input.splitlines())} lines")
    
    elif input_method == "File Upload":
        st.markdown("### File Upload")
        
        uploaded_files = st.file_uploader(
            "Select Code Files *",
            type=["py", "js", "ts", "java", "go", "rs", "cpp", "c", "cs", "php", "rb", "swift", "kt", "scala"],
            accept_multiple_files=True,
            help="Upload one or more code files (max 10 MB per file)"
        )
        
        if uploaded_files:
            st.markdown(f"**Uploaded Files ({len(uploaded_files)}):**")
            total_size = 0
            for file in uploaded_files:
                size_kb = file.size / 1024
                st.text(f"  • {file.name} ({size_kb:.1f} KB)")
                total_size += file.size
            
            if total_size > 10 * 1024 * 1024:  # 10 MB limit
                st.warning("Total file size exceeds 10 MB. Please reduce file size or number of files.")
        
        language = st.selectbox(
            "Primary Language *",
            options=["python", "javascript", "typescript", "java", "go", "rust", "cpp", "c", "csharp", "php", "ruby"],
            index=0,
            help="Select the primary programming language of your files"
        )
    
    st.markdown("---")
    
    # Bug description section
    st.markdown("### Bug Description")
    
    issue_description = st.text_area(
        "Describe the Bug *",
        height=150,
        placeholder="""Provide a clear and specific description of the bug. Include:

1. What the code is supposed to do
2. What it's actually doing wrong
3. Steps to reproduce (if applicable)
4. Error messages (if any)

Example:
"The calculate_total() function should sum all items in the list, but it only returns the last item. When passing [1, 2, 3], it returns 3 instead of 6."
""",
        help="Be as specific as possible. Good descriptions lead to better fixes."
    )
    
    # Test configuration
    st.markdown("---")
    st.markdown("### Test Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        test_command = st.text_input(
            "Test Command",
            placeholder="pytest tests/ or npm test or mvn test",
            help="Command to validate the fix (optional but recommended)"
        )
    
    with col2:
        priority = st.selectbox(
            "Priority Level",
            options=["Low", "Medium", "High", "Critical"],
            index=1,
            help="Select bug priority"
        )
    
    # Advanced options
    with st.expander("**Advanced Options**"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_attempts = st.number_input(
                "Max Attempts",
                min_value=1,
                max_value=5,
                value=3,
                help="Maximum fix attempts"
            )
        
        with col2:
            timeout = st.number_input(
                "Timeout (seconds)",
                min_value=60,
                max_value=1800,
                value=300,
                step=60,
                help="Maximum processing time"
            )
        
        with col3:
            auto_merge = st.checkbox(
                "Auto-apply Fix",
                value=False,
                help="Automatically apply the fix if tests pass"
            )
    
    st.markdown("---")
    
    # Submit section
    col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
    
    with col1:
        submit_button = st.button(
            "SUBMIT REQUEST",
            type="primary",
            use_container_width=True,
            help="Submit the bug fix request"
        )
    
    with col2:
        if st.button("CLEAR FORM", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("VIEW HISTORY", use_container_width=True):
            st.session_state['page'] = 'Task History'
            st.rerun()
    
    # Handle submission
    if submit_button:
        # Validation
        validation_errors = []
        
        if not issue_description or len(issue_description.strip()) < 10:
            validation_errors.append("Bug description must be at least 10 characters")
        
        if input_method == "Repository URL":
            if not repository_url:
                validation_errors.append("Repository URL is required")
            elif not (repository_url.startswith("http://") or repository_url.startswith("https://")):
                validation_errors.append("Repository URL must start with http:// or https://")
        
        elif input_method == "Direct Code Input":
            if not filename:
                validation_errors.append("Filename is required")
            if not code_input or len(code_input.strip()) < 10:
                validation_errors.append("Code must be at least 10 characters")
        
        elif input_method == "File Upload":
            if not uploaded_files:
                validation_errors.append("Please upload at least one file")
        
        if validation_errors:
            st.error("**Please fix the following errors:**")
            for error in validation_errors:
                st.error(f"• {error}")
            return
        
        # Prepare submission data
        with st.spinner("Processing your request..."):
            request_data = {
                "issue_description": issue_description,
                "language": language,
                "test_command": test_command if test_command else None,
                "priority": priority.lower(),
                "max_attempts": max_attempts,
                "timeout": timeout,
                "metadata": {
                    "submitted_at": datetime.now().isoformat(),
                    "input_method": input_method,
                    "auto_merge": auto_merge
                }
            }
            
            # Add method-specific data
            if input_method == "Repository URL":
                request_data["repository_url"] = repository_url
                request_data["branch"] = branch
            
            elif input_method == "Direct Code Input":
                request_data["code_content"] = {
                    "filename": filename,
                    "content": code_input,
                    "language": language
                }
                request_data["repository_url"] = "direct_input"
                request_data["branch"] = "main"
            
            elif input_method == "File Upload":
                files_data = []
                for file in uploaded_files:
                    try:
                        content = file.read().decode("utf-8")
                        files_data.append({
                            "filename": file.name,
                            "content": content,
                            "size": file.size
                        })
                    except Exception as e:
                        st.error(f"Error reading {file.name}: {str(e)}")
                        return
                
                request_data["uploaded_files"] = files_data
                request_data["repository_url"] = "file_upload"
                request_data["branch"] = "main"
            
            # Submit to API
            result = api_client.submit_bug_fix(request_data)
        
        if result and result.get('task_id'):
            # Success
            task_id = result['task_id']
            st.success("**REQUEST SUBMITTED SUCCESSFULLY**")
            
            # Display task information
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.info(
                    f"**Task Details**\n\n"
                    f"Task ID: `{task_id}`\n\n"
                    f"Status: Processing\n\n"
                    f"Priority: {priority}\n\n"
                    f"Method: {input_method}"
                )
            
            with info_col2:
                st.info(
                    f"**Processing Info**\n\n"
                    f"Max Attempts: {max_attempts}\n\n"
                    f"Timeout: {timeout}s\n\n"
                    f"Auto-apply: {'Yes' if auto_merge else 'No'}\n\n"
                    f"Submitted: {datetime.now().strftime('%H:%M:%S')}"
                )
            
            # Store task ID for monitoring
            if 'recent_tasks' not in st.session_state:
                st.session_state['recent_tasks'] = []
            if task_id not in st.session_state['recent_tasks']:
                st.session_state['recent_tasks'].insert(0, task_id)
                st.session_state['recent_tasks'] = st.session_state['recent_tasks'][:10]
            
            st.session_state['active_task_id'] = task_id
            
            # Action buttons
            st.markdown("---")
            st.markdown("### Next Steps")
            
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("MONITOR PROGRESS", type="primary", use_container_width=True):
                    st.session_state['page'] = 'Task Monitor'
                    st.rerun()
            
            with action_col2:
                if st.button("SUBMIT ANOTHER", use_container_width=True):
                    st.rerun()
            
            with action_col3:
                if st.button("VIEW ALL TASKS", use_container_width=True):
                    st.session_state['page'] = 'Task History'
                    st.rerun()
        
        else:
            # Error
            st.error(
                "**SUBMISSION FAILED**\n\n"
                "Unable to submit your request. Please check:\n\n"
                "• API service is running and accessible\n"
                "• Your network connection is stable\n"
                "• Request data is valid and complete\n\n"
                f"Error details: {result.get('error', 'Unknown error') if result else 'No response from API'}"
            )
            
            if st.button("RETRY", type="primary"):
                st.rerun()
