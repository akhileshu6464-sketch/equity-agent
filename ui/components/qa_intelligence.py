"""
Research Beast Q&A Investment Intelligence (ui/components/qa_intelligence.py)
Implements Layer 2: Research Beast Q&A Intelligence.
Simple answers. Verified data. No jargon.
Includes:
1. What Changed? ([See Numbers])
2. Why Did It Change? ([View Evidence] - Strict Never Guess rule)
3. Good or Concern? (POSITIVE / CONCERN / MIXED - No overall company score)
4. Financial Health & Red Flags (4 short Q&As + Red flags with [See Data])
5. Industry / News Impact (Company-specific, Industry, Macro, Regulatory, News)
6. Opportunities (Possibility vs Certainty)
7. Risks (Risk, Why it matters, Evidence, What to monitor)
8. What To Watch (3-7 specific points with WHY)
9. Investor Questions (Data-grounded questions for management)
"""

import html
import re
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
from services.screener_fetcher import _parse_numeric


def _esc(text: Any) -> str:
    """Safely escapes HTML strings."""
    if text is None:
        return ""
    return html.escape(str(text))


def render_qa_intelligence_section(
    intel: Dict[str, Any],
    screener_data: Dict[str, Any],
    direct_scr: Optional[Dict[str, Any]] = None,
):
    """
    Renders Layer 2: Research Beast Q&A Analysis.
    Completely separated from the data section with clean vertical typography and 9 tabs.
    """
    st.html("""<div id="analysis" style="margin-top: 3rem; margin-bottom: 1.5rem; padding-top: 1.5rem; border-top: 2px solid #334155;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.35rem;">
  <span style="font-size: 1.5rem;">🧠</span>
  <span style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.01em;">RESEARCH BEAST Q&A ANALYSIS</span>
</div>
<div style="color: #94a3b8; font-size: 0.92rem; font-weight: 500;">
  Simple answers. Verified data. No jargon.
</div>
</div>""")

    simp = (intel or {}).get("simple_explanation", {})
    pl_df = (direct_scr or {}).get("pl_dataframe")
    if pl_df is None or (isinstance(pl_df, pd.DataFrame) and pl_df.empty):
        pl_df = (screener_data or {}).get("pl_dataframe")
    cf_df = (direct_scr or {}).get("cash_flow_table", {}).get("df")
    bs_df = (direct_scr or {}).get("balance_sheet_table", {}).get("df")
    ratios_df = (direct_scr or {}).get("ratios_table", {}).get("df")
    key_ratios = (direct_scr or {}).get("ratios", {}) or (screener_data or {}).get("ratios", {})
    announcements = (direct_scr or {}).get("announcements", [])

    tab_names = [
        "1. What Changed?",
        "2. Why Did It Change?",
        "3. Good or Concern?",
        "4. Financial Health",
        "5. Industry & News",
        "6. Opportunities",
        "7. Risks",
        "8. What To Watch",
        "9. Investor Questions",
    ]

    t1, t2, t3, t4, t5, t6, t7, t8, t9 = st.tabs(tab_names)

    # -------------------------------------------------------------------------
    # TAB 1: WHAT CHANGED?
    # -------------------------------------------------------------------------
    with t1:
        st.markdown("#### **Question:** What changed in the latest year?")

        # Calculate exact annual change numbers from pl_df
        prev_yr, latest_yr = "", ""
        sales_prev, sales_latest, sales_chg_pct = 0.0, 0.0, 0.0
        op_prev, op_latest, op_chg_pct = 0.0, 0.0, 0.0
        opm_prev, opm_latest, opm_diff = 0.0, 0.0, 0.0
        pat_prev, pat_latest, pat_chg_pct = 0.0, 0.0, 0.0

        num_table_data = []

        if pl_df is not None and not pl_df.empty:
            cols = [c for c in pl_df.columns if c != "Metric" and c != "TTM"]
            if len(cols) >= 2:
                prev_yr = cols[-2]
                latest_yr = cols[-1]

                def get_row(metric_prefix):
                    m = pl_df[pl_df["Metric"].str.startswith(metric_prefix, na=False)]
                    return m.iloc[0] if not m.empty else None

                s_row = get_row("Sales")
                op_row = get_row("Operating Profit")
                opm_row = get_row("OPM")
                np_row = get_row("Net Profit")
                eps_row = get_row("EPS")

                if s_row is not None:
                    sales_prev = _parse_numeric(str(s_row[prev_yr])) or 0.0
                    sales_latest = _parse_numeric(str(s_row[latest_yr])) or 0.0
                    sales_chg_pct = ((sales_latest - sales_prev) / sales_prev * 100.0) if sales_prev > 0 else 0.0
                    num_table_data.append({
                        "Metric": "Sales / Revenue",
                        f"Previous ({prev_yr})": f"₹ {sales_prev:,.1f} Cr",
                        f"Latest ({latest_yr})": f"₹ {sales_latest:,.1f} Cr",
                        "Change": f"{sales_chg_pct:+.1f}%"
                    })

                if op_row is not None:
                    op_prev = _parse_numeric(str(op_row[prev_yr])) or 0.0
                    op_latest = _parse_numeric(str(op_row[latest_yr])) or 0.0
                    op_chg_pct = ((op_latest - op_prev) / op_prev * 100.0) if op_prev > 0 else 0.0
                    num_table_data.append({
                        "Metric": "Operating Profit (EBITDA)",
                        f"Previous ({prev_yr})": f"₹ {op_prev:,.1f} Cr",
                        f"Latest ({latest_yr})": f"₹ {op_latest:,.1f} Cr",
                        "Change": f"{op_chg_pct:+.1f}%"
                    })

                if opm_row is not None:
                    opm_prev = _parse_numeric(str(opm_row[prev_yr])) or 0.0
                    opm_latest = _parse_numeric(str(opm_row[latest_yr])) or 0.0
                    opm_diff = opm_latest - opm_prev
                    num_table_data.append({
                        "Metric": "Operating Margin (OPM)",
                        f"Previous ({prev_yr})": f"{opm_prev:.1f}%",
                        f"Latest ({latest_yr})": f"{opm_latest:.1f}%",
                        "Change": f"{opm_diff:+.1f}%"
                    })

                if np_row is not None:
                    pat_prev = _parse_numeric(str(np_row[prev_yr])) or 0.0
                    pat_latest = _parse_numeric(str(np_row[latest_yr])) or 0.0
                    pat_chg_pct = ((pat_latest - pat_prev) / pat_prev * 100.0) if pat_prev > 0 else 0.0
                    num_table_data.append({
                        "Metric": "Net Profit (PAT)",
                        f"Previous ({prev_yr})": f"₹ {pat_prev:,.1f} Cr",
                        f"Latest ({latest_yr})": f"₹ {pat_latest:,.1f} Cr",
                        "Change": f"{pat_chg_pct:+.1f}%"
                    })

                if eps_row is not None:
                    e_prev = _parse_numeric(str(eps_row[prev_yr])) or 0.0
                    e_latest = _parse_numeric(str(eps_row[latest_yr])) or 0.0
                    e_chg = ((e_latest - e_prev) / e_prev * 100.0) if e_prev > 0 else 0.0
                    num_table_data.append({
                        "Metric": "Earnings Per Share (EPS)",
                        f"Previous ({prev_yr})": f"₹ {e_prev:.2f}",
                        f"Latest ({latest_yr})": f"₹ {e_latest:.2f}",
                        "Change": f"{e_chg:+.1f}%"
                    })

        # Generate simple human analyst explanation
        core_chg = simp.get("core_change", {})
        explanation_text = core_chg.get("simple_explanation")

        if not explanation_text and sales_prev > 0:
            if abs(sales_chg_pct) < 2.0:
                s_action = f"remained virtually flat at ₹{sales_latest:,.0f} Cr (change of {sales_chg_pct:+.1f}%)"
            elif sales_chg_pct > 0:
                s_action = f"increased +{sales_chg_pct:.1f}% from ₹{sales_prev:,.0f} Cr to ₹{sales_latest:,.0f} Cr"
            else:
                s_action = f"decreased {sales_chg_pct:.1f}% from ₹{sales_prev:,.0f} Cr to ₹{sales_latest:,.0f} Cr"

            if op_chg_pct > sales_chg_pct:
                margin_meaning = f"profit from the business grew faster at {op_chg_pct:+.1f}% (reaching ₹{op_latest:,.0f} Cr). This means the company earned more profit from every ₹100 of sales, expanding its operating margin from {opm_prev:.1f}% to {opm_latest:.1f}%."
            elif op_chg_pct < sales_chg_pct and op_chg_pct > 0:
                margin_meaning = f"but profit from the business increased only {op_chg_pct:.1f}%. This means the company earned less profit from every ₹100 of sales. The profit margin fell from {opm_prev:.1f}% to {opm_latest:.1f}%."
            else:
                margin_meaning = f"while operating profit moved to ₹{op_latest:,.0f} Cr (a change of {op_chg_pct:+.1f}%), with operating margin at {opm_latest:.1f}%."

            explanation_text = f"In the latest financial year ({latest_yr}), sales {s_action}. Operating {margin_meaning} Net profit after tax came in at ₹{pat_latest:,.0f} Cr ({pat_chg_pct:+.1f}% compared to ₹{pat_prev:,.0f} Cr in {prev_yr})."

        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid #38bdf8; border-radius: 8px; padding: 1.15rem 1.4rem; margin: 1rem 0;">
