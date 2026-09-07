"""
Full-Stack Institutional Equity Research Dashboard (NSE/BSE)
Multi-Agent Analysis Platform (Agents 0 through 6)
3D Glassmorphic UI with 2-State Flow (Minimal Search Landing -> Full Dossier Display)
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any
import io
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfgen import canvas

from agents.pipeline import EquityAgentPipeline


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        # Header rule & text
        self.drawString(15 * mm, 285 * mm, "RESEARCH BEAST | INSTITUTIONAL EQUITY REPORT")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(15 * mm, 282 * mm, 195 * mm, 282 * mm)
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(195 * mm, 12 * mm, page_text)
        self.drawString(15 * mm, 12 * mm, "CONFIDENTIAL - PREPARED FOR INSTITUTIONAL CLIENTS")
        self.line(15 * mm, 15 * mm, 195 * mm, 15 * mm)
        self.restoreState()


def clean_markdown_for_pdf(text):
    """Clean raw markdown, technical symbols, code fences, and broken unicode into clean text for ReportLab."""
    if not text:
        return ""
    if isinstance(text, dict):
        text = "\n".join(f"{k}: {v}" for k, v in text.items())
    elif isinstance(text, list):
        text = "\n".join(str(item) for item in text)
    else:
        text = str(text)

    # 1. Normalize currency and standard symbols
    text = text.replace('₹', 'Rs. ')
    text = text.replace('€', 'EUR ').replace('£', 'GBP ')

    # 2. Strip code fences (```json, ```, etc.) and inline backticks
    text = re.sub(r'```[a-zA-Z]*', '', text)
    text = text.replace('```', '')
    text = text.replace('`', '')

    # 3. Clean line by line
    cleaned_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip horizontal rules (---, ***, ___)
        if re.match(r'^[-*_]{3,}\s*$', line):
            continue

        # Strip markdown headers (##, ###, ####, etc.)
        line = re.sub(r'^#+\s*', '', line)

        # Convert markdown bullet points (- , * , + ) to standard bullet &bull;
        line = re.sub(r'^[-*+]\s+', '&bull; ', line)
        if line.startswith('•'):
            line = '&bull; ' + line.lstrip('•').strip()

        # Clean JSON bracket lines if any stray ones appear
        if (line.startswith('{') and line.endswith('}')) or (line.startswith('[') and line.endswith(']')):
            clean_json_content = re.sub(r'["{}\[\]]', '', line).strip()
            if clean_json_content:
                line = clean_json_content
            else:
                continue

        # Convert bold **text** to <b>text</b>
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        # Convert __text__ to <b>text</b>
        line = re.sub(r'__(.*?)__', r'<b>\1</b>', line)

        # Convert italic *text* or _text_ to <i>text</i>
        line = re.sub(r'(?<!\w)\*(.*?)\*(?!\w)', r'<i>\1</i>', line)
        line = re.sub(r'(?<!\w)_(.*?)_(?!\w)', r'<i>\1</i>', line)

        # Remove any remaining stray asterisks, hashes
        line = line.replace('**', '').replace('##', '').replace('###', '')

        # Escape stray & that aren't recognized XML entities
        line = re.sub(r'&(?!(bull|amp|lt|gt|quot|apos);)', '&amp;', line)

        # Escape stray < and > not part of valid ReportLab tags
        line = line.replace('<b>', '___B_OPEN___').replace('</b>', '___B_CLOSE___')
        line = line.replace('<i>', '___I_OPEN___').replace('</i>', '___I_CLOSE___')
        line = line.replace('<u>', '___U_OPEN___').replace('</u>', '___U_CLOSE___')
        line = line.replace('<', '&lt;').replace('>', '&gt;')
        line = line.replace('___B_OPEN___', '<b>').replace('___B_CLOSE___', '</b>')
        line = line.replace('___I_OPEN___', '<i>').replace('___I_CLOSE___', '</i>')
        line = line.replace('___U_OPEN___', '<u>').replace('___U_CLOSE___', '</u>')

        # Remove broken/unwanted unicode symbols and emojis that break Helvetica
        line = re.sub(r'[^\x20-\x7E&;]', ' ', line)

        # Clean up multiple spaces
        line = re.sub(r'[ \t]+', ' ', line).strip()

        if line:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


from pdf_generator import build_institutional_pdf, build_presentation_pdf


# Page configuration
st.set_page_config(
    page_title="Research Beast",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 3D Glassmorphism & Ambient 3D Floating Orbs Styles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&family=Fira+Code:wght@400;600&display=swap');

/* Base Dark Canvas */
.stApp {
    background-color: #0d0e15;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #f1f5f9;
    overflow-x: hidden;
}

/* Background Ambient 3D Floating Orbs */
.stApp::before {
    content: '';
    position: fixed;
    top: 5%;
    left: 8%;
    width: 380px;
    height: 380px;
    background: radial-gradient(circle, #ec4899 0%, #be185d 60%, transparent 75%);
    filter: blur(75px);
    opacity: 0.45;
    z-index: 0;
    pointer-events: none;
    border-radius: 50%;
}

.stApp::after {
    content: '';
    position: fixed;
    bottom: 8%;
    right: 10%;
    width: 440px;
    height: 440px;
    background: radial-gradient(circle, #f59e0b 0%, #d97706 60%, transparent 75%);
    filter: blur(85px);
    opacity: 0.4;
    z-index: 0;
    pointer-events: none;
    border-radius: 50%;
}

/* Secondary Purple Orb */
.orb-purple {
    position: fixed;
    top: 55%;
    left: 20%;
    width: 420px;
    height: 420px;
    background: radial-gradient(circle, #8b5cf6 0%, #6d28d9 60%, transparent 75%);
    filter: blur(90px);
    opacity: 0.35;
    z-index: 0;
    pointer-events: none;
    border-radius: 50%;
}

/* Frosted Glass Card Container */
.glass-panel {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 24px;
    padding: 32px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.15);
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
}

/* Glass Stat Tile */
.glass-stat {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
.stat-tag {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important;
    margin-bottom: 4px !important;
}
.stat-num {
    font-size: 1.15rem !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    color: #f8fafc !important;
    margin-top: 4px !important;
}

/* Glass Risk Pills */
.pill-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.pill-green {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.35);
}
.pill-yellow {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.35);
}
.pill-red {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.35);
}

/* Container Tab Strip */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: rgba(15, 23, 42, 0.4) !important;
    padding: 6px 10px !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
}

/* Individual Tab Items (Inactive State) */
.stTabs [data-baseweb="tab"] {
    height: auto !important;
    padding: 8px 16px !important;
    background-color: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    color: #94a3b8 !important; /* Muted Slate */
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    transition: all 0.25s ease-in-out !important;
}
.stTabs [data-baseweb="tab"] p {
    font-size: 0.88rem !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Tab Hover Effect */
.stTabs [data-baseweb="tab"]:hover {
    color: #f1f5f9 !important;
    background-color: rgba(255, 255, 255, 0.04) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
}

/* Active Tab (Sleek Elevated Glass Pill) */
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.03) 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: 0 4px 15px -2px rgba(0, 0, 0, 0.4), 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.2) !important;
    border-radius: 10px !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] p {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Remove the harsh red underline highlight */
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* Remove default bottom tab border line */
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* Minimal Input Styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    color: #ffffff !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    font-size: 1.05rem !important;
}

/* Glass Buttons */
.stButton > button {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(12px) !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: rgba(255, 255, 255, 0.14) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
}

/* Question & Content Cards */
.q-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 12px;
    backdrop-filter: blur(12px);
}
.q-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #818cf8;
    margin-bottom: 5px;
}
.q-ans {
    font-size: 0.92rem;
    color: #e2e8f0;
    line-height: 1.55;
}

/* Bullet Cards */
.bullet-card {
    background: rgba(255, 255, 255, 0.03);
    border-left: 3px solid #6366f1;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 0.92rem;
    color: #f1f5f9;
    backdrop-filter: blur(8px);
}

/* Glass Expanders */
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.02) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 18px !important;
    margin-bottom: 18px !important;
}

/* Streamlit Header / Clean Overrides */
header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
}

/* Metric Card Category Label (Small Header) */
.metric-label, .kpi-label, [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] label, [data-testid="stMetricLabel"] p {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important; /* Muted slate */
    margin-bottom: 4px !important;
}

/* Metric Primary Value (The oversized text to shrink) */
.metric-value, .kpi-value, .stMetricValue, [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {
    font-size: 1.15rem !important; /* Scaled down from oversized 1.8rem+ */
    font-weight: 600 !important;
    line-height: 1.4 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    color: #f8fafc !important; /* Bright crisp white */
}

/* Metric Subtext / Benchmark Benchmark annotation */
.metric-benchmark, .kpi-benchmark, [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] > div {
    font-size: 0.85rem !important;
    font-weight: 400 !important;
    color: #cbd5e1 !important;
}
</style>
<div class="orb-purple"></div>
""", unsafe_allow_html=True)


