"""
Research Beast — Fundamental Investment Intelligence & Equity Workstation
100% deterministic mathematical calculations, multi-year financial statement modeling,
and an exhaustive 15-module institutional equity research audit engine.
Separates deterministic quantitative figures from context-locked editorial analysis.
"""

import os
import io
import re
import json
import logging
import textwrap
from typing import Optional, Dict, Any, List, Tuple
import streamlit as st
import pandas as pd
import numpy as np

from services.financial_data import extract_pure_symbol
from services.screener_engine import ScreenerEngine
from agents.editorial_agent import EditorialAgent
from utils.symbol_resolver import resolve_ticker, resolve_ticker_info
from agents.pipeline import run_deep_institutional_pipeline, parse_dimension_data
from core.company_identity import resolve_canonical_identity
from core.research_context import (
    create_research_context,
    ResearchRunContext,
    assert_company_boundary,
    DataContaminationError,
    EntityRole
)
from services.decision_engine.coordinator import DecisionEngineCoordinator
from services.decision_engine.terminal_renderer import (
    build_decision_pillars_html,
    build_what_changed_html,
    build_why_it_changed_html,
    build_signals_dashboard_html,
    build_financial_quality_html,
    build_forensic_audit_html,
    build_industry_intelligence_html,
    build_opportunities_and_risks_html,
    build_valuation_expectations_html,
    build_event_timeline_html,
    build_investor_questions_html,
    build_jev_verification_gate_html,
)

# UI Modular Architecture
from ui.theme import apply_theme
from ui.layout import render_workstation_top_bar, render_command_bar
from ui.components.company_header import render_company_header
from ui.components.research_status import render_research_status_bar
from ui.components.metric_grid import render_key_investment_signals, render_compounded_growth_cards
from ui.components.decision_matrix import render_decision_pillars
from ui.components.what_changed import render_what_changed
from ui.components.forensic_signal import render_forensic_audit
from ui.components.financial_table import (
    render_pl_table,
    render_quarterly_table,
    render_peer_table,
    render_cash_flow_waterfall,
)
from ui.components.evidence_card import (
    render_evidence_drawer,
    render_investor_questions,
    render_event_timeline,
    render_jev_audit_log,
)
from ui.components.section_header import render_section_header
from ui.components.empty_state import render_workstation_home
from ui.components.error_state import render_error_state
from ui.components.simple_investor_deck import render_simple_investor_overview

# Direct Screener Extractor, Thesis Agent & Clean Screener View
from services.screener_fetcher import (
    fetch_screener_data,
    clean_user_input,
    fetch_stock_chart_data,
    fetch_day_change,
)
from agents.thesis_agent import ThesisAgent
from ui.components.screener_view import (
    render_screener_top_header,
    render_screener_about_box,
    render_screener_ratios_3x3,
    render_screener_financial_table,
    render_screener_editorial_memo,
)
from ui.components.simple_company_view import (
    render_section_1_header_and_chart,
    render_section_2_key_financials,
    render_section_3_business_snapshot,
    render_section_4_whats_changing,
    render_section_5_why_is_it_happening,
    render_section_6_financial_trends,
    render_section_7_risk_check,
    render_section_8_and_9_opps_and_risks,
    render_section_10_ask_company_qa,
    render_section_11_deep_dive,
)
from ui.components.screener_tables import (
    render_layer1_header,
    render_horizontal_nav,
    render_overview_row,
    render_stock_chart,
    render_compact_key_financials,
    render_peers_table,
    render_quarterly_section,
    render_annual_section,
    render_cash_flow_section,
    render_balance_sheet_section,
    render_ratios_section,
    render_shareholding_section,
    render_news_section,
)
from ui.components.qa_intelligence import render_qa_intelligence_section

logger = logging.getLogger("ResearchBeast.App")

# -------------------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Research Beast — Fundamental Investment Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject central design tokens and global workstation theme
apply_theme()


# -------------------------------------------------------------------------
# Helper Functions: Formatters
# -------------------------------------------------------------------------
def fmt_cr(val: float) -> str:
    """Formats values in ₹ Crores with comma separators."""
    if val is None or val == 0.0:
        return "₹ 0"
    return f"₹ {val:,.2f} Cr"


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


