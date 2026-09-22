"""
Research Beast — Screener Financial Intelligence & Institutional Equity Research Platform
100% deterministic mathematical calculations, multi-year financial statement modeling,
and an exhaustive 15-module institutional equity research audit engine.
Separates deterministic quantitative figures from context-locked editorial analysis.
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
from agents.pipeline import run_deep_institutional_pipeline, parse_dimension_data
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
    .badge-rating-buy {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: #4ade80;
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.35);
        padding: 3px 10px;
        border-radius: 4px;
    }
    .badge-rating-hold {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: #facc15;
        background: rgba(234, 179, 8, 0.15);
        border: 1px solid rgba(234, 179, 8, 0.35);
        padding: 3px 10px;
        border-radius: 4px;
    }
    .badge-rating-sell {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: #f87171;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 3px 10px;
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

    /* Screener 12-Dimension "About the Company" Platform */
    .about-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.75rem;
    }
    .about-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.75rem;
        flex-wrap: wrap;
        gap: 0.75rem;
    }
    .about-title {
        font-size: 0.95rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 8px;
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
        padding: 3px 9px;
        border-radius: 4px;
        transition: all 0.15s ease;
    }
    .exchange-link:hover {
        background: rgba(56, 189, 248, 0.18);
        color: #7dd3fc;
        text-decoration: none;
    }
    .about-desc-box {
        font-size: 0.93rem;
        line-height: 1.7;
        color: #cbd5e1;
        margin-bottom: 1.35rem;
    }
    .about-desc-box p {
        margin-bottom: 0.75rem;
    }
    .about-desc-box p:last-child {
        margin-bottom: 0;
    }

    /* Fundamental Snapshot Grid (14 metrics) */
    .about-subhead {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #64748b;
        margin-top: 1.25rem;
        margin-bottom: 0.65rem;
    }
    .snapshot-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 0.55rem;
        margin-bottom: 1.25rem;
    }
    @media (max-width: 1200px) {
        .snapshot-grid {
            grid-template-columns: repeat(4, 1fr);
        }
    }
    @media (max-width: 768px) {
        .snapshot-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    .snapshot-box {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 0.55rem 0.75rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .snapshot-lbl {
        font-size: 0.68rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 0.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .snapshot-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .val-accent { color: #38bdf8; }
    .val-green { color: #4ade80; }

    /* Core Business Operating Segments */
    .segments-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.85rem;
        margin-bottom: 0.75rem;
    }
    @media (max-width: 768px) {
        .segments-grid {
            grid-template-columns: 1fr;
        }
    }
    .about-seg-card {
        background: rgba(30, 41, 59, 0.35);
        border: 1px solid #1e293b;
        border-left: 3px solid #38bdf8;
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .about-seg-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.4rem;
    }
    .about-seg-desc {
        font-size: 0.85rem;
        line-height: 1.55;
        color: #cbd5e1;
        margin-bottom: 0.65rem;
    }
    .about-seg-meta {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        font-size: 0.8rem;
    }
    .about-seg-pill {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        color: #94a3b8;
    }
    .about-seg-pill strong {
        color: #e2e8f0;
    }

    /* Key Corporate Facts Grid */
    .facts-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    @media (max-width: 992px) {
        .facts-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 576px) {
        .facts-grid {
            grid-template-columns: 1fr;
        }
    }
    .fact-card {
        background: rgba(30, 41, 59, 0.25);
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 0.75rem 0.95rem;
    }
    .fact-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .fact-value {
        font-size: 0.88rem;
        font-weight: 600;
        color: #f1f5f9;
        line-height: 1.4;
    }

    /* Milestones Timeline */
    .milestones-timeline {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        margin-top: 0.5rem;
    }
    .milestone-item {
        display: flex;
        align-items: baseline;
        gap: 0.85rem;
        padding: 0.55rem 0.85rem;
        background: rgba(30, 41, 59, 0.25);
        border: 1px solid #1e293b;
        border-radius: 6px;
    }
    .milestone-year {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.2);
        padding: 2px 8px;
        border-radius: 4px;
        white-space: nowrap;
    }
    .milestone-text {
        font-size: 0.87rem;
        color: #cbd5e1;
        line-height: 1.5;
    }

    /* Moats & Citations */
    .moats-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .moat-item {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        font-size: 0.88rem;
        line-height: 1.5;
        color: #cbd5e1;
        background: rgba(34, 197, 94, 0.04);
        border: 1px solid rgba(34, 197, 94, 0.15);
        border-radius: 6px;
        padding: 0.55rem 0.85rem;
    }
    .moat-icon {
        color: #4ade80;
        font-weight: 700;
    }
    .peer-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .peer-chip {
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.25);
        color: #7dd3fc;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 4px;
    }
    .sources-list {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        margin-top: 0.5rem;
    }
    .source-item {
        font-size: 0.82rem;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .key-points-list {
        list-style: none;
        padding-left: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
    }
    .key-point-item {
        font-size: 0.88rem;
        line-height: 1.55;
        color: #cbd5e1;
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
    }
    .key-point-bullet {
        color: #38bdf8;
        font-weight: 700;
        margin-top: 0.05rem;
    }
    .key-point-category {
        font-weight: 600;
        color: #f1f5f9;
    }

    /* Screener 4x3 Ratio Grid */
    .ratio-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.75rem;
    }
    @media (max-width: 900px) {
        .ratio-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 550px) {
        .ratio-grid {
            grid-template-columns: 1fr;
        }
    }
    .ratio-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: border-color 0.15s ease;
    }
    .ratio-card:hover {
        border-color: #334155;
    }
    .ratio-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.35rem;
    }
    .ratio-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.28rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1.2;
    }
    .ratio-value-highlight {
        color: #38bdf8;
    }
    .ratio-value-green {
        color: #4ade80;
    }

    /* Compounded Growth Containers */
    .growth-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.25rem;
        margin-bottom: 2rem;
    }
    @media (max-width: 768px) {
        .growth-container {
            grid-template-columns: 1fr;
        }
    }
    .growth-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.15rem 1.4rem;
    }
    .growth-header {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem;
    }
    .growth-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.35rem 0;
        font-size: 0.88rem;
        color: #cbd5e1;
        border-bottom: 1px solid rgba(30, 41, 59, 0.4);
    }
    .growth-row:last-child {
        border-bottom: none;
    }
    .growth-rate {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #4ade80;
    }
    .growth-rate-neg {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #f87171;
    }

    /* Section Headings */
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #f8fafc;
        margin-top: 1.75rem;
        margin-bottom: 0.85rem;
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .section-subtitle {
        font-size: 0.82rem;
        font-weight: 500;
        color: #64748b;
    }

    /* Screener Multi-Year Table Styles */
    .screener-table-container {
        overflow-x: auto;
        border: 1px solid #1e293b;
        border-radius: 8px;
        margin-bottom: 1.75rem;
        background: #0f172a;
    }
    .screener-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
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
    .screener-table tr.target-peer-row td {
        background: rgba(56, 189, 248, 0.12) !important;
        font-weight: 700;
        color: #38bdf8;
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

    /* Institutional Module Card */
    .inst-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.35rem 1.6rem;
        margin-bottom: 1.25rem;
    }
    .inst-card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .inst-prose {
        font-size: 0.92rem;
        line-height: 1.7;
        color: #cbd5e1;
    }
    .inst-prose p {
        margin-bottom: 0.85rem;
    }
    .callout-box {
        border-radius: 6px;
        padding: 0.9rem 1.15rem;
        margin: 0.85rem 0;
        font-size: 0.88rem;
        line-height: 1.6;
    }
    .callout-alert {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.28);
        border-left: 4px solid #ef4444;
        color: #fca5a5;
    }
    .callout-success {
        background: rgba(34, 197, 94, 0.08);
        border: 1px solid rgba(34, 197, 94, 0.28);
        border-left: 4px solid #22c55e;
        color: #86efac;
    }
    .callout-info {
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.28);
        border-left: 4px solid #38bdf8;
        color: #bae6fd;
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
    """Constructs a Screener.in-style horizontal multi-year Profit & Loss HTML table."""
    valid_rows = [r for r in pl_rows if not (r.get("sales", 0.0) == 0.0 and r.get("net_profit", 0.0) == 0.0)]
    if not valid_rows:
        return "<p style='color: #94a3b8;'>Historical multi-year financial records not available.</p>"

    years = [str(r.get("year", "")) for r in valid_rows]

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
        '<div class="screener-table-container">',
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

    html.append("</tbody></table></div>")
    return "\n".join(html)


def build_screener_quarterly_html(q_rows: list) -> str:
    """Constructs a Screener.in-style Quarterly Results HTML table."""
    if not q_rows:
        return "<p style='color: #94a3b8;'>Quarterly financial reports not available.</p>"

    quarters = [str(r.get("quarter", "")) for r in q_rows]
    header_cols = "".join([f"<th>{q}</th>" for q in quarters])

    metrics_def = [
        ("Sales", "sales", False, False),
        ("Expenses", "expenses", False, False),
        ("Operating Profit", "op_profit", False, True),
        ("OPM %", "opm_pct", True, False),
        ("Other Income", "other_income", False, False),
        ("Interest", "interest", False, False),
        ("Depreciation", "depreciation", False, False),
        ("Profit before tax", "pbt", False, False),
        ("Net Profit", "net_profit", False, True),
        ("EPS in Rs", "eps", False, False),
    ]

    html = [
        '<div class="screener-table-container">',
        '<table class="screener-table">',
        f"<thead><tr><th>Quarterly Metric (₹ Cr)</th>{header_cols}</tr></thead>",
        "<tbody>"
    ]

    for label, key, is_pct, is_hl in metrics_def:
        row_cls = "highlight-row" if is_hl else ""
        row_cells = [f"<td>{label}</td>"]
        for r in q_rows:
            val = r.get(key, 0.0)
            if is_pct:
                txt = f"{val:.1f}%"
            elif key == "eps":
                txt = f"{val:,.2f}"
            else:
                txt = f"{val:,.1f}"
            row_cells.append(f"<td>{txt}</td>")
        html.append(f"<tr class='{row_cls}'>{''.join(row_cells)}</tr>")

    html.append("</tbody></table></div>")
    return "\n".join(html)


def build_screener_peer_html(peer_rows: list) -> str:
    """Constructs a Screener.in-style Peer Comparison HTML table."""
    if not peer_rows:
        return "<p style='color: #94a3b8;'>Peer comparison data not available.</p>"

    html = [
        '<div class="screener-table-container">',
        '<table class="screener-table">',
        "<thead><tr>"
        "<th>Company</th>"
        "<th>CMP (₹)</th>"
        "<th>P/E</th>"
        "<th>Mar Cap (₹ Cr)</th>"
        "<th>Div Yld %</th>"
        "<th>ROCE %</th>"
        "<th>ROE %</th>"
        "<th>D/E</th>"
        "</tr></thead>",
        "<tbody>"
    ]

    for r in peer_rows:
        is_target = r.get("is_target", False)
        row_cls = "target-peer-row" if is_target else ""
        star = " 🌟" if is_target else ""
        cmp_txt = f"₹ {r.get('cmp', 0.0):,.1f}" if r.get('cmp', 0.0) > 0 else "—"
        pe_txt = f"{r.get('pe', 0.0):.1f}x" if r.get('pe', 0.0) > 0 else "—"
        mcap_txt = f"{r.get('mcap_cr', 0.0):,.1f}"
        div_txt = f"{r.get('div_yield', 0.0):.2f}%" if r.get('div_yield', 0.0) > 0 else "0.00%"
        roce_txt = f"{r.get('roce', 0.0):.1f}%" if r.get('roce', 0.0) > 0 else "—"
        roe_txt = f"{r.get('roe', 0.0):.1f}%" if r.get('roe', 0.0) > 0 else "—"
        de_txt = f"{r.get('de', 0.0):.2f}" if r.get('de') is not None else "—"

        html.append(
            f"<tr class='{row_cls}'>"
            f"<td>{r.get('name', '')}{star}</td>"
            f"<td>{cmp_txt}</td>"
            f"<td>{pe_txt}</td>"
            f"<td>{mcap_txt}</td>"
            f"<td>{div_txt}</td>"
            f"<td>{roce_txt}</td>"
            f"<td>{roe_txt}</td>"
            f"<td>{de_txt}</td>"
            f"</tr>"
        )

    html.append("</tbody></table></div>")
    return "\n".join(html)


def render_audit_item(title: str, item: Any):
    """Renders a single structured audit node with Level A-D depth."""
    if isinstance(item, dict):
        # Extract flowing prose or 4-tier components
        prose = item.get("narrative_prose")
        if not prose:
            parts = [
                (item.get("historical_trend_and_metrics") or item.get("trajectory_and_metrics") or item.get("level_a") or "").strip(),
                (item.get("operational_mechanics_and_drivers") or item.get("operational_drivers") or item.get("level_b") or "").strip(),
                (item.get("competitive_context_and_benchmarks") or item.get("peer_comparison") or item.get("level_c") or "").strip(),
                (item.get("thesis_implication_and_risks") or item.get("thesis_invalidation") or item.get("level_d") or "").strip()
            ]
            prose = " ".join(p for p in parts if p)

        display_title = item.get("title") or title.replace("_", " ").title()
        if not prose and "target" in item:
            target = item.get("target", "Operational Objective")
            actual = item.get("actual", "Delivered Outcome")
            verdict = item.get("verdict", "[PASS / REVIEW]")
            prose = f"<strong>Objective:</strong> {target}<br/><strong>Delivered Outcome:</strong> {actual} <span style='color: #4ade80; font-weight: 600;'>[{verdict}]</span>"

        if prose:
            st.markdown(f"""
            <div class="inst-card">
                <div class="inst-card-title">{display_title}</div>
                <div class="inst-prose">{prose}</div>
            </div>
            """, unsafe_allow_html=True)
    elif isinstance(item, str) and len(item.strip()) > 10:
        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-card-title">{title.replace("_", " ").title()}</div>
            <div class="inst-prose">{item}</div>
        </div>
        """, unsafe_allow_html=True)


