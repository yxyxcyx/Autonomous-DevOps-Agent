"""Custom CSS styles for the Streamlit application."""

import streamlit as st


def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown("""
    <style>
        /* Main header styling */
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f77b4;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Step boxes for workflow visualization */
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
        
        /* Code block styling */
        .code-block {
            background-color: #f5f5f5;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #ddd;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        /* Metric card styling */
        .metric-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        /* Status badge styling */
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
        
        .status-cancelled {
            background-color: #f5f5f5;
            color: #757575;
        }
        
        /* Log entry styling */
        .log-entry {
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-left: 3px solid #2196f3;
            background-color: #f8f9fa;
            font-family: monospace;
            font-size: 0.9rem;
        }
        
        /* Error log styling */
        .log-error {
            border-color: #f44336;
            background-color: #ffebee;
        }
        
        /* Success log styling */
        .log-success {
            border-color: #4caf50;
            background-color: #e8f5e9;
        }
        
        /* Card container styling */
        .task-card {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            margin-bottom: 1rem;
        }
        
        /* Improve button styling */
        .stButton > button {
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Improve sidebar styling */
        .css-1d391kg {
            padding-top: 2rem;
        }
        
        /* Custom animations */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .processing-indicator {
            animation: pulse 2s infinite;
        }
        
        /* Improve metric display */
        [data-testid="metric-container"] {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* Improve expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
        }
        
        /* Table styling */
        .dataframe {
            border: none !important;
        }
        
        .dataframe thead tr th {
            background-color: #1f77b4 !important;
            color: white !important;
        }
        
        .dataframe tbody tr:hover {
            background-color: #f5f5f5 !important;
        }
        
        /* Info box styling */
        .info-box {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            border-radius: 0.25rem;
            margin: 1rem 0;
        }
        
        /* Warning box styling */
        .warning-box {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 1rem;
            border-radius: 0.25rem;
            margin: 1rem 0;
        }
        
        /* Error box styling */
        .error-box {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 1rem;
            border-radius: 0.25rem;
            margin: 1rem 0;
        }
        
        /* Success box styling */
        .success-box {
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 1rem;
            border-radius: 0.25rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
