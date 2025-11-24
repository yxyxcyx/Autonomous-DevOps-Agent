"""
Autonomous DevOps Agent - User-Friendly Interface
Simple and intuitive bug fixing tool for everyone
"""

import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.api_client import APIClient
from ui.views.submit import render_submit_page
from ui.views.monitor import render_monitor_page
from ui.views.history import render_history_page
from ui.components.styles import apply_custom_styles

NAV_ITEMS = [
    {"key": "Home", "label": "Overview"},
    {"key": "Submit", "label": "New Fix"},
    {"key": "Monitor", "label": "Monitor"},
    {"key": "History", "label": "History"},
    {"key": "Help", "label": "Help"},
]

# Page configuration with modern styling
st.set_page_config(
    page_title="DevOps Agent - AI-Powered Bug Fixer",
    page_icon=":gear:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-powered autonomous bug fixing agent",
        'Report a bug': "https://github.com/your-repo/issues",
    }
)

apply_custom_styles()

def initialize_session_state():
    """Initialize session state variables."""
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Home'
    if 'api_client' not in st.session_state:
        st.session_state['api_client'] = APIClient()
    if 'active_task_id' not in st.session_state:
        st.session_state['active_task_id'] = None
    if 'recent_tasks' not in st.session_state:
        st.session_state['recent_tasks'] = []

def render_header():
    """Render the hero header with system status."""
    api_client = st.session_state['api_client']
    status_report = api_client.test_connection()
    connected = status_report.get("connected", False)
    version = status_report.get("version", "-")
    components = status_report.get("components", {})
    recent_count = len(st.session_state.get('recent_tasks', []))
    status_class = "status-pill--online" if connected else "status-pill--offline"
    status_label = "System Online" if connected else "System Offline"
    status_icon = "🟢" if connected else "🔴"

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-eyebrow">Autonomous DevOps Agent</div>
            <div style="display:flex; gap:2rem; flex-wrap:wrap; align-items:flex-start;">
                <div style="flex:1 1 360px;">
                    <h1 style="margin-bottom:0.35rem;">Ship production-ready fixes without context switching</h1>
                    <p style="color: var(--muted); font-size:1rem; margin-bottom:1.25rem;">
                        Let an AI-native DevOps partner triage bugs, craft patches, and verify tests
                        while you stay in your creative flow.
                    </p>
                    <div style="display:flex; gap:0.75rem; flex-wrap:wrap;">
                        <span class="highlight-pill">⚡ {recent_count} recent tasks</span>
                        <span class="highlight-pill">🛡️ Safe retries up to 5x</span>
                    </div>
                </div>
                <div class="hero-status-card" style="flex:0 0 280px;">
                    <div class="section-title" style="margin-bottom:0.75rem;">System Status</div>
                    <div class="status-pill {status_class}">
                        {status_icon} {status_label}
                    </div>
                    <ul style="list-style:none; padding:0; margin:1rem 0 0; color:var(--muted); font-size:0.9rem;">
                        <li><strong>API:</strong> {api_client.base_url}</li>
                        <li><strong>Version:</strong> {version}</li>
                        <li><strong>Components:</strong> {len(components) or '—'}</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_primary_navigation():
    """Render a horizontal navigation ribbon for quick access."""
    current_page = st.session_state.get('page', 'Home')
    cols = st.columns(len(NAV_ITEMS))

    for item, col in zip(NAV_ITEMS, cols):
        with col:
            is_active = item["key"] == current_page
            if st.button(
                item["label"],
                key=f"top_nav_{item['key']}",
                type="primary" if is_active else "secondary"
            ):
                if not is_active:
                    st.session_state['page'] = item["key"]
                    st.rerun()