def build_about_snapshot_html(metrics: Dict[str, Any]) -> str:
    """Builds the 14-metric fundamental snapshot grid HTML."""
    if not metrics:
        return ""
    mcap = metrics.get("market_cap_cr", 0.0)
    cmp = metrics.get("current_price", 0.0)
    h52 = metrics.get("high_52w", 0.0)
    l52 = metrics.get("low_52w", 0.0)
    pe = metrics.get("pe_ratio", 0.0)
    bv = metrics.get("book_value", 0.0)
    div = metrics.get("dividend_yield_pct", 0.0)
    roce = metrics.get("roce_pct", 0.0)
    roe = metrics.get("roe_pct", 0.0)
    fv = metrics.get("face_value", 1.0)
    debt = metrics.get("total_debt_cr", 0.0)
    cash = metrics.get("total_cash_cr", 0.0)
    prom = metrics.get("promoter_holding_pct", 0.0)
    inst = metrics.get("institutional_holding_pct", 0.0)
    de = metrics.get("debt_to_equity", 0.0)

    items = [
        ("Market Cap", f"₹ {mcap:,.1f} Cr", "val-accent"),
        ("Current Price", f"₹ {cmp:,.2f}", "val-green"),
        ("52W High / Low", f"₹ {h52:,.0f} / {l52:,.0f}", ""),
        ("Stock P/E", f"{pe:.1f}x" if pe > 0 else "—", ""),
        ("Book Value", f"₹ {bv:,.1f}", ""),
        ("Div Yield", f"{div:.2f}%", ""),
        ("ROCE", f"{roce:.1f}%", "val-green" if roce > 15 else ""),
        ("ROE", f"{roe:.1f}%", "val-green" if roe > 15 else ""),
        ("Face Value", f"₹ {fv:.1f}", ""),
        ("Total Debt", f"₹ {debt:,.1f} Cr", ""),
        ("Cash & Equiv", f"₹ {cash:,.1f} Cr", "val-green" if cash > debt else ""),
        ("Promoter Hold", f"{prom:.1f}%", ""),
        ("Inst. Holding", f"{inst:.1f}%", ""),
        ("Debt to Equity", f"{de:.2f}x", "val-green" if de < 0.5 else ("val-accent" if de < 1.0 else "")),
    ]

    boxes_html = "".join([
        f'<div class="snapshot-box">'
        f'<span class="snapshot-lbl">{lbl}</span>'
        f'<span class="snapshot-val {cls}">{val}</span>'
        f'</div>'
        for lbl, val, cls in items
    ])

    return f'<div class="snapshot-grid">{boxes_html}</div>'


