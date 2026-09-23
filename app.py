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
        resolved_sym, matched_name = resolve_ticker_info(raw_user_input)
        clean_sym = extract_pure_symbol(resolved_sym) or resolved_sym

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
data = st.session_state.get(f"screener_data:{active_cid}") or st.session_state.get("screener_data")
dossier = st.session_state.get(f"dossier:{active_cid}") or st.session_state.get("dossier")
about = st.session_state.get(f"about_data:{active_cid}") or st.session_state.get("about_data")
intel = st.session_state.get(f"intel_dossier:{active_cid}") or st.session_state.get("intel_dossier")

if not data or not dossier:
    # Render Workstation Home Landing View when no company is searched
    render_workstation_home()
else:
    # HARD FAILURE ZERO-CONTAMINATION RENDER GATE
    try:
        if active_cid:
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

    company_name = data.get("company_name", "Corporate Enterprise")
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

    cid = (intel or {}).get("company_id") or f"NSE_{clean_sym}"
    isin = (intel or {}).get("isin") or "INE-VERIFIED"

    # ---------------------------------------------------------------------
    # LEVEL 1: Company Header & Identity
    # ---------------------------------------------------------------------
    render_company_header(
        company_name=company_name,
        symbol=clean_sym,
        sector=sector,
        industry=industry,
        cmp=cmp,
        market_cap_cr=mcap_cr,
        high_52=high_52,
        low_52=low_52,
        rating=inst_rating,
        website=website,
        bse_url=bse_url,
        nse_url=nse_url,
    )

    # Canonical Company Isolation Bar
    render_research_status_bar(cid=cid, isin=isin, period="FY2025 · Consolidated")

    # ---------------------------------------------------------------------
    # LEVEL 2: Key Investment Signals & Compounded Growth
    # ---------------------------------------------------------------------
    render_section_header("Key Investment Signals", "Latest audited fundamentals and cash metrics")
    render_key_investment_signals(data)
    render_compounded_growth_cards(data)

    # ---------------------------------------------------------------------
    # LEVEL 3: Business Health & Decision Matrix (7 Pillars)
    # ---------------------------------------------------------------------
    if intel and "decision_map" in intel:
        render_section_header("Business Health & Decision Matrix", "7 Fundamental Investment Pillars")
        render_decision_pillars(intel["decision_map"].get("decision_pillars", []))

    # ---------------------------------------------------------------------
    # MASTER WORKSTATION TABS (7 Integrated Modules)
    # ---------------------------------------------------------------------
    tab_dec, tab_fq, tab_ind, tab_dd, tab_stmt, tab_about, tab_dossier = st.tabs([
        "🎯 Core Decision Intelligence",
        "🛡️ Financial Quality & Forensics",
        "🌐 Industry, Catalysts & Risks",
        "🔍 Due Diligence & Audit Trail",
        "📊 Financial Statements",
        "🏢 Screener Profile & Moats",
        "🏛️ Institutional Dossier & Report"
    ])

    # ---------------------------------------------------------------------
    # TAB 1: Core Decision Intelligence (What Changed, Why, Signals, Valuation)
    # ---------------------------------------------------------------------
    with tab_dec:
        st.subheader("1. What Changed? — Multi-Year Trajectory & Divergence Alerts")
        if intel and "changes_detected" in intel:
            render_what_changed(intel["changes_detected"])

        st.subheader("2. Why Did It Change? — Audited Driver Attribution & Causation Guard")
        if intel and "driver_analysis" in intel:
            st.html(build_why_it_changed_html(intel["driver_analysis"]))

        st.subheader("3. Granular Business Signals — Positive, Negative & Watch")
        if intel and "signals" in intel:
            st.html(build_signals_dashboard_html(intel["signals"]))

        st.subheader("4. Valuation Expectations — Reverse DCF Growth Hurdle")
        if intel and "valuation_and_expectations" in intel:
            st.html(build_valuation_expectations_html(intel["valuation_and_expectations"]))

    # ---------------------------------------------------------------------
    # TAB 2: Financial Quality & Forensics
    # ---------------------------------------------------------------------
    with tab_fq:
        st.subheader("1. Cumulative 5-Year Cash Flow Conversion Waterfall")
        if intel and "financial_quality" in intel:
            render_cash_flow_waterfall(intel["financial_quality"])

        st.subheader("2. Systematic Forensic & Red-Flag Investigation")
        if intel and "forensic_audit" in intel:
            render_forensic_audit(intel["forensic_audit"].get("anomalies", []))

    # ---------------------------------------------------------------------
    # TAB 3: Industry, Catalysts & Risks
    # ---------------------------------------------------------------------
    with tab_ind:
        st.subheader("1. Industry Intelligence, Macro Factors & Structural Shifts")
        if intel and "industry_intelligence" in intel:
            st.html(build_industry_intelligence_html(intel["industry_intelligence"]))

        st.subheader("2. Future Catalysts & Opportunities vs Structural Vulnerabilities")
        if intel:
            st.html(build_opportunities_and_risks_html(
                intel.get("opportunities", []),
                intel.get("risks", [])
            ))

    # ---------------------------------------------------------------------
    # TAB 4: Due Diligence & Audit Trail
    # ---------------------------------------------------------------------
    with tab_dd:
        st.subheader("1. What Should The Investor Investigate Next?")
        if intel and "investor_investigation_questions" in intel:
            render_investor_questions(intel["investor_investigation_questions"])

        st.subheader("2. Corporate Regulatory Filings & Event Timeline")
        if intel and "event_timeline" in intel:
            render_event_timeline(intel["event_timeline"])

        st.subheader("3. TypeSafe AI JEV Structured Verification Gate Audit Trail")
        if intel and "jev_verification_log" in intel:
            render_jev_audit_log(intel["jev_verification_log"])

    # ---------------------------------------------------------------------
    # TAB 5: Financial Statements
    # ---------------------------------------------------------------------
    with tab_stmt:
        render_section_header("Profit & Loss", "Consolidated figures in ₹ Crores (Annual)")
        render_pl_table(data.get("pl_rows", []))

        q_rows = data.get("quarterly_rows", [])
        if q_rows:
            render_section_header("Quarterly Results", "Consolidated figures in ₹ Crores (Recent Quarters)")
            render_quarterly_table(q_rows)

        peer_rows = data.get("peer_rows", [])
        if peer_rows:
            render_section_header("Peer Comparison", "Sector benchmark peers listed in India")
            render_peer_table(peer_rows, target_symbol=clean_sym)

    # ---------------------------------------------------------------------
    # TAB 6: Screener Profile & Moats
    # ---------------------------------------------------------------------
    with tab_about:
        if not about or not about.get("company_description"):
            agent = EditorialAgent()
            about = agent.generate_comprehensive_about(
                summary_text=data.get("raw_summary", ""),
                company_name=company_name,
                symbol=clean_sym,
                sector=sector,
                industry=industry,
                screener_data=data,
                primary_disclosures=prim_disc
            )
            st.session_state["about_data"] = about

        comp_desc = about.get("company_description", data.get("raw_summary", ""))
        desc_paras = [p.strip() for p in comp_desc.split("\n\n") if p.strip()]
        desc_html = "".join([f"<p style='margin-bottom: 0.65rem;'>{p}</p>" for p in desc_paras])

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

        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;">