@st.cache_resource
def get_pipeline():
    return EquityAgentPipeline()


def pill_color(status: str) -> str:
    s = str(status).upper()
    if "GREEN" in s:
        return "green"
    elif "YELLOW" in s:
        return "yellow"
    return "red"


def render_risk_pill(domain: str, status: str) -> str:
    color_class = f"pill-{pill_color(status)}"
    icon = "●"
    return f'<span class="pill-badge {color_class}"><span>{icon}</span> {domain}: {status}</span>'


def render_glass_stat(tag: str, num: str) -> str:
    return f"""
    <div class="glass-stat">
        <div class="stat-tag">{tag}</div>
        <div class="stat-num">{num}</div>
    </div>
    """


def is_bfsi(sector: str = "", industry: str = "") -> bool:
    """Returns True if the entity belongs to Banking, NBFC, or Financial Services."""
    s = str(sector or "").lower()
    i = str(industry or "").lower()
    return any(k in s or k in i for k in ["bank", "financial", "lending", "nbfc", "housing finance", "insurance"])


def main():
    # Default Valuation & DCF Assumptions
    wacc_input = 0.115
    terminal_g_input = 0.055
    base_g_input = 0.12

    # Session state initialization
    if "active_ticker" not in st.session_state:
        st.session_state.active_ticker = ""

    # STATE 1: Hero Landing (Shows when no search has been initiated)
    if not st.session_state.active_ticker:
        st.markdown("""
        <div style="text-align: center; margin-top: 14vh; margin-bottom: 32px;">
            <h1 style="font-size: 3.2rem; font-weight: 800; letter-spacing: -0.03em; color: #ffffff; margin-bottom: 10px; text-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                Research Beast
            </h1>
            <p style="color: #94a3b8; font-size: 1.05rem; font-weight: 500; letter-spacing: 0.02em; margin: 0;">
                Institutional Equity Intelligence &bull; 7-Agent Autonomous Audit
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Centered Search Input
        col_l, col_center, col_r = st.columns([1, 2.5, 1])
        with col_center:
            ticker_input = st.text_input("Enter NSE/BSE Stock Ticker", placeholder="e.g. CROMPTON, RELIANCE, HDFCBANK, TCS", label_visibility="collapsed")
            
            # Sample Quick-Select Buttons
            st.markdown("<p style='text-align:center; color:#64748b; font-size:0.75rem; margin-top:12px;'>POPULAR INSTITUTIONAL TICKERS</p>", unsafe_allow_html=True)
            q1, q2, q3, q4 = st.columns(4)
            if q1.button("CROMPTON", use_container_width=True): ticker_input = "CROMPTON.NS"
            if q2.button("RELIANCE", use_container_width=True): ticker_input = "RELIANCE.NS"
            if q3.button("HDFCBANK", use_container_width=True): ticker_input = "HDFCBANK.NS"
            if q4.button("TCS", use_container_width=True): ticker_input = "TCS.NS"

            if ticker_input:
                clean_ticker = ticker_input.strip().upper()
                if not (clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO")):
                    clean_ticker += ".NS"
                st.session_state.active_ticker = clean_ticker
                st.rerun()

    # STATE 2: Full Institutional Dossier (Shows after ticker selection)
    else:
        ticker = st.session_state.active_ticker

        # Minimal Top Navigation / Re-search Bar
        top_col1, top_col2 = st.columns([4.2, 1.8])
        with top_col1:
            st.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>Analyzing:</span> <b style='font-size:1.2rem; color:#fff;'>{ticker}</b>", unsafe_allow_html=True)
        with top_col2:
            if st.button("← Search Another Stock", use_container_width=True):
                st.session_state.active_ticker = ""
                st.rerun()

        # Pipeline Execution with Session State Caching
        pipeline = get_pipeline()
        cache_key = f"{ticker}_{wacc_input}_{terminal_g_input}_{base_g_input}"
        if "dossier_cache" not in st.session_state:
            st.session_state["dossier_cache"] = {}

        dossier = None
        if cache_key in st.session_state["dossier_cache"]:
            cached_dossier = st.session_state["dossier_cache"][cache_key]
            c_sec = cached_dossier.get("sector", "")
            c_ind = cached_dossier.get("industry", "")
            # Validate cache for BFSI entities: purge if contaminated by stale manufacturing terms
            if is_bfsi(c_sec, c_ind):
                a1_dump = str(cached_dossier.get("agent_1", {}))
                if any(b in a1_dump.lower() for b in ["inventory", "raw material", "factory", "machinery"]):
                    del st.session_state["dossier_cache"][cache_key]
                    cached_dossier = None
            if cached_dossier:
                dossier = cached_dossier

        if not dossier:
            with st.spinner("Running 7-Agent Institutional Audit..."):
                try:
                    dossier = pipeline.run_pipeline(
                        ticker=ticker,
                        wacc=wacc_input,
                        terminal_growth=terminal_g_input,
                        base_growth=base_g_input
                    )
                    st.session_state["dossier_cache"][cache_key] = dossier
                except Exception as e:
                    err_msg = str(e)
                    if any(k in err_msg.lower() for k in ["rate limit", "429", "resourceexhausted", "quota"]):
                        st.error("🚨 **Gemini API Rate Limit Reached**: The free-tier AI request quota has been temporarily exhausted. Please wait 30–60 seconds before re-trying.")
                        st.info("💡 **Tip**: Running consecutive deep analyses on high-cap companies can trigger temporary API rate limiting. Pausing briefly will reset the quota window.")
                    elif any(k in err_msg.lower() for k in ["failed to retrieve", "not found", "404", "delisted", "quote not found"]):
                        st.error(f"❌ **Stock Ticker Not Found**: yfinance failed to retrieve financial statement data for **'{ticker}'**.")
                        st.info(f"💡 **Tip**: Please verify that the symbol is an active stock listed on the National Stock Exchange of India (NSE) or Bombay Stock Exchange (BSE). Examples: `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.NS`, `CROMPTON.NS`.")
                    else:
                        st.error(f"⚠️ **Analysis Execution Error**: An unexpected error occurred while auditing '{ticker}': {err_msg}")
                        st.info("💡 **Tip**: Please verify your network connection, try an alternate ticker, or refresh the page.")
                    
                    if st.button("← Return to Search Landing", key="err_btn_return"):
                        st.session_state.active_ticker = ""
                        st.rerun()
                    return

        company_name = dossier.get("company_name", ticker)
        sector = dossier.get("sector", "N/A")
        industry = dossier.get("industry", "N/A")
        cmp = dossier.get("current_price", 0.0)
        mcap = dossier.get("market_cap_cr", 0.0)
        pe = dossier.get("trailing_pe", 0.0)
        ev_ebitda = dossier.get("ev_to_ebitda", 0.0)
        high_52 = dossier.get("fifty_two_week_high", 0.0)
        low_52 = dossier.get("fifty_two_week_low", 0.0)
        range_val = f"{low_52:,.0f} - {high_52:,.0f}"
        implied_cagr = dossier.get("implied_growth_pct", "N/A")
        verdict = dossier.get("institutional_rating", "[HOLD / FAIR VALUE]")
        pills = dossier.get("risk_pills", {})

        moat_status = pills.get("Moat & Business", "GREEN")
        forensic_status = pills.get("Forensics", "GREEN")
        solvency_status = pills.get("Solvency", "GREEN")
        gov_status = pills.get("Governance", "GREEN")
        kpi_status = pills.get("Industry KPIs", "GREEN")
        val_status = pills.get("Valuation", "GREEN")

        a0 = dossier.get("agent_0", {})
        a1 = dossier.get("agent_1", {})
        a2 = dossier.get("agent_2", {})
        a3 = dossier.get("agent_3", {})
        a4 = dossier.get("agent_4", {})
        a5 = dossier.get("agent_5", {})
        a6 = dossier.get("agent_6", {})
        a7 = dossier.get("agent_7", {})

        verdict_badge_class = "pill-green" if ("BUY" in verdict.upper() or "ACCUMULATE" in verdict.upper()) else ("pill-yellow" if "HOLD" in verdict.upper() else "pill-red")

        # Glassmorphic Header Card with Verdict Badge
        st.markdown(f"""
        <div class="glass-panel" style="padding: 24px 28px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                <div>
                    <h2 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: #ffffff;">{company_name} <span style="font-size: 1rem; color: #94a3b8; font-weight: 500;">({ticker})</span></h2>
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px; margin-bottom: 0;">{sector} • {industry} • Primary Sector: <strong style="color: #cbd5e1;">{a0.get("primary_sector", "N/A")}</strong></p>
                </div>
                <div>
                    <span class="pill-badge {verdict_badge_class}">{verdict}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        sector_key = dossier.get("sector_key", "CONSUMER_DURABLES_FMCG")
        banned = dossier.get("banned_metrics", [])
        
        # Sector-adaptive labels and metrics for KPI tiles
        if any("trailing p/e" in b.lower() for b in banned) or sector_key == "REAL_ESTATE":
            stat4_tag = "P / NAV"
            stat4_num = a6.get("audit_metrics", {}).get("P/BV Ratio", "N/A")
        else:
            stat4_tag = "Trailing P/E"
            stat4_num = f"{pe:,.1f}x" if pe > 0 else "N/A"

        if any("ev/ebitda" in b.lower() for b in banned) or sector_key in ["BFSI_BANKS", "BFSI_NBFC"]:
            stat5_tag = "P / BV"
            stat5_num = a6.get("audit_metrics", {}).get("P/BV Ratio", "N/A")
        else:
            stat5_tag = "EV / EBITDA"
            stat5_num = f"{ev_ebitda:,.1f}x" if ev_ebitda > 0 else "N/A"

        if any("reverse dcf" in b.lower() or "free cash flow" in b.lower() for b in banned) or sector_key in ["BFSI_BANKS", "BFSI_NBFC"]:
            stat6_tag = "Sustainable RoE"
            stat6_num = a6.get("audit_metrics", {}).get("Valuation Hurdle Metric", str(implied_cagr))
        elif sector_key == "REAL_ESTATE":
            stat6_tag = "Presales Hurdle"
            stat6_num = a6.get("audit_metrics", {}).get("Valuation Hurdle Metric", str(implied_cagr))
        elif sector_key == "METALS_MINING":
            stat6_tag = "Cycle Hurdle"
            stat6_num = a6.get("audit_metrics", {}).get("Valuation Hurdle Metric", str(implied_cagr))
        else:
            stat6_tag = "Implied 10Y FCF"
            stat6_num = f"{implied_cagr}%" if not str(implied_cagr).endswith("%") else str(implied_cagr)

        # 6-Column Glass KPI Grid
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.markdown(f"<div class='glass-stat'><div class='stat-tag'>CMP</div><div class='stat-num'>₹{cmp:,.2f}</div></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='glass-stat'><div class='stat-tag'>Market Cap</div><div class='stat-num'>₹{mcap:,.1f} Cr</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='glass-stat'><div class='stat-tag'>52W Range</div><div class='stat-num'>₹{range_val}</div></div>", unsafe_allow_html=True)
        k4.markdown(f"<div class='glass-stat'><div class='stat-tag'>{stat4_tag}</div><div class='stat-num'>{stat4_num}</div></div>", unsafe_allow_html=True)
        k5.markdown(f"<div class='glass-stat'><div class='stat-tag'>{stat5_tag}</div><div class='stat-num'>{stat5_num}</div></div>", unsafe_allow_html=True)
        k6.markdown(f"<div class='glass-stat'><div class='stat-tag'>{stat6_tag}</div><div class='stat-num'>{stat6_num}</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Glass Risk Strip
        st.markdown(f"""
        <div class="glass-panel" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; padding: 18px 24px; margin-bottom: 24px;">
          <div><span class="stat-tag">Moat & Business</span><br><span class="pill-badge pill-{pill_color(moat_status)}">{moat_status}</span></div>
          <div><span class="stat-tag">Forensics</span><br><span class="pill-badge pill-{pill_color(forensic_status)}">{forensic_status}</span></div>
          <div><span class="stat-tag">Solvency</span><br><span class="pill-badge pill-{pill_color(solvency_status)}">{solvency_status}</span></div>
          <div><span class="stat-tag">Governance</span><br><span class="pill-badge pill-{pill_color(gov_status)}">{gov_status}</span></div>
          <div><span class="stat-tag">Industry KPIs</span><br><span class="pill-badge pill-{pill_color(kpi_status)}">{kpi_status}</span></div>
          <div><span class="stat-tag">Valuation</span><br><span class="pill-badge pill-{pill_color(val_status)}">{val_status}</span></div>
        </div>
        """, unsafe_allow_html=True)

        # Prepare Presentation PDF Data
        pdf_metrics = {
            'sector': sector,
            'primary_valuation': a6.get('primary_valuation', 'Standard Architecture'),
            'implied_cagr': str(implied_cagr),
            'stat4_tag': stat4_tag,
            'stat4_num': stat4_num,
            'stat5_tag': stat5_tag,
            'stat5_num': stat5_num,
            'stat6_tag': stat6_tag,
            'stat6_num': stat6_num,
            'cmp': f"{cmp:,.2f}",
            'mcap': f"{mcap:,.1f}",
            'range': range_val,
            'verdict': verdict
        }

        pdf_pills = {
            'moat': moat_status,
            'forensics': forensic_status,
            'solvency': solvency_status,
            'governance': gov_status,
            'industry': kpi_status,
            'valuation': val_status,
        }

        agent0_pdf_text = f"""• Primary Sector (Assigned 1 of 12): {a0.get('primary_sector')}
• Sub-Vertical: {a0.get('sub_vertical')}
• Revenue Engine (>60% Profit Generator): {a0.get('revenue_engine_summary')}
• Secondary / Hybrid Business Verticals: {', '.join(a0.get('hybrid_verticals', [])) if a0.get('hybrid_verticals') else 'None'}"""

        if is_bfsi(sector, industry):
            p5_pdf_op_label = "Operating Leverage & Branch Efficiency"
            p5_pdf_src_label = "Liability & Deposit Sourcing Risks"
            p5_pdf_cap_label = "Regulatory Capital Buffers (CET-1)"
        else:
            p5_pdf_op_label = "Scalability & Operating Leverage"
            p5_pdf_src_label = "Supply Chain Sourcing Risks"
            p5_pdf_cap_label = "Capital Intensity & Reinvestment"

        agent1_pdf_text = f"""• Core Product / Service: {a1.get('part1_business_model', {}).get('1_core_product_service')}
• Revenue Mechanics: {a1.get('part1_business_model', {}).get('2_revenue_model')}
• Customer Concentration & Switching Costs: {a1.get('part1_business_model', {}).get('3_customer_concentration')} | {a1.get('part1_business_model', {}).get('4_switching_costs')}
• Sales Engine: {a1.get('part1_business_model', {}).get('5_sales_process')}
• Economic Moat Source & Trajectory: {a1.get('part2_competitive_moat', {}).get('2_moat_source')} ({a1.get('part2_competitive_moat', {}).get('3_moat_trajectory')})
• Barriers to Entry: {a1.get('part2_competitive_moat', {}).get('1_barriers_to_entry')}
• Pricing Power & Pass-Through: {a1.get('part2_competitive_moat', {}).get('5_pricing_power')}
• Industry Structural Growth & TAM: {a1.get('part3_industry_growth', {}).get('1_structural_growth')} — {a1.get('part3_industry_growth', {}).get('2_tam_and_headroom')}
• Cyclicality & Recession Resilience: {a1.get('part3_industry_growth', {}).get('3_cyclicality_recession')}
• {p5_pdf_op_label}: {a1.get('part5_operations_scalability', {}).get('1_operating_leverage')}
• {p5_pdf_src_label} & {p5_pdf_cap_label}: {a1.get('part5_operations_scalability', {}).get('2_supply_chain_risks')} | {a1.get('part5_operations_scalability', {}).get('3_capital_intensity')}
• Ground-Level Scuttlebutt: {a1.get('part6_scuttlebutt', {}).get('1_customer_sentiment')} | Workplace Culture: {a1.get('part6_scuttlebutt', {}).get('2_employee_culture')}
• Single Biggest Operational Failure Point: {a1.get('part7_qualitative_risks', {}).get('4_single_biggest_failure_point')}"""

        agent2_pdf_text = f"""• 5-Year Cumulative CFO vs PAT Conversion: {a2.get('part15_revenue_quality', {}).get('3_cfo_pat_divergence')}
• Receivables & DSO Trajectory: {a2.get('part15_revenue_quality', {}).get('2_dso_trajectory')} (Channel Stuffing Check: {a2.get('part15_revenue_quality', {}).get('1_receivables_vs_revenue')})
• Depreciation & Asset Useful Lifespans: {a2.get('part13_depreciation', {}).get('1_useful_lifespan_extension')} | Method: {a2.get('part13_depreciation', {}).get('2_depreciation_method_change')}
• CapEx vs D&A Relationship: {a2.get('part13_depreciation', {}).get('3_capex_vs_da_relationship')}
• SG&A Growth vs Top-Line Revenue: {a2.get('part14_sga_anomalies', {}).get('1_sga_growth_vs_revenue')}
• Stock-Based Compensation & Overhead: {a2.get('part14_sga_anomalies', {}).get('4_stock_based_compensation')} | Miscellany: {a2.get('part14_sga_anomalies', {}).get('5_unexplained_miscellaneous_spikes')}
• Goodwill & Intangible Assets Load: {a2.get('part16_balance_sheet', {}).get('1_goodwill_percentage')}
• Auditor Independence & Pedigree: {a2.get('part16_balance_sheet', {}).get('3_auditor_management_turnover')}"""

        agent3_pdf_text = f"""• Balance Sheet Leverage: Total Debt: Rs. {a3.get('audit_metrics', {}).get('Total Debt')}, Net Debt: Rs. {a3.get('audit_metrics', {}).get('Net Debt')} (Net Debt/Equity: {a3.get('audit_metrics', {}).get('Net Debt / Equity')}, Total Debt/Equity: {a3.get('audit_metrics', {}).get('Total Debt / Equity')})
• Liquid Cash Buffer: Rs. {a3.get('audit_metrics', {}).get('Cash & Equivalents')} in cash and short-term equivalents
• Debt Service Headroom: Normalized Interest Coverage: {a3.get('audit_metrics', {}).get('Normalized Interest Coverage')}
• Working Capital Cycle (Cash Conversion Cycle): {a3.get('audit_metrics', {}).get('Cash Conversion Cycle')} ({a3.get('part11_working_capital', {}).get('1_cash_conversion_cycle')})
• Return on Invested Capital (ROIC): {a3.get('part9_cash_flow_roic', {}).get('5_roic_vs_wacc')}
• Free Cash Flow & Margin: FCF Margin: {a3.get('audit_metrics', {}).get('FCF Margin')} ({a3.get('part9_cash_flow_roic', {}).get('2_fcf_trajectory')})
• FCF Dividend Sustainability: {a3.get('part12_capital_allocation', {}).get('4_dividend_fcf_sustainability')} (Coverage: {a3.get('audit_metrics', {}).get('FCF Dividend Coverage')})"""

        agent4_pdf_text = f"""• Promoter Alignment & Encumbrance: {a4.get('section1_promoter_integrity', {}).get('2_promoter_pledge_percentage')}
• Executive Remuneration vs PAT: {a4.get('section2_executive_remuneration', {}).get('1_ceo_remuneration_vs_pat')} (CEO-to-Median-Employee Ratio: {a4.get('audit_metrics', {}).get('CEO / Median Pay')})
• Incentive Hurdle Alignment: {a4.get('section2_executive_remuneration', {}).get('3_incentive_hurdle_alignment')}
• Politically Exposed Persons (PEP) & Rent-Seeking: {a4.get('section3_pep_rent_seeking', {}).get('1_pep_presence')} | Dependency: {a4.get('section3_pep_rent_seeking', {}).get('2_government_concession_dependency')}
• Master RPT Pricing & Arm's Length Validation: {a4.get('section4_master_rpt', {}).get('pricing_validation', {}).get('pricing_arms_length')}
• Capital Siphoning & Corporate Guarantees: {a4.get('section4_master_rpt', {}).get('capital_siphoning', {}).get('unsecured_loans_to_insiders')} | Guarantees: {a4.get('section4_master_rpt', {}).get('capital_siphoning', {}).get('corporate_guarantees')}
• RPT Revenue & Disclosure Governance: RPT % of Revenue: {a4.get('audit_metrics', {}).get('RPT % of Revenue')} | Audit Committee Sign-Off: {a4.get('section4_master_rpt', {}).get('governance_disclosures', {}).get('audit_committee_preapproval')}"""

        a5_pdf_lines = [f"• {k}: {v}" for k, v in a5.get("kpi_results", {}).items()]
        agent5_pdf_text = f"Sector Checklist Activated: {a5.get('activated_checklist_section')}\n" + "\n".join(a5_pdf_lines)

        inval_pdf_lines = [f"  - {trig}" for trig in a6.get("invalidation_triggers", [])]
        agent6_pdf_text = f"""• Management Walk-the-Talk Audit:
  - Target 1: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_1', {}).get('target', 'Operational Target')} -> {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_1', {}).get('verdict')}
  - Target 2: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_2', {}).get('target', 'Capital Allocation Target')} -> {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_2', {}).get('verdict')}
  - Target 3: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_3', {}).get('target', 'Operating Delivery')} -> {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_3', {}).get('verdict')}
• Independent Asset & Yield Valuation Floors:
"""
        for fl_k, fl_v in a6.get("section2_asset_yield_valuation", {}).items():
            agent6_pdf_text += f"  - {fl_k.replace('_', ' ').title()}: {fl_v}\n"

        agent6_pdf_text += f"• Primary Valuation Architecture: {a6.get('primary_valuation', 'Sector Architecture')}\n"
        for r_k, r_v in a6.get("section3_reverse_dcf", {}).items():
            agent6_pdf_text += f"  - {r_k.replace('_', ' ').title()}: {r_v}\n"

        agent6_pdf_text += f"""• 3-Scenario Valuation Matrix:
  - Bear Case: Target {a6.get('section4_scenario_matrix', {}).get('bear_case', {}).get('fair_target_price')} ({a6.get('section4_scenario_matrix', {}).get('bear_case', {}).get('expected_return')}) | {a6.get('section4_scenario_matrix', {}).get('bear_case', {}).get('growth_assumed')}
  - Base Case: Target {a6.get('section4_scenario_matrix', {}).get('base_case', {}).get('fair_target_price')} ({a6.get('section4_scenario_matrix', {}).get('base_case', {}).get('expected_return')}) | {a6.get('section4_scenario_matrix', {}).get('base_case', {}).get('growth_assumed')}
  - Bull Case: Target {a6.get('section4_scenario_matrix', {}).get('bull_case', {}).get('fair_target_price')} ({a6.get('section4_scenario_matrix', {}).get('bull_case', {}).get('expected_return')}) | {a6.get('section4_scenario_matrix', {}).get('bull_case', {}).get('growth_assumed')}
• Thesis Invalidation Triggers:
""" + "\n".join(inval_pdf_lines)

        pdf_dossier_dict = {
            'risk_pills': pdf_pills,
            'agent0': agent0_pdf_text,
            'agent1': agent1_pdf_text,
            'agent2': agent2_pdf_text,
            'agent3': agent3_pdf_text,
            'agent4': agent4_pdf_text,
            'agent5': agent5_pdf_text,
            'agent6': agent6_pdf_text,
            'agent7': a7,
        }

        # Generate presentation-grade institutional PDF
        pdf_bytes = build_institutional_pdf(
            ticker=ticker,
            company_name=company_name,
            metrics=pdf_metrics,
            dossier_dict={**dossier, **pdf_dossier_dict}
        )

        clean_comp_name = re.sub(r'[\\/*?:"<>|]', '', company_name).strip() if company_name else ticker
        pdf_filename = f"{clean_comp_name} - Equity Research Report.pdf"

        # Institutional Tabbed Breakdown (Retains all audit bullets and triggers)
        tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🏷️ Overview", "🛡️ Moat", "🔍 Forensics", "⚖️ Solvency", "🏛️ Governance", "📈 KPIs", "🎯 Valuation", "🎙️ Concall"
        ])

        with tab0:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown(
                    f'<div class="q-box">'
                    f'<div class="q-title">PRIMARY SECTOR (ASSIGNED 1 OF 12)</div>'
                    f'<div class="q-ans"><strong>{a0.get("primary_sector", "N/A")}</strong></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="q-box">'
                    f'<div class="q-title">SUB-VERTICAL</div>'
                    f'<div class="q-ans">{a0.get("sub_vertical", "N/A")}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_right:
                st.markdown(
                    f'<div class="q-box">'
                    f'<div class="q-title">REVENUE ENGINE SUMMARY (>60% OPERATING PROFIT DRIVER)</div>'
                    f'<div class="q-ans" style="line-height: 1.6;">{a0.get("revenue_engine_summary", "N/A")}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown("##### 🌿 Hybrid / Secondary Business Verticals")
            hybrids = a0.get("hybrid_verticals", [])
            if hybrids:
                for hv in hybrids:
                    st.markdown(f"- {hv}")
            else:
                st.markdown("- *No secondary or hybrid business verticals identified.*")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab1:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown(f"**Moat Classification**: `{a1.get('moat_rating')}` (Checklist Score: **{a1.get('checklist_score')}/100**)")
            t1, t2, t3, t4, t5, t6 = st.tabs([
                "Part 1: Business Model", 
                "Part 2: Economic Moat", 
                "Part 3: Industry & TAM", 
                "Part 5: Scalability", 
                "Part 6: Scuttlebutt", 
                "Part 7: Qualitative Risks"
            ])
            with t1:
                for k, v in a1.get("part1_business_model", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with t2:
                for k, v in a1.get("part2_competitive_moat", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with t3:
                for k, v in a1.get("part3_industry_growth", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with t4:
                p5_items = a1.get("part5_operations_scalability", {})
                if is_bfsi(sector, industry):
                    op_lev_label = "1. OPERATING LEVERAGE & BRANCH EFFICIENCY"
                    sourcing_label = "2. LIABILITY & DEPOSIT SOURCING RISKS"
                    cap_label = "3. REGULATORY CAPITAL CONSUMPTION (CET-1 / RWA)"
                else:
                    op_lev_label = "1. OPERATING LEVERAGE & CAPACITY UTILIZATION"
                    sourcing_label = "2. SUPPLY CHAIN & RAW MATERIAL SOURCING RISKS"
                    cap_label = "3. CAPITAL INTENSITY & REINVESTMENT"

                op_val = p5_items.get("1_operating_leverage") or (
                    "Branch vintage maturation, digital transaction penetration (>90%), and Cost-to-Income trajectory optimization without fixed asset constraints."
                    if is_bfsi(sector, industry) else
                    "Plant capacity utilization, fixed-cost overhead absorption, and incremental volume leverage."
                )
                src_val = p5_items.get("2_supply_chain_risks") or (
                    "Granular retail CASA deposit franchise and wholesale liability diversification with balanced ALM duration matching."
                    if is_bfsi(sector, industry) else
                    "Input cost inflation pass-through capability, vendor diversification, and strategic buffer inventory management."
                )
                cap_val = p5_items.get("3_capital_intensity") or (
                    "CET-1 Tier-1 capital conservation and regulatory capital buffers maintained comfortably above RBI minimums."
                    if is_bfsi(sector, industry) else
                    "Maintenance vs growth CapEx-to-depreciation ratio and internal operating cash flow reinvestment."
                )

                if is_bfsi(sector, industry):
                    for bw, rw in [
                        (r"\braw\s+materials\b", "capital inputs"),
                        (r"\braw\s+material\b", "capital input"),
                        (r"\binventories\b", "liquid assets"),
                        (r"\binventory\b", "liquid assets"),
                        (r"\bfactories\b", "operating facilities"),
                        (r"\bfactory\b", "operating facility"),
                        (r"\bmachineries\b", "operating infrastructure"),
                        (r"\bmachinery\b", "operating infrastructure"),
                        (r"\bsupplier\s+base\b", "liability deposit base"),
                        (r"\bsuppliers\b", "depositors and funding partners"),
                        (r"\bsupplier\b", "funding source"),
                        (r"\bsupply\s+chain\b", "funding and liability sourcing"),
                    ]:
                        op_val = re.sub(bw, rw, str(op_val), flags=re.IGNORECASE)
                        src_val = re.sub(bw, rw, str(src_val), flags=re.IGNORECASE)
                        cap_val = re.sub(bw, rw, str(cap_val), flags=re.IGNORECASE)

                st.markdown(f'<div class="q-box"><div class="q-title">{op_lev_label}</div><div class="q-ans">{op_val}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="q-box"><div class="q-title">{sourcing_label}</div><div class="q-ans">{src_val}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="q-box"><div class="q-title">{cap_label}</div><div class="q-ans">{cap_val}</div></div>', unsafe_allow_html=True)
            with t5:
                for k, v in a1.get("part6_scuttlebutt", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with t6:
                for k, v in a1.get("part7_qualitative_risks", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown(f"**Forensic Status**: {render_risk_pill('Forensics', forensic_status)}", unsafe_allow_html=True)
            st.markdown(f"**Detective Summary**: {a2.get('summary')}")
            m2_items = list(a2.get("audit_metrics", {}).items())
            m2_cols = st.columns(3)
            for idx, (k, v) in enumerate(m2_items):
                m2_cols[idx % 3].metric(k, str(v))

            cfo_pat_data = a2.get("cfo_pat_series", [])
            df_cfo = pd.DataFrame(cfo_pat_data) if cfo_pat_data else pd.DataFrame()
            if isinstance(df_cfo, pd.DataFrame) and not df_cfo.empty and "Year" in df_cfo.columns and "year" not in df_cfo.columns:
                df_cfo = df_cfo.rename(columns={"Year": "year", "Net Profit (PAT)": "pat_cr", "Cash Flow from Operations (CFO)": "cfo_cr"})

            st.markdown("##### 📊 5-Year Cash Flow Divergence (CFO vs Net Profit)")
            # Safe CFO vs PAT chart rendering
            is_bfsi_co = is_bfsi(sector, industry) or sector_key in ["BFSI_BANKS", "BFSI_NBFC"]
            if is_bfsi_co:
                # Banks do not use CFO vs PAT; display Net Interest Income (NII) vs PAT or a clean message
                st.info("Operating Cash Flow (CFO) chart is not applicable for Financial Institutions. Balance sheet and asset quality metrics are audited in the KPIs & Solvency sections.")
            else:
                # For Non-BFSI / Industrial companies, ensure columns exist before plotting
                if isinstance(df_cfo, pd.DataFrame) and not df_cfo.empty and "year" in df_cfo.columns and "pat_cr" in df_cfo.columns:
                    fig_cfo = go.Figure()
                    fig_cfo.add_trace(go.Bar(x=df_cfo["year"], y=df_cfo["pat_cr"], name="PAT (Net Profit ₹ Cr)", marker_color="#38bdf8"))
                    if "cfo_cr" in df_cfo.columns:
                        fig_cfo.add_trace(go.Bar(x=df_cfo["year"], y=df_cfo["cfo_cr"], name="CFO (₹ Cr)", marker_color="#10b981"))
                    fig_cfo.update_layout(
                        barmode="group",
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=10, r=10, t=30, b=10)
                    )
                    st.plotly_chart(fig_cfo, use_container_width=True)
                else:
                    st.warning("Historical CFO/PAT data not available for this ticker.")

            f_tabs = st.tabs(["Part 13: D&A Manipulation", "Part 14: SG&A Anomalies", "Part 15: Revenue Quality (CFO/PAT)", "Part 16: Goodwill & Governance"])
            with f_tabs[0]:
                for k, v in a2.get("part13_depreciation", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with f_tabs[1]:
                for k, v in a2.get("part14_sga_anomalies", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with f_tabs[2]:
                for k, v in a2.get("part15_revenue_quality", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with f_tabs[3]:
                for k, v in a2.get("part16_balance_sheet", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown(f"**Solvency Status**: {render_risk_pill('Solvency', solvency_status)}", unsafe_allow_html=True)
            st.markdown(f"**Assessment**: {a3.get('summary')}")
            m3_items = list(a3.get("audit_metrics", {}).items())
            m3_cols = st.columns(4)
            for idx, (k, v) in enumerate(m3_items):
                m3_cols[idx % 4].metric(k, str(v))

            s_tabs = st.tabs(["Part 8: Profitability", "Part 9: Cash Flow & ROIC vs WACC", "Part 10: Solvency", "Part 11: Working Capital (CCC)", "Part 12: Capital Allocation"])
            with s_tabs[0]:
                for k, v in a3.get("part8_profitability", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with s_tabs[1]:
                for k, v in a3.get("part9_cash_flow_roic", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with s_tabs[2]:
                for k, v in a3.get("part10_solvency", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with s_tabs[3]:
                for k, v in a3.get("part11_working_capital", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with s_tabs[4]:
                for k, v in a3.get("part12_capital_allocation", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab4:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown(f"**Governance Status**: {render_risk_pill('Governance', gov_status)}", unsafe_allow_html=True)
            st.markdown(f"**Audit Findings**: {a4.get('summary')}")
            m4_items = list(a4.get("audit_metrics", {}).items())
            m4_cols = st.columns(3)
            for idx, (k, v) in enumerate(m4_items):
                m4_cols[idx % 3].metric(k, str(v))

            g_tabs = st.tabs(["Section 1: Promoter Integrity & Pledge", "Section 2: Executive Remuneration", "Section 3: PEP & Political Risk", "Section 4: Master RPT Audit"])
            with g_tabs[0]:
                for k, v in a4.get("section1_promoter_integrity", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with g_tabs[1]:
                for k, v in a4.get("section2_executive_remuneration", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with g_tabs[2]:
                for k, v in a4.get("section3_pep_rent_seeking", {}).items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with g_tabs[3]:
                st.markdown("##### 🔍 Master Related Party Transactions (RPT) Matrix")
                rpt = a4.get("section4_master_rpt", {})
                for sub_name, sub_dict in rpt.items():
                    st.markdown(f"**{sub_name.replace('_', ' ').title()}**")
                    for sub_k, sub_v in sub_dict.items():
                        st.markdown(f'<div class="q-box"><div class="q-title">{sub_k.replace("_", " ").upper()}</div><div class="q-ans">{sub_v}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab5:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown(f"**Activated Sector Checklist**: `{a5.get('activated_checklist_section')}`")
            st.markdown(f"**Summary**: {a5.get('summary')}")
            kpi_items = list(a5.get("kpi_results", {}).items())
            kpi_cols = st.columns(2)
            for idx, (k, v) in enumerate(kpi_items):
                kpi_cols[idx % 2].metric(k, str(v))
            st.markdown("</div>", unsafe_allow_html=True)

        with tab6:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown(f"**CIO Final Rating Badge**: `{a6.get('institutional_rating')}`")
            st.markdown(f"**CIO Synthesis**: {a6.get('summary')}")
            cio_tabs = st.tabs(["Section 1: Walk-the-Talk", "Section 2: Asset & Yield Floors", "Section 3: Valuation Architecture", "Section 4: Scenario Matrix", "Invalidation Triggers"])
            with cio_tabs[0]:
                st.markdown("##### 📜 Historical Promise vs Delivery Audit")
                wtt = a6.get("section1_management_walk_the_talk", {})
                for k, v in wtt.items():
                    if isinstance(v, dict):
                        st.markdown(f"**Target**: {v.get('target')}")
                        st.markdown(f"**Actual**: {v.get('actual')}")
                        st.markdown(f"**Delivery Rating**: `{v.get('verdict')}`")
                        st.markdown("---")
                    else:
                        st.markdown(f"**Forward Guidance Realism**: {v}")
            with cio_tabs[1]:
                st.markdown("##### 🛡️ Independent Valuation Floors")
                floors = a6.get("section2_asset_yield_valuation", {})
                for k, v in floors.items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
            with cio_tabs[2]:
                st.markdown(f"##### 🧮 {a6.get('primary_valuation', 'Valuation Architecture & Hurdle Test')}")
                rdcf = a6.get("section3_reverse_dcf", {})
                for k, v in rdcf.items():
                    st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
                dcf_data = a6.get("dcf_model", {})
                sens = dcf_data.get("sensitivity_matrix", {})
                if sens and "matrix" in sens:
                    st.markdown("###### Valuation Sensitivity Matrix (Intrinsic Fair Value per Share ₹)")
                    df_sens = pd.DataFrame(
                        sens["matrix"],
                        index=[str(tg) for tg in sens.get("terminal_growth_labels", [])],
                        columns=[str(w) for w in sens.get("wacc_labels", [])]
                    )
                    st.dataframe(df_sens.style.format("₹{:,.1f}"), use_container_width=True)
            with cio_tabs[3]:
                st.markdown("##### ⚖️ 3-Scenario Valuation Matrix")
                sc_data = a6.get("section4_scenario_matrix", {})
                c_bear, c_base, c_bull = st.columns(3)
                with c_bear:
                    st.metric("BEAR CASE", sc_data.get("bear_case", {}).get("fair_target_price", "N/A"), sc_data.get("bear_case", {}).get("expected_return", "N/A"))
                    st.caption(f"Thesis: {sc_data.get('bear_case', {}).get('thesis')}")
                with c_base:
                    st.metric("BASE CASE", sc_data.get("base_case", {}).get("fair_target_price", "N/A"), sc_data.get("base_case", {}).get("expected_return", "N/A"))
                    st.caption(f"Thesis: {sc_data.get('base_case', {}).get('thesis')}")
                with c_bull:
                    st.metric("BULL CASE", sc_data.get("bull_case", {}).get("fair_target_price", "N/A"), sc_data.get("bull_case", {}).get("expected_return", "N/A"))
                    st.caption(f"Thesis: {sc_data.get('bull_case', {}).get('thesis')}")
            with cio_tabs[4]:
                st.markdown("##### 🚨 Thesis Invalidation Triggers")
                for trig in a6.get("invalidation_triggers", []):
                    st.markdown(f'<div class="bullet-card">❌ {trig}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab7:
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            tone_dict = a7.get("tone_sentiment", {})
            tone_val = tone_dict.get("overall_tone", "Pragmatic")
            integrity_val = tone_dict.get("commitment_integrity", "High")
            tone_color = "#10b981" if "Bullish" in tone_val else ("#f59e0b" if "Defensive" in tone_val else "#38bdf8")

            # Header Banner
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
                <div>
                    <h3 style="margin: 0; font-size: 1.25rem; color: #f8fafc;">🎙️ {a7.get('call_period', 'Latest Fiscal Earnings Conference Call')}</h3>
                    <p style="margin: 2px 0 0 0; font-size: 0.82rem; color: #94a3b8;">Synthesized Institutional Notes, Management Disclosures & Analyst Pushback</p>
                </div>
                <div style="display: flex; gap: 10px;">
                    <span style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); padding: 4px 12px; border-radius: 8px; font-size: 0.82rem; color: {tone_color}; font-weight: 600;">
                        Tone: {tone_val.upper()}
                    </span>
                    <span style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); padding: 4px 12px; border-radius: 8px; font-size: 0.82rem; color: #e2e8f0; font-weight: 600;">
                        Integrity: {integrity_val.upper()}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_sub1, c_sub2, c_sub3, c_sub4 = st.tabs([
                "🎯 Forward Guidance & Targets",
                "⚙️ Sector Operational Disclosures",
                "❓ Analyst Q&A Scrutiny",
                "🎭 Management Tone & Integrity"
            ])

            with c_sub1:
                guidance = a7.get("guidance_summary", {})
                margin_out = a7.get("margin_outlook", {})
                capex = a7.get("capex_plans", {})
                
                c_g1, c_g2 = st.columns(2)
                with c_g1:
                    st.markdown(f'<div class="q-box"><div class="q-title">REVENUE / VOLUME GROWTH TRAJECTORY</div><div class="q-ans">{guidance.get("revenue_growth_target", "N/A")}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-box"><div class="q-title">MARGIN CORRIDOR & SPREAD OUTLOOK</div><div class="q-ans">{margin_out.get("target_corridor", guidance.get("margin_outlook", "N/A"))}</div></div>', unsafe_allow_html=True)
                with c_g2:
                    st.markdown(f'<div class="q-box"><div class="q-title">COMMITTED CAPEX & EXPANSION OUTLAY</div><div class="q-ans">{capex.get("total_outlay_cr", guidance.get("capex_commitments", "N/A"))}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="q-box"><div class="q-title">MEDIUM-TERM STRATEGIC ASPIRATIONS</div><div class="q-ans">{guidance.get("medium_term_aspirations", "Targeting sustainable compounding and margin resilience across credit cycles.")}</div></div>', unsafe_allow_html=True)

                st.markdown("##### 🏗️ CapEx & Commissioning Pipeline")
                st.markdown(f'<div class="bullet-card"><b>Key Projects:</b> {capex.get("key_projects", "Modernization and technology upgrades")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="bullet-card"><b>Timeline:</b> {capex.get("commissioning_timeline", "Phased over 18-24 months")} &bull; <b>Funding:</b> {capex.get("funding_mode", "Internal accruals")}</div>', unsafe_allow_html=True)

            with c_sub2:
                ops = a7.get("operational_disclosures", {})
                st.markdown(f'<div class="q-box"><div class="q-title">SECTOR DISCLOSURE 1</div><div class="q-ans">{ops.get("sector_metric_1", "N/A")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="q-box"><div class="q-title">SECTOR DISCLOSURE 2</div><div class="q-ans">{ops.get("sector_metric_2", "N/A")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="q-box"><div class="q-title">SECTOR DISCLOSURE 3</div><div class="q-ans">{ops.get("sector_metric_3", "N/A")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="bullet-card"><b>Institutional Commentary:</b> {ops.get("commentary", "Management reiterated operating focus and capacity headroom.")}</div>', unsafe_allow_html=True)

            with c_sub3:
                st.markdown("##### 🔍 Top Scrutinized Analyst Q&A Exchanges")
                for idx, qa in enumerate(a7.get("qa_highlights", []), 1):
                    posture = qa.get("posture", "Realistic")
                    p_badge = "pill-green" if posture == "Confident" else ("pill-yellow" if posture == "Realistic" else "pill-red")
                    st.markdown(f"""
                    <div class="q-box" style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; color: #38bdf8; font-size: 0.85rem;">Q{idx}: {qa.get('analyst_institution', 'Institutional Analyst')}</span>
                            <span class="pill-badge {p_badge}" style="font-size: 0.72rem; padding: 2px 8px;">{posture.upper()}</span>
                        </div>
                        <div style="color: #e2e8f0; font-weight: 600; margin-bottom: 6px;">"{qa.get('question')}"</div>
                        <div style="color: #94a3b8; font-size: 0.82rem; margin-bottom: 6px;"><b>Scrutiny Focus:</b> {qa.get('scrutiny_focus')}</div>
                        <div style="color: #cbd5e1; font-size: 0.88rem; background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #3b82f6;">
                            <b>Management Response:</b> {qa.get('management_response')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with c_sub4:
                st.markdown(f'<div class="q-box"><div class="q-title">TONE & SENTIMENT SUMMARY</div><div class="q-ans">{tone_dict.get("summary", "Management displayed balanced operational confidence.")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="q-box"><div class="q-title">GUIDANCE REVISIONS & WALK-BACK WARNINGS</div><div class="q-ans">{tone_dict.get("walkbacks_or_revisions", "No material guidance walk-backs detected.")}</div></div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)


        # Download PDF Button
        st.download_button(
            "📥 Download Institutional Research PDF",
            data=pdf_bytes,
            file_name=pdf_filename,
            mime="application/pdf",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
