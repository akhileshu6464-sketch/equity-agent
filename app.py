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
from fpdf import FPDF

from agents.pipeline import EquityAgentPipeline


class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, f'{self.ticker} - Institutional Equity Audit', border=False, align='C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', border=False, align='C')


def generate_pdf(report_text: str, ticker: str) -> bytes:
    pdf = PDFReport()
    pdf.ticker = ticker
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=10)
    
    # Sanitize text to latin-1 to avoid fpdf encoding crashes
    clean_text = report_text.replace('₹', 'Rs. ').encode('latin-1', 'replace').decode('latin-1')
    
    for line in clean_text.split('\n'):
        if not line.strip():
            pdf.ln(3)
        else:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, line)
    
    return bytes(pdf.output())

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
    .report-card {
        background-color: #131720;
        border: 1px solid #2A303C;
        border-radius: 8px;
        padding: 24px;
        margin: 20px 0px 30px 0px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
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

    # Session state for ticker selection
    if "selected_ticker" not in st.session_state:
        st.session_state["selected_ticker"] = "CROMPTON.NS"

    # Quick Ticker Buttons passing valid tickers (.NS)
    quick_cols = st.columns(6)
    quick_tickers = ["CROMPTON.NS", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "INFY.NS"]
    for i, t in enumerate(quick_tickers):
        label = t.replace(".NS", "")
        if quick_cols[i].button(label, key=f"quick_btn_{t}", use_container_width=True):
            st.session_state["selected_ticker"] = t

    # Search Bar
    user_input = st.text_input(
        "Enter NSE/BSE Stock Ticker (e.g., RELIANCE, TCS, HDFCBANK, CROMPTON):",
        value=st.session_state.get("selected_ticker", "CROMPTON.NS")
    )

    if not user_input or not user_input.strip():
        st.info("ℹ️ Please enter an Indian stock ticker above to start the multi-agent audit.")
        return

    # 1. Automatic Suffix Appender: Ensure ticker ends with .NS or .BO
    ticker = user_input.strip().upper()
    if not (ticker.endswith(".NS") or ticker.endswith(".BO")):
        ticker += ".NS"
    st.session_state["selected_ticker"] = ticker

    # Run Pipeline
    pipeline = get_pipeline()
    
    with st.spinner(f"Running Unabridged 7-Agent Institutional Pipeline for {ticker}..."):
        try:
            dossier = pipeline.run_pipeline(
                ticker=ticker,
                wacc=wacc_input,
                terminal_growth=terminal_g_input,
                base_growth=base_g_input
            )
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
            return

    symbol = dossier.get("symbol", ticker)
    company_name = dossier.get("company_name", ticker)
    cmp = dossier.get("current_price", 0.0)
    mcap_cr = dossier.get("market_cap_cr", 0.0)
    pe = dossier.get("trailing_pe", 0.0)
    ev_ebitda = dossier.get("ev_to_ebitda", 0.0)
    high_52 = dossier.get("fifty_two_week_high", 0.0)
    low_52 = dossier.get("fifty_two_week_low", 0.0)
    rating = dossier.get("institutional_rating", "[HOLD / FAIR VALUE]")
    rating_color = dossier.get("rating_color", "#1565C0")
    pills = dossier.get("risk_pills", {})

    a0 = dossier.get("agent_0", {})
    a1 = dossier.get("agent_1", {})
    a2 = dossier.get("agent_2", {})
    a3 = dossier.get("agent_3", {})
    a4 = dossier.get("agent_4", {})
    a5 = dossier.get("agent_5", {})
    a6 = dossier.get("agent_6", {})

    # Top Hero Section
    st.markdown("---")
    hero_c1, hero_c2 = st.columns([3, 1])

    with hero_c1:
        st.markdown(f'<div class="company-title">{company_name} ({symbol})</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="company-subtitle">{dossier.get("sector")} • {dossier.get("industry")} • {a0.get("primary_sector")}</div>', unsafe_allow_html=True)

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

    # =========================================================================
    # INSTITUTIONAL RESEARCH REPORT (Full Markdown Dossier on Main Page)
    # =========================================================================
    history_years = dossier.get("company_data", {}).get("history_years", [])
    total_cfo_cr = round(sum(h.get("operating_cash_flow", 0.0) for h in history_years) / 1e7, 1)

    full_report_md = f"""# 📑 Institutional Equity Research Dossier: {company_name} ({symbol})

**Ticker**: `{symbol}` | **Current Market Price (CMP)**: ₹{cmp:,.2f} | **Market Cap**: ₹{mcap_cr:,.1f} Cr | **52-Week Range**: ₹{low_52:,.0f} - ₹{high_52:,.0f}  
**Institutional Rating**: **{rating}** | **Sector**: {dossier.get('sector')} | **Primary Sector (1 of 12)**: **{a0.get('primary_sector')}**

---

### 🚦 Executive Risk Pill Dashboard
| Audit Domain | Risk Status | Institutional Evaluation |
| :--- | :---: | :--- |
| **Moat & Business Model** | `{pills.get('Moat & Business')}` | **{a1.get('moat_rating')}** (Checklist Score: {a1.get('checklist_score')}/100) — {a1.get('part2_competitive_moat', {}).get('2_moat_source')} |
| **Forensic Detective** | `{pills.get('Forensics')}` | 5-Year Cumulative CFO/PAT Conversion: **{a2.get('audit_metrics', {}).get('Cumulative CFO/PAT')}** (Cumulative CFO: ₹{total_cfo_cr} Cr) |
| **Solvency & Capital** | `{pills.get('Solvency')}` | Net Debt: **{a3.get('audit_metrics', {}).get('Net Debt')}** (Net Debt/Equity: {a3.get('audit_metrics', {}).get('Net Debt / Equity')}), CCC: **{a3.get('audit_metrics', {}).get('Cash Conversion Cycle')}** |
| **Governance & Master RPT** | `{pills.get('Governance')}` | Promoter Pledge: **{a4.get('audit_metrics', {}).get('Promoter Pledge')}**, Institutional Ownership: **{a4.get('audit_metrics', {}).get('Institutional Holding')}** |
| **Industry Operational KPIs** | `{pills.get('Industry KPIs')}` | Activated Section: **{a5.get('activated_checklist_section')}** |
| **Valuation & Reverse DCF** | `{pills.get('Valuation')}` | Implied 10Y FCF CAGR: **{dossier.get('implied_growth_pct')}%** (Base Case Fair Value: **{a6.get('audit_metrics', {}).get('Base Fair Value')}**) |

---

### 🏷️ Agent 0: Industry Taxonomy & Routing Profile
- **Primary Sector (Assigned 1 of 12)**: {a0.get('primary_sector')}
- **Sub-Vertical**: {a0.get('sub_vertical')}
- **Revenue Engine (>60% Profit Generator)**: {a0.get('revenue_engine_summary')}
- **Secondary / Hybrid Business Verticals**: {', '.join(a0.get('hybrid_verticals', [])) if a0.get('hybrid_verticals') else 'None'}

---

### 🛡️ Agent 1: Qualitative & Economic Moat Analysis
- **Core Product / Service**: {a1.get('part1_business_model', {}).get('1_core_product_service')}
- **Revenue Mechanics**: {a1.get('part1_business_model', {}).get('2_revenue_model')}
- **Customer Concentration & Switching Costs**: {a1.get('part1_business_model', {}).get('3_customer_concentration')} | {a1.get('part1_business_model', {}).get('4_switching_costs')}
- **Sales Engine**: {a1.get('part1_business_model', {}).get('5_sales_process')}
- **Economic Moat Source & Trajectory**: {a1.get('part2_competitive_moat', {}).get('2_moat_source')} ({a1.get('part2_competitive_moat', {}).get('3_moat_trajectory')})
- **Barriers to Entry**: {a1.get('part2_competitive_moat', {}).get('1_barriers_to_entry')}
- **Pricing Power & Pass-Through**: {a1.get('part2_competitive_moat', {}).get('5_pricing_power')}
- **Industry Structural Growth & TAM**: {a1.get('part3_industry_growth', {}).get('1_structural_growth')} — {a1.get('part3_industry_growth', {}).get('2_tam_and_headroom')}
- **Cyclicality & Recession Resilience**: {a1.get('part3_industry_growth', {}).get('3_cyclicality_recession')}
- **Scalability & Operating Leverage**: {a1.get('part5_operations_scalability', {}).get('1_operating_leverage')}
- **Supply Chain Risks & Capital Intensity**: {a1.get('part5_operations_scalability', {}).get('2_supply_chain_risks')} | {a1.get('part5_operations_scalability', {}).get('3_capital_intensity')}
- **Ground-Level Scuttlebutt**: {a1.get('part6_scuttlebutt', {}).get('1_customer_sentiment')} | Workplace Culture: {a1.get('part6_scuttlebutt', {}).get('2_employee_culture')}
- **Single Biggest Operational Failure Point**: {a1.get('part7_qualitative_risks', {}).get('4_single_biggest_failure_point')}

---

### 🔍 Agent 2: Forensic Accounting Detective
- **5-Year Cumulative CFO vs PAT Conversion**: {a2.get('part15_revenue_quality', {}).get('3_cfo_pat_divergence')}
- **Receivables & DSO Trajectory**: {a2.get('part15_revenue_quality', {}).get('2_dso_trajectory')} (Channel Stuffing Check: {a2.get('part15_revenue_quality', {}).get('1_receivables_vs_revenue')})
- **Depreciation & Asset Useful Lifespans**: {a2.get('part13_depreciation', {}).get('1_useful_lifespan_extension')} | Method: {a2.get('part13_depreciation', {}).get('2_depreciation_method_change')}
- **CapEx vs D&A Relationship**: {a2.get('part13_depreciation', {}).get('3_capex_vs_da_relationship')}
- **SG&A Growth vs Top-Line Revenue**: {a2.get('part14_sga_anomalies', {}).get('1_sga_growth_vs_revenue')}
- **Stock-Based Compensation & Overhead**: {a2.get('part14_sga_anomalies', {}).get('4_stock_based_compensation')} | Miscellany: {a2.get('part14_sga_anomalies', {}).get('5_unexplained_miscellaneous_spikes')}
- **Goodwill & Intangible Assets Load**: {a2.get('part16_balance_sheet', {}).get('1_goodwill_percentage')}
- **Auditor Independence & Pedigree**: {a2.get('part16_balance_sheet', {}).get('3_auditor_management_turnover')}

---

### ⚖️ Agent 3: Balance Sheet, Solvency & Capital Health
- **Balance Sheet Leverage**: Total Debt: ₹{a3.get('audit_metrics', {}).get('Total Debt')}, Net Debt: ₹{a3.get('audit_metrics', {}).get('Net Debt')} (Net Debt/Equity: {a3.get('audit_metrics', {}).get('Net Debt / Equity')}, Total Debt/Equity: {a3.get('audit_metrics', {}).get('Total Debt / Equity')})
- **Liquid Cash Buffer**: ₹{a3.get('audit_metrics', {}).get('Cash & Equivalents')} in cash and short-term equivalents
- **Debt Service Headroom**: Normalized Interest Coverage: **{a3.get('audit_metrics', {}).get('Normalized Interest Coverage')}**
- **Working Capital Cycle (Cash Conversion Cycle)**: **{a3.get('audit_metrics', {}).get('Cash Conversion Cycle')}** ({a3.get('part11_working_capital', {}).get('1_cash_conversion_cycle')})
- **Return on Invested Capital (ROIC)**: **{a3.get('part9_cash_flow_roic', {}).get('5_roic_vs_wacc')}**
- **Free Cash Flow & Margin**: FCF Margin: {a3.get('audit_metrics', {}).get('FCF Margin')} ({a3.get('part9_cash_flow_roic', {}).get('2_fcf_trajectory')})
- **FCF Dividend Sustainability**: **{a3.get('part12_capital_allocation', {}).get('4_dividend_fcf_sustainability')}** (Coverage: {a3.get('audit_metrics', {}).get('FCF Dividend Coverage')})

---

### 🏛️ Agent 4: Corporate Governance & Master RPT Audit
- **Promoter Alignment & Encumbrance**: {a4.get('section1_promoter_integrity', {}).get('2_promoter_pledge_percentage')}
- **Executive Remuneration vs PAT**: {a4.get('section2_executive_remuneration', {}).get('1_ceo_remuneration_vs_pat')} (CEO-to-Median-Employee Ratio: {a4.get('audit_metrics', {}).get('CEO / Median Pay')})
- **Incentive Hurdle Alignment**: {a4.get('section2_executive_remuneration', {}).get('3_incentive_hurdle_alignment')}
- **Politically Exposed Persons (PEP) & Rent-Seeking**: {a4.get('section3_pep_rent_seeking', {}).get('1_pep_presence')} | Dependency: {a4.get('section3_pep_rent_seeking', {}).get('2_government_concession_dependency')}
- **Master RPT Pricing & Arm's Length Validation**: {a4.get('section4_master_rpt', {}).get('pricing_validation', {}).get('pricing_arms_length')}
- **Capital Siphoning & Corporate Guarantees**: {a4.get('section4_master_rpt', {}).get('capital_siphoning', {}).get('unsecured_loans_to_insiders')} | Guarantees: {a4.get('section4_master_rpt', {}).get('capital_siphoning', {}).get('corporate_guarantees')}
- **RPT Revenue & Disclosure Governance**: RPT % of Revenue: {a4.get('audit_metrics', {}).get('RPT % of Revenue')} | Audit Committee Sign-Off: {a4.get('section4_master_rpt', {}).get('governance_disclosures', {}).get('audit_committee_preapproval')}

---

### 📈 Agent 5: Industry Operational KPIs ({a5.get('activated_checklist_section')})
"""
    for k, v in a5.get("kpi_results", {}).items():
        full_report_md += f"- **{k}**: {v}\n"

    full_report_md += f"""
---

### 🎯 Agent 6: CIO Valuation, Asset Floors & Reverse DCF
- **Management Walk-the-Talk Audit**:
  - Target 1: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_1', {}).get('target', 'Core Operational Target')} -> **{a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_1', {}).get('verdict')}**
  - Target 2: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_2', {}).get('target', 'Capital Allocation Target')} -> **{a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_2', {}).get('verdict')}**
  - Target 3: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_3', {}).get('target', 'Operating Cash Flow Conversion')} -> **{a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_3', {}).get('verdict')}**
- **Independent Asset & Yield Valuation Floors (Non-DCF / Non-Relative)**:
  - **Tangible Book Value (TBV)**: {a6.get('section2_asset_yield_valuation', {}).get('1_tangible_book_value_per_share')}
  - **Graham Net-Net (NCAV)**: {a6.get('section2_asset_yield_valuation', {}).get('2_graham_net_net_ncav')}
  - **Stressed Liquidation Value**: {a6.get('section2_asset_yield_valuation', {}).get('3_liquidation_value_stressed')}
  - **Owner Earnings Yield**: {a6.get('section2_asset_yield_valuation', {}).get('4_owner_earnings_yield')}
  - **Earnings Power Value (EPV, 0% Growth)**: {a6.get('section2_asset_yield_valuation', {}).get('5_earnings_power_value_epv')}
  - **Dividend Yield & Organic Coverage**: {a6.get('section2_asset_yield_valuation', {}).get('6_dividend_yield_and_fcf_payout')}
- **Reverse DCF Hurdle Test (WACC 11.5%, Terminal Growth 5.5%)**:
  - Implied 10-Year FCF CAGR: **{dossier.get('implied_growth_pct')}%** ({a6.get('section3_reverse_dcf', {}).get('2_reality_check_vs_guidance')})
- **3-Scenario Valuation Matrix**:
  - **Bear Case**: Target {a6.get('section4_scenario_matrix', {}).get('bear_case', {}).get('fair_target_price')} ({a6.get('section4_scenario_matrix', {}).get('bear_case', {}).get('expected_return')}) | Growth: {a6.get('section4_scenario_matrix', {}).get('bear_case', {}).get('growth_assumed')}
  - **Base Case**: Target {a6.get('section4_scenario_matrix', {}).get('base_case', {}).get('fair_target_price')} ({a6.get('section4_scenario_matrix', {}).get('base_case', {}).get('expected_return')}) | Growth: {a6.get('section4_scenario_matrix', {}).get('base_case', {}).get('growth_assumed')}
  - **Bull Case**: Target {a6.get('section4_scenario_matrix', {}).get('bull_case', {}).get('fair_target_price')} ({a6.get('section4_scenario_matrix', {}).get('bull_case', {}).get('expected_return')}) | Growth: {a6.get('section4_scenario_matrix', {}).get('bull_case', {}).get('growth_assumed')}
- **Thesis Invalidation Triggers**:
"""
    for trig in a6.get("invalidation_triggers", []):
        full_report_md += f"  - {trig}\n"

    full_report_md += f"""
---
### 🏛️ Final Institutional Verdict: **{rating}**
"""

    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown(full_report_md, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Direct PDF Download Button
    pdf_data = generate_pdf(full_report_md, ticker)
    st.download_button(
        label="📄 Download Full Institutional PDF Dossier",
        data=pdf_data,
        file_name=f"{ticker}_Institutional_Audit.pdf",
        mime="application/pdf"
    )

    # Accordion Tabs for All 7 Agent Audits (Expanded by default)
    st.subheader("🔬 Deep-Dive Multi-Agent Audit Accordions (Expanded by Default)")

    # Agent 0: Classifier
    with st.expander("🏷️ Agent 0: Industry Taxonomy & Routing Profile", expanded=True):
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
    with st.expander("⚖️ Agent 3: Balance Sheet, Solvency & Capital Allocation Analyst", expanded=True):
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
    with st.expander("🏛️ Agent 4: Governance, RPT & Executive Remuneration Auditor", expanded=True):
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
    with st.expander("📈 Agent 5: Industry KPI Specialist", expanded=True):
        st.caption("System Prompt dynamically loaded from: `agent5_industry_kpi.txt`")
        st.markdown(f"**Activated Sector Checklist**: `{a5.get('activated_checklist_section')}`")
        st.markdown(f"**Summary**: {a5.get('summary')}")

        kpi_items = list(a5.get("kpi_results", {}).items())
        kpi_cols = st.columns(2)
        for idx, (k, v) in enumerate(kpi_items):
            kpi_cols[idx % 2].metric(k, str(v))

    # Agent 6: CIO & Valuation Specialist
    with st.expander("🎯 Agent 6: Chief Investment Officer & Valuation Specialist", expanded=True):
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

    # Download Dossier Buttons (Markdown and JSON)
    st.markdown("---")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.download_button(
            label="📥 Download Full Research Report (.md)",
            data=full_report_md,
            file_name=f"{symbol}_institutional_dossier.md",
            mime="text/markdown",
            use_container_width=True
        )
    with d_col2:
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
            label="📥 Download Structured Dossier (.json)",
            data=export_json,
            file_name=f"{symbol}_institutional_dossier.json",
            mime="application/json",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