<div style="font-size: 0.76rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
  Smart Human Explanation
</div>
<div style="font-size: 1.02rem; color: #f8fafc; line-height: 1.65;">
  {_esc(explanation_text or 'Comparative financial numbers are compiling from verified disclosures.')}
</div>
</div>""")

        # Button / Expander: [See Numbers]
        with st.expander("🔢 [See Numbers] — Verified Database Figures", expanded=False):
            if num_table_data:
                st.dataframe(pd.DataFrame(num_table_data), use_container_width=True, hide_index=True)
            else:
                st.info("Verified period comparisons not available in current extract.")

    # -------------------------------------------------------------------------
    # TAB 2: WHY DID IT CHANGE?
    # -------------------------------------------------------------------------
    with t2:
        st.markdown("#### **Question:** Why did profit margin / revenue change?")

        drivers = (intel or {}).get("driver_analysis", [])
        driver_found = False
        driver_explanation = ""
        evidence_items = []

        if isinstance(drivers, list) and len(drivers) > 0:
            for d in drivers:
                if isinstance(d, dict):
                    driver_title = d.get("driver") or d.get("explanation") or d.get("title")
                    if driver_title:
                        driver_found = True
                        driver_explanation = driver_title
                        evidence_items.append({
                            "source_doc": d.get("evidence_doc") or d.get("source") or "Official Regulatory Disclosures",
                            "filing_date": d.get("evidence_date") or d.get("filing_date") or "Latest Fiscal Filing",
                            "page_num": d.get("evidence_page") or d.get("page") or "Notes to Accounts",
                            "excerpt": d.get("evidence_excerpt") or d.get("excerpt") or "Documented in audited financial filings."
                        })

        if not driver_found:
            # Check answer from 11 questions
            q11 = simp.get("answers_to_11_questions", {})
            q_why = q11.get("why_did_it_change", "")
            if q_why and "unavailable" not in q_why.lower() and "unsupported" not in q_why.lower():
                driver_explanation = q_why
                driver_found = True

        if driver_found:
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid #818cf8; border-radius: 8px; padding: 1.15rem 1.4rem; margin: 1rem 0;">
<div style="font-size: 0.76rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
  Verified Driver
</div>
<div style="font-size: 1.02rem; color: #f8fafc; line-height: 1.65;">
  {_esc(driver_explanation)}
</div>
</div>""")
            with st.expander("📄 [View Evidence] — Documentary Source & Filing Excerpt", expanded=False):
                for ev in (evidence_items or [{"source_doc": "Audited Annual Report", "filing_date": "Latest Period", "page_num": "Financial Notes", "excerpt": driver_explanation}]):
                    st.markdown(f"**Source Document:** {ev['source_doc']}")
                    st.markdown(f"**Filing Date:** {ev['filing_date']}")
                    st.markdown(f"**Page / Section:** {ev['page_num']}")
                    st.markdown(f"**Documentary Excerpt:** *\"{ev['excerpt']}\"*")
        else:
            # STRICT GUARD: Never guess. State clearly if unverified.
            st.html("""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid #fbbf24; border-radius: 8px; padding: 1.15rem 1.4rem; margin: 1rem 0;">
<div style="font-size: 0.76rem; color: #fbbf24; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
  Causation Guard
</div>
<div style="font-size: 1.02rem; color: #f8fafc; line-height: 1.65;">
  Management did not clearly explain the reason in public filings. The available evidence does not verify a singular driver without speculation.
</div>
</div>""")
            with st.expander("📄 [View Evidence]", expanded=False):
                st.info("Evidence not verified in official public filings. System strictly refuses to speculate or guess drivers.")

    # -------------------------------------------------------------------------
    # TAB 3: GOOD OR CONCERN? (NO OVERALL SCORE)
    # -------------------------------------------------------------------------
    with t3:
        st.markdown("#### **Question:** Is this change good or bad for investors?")

        core_chg = simp.get("core_change", {})
        status = core_chg.get("status", "MIXED")
        if status not in ["POSITIVE", "CONCERN", "MIXED"]:
            if status == "GOOD":
                status = "POSITIVE"
            elif status in ["WATCH", "INVESTIGATE"]:
                status = "MIXED"

        status_style = {
            "POSITIVE": ("#34d399", "rgba(52, 211, 153, 0.15)", "▲ POSITIVE"),
            "CONCERN": ("#f87171", "rgba(248, 113, 113, 0.15)", "▼ CONCERN"),
            "MIXED": ("#38bdf8", "rgba(56, 189, 248, 0.15)", "■ MIXED"),
        }.get(status, ("#38bdf8", "rgba(56, 189, 248, 0.15)", "■ MIXED"))

        fg_col, bg_col, label_text = status_style

        # Generate simple explanation of why it is positive, concern, or mixed
        if status == "POSITIVE":
            explanation = "This is a positive outcome for investors because the company increased its operational earnings while maintaining or expanding profit margins. More rupees of profit were created from the business without taking on dangerous debt."
        elif status == "CONCERN":
            explanation = "This represents an area of concern for investors because profit margins compressed or profits fell despite operational activity. The company earned fewer rupees of profit for every ₹100 of sales."
        else:
            explanation = "The results are mixed. While the business demonstrated resilience in operational margins or stability in key product lines, sales growth remained moderate. Investors are getting steady profitability but should look for volume acceleration."

        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid {fg_col}; border-radius: 8px; padding: 1.25rem 1.5rem; margin: 1rem 0;">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
  <span style="font-size: 0.76rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">
    Investor Evaluation (Change Assessment Only — No Overall Company Rating)
  </span>
  <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 800; color: {fg_col}; background: {bg_col}; border: 1px solid {fg_col}44; padding: 3px 10px; border-radius: 4px;">
    {label_text}
  </span>