def render_audit_item(title: str, item: Any):
    """Renders a single structured audit node with Level A-D depth."""
    if isinstance(item, dict):
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
            prose = f"<strong>Objective:</strong> {target}<br/><strong>Delivered Outcome:</strong> {actual} <span style='color: #34d399; font-weight: 600;'>[{verdict}]</span>"

        if prose:
            html = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.85rem;">
<div style="font-size: 0.92rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">{display_title}</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">{prose}</div>
</div>"""
            st.html(html)
    elif isinstance(item, str) and len(item.strip()) > 10:
        html = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.85rem;">
<div style="font-size: 0.92rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">{title.replace('_', ' ').title()}</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">{item}</div>
</div>"""
        st.html(html)


def build_about_snapshot_html(metrics: Dict[str, Any]) -> str:
    """Builds the 14-metric fundamental snapshot grid HTML without indentation traps."""
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
        ("Market Cap", f"₹{mcap:,.1f} Cr", "#38bdf8"),
        ("Current Price", f"₹{cmp:,.2f}", "#34d399"),
        ("52W High / Low", f"₹{h52:,.0f} / {l52:,.0f}", "#f8fafc"),
        ("Stock P/E", f"{pe:.1f}x" if pe > 0 else "—", "#f8fafc"),
        ("Book Value", f"₹{bv:,.1f}", "#f8fafc"),
        ("Div Yield", f"{div:.2f}%", "#f8fafc"),
        ("ROCE", f"{roce:.1f}%", "#34d399" if roce > 15 else "#f8fafc"),
        ("ROE", f"{roe:.1f}%", "#34d399" if roe > 15 else "#f8fafc"),
        ("Face Value", f"₹{fv:.1f}", "#f8fafc"),
        ("Total Debt", f"₹{debt:,.1f} Cr", "#f8fafc"),
        ("Cash & Equiv", f"₹{cash:,.1f} Cr", "#34d399" if cash > debt else "#f8fafc"),
        ("Promoter Hold", f"{prom:.1f}%", "#f8fafc"),
        ("Inst. Holding", f"{inst:.1f}%", "#f8fafc"),
        ("Debt to Equity", f"{de:.2f}x", "#34d399" if de < 0.5 else "#f8fafc"),
    ]

    boxes = "".join([
        f'<div style="background: #141f36; padding: 0.55rem 0.75rem; border-radius: 5px; border: 1px solid #1e293b;">'
        f'<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px;">{lbl}</div>'
        f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.95rem; font-weight: 700; color: {col};">{val}</div>'
        f'</div>'
        for lbl, val, col in items
    ])

    return f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.55rem; margin-bottom: 1.25rem;">{boxes}</div>'


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
            f'<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem; margin-bottom: 0.65rem;">'
            f'<div style="font-weight: 600; font-size: 0.92rem; color: #38bdf8; margin-bottom: 4px;">🔷 {name}</div>'
            f'<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 8px;">{desc}</div>'
            f'<div style="display: flex; gap: 12px; font-size: 0.76rem; color: #94a3b8; flex-wrap: wrap;">'
            f'<span>🎯 <strong>Driver:</strong> {driver}</span>'
            f'<span>📦 <strong>Scope:</strong> {scope}</span>'
            f'</div>'
            f'</div>'
        )
    return f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 0.75rem;">{"".join(cards)}</div>'


def build_about_facts_html(facts: Dict[str, Any]) -> str:
    """Builds grid of key corporate facts."""
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
        f'<div style="background: #141f36; padding: 0.65rem 0.85rem; border-radius: 5px; border: 1px solid #1e293b;">'
        f'<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px;">{lbl}</div>'
        f'<div style="font-size: 0.85rem; font-weight: 600; color: #f8fafc;">{val}</div>'
        f'</div>'
        for lbl, val in fact_items
    ])
    return f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.55rem; margin-bottom: 1rem;">{cards}</div>'


