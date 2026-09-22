"""
Research Beast — Screener Financial Intelligence Dashboard
100% deterministic mathematical calculations and multi-year financial modeling.
Separates deterministic quantitative figures from context-locked LLM editorial analysis.
"""

import os
import io
import re
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
import streamlit as st
import pandas as pd
import numpy as np

from services.financial_data import extract_pure_symbol
from services.screener_engine import ScreenerEngine
from agents.editorial_agent import EditorialAgent
from utils.symbol_resolver import resolve_ticker, resolve_ticker_info
from pdf_generator import build_institutional_pdf

# -------------------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Research Beast — Screener Financial Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------------------
# Screener.in-Style High-Density Typography & Custom CSS
# -------------------------------------------------------------------------
st.markdown("""
<style>
    /* Suppress Streamlit chrome, deploy buttons, toolbar, and footer */
    header[data-testid="stHeader"],
    .stAppDeployButton,
    footer,
    #MainMenu,
    [data-testid="manage-app-button"],
    .viewerBadge {
        display: none !important;
        visibility: hidden !important;
    }

    /* Container max-width & padding for desktop & mobile */
    .block-container {
        max-width: 1140px !important;
        padding-top: 2.2rem !important;
        padding-bottom: 5rem !important;
    }

    /* Screener Top Header */
    .company-header {
        border-bottom: 1px solid #1e293b;
        padding-bottom: 1.25rem;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .company-name {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 2.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f8fafc;
        margin: 0;
        line-height: 1.2;
    }
    .company-badges {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 0.45rem;
        flex-wrap: wrap;
    }
    .badge-ticker {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.12);
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid rgba(56, 189, 248, 0.25);
    }
    .badge-sector {
        font-size: 0.82rem;
        color: #94a3b8;
        background: #1e293b;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .price-box {
        text-align: right;
    }
    .live-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.95rem;
        font-weight: 700;
        color: #4ade80;
        line-height: 1.2;
    }
    .price-range {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 0.2rem;
    }

    /* Screener "About the Company" Box */
    .about-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.35rem 1.6rem;
        margin-bottom: 1.75rem;
    }
    .about-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.6rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .about-title {
        font-size: 0.88rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
    }
    .exchange-links {
        display: flex;
        gap: 0.75rem;
    }
    .exchange-link {
        font-size: 0.82rem;
        font-weight: 600;
        color: #38bdf8;
        text-decoration: none;
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.22);
        padding: 2px 8px;
        border-radius: 4px;
        transition: all 0.15s ease;
    }
    .exchange-link:hover {
        background: rgba(56, 189, 248, 0.2);
        color: #7dd3fc;
        text-decoration: none;
    }
    .about-overview {
        font-size: 0.95rem;
        line-height: 1.65;
        color: #cbd5e1;
        margin-bottom: 1rem;
    }
    .key-points-list {
        list-style: none;
        padding-left: 0;
        margin: 0;
    }
    .key-point-item {
        font-size: 0.92rem;
        line-height: 1.6;
        color: #cbd5e1;
        margin-bottom: 0.45rem;
        display: flex;
        gap: 0.5rem;
    }
    .key-point-bullet {
        color: #38bdf8;
        font-weight: bold;
    }
    .key-point-category {
        font-weight: 600;
        color: #f1f5f9;
    }

    /* Screener Ratio Grid */
    .ratio-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.75rem;
    }
    @media (max-width: 860px) {
        .ratio-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    .ratio-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 0.85rem 1rem;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    .ratio-label {
        font-size: 0.84rem;
        color: #94a3b8;
        font-weight: 500;
    }
    .ratio-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.98rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .ratio-value-highlight {
        color: #38bdf8;
    }
    .ratio-value-green {
        color: #4ade80;
    }

    /* Compounded Growth Section */
    .growth-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.25rem;
        margin-bottom: 1.75rem;
    }
    @media (max-width: 680px) {
        .growth-container {
            grid-template-columns: 1fr;
        }
    }
    .growth-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.1rem 1.35rem;
    }
    .growth-header {
        font-size: 0.86rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #94a3b8;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem;
        margin-bottom: 0.75rem;
    }
    .growth-row {
        display: flex;
        justify-content: space-between;
        padding: 0.35rem 0;
        font-size: 0.9rem;
        color: #cbd5e1;
    }
    .growth-rate {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #4ade80;
    }
    .growth-rate-neg {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #f87171;
    }

    /* Screener Financial Statement Table */
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 2rem;
        margin-bottom: 0.85rem;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    .section-subtitle {
        font-size: 0.8rem;
        font-weight: normal;
        color: #64748b;
    }
    .screener-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 2rem;
        font-size: 0.9rem;
        background: #0f172a;
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid #1e293b;
    }
    .screener-table th {
        background: #1e293b;
        color: #94a3b8;
        font-weight: 600;
        text-align: right;
        padding: 10px 14px;
        border-bottom: 1px solid #334155;
        font-size: 0.84rem;
        letter-spacing: 0.03em;
    }
    .screener-table th:first-child {
        text-align: left;
    }
    .screener-table td {
        padding: 9px 14px;
        text-align: right;
        border-bottom: 1px solid #1e293b;
        color: #cbd5e1;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
    }
    .screener-table td:first-child {
        text-align: left;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-weight: 500;
        color: #f1f5f9;
    }
    .screener-table tr:hover td {
        background: rgba(30, 41, 59, 0.4);
    }
    .screener-table tr.highlight-row td {
        background: rgba(56, 189, 248, 0.05);
        font-weight: 600;
    }

    /* Editorial Memo Callouts */
    .pros-box {
        background: rgba(34, 197, 94, 0.06);
        border: 1px solid rgba(34, 197, 94, 0.25);
        border-left: 4px solid #22c55e;
        border-radius: 6px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.25rem;
    }
    .cons-box {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.25rem;
    }
    .memo-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.5rem 1.8rem;
        margin-top: 1.5rem;
    }

    /* Verification Badge */
    .audit-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #94a3b8;
        padding: 5px 12px;
        border-radius: 6px;
        background: #0f172a;
        border: 1px solid #1e293b;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------------
# Helper Functions: Formatters
# -------------------------------------------------------------------------
def fmt_cr(val: float) -> str:
    """Formats values in ₹ Crores with comma separators."""
    if val is None or val == 0.0:
        return "₹ 0"
    return f"₹ {val:,.2f} Cr" if val >= 100 else f"₹ {val:,.2f} Cr"


def fmt_curr(val: float) -> str:
    """Formats share price in ₹."""
    if val is None or val == 0.0:
        return "₹ 0.00"
    return f"₹ {val:,.2f}"


def fmt_pct(val: Optional[float]) -> str:
    """Formats percentage or returns N/A."""
    if val is None:
        return "N/A"
    return f"{val:+.1f} %" if val != 0 else "0.0 %"


def build_screener_pl_html(pl_rows: list) -> str:
    """
    Constructs a Screener.in-style horizontal multi-year Profit & Loss HTML table
    with Fiscal Years as columns and statement line items as rows.
    """
    # Filter out empty zero years
    valid_rows = [r for r in pl_rows if not (r.get("sales", 0.0) == 0.0 and r.get("net_profit", 0.0) == 0.0)]
    if not valid_rows:
        return "<p style='color: #94a3b8;'>Historical multi-year financial records not available.</p>"

    years = [str(r.get("year", "")) for r in valid_rows]

    # Metrics definition: (Label, key, is_percentage, is_highlight)
    metrics_def = [
        ("Sales", "sales", False, False),
        ("Expenses", "expenses", False, False),
        ("Operating Profit", "op_profit", False, True),
        ("OPM %", "opm_pct", True, False),
        ("Interest", "interest", False, False),
        ("Net Profit", "net_profit", False, True),
        ("EPS in Rs", "eps", False, False),
    ]

    header_cols = "".join([f"<th>{y}</th>" for y in years])
    html = [
        '<table class="screener-table">',
        f"<thead><tr><th>Line Item (₹ Cr)</th>{header_cols}</tr></thead>",
        "<tbody>"
    ]

    for label, key, is_pct, is_hl in metrics_def:
        row_cls = "highlight-row" if is_hl else ""
        row_cells = [f"<td>{label}</td>"]
        for r in valid_rows:
            val = r.get(key, 0.0)
            if is_pct:
                txt = f"{val:.1f}%"
            elif key == "eps":
                txt = f"{val:,.2f}"
            else:
                txt = f"{val:,.1f}"
            row_cells.append(f"<td>{txt}</td>")
        html.append(f"<tr class='{row_cls}'>{''.join(row_cells)}</tr>")

    html.append("</tbody></table>")
    return "\n".join(html)


# -------------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------------
if "screener_data" not in st.session_state:
    st.session_state["screener_data"] = None
if "about_data" not in st.session_state:
    st.session_state["about_data"] = None
if "editorial_memo" not in st.session_state:
    st.session_state["editorial_memo"] = None
if "active_symbol" not in st.session_state:
    st.session_state["active_symbol"] = ""
if "resolved_from" not in st.session_state:
    st.session_state["resolved_from"] = ""


# -------------------------------------------------------------------------
# Search & Quick Benchmark Bar
# -------------------------------------------------------------------------
st.markdown("### 📈 Research Beast — Screener Financial Intelligence")

col_search, col_btn = st.columns([4, 1])
with col_search:
    ticker_input = st.text_input(
        "Search Indian Stock / Ticker:",
        value=st.session_state.get("active_symbol", ""),
        placeholder="Enter symbol or company name (e.g., vinati organics, tata motors, HDFCBANK, CROMPTON)...",
        label_visibility="collapsed"
    )

with col_btn:
    analyze_click = st.button("Audit Stock", use_container_width=True, type="primary")

# Quick Benchmark Chips
st.markdown(
    "<div style='font-size: 0.8rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.4rem;'>"
    "Quick Select:</div>",
    unsafe_allow_html=True
)
qs_cols = st.columns(6)
quick_tickers = ["VINATIORGA", "TATAMOTORS", "HDFCBANK", "CROMPTON", "RELIANCE", "INFY"]
for idx, q_sym in enumerate(quick_tickers):
    if qs_cols[idx].button(q_sym, key=f"qs_{q_sym}", use_container_width=True):
        st.session_state["active_symbol"] = q_sym
        st.rerun()


# -------------------------------------------------------------------------
# Trigger Pipeline Analysis with Auto-Symbol Resolution
# (ONLY executes upon explicit 'Audit Stock' button click)
# -------------------------------------------------------------------------
if analyze_click:
    raw_user_input = ticker_input.strip()
    if raw_user_input:
        resolved_sym, matched_name = resolve_ticker_info(raw_user_input)
        clean_sym = extract_pure_symbol(resolved_sym) or resolved_sym

        if clean_sym:
            st.session_state["active_symbol"] = clean_sym
            is_resolved = clean_sym.upper() != raw_user_input.upper()
            st.session_state["resolved_from"] = raw_user_input if is_resolved else ""

            # Display clean status message indicating security matching
            if is_resolved:
                status_msg = f"Analyzing {clean_sym} (resolved from '{raw_user_input}')..."
            else:
                status_msg = f"Extracting fundamentals and computing deterministic ratios for {clean_sym}..."

            with st.spinner(status_msg):
                try:
                    # 1. Deterministic Calculation
                    scr_data = ScreenerEngine.get_screener_data(clean_sym)
                    st.session_state["screener_data"] = scr_data

                    # 2. Screener "About the Company" Synthesis
                    agent = EditorialAgent()
                    about_data = agent.generate_screener_about(
                        summary_text=scr_data["raw_summary"],
                        company_name=scr_data["company_name"],
                        sector=scr_data["sector"],
                        industry=scr_data["industry"]
                    )
                    st.session_state["about_data"] = about_data

                    # 3. Qualitative Context-Locked Editorial Memo
                    memo = agent.generate_editorial_memo(scr_data)
                    st.session_state["editorial_memo"] = memo

                except Exception as exc:
                    st.error(f"Error computing financial models for {clean_sym}: {str(exc)}")
        else:
            st.error(f"Could not resolve a valid stock symbol for '{raw_user_input}'.")
    else:
        st.warning("Please enter a company name or stock symbol before clicking 'Audit Stock'.")


# -------------------------------------------------------------------------
# Render Screener Dashboard View (Only when audit data exists)
# -------------------------------------------------------------------------
data = st.session_state.get("screener_data")
about = st.session_state.get("about_data")
memo = st.session_state.get("editorial_memo")

if data:
    company_name = data.get("company_name", "Corporate Enterprise")
    raw_sym = data.get("raw_symbol", "")
    clean_sym = data.get("clean_symbol", "")
    sector = data.get("sector", "")
    industry = data.get("industry", "")
    website = data.get("website", "")
    bse_url = data.get("bse_url", "")
    nse_url = data.get("nse_url", "")

    cmp = data.get("current_price", 0.0)
    mcap_cr = data.get("market_cap_cr", 0.0)
    high_52 = data.get("high_52w", 0.0)
    low_52 = data.get("low_52w", 0.0)

    # ---------------------------------------------------------------------
    # 1. Screener Header: Company Name, Ticker, Live Price, 52W High/Low
    # ---------------------------------------------------------------------
    st.markdown(f"""
    <div class="company-header">
        <div>
            <h1 class="company-name">{company_name}</h1>
            <div class="company-badges">
                <span class="badge-ticker">{clean_sym}</span>
                {f'<span class="badge-sector">{sector}</span>' if sector else ''}
                {f'<span class="badge-sector">{industry}</span>' if industry and industry != sector else ''}
            </div>
        </div>
        <div class="price-box">
            <div class="live-price">{fmt_curr(cmp)}</div>
            <div class="price-range">52W High / Low: <strong>{fmt_curr(high_52)}</strong> / <strong>{fmt_curr(low_52)}</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Resolved query notice if applicable
    resolved_from = st.session_state.get("resolved_from", "")
    if resolved_from:
        st.markdown(
            f'<div style="font-size: 0.84rem; color: #38bdf8; margin-top: -0.75rem; margin-bottom: 1rem;">'
            f'🔍 Matched security for: <strong>"{resolved_from}"</strong></div>',
            unsafe_allow_html=True
        )

    # Verification Banner
    st.markdown(f"""
    <div class="audit-badge">
        <span>🛡️</span>
        <span>100% Deterministic Financial Engine</span>
        <span>•</span>
        <span>Zero Numerical Hallucinations</span>
        <span>•</span>
        <span>Primary Tabular Ingestion</span>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 2. Dedicated Screener "About the Company" Section
    # Positioned directly beneath top header and above Key Ratios grid
    # ---------------------------------------------------------------------
    overview_text = about.get("overview", "") if about else data.get("raw_summary", "")
    key_points = about.get("key_points", []) if about else []

    # Format exchange & website links
    links_html = []
    if website:
        links_html.append(f'<a class="exchange-link" href="{website}" target="_blank" rel="noopener noreferrer">🌐 Website ↗</a>')
    if bse_url:
        links_html.append(f'<a class="exchange-link" href="{bse_url}" target="_blank" rel="noopener noreferrer">🏛️ BSE ↗</a>')
    if nse_url:
        links_html.append(f'<a class="exchange-link" href="{nse_url}" target="_blank" rel="noopener noreferrer">🏛️ NSE ↗</a>')
    links_bar = f'<div class="exchange-links">{"".join(links_html)}</div>'

    # Format Key Business Points
    kp_items_html = []
    for cat, detail in key_points:
        kp_items_html.append(
            f'<li class="key-point-item">'
            f'<span class="key-point-bullet">•</span>'
            f'<span><span class="key-point-category">{cat}:</span> {detail}</span>'
            f'</li>'
        )
    kp_list_html = f'<ul class="key-points-list">{"".join(kp_items_html)}</ul>' if kp_items_html else ""

    st.markdown(f"""
    <div class="about-card">
        <div class="about-header">
            <span class="about-title">About the Company</span>
            {links_bar}
        </div>
        <div class="about-overview">{overview_text}</div>
        {kp_list_html}
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 3. Screener Key Ratios Grid (4x3 High-Density Cards)
    # ---------------------------------------------------------------------
    pe = data.get("pe_ratio", 0.0)
    pb = data.get("pb_ratio", 0.0)
    bv = data.get("book_value", 0.0)
    div_y = data.get("dividend_yield_pct", 0.0)
    roce = data.get("roce_pct", 0.0)
    roe = data.get("roe_pct", 0.0)
    fv = data.get("face_value", 1.0)
    de = data.get("debt_to_equity", 0.0)
    opm = data.get("opm_pct", 0.0)

    st.markdown(f"""
    <div class="ratio-grid">
        <div class="ratio-card">
            <span class="ratio-label">Market Cap</span>
            <span class="ratio-value ratio-value-highlight">₹ {mcap_cr:,.1f} Cr</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Current Price</span>
            <span class="ratio-value ratio-value-green">₹ {cmp:,.2f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">High / Low</span>
            <span class="ratio-value">₹ {high_52:,.0f} / {low_52:,.0f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Stock P/E</span>
            <span class="ratio-value">{pe:.1f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Book Value</span>
            <span class="ratio-value">₹ {bv:,.1f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Dividend Yield</span>
            <span class="ratio-value">{div_y:.2f} %</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">ROCE</span>
            <span class="ratio-value ratio-value-green">{roce:.1f} %</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">ROE</span>
            <span class="ratio-value ratio-value-green">{roe:.1f} %</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Face Value</span>
            <span class="ratio-value">₹ {fv:.1f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Price to Book</span>
            <span class="ratio-value">{pb:.2f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">Debt to Equity</span>
            <span class="ratio-value">{de:.2f}</span>
        </div>
        <div class="ratio-card">
            <span class="ratio-label">OPM</span>
            <span class="ratio-value ratio-value-highlight">{opm:.1f} %</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 4. Compounded Growth Rates (Sales & Profit)
    # ---------------------------------------------------------------------
    s_3y = data.get("sales_cagr_3y")
    s_5y = data.get("sales_cagr_5y")
    p_3y = data.get("profit_cagr_3y")
    p_5y = data.get("profit_cagr_5y")

    s_3y_cls = "growth-rate" if (s_3y and s_3y >= 0) else "growth-rate-neg"
    s_5y_cls = "growth-rate" if (s_5y and s_5y >= 0) else "growth-rate-neg"
    p_3y_cls = "growth-rate" if (p_3y and p_3y >= 0) else "growth-rate-neg"
    p_5y_cls = "growth-rate" if (p_5y and p_5y >= 0) else "growth-rate-neg"

    st.markdown(f"""
    <div class="growth-container">
        <div class="growth-card">
            <div class="growth-header">Compounded Sales Growth</div>
            <div class="growth-row">
                <span>5 Years:</span>
                <span class="{s_5y_cls}">{fmt_pct(s_5y)}</span>
            </div>
            <div class="growth-row">
                <span>3 Years:</span>
                <span class="{s_3y_cls}">{fmt_pct(s_3y)}</span>
            </div>
        </div>
        <div class="growth-card">
            <div class="growth-header">Compounded Profit Growth</div>
            <div class="growth-row">
                <span>5 Years:</span>
                <span class="{p_5y_cls}">{fmt_pct(p_5y)}</span>
            </div>
            <div class="growth-row">
                <span>3 Years:</span>
                <span class="{p_3y_cls}">{fmt_pct(p_3y)}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 5. Multi-Year Historical Profit & Loss Statement
    # ---------------------------------------------------------------------
    st.markdown("""
    <div class="section-title">
        <span>Profit & Loss</span>
        <span class="section-subtitle">Consolidated figures in ₹ Crores</span>
    </div>
    """, unsafe_allow_html=True)

    pl_html = build_screener_pl_html(data.get("pl_rows", []))
    st.markdown(pl_html, unsafe_allow_html=True)

    # Optional CSV download of raw tabular data
    pl_df = data.get("pl_dataframe")
    if pl_df is not None and not pl_df.empty:
        csv_buffer = io.StringIO()
        pl_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Profit & Loss CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{raw_sym}_profit_and_loss.csv",
            mime="text/csv",
        )

    # ---------------------------------------------------------------------
    # 6. Qualitative Context-Locked Editorial Memo
    # ---------------------------------------------------------------------
    st.markdown("""
    <div class="section-title">
        <span>Editorial Investment Thesis & Institutional Analysis</span>
        <span class="section-subtitle">Context-Locked Qualitative Synthesis</span>
    </div>
    """, unsafe_allow_html=True)

    if memo:
        st.markdown(f'<div class="memo-card">\n\n{memo}\n\n</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 7. Institutional Dossier & PDF Export
    # ---------------------------------------------------------------------
    st.write("")
    st.divider()

    col_pdf, col_raw = st.columns([1, 1])
    with col_pdf:
        st.markdown("##### 📄 Export Research Dossier")
        st.caption("Generate a publication-grade, SEBI-compliant institutional PDF report.")
        try:
            pdf_bytes = build_institutional_pdf(
                ticker=clean_sym,
                company_name=company_name,
                metrics={
                    "current_price": cmp,
                    "market_cap_cr": mcap_cr,
                    "pe_ratio": pe,
                    "pb_ratio": pb,
                    "roce_pct": roce,
                    "roe_pct": roe,
                    "debt_to_equity": de,
                    "opm_pct": opm,
                },
                dossier_dict={
                    "ticker": clean_sym,
                    "company_name": company_name,
                    "current_price": cmp,
                    "sector": sector,
                    "industry": industry,
                    "screener_data": data,
                    "memo": memo
                }
            )
            st.download_button(
                label="📥 Download Publication PDF",
                data=pdf_bytes,
                file_name=f"{raw_sym}_Institutional_Research.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as p_err:
            st.caption(f"PDF exporter notice: {p_err}")

    with col_raw:
        st.markdown("##### 🔍 Verified Deterministic JSON Context")
        st.caption("The exact mathematically pre-calculated context fed to LLMs to prevent hallucinations.")
        with st.expander("View Numerical JSON"):
            st.json(data.get("json_context", {}))
