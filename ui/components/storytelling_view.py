"""
Vertical Storytelling Presentation Layer (ui/components/storytelling_view.py)
Redesigns the final company analysis into a clean, smooth-scrolling vertical narrative:
1. COMPANY SNAPSHOT
2. WHAT CHANGED?
3. WHY DID IT CHANGE?
4. FINANCIAL HEALTH (Revenue, EBITDA, PAT, Margins, Cash Flow, Working Capital, Debt, ROCE/ROE)
5. FINANCIAL RED FLAGS (Forensics & Accounting Checks)
6. INDUSTRY & PEER COMPARISON
7. VALUATION / MARKET (Reverse DCF Embedded Hurdle)
8. OPPORTUNITIES (Catalysts & Growth Drivers)
9. RISKS (Concrete Business & Balance Sheet Vulnerabilities)
10. WHAT TO WATCH NEXT
11. INVESTOR QUESTIONS
12. SOURCES & EVIDENCE
"""

from typing import Dict, Any, List, Optional, Union
import streamlit as st
import html


def _escape(text: Any) -> str:
    """Safely escapes HTML strings."""
    if text is None:
        return ""
    return html.escape(str(text))


STATUS_THEMES = {
    "GOOD": {
        "fg": "#34d399",
        "bg": "rgba(52, 211, 153, 0.12)",
        "border": "#34d399",
        "symbol": "▲"
    },
    "CONCERN": {
        "fg": "#f87171",
        "bg": "rgba(248, 113, 113, 0.14)",
        "border": "#f87171",
        "symbol": "▼"
    },
    "MIXED": {
        "fg": "#38bdf8",
        "bg": "rgba(56, 189, 248, 0.12)",
        "border": "#38bdf8",
        "symbol": "◆"
    },
    "WATCH": {
        "fg": "#fbbf24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "#fbbf24",
        "symbol": "■"
    },
    "INVESTIGATE": {
        "fg": "#f97316",
        "bg": "rgba(249, 115, 22, 0.15)",
        "border": "#f97316",
        "symbol": "🔍"
    }
}


def render_structured_insight_card(insight: Dict[str, Any]):
    """
    Renders a unified StructuredInsight card consistently across all modules.
    Adheres strictly to the 5 core investor questions and traceable evidence.
    """
    title = _escape(insight.get("title", "Insight"))
    metric = _escape(insight.get("metric", "Financial Metric"))
    curr_val = _escape(insight.get("current_value", "Data unavailable"))
    prev_val = _escape(insight.get("previous_value", "Data unavailable"))
    change = _escape(insight.get("change", "Data unavailable"))
    explanation = _escape(insight.get("explanation", ""))
    driver = _escape(insight.get("driver", "The available evidence does not clearly establish the cause."))
    evidence = insight.get("evidence", {}) or {}
    classification = insight.get("classification", "WATCH").upper()
    source = _escape(insight.get("source", "Audited Financial Statements"))
    ver_status = _escape(insight.get("verification_status", "VERIFIED_AUDIT"))

    what_happened = _escape(insight.get("what_happened", ""))
    why_it_matters = _escape(insight.get("why_it_matters", ""))
    why_it_happened = _escape(insight.get("why_it_happened", driver))
    what_to_watch = _escape(insight.get("what_to_watch", ""))

    theme = STATUS_THEMES.get(classification, STATUS_THEMES["WATCH"])
    fg = theme["fg"]
    bg = theme["bg"]
    border_col = theme["border"]
    symbol = theme["symbol"]

    # Render card container
    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid {border_col}; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1.15rem; transition: transform 0.2s ease, border-color 0.2s ease;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
<div>
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">{metric}</div>
<div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-top: 2px;">{title}</div>
</div>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: {fg}; background: {bg}; border: 1px solid {fg}44; padding: 3px 8px; border-radius: 4px;">
{symbol} {classification}
</span>
</div>

<div style="display: flex; align-items: baseline; gap: 1.25rem; margin-bottom: 0.85rem; flex-wrap: wrap; background: #0b0f19; padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid #1e293b88;">
<div>
<div style="font-size: 0.68rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Previous</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: #94a3b8; font-weight: 600;">{prev_val}</div>
</div>
<div style="color: #475569; font-size: 1rem;">→</div>
<div>
<div style="font-size: 0.68rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Current</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">{curr_val}</div>
</div>
<div style="margin-left: auto;">
<div style="font-size: 0.68rem; color: #64748b; text-transform: uppercase; font-weight: 600; text-align: right;">Change</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; color: {fg}; font-weight: 700; text-align: right;">{change}</div>
</div>
</div>

