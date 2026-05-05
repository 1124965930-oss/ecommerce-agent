"""Marketing AI Hub — Multi-modal 24/7 Automated Marketing Agent System.

Entry point: streamlit run ecommerce-agent/main.py --server.port 8502
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Marketing AI Hub",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

from orchestrator import Orchestrator
from ui.dashboard import render


@st.cache_resource
def get_orchestrator():
    orch = Orchestrator()
    orch.initialize()
    return orch


def main():
    st.markdown("""
    <style>
    .stButton button {
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stMetric {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
    }
    .stExpander {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

    orch = get_orchestrator()
    render(orch)


if __name__ == "__main__":
    main()
