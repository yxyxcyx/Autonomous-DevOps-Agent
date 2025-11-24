"""Custom CSS styles for the Streamlit application."""

import streamlit as st


def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --page-bg: #030712;
            --surface: rgba(15, 23, 42, 0.85);
            --glass: rgba(255, 255, 255, 0.03);
            --border: rgba(148, 163, 184, 0.2);
            --text: #e2e8f0;
            --muted: #94a3b8;
            --accent: #7a5af8;
            --accent-2: #0ea5e9;
            --success: #22c55e;
            --error: #f43f5e;
        }

        body, .stApp, [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top, #0f172a 0%, #030712 55%);
            color: var(--text);
            font-family: 'Space Grotesk', sans-serif;
        }

        [data-testid="stAppViewContainer"] .main {
            padding: 2rem 4rem;
        }

        section[data-testid="stSidebar"] > div:first-child {
            background: rgba(2, 6, 23, 0.9);
            backdrop-filter: blur(16px);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] label {
            color: var(--text) !important;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] > label {
            background: rgba(255, 255, 255, 0.02);
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            margin-bottom: 0.35rem;
            border: 1px solid transparent;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            border-color: var(--border);
            background: rgba(255, 255, 255, 0.05);
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {
            color: var(--accent);
        }

        .hero-banner {
            background: linear-gradient(135deg, rgba(122, 90, 248, 0.15), rgba(14, 165, 233, 0.15));
            border: 1px solid var(--border);
            border-radius: 1.5rem;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 30px 70px rgba(2, 6, 23, 0.65);
            position: relative;
            overflow: hidden;
        }

        .hero-banner::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 20% 20%, rgba(248, 250, 252, 0.35), transparent 45%);
            pointer-events: none;
        }

        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.2em;
            font-size: 0.75rem;
            color: var(--muted);
        }

        .hero-status-card {
            background: rgba(2, 6, 23, 0.7);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .status-pill--online {
            background: rgba(34, 197, 94, 0.18);
            color: var(--success);
        }

        .status-pill--offline {
            background: rgba(244, 63, 94, 0.18);
            color: var(--error);
        }

        .glass-card {
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 1.25rem;
            padding: 1.5rem;
            backdrop-filter: blur(18px);
            box-shadow: 0 24px 60px rgba(2, 6, 23, 0.45);
        }

        .section-title {
            font-size: 1rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 0.5rem;
        }

        .action-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.25rem;
            min-height: 210px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .action-card:hover {
            transform: translateY(-4px);
            border-color: rgba(122, 90, 248, 0.6);
        }

        .action-card h4 {
            margin-bottom: 0.25rem;
        }

        .action-card p {
            color: var(--muted);
            font-size: 0.9rem;
        }

        .workflow-step {
            border-left: 3px solid var(--border);
            padding-left: 1rem;
            margin-bottom: 1rem;
        }

        .workflow-step strong {
            display: block;
            margin-bottom: 0.25rem;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1rem;
        }

        .metric-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.2rem;
        }

        .metric-card span {
            font-size: 0.75rem;
            letter-spacing: 0.25em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .metric-card h3 {
            margin: 0.4rem 0 0;
            font-size: 1.75rem;
        }

        .stButton > button {
            width: 100%;
            border-radius: 999px;
            padding: 0.75rem 1.5rem;
            border: 1px solid transparent;
            font-weight: 600;
            letter-spacing: 0.02em;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #fff;
            box-shadow: 0 12px 30px rgba(15, 118, 255, 0.25);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(14, 165, 233, 0.3);
        }

        .stButton.secondary > button {
            background: transparent;
            color: var(--text);
            border-color: var(--border);
            box-shadow: none;
        }

        .highlight-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.8rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 999px;
            font-size: 0.85rem;
            color: var(--muted);
        }

        /* Tables & data */
        .dataframe {
            border: none !important;
        }

        .dataframe thead tr th {
            background-color: rgba(15, 23, 42, 0.7) !important;
            color: var(--text) !important;
        }

        .dataframe tbody tr:hover {
            background-color: rgba(122, 90, 248, 0.08) !important;
        }

        /* Metrics */
        [data-testid="metric-container"] {
            background-color: rgba(2, 6, 23, 0.6);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1rem;
            color: var(--text);
        }

        /* Cards reused elsewhere */
        .task-card {
            background-color: rgba(2, 6, 23, 0.75);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.25rem;
        }

        .info-box {
            background-color: rgba(14, 165, 233, 0.12);
            border-left: 4px solid var(--accent-2);
            padding: 1rem;
            border-radius: 0.75rem;
        }

        .warning-box {
            background-color: rgba(250, 204, 21, 0.12);
            border-left: 4px solid #facc15;
            padding: 1rem;
            border-radius: 0.75rem;
        }

        .error-box {
            background-color: rgba(244, 63, 94, 0.12);
            border-left: 4px solid var(--error);
            padding: 1rem;
            border-radius: 0.75rem;
        }

        .success-box {
            background-color: rgba(34, 197, 94, 0.12);
            border-left: 4px solid var(--success);
            padding: 1rem;
            border-radius: 0.75rem;
        }

        /* Logs */
        .log-entry {
            padding: 0.75rem 1rem;
            margin: 0.35rem 0;
            border-left: 3px solid var(--accent-2);
            background-color: rgba(14, 165, 233, 0.07);
            font-family: 'Space Grotesk', monospace;
            font-size: 0.9rem;
            border-radius: 0.5rem;
        }

        .log-error {
            border-color: var(--error);
            background-color: rgba(244, 63, 94, 0.12);
        }

        .log-success {
            border-color: var(--success);
            background-color: rgba(34, 197, 94, 0.12);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.5);
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(148, 163, 184, 0.8);
        }

        .processing-indicator {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* Legacy helpers retained for compatibility */
        .step-box {
            padding: 1rem;
            border-radius: 0.75rem;
            margin: 0.5rem 0;
            border-left: 4px solid;
        }

        .step-planning { background-color: rgba(33, 150, 243, 0.12); border-color: #2196f3; }
        .step-coding { background-color: rgba(255, 152, 0, 0.12); border-color: #ff9800; }
        .step-reviewing { background-color: rgba(156, 39, 176, 0.12); border-color: #9c27b0; }
        .step-testing { background-color: rgba(76, 175, 80, 0.12); border-color: #4caf50; }
        .step-complete { background-color: rgba(67, 160, 71, 0.18); border-color: #43a047; }
        .step-failed { background-color: rgba(229, 57, 53, 0.18); border-color: #e53935; }

        .code-block {
            background-color: rgba(15, 23, 42, 0.9);
            padding: 1rem;
            border-radius: 0.75rem;
            border: 1px solid var(--border);
            font-family: 'Space Grotesk', monospace;
            font-size: 0.95rem;
        }

        .status-badge {
            padding: 0.35rem 0.9rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }

        .status-pending { background-color: rgba(245, 124, 0, 0.15); color: #f57c00; }
        .status-processing { background-color: rgba(25, 118, 210, 0.15); color: #1976d2; }
        .status-success { background-color: rgba(56, 142, 60, 0.15); color: #388e3c; }
        .status-failed { background-color: rgba(211, 47, 47, 0.15); color: #d32f2f; }
        .status-cancelled { background-color: rgba(117, 117, 117, 0.15); color: #757575; }
    </style>
    """, unsafe_allow_html=True)