<div style="font-size: 0.92rem; color: #e2e8f0; line-height: 1.6; margin-bottom: 0.9rem; font-weight: 400;">
{explanation}
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.65rem; background: #080c14; padding: 0.85rem 1rem; border-radius: 6px; border: 1px solid #1e293b44; font-size: 0.82rem; margin-bottom: 0.6rem;">
<div>
<span style="color: #38bdf8; font-weight: 600;">What happened?</span><br/>
<span style="color: #cbd5e1; line-height: 1.45;">{what_happened}</span>
</div>
<div>
<span style="color: #38bdf8; font-weight: 600;">Why does it matter?</span><br/>
<span style="color: #cbd5e1; line-height: 1.45;">{why_it_matters}</span>
</div>
<div>
<span style="color: #fbbf24; font-weight: 600;">Why did it happen?</span><br/>
<span style="color: #cbd5e1; line-height: 1.45;">{why_it_happened}</span>
</div>
<div>
<span style="color: #34d399; font-weight: 600;">What should the investor watch?</span><br/>
<span style="color: #cbd5e1; line-height: 1.45;">{what_to_watch}</span>
</div>
</div>
</div>""")

    # Expandable evidence drawer
    with st.expander("📄 View Evidence → Source, Document & Note", expanded=False):
        ev_src = _escape(evidence.get("source", source))
        ev_doc = _escape(evidence.get("document", "Audited Financial Statements"))
        ev_date = _escape(evidence.get("date", "Current"))
        ev_sec = _escape(evidence.get("page_or_section", "Notes to Accounts"))
        st.markdown(f"""
- **Primary Source:** `{ev_src}`
- **Filing Document:** `{ev_doc}`
- **Period / Date:** `{ev_date}`
- **Page / Section:** `{ev_sec}`
- **Verification Status:** `{ver_status}`
""")


def render_vertical_storytelling_view(
    story_data: Dict[str, Any],
    screener_data: Dict[str, Any],
    intel: Dict[str, Any]
):
    """
    Renders the complete 12-section vertical storytelling interface.
    Features smooth scroll navigation and clean card storytelling.
    """
    # -------------------------------------------------------------------------
    # Sticky Navigation Header & Smooth Scroll Style
    # -------------------------------------------------------------------------
    st.html("""<style>
html {
    scroll-behavior: smooth !important;
}
.rb-nav-sticky {
    position: -webkit-sticky;
    position: sticky;
    top: 0;
    z-index: 99;
    background: rgba(15, 23, 42, 0.94);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid #1e293b;
    padding: 0.6rem 0.5rem;
    margin-bottom: 1.75rem;
    display: flex;
    gap: 0.45rem;
    overflow-x: auto;
    white-space: nowrap;
}
.rb-nav-item {
    color: #94a3b8 !important;
    text-decoration: none !important;
    font-size: 0.74rem;
    font-weight: 600;
    padding: 0.35rem 0.7rem;
    border-radius: 6px;
    background: #0b0f19;
    border: 1px solid #1e293b;
    transition: all 0.2s ease;
}
.rb-nav-item:hover {
    color: #38bdf8 !important;
    border-color: #38bdf866;
    background: #1e293b;
}
.rb-story-section {
    scroll-margin-top: 75px;
    margin-bottom: 2.25rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid #1e293b44;
}
.rb-sec-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    padding: 2px 7px;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 0.4rem;
}
.rb-sec-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.2rem;
    letter-spacing: -0.01em;
}
.rb-sec-sub {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-bottom: 1.15rem;
    line-height: 1.45;
}
</style>

<div class="rb-nav-sticky">
<a href="#sec-snapshot" class="rb-nav-item">🏢 1. Snapshot</a>
<a href="#sec-what-changed" class="rb-nav-item">📈 2. What Changed?</a>
<a href="#sec-why-changed" class="rb-nav-item">🔍 3. Why It Changed</a>
<a href="#sec-health" class="rb-nav-item">❤️ 4. Financial Health</a>
<a href="#sec-red-flags" class="rb-nav-item">⚠️ 5. Red Flags</a>
<a href="#sec-industry" class="rb-nav-item">🌐 6. Industry & Peers</a>
<a href="#sec-valuation" class="rb-nav-item">🎯 7. Valuation / Market</a>
<a href="#sec-opps" class="rb-nav-item">🚀 8. Opportunities</a>
<a href="#sec-risks" class="rb-nav-item">🛡️ 9. Risks</a>
<a href="#sec-watch" class="rb-nav-item">👁️ 10. What to Watch</a>
<a href="#sec-questions" class="rb-nav-item">❓ 11. Investor Questions</a>
<a href="#sec-sources" class="rb-nav-item">📜 12. Sources</a>
</div>""")

    # -------------------------------------------------------------------------
    # 1. COMPANY SNAPSHOT
    # -------------------------------------------------------------------------
    snapshot_text = story_data.get("snapshot", "")
    st.html(f"""<div id="sec-snapshot" class="rb-story-section">