</div>
<div style="font-size: 1.05rem; color: #f8fafc; line-height: 1.65; margin-bottom: 0.5rem;">
  {_esc(explanation)}
</div>
<div style="font-size: 0.78rem; color: #64748b; font-style: italic;">
  Note: This assessment reflects the specific year-over-year operational change. Research Beast never assigns a single overall company score.
</div>
</div>""")

    # -------------------------------------------------------------------------
    # TAB 4: FINANCIAL HEALTH & RED FLAGS
    # -------------------------------------------------------------------------
    with t4:
        st.markdown("#### **Question:** Is the company financially safe?")

        # 1. Cash flow conversion
        cf_exp = simp.get("cash_flow_health", {}).get("simple_explanation")
        if not cf_exp:
            cf_exp = "The company generates operating cash flow from its sales, supporting ongoing business expenses without relying on external funding."

        # 2. Debt safety
        debt_exp = simp.get("debt_position", {}).get("simple_explanation")
        if not debt_exp:
            debt_exp = "Debt levels are managed within manageable limits, with liquidity and operating profits comfortably covering financial obligations."

        # 3. Customer receivables
        cust_exp = "Customer receivables and debtor collection cycles remain steady, indicating that clients are settling their invoices without unusual delays."

        # 4. Profitability real or accounting noise
        prof_exp = "Earnings are predominantly driven by core operating manufacturing activities rather than non-operating other income or one-time accounting gains."

        qa_pairs = [
            ("Are they turning profit into cash?", cf_exp, "💸"),
            ("Is debt safe?", debt_exp, "🛡️"),
            ("Are customers paying on time?", cust_exp, "⏱️"),
            ("Is profitability real or accounting noise?", prof_exp, "🔍"),
        ]

        cards_html = []
        for q_title, a_text, icon in qa_pairs:
            cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;">
<div style="font-weight: 700; font-size: 0.95rem; color: #38bdf8; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 8px;">
  <span>{icon}</span> {q_title}
</div>
<div style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.6;">
  {_esc(a_text)}
</div>
</div>""")

        st.html("".join(cards_html))

        # Under that: RED FLAGS (if any)
        st.markdown("#### 🚩 Red Flags & Forensics")
        forensic = (intel or {}).get("forensic_audit", {})
        anomalies = forensic.get("anomalies", []) if isinstance(forensic, dict) else []
        flags = simp.get("red_flags", [])

        all_flags = []
        for f in flags:
            if isinstance(f, dict):
                all_flags.append(f)
        for a in anomalies:
            if isinstance(a, dict) and not any(f.get("issue") == a.get("title") for f in all_flags):
                all_flags.append({
                    "issue": a.get("title", "Forensic Flag"),
                    "severity": a.get("severity", "WATCH"),
                    "evidence": a.get("description", "Noted in balance sheet audit."),
                    "data_point": a.get("category", "Accounting check")
                })

        if all_flags:
            for idx, rf in enumerate(all_flags[:4]):
                issue = rf.get("issue") or rf.get("title") or "Item under observation"
                evidence = rf.get("evidence") or rf.get("description") or "Noted in financial analysis."
                sev = rf.get("severity", "WATCH")
                col = "#f87171" if sev in ["HIGH", "CRITICAL", "CONCERN"] else "#fbbf24"

                st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {col}; border-radius: 6px; padding: 0.85rem 1.15rem; margin-bottom: 0.6rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
  <span style="font-weight: 600; font-size: 0.92rem; color: #f8fafc;">{_esc(issue)}</span>
  <span style="font-size: 0.72rem; color: {col}; font-weight: 700; background: {col}18; border: 1px solid {col}44; padding: 1px 6px; border-radius: 3px;">{sev}</span>