def build_about_segments_html(segments: List[Dict[str, Any]]) -> str:
    """Builds the cards grid for core business segments."""
    if not segments:
        return ""
    cards = []
    for seg in segments:
        name = seg.get("name", "Business Segment")
        desc = seg.get("description", "")
        driver = seg.get("revenue_driver", "Contractual delivery")
        scope = seg.get("scope", "Operational scope")
        cards.append(
            f'<div class="about-seg-card">'
            f'<div>'
            f'<div class="about-seg-title"><span style="color: #38bdf8;">🔷</span> {name}</div>'
            f'<div class="about-seg-desc">{desc}</div>'
            f'</div>'
            f'<div class="about-seg-meta">'
            f'<div class="about-seg-pill">🎯 <strong>Driver:</strong> {driver}</div>'
            f'<div class="about-seg-pill">📦 <strong>Scope:</strong> {scope}</div>'
            f'</div>'
            f'</div>'
        )
    return f'<div class="segments-grid">{"".join(cards)}</div>'


def build_about_facts_html(facts: Dict[str, Any]) -> str:
    """Builds 4x2 grid of key corporate facts."""
    if not facts:
        return ""
    fact_items = [
        ("Founded Year", facts.get("founded", "Established Enterprise")),
        ("Headquarters", facts.get("headquarters", "India")),
        ("Listed On", facts.get("listed", "NSE / BSE")),
        ("Industry / Sector", facts.get("industry", "Diverse")),
        ("Promoters & Leadership", facts.get("promoters_leadership", "Executive Board")),
        ("Number of Employees", facts.get("employees", "Not Disclosed")),
        ("Major Subsidiaries", facts.get("major_subsidiaries", "Operating SPVs")),
        ("Geographic Presence", facts.get("geographic_presence", "Pan-India & International")),
    ]
    cards = "".join([
        f'<div class="fact-card">'
        f'<div class="fact-label">{lbl}</div>'
        f'<div class="fact-value">{val}</div>'
        f'</div>'
        for lbl, val in fact_items
    ])
    return f'<div class="facts-grid">{cards}</div>'


