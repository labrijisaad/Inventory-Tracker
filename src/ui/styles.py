"""
Custom CSS Styles - Simple Clean Dark Mode
"""

import streamlit as st


def load_custom_css():
    """Load simple, clean dark mode CSS."""
    st.markdown(
        """
        <style>
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #2d2d2d;
            border-right: 1px solid #3d3d3d;
        }
        
        /* Navigation buttons */
        [data-testid="stSidebar"] .stButton > button {
            background: #3d3d3d;
            color: #e5e7eb;
            border: 1px solid #4d4d4d;
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: 600;
            text-align: left;
            transition: all 0.2s;
            margin-bottom: 8px;
        }
        
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }
        
        /* Main buttons */
        .main .stButton > button {
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .main .stButton > button:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }
        
        .stButton > button[kind="secondary"] {
            background: #4d4d4d;
            color: #e5e7eb;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: #5d5d5d;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #2d2d2d;
            padding: 6px;
            border-radius: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 600;
            background: transparent;
            color: #9ca3af;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: #3d3d3d;
            color: #e5e7eb;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #3b82f6;
            color: white;
        }
        
        /* Input fields */
        .stSelectbox > div > div,
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input {
            background: #2d2d2d;
            color: #e5e7eb;
            border: 1px solid #4d4d4d;
            border-radius: 6px;
        }
        
        .stSelectbox > div > div:hover,
        .stNumberInput > div > div > input:hover,
        .stTextInput > div > div > input:hover,
        .stTextArea > div > div > textarea:hover,
        .stDateInput > div > div > input:hover {
            border-color: #3b82f6;
        }
        
        .stSelectbox > div > div:focus-within,
        .stNumberInput > div > div > input:focus,
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stDateInput > div > div > input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        
        /* Dropdown */
        [role="listbox"] {
            background: #2d2d2d;
            border: 1px solid #4d4d4d;
            border-radius: 6px;
        }
        
        [role="option"]:hover {
            background: #3d3d3d;
        }
        
        /* Data editor */
        .stDataFrame {
            border-radius: 8px;
            border: 1px solid #3d3d3d;
            background: #2d2d2d;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: #2d2d2d;
            border: 1px solid #4d4d4d;
            border-radius: 6px;
            padding: 12px;
            color: #e5e7eb;
        }
        
        .streamlit-expanderHeader:hover {
            background: #3d3d3d;
        }
        
        /* Messages */
        .stSuccess {
            background: rgba(34, 197, 94, 0.15);
            border-left: 3px solid #22c55e;
            border-radius: 6px;
            color: #86efac;
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.15);
            border-left: 3px solid #ef4444;
            border-radius: 6px;
            color: #fca5a5;
        }
        
        .stWarning {
            background: rgba(245, 158, 11, 0.15);
            border-left: 3px solid #f59e0b;
            border-radius: 6px;
            color: #fcd34d;
        }
        
        .stInfo {
            background: rgba(59, 130, 246, 0.15);
            border-left: 3px solid #3b82f6;
            border-radius: 6px;
            color: #93c5fd;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1e1e1e;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #4d4d4d;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #5d5d5d;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