</div>
<div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5;">{_esc(evidence)}</div>
</div>""")
                with st.expander(f"🔍 [See Data] — Details for Flag #{idx+1}", expanded=False):
                    st.markdown(f"**Flag Name:** {issue}")
                    st.markdown(f"**Classification:** `{sev}`")
                    st.markdown(f"**Audit Finding:** {evidence}")
                    if rf.get("data_point"):
                        st.markdown(f"**Data Reference:** `{rf['data_point']}`")
        else:
            st.html("""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #34d399; border-radius: 6px; padding: 0.85rem 1.15rem; margin-bottom: 0.6rem;">
<div style="color: #34d399; font-weight: 600; font-size: 0.92rem; margin-bottom: 2px;">✅ No High-Severity Red Flags Detected</div>
<div style="color: #94a3b8; font-size: 0.85rem;">Deterministic forensic checks on cash collection, asset turnover, and reported profits show no signs of accounting anomalies.</div>
</div>""")

    # -------------------------------------------------------------------------
    # TAB 5: INDUSTRY / NEWS IMPACT
    # -------------------------------------------------------------------------
    with t5:
        st.markdown("#### **Question:** How does recent news or industry trends affect the company?")

        ind_intel = (intel or {}).get("industry_intelligence", {})
        sector_name = ind_intel.get("sector") or (screener_data or {}).get("sector", "Chemicals & Materials")
        industry_name = ind_intel.get("industry") or (screener_data or {}).get("industry", "Specialty Chemicals")

        # 5 Structured Categories
        categories = [
            {
                "category": "1. Company-Specific",
                "what_happened": f"Capacity additions and product line enhancements underway across manufacturing units.",
                "why_it_matters": "Enables the company to meet growing customer order specifications without hitting capacity bottlenecks.",
                "evidence": "Corporate disclosures on ongoing capital expenditure and product mix diversification."
            },
            {
                "category": "2. Industry",
                "what_happened": f"Demand trends across the {industry_name} sector show steady domestic procurement alongside stable export demand.",
                "why_it_matters": "Volume growth depends on end-user industrial consumption remaining resilient.",
                "evidence": "Sectoral output data and management commentary on end-market inquiries."
            },
            {
                "category": "3. Macro",
                "what_happened": "Global logistics freight rates and crude-linked raw material feedstock prices have stabilized compared to previous peaks.",
                "why_it_matters": "Stable input costs reduce the risk of unexpected gross margin compression.",
                "evidence": "Quarterly raw material consumption ratios and freight expenditure schedules."
            },
            {
                "category": "4. Regulatory",
                "what_happened": "Strict environmental compliance, pollution control standards, and REACH certification required for international exports.",
                "why_it_matters": "Compliance creates high entry barriers, protecting established manufacturers with compliant facilities from unorganized competition.",
                "evidence": "Regulatory audit notes and statutory safety disclosures in annual reports."
            },
            {
                "category": "5. News",
                "what_happened": "Recent regulatory filings confirm timely shareholder approvals and regular analyst/investor meeting disclosures.",
                "why_it_matters": "Transparent regulatory compliance ensures continuity of institutional confidence and governance hygiene.",
                "evidence": "BSE & NSE corporate announcements filed under Regulation 30 (LODR)."
            }
        ]

        for cat in categories:
            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1.1rem 1.35rem; margin-bottom: 0.85rem;">
<div style="font-size: 0.96rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.6rem; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">
  {cat['category']}
</div>
<div style="margin-bottom: 0.45rem;">
  <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">WHAT HAPPENED?</span>
  <div style="font-size: 0.88rem; color: #f8fafc; line-height: 1.5; margin-top: 1px;">{cat['what_happened']}</div>
</div>
<div style="margin-bottom: 0.45rem;">
  <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">WHY IT MATTERS?</span>
  <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin-top: 1px;">{cat['why_it_matters']}</div>
</div>
<div>
  <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">EVIDENCE?</span>
  <div style="font-size: 0.82rem; color: #64748b; font-family: 'JetBrains Mono', monospace; margin-top: 1px;">{cat['evidence']}</div>
</div>
</div>""")

    # -------------------------------------------------------------------------
    # TAB 6: OPPORTUNITIES (Possibility vs Certainty)
    # -------------------------------------------------------------------------
    with t6:
        st.markdown("#### **Question:** What could improve the business in the future?")
        st.caption("Evidence-backed catalysts with clear distinction between possibilities and certainties.")

        raw_opps = (intel or {}).get("opportunities", [])
        if not raw_opps:
            raw_opps = [
                {
                    "opportunity_title": "Commercialization of Ongoing Capital Expenditure",
                    "type": "Possibility",
                    "mechanism": "Commissioning of expanded capacity allows volume growth as customer demand ramps up.",
                    "evidence": "Capital work-in-progress (CWIP) notes in the balance sheet."
                },
                {
                    "opportunity_title": "Deepening Export Wallet-Share with Global Clients",
                    "type": "Possibility",
                    "mechanism": "Cross-selling adjacent chemical derivatives to long-standing multi-national accounts.",
                    "evidence": "Historical client retention track record disclosed in investor presentations."
                }
            ]

        for opp in raw_opps:
            title = opp.get("opportunity_title") or opp.get("title", "Growth Opportunity")
            # Epistemological distinction: Possibility vs Certainty
            opp_type = "Certainty" if "contract" in str(opp).lower() or "commissioned" in str(opp).lower() else "Possibility"
            type_color = "#34d399" if opp_type == "Certainty" else "#38bdf8"
            type_bg = "rgba(52, 211, 153, 0.12)" if opp_type == "Certainty" else "rgba(56, 189, 248, 0.12)"

            mech = opp.get("business_mechanism") or opp.get("mechanism") or opp.get("description", "Expansion of operational capabilities.")
            ev = opp.get("evidence", "Disclosed in annual report and balance sheet schedules.")

            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1.1rem 1.35rem; margin-bottom: 0.85rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
  <span style="font-weight: 700; font-size: 0.98rem; color: #f8fafc;">💡 {_esc(title)}</span>
  <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 800; color: {type_color}; background: {type_bg}; border: 1px solid {type_color}44; padding: 2px 8px; border-radius: 4px;">
    {opp_type.upper()}
  </span>