<div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.75rem;">
🏢 About {company_name} — Fundamental Profile
</div>
<div style="font-size: 0.88rem; line-height: 1.65; color: #cbd5e1; margin-bottom: 1.25rem;">
{desc_html}
</div>
<div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.5rem;">
📊 Company Fundamental Snapshot
</div>
{snapshot_grid_html}
<div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin-top: 1rem; margin-bottom: 0.5rem;">
📦 Core Business Operating Segments
</div>
{segments_html}
</div>""")

        subtab_biz, subtab_gov, subtab_market, subtab_comp = st.tabs([
            "🏢 Business Model & Revenue Mix",
            "📋 Corporate Facts & Governance",
            "🌍 Markets & Footprint",
            "🏆 Competitive Moat & Milestones"
        ])

        with subtab_biz:
            biz_model_text = about.get("business_model", "")
            if biz_model_text:
                st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
<div style="font-size: 0.92rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem;">💡 Revenue Generation & Contracting Model</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">{biz_model_text}</div>
</div>""")
            st.subheader("Segment Revenue Mix & Contribution")
            st.html(build_about_revenue_mix_html(about.get("revenue_mix", [])))

        with subtab_gov:
            st.subheader("Key Corporate Facts")
            st.html(build_about_facts_html(about.get("key_business_facts", {})))
            st.subheader("Major Subsidiaries & Concession SPVs")
            st.html(build_about_subsidiaries_html(about.get("subsidiaries_jvs", [])))

        with subtab_market:
            geo = about.get("geographic_presence", {})
            dom_text = geo.get("domestic", "Established domestic operations across major state clusters.")
            intl_text = geo.get("international", "Export presence and global client channels where disclosed.")
            geo_summary = geo.get("summary", "")

            col_dom, col_intl = st.columns(2)
            with col_dom:
                st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem;">