def render_sidebar():
    """Render the sidebar navigation and info."""
    with st.sidebar:
        st.markdown("## Command Center")

        nav_labels = [item["label"] for item in NAV_ITEMS]
        current_page = st.session_state.get('page', 'Home')
        selected_idx = next((i for i, item in enumerate(NAV_ITEMS) if item["key"] == current_page), 0)
        selected_label = st.radio(
            "Navigation",
            nav_labels,
            index=selected_idx,
            label_visibility="collapsed"
        )

        selected_key = next(item["key"] for item in NAV_ITEMS if item["label"] == selected_label)
        if selected_key != current_page:
            st.session_state['page'] = selected_key
            st.rerun()

        st.divider()

        # Active task context
        st.markdown("### Active Task")
        active_task = st.session_state.get('active_task_id')
        if active_task:
            st.code(active_task, language="bash")
            if st.button("Jump to monitor", use_container_width=True, key="sidebar_monitor"):
                st.session_state['page'] = 'Monitor'
                st.rerun()
        else:
            st.info("No task selected yet")

        st.divider()

        # Snapshot metrics (lightweight fetch)
        api_client = st.session_state['api_client']
        tasks_data = api_client.get_all_tasks(limit=50)
        tasks = [t for t in tasks_data.get('tasks', []) if t]

        if tasks:
            total_tasks = len(tasks)
            success = sum(1 for t in tasks if t.get('status') == 'success')
            failed = sum(1 for t in tasks if t.get('status') == 'failed')
            pending = sum(1 for t in tasks if t.get('status') in ('pending', 'processing'))

            st.markdown("### Workspace Pulse")
            st.metric("Total", total_tasks)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Success", success)
            with col2:
                st.metric("Failed", failed)
            if pending:
                st.info(f"{pending} running tasks")

        st.divider()

        # Recent Activity quick links
        st.markdown("### Recent Activity")
        recent_tasks = st.session_state.get('recent_tasks', [])[:5]

        if recent_tasks:
            for task_id in recent_tasks:
                if st.button(f"↗︎ {task_id[:12]}...", key=f"recent_{task_id}", use_container_width=True):
                    st.session_state['active_task_id'] = task_id
                    st.session_state['page'] = 'Monitor'
                    st.rerun()
        else:
            st.info("Nothing yet — submit your first bug!")

        st.divider()

        with st.expander("System info"):
            st.markdown(
                """
                **Version:** 1.0.0  
                """
            )