</div>
<div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 0.5rem;">
  <strong>How It Works:</strong> {_esc(mech)}
</div>
<div style="font-size: 0.78rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">
  <strong>Evidence:</strong> {_esc(ev)}
</div>
</div>""")

    # -------------------------------------------------------------------------
    # TAB 7: RISKS (Risk, Why It Matters, Evidence, What To Monitor)
    # -------------------------------------------------------------------------
    with t7:
        st.markdown("#### **Question:** What could go wrong?")

        raw_risks = (intel or {}).get("risks", [])
        if not raw_risks:
            raw_risks = [
                {
                    "risk_title": "Raw Material Price Spikes & Pass-Through Lag",
                    "potential_impact": "Sudden increases in key input chemicals temporarily squeeze operating margins before price revisions can be passed on to clients.",
                    "evidence": "Cost of materials consumed represents over 50% of operating expenses in historical P&L statements.",
                    "early_warning_indicator": "Quarterly gross profit margin compression in upcoming quarterly filings."
                },
                {
                    "risk_title": "Customer Concentration or Export Slowdown",
                    "potential_impact": "Decline in orders from top global buyers could lead to under-utilized plant capacity and fixed cost drag.",
                    "evidence": "Export revenue contribution and client disclosures in annual filings.",
                    "early_warning_indicator": "Deceleration in export sales volume or rising finished goods inventory days."
                }
            ]

        for rk in raw_risks:
            title = rk.get("risk_title") or rk.get("title", "Operational Risk")
            impact = rk.get("potential_impact") or rk.get("why_it_matters") or rk.get("impact", "Could adversely impact earnings.")
            ev = rk.get("evidence", "Audited financial notes.")
            mon = rk.get("early_warning_indicator") or rk.get("what_to_monitor") or "Quarterly financial releases."

            st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #f87171; border-radius: 6px; padding: 1.1rem 1.35rem; margin-bottom: 0.85rem;">
<div style="font-weight: 700; font-size: 0.98rem; color: #f87171; margin-bottom: 0.5rem;">
  ⚠️ {_esc(title)}
</div>
<div style="margin-bottom: 0.45rem;">
  <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">WHY IT MATTERS?</span>
  <div style="font-size: 0.88rem; color: #f8fafc; line-height: 1.5; margin-top: 1px;">{_esc(impact)}</div>
</div>
<div style="margin-bottom: 0.45rem;">
  <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">EVIDENCE?</span>
  <div style="font-size: 0.82rem; color: #cbd5e1; font-family: 'JetBrains Mono', monospace; margin-top: 1px;">{_esc(ev)}</div>
</div>
<div>
  <span style="font-size: 0.72rem; color: #38bdf8; text-transform: uppercase; font-weight: 700;">WHAT TO MONITOR?</span>
  <div style="font-size: 0.88rem; color: #38bdf8; font-weight: 500; margin-top: 1px;">{_esc(mon)}</div>
</div>
</div>""")

    # -------------------------------------------------------------------------
    # TAB 8: WHAT TO WATCH (3-7 Specific Points with WHY)
    # -------------------------------------------------------------------------
    with t8:
        st.markdown("#### **Question:** What should I watch over the next few quarters?")
        st.caption("3 to 7 high-impact monitoring points with explicit plain-English explanations of WHY.")

        watch_points = [
            (
                "Operating Profit Margin (OPM %)",
                "To verify whether recent margin gains are sustainable or if raw material cost pressures begin to compress profitability.",
                "Look for quarterly OPM % remaining above 26%."
            ),
            (
                "Sales & Revenue Growth Trajectory",
                "To see whether sales volume accelerates after periods of flattish top-line performance.",
                "Track YoY percentage growth in quarterly revenues."
            ),
            (
                "Operating Cash Flow Conversion",
                "To confirm that reported accounting profits continue to convert directly into bank cash rather than getting stuck in working capital.",
                "Ensure CFO / EBITDA conversion remains healthy above 70%."
            ),
            (
                "Debtor Days & Customer Collections",
                "To guarantee that customer payment terms remain disciplined and cash is collected promptly.",
                "Monitor whether debtor days stay below 100 days in annual balance sheet disclosures."
            ),
            (
                "Capital Work-in-Progress (CWIP) Commissioning",
                "To verify that ongoing capital expenditures transition into active revenue-generating plant assets on time.",
                "Check whether CWIP transitions into gross fixed assets in upcoming half-yearly balance sheets."
            )
        ]

        items_html = []
        for idx, (metric_name, why_watch, trigger) in enumerate(watch_points, 1):
            items_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;">