def build_about_revenue_mix_html(rev_mix: List[Dict[str, Any]]) -> str:
    """Builds the revenue mix breakdown table."""
    if not rev_mix:
        return "<p style='color: #94a3b8; font-size: 0.84rem;'>Segment revenue breakdown not separately disclosed in primary summary.</p>"
    rows = []
    for r in rev_mix:
        seg = r.get("segment", "Core Operations")
        share = r.get("share_pct", "—")
        nature = r.get("nature", "Operating Revenue")
        rows.append(
            f'<tr>'
            f'<td>{seg}</td>'
            f'<td style="color: #38bdf8; font-weight: 700;">{share}</td>'
            f'<td>{nature}</td>'
            f'</tr>'
        )
    return (
        '<div class="rb-table-wrap">'
        '<table class="rb-table">'
        '<thead><tr><th>Operating Segment / Revenue Stream</th><th>Contribution / Share %</th><th>Nature of Revenue</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>'
    )


def build_about_subsidiaries_html(subs: List[Dict[str, Any]]) -> str:
    """Builds the subsidiaries and joint ventures table."""
    if not subs:
        return "<p style='color: #94a3b8; font-size: 0.84rem;'>Subsidiaries and joint ventures not separately disclosed.</p>"
    rows = []
    for s in subs:
        entity = s.get("entity", "Operating Entity")
        ownership = s.get("ownership", "Subsidiary")
        biz = s.get("business", "Operating Activity")
        importance = s.get("importance", "Core Operating Arm")
        rows.append(
            f'<tr>'
            f'<td><strong>{entity}</strong></td>'
            f'<td style="color: #34d399; font-weight: 600;">{ownership}</td>'
            f'<td>{biz}</td>'
            f'<td>{importance}</td>'
            f'</tr>'
        )
    return (
        '<div class="rb-table-wrap">'
        '<table class="rb-table">'
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
            f'<div style="display: flex; gap: 12px; margin-bottom: 0.5rem; font-size: 0.84rem;">'
            f'<span style="font-family: \'JetBrains Mono\', monospace; font-weight: 700; color: #38bdf8; min-width: 55px;">{yr}</span>'
            f'<span style="color: #cbd5e1;">{ev}</span>'
            f'</div>'
        )
    return f'<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.85rem 1rem;">{"".join(items)}</div>'


# -------------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------------
if "screener_direct" not in st.session_state:
    st.session_state["screener_direct"] = None
if "editorial_memo" not in st.session_state:
    st.session_state["editorial_memo"] = None
if "screener_data" not in st.session_state:
    st.session_state["screener_data"] = None
if "dossier" not in st.session_state:
    st.session_state["dossier"] = None
if "about_data" not in st.session_state:
    st.session_state["about_data"] = None
if "intel_dossier" not in st.session_state:
    st.session_state["intel_dossier"] = None
if "active_symbol" not in st.session_state:
    st.session_state["active_symbol"] = ""
if "resolved_from" not in st.session_state:
    st.session_state["resolved_from"] = ""
if "active_company_id" not in st.session_state:
    st.session_state["active_company_id"] = ""


# -------------------------------------------------------------------------
# Workstation Top Bar & Command Search Interface
# -------------------------------------------------------------------------
render_workstation_top_bar()
query_to_audit = render_command_bar(active_symbol=st.session_state.get("active_symbol", ""))


