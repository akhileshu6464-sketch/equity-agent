"""
Simple Investor Intelligence Deck (ui/components/simple_investor_deck.py)
Provides a clean, intuitive 2-5 minute investment overview for retail investors:
1. Company Snapshot (What does the company do in 2-3 simple sentences?)
2. What Changed? (Material changes with prominent numbers, arrows, and plain-English takeaways)
3. Why Did It Change? (Verified drivers with evidence and causation guard)
4. Is This Good, Bad, or Mixed? (Simple labels: GOOD, CONCERN, MIXED, WATCH, INVESTIGATE)
5. Financial Health (Cash flow, Debt, Receivables, Inventory, Working Capital, ROCE, ROE in plain English)
6. Potential Red Flags (Evidence-backed anomalies)
7. Market Valuation (Reverse DCF hurdle in plain English, NO BUY/HOLD/SELL)
8. Potential Opportunities & Key Risks (Structured with evidence, impact, what to monitor)
9. What Should I Watch Next? & Questions An Investor Should Ask
10. Progressive Disclosure: Click-to-verify "Why am I seeing this?" drawers.
"""

from typing import Dict, Any, List, Optional
import streamlit as st


def render_simple_investor_overview(
    simple_data: Dict[str, Any],
    screener_data: Dict[str, Any],
    intel: Dict[str, Any]
):
    """
    Renders the complete 2-5 Minute Simple Investor Intelligence Overview.
    Delegates to the smooth vertical storytelling presentation layer when story_sections are available.
    """
    story_sections = simple_data.get("story_sections")
    if story_sections:
        from ui.components.storytelling_view import render_vertical_storytelling_view
        render_vertical_storytelling_view(story_sections, screener_data, intel)
        return

    snapshot = simple_data.get("snapshot", "")
    core_chg = simple_data.get("core_change", {})
    cf_health = simple_data.get("cash_flow_health", {})
    debt_pos = simple_data.get("debt_position", {})
    val_hurdle = simple_data.get("valuation_hurdle", {})
    red_flags = simple_data.get("red_flags", [])
    answers_11 = simple_data.get("answers_to_11_questions", {})

    status_colors = {
        "GOOD": ("#34d399", "rgba(52, 211, 153, 0.12)"),
        "CONCERN": ("#f87171", "rgba(248, 113, 113, 0.15)"),
        "MIXED": ("#38bdf8", "rgba(56, 189, 248, 0.12)"),
        "WATCH": ("#fbbf24", "rgba(251, 191, 36, 0.12)"),
        "INVESTIGATE": ("#f97316", "rgba(249, 115, 22, 0.15)"),
    }

    # -------------------------------------------------------------------------
    # 1. COMPANY SNAPSHOT (2-3 Sentences)
    # -------------------------------------------------------------------------
    if snapshot:
        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 4px;">