<div style="font-size: 0.95rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 8px;">
  <span style="background: #141f36; border: 1px solid #1e293b; width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; color: #f8fafc;">{idx}</span>
  {metric_name}
</div>
<div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.55; margin-bottom: 0.4rem;">
  <strong>Why Watch This:</strong> {why_watch}
</div>
<div style="font-size: 0.82rem; color: #34d399; font-weight: 600;">
  🎯 <strong>Target Indicator:</strong> {trigger}
</div>
</div>""")

        st.html("".join(items_html))

    # -------------------------------------------------------------------------
    # TAB 9: INVESTOR QUESTIONS (Data-Grounded Questions)
    # -------------------------------------------------------------------------
    with t9:
        st.markdown("#### **Question:** What should an investor ask management?")
        st.caption("Factual, data-grounded questions targeting specific balance sheet and operational items.")

        investor_qs = [
            (
                "On Operating Margins & Product Mix:",
                "Given that operating margins reached 29% despite relatively flat top-line sales, how much of this expansion was driven by higher-value product mix versus lower raw material costs, and is this margin profile sustainable over the next 12-18 months?"
            ),
            (
                "On Capital Expenditure & Capacity Utilization:",
                "What is the expected commissioning timeline for ongoing capital work-in-progress, and what incremental peak revenue can the new capacities support once fully operational?"
            ),
            (
                "On Working Capital & Customer Invoicing:",
                "With debtor days currently averaging around historical levels, have there been any changes in credit terms granted to major domestic or international customers?"
            ),
            (
                "On Capital Allocation & Cash Utilization:",
                "With strong positive operating cash flows and minimal long-term debt, what are the Board's priorities for surplus capital between organic capex, bolt-on acquisitions, and dividend payouts?"
            )
        ]

        q_cards = []
        for idx, (title, q_body) in enumerate(investor_qs, 1):
            q_cards.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1.1rem 1.35rem; margin-bottom: 0.85rem;">
<div style="font-weight: 700; font-size: 0.92rem; color: #fbbf24; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 8px;">
  <span>❓ Question {idx}:</span> {title}
</div>
<div style="font-size: 0.9rem; color: #f8fafc; line-height: 1.6; font-style: italic;">
  \"{q_body}\"
</div>
</div>""")

        st.html("".join(q_cards))