def render_home_page():
    """Render the redesigned home/landing page."""
    api_client = st.session_state['api_client']
    tasks_data = api_client.get_all_tasks(limit=100)
    tasks = [t for t in tasks_data.get('tasks', []) if t]

    total_tasks = len(tasks)
    successful = sum(1 for t in tasks if t.get('status') == 'success')
    failed = sum(1 for t in tasks if t.get('status') == 'failed')
    running = sum(1 for t in tasks if t.get('status') in ('pending', 'processing'))
    durations = [t.get('duration') for t in tasks if t.get('duration')]
    avg_duration = sum(durations) / len(durations) if durations else 0
    total_tokens = sum(
        t.get('result', {}).get('total_tokens_used', 0)
        for t in tasks if t.get('result')
    )
    success_rate = (successful / total_tasks * 100) if total_tasks else 0

    st.markdown("<div class=\"section-title\">Choose your next move</div>", unsafe_allow_html=True)
    action_cols = st.columns(3)
    actions = [
        {
            "title": "Submit a new bug",
            "desc": "Upload code, describe the failure, and let the agent craft a patch.",
            "button": "Start a fix",
            "target": "Submit",
            "meta": "Supports repos & pastes"
        },
        {
            "title": "Monitor live progress",
            "desc": "Observe autonomous reasoning, diffs, and test runs in real-time.",
            "button": "Open monitor",
            "target": "Monitor",
            "meta": "Auto-refresh capable"
        },
        {
            "title": "Browse task history",
            "desc": "Search every fix, download patches, and audit AI decisions.",
            "button": "View history",
            "target": "History",
            "meta": "Export-ready logs"
        }
    ]

    for col, action in zip(action_cols, actions):
        with col:
            st.markdown(
                f"""
                <div class="action-card">
                    <div>
                        <h4>{action['title']}</h4>
                        <p>{action['desc']}</p>
                    </div>
                    <span class="highlight-pill">{action['meta']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(action['button'], key=f"action_{action['target']}"):
                st.session_state['page'] = action['target']
                st.rerun()

    st.markdown("---")

    st.markdown("## Performance snapshot")
    metric_cols = st.columns(4)
    metric_cards = [
        {"label": "Total fixes", "value": f"{total_tasks:,}", "sub": "Past 100 tasks"},
        {"label": "Success rate", "value": f"{success_rate:.1f}%", "sub": "Validated patches"},
        {"label": "Avg. fix time", "value": f"{avg_duration:.1f}s" if avg_duration else "N/A", "sub": "From assign to pass"},
        {"label": "Tokens used", "value": f"{total_tokens:,}" if total_tokens else "—", "sub": "LLM consumption"},
    ]

    for col, metric in zip(metric_cols, metric_cards):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <span>{metric['label']}</span>
                    <h3>{metric['value']}</h3>
                    <p style="margin:0; color: var(--muted);">{metric['sub']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    if running:
        st.info(f"{running} tasks currently running across environments")

    st.markdown("---")
    st.markdown("## Intelligent workflow")
    workflow_cols = st.columns(4)
    steps = [
        ("Scope", "Describe the failure, stack, and reproduction steps."),
        ("Reason", "Multi-agent planning pinpoints likely root causes."),
        ("Patch", "Coder agents draft, diff, and iteratively improve fixes."),
        ("Verify", "Automated tests and lint checks gate delivery."),
    ]

    for col, (title, desc) in zip(workflow_cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="workflow-step">
                    <strong>{title}</strong>
                    <p style="margin-bottom:0; color: var(--muted);">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("## Latest activity")

    if tasks:
        latest = tasks[:5]
        history_cols = st.columns([2, 1, 1, 1])
        headers = ["Task", "Status", "Priority", "Duration"]
        for col, header in zip(history_cols, headers):
            with col:
                st.markdown(f"**{header}**")

        for task in latest:
            col_task, col_status, col_priority, col_duration = st.columns([2, 1, 1, 1])
            with col_task:
                st.markdown(f"`{task.get('task_id', '')[:12]}...`")
            with col_status:
                st.markdown(task.get('status', 'unknown').title())
            with col_priority:
                st.markdown(task.get('priority', 'n/a').title())
            with col_duration:
                duration = task.get('duration')
                st.markdown(f"{duration:.1f}s" if duration else "—")
    else:
        st.info("No tasks yet. Submit your first bug to see insights here.")

def render_help_page():
    """Render the help page with user guide."""
    st.markdown("# Need Help? We're Here!")
    st.markdown("*Everything you need to know, explained simply*")
    
    tabs = st.tabs(["Getting Started", "How to Use", "Common Questions", "Troubleshooting"])
    
    with tabs[0]:
        st.markdown("""
        ### It's Easy! Just 3 Steps:
        
        **Step 1: Tell us what's broken**
        - Click "Fix New Bug" button
        - Paste your broken code
        - Explain what's wrong in plain English
        
        **Step 2: Let the AI work**
        - Get a Task ID (save this number!)
        - Watch the progress in real-time
        - Usually takes 30-60 seconds
        
        **Step 3: Get your fixed code**
        - Copy the corrected code
        - Read the explanation
        - Use it in your project!
        
        **Tip:** Don't worry about technical terms - just describe what's wrong like you'd tell a friend!
        """)
    
    with tabs[1]:
        st.markdown("""
        ### How to Write a Good Bug Description
        
        **Good Example:**
        > "My add function gives 2 when I add 5+3, but it should give 8"
        
        **Bad Example:**  
        > "Code doesn't work"
        
        ### What Information to Include:
        
        1. **What should happen:** "It should add two numbers"
        2. **What actually happens:** "It subtracts them instead"
        3. **Example:** "When I use add(5,3) I get 2 not 8"
        
        ### Supported Languages:
        Python, JavaScript, Java, Go, C++, Ruby, PHP, and more!
        """)
    
    with tabs[2]:
        st.markdown("""
        ### Common Questions:
        
        **How long does it take?**
        > Usually 30-60 seconds. Simple bugs are faster!
        
        **Does it cost money?**
        > This tool is free to use!
        
        **Is my code safe?**
        > Yes! Your code is private and secure.
        
        **What if the fix doesn't work?**
        > Try describing the problem differently, or add more details.
        
        **Do I need to sign up?**
        > No signup needed - just paste and go!
        
        **Where are fixes saved?**
        > Check "View History" to see all your past fixes.
        """)
    
    with tabs[3]:
        st.markdown("""
        ### Having Problems? Here's Help:
        
        **"My task is stuck"**
        > Wait 1 minute, then try again. Make sure "System Online" shows at the top.
        
        **"The fix didn't work"**
        > Try explaining the problem differently. Add examples like: "When I type X, I get Y but want Z"
        
        **"I lost my Task ID"**
        > No worries! Click "View History" to see all your submissions.
        
        **"Page is loading slowly"**
        > This is normal when AI is thinking. Give it 30-60 seconds.
        
        **Still need help?**
        > Take a screenshot and ask for help in the community!
        """)

def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Render header
    render_header()
    render_primary_navigation()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    page = st.session_state['page']
    
    if page == 'Home':
        render_home_page()
    elif page == 'Submit':
        render_submit_page(st.session_state['api_client'])
    elif page == 'Monitor':
        render_monitor_page(st.session_state['api_client'])
    elif page == 'History':
        render_history_page(st.session_state['api_client'])
    elif page == 'Help':
        render_help_page()
    else:
        render_home_page()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 1rem;">
        AI-Powered Bug Fixing Tool | Made to help everyone code better
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