🏢 What Does The Company Do? — Quick 2-Minute Snapshot
</div>
<div style="font-size: 0.95rem; color: #f8fafc; line-height: 1.6; font-weight: 400;">
{snapshot}
</div>
</div>""")

    # -------------------------------------------------------------------------
    # 2. WHAT CHANGED & WHY? (Primary Core Change Card)
    # -------------------------------------------------------------------------
    if core_chg:
        chg_status = core_chg.get("status", "WATCH")
        fg, bg = status_colors.get(chg_status, status_colors["WATCH"])
        dir_symbol = "▲" if core_chg.get("direction") == "UP" else ("▼" if core_chg.get("direction") == "DOWN" else "■")

        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid {fg}; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1.25rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
<div style="font-size: 0.76rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">
📈 What Changed Most Materially?
</div>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; color: {fg}; background: {bg}; border: 1px solid {fg}44; padding: 3px 8px; border-radius: 4px;">
{dir_symbol} {chg_status}
</span>
</div>
<div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.6rem; line-height: 1.35;">
{core_chg.get('headline')}
</div>
<div style="font-size: 0.92rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 0.75rem;">
{core_chg.get('simple_explanation')}
</div>
<div style="font-size: 0.76rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">
Source: {core_chg.get('source_citation')}
</div>
</div>""")

        # Progressive Disclosure Drawer: "Why am I seeing this?"
        with st.expander("🔍 Why am I seeing this? — Data & Math Audit Trail", expanded=False):
            st.markdown(f"**Data Used:** {core_chg.get('numbers_used')}")
            st.markdown(f"**Calculation Formula:** `{core_chg.get('formula_used')}`")
            st.markdown(f"**Classification:** `{core_chg.get('epistemological_type')}`")
            st.markdown(f"**Source Document:** {core_chg.get('source_citation')}")

    # -------------------------------------------------------------------------
    # 3. FINANCIAL HEALTH RADAR (Cash Flow, Debt, Valuation)
    # -------------------------------------------------------------------------
    st.subheader("Financial Health in Plain English")

    col_cf, col_debt, col_val = st.columns(3)

    with col_cf:
        if cf_health:
            st_col = status_colors.get(cf_health.get("status", "WATCH"), status_colors["WATCH"])[0]
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-top: 3px solid {st_col}; border-radius: 6px; padding: 1rem; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
<div>
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">💵 Cash Flow Health</div>
<div style="font-weight: 600; font-size: 0.92rem; color: #f8fafc; margin-bottom: 0.4rem;">{cf_health.get('headline')}</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5;">{cf_health.get('simple_explanation')}</div>
</div>
<div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; margin-top: 8px;">{cf_health.get('source_citation')}</div>
</div>""")

    with col_debt:
        if debt_pos:
            st_col = status_colors.get(debt_pos.get("status", "WATCH"), status_colors["WATCH"])[0]
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-top: 3px solid {st_col}; border-radius: 6px; padding: 1rem; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
<div>
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">⚖️ Debt & Borrowings</div>
<div style="font-weight: 600; font-size: 0.92rem; color: #f8fafc; margin-bottom: 0.4rem;">{debt_pos.get('headline')}</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5;">{debt_pos.get('simple_explanation')}</div>
</div>
<div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; margin-top: 8px;">{debt_pos.get('source_citation')}</div>
</div>""")

    with col_val:
        if val_hurdle:
            st_col = status_colors.get(val_hurdle.get("status", "WATCH"), status_colors["WATCH"])[0]
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-top: 3px solid {st_col}; border-radius: 6px; padding: 1rem; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
<div>
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">🎯 Market Expectations</div>
<div style="font-weight: 600; font-size: 0.92rem; color: #f8fafc; margin-bottom: 0.4rem;">{val_hurdle.get('headline')}</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5;">{val_hurdle.get('simple_explanation')}</div>
</div>
<div style="font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; margin-top: 8px;">{val_hurdle.get('source_citation')}</div>
</div>""")

    # -------------------------------------------------------------------------
    # 4. POTENTIAL RED FLAGS (Evidence-Backed Forensic Findings)
    # -------------------------------------------------------------------------
    if red_flags:
        st.subheader("Areas Requiring Investor Due Diligence (Potential Red Flags)")
        st.caption("These are mathematically verified divergences or accounting shifts that warrant investigation before committing capital. They are not accusations of wrongdoing.")

        for rf in red_flags:
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #f87171; border-radius: 6px; padding: 0.9rem 1.15rem; margin-bottom: 0.75rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
<span style="font-weight: 600; font-size: 0.9rem; color: #f8fafc;">⚠️ {rf.get('title')}</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: #f87171; background: rgba(248, 113, 113, 0.15); padding: 2px 7px; border-radius: 4px;">INVESTIGATE</span>
</div>
<div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 0.35rem;">
<strong>Observed Movement:</strong> {rf.get('what_was_noticed')}
</div>
<div style="font-size: 0.78rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.45rem;">
Evidence: {rf.get('evidence')}
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.5rem; background: #080c14; padding: 0.65rem 0.85rem; border-radius: 4px; font-size: 0.8rem;">
<div><span style="color: #38bdf8; font-weight: 600;">Routine Commercial Reason:</span><br/><span style="color: #94a3b8;">{rf.get('normal_business_explanation')}</span></div>
<div><span style="color: #f87171; font-weight: 600;">Potential Investment Risk:</span><br/><span style="color: #94a3b8;">{rf.get('potential_risk_explanation')}</span></div>
<div><span style="color: #fbbf24; font-weight: 600;">Where To Verify:</span><br/><span style="color: #94a3b8;">{rf.get('what_to_check')}</span></div>
</div>
</div>""")

    # -------------------------------------------------------------------------
    # 5. KEY QUESTIONS TO ASK & WHAT TO WATCH NEXT
    # -------------------------------------------------------------------------
    questions = answers_11.get("what_should_investor_monitor_next", [])
    opportunities = answers_11.get("what_opportunities_should_investor_investigate", [])
    risks = answers_11.get("what_risks_should_investor_investigate", [])

    col_q, col_opp_risk = st.columns([1.1, 0.9])

    with col_q:
        st.subheader("Questions An Investor Should Ask Next")
        if questions:
            for idx, q_item in enumerate(questions, 1):
                st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
<span style="color: #38bdf8; font-weight: 700; font-family: 'JetBrains Mono', monospace;">Q{idx}:</span>
<span style="color: #f8fafc; font-size: 0.88rem; font-weight: 500;"> {q_item}</span>
</div>""")
        else:
            st.write("No critical open questions flagged for current filings.")

    with col_opp_risk:
        st.subheader("Key Opportunities & Vulnerabilities")
        if opportunities:
            for opp in opportunities:
                st.html(f"""<div style="background: rgba(52, 211, 153, 0.05); border: 1px solid rgba(52, 211, 153, 0.2); border-left: 3px solid #34d399; border-radius: 5px; padding: 0.65rem 0.85rem; margin-bottom: 0.45rem; font-size: 0.85rem; color: #f8fafc;">
🚀 <strong>Potential Opportunity:</strong> {opp}
</div>""")
        if risks:
            for rk in risks:
                st.html(f"""<div style="background: rgba(248, 113, 113, 0.05); border: 1px solid rgba(248, 113, 113, 0.2); border-left: 3px solid #f87171; border-radius: 5px; padding: 0.65rem 0.85rem; margin-bottom: 0.45rem; font-size: 0.85rem; color: #f8fafc;">
🛡️ <strong>Key Risk To Monitor:</strong> {rk}
</div>""")