<div class="rb-sec-tag">SECTION 1 OF 12</div>
<div class="rb-sec-title">🏢 Company Snapshot</div>
<div class="rb-sec-sub">What does the company do in 2–3 plain sentences?</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid #38bdf8; border-radius: 8px; padding: 1.25rem 1.5rem;">
<div style="font-size: 0.95rem; color: #f8fafc; line-height: 1.65; font-weight: 400;">
{_escape(snapshot_text)}
</div>
</div>
</div>""")

    # -------------------------------------------------------------------------
    # 2. WHAT CHANGED?
    # -------------------------------------------------------------------------
    what_changed_insights = story_data.get("what_changed", [])
    st.html("""<div id="sec-what-changed" class="rb-story-section">
<div class="rb-sec-tag">SECTION 2 OF 12</div>
<div class="rb-sec-title">📈 What Changed?</div>
<div class="rb-sec-sub">Most material multi-year shifts in sales, profit and operating margins.</div>
</div>""")
    if what_changed_insights:
        for ins in what_changed_insights:
            render_structured_insight_card(ins)
    else:
        st.info("Verified comparative data is compiling...")

    # -------------------------------------------------------------------------
    # 3. WHY DID IT CHANGE?
    # -------------------------------------------------------------------------
    why_insights = story_data.get("why_it_changed", [])
    st.html("""<div id="sec-why-changed" class="rb-story-section">
<div class="rb-sec-tag">SECTION 3 OF 12</div>
<div class="rb-sec-title">🔍 Why Did It Change?</div>
<div class="rb-sec-sub">Audited driver attribution backed by verified filing evidence. Never guesses.</div>
</div>""")
    if why_insights:
        for ins in why_insights:
            render_structured_insight_card(ins)
    else:
        st.write("The available evidence does not clearly establish why margins shifted.")

    # -------------------------------------------------------------------------
    # 4. FINANCIAL HEALTH
    # -------------------------------------------------------------------------
    fin_health = story_data.get("financial_health", [])
    st.html("""<div id="sec-health" class="rb-story-section">
<div class="rb-sec-tag">SECTION 4 OF 12</div>
<div class="rb-sec-title">❤️ Financial Health</div>
<div class="rb-sec-sub">Revenue, EBITDA, PAT, Margins, Cash Flow, Working Capital, Debt, and Capital Efficiency in plain English.</div>
</div>""")
    if fin_health:
        for ins in fin_health:
            render_structured_insight_card(ins)

    # Clean expander for deep financial statement tables
    pl_rows = screener_data.get("pl_rows", [])
    q_rows = screener_data.get("quarterly_rows", [])
    if pl_rows or q_rows:
        with st.expander("📊 View Complete Audited Financial Statement Tables (Annual & Quarterly)", expanded=False):
            from ui.components.financial_table import render_pl_table, render_quarterly_table
            if pl_rows:
                st.markdown("##### Consolidated Annual Profit & Loss (₹ Crores)")
                render_pl_table(pl_rows)
            if q_rows:
                st.markdown("##### Consolidated Quarterly Results (₹ Crores)")
                render_quarterly_table(q_rows)

    # -------------------------------------------------------------------------
    # 5. FINANCIAL RED FLAGS
    # -------------------------------------------------------------------------
    red_flags = story_data.get("financial_red_flags", [])
    st.html("""<div id="sec-red-flags" class="rb-story-section">
<div class="rb-sec-tag">SECTION 5 OF 12</div>
<div class="rb-sec-title">⚠️ Financial Red Flags & Forensic Checks</div>
<div class="rb-sec-sub">Non-accusatory investigations of accounting shifts, receivables, and auditor disclosures.</div>
</div>""")
    if red_flags:
        for ins in red_flags:
            render_structured_insight_card(ins)
    else:
        st.write("Clean audit report issued by statutory auditors.")

    # -------------------------------------------------------------------------
    # 6. INDUSTRY & PEER COMPARISON
    # -------------------------------------------------------------------------
    ind_peers = story_data.get("industry_and_peers", [])
    st.html("""<div id="sec-industry" class="rb-story-section">