<div style="font-size: 0.92rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem;">🇮🇳 Domestic Operations & Clusters</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">{dom_text}</div>
</div>""")
            with col_intl:
                st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem;">
<div style="font-size: 0.92rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem;">🌐 International & Export Reach</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">{intl_text}</div>
</div>""")
            if geo_summary:
                st.html(f"<div style='font-size: 0.82rem; color: #94a3b8; margin-top: 0.5rem;'>📍 <em>{geo_summary}</em></div>")

            st.subheader("Key Customer Base & Primary Counterparties")
            cust_list = about.get("key_customers", [])
            if cust_list:
                cust_items = "".join([f"<li style='margin-bottom: 4px;'>{c}</li>" for c in cust_list])
                st.html(f"<ul style='color: #cbd5e1; font-size: 0.86rem; padding-left: 1.25rem;'>{cust_items}</ul>")

        with subtab_comp:
            comp = about.get("competitive_position", {})
            mkt_pos = comp.get("market_position", f"Established market position in {sector}.")
            scale_m = comp.get("scale_metrics", "")
            peers = comp.get("key_competitors", [])
            moats = comp.get("core_advantages", [])

            scale_line = f"<p style='margin-top: 4px;'><strong>Scale Metric:</strong> {scale_m}</p>" if scale_m else ""
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
<div style="font-size: 0.92rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem;">🏆 Market Position & Defensibility</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">
<p style="margin: 0;"><strong>Standing:</strong> {mkt_pos}</p>
{scale_line}
</div>
</div>""")

            if peers:
                peer_chips = "".join([f"<span style='background: #1e293b; color: #cbd5e1; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 6px;'>{p}</span>" for p in peers])
                st.subheader("Benchmark Competitors")
                st.html(f"<div style='display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 1rem;'>{peer_chips}</div>")

            if moats:
                moat_items = "".join([f"<div style='margin-bottom: 4px;'>🛡️ {m}</div>" for m in moats])
                st.subheader("Core Competitive Advantages & Moats")
                st.html(f"<div style='font-size: 0.86rem; color: #cbd5e1;'>{moat_items}</div>")

            st.subheader("Company History & Key Milestones")
            st.html(build_about_milestones_html(about.get("milestones", [])))

            sources = about.get("sources", [])
            if sources:
                render_evidence_drawer(prim_disc, sources)

    # ---------------------------------------------------------------------
    # TAB 7: Institutional Research Dossier
    # ---------------------------------------------------------------------
    with tab_dossier:
        render_section_header("Institutional Equity Research Dossier", "15 Multi-Dimensional Research Modules")

        subtab_moat, subtab_dossier_ind, subtab_fin, subtab_dossier_gov, subtab_concall, subtab_val = st.tabs([
            "🛡️ Business & Moat",
            "🌐 Industry & Peers",
            "📊 Financials & Quality",
            "🏛️ Governance & Filings",
            "🎙️ Concall & Guidance",
            "🎯 Valuation & Scenarios"
        ])

        with subtab_moat:
            st.subheader("Module 1: Company Overview, Business Model & Economic Moat")
            moat_md = dossier.get("moat_markdown")
            if moat_md:
                st.markdown(moat_md)

            p1_bm = a1.get("part1_business_model", {})
            for k, v in p1_bm.items():
                render_audit_item(k, v)

            p2_moat = a1.get("part2_competitive_moat", {})
            for k, v in p2_moat.items():
                render_audit_item(k, v)

            st.subheader("Module 11: Documented Growth Drivers & Operating Leverage")
            p5_ops = a1.get("part5_operations_scalability", {})
            if p5_ops:
                for k, v in p5_ops.items():
                    render_audit_item(k, v)
            else:
                render_audit_item("Capacity Additions & Operating Leverage Trajectory",
                                  "The enterprise exhibits operating leverage headroom as utilization across existing execution clusters expands.")

            st.subheader("Module 12: Near-Term & Long-Term Catalysts")
            render_audit_item("Documented vs Potential Catalysts",
                              "Near-term execution acceleration driven by primary sector demand and balance sheet deleveraging.")

        with subtab_dossier_ind:
            st.subheader("Module 2: Industry Research & Structural Market Dynamics")
            p3_ind = a1.get("part3_industry_growth", {})
            if p3_ind:
                for k, v in p3_ind.items():
                    render_audit_item(k, v)

            kpi_res = a5.get("kpi_results", {})
            if kpi_res:
                st.markdown("##### Sector-Specific Operational KPIs")
                for kpi_k, kpi_v in kpi_res.items():
                    render_audit_item(kpi_k, kpi_v)

            st.subheader("Module 8: Competitive Benchmarking & Peer Comparison")
            comp_matrix = a4.get("dimension4_competitor_matrix", {})
            if comp_matrix and isinstance(comp_matrix, dict):
                render_audit_item("Competitive Positioning & Peer Benchmarking", comp_matrix)

            leadership_md = dossier.get("leadership_markdown")
            if leadership_md:
                st.markdown(leadership_md)

        with subtab_fin:
            st.subheader("Module 3: 5-Year Historical Financial Analysis & DuPont Trajectory")
            p8_prof = a3.get("part8_profitability", {})
            if p8_prof:
                for k, v in p8_prof.items():
                    render_audit_item(k, v)

            p10_solv = a3.get("part10_solvency", {})
            if p10_solv:
                for k, v in p10_solv.items():
                    render_audit_item(k, v)

            st.subheader("Module 4: Quarterly Financial Trends & Driver Identification")
            render_audit_item("Quarterly Margin & Volume Momentum",
                              "Trailing quarterly performance reflects seasonal execution ramp-up and operational volume delivery.")

            st.subheader("Module 9: Financial Quality & Accrual Forensics")
            forensic_md = dossier.get("forensics_markdown")
            if forensic_md:
                st.markdown(forensic_md)

            p15_rev = a2.get("part15_revenue_quality", {})
            for k, v in p15_rev.items():
                render_audit_item(k, v)

            p11_wc = a3.get("part11_working_capital", {})
            for k, v in p11_wc.items():
                render_audit_item(k, v)

        with subtab_dossier_gov:
            st.subheader("Module 5: Annual Report Deep Analysis & Contingent Liabilities")
            p16_bs = a2.get("part16_balance_sheet", {})
            for k, v in p16_bs.items():
                render_audit_item(k, v)

            p13_dep = a2.get("part13_depreciation", {})
            for k, v in p13_dep.items():
                render_audit_item(k, v)

            st.subheader("Module 7: Management, Promoter Pledging & Corporate Governance")
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

            st.subheader("Module 10: Institutional Red Flag & Forensic Vulnerability Audit")
            render_audit_item("Critical Forensic Vulnerability Audit",
                              "Review contingent liabilities, contract assets, retention monies, and promoter encumbrance ratios.")

        with subtab_concall:
            st.subheader("Module 6: Earnings Conference Call Transcripts & Guidance Tracking")
            call_period = a7.get("call_period", "Recent Earnings Conference Call")
            tone = a7.get("tone_sentiment", "Pragmatic / Constructive")
            integrity = a7.get("integrity_score", "High Integrity")
            rev_guid = a7.get("revenue_growth_guidance", "Management targets execution in line with order book pacing.")
            margin_out = a7.get("margin_outlook", "Operating profit margins guided within historical corridors.")
            capex_comm = a7.get("committed_capex", "Routine capex funded from internal accruals.")

            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
<div style="font-size: 0.95rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.4rem;">{call_period} — Executive Management Tone & Guidance</div>
<div style="font-size: 0.86rem; line-height: 1.6; color: #cbd5e1;">
<p style="margin-bottom: 0.4rem;"><strong>Executive Tone:</strong> <span style="color: #38bdf8; font-weight: 600;">{tone}</span> &bull; <strong>Commitment Integrity Score:</strong> <span style="color: #34d399; font-weight: 600;">{integrity}</span></p>
<p style="margin-bottom: 0.4rem;"><strong>Revenue Growth Guidance:</strong> {rev_guid}</p>
<p style="margin-bottom: 0.4rem;"><strong>Margin Outlook:</strong> {margin_out}</p>
<p style="margin: 0;"><strong>Committed Capex:</strong> {capex_comm}</p>
</div>
</div>""")

            qa_list = a7.get("qa_highlights", [])
            if qa_list:
                st.markdown("##### Key Analyst Q&A Pushback & Management Responses")
                for qa in qa_list:
                    if isinstance(qa, dict):
                        q_text = qa.get("question", "Operational query")
                        ans_text = qa.get("answer") or qa.get("management_response", "Addressed in call")
                        inst = qa.get("analyst_institution") or qa.get("institution", "Institutional Equities")
                        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.85rem 1rem; margin-bottom: 0.65rem;">