# -------------------------------------------------------------------------
# Trigger Pipeline Analysis with Auto-Symbol Resolution
# -------------------------------------------------------------------------
if query_to_audit:
    raw_user_input = query_to_audit.strip()
    if raw_user_input:
        clean_input = clean_user_input(raw_user_input)
        resolved_sym, matched_name = resolve_ticker_info(clean_input or raw_user_input)
        clean_sym = extract_pure_symbol(resolved_sym) or resolved_sym
        if clean_user_input(clean_sym):
            clean_sym = clean_user_input(clean_sym)

        if clean_sym:
            # Canonical Identity Resolution
            try:
                canonical_id = resolve_canonical_identity(clean_sym)
                run_context = create_research_context(canonical_id)
            except Exception:
                run_context = create_research_context(clean_sym)

            target_cid = run_context.company_id

            # Strict Session State Isolation: purge old company data on company switch
            prev_cid = st.session_state.get("active_company_id")
            if prev_cid != target_cid:
                st.session_state["screener_direct"] = None
                st.session_state["editorial_memo"] = None
                st.session_state["screener_data"] = None
                st.session_state["about_data"] = None
                st.session_state["dossier"] = None
                st.session_state["intel_dossier"] = None
                st.session_state["active_company_id"] = target_cid

            st.session_state["active_symbol"] = clean_sym
            st.session_state["active_context"] = run_context
            is_resolved = clean_sym.upper() != raw_user_input.upper()
            st.session_state["resolved_from"] = raw_user_input if is_resolved else ""

            status_msg = f"Auditing {run_context.company_name} ({clean_sym}, {target_cid}) across 15 institutional domains..."

            with st.spinner(status_msg):
                # 0. Direct Financial Extractor (Primary Regulatory Ground Truth from Screener.in)
                direct_scr = None
                try:
                    direct_scr = fetch_screener_data(clean_sym)
                    st.session_state[f"screener_direct:{target_cid}"] = direct_scr
                    st.session_state["screener_direct"] = direct_scr
                except Exception as exc:
                    logger.warning(f"Direct screener extractor fallback for {clean_sym}: {exc}")
                    direct_scr = None

                # Editorial Research Memo (Qualitative Thesis Synthesis locked to verified figures)
                if direct_scr:
                    try:
                        thesis_agent = ThesisAgent()
                        memo = thesis_agent.generate_editorial_memo(direct_scr)
                        st.session_state[f"editorial_memo:{target_cid}"] = memo
                        st.session_state["editorial_memo"] = memo
                    except Exception as exc:
                        logger.warning(f"Thesis agent synthesis failed for {clean_sym}: {exc}")
                        st.session_state[f"editorial_memo:{target_cid}"] = None
                        st.session_state["editorial_memo"] = None

                scr_data = None
                try:
                    # 1. Deterministic Calculation & Financial Statements
                    scr_data = ScreenerEngine.get_screener_data(clean_sym, run_context=run_context)
                    assert_company_boundary(scr_data, target_cid, caller_module="App.ScreenerEngine")
                    st.session_state[f"screener_data:{target_cid}"] = scr_data
                    st.session_state["screener_data"] = scr_data
                except Exception as exc:
                    logger.error(f"Screener engine failed for {clean_sym}: {exc}", exc_info=True)
                    st.error(f"Could not retrieve fundamental financial data for '{clean_sym}': {str(exc)}")

                if scr_data:
                    # 2. Deep 15-Module Institutional Research Pipeline
                    dossier = None
                    try:
                        dossier = run_deep_institutional_pipeline(
                            ticker=clean_sym,
                            force_refresh=True,
                            run_context=run_context
                        )
                        assert_company_boundary(dossier, target_cid, caller_module="App.Pipeline")
                        st.session_state[f"dossier:{target_cid}"] = dossier
                        st.session_state["dossier"] = dossier
                    except Exception as exc:
                        logger.error(f"Institutional research pipeline failed for {clean_sym}: {exc}", exc_info=True)
                        st.error(f"Error executing institutional research pipeline for {clean_sym}: {str(exc)}")

                    # 3. Screener "About the Company" Synthesis
                    try:
                        agent = EditorialAgent()
                        prim_disc = (dossier or {}).get("primary_disclosures")
                        about_data = agent.generate_comprehensive_about(
                            summary_text=scr_data.get("raw_summary", ""),
                            company_name=scr_data.get("company_name", run_context.company_name),
                            symbol=clean_sym,
                            sector=scr_data.get("sector", ""),
                            industry=scr_data.get("industry", ""),
                            screener_data=scr_data,
                            primary_disclosures=prim_disc
                        )
                        st.session_state[f"about_data:{target_cid}"] = about_data
                        st.session_state["about_data"] = about_data
                    except Exception as exc:
                        logger.error(f"About company synthesis failed for {clean_sym}: {exc}", exc_info=True)
                        st.session_state["about_data"] = None

                    # 4. Fundamental Investment Decision-Support Engine & JEV Verification Gate
                    try:
                        coordinator = DecisionEngineCoordinator()
                        intel_dossier = coordinator.run_investment_intelligence_audit(
                            company_data=scr_data,
                            screener_data=scr_data,
                            dossier=dossier or {},
                            run_context=run_context
                        )
                        assert_company_boundary(intel_dossier, target_cid, caller_module="App.DecisionEngine")
                        st.session_state[f"intel_dossier:{target_cid}"] = intel_dossier
                        st.session_state["intel_dossier"] = intel_dossier
                    except Exception as exc:
                        logger.error(f"Investment intelligence audit failed for {clean_sym}: {exc}", exc_info=True)
                        st.session_state["intel_dossier"] = None
        else:
            st.error(f"Could not resolve a valid stock symbol for '{raw_user_input}'.")


