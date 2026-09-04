"""
Full-Stack Institutional Equity Research Dashboard (NSE/BSE)
Multi-Agent Analysis Platform (Agents 0 through 6)
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any

from agents.pipeline import EquityAgentPipeline

# Page configuration
st.set_page_config(
    page_title="BharatAlpha | 7-Agent Institutional Equity Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .company-title {
        font-size: 26px;
        font-weight: 700;
        color: #F0F2F6;
        margin-bottom: 4px;
    }
    .company-subtitle {
        font-size: 14px;
        color: #9AA0A6;
        margin-bottom: 16px;
    }
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 14px 0px 22px 0px;
    }
    .risk-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }
    .pill-green {
        background-color: rgba(46, 125, 50, 0.2);
        color: #81C784;
        border: 1px solid #2E7D32;
    }
    .pill-yellow {
        background-color: rgba(245, 127, 23, 0.2);
        color: #FFD54F;
        border: 1px solid #F57F17;
    }
    .pill-red {
        background-color: rgba(198, 40, 40, 0.2);
        color: #E57373;
        border: 1px solid #C62828;
    }
    .rating-badge {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 700;
        text-align: center;
        margin-top: 8px;
        letter-spacing: 0.5px;
    }
    .bullet-card {
        background-color: #1A1D24;
        border-left: 3px solid #3F51B5;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 0px 6px 6px 0px;
        font-size: 14px;
    }
    .q-box {
        background-color: #161920;
        border: 1px solid #282C37;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .q-title {
        font-size: 13px;
        font-weight: 700;
        color: #64B5F6;
        margin-bottom: 4px;
    }
    .q-ans {
        font-size: 14px;
        color: #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_pipeline():
    return EquityAgentPipeline()


def render_risk_pill(domain: str, status: str) -> str:
    color_class = "pill-green" if status == "GREEN" else ("pill-yellow" if status == "YELLOW" else "pill-red")
    icon = "●"
    return f'<div class="risk-pill {color_class}"><span>{icon}</span> {domain}: {status}</div>'


def main():
    # Sidebar
    st.sidebar.title("🏛️ BharatAlpha Research")
    st.sidebar.caption("Unabridged 7-Agent Institutional Equity Pipeline")

    st.sidebar.subheader("Valuation & DCF Assumptions")
    wacc_input = st.sidebar.slider("Cost of Capital (WACC %)", min_value=9.0, max_value=16.0, value=11.5, step=0.5) / 100.0
    terminal_g_input = st.sidebar.slider("Terminal FCF Growth (%)", min_value=3.0, max_value=7.0, value=5.5, step=0.5) / 100.0
    base_g_input = st.sidebar.slider("Base 10Y FCF CAGR (%)", min_value=5.0, max_value=25.0, value=12.0, step=1.0) / 100.0

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Multi-Agent Checklist Architecture:**
    - 🏷️ **Agent 0**: Classifier (`agent0_classifier.txt`)
    - 🛡️ **Agent 1**: Qualitative & Moat (`agent1_qualitative.txt`)
    - 🔍 **Agent 2**: Forensic Detective (`agent2_forensics.txt`)
    - ⚖️ **Agent 3**: Solvency & Capital (`agent3_solvency.txt`)
    - 🏛️ **Agent 4**: Governance & Master RPT (`agent4_governance_rpt.txt`)
    - 📈 **Agent 5**: Industry KPI Specialist (`agent5_industry_kpi.txt`)
    - 🎯 **Agent 6**: CIO Valuation & Reverse DCF (`agent6_valuation_cio.txt`)
    """)

    # Main Header & Search
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        st.title("Indian Equity Institutional Research Platform")
        st.caption("Deep forensic accounting, governance & RPT audits, industry KPIs, and reverse DCF.")

    # Search Bar
    ticker_input = st.text_input("Enter NSE/BSE Stock Ticker:", value="CROMPTON.NS")

    # Quick Ticker Buttons
    quick_cols = st.columns(6)
    quick_tickers = ["CROMPTON.NS", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "INFY.NS"]
    for i, t in enumerate(quick_tickers):
        if quick_cols[i].button(t.replace(".NS", ""), use_container_width=True):
            ticker_input = t

    if not ticker_input:
        st.info("Please enter an Indian stock ticker above to start the multi-agent audit.")
        return

    # Run Pipeline
    pipeline = get_pipeline()
    
    with st.spinner(f"Running Unabridged 7-Agent Institutional Pipeline for {ticker_input}..."):
        try:
            dossier = pipeline.run_pipeline(
                ticker=ticker_input,
                wacc=wacc_input,
                terminal_growth=terminal_g_input,
                base_growth=base_g_input
            )
        except Exception as e:
            st.error(f"Error executing agent pipeline for '{ticker_input}': {str(e)}")
            st.info("Tip: Ensure the symbol is valid on NSE or BSE (e.g., CROMPTON.NS, RELIANCE.NS, TCS.NS).")
            return

    symbol = dossier.get("symbol")
    company_name = dossier.get("company_name")
    cmp = dossier.get("current_price", 0.0)
    mcap_cr = dossier.get("market_cap_cr", 0.0)
    pe = dossier.get("trailing_pe", 0.0)
    ev_ebitda = dossier.get("ev_to_ebitda", 0.0)
    high_52 = dossier.get("fifty_two_week_high", 0.0)
    low_52 = dossier.get("fifty_two_week_low", 0.0)
    rating = dossier.get("institutional_rating", "[HOLD / FAIR VALUE]")
    rating_color = dossier.get("rating_color", "#1565C0")
    pills = dossier.get("risk_pills", {})

    # Top Hero Section
    st.markdown("---")
    hero_c1, hero_c2 = st.columns([3, 1])

    with hero_c1:
        st.markdown(f'<div class="company-title">{company_name} ({symbol})</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="company-subtitle">{dossier.get("sector")} • {dossier.get("industry")} • {dossier["agent_0"].get("primary_sector")}</div>', unsafe_allow_html=True)

    with hero_c2:
        st.markdown(f'<div class="rating-badge" style="background-color: {rating_color}; color: white;">{rating}</div>', unsafe_allow_html=True)

    # Key Metrics Bar
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
    m_col1.metric("CMP", f"₹{cmp:,.2f}")
    m_col2.metric("Market Cap", f"₹{mcap_cr:,.1f} Cr")
    m_col3.metric("52W Range", f"₹{low_52:,.0f} - {high_52:,.0f}")
    m_col4.metric("Trailing P/E", f"{pe:,.1f}x" if pe > 0 else "N/A")
    m_col5.metric("EV / EBITDA", f"{ev_ebitda:,.1f}x" if ev_ebitda > 0 else "N/A")
    m_col6.metric("Implied 10Y FCF CAGR", f"{dossier.get('implied_growth_pct')}%")

    # Colored Risk Pills Horizontal Ribbon
    st.markdown('<div class="pill-container">' + "".join([
        render_risk_pill(domain, status) for domain, status in pills.items()
    ]) + '</div>', unsafe_allow_html=True)

    # Accordion Tabs for All 7 Agent Audits
    st.subheader("🔬 Unabridged Multi-Agent Audit Dossier")

    # Agent 0: Classifier
    with st.expander("🏷️ Agent 0: Industry Taxonomy & Routing Profile", expanded=False):
        a0 = dossier["agent_0"]
        st.caption("System Prompt dynamically loaded from: `agent0_classifier.txt`")
        
        c0_1, c0_2 = st.columns(2)
        c0_1.metric("Primary Sector (1 of 12)", a0.get("primary_sector"))
        c0_2.metric("Sub-Vertical", a0.get("sub_vertical")[:45] + "...")

        st.markdown("##### 📄 Exact Routing Profile JSON:")
        st.json(a0.get("routing_profile", {}))

        st.markdown("**Hybrid / Secondary Business Verticals:**")
        for hv in a0.get("hybrid_verticals", []):
            st.markdown(f"- {hv}")

    # Agent 1: Qualitative & Moat Auditor
    with st.expander("🛡️ Agent 1: Qualitative & Economic Moat Auditor", expanded=True):
        a1 = dossier["agent_1"]
        st.caption("System Prompt dynamically loaded from: `agent1_qualitative.txt`")
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
            for k, v in a1.get("part5_operations_scalability", {}).items():
                st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
        with t5:
            for k, v in a1.get("part6_scuttlebutt", {}).items():
                st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)
        with t6:
            for k, v in a1.get("part7_qualitative_risks", {}).items():
                st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)

    # Agent 2: Forensic Detective
    with st.expander("🔍 Agent 2: Forensic Accounting Detective", expanded=True):
        a2 = dossier["agent_2"]
        st.caption("System Prompt dynamically loaded from: `agent2_forensics.txt`")
        st.markdown(f"**Forensic Status**: {render_risk_pill('Forensics', a2.get('risk_pill'))}", unsafe_allow_html=True)
        st.markdown(f"**Detective Summary**: {a2.get('summary')}")

        m2_items = list(a2.get("audit_metrics", {}).items())
        m2_cols = st.columns(3)
        for idx, (k, v) in enumerate(m2_items):
            m2_cols[idx % 3].metric(k, str(v))

        # CFO vs PAT Chart
        cfo_pat_data = a2.get("cfo_pat_series", [])
        if cfo_pat_data:
            st.markdown("##### 📊 5-Year Cash Flow Divergence (CFO vs Net Profit)")
            df_cfo = pd.DataFrame(cfo_pat_data)
            fig_cfo = go.Figure()
            fig_cfo.add_trace(go.Bar(x=df_cfo["year"], y=df_cfo["pat_cr"], name="PAT (Net Profit ₹ Cr)", marker_color="#42A5F5"))
            fig_cfo.add_trace(go.Bar(x=df_cfo["year"], y=df_cfo["cfo_cr"], name="CFO (Operating Cash Flow ₹ Cr)", marker_color="#66BB6A"))
            fig_cfo.update_layout(
                barmode="group", height=300, margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_cfo, use_container_width=True)

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

    # Agent 3: Solvency & Capital Allocation
    with st.expander("⚖️ Agent 3: Balance Sheet, Solvency & Capital Allocation Analyst", expanded=False):
        a3 = dossier["agent_3"]
        st.caption("System Prompt dynamically loaded from: `agent3_solvency.txt`")
        st.markdown(f"**Solvency Status**: {render_risk_pill('Solvency', a3.get('risk_pill'))}", unsafe_allow_html=True)
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

    # Agent 4: Governance & Master RPT
    with st.expander("🏛️ Agent 4: Governance, RPT & Executive Remuneration Auditor", expanded=False):
        a4 = dossier["agent_4"]
        st.caption("System Prompt dynamically loaded from: `agent4_governance_rpt.txt`")
        st.markdown(f"**Governance Status**: {render_risk_pill('Governance', a4.get('risk_pill'))}", unsafe_allow_html=True)
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

    # Agent 5: Industry KPI Specialist
    with st.expander("📈 Agent 5: Industry KPI Specialist", expanded=False):
        a5 = dossier["agent_5"]
        st.caption("System Prompt dynamically loaded from: `agent5_industry_kpi.txt`")
        st.markdown(f"**Activated Sector Checklist**: `{a5.get('activated_checklist_section')}`")
        st.markdown(f"**Summary**: {a5.get('summary')}")

        kpi_items = list(a5.get("kpi_results", {}).items())
        kpi_cols = st.columns(2)
        for idx, (k, v) in enumerate(kpi_items):
            kpi_cols[idx % 2].metric(k, str(v))

    # Agent 6: CIO & Valuation Specialist
    with st.expander("🎯 Agent 6: Chief Investment Officer & Valuation Specialist", expanded=True):
        a6 = dossier["agent_6"]
        st.caption("System Prompt dynamically loaded from: `agent6_valuation_cio.txt`")
        st.markdown(f"**CIO Final Rating Badge**: `{a6.get('institutional_rating')}`")
        st.markdown(f"**CIO Synthesis**: {a6.get('summary')}")

        cio_tabs = st.tabs(["Section 1: Walk-the-Talk", "Section 2: Asset & Yield Floors", "Section 3: Reverse DCF", "Section 4: Scenario Matrix", "Invalidation Triggers"])

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
            st.markdown("##### 🛡️ Independent Valuation Floors (Non-DCF / Non-Relative)")
            floors = a6.get("section2_asset_yield_valuation", {})
            for k, v in floors.items():
                st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)

        with cio_tabs[2]:
            st.markdown("##### 🧮 Reverse DCF Hurdle Test")
            rdcf = a6.get("section3_reverse_dcf", {})
            for k, v in rdcf.items():
                st.markdown(f'<div class="q-box"><div class="q-title">{k.replace("_", " ").upper()}</div><div class="q-ans">{v}</div></div>', unsafe_allow_html=True)

            dcf_data = a6.get("dcf_model", {})
            sens = dcf_data.get("sensitivity_matrix", {})
            if sens and "matrix" in sens:
                st.markdown("###### Reverse DCF Sensitivity Matrix (Intrinsic Fair Value per Share ₹)")
                df_sens = pd.DataFrame(
                    sens["matrix"],
                    index=[f"Terminal Growth: {tg}" for tg in sens.get("terminal_growth_labels", [])],
                    columns=[f"WACC: {w}" for w in sens.get("wacc_labels", [])]
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

    # Download Report Button
    st.markdown("---")
    export_json = json.dumps({
        "symbol": symbol,
        "company_name": company_name,
        "current_price": cmp,
        "market_cap_cr": mcap_cr,
        "institutional_rating": rating,
        "agent_0_classifier": a0.get("routing_profile"),
        "agent_1_qualitative": a1.get("summary"),
        "agent_2_forensics": a2.get("summary"),
        "agent_3_solvency": a3.get("summary"),
        "agent_4_governance": a4.get("summary"),
        "agent_5_industry_kpi": a5.get("summary"),
        "agent_6_valuation_cio": a6.get("summary")
    }, indent=2)

    st.download_button(
        label="📥 Download Complete Institutional Dossier (JSON)",
        data=export_json,
        file_name=f"{symbol}_institutional_dossier.json",
        mime="application/json",
        use_container_width=True
    )


if __name__ == "__main__":
    main()