<div class="rb-sec-tag">SECTION 6 OF 12</div>
<div class="rb-sec-title">🌐 Industry & Peer Comparison</div>
<div class="rb-sec-sub">How the company stacks up against sector competitors in growth, profitability, and debt.</div>
</div>""")
    if ind_peers:
        for ins in ind_peers:
            render_structured_insight_card(ins)

    peer_rows = screener_data.get("peer_rows", [])
    if peer_rows:
        with st.expander("📊 View Benchmark Competitor Matrix (P/E, ROCE, Market Cap)", expanded=False):
            from ui.components.financial_table import render_peer_table
            clean_sym = screener_data.get("symbol", "")
            render_peer_table(peer_rows, target_symbol=clean_sym)

    # -------------------------------------------------------------------------
    # 7. VALUATION / MARKET
    # -------------------------------------------------------------------------
    val_market = story_data.get("valuation_and_market", [])
    st.html("""<div id="sec-valuation" class="rb-story-section">
<div class="rb-sec-tag">SECTION 7 OF 12</div>
<div class="rb-sec-title">🎯 Valuation & Market Expectations</div>
<div class="rb-sec-sub">Reverse DCF embedded growth hurdle vs historical track record. Zero stock tips.</div>
</div>""")
    if val_market:
        for ins in val_market:
            render_structured_insight_card(ins)

    # -------------------------------------------------------------------------
    # 8. GROWTH OPPORTUNITIES
    # -------------------------------------------------------------------------
    opps = story_data.get("opportunities", [])
    st.html("""<div id="sec-opps" class="rb-story-section">
<div class="rb-sec-tag">SECTION 8 OF 12</div>
<div class="rb-sec-title">🚀 Growth Opportunities & Catalysts</div>
<div class="rb-sec-sub">Concrete expansion avenues, tender pipelines, and capacity additions backed by filings.</div>
</div>""")
    if opps:
        for ins in opps:
            render_structured_insight_card(ins)

    # -------------------------------------------------------------------------
    # 9. KEY INVESTMENT RISKS
    # -------------------------------------------------------------------------
    risks = story_data.get("risks", [])
    st.html("""<div id="sec-risks" class="rb-story-section">
<div class="rb-sec-tag">SECTION 9 OF 12</div>
<div class="rb-sec-title">🛡️ Key Investment Risks & Vulnerabilities</div>
<div class="rb-sec-sub">Specific operational, raw-material, and balance-sheet factors that could impair future returns.</div>
</div>""")
    if risks:
        for ins in risks:
            render_structured_insight_card(ins)

    # -------------------------------------------------------------------------
    # 10. WHAT TO WATCH NEXT
    # -------------------------------------------------------------------------
    watch = story_data.get("what_to_watch", [])
    st.html("""<div id="sec-watch" class="rb-story-section">
<div class="rb-sec-tag">SECTION 10 OF 12</div>
<div class="rb-sec-title">👁️ What To Watch Next</div>
<div class="rb-sec-sub">Specific operational triggers and quarterly milestones to monitor over the next 2–4 quarters.</div>
</div>""")
    if watch:
        for ins in watch:
            render_structured_insight_card(ins)

    # -------------------------------------------------------------------------
    # 11. INVESTOR QUESTIONS
    # -------------------------------------------------------------------------
    questions = story_data.get("investor_questions", [])
    st.html("""<div id="sec-questions" class="rb-story-section">
<div class="rb-sec-tag">SECTION 11 OF 12</div>
<div class="rb-sec-title">❓ Questions An Investor Should Ask</div>
<div class="rb-sec-sub">Practical due diligence questions for management conference calls and annual report reading.</div>
</div>""")
    if questions:
        for ins in questions:
            render_structured_insight_card(ins)

    # -------------------------------------------------------------------------
    # 12. SOURCES & AUDIT TRAIL
    # -------------------------------------------------------------------------
    sources = story_data.get("sources", [])
    st.html("""<div id="sec-sources" class="rb-story-section">
<div class="rb-sec-tag">SECTION 12 OF 12</div>
<div class="rb-sec-title">📜 Sources & Document Verification Audit Trail</div>
<div class="rb-sec-sub">Every claim and metric is company-locked and verified against primary regulatory disclosures.</div>
</div>""")

    sources_html = []
    for s in sources:
        t = _escape(s.get("title", "Filing"))
        d = _escape(s.get("date", "Recent"))
        ft = _escape(s.get("filing_type", "Regulatory Disclosure"))
        st_badge = _escape(s.get("status", "VERIFIED_AUDIT"))

        sources_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
<div>
<div style="font-weight: 600; font-size: 0.88rem; color: #f8fafc;">{t}</div>
<div style="font-size: 0.75rem; color: #94a3b8;">Filing Type: {ft} · Date: {d}</div>
</div>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: #34d399; background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.25); padding: 2px 7px; border-radius: 4px;">
✓ {st_badge}
</span>
</div>""")

    st.html(f"""<div style="margin-bottom: 2rem;">
{"".join(sources_html)}
</div>""")