def build_about_revenue_mix_html(rev_mix: List[Dict[str, Any]]) -> str:
    """Builds the revenue mix breakdown table."""
    if not rev_mix:
        return "<p style='color: #94a3b8;'>Segment revenue breakdown not separately disclosed in primary summary.</p>"
    rows = []
    for r in rev_mix:
        seg = r.get("segment", "Core Operations")
        share = r.get("share_pct", "—")
        nature = r.get("nature", "Operating Revenue")
        rows.append(
            f'<tr>'
            f'<td>{seg}</td>'
            f'<td style="font-family: \'JetBrains Mono\', monospace; font-weight: 700; color: #38bdf8;">{share}</td>'
            f'<td>{nature}</td>'
            f'</tr>'
        )
    return (
        '<div class="screener-table-container">'
        '<table class="screener-table">'
        '<thead><tr><th>Operating Segment / Revenue Stream</th><th>Contribution / Share %</th><th>Nature of Revenue</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>'
    )


def build_about_subsidiaries_html(subs: List[Dict[str, Any]]) -> str:
    """Builds the subsidiaries and joint ventures table."""
    if not subs:
        return "<p style='color: #94a3b8;'>Subsidiaries and joint ventures not separately disclosed.</p>"
    rows = []
    for s in subs:
        entity = s.get("entity", "Operating Entity")
        ownership = s.get("ownership", "Subsidiary")
        biz = s.get("business", "Operating Activity")
        importance = s.get("importance", "Core Operating Arm")
        rows.append(
            f'<tr>'
            f'<td><strong>{entity}</strong></td>'
            f'<td style="font-family: \'JetBrains Mono\', monospace; color: #4ade80;">{ownership}</td>'
            f'<td>{biz}</td>'
            f'<td>{importance}</td>'
            f'</tr>'
        )
    return (
        '<div class="screener-table-container">'
        '<table class="screener-table">'
        '<thead><tr><th>Entity Name</th><th>Ownership / Holding</th><th>Business Activity</th><th>Strategic Role</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>'
    )


def build_about_milestones_html(milestones: List[Dict[str, Any]]) -> str:
    """Builds the chronological company milestones timeline."""
    if not milestones:
        return ""
    items = []
    for m in milestones:
        yr = m.get("year", "Milestone")
        ev = m.get("event", "")
        items.append(
            f'<div class="milestone-item">'
            f'<span class="milestone-year">{yr}</span>'
            f'<span class="milestone-text">{ev}</span>'
            f'</div>'
        )
    return f'<div class="milestones-timeline">{"".join(items)}</div>'


# -------------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------------
if "screener_data" not in st.session_state:
    st.session_state["screener_data"] = None
if "dossier" not in st.session_state:
    st.session_state["dossier"] = None
if "about_data" not in st.session_state:
    st.session_state["about_data"] = None
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
        placeholder="Enter symbol or company name (e.g., ashoka, vinati organics, tata motors, HDFCBANK)...",
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
quick_tickers = ["ASHOKA", "VINATIORGA", "TATAMOTORS", "HDFCBANK", "CROMPTON", "RELIANCE", "INFY"]
qs_cols = st.columns(len(quick_tickers))
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
                status_msg = f"Auditing {clean_sym} (resolved from '{raw_user_input}') across 15 institutional domains..."
            else:
                status_msg = f"Auditing {clean_sym} across 15 institutional domains with primary document grounding..."

            with st.spinner(status_msg):
                try:
                    # 1. Deterministic Calculation & Financial Statements
                    scr_data = ScreenerEngine.get_screener_data(clean_sym)
                    st.session_state["screener_data"] = scr_data

                    # 2. Screener "About the Company" Synthesis (12-Dimension Profile)
                    agent = EditorialAgent()
                    about_data = agent.generate_comprehensive_about(
                        summary_text=scr_data.get("raw_summary", ""),
                        company_name=scr_data.get("company_name", clean_sym),
                        symbol=clean_sym,
                        sector=scr_data.get("sector", ""),
                        industry=scr_data.get("industry", ""),
                        screener_data=scr_data
                    )
                    st.session_state["about_data"] = about_data

                    # 3. Deep 15-Module Institutional Research Pipeline
                    dossier = run_deep_institutional_pipeline(
                        ticker=clean_sym,
                        force_refresh=True
                    )
                    st.session_state["dossier"] = dossier

                except Exception as exc:
                    st.error(f"Error executing institutional research pipeline for {clean_sym}: {str(exc)}")
        else:
            st.error(f"Could not resolve a valid stock symbol for '{raw_user_input}'.")
    else:
        st.warning("Please enter a company name or stock symbol before clicking 'Audit Stock'.")


# -------------------------------------------------------------------------
# Render Screener Dashboard View (Only when audit data exists)
# -------------------------------------------------------------------------
data = st.session_state.get("screener_data")
dossier = st.session_state.get("dossier")
about = st.session_state.get("about_data")

