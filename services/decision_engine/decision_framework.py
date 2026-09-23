"""
Investor Decision Framework (services/decision_engine/decision_framework.py)
Produces the structured multi-dimensional Investor Decision Map:
- BUSINESS QUALITY: Strong / Mixed / Weak
- EARNINGS TREND: Improving / Stable / Deteriorating
- CASH FLOW QUALITY: Strong / Mixed / Weak
- BALANCE SHEET: Strong / Moderate / Stressed
- INDUSTRY OUTLOOK: Positive / Mixed / Challenging
- MANAGEMENT EXECUTION: Strong / Mixed / Weak / Insufficient evidence
- FORENSIC RISK: Low observed red flags / Some red flags / Significant red flags requiring investigation
- VALUATION CONTEXT: Reverse DCF implied hurdle vs historical delivery pace
- TOP OPPORTUNITIES & RISKS
- KEY DUE DILIGENCE QUESTIONS
Does NOT output an unsupported simplistic BUY or SELL label.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.DecisionFramework")


@dataclass(frozen=True)
class DecisionPillar:
    """Represents one of the 7 core fundamental pillars in the Investor Decision Map."""
    pillar_name: str
    status: str            # e.g. "STRONG", "IMPROVING", "MODERATE", "LOW_OBSERVED_RED_FLAGS"
    color: str             # "green", "amber", "red", "blue"
    summary_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InvestorDecisionFramework:
    """
    Synthesizes signals, financial quality diagnostics, forensic audits, and valuation hurdles
    into the master investor decision map.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def assemble_decision_map(
        self,
        signals_data: Dict[str, Any],
        financial_quality: Dict[str, Any],
        forensic_data: Dict[str, Any],
        industry_data: Dict[str, Any],
        management_data: Dict[str, Any],
        valuation_data: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
        investor_questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes the complete, structured Decision Support Map.
        """
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        curr_p = annual_periods[-1] if annual_periods else "Recent"

        # 1. Business Quality Pillar (ROCE + Margins + Moat)
        roce_dp = self.store.get_datapoint("ROCE", curr_p, "ANNUAL")
        roce_val = roce_dp.value if roce_dp else 0.0
        if roce_val >= 18.0:
            bq_status = "STRONG"
            bq_color = "green"
            bq_rationale = f"High capital efficiency: ROCE of {roce_val:.1f}% exceeds cost of capital (~11.5%) with established market standing."
        elif roce_val >= 11.0:
            bq_status = "MIXED"
            bq_color = "amber"
            bq_rationale = f"Moderate capital productivity: ROCE of {roce_val:.1f}% roughly covers cost of capital; returns sensitive to utilization cycles."
        else:
            bq_status = "WEAK"
            bq_color = "red"
            bq_rationale = f"Sub-hurdle capital efficiency: ROCE of {roce_val:.1f}% operates below the cost of capital."

        # 2. Earnings Trend Pillar (YoY Revenue & Margin direction)
        rev_dp = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
        prev_p = annual_periods[-2] if len(annual_periods) >= 2 else None
        rev_prev = self.store.get_datapoint("Revenue", prev_p, "ANNUAL") if prev_p else None
        rev_g = ((rev_dp.value - rev_prev.value) / rev_prev.value) * 100.0 if rev_dp and rev_prev and rev_prev.value > 0 else 0.0

        if rev_g >= 12.0:
            et_status = "IMPROVING"
            et_color = "green"
            et_rationale = f"Top-line expansion delivering {rev_g:+.1f}% YoY growth backed by ongoing operational execution."
        elif rev_g >= 0.0:
            et_status = "STABLE"
            et_color = "blue"
            et_rationale = f"Top-line delivery stable ({rev_g:+.1f}% YoY) with steady volume demand."
        else:
            et_status = "DETERIORATING"
            et_color = "red"
            et_rationale = f"Top-line sales contracted {rev_g:+.1f}% YoY, reflecting volume softness or completion pauses."

        # 3. Cash Flow Quality Pillar (5Y CFO/PAT)
        cfo_pct = financial_quality.get("cfo_to_pat_5y_pct")
        if cfo_pct is not None and cfo_pct >= 85.0:
            cf_status = "STRONG"
            cf_color = "green"
            cf_rationale = f"High 5-year cumulative CFO/PAT conversion of {cfo_pct:.1f}%; accounting profits translate cleanly into liquid cash."
        elif cfo_pct is not None and cfo_pct >= 60.0:
            cf_status = "MIXED"
            cf_color = "amber"
            cf_rationale = f"Moderate cash conversion ({cfo_pct:.1f}%); part of operating earnings is absorbed into working capital."
        else:
            cf_status = "WEAK"
            cf_color = "red"
            cfo_str = f"{cfo_pct:.1f}%" if cfo_pct is not None else "N/A"
            cf_rationale = f"Subdued cash flow conversion ({cfo_str}); paper profits diverge from cash inflows."

        # 4. Balance Sheet Pillar (Net Debt / EBITDA & Cash Buffer)
        debt_dp = self.store.get_datapoint("Total Debt", curr_p, "ANNUAL")
        cash_dp = self.store.get_datapoint("Cash & Equivalents", curr_p, "ANNUAL")
        ebitda_dp = self.store.get_datapoint("EBITDA", curr_p, "ANNUAL")
        net_debt = (debt_dp.value - cash_dp.value) if debt_dp and cash_dp else 0.0
        leverage = (net_debt / ebitda_dp.value) if ebitda_dp and ebitda_dp.value > 0 else 0.0

        if leverage <= 0.5:
            bs_status = "STRONG"
            bs_color = "green"
            bs_rationale = f"Lean leverage profile: Net Debt/EBITDA stands at {leverage:.2f}x with comfortable solvency buffer."
        elif leverage <= 2.2:
            bs_status = "MODERATE"
            bs_color = "amber"
            bs_rationale = f"Manageable leverage: Net Debt/EBITDA of {leverage:.2f}x; debt servicing supported by current operating cash flows."
        else:
            bs_status = "STRESSED"
            bs_color = "red"
            bs_rationale = f"Elevated leverage: Net Debt/EBITDA of {leverage:.2f}x requires significant cash flow allocation to debt service."

        # 5. Industry Outlook Pillar
        tw_count = len(industry_data.get("tailwinds", []))
        hw_count = len(industry_data.get("headwinds", []))
        if tw_count > hw_count:
            ind_status = "POSITIVE"
            ind_color = "green"
            ind_rationale = f"Sector supported by {tw_count} key structural tailwinds, including budgetary allocations or domestic consumption scaling."
        elif tw_count == hw_count:
            ind_status = "MIXED"
            ind_color = "amber"
            ind_rationale = "Sector presents balanced macro tailwinds offset by input commodity or competitive headwinds."
        else:
            ind_status = "CHALLENGING"
            ind_color = "red"
            ind_rationale = f"Sector faces {hw_count} headwinds including margin compression or competitive capacity additions."

        # 6. Management Execution Pillar
        tone = management_data.get("executive_tone", "Pragmatic")
        integrity = management_data.get("commitment_integrity_score", "High Integrity")
        if "High" in integrity:
            mgmt_status = "STRONG"
            mgmt_color = "green"
            mgmt_rationale = f"Management displays pragmatic operational commentary ({tone}) and consistent milestone execution."
        elif "Moderate" in integrity:
            mgmt_status = "MIXED"
            mgmt_color = "amber"
            mgmt_rationale = f"Guidance tracked with moderate execution variability across shifting quarterly cycles."
        else:
            mgmt_status = "INSUFFICIENT_EVIDENCE"
            mgmt_color = "blue"
            mgmt_rationale = "Limited direct management commentary available in primary regulatory filings."

        # 7. Forensic Risk Pillar
        anom_count = forensic_data.get("total_anomalies_flagged", 0)
        forensic_status_raw = forensic_data.get("forensic_status", "")
        if "ELEVATED" in forensic_status_raw:
            fr_status = "SIGNIFICANT_ANOMALIES_REQUIRING_INVESTIGATION"
            fr_color = "red"
            fr_rationale = f"{anom_count} financial/balance sheet anomalies flagged for detailed investor due diligence."
        elif anom_count > 0:
            fr_status = "SOME_RED_FLAGS_ON_WATCH"
            fr_color = "amber"
            fr_rationale = f"{anom_count} moderate balance sheet or working capital conditions identified for ongoing monitoring."
        else:
            fr_status = "LOW_OBSERVED_RED_FLAGS"
            fr_color = "green"
            fr_rationale = "Zero material accounting divergence or high-severity forensic anomalies detected."

        pillars = [
            DecisionPillar("Business Quality", bq_status, bq_color, bq_rationale),
            DecisionPillar("Earnings Trend", et_status, et_color, et_rationale),
            DecisionPillar("Cash Flow Quality", cf_status, cf_color, cf_rationale),
            DecisionPillar("Balance Sheet", bs_status, bs_color, bs_rationale),
            DecisionPillar("Industry Outlook", ind_status, ind_color, ind_rationale),
            DecisionPillar("Management Execution", mgmt_status, mgmt_color, mgmt_rationale),
            DecisionPillar("Forensic Risk", fr_status, fr_color, fr_rationale),
        ]

        mkt_analysis = valuation_data.get("market_pricing_analysis", {})
        val_summary = (
            f"Reverse DCF indicates the market price implies a {mkt_analysis.get('implied_growth_hurdle_cagr', 10.0):.1f}% 10-year cash flow CAGR "
            f"(historical 5-year delivery pace: {mkt_analysis.get('historical_5y_growth_cagr', 10.0):.1f}%)."
        )

        return {
            "decision_pillars": [p.to_dict() for p in pillars],
            "valuation_context": val_summary,
            "top_opportunities": opportunities[:3],
            "top_risks": risks[:3],
            "investor_due_diligence_questions": investor_questions
        }
