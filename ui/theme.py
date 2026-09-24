"""
Research Beast — Design System & Theme Engine
Central design tokens, color variables, typography, spacing, and CSS injection.
"""

import streamlit as st

# -----------------------------------------------------------------------------
# Design Tokens
# -----------------------------------------------------------------------------
THEME = {
    "colors": {
        "background": "#080c14",
        "surface": "#0f172a",
        "surface_elevated": "#172238",
        "surface_subtle": "rgba(15, 23, 42, 0.6)",
        "border": "#1e293b",
        "border_subtle": "rgba(30, 41, 59, 0.6)",
        "border_focus": "#38bdf8",
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        "accent": "#38bdf8",
        "accent_muted": "rgba(56, 189, 248, 0.12)",
        "positive": "#34d399",
        "positive_muted": "rgba(52, 211, 153, 0.12)",
        "negative": "#f87171",
        "negative_muted": "rgba(248, 113, 113, 0.12)",
        "warning": "#fbbf24",
        "warning_muted": "rgba(251, 191, 36, 0.12)",
        "info": "#60a5fa",
        "info_muted": "rgba(96, 165, 250, 0.12)",
    },
    "typography": {
        "font_family_sans": '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif',
        "font_family_mono": '"JetBrains Mono", "SF Mono", Consolas, monospace',
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
        "2xl": "48px",
    },
    "radii": {
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "pill": "9999px",
    }
}

THEME_CSS = """
<style>
    /* Suppress Streamlit default clutter */
    header[data-testid="stHeader"],
    .stAppDeployButton,
    footer,
    #MainMenu,
    [data-testid="manage-app-button"],
    .viewerBadge {
        display: none !important;
        visibility: hidden !important;
    }

    /* Base App Canvas */
    .stApp {
        background-color: #080c14 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Container Max Width & Responsiveness */
    .block-container {
        max-width: 1240px !important;
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }
    }

    /* Native Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        border-bottom: 1px solid #1e293b !important;
        padding-bottom: 4px !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 38px !important;
        padding: 6px 14px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(30, 41, 59, 0.4) !important;
        color: #f8fafc !important;
    }

    .stTabs [aria-selected="true"] {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        color: #38bdf8 !important;
        font-weight: 600 !important;
    }

    /* Inputs & Command Bar */
    .stTextInput input {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 0.9rem !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    .stTextInput input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 1px #38bdf8 !important;
    }

    /* Buttons */
    .stButton button {
        border-radius: 6px !important;
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
        padding: 0.45rem 1rem !important;
    }

    .stButton button[kind="primary"] {
        background: #0284c7 !important;
        border: 1px solid #0369a1 !important;
        color: #ffffff !important;
    }

    .stButton button[kind="primary"]:hover {
        background: #0369a1 !important;
        border-color: #0ea5e9 !important;
    }

    .stButton button[kind="secondary"] {
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        color: #cbd5e1 !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: #1e293b !important;
        color: #f8fafc !important;
        border-color: #334155 !important;
    }

    /* Native Expander Styling */
    .streamlit-expanderHeader {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px !important;
        color: #f8fafc !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        padding: 0.65rem 1rem !important;
    }

    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        margin-bottom: 0.6rem !important;
    }

    [data-testid="stExpanderDetails"] {
        background-color: #0b1325 !important;
        border: 1px solid #1e293b !important;
        border-top: none !important;
        border-bottom-left-radius: 6px !important;
        border-bottom-right-radius: 6px !important;
        padding: 1rem 1.25rem !important;
    }

    /* Clean Financial Table Styling */
    .rb-table-wrap {
        overflow-x: auto;
        border: 1px solid #1e293b;
        border-radius: 8px;
        background: #0f172a;
        margin-bottom: 1.5rem;
    }

    .rb-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.86rem;
    }

    .rb-table th {
        background: #141f36;
        color: #94a3b8;
        font-weight: 600;
        text-align: right;
        padding: 10px 14px;
        border-bottom: 1px solid #24324d;
        font-size: 0.8rem;
        letter-spacing: 0.03em;
        white-space: nowrap;
    }

    .rb-table th:first-child {
        text-align: left;
    }

    .rb-table td {
        padding: 9px 14px;
        text-align: right;
        border-bottom: 1px solid #172338;
        color: #cbd5e1;
        font-variant-numeric: tabular-nums;
        font-family: 'JetBrains Mono', 'SF Mono', monospace;
        font-size: 0.84rem;
        white-space: nowrap;
    }

    .rb-table td:first-child {
        text-align: left;
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
        font-weight: 500;
        color: #f1f5f9;
        white-space: normal;
    }

    .rb-table tr:hover td {
        background: rgba(30, 41, 59, 0.35);
    }

    .rb-table tr.highlight-row td {
        background: rgba(56, 189, 248, 0.05);
        font-weight: 600;
        color: #f8fafc;
    }

    .rb-table tr.target-row td {
        background: rgba(56, 189, 248, 0.12) !important;
        font-weight: 700;
        color: #38bdf8;
    }
</style>
"""


def apply_theme():
    """Applies global CSS design system rules via native Streamlit st.html."""
    st.html(THEME_CSS)