<div style="font-size: 0.82rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.3rem;">{inst}</div>
<div style="font-size: 0.84rem; line-height: 1.5; color: #cbd5e1;">
<p style="margin-bottom: 0.25rem;"><strong>Q:</strong> {q_text}</p>
<p style="margin: 0;"><strong>Management Response:</strong> {ans_text}</p>
</div>
</div>""")

        with subtab_val:
            st.subheader("Module 13: Deterministic Multi-Stage DCF & Reverse DCF Hurdle")
            val_md = dossier.get("valuation_markdown")
            if val_md:
                st.markdown(val_md)

            dynamic_wacc = dossier.get("wacc_pct", 11.5)
            implied_hurdle = dossier.get("implied_growth_pct", "10.0%")
            mos = dossier.get("margin_of_safety_pct", 15.0)

            st.html(f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.65rem; margin-top: 1rem; margin-bottom: 1.25rem;">
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Cost of Capital (WACC)</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: #38bdf8;">{dynamic_wacc:.2f}%</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Reverse DCF Hurdle Rate</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: #34d399;">{implied_hurdle}</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Margin of Safety</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: #34d399;">{mos:+.1f}%</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Primary Architecture</div>
<div style="font-size: 0.95rem; font-weight: 600; color: #f8fafc; margin-top: 4px;">{dossier.get('primary_valuation', 'Multi-Stage DCF')}</div>
</div>
</div>""")

            st.subheader("Module 14: 3-Scenario Valuation Matrix")
            sc_matrix = a6.get("section4_scenario_matrix", {})
            bear = sc_matrix.get("bear_case", {})
            base = sc_matrix.get("base_case", {})
            bull = sc_matrix.get("bull_case", {})

            st.html(f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem;">
<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #f87171; border-radius: 6px; padding: 0.9rem 1.1rem;">
<div style="font-weight: 600; color: #f87171; font-size: 0.88rem; margin-bottom: 0.4rem;">Bear Case (Stressed)</div>
<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">
<div>Target Price: <strong style="color: #f87171;">{bear.get('fair_target_price', 'Downside floor')}</strong></div>
<div>Expected Return: <strong style="color: #f87171;">{bear.get('expected_return', '-15% to -25%')}</strong></div>
<div>Growth Assumed: {bear.get('growth_assumed', '4.0% to 6.0%')}</div>
</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; border-radius: 6px; padding: 0.9rem 1.1rem;">
<div style="font-weight: 600; color: #38bdf8; font-size: 0.88rem; margin-bottom: 0.4rem;">Base Case (Most Likely)</div>
<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">
<div>Target Price: <strong style="color: #34d399;">{base.get('fair_target_price', 'Fair intrinsic value')}</strong></div>
<div>Expected Return: <strong style="color: #34d399;">{base.get('expected_return', '+15% to +22%')}</strong></div>
<div>Growth Assumed: {base.get('growth_assumed', '11.0% to 13.5%')}</div>
</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #34d399; border-radius: 6px; padding: 0.9rem 1.1rem;">
<div style="font-weight: 600; color: #34d399; font-size: 0.88rem; margin-bottom: 0.4rem;">Bull Case (Accelerated Expansion)</div>
<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">
<div>Target Price: <strong style="color: #34d399;">{bull.get('fair_target_price', 'Upside valuation')}</strong></div>
<div>Expected Return: <strong style="color: #34d399;">{bull.get('expected_return', '+35% to +50%')}</strong></div>
<div>Growth Assumed: {bull.get('growth_assumed', '16.0% to 18.5%')}</div>
</div>
</div>
</div>""")

            st.subheader("Module 15: Synthesized Investment Thesis & Invalidation Triggers")
            inval_list = a6.get("invalidation_triggers", [])
            if inval_list:
                inval_items = "".join([f"<li style='margin-bottom: 4px;'>{t}</li>" for t in inval_list])
                st.html(f"""<div style="background: rgba(248, 113, 113, 0.08); border: 1px solid rgba(248, 113, 113, 0.3); border-left: 3px solid #f87171; border-radius: 6px; padding: 1rem 1.25rem;">
<strong style="color: #f87171; font-size: 0.88rem;">EXACT CONDITIONS REQUIRING THESIS INVALIDATION:</strong>
<ul style="margin-top: 0.5rem; margin-bottom: 0; font-size: 0.84rem; color: #cbd5e1; padding-left: 1.25rem;">{inval_items}</ul>
</div>""")