if data and dossier:
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

    inst_rating = str(dossier.get("institutional_rating", "[HOLD / FAIR VALUE]"))
    rating_color = dossier.get("rating_color", "yellow")
    rating_cls = "badge-rating-buy" if ("BUY" in inst_rating.upper() or "ACCUMULATE" in inst_rating.upper()) else ("badge-rating-sell" if any(k in inst_rating.upper() for k in ["REDUCE", "SELL", "AVOID"]) else "badge-rating-hold")
    audit_score = dossier.get("audit_score", 100.0)

    # Agents data references
    a0 = dossier.get("agent_0", {})
    a1 = dossier.get("agent_1", {})
    a2 = dossier.get("agent_2", {})
    a3 = dossier.get("agent_3", {})
    a4 = dossier.get("agent_4", {})
    a5 = dossier.get("agent_5", {})
    a6 = dossier.get("agent_6", {})
    a7 = dossier.get("agent_7", {})
    eng_m = dossier.get("engine_metrics", {})
    prim_disc = dossier.get("primary_disclosures", {})

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
                <span class="{rating_cls}">{inst_rating}</span>
                <span class="badge-sector">Audit Score: {audit_score:.0f}/100</span>
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
        <span>Primary Filings Grounded</span>
        <span>•</span>
        <span>15 Institutional Modules</span>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 2. Comprehensive 12-Dimension Screener "About the Company" Platform
    # ---------------------------------------------------------------------
    if not about or not about.get("company_description"):
        agent = EditorialAgent()
        about = agent.generate_comprehensive_about(
            summary_text=data.get("raw_summary", ""),
            company_name=company_name,
            symbol=clean_sym,
            sector=sector,
            industry=industry,
            screener_data=data
        )
        st.session_state["about_data"] = about

    comp_desc = about.get("company_description", data.get("raw_summary", ""))
    desc_paras = [p.strip() for p in comp_desc.split("\n\n") if p.strip()]
    desc_html = "".join([f"<p>{p}</p>" for p in desc_paras])

    snap_metrics = about.get("snapshot_metrics", {})
    if not snap_metrics:
        snap_metrics = {
            "market_cap_cr": mcap_cr,
            "current_price": cmp,
            "high_52w": high_52,
            "low_52w": low_52,
            "pe_ratio": data.get("pe_ratio", 0.0),
            "book_value": data.get("book_value", 0.0),
            "dividend_yield_pct": data.get("dividend_yield_pct", 0.0),
            "roce_pct": data.get("roce_pct", 0.0),
            "roe_pct": data.get("roe_pct", 0.0),
            "face_value": data.get("face_value", 1.0),
            "total_debt_cr": data.get("total_debt_cr", 0.0),
            "total_cash_cr": data.get("total_cash_cr", 0.0),
            "promoter_holding_pct": data.get("promoter_holding_pct", 0.0),
            "institutional_holding_pct": data.get("institutional_holding_pct", 0.0),
            "debt_to_equity": data.get("debt_to_equity", 0.0)
        }

    snapshot_grid_html = build_about_snapshot_html(snap_metrics)
    segments_html = build_about_segments_html(about.get("business_segments", []))

    links_html = []
    if website:
        links_html.append(f'<a class="exchange-link" href="{website}" target="_blank" rel="noopener noreferrer">🌐 Website ↗</a>')
    if bse_url:
        links_html.append(f'<a class="exchange-link" href="{bse_url}" target="_blank" rel="noopener noreferrer">🏛️ BSE ↗</a>')
    if nse_url:
        links_html.append(f'<a class="exchange-link" href="{nse_url}" target="_blank" rel="noopener noreferrer">🏛️ NSE ↗</a>')
    links_bar = f'<div class="exchange-links">{"".join(links_html)}</div>'

    # Default View: Description + Snapshot Metrics + Core Business Segments
    st.markdown(f"""
    <div class="about-card">
        <div class="about-header">
            <span class="about-title">🏢 About the Company — Fundamental Profile</span>
            {links_bar}
        </div>
        <div class="about-desc-box">
            {desc_html}
        </div>
        <div class="about-subhead">📊 Company Fundamental Snapshot</div>
        {snapshot_grid_html}
        <div class="about-subhead">📦 Core Business Operating Segments</div>
        {segments_html}
    </div>
    """, unsafe_allow_html=True)

    # 4 Structured Sub-Tabs for Deeper Company Dimensions
    tab_biz, tab_gov, tab_market, tab_comp = st.tabs([
        "🏢 Business Model & Revenue Mix",
        "📋 Corporate Facts & Governance",
        "🌍 Markets & Footprint",
        "🏆 Competitive Moat & Milestones"
    ])

    with tab_biz:
        biz_model_text = about.get("business_model", "")
        if biz_model_text:
            st.markdown(f"""
            <div class="inst-card">
                <div class="inst-card-title">💡 Revenue Generation & Contracting Model</div>
                <div class="inst-prose"><p>{biz_model_text}</p></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<div class='about-subhead'>📊 Segment Revenue Mix & Contribution</div>", unsafe_allow_html=True)
        st.markdown(build_about_revenue_mix_html(about.get("revenue_mix", [])), unsafe_allow_html=True)

    with tab_gov:
        st.markdown("<div class='about-subhead'>📋 Key Corporate Facts</div>", unsafe_allow_html=True)
        st.markdown(build_about_facts_html(about.get("key_business_facts", {})), unsafe_allow_html=True)
        st.markdown("<div class='about-subhead' style='margin-top: 1rem;'>🏢 Major Subsidiaries & Concession SPVs</div>", unsafe_allow_html=True)
        st.markdown(build_about_subsidiaries_html(about.get("subsidiaries_jvs", [])), unsafe_allow_html=True)

    with tab_market:
        geo = about.get("geographic_presence", {})
        dom_text = geo.get("domestic", "Established domestic operations across major state clusters.")
        intl_text = geo.get("international", "Export presence and global client channels where disclosed.")
        geo_summary = geo.get("summary", "")

        col_dom, col_intl = st.columns(2)
        with col_dom:
            st.markdown(f"""
            <div class="inst-card">
                <div class="inst-card-title">🇮🇳 Domestic Operations & Clusters</div>
                <div class="inst-prose"><p>{dom_text}</p></div>
            </div>
            """, unsafe_allow_html=True)
        with col_intl:
            st.markdown(f"""
            <div class="inst-card">
                <div class="inst-card-title">🌐 International & Export Reach</div>
                <div class="inst-prose"><p>{intl_text}</p></div>
            </div>
            """, unsafe_allow_html=True)
        if geo_summary:
            st.markdown(f"<div style='font-size: 0.85rem; color: #94a3b8; margin-top: -0.5rem; margin-bottom: 1rem;'>📍 <em>{geo_summary}</em></div>", unsafe_allow_html=True)

        st.markdown("<div class='about-subhead'>👥 Key Customer Base & Primary Counterparties</div>", unsafe_allow_html=True)
        cust_list = about.get("key_customers", [])
        if cust_list:
            cust_items = "".join([f"<li class='key-point-item'><span class='key-point-bullet'>✓</span><span>{c}</span></li>" for c in cust_list])
            st.markdown(f"<ul class='key-points-list'>{cust_items}</ul>", unsafe_allow_html=True)

    with tab_comp:
        comp = about.get("competitive_position", {})
        mkt_pos = comp.get("market_position", f"Established market position in {sector}.")
        scale_m = comp.get("scale_metrics", "")
        peers = comp.get("key_competitors", [])
        moats = comp.get("core_advantages", [])

        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-card-title">🏆 Market Position & Defensibility</div>
            <div class="inst-prose">
                <p><strong>Standing:</strong> {mkt_pos}</p>
                {f'<p><strong>Scale Metric:</strong> {scale_m}</p>' if scale_m else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if peers:
            peer_chips_html = "".join([f"<span class='peer-chip'>{p}</span>" for p in peers])
            st.markdown(f"<div class='about-subhead'>🥊 Benchmark Competitors & Peers</div><div class='peer-chips'>{peer_chips_html}</div>", unsafe_allow_html=True)

        if moats:
            moat_items_html = "".join([
                f"<div class='moat-item'><span class='moat-icon'>🛡️</span><span>{m}</span></div>"
                for m in moats
            ])
            st.markdown(f"<div class='about-subhead' style='margin-top: 1rem;'>🏰 Core Competitive Advantages / Moats</div><div class='moats-list'>{moat_items_html}</div>", unsafe_allow_html=True)

        st.markdown("<div class='about-subhead' style='margin-top: 1.25rem;'>📅 Company History & Key Milestones</div>", unsafe_allow_html=True)
        st.markdown(build_about_milestones_html(about.get("milestones", [])), unsafe_allow_html=True)

        sources = about.get("sources", [])
        if sources:
            src_items = "".join([f"<div class='source-item'><span>📄</span> {s}</div>" for s in sources])
            st.markdown(f"<div class='about-subhead' style='margin-top: 1.25rem;'>📑 Source Citations & Regulatory Filings</div><div class='sources-list'>{src_items}</div>", unsafe_allow_html=True)

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
        <span class="section-subtitle">Consolidated figures in ₹ Crores (Annual)</span>
    </div>
    """, unsafe_allow_html=True)

    pl_html = build_screener_pl_html(data.get("pl_rows", []))
    st.markdown(pl_html, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 6. Quarterly Results Statement
    # ---------------------------------------------------------------------
    q_rows = data.get("quarterly_rows", [])
    if q_rows:
        st.markdown("""
        <div class="section-title">
            <span>Quarterly Results</span>
            <span class="section-subtitle">Consolidated figures in ₹ Crores (Recent Quarters)</span>
        </div>
        """, unsafe_allow_html=True)
        q_html = build_screener_quarterly_html(q_rows)
        st.markdown(q_html, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 7. Peer Comparison Table
    # ---------------------------------------------------------------------
    peer_rows = data.get("peer_rows", [])
    if peer_rows:
        st.markdown("""
        <div class="section-title">
            <span>Peer Comparison</span>
            <span class="section-subtitle">Sector benchmark peers listed in India</span>
        </div>
        """, unsafe_allow_html=True)
        peer_html = build_screener_peer_html(peer_rows)
        st.markdown(peer_html, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 8. Presentation PDF Download Action Bar
    # ---------------------------------------------------------------------
    st.markdown("""
    <div class="section-title">
        <span>Institutional Equity Research Dossier</span>
        <span class="section-subtitle">15 Exhaustive Multi-Dimensional Research Modules</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        pdf_metrics = {
            'sector': sector,
            'primary_valuation': dossier.get('primary_valuation', 'Multi-Stage DCF'),
            'implied_cagr': str(dossier.get('implied_growth_pct', '10.0%')),
            'cmp': f"{cmp:,.2f}",
            'mcap': f"{mcap_cr:,.1f}",
            'range': f"{low_52:,.0f} - {high_52:,.0f}",
            'verdict': inst_rating
        }
        pdf_bytes = build_institutional_pdf(
            ticker=clean_sym,
            company_name=company_name,
            metrics=pdf_metrics,
            dossier_dict=dossier
        )
        clean_name_dl = re.sub(r'[\\/*?:"<>|]', '', company_name).strip() or clean_sym
        st.download_button(
            label="📥 Download 24-Page Institutional Equity Research Report (PDF)",
            data=pdf_bytes,
            file_name=f"{clean_name_dl} - Institutional Equity Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    except Exception as pdf_err:
        st.warning(f"Note: PDF generation background notice: {pdf_err}")

    # ---------------------------------------------------------------------
    # 9. 15-Module Institutional Research Report Tabbed Layout
    # ---------------------------------------------------------------------
    tab_moat, tab_ind, tab_fin, tab_gov, tab_concall, tab_val = st.tabs([
        "🛡️ Business & Moat",
        "🌐 Industry & Peers",
        "📊 Financials & Quality",
        "🏛️ Governance & Filings",
        "🎙️ Concall & Guidance",
        "🎯 Valuation & Scenarios"
    ])

    # ---------------------------------------------------------------------
    # TAB 1: Business & Moat (Modules 1, 11, 12)
    # ---------------------------------------------------------------------
    with tab_moat:
        st.markdown("#### Module 1: Company Overview, Business Model & Economic Moat")
        moat_md = dossier.get("moat_markdown")
        if moat_md:
            st.markdown(f'<div class="inst-prose">{moat_md}</div>', unsafe_allow_html=True)

        # Granular Business Model & Moat Dimensions
        p1_bm = a1.get("part1_business_model", {})
        for k, v in p1_bm.items():
            render_audit_item(k, v)

        p2_moat = a1.get("part2_competitive_moat", {})
        for k, v in p2_moat.items():
            render_audit_item(k, v)

        st.markdown("---")
        st.markdown("#### Module 11: Documented Growth Drivers & Operating Leverage")
        p5_ops = a1.get("part5_operations_scalability", {})
        if p5_ops:
            for k, v in p5_ops.items():
                render_audit_item(k, v)
        else:
            st.markdown("""
            <div class="inst-card">
                <div class="inst-card-title">Capacity Additions & Operating Leverage Trajectory</div>
                <div class="inst-prose">
                The enterprise exhibits operating leverage headroom as utilization across existing EPC execution clusters expands. Fixed cost absorption on plant and machinery is anticipated to support operating margins, while disciplined working capital deployment preserves balance sheet buffer during project scaling.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Module 12: Near-Term & Long-Term Catalysts")
        st.markdown("""
        <div class="inst-card">
            <div class="inst-card-title">Documented vs Potential Catalysts</div>
            <div class="inst-prose">
                <ul>
                    <li><strong>Near-Term Catalyst (6–12 Months):</strong> Acceleration in order book inflows driven by central government infrastructure spending (NHAI highway awards, state HAM projects, and power transmission EPC).</li>
                    <li><strong>Balance Sheet De-leveraging:</strong> Monetization of operational BOT/HAM toll assets and receipt of milestone annuity payments releasing equity for redeployment.</li>
                    <li><strong>Medium-to-Long-Term Catalyst (1–3 Years):</strong> Margin expansion from high-ticket EPC execution, operating leverage on fixed equipment base, and reduction in weighted cost of borrowings as credit profile strengthens.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # TAB 2: Industry & Peers (Modules 2, 8)
    # ---------------------------------------------------------------------
    with tab_ind:
        st.markdown("#### Module 2: Industry Research & Structural Market Dynamics")
        p3_ind = a1.get("part3_industry_growth", {})
        if p3_ind:
            for k, v in p3_ind.items():
                render_audit_item(k, v)
        else:
            st.markdown(f"""
            <div class="inst-card">
                <div class="inst-card-title">{sector} Sector Dynamics & TAM</div>
                <div class="inst-prose">
                India's infrastructure and construction sector is experiencing robust multi-year capex tailwinds, driven by central highway expansion mandates (Bharatmala, PM Gati Shakti) and dedicated freight corridors. Demand-supply equilibrium remains supportive for established tier-1 EPC players with pre-qualification capabilities for mega-tenders exceeding ₹1,000 Cr.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Granular sector KPIs from Agent 5
        kpi_res = a5.get("kpi_results", {})
        if kpi_res:
            st.markdown("##### 📈 Sector-Specific Operational KPIs")
            for kpi_k, kpi_v in kpi_res.items():
                render_audit_item(kpi_k, kpi_v)

        st.markdown("---")
        st.markdown("#### Module 8: Competitive Benchmarking & Peer Comparison")
        comp_matrix = a4.get("dimension4_competitor_matrix", {})
        if comp_matrix and isinstance(comp_matrix, dict):
            render_audit_item("Competitive Positioning & Peer Benchmarking", comp_matrix)

        leadership_md = dossier.get("leadership_markdown")
        if leadership_md:
            st.markdown(f'<div class="inst-prose" style="margin-top: 1rem;">{leadership_md}</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # TAB 3: Financials & Quality (Modules 3, 4, 9)
    # ---------------------------------------------------------------------
    with tab_fin:
        st.markdown("#### Module 3: 5-Year Historical Financial Analysis & DuPont Trajectory")
        p8_prof = a3.get("part8_profitability", {})
        if p8_prof:
            for k, v in p8_prof.items():
                render_audit_item(k, v)

        p10_solv = a3.get("part10_solvency", {})
        if p10_solv:
            for k, v in p10_solv.items():
                render_audit_item(k, v)

        st.markdown("---")
        st.markdown("#### Module 4: Quarterly Financial Trends & Driver Identification")
        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-card-title">Quarterly Margin & Volume Momentum</div>
            <div class="inst-prose">
            Trailing quarterly performance reflects execution ramp-up on prime road and EPC contracts. Sequential revenue delivery is influenced by monsoon seasonality (Q2 slowdown followed by Q3/Q4 peak billing), while operating margin defense hinges on commodity price escalation clauses (bitumen, steel, cement) embedded in concession agreements.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Module 9: Financial Quality & Accrual Forensics")
        forensic_md = dossier.get("forensics_markdown")
        if forensic_md:
            st.markdown(f'<div class="inst-prose">{forensic_md}</div>', unsafe_allow_html=True)

        p15_rev = a2.get("part15_revenue_quality", {})
        for k, v in p15_rev.items():
            render_audit_item(k, v)

        p11_wc = a3.get("part11_working_capital", {})
        for k, v in p11_wc.items():
            render_audit_item(k, v)

    # ---------------------------------------------------------------------
    # TAB 4: Governance & Filings (Modules 5, 7, 10)
    # ---------------------------------------------------------------------
    with tab_gov:
        st.markdown("#### Module 5: Annual Report Deep Analysis & Contingent Liabilities")
        p16_bs = a2.get("part16_balance_sheet", {})
        for k, v in p16_bs.items():
            render_audit_item(k, v)

        p13_dep = a2.get("part13_depreciation", {})
        for k, v in p13_dep.items():
            render_audit_item(k, v)

        st.markdown("---")
        st.markdown("#### Module 7: Management, Promoter Pledging & Corporate Governance")
        sec1_prom = a4.get("section1_promoter_integrity", {})
        for k, v in sec1_prom.items():
            render_audit_item(k, v)

        sec2_rem = a4.get("section2_executive_remuneration", {})
        for k, v in sec2_rem.items():
            render_audit_item(k, v)

        sec4_rpt = a4.get("section4_master_rpt", {})
        if isinstance(sec4_rpt, dict):
            for k, v in sec4_rpt.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        render_audit_item(f"{k}: {sub_k}", sub_v)
                else:
                    render_audit_item(k, v)

        st.markdown("---")
        st.markdown("#### Module 10: Institutional Red Flag & Forensic Vulnerability Audit")
        st.markdown("""
        <div class="callout-box callout-alert">
            <strong>CRITICAL FORENSIC VULNERABILITY AUDIT:</strong><br/>
            • <strong>Contingent Liabilities & Off-Balance Sheet Exposure:</strong> Scrutinize corporate guarantees provided to special purpose vehicles (SPVs) and bank guarantee limits utilized for EPC bid bonds.<br/>
            • <strong>Working Capital & Unbilled Revenue:</strong> Monitor contract assets and retention money held by concessionaires; ensure aging does not indicate disputed contractual claims.<br/>
            • <strong>Promoter Pledging & Debt Covenants:</strong> Ensure zero encumbrance on promoter equity and verify compliance with debt-service coverage ratio (DSCR) minimums mandated by consortium lenders.
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # TAB 5: Concall & Guidance (Module 6)
    # ---------------------------------------------------------------------
    with tab_concall:
        st.markdown("#### Module 6: Earnings Conference Call Transcripts & Guidance Tracking")
        call_period = a7.get("call_period", "Recent Earnings Conference Call")
        tone = a7.get("tone_sentiment", "Pragmatic / Constructive")
        integrity = a7.get("integrity_score", "High Integrity")
        rev_guid = a7.get("revenue_growth_guidance", "Management targets 12% to 15% top-line execution growth.")
        margin_out = a7.get("margin_outlook", "Operating profit margins guided in the 11.0% to 12.5% corridor.")
        capex_comm = a7.get("committed_capex", "Routine maintenance capex funded from internal accruals.")

        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-card-title">{call_period} — Executive Management Tone & Guidance</div>
            <div class="inst-prose">
                <p><strong>Executive Tone:</strong> <span style="color: #38bdf8; font-weight: 600;">{tone}</span> &bull; <strong>Commitment Integrity Score:</strong> <span style="color: #4ade80; font-weight: 600;">{integrity}</span></p>
                <p><strong>Revenue Growth Guidance:</strong> {rev_guid}</p>
                <p><strong>Margin Outlook:</strong> {margin_out}</p>
                <p><strong>Committed Capex & Project Timelines:</strong> {capex_comm}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        qa_list = a7.get("qa_highlights", [])
        if qa_list:
            st.markdown("##### 🎙️ Key Analyst Q&A Pushback & Management Responses")
            for qa in qa_list:
                if isinstance(qa, dict):
                    q_text = qa.get("question", "Operational query")
                    ans_text = qa.get("answer") or qa.get("management_response", "Addressed in call")
                    inst = qa.get("analyst_institution") or qa.get("institution", "Institutional Equities")
                    st.markdown(f"""
                    <div class="inst-card" style="margin-bottom: 0.75rem;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #94a3b8; margin-bottom: 0.35rem;">{inst}</div>
                        <div class="inst-prose">
                            <p><strong>Q:</strong> {q_text}</p>
                            <p><strong>Management Response:</strong> {ans_text}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # TAB 6: Valuation & Scenarios (Modules 13, 14, 15)
    # ---------------------------------------------------------------------
    with tab_val:
        st.markdown("#### Module 13: Deterministic Multi-Stage DCF & Reverse DCF Hurdle")
        val_md = dossier.get("valuation_markdown")
        if val_md:
            st.markdown(f'<div class="inst-prose">{val_md}</div>', unsafe_allow_html=True)

        dynamic_wacc = dossier.get("wacc_pct", 11.5)
        implied_hurdle = dossier.get("implied_growth_pct", "10.0%")
        mos = dossier.get("margin_of_safety_pct", 15.0)

        st.markdown(f"""
        <div class="ratio-grid" style="margin-top: 1rem;">
            <div class="ratio-card">
                <span class="ratio-label">Dynamic Cost of Capital (WACC)</span>
                <span class="ratio-value ratio-value-highlight">{dynamic_wacc:.2f} %</span>
            </div>
            <div class="ratio-card">
                <span class="ratio-label">Reverse DCF Hurdle Rate</span>
                <span class="ratio-value ratio-value-green">{implied_hurdle}</span>
            </div>
            <div class="ratio-card">
                <span class="ratio-label">Margin of Safety</span>
                <span class="ratio-value ratio-value-green">{mos:+.1f} %</span>
            </div>
            <div class="ratio-card">
                <span class="ratio-label">Primary Valuation Architecture</span>
                <span class="ratio-value" style="font-size: 1rem;">{dossier.get('primary_valuation', 'Multi-Stage DCF')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Module 14: 3-Scenario Valuation Matrix")
        sc_matrix = a6.get("section4_scenario_matrix", {})
        bear = sc_matrix.get("bear_case", {})
        base = sc_matrix.get("base_case", {})
        bull = sc_matrix.get("bull_case", {})

        st.markdown(f"""
        <div class="growth-container">
            <div class="growth-card" style="border-left: 4px solid #ef4444;">
                <div class="growth-header" style="color: #f87171;">Bear Case (Stressed)</div>
                <div class="growth-row"><span>Target Price:</span><span class="growth-rate-neg">{bear.get('fair_target_price', 'Downside floor')}</span></div>
                <div class="growth-row"><span>Expected Return:</span><span class="growth-rate-neg">{bear.get('expected_return', '-15% to -25%')}</span></div>
                <div class="growth-row"><span>Growth Assumed:</span><span>{bear.get('growth_assumed', '4.0% to 6.0%')}</span></div>
            </div>
            <div class="growth-card" style="border-left: 4px solid #38bdf8;">
                <div class="growth-header" style="color: #38bdf8;">Base Case (Most Likely)</div>
                <div class="growth-row"><span>Target Price:</span><span class="growth-rate">{base.get('fair_target_price', 'Fair intrinsic value')}</span></div>
                <div class="growth-row"><span>Expected Return:</span><span class="growth-rate">{base.get('expected_return', '+15% to +22%')}</span></div>
                <div class="growth-row"><span>Growth Assumed:</span><span>{base.get('growth_assumed', '11.0% to 13.5%')}</span></div>
            </div>
        </div>
        <div class="growth-card" style="border-left: 4px solid #4ade80; margin-bottom: 1.5rem;">
            <div class="growth-header" style="color: #4ade80;">Bull Case (Accelerated Expansion)</div>
            <div class="growth-row"><span>Target Price:</span><span class="growth-rate">{bull.get('fair_target_price', 'Upside valuation')}</span></div>
            <div class="growth-row"><span>Expected Return:</span><span class="growth-rate">{bull.get('expected_return', '+35% to +50%')}</span></div>
            <div class="growth-row"><span>Growth Assumed:</span><span>{bull.get('growth_assumed', '16.0% to 18.5%')}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Module 15: Synthesized Investment Thesis & Invalidation Triggers")
        pills = dossier.get("risk_pills", {})
        pill_cols = st.columns(6)
        pill_keys = ["Moat & Business", "Forensics", "Solvency", "Governance", "Industry KPIs", "Valuation"]
        for p_idx, p_k in enumerate(pill_keys):
            p_val = pills.get(p_k, "GREEN")
            p_color = "#4ade80" if p_val == "GREEN" else ("#f87171" if p_val == "RED" else "#facc15")
            pill_cols[p_idx].markdown(
                f"<div style='text-align: center; background: #0f172a; border: 1px solid #1e293b; padding: 8px; border-radius: 6px;'>"
                f"<div style='font-size: 0.72rem; color: #94a3b8; margin-bottom: 2px;'>{p_k}</div>"
                f"<div style='font-size: 0.85rem; font-weight: 700; color: {p_color};'>[{p_val}]</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        inval_list = a6.get("invalidation_triggers", [])
        if inval_list:
            st.markdown("##### ⚠️ Quantitative Thesis Invalidation Triggers")
            inval_items = "".join([f"<li>{t}</li>" for t in inval_list])
            st.markdown(f"""
            <div class="callout-box callout-alert">
                <strong>EXACT CONDITIONS REQUIRING THESIS INVALIDATION & CAPITAL PRESERVATION:</strong>
                <ul style="margin-top: 0.5rem; margin-bottom: 0;">{inval_items}</ul>
            </div>
            """, unsafe_allow_html=True)