# -------------------------------------------------------------------------
# Render Workstation View
# -------------------------------------------------------------------------
active_cid = st.session_state.get("active_company_id", "")
direct_scr = st.session_state.get(f"screener_direct:{active_cid}") or st.session_state.get("screener_direct")
editorial_memo = st.session_state.get(f"editorial_memo:{active_cid}") or st.session_state.get("editorial_memo")
data = st.session_state.get(f"screener_data:{active_cid}") or st.session_state.get("screener_data")
dossier = st.session_state.get(f"dossier:{active_cid}") or st.session_state.get("dossier")
about = st.session_state.get(f"about_data:{active_cid}") or st.session_state.get("about_data")
intel = st.session_state.get(f"intel_dossier:{active_cid}") or st.session_state.get("intel_dossier")

if not data and not direct_scr:
    # Render Workstation Home Landing View when no company is searched
    render_workstation_home()
else:
    # HARD FAILURE ZERO-CONTAMINATION RENDER GATE
    try:
        if active_cid and data and dossier:
            assert_company_boundary(data, active_cid, caller_module="App.Render.ScreenerData")
            assert_company_boundary(dossier, active_cid, caller_module="App.Render.Dossier")
            if intel:
                assert_company_boundary(intel, active_cid, caller_module="App.Render.IntelDossier")
    except DataContaminationError as boundary_err:
        render_error_state(
            title="CRITICAL DATA INTEGRITY VIOLATION DETECTED",
            message=f"Cross-company boundary breach for active company '{active_cid}': {str(boundary_err)}",
            is_critical=True
        )
        st.stop()

    company_name = (direct_scr or {}).get("company_name") or (data or {}).get("company_name", "Corporate Enterprise")
    clean_sym = (direct_scr or {}).get("symbol") or (data or {}).get("clean_symbol", "")
    sector = (data or {}).get("sector", "")
    industry = (data or {}).get("industry", "")
    website = (data or {}).get("website", "")
    bse_url = (data or {}).get("bse_url", "")
    nse_url = (data or {}).get("nse_url", "")

    cmp = (direct_scr or {}).get("ratios", {}).get("current_price") or (data or {}).get("current_price", 0.0)
    mcap_cr = (direct_scr or {}).get("ratios", {}).get("market_cap_cr") or (data or {}).get("market_cap_cr", 0.0)
    high_52 = (direct_scr or {}).get("ratios", {}).get("high_52w") or (data or {}).get("high_52w", 0.0)
    low_52 = (direct_scr or {}).get("ratios", {}).get("low_52w") or (data or {}).get("low_52w", 0.0)

    if direct_scr and not editorial_memo:
        try:
            thesis_agent = ThesisAgent()
            editorial_memo = thesis_agent.generate_editorial_memo(direct_scr)
            st.session_state[f"editorial_memo:{active_cid}"] = editorial_memo
            st.session_state["editorial_memo"] = editorial_memo
        except Exception as exc:
            logger.warning(f"Lazy thesis synthesis failed: {exc}")

    inst_rating = str((dossier or {}).get("institutional_rating", "[HOLD / FAIR VALUE]"))

    # Agents data references
    a0 = dossier.get("agent_0", {})
    a1 = dossier.get("agent_1", {})
    a2 = dossier.get("agent_2", {})
    a3 = dossier.get("agent_3", {})
    a4 = dossier.get("agent_4", {})
    a5 = dossier.get("agent_5", {})
    a6 = dossier.get("agent_6", {})
    a7 = dossier.get("agent_7", {})
    prim_disc = dossier.get("primary_disclosures", {})

    # Ensure Fundamental Investment Decision Engine has run
    if not intel:
        try:
            coordinator = DecisionEngineCoordinator()
            canonical_id = resolve_canonical_identity(clean_sym)
            r_ctx = create_research_context(canonical_id)
            intel = coordinator.run_investment_intelligence_audit(
                company_data=data,
                screener_data=data,
                dossier=dossier or {},
                run_context=r_ctx
            )
            st.session_state["intel_dossier"] = intel
        except Exception as exc:
            logger.error(f"Fallback decision engine audit failed for {clean_sym}: {exc}", exc_info=True)
            intel = None

    # Resolve canonical identity for regulatory symbols and classification
    try:
        canonical_id = resolve_canonical_identity(clean_sym)
    except Exception:
        canonical_id = None

    cid = (intel or {}).get("company_id") or getattr(canonical_id, "company_id", f"NSE_{clean_sym}")
    isin = getattr(canonical_id, "isin", (intel or {}).get("isin") or "INE-VERIFIED")
    nse_sym = getattr(canonical_id, "nse_symbol", clean_sym)
    bse_code = getattr(canonical_id, "bse_code", "")
    sector_name = getattr(canonical_id, "sector", sector or "General")
    industry_name = getattr(canonical_id, "industry", industry or "Diversified")

    # Fetch live day change metrics
    day_chg_rs, day_chg_pct = fetch_day_change(clean_sym)

    simple_exp = (intel or {}).get("simple_explanation", {})
    health_status = simple_exp.get("core_change", {}).get("status", "VERIFIED AUDIT")

    # Extract verified financial tables from direct extract or engine data
    if direct_scr:
        scr_cname = direct_scr.get("company_name", company_name)
        scr_cmp_str = direct_scr.get("ratios", {}).get("Current Price", fmt_curr(cmp))
        scr_mcap_str = direct_scr.get("ratios", {}).get("Market Cap", fmt_cr(mcap_cr))
        scr_about = direct_scr.get("about", "")
        scr_ratios = direct_scr.get("ratios", {})
        scr_pl_df = direct_scr.get("pl_dataframe")
        q_df = direct_scr.get("quarters_table", {}).get("df")
        bs_df = direct_scr.get("balance_sheet_table", {}).get("df")
        cf_df = direct_scr.get("cash_flow_table", {}).get("df")
        r_df = direct_scr.get("ratios_table", {}).get("df")
        sh_df = direct_scr.get("shareholding_table", {}).get("df")
        announcements = direct_scr.get("announcements", [])
    else:
        scr_cname = company_name
        scr_cmp_str = fmt_curr(cmp)
        scr_mcap_str = fmt_cr(mcap_cr)
        scr_about = data.get("raw_summary", "") if data else ""
        scr_ratios = {
            "Market Cap": fmt_cr(mcap_cr),
            "Current Price": fmt_curr(cmp),
            "High / Low": f"₹{high_52:,.0f} / ₹{low_52:,.0f}",
            "Stock P/E": f"{data.get('pe_ratio', 0.0):.1f}" if data and data.get('pe_ratio', 0.0) > 0 else "—",
            "Book Value": f"₹{data.get('book_value', 0.0):,.1f}" if data else "—",
            "Dividend Yield": f"{data.get('dividend_yield_pct', 0.0):.2f}%" if data else "—",
            "ROCE": f"{data.get('roce_pct', 0.0):.1f}%" if data else "—",
            "ROE": f"{data.get('roe_pct', 0.0):.1f}%" if data else "—",
            "Face Value": f"₹{data.get('face_value', 1.0):.1f}" if data else "₹ 1.0",
        }
        scr_pl_df = data.get("pl_dataframe") if data else None
        q_df = pd.DataFrame(data.get("quarterly_rows", [])) if data and data.get("quarterly_rows") else None
        bs_df = pd.DataFrame(data.get("balance_sheet_rows", [])) if data and data.get("balance_sheet_rows") else None
        cf_df = pd.DataFrame(data.get("cash_flow_rows", [])) if data and data.get("cash_flow_rows") else None
        r_df = pd.DataFrame(data.get("ratio_rows", [])) if data and data.get("ratio_rows") else None
        sh_df = None
        announcements = []

    peer_rows = (data or {}).get("peer_rows", [])
    debt_to_equity = (data or {}).get("debt_to_equity")

    # Enrich announcements feed with Drishti intelligence if available
    d_intel = (intel or {}).get("drishti_intelligence")
    if d_intel and d_intel.get("news"):
        for dn in d_intel["news"]:
            hl = getattr(dn, "headline", "") or (dn.get("headline", "") if isinstance(dn, dict) else "")
            dt = getattr(dn, "publication_date", "") or (dn.get("publication_date", "") if isinstance(dn, dict) else "")
            src = getattr(dn, "article_source", "") or (dn.get("article_source", "Drishti News") if isinstance(dn, dict) else "Drishti News")
            lk = getattr(dn, "source_url", "") or (dn.get("source_url", "") if isinstance(dn, dict) else "")
            if hl and not any(a.get("headline") == hl for a in announcements):
                announcements.append({
                    "headline": hl,
                    "date": dt,
                    "source": f"Drishti News ({src})",
                    "link": lk,
                })

    # =====================================================================
    # SIMPLIFIED 5-MINUTE COMPANY RESEARCH FLOW
    # =====================================================================

    # 1. Company Header & Stock Chart (Clean, No Long Descriptions)
    render_section_1_header_and_chart(
        company_name=scr_cname,
        ticker=clean_sym,
        current_price=cmp,
        day_change_rs=day_chg_rs,
        day_change_pct=day_chg_pct,
        market_cap_str=scr_mcap_str,
        sector=sector_name,
    )

    # 2. Key Financial Numbers (Screener-style compact typography: Revenue, EBITDA, Margin, PAT, ROE, Debt)
    render_section_2_key_financials(
        pl_df=scr_pl_df,
        bs_df=bs_df,
        ratios_dict=scr_ratios,
        data_dict=data or {},
    )

    # 3. What Does This Company Do? (2-4 lines + [View details])
    render_section_3_business_snapshot(
        company_name=scr_cname,
        about_text=scr_about,
        about_data=about,
    )

    # 4. What's Changing? (Automatic change detection with ↑/↓)
    render_section_4_whats_changing(
        pl_df=scr_pl_df,
        bs_df=bs_df,
        cf_df=cf_df,
        intel=intel or {},
    )

    # 5. Why Is It Happening? (3-5 important questions with numbers & evidence)
    render_section_5_why_is_it_happening(
        intel=intel or {},
        pl_df=scr_pl_df,
        bs_df=bs_df,
        cf_df=cf_df,
    )

    # 6. Financial Trend ([QoQ] [YoY] [5Y] tabs with Revenue, EBITDA, Margin, PAT, EPS, CFO)
    render_section_6_financial_trends(
        pl_df=scr_pl_df,
        q_df=q_df,
        cf_df=cf_df,
    )

    # 7. Risk Check (Debt, Receivables, Margin, Cash Flow with ✓ / ⚠ signals)
    render_section_7_risk_check(
        pl_df=scr_pl_df,
        bs_df=bs_df,
        cf_df=cf_df,
        data_dict=data or {},
    )

    # 8 & 9. Opportunities & Risks (Short, factual, evidence-backed)
    render_section_8_and_9_opps_and_risks(
        intel=intel or {},
    )

    # 10. Ask About This Company (Interactive Q&A with suggested chips)
    render_section_10_ask_company_qa(
        company_name=scr_cname,
        ticker=clean_sym,
        intel=intel or {},
        data_dict=data or {},
        pl_df=scr_pl_df,
        bs_df=bs_df,
        cf_df=cf_df,
    )

    # 11. Deep Dive (Collapsible area: Statements, Forensics, Valuation, Peers, Sources)
    render_section_11_deep_dive(
        company_name=scr_cname,
        ticker=clean_sym,
        direct_scr=direct_scr,
        screener_data=data or {},
        intel=intel or {},
        dossier=dossier,
    )
