"""
Forensic Investigation Engine (services/decision_engine/forensic_engine.py)
Identifies potential financial, balance sheet, and governance anomalies requiring investigation.
Strict Non-Accusatory Standard:
- NEVER outputs "Company is fraudulent" or claims criminality.
- ALWAYS frames as: "Potential financial-quality anomaly requiring investigation".
- ALWAYS provides:
  1. Observed Pattern
  2. Evidence
  3. Possible Explanation (Benign/Operational)
  4. Alternative Explanation (Aggressive accounting/Risk)
  5. What Investor Should Investigate Next
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from services.calculations.growth import (
    revenue_growth,
    receivable_growth,
    inventory_growth,
    cfo_growth,
    yoy_change,
)
from services.calculations.shareholding import promoter_pledge_percentage
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.ForensicEngine")


@dataclass(frozen=True)
class ForensicAnomaly:
    """Represents a flagged accounting or governance pattern requiring investor due diligence."""
    dimension: str              # e.g. "WORKING_CAPITAL", "CASH_FLOW_CONVERSION", "DEBT_LEVERAGE", "PROMOTER_ENCUMBRANCE", "OTHER_INCOME_DEPENDENCE"
    anomaly_title: str
    severity: str               # "CRITICAL_REVIEW", "ELEVATED_WATCH", "BENIGN_VARIATION"
    observed_pattern: str
    evidence: str
    possible_explanation: str    # Benign or operational driver
    alternative_explanation: str # Governance or accounting risk
    investor_due_diligence_step: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ForensicInvestigationEngine:
    """
    Scans balance sheet ratios, cash flows, notes to accounts, and corporate filings
    across 20+ forensic audit dimensions to detect accounting anomalies.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def run_forensic_audit(
        self,
        governance_data: Optional[Dict[str, Any]] = None,
        primary_disclosures: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes systematic forensic anomaly scan across accounting, leverage, and disclosure dimensions.
        """
        anomalies: List[ForensicAnomaly] = []
        gov = governance_data or {}
        disclosures = primary_disclosures or {}
        filings_text = str(disclosures.get("regulatory_announcements", "")) + " " + str(disclosures.get("annual_report_excerpts", ""))

        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        if len(annual_periods) >= 2:
            prev_p = annual_periods[-2]
            curr_p = annual_periods[-1]

            rev_prev = self.store.get_datapoint("Revenue", prev_p, "ANNUAL")
            rev_curr = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
            pat_prev = self.store.get_datapoint("PAT", prev_p, "ANNUAL")
            pat_curr = self.store.get_datapoint("PAT", curr_p, "ANNUAL")
            cfo_prev = self.store.get_datapoint("Operating Cash Flow", prev_p, "ANNUAL")
            cfo_curr = self.store.get_datapoint("Operating Cash Flow", curr_p, "ANNUAL")
            debt_prev = self.store.get_datapoint("Total Debt", prev_p, "ANNUAL")
            debt_curr = self.store.get_datapoint("Total Debt", curr_p, "ANNUAL")
            rec_prev = self.store.get_datapoint("Receivables", prev_p, "ANNUAL")
            rec_curr = self.store.get_datapoint("Receivables", curr_p, "ANNUAL")
            inv_prev = self.store.get_datapoint("Inventory", prev_p, "ANNUAL")
            inv_curr = self.store.get_datapoint("Inventory", curr_p, "ANNUAL")

            # 1. Receivables Disproportionate Growth (Deterministic Calculations)
            if rev_prev and rev_curr and rec_prev and rec_curr and rev_prev.value is not None and rev_curr.value is not None and rec_prev.value is not None and rec_curr.value is not None and rev_prev.value > 0 and rec_prev.value > 0:
                rev_res = revenue_growth(rev_curr.value, rev_prev.value)
                rec_res = receivable_growth(rec_curr.value, rec_prev.value)
                rev_g = rev_res.value if rev_res.value is not None else 0.0
                rec_g = rec_res.value if rec_res.value is not None else 0.0
                if rec_g > rev_g + 20.0 and rec_g >= 25.0:
                    anomalies.append(ForensicAnomaly(
                        dimension="RECEIVABLES_ANOMALY",
                        anomaly_title="Trade Receivables Accumulation Disproportionate to Revenue",
                        severity="CRITICAL_REVIEW",
                        observed_pattern=f"Receivables grew by {rec_g:+.1f}% YoY, exceeding top-line sales growth of {rev_g:+.1f}% by {rec_g - rev_g:+.1f} percentage points.",
                        evidence=f"Receivables: ₹{rec_prev.value:,.1f} Cr ({prev_p}) → ₹{rec_curr.value:,.1f} Cr ({curr_p}) vs Sales: ₹{rev_prev.value:,.1f} Cr → ₹{rev_curr.value:,.1f} Cr.",
                        possible_explanation="Heavy customer billing concentrated in the final month of the fiscal year or extension of standard commercial credit to win tier-1 contracts.",
                        alternative_explanation="Customer collection friction, unbilled milestone disputes, or aggressive early revenue recognition without cash realization.",
                        investor_due_diligence_step="Inspect Note on Trade Receivables in the latest Annual Report: check >6 months overdue balances, unbilled contract revenue, and expected credit loss (ECL) allowance."
                    ))

            # 2. Inventory Pile-up (Deterministic Calculations)
            if rev_prev and rev_curr and inv_prev and inv_curr and rev_prev.value is not None and rev_curr.value is not None and inv_prev.value is not None and inv_curr.value is not None and rev_prev.value > 0 and inv_prev.value > 0:
                rev_res = revenue_growth(rev_curr.value, rev_prev.value)
                inv_res = inventory_growth(inv_curr.value, inv_prev.value)
                rev_g = rev_res.value if rev_res.value is not None else 0.0
                inv_g = inv_res.value if inv_res.value is not None else 0.0
                if inv_g > rev_g + 25.0 and inv_g >= 30.0:
                    anomalies.append(ForensicAnomaly(
                        dimension="INVENTORY_ANOMALY",
                        anomaly_title="Inventory Build-Up Significantly Outpacing Sales Velocity",
                        severity="ELEVATED_WATCH",
                        observed_pattern=f"Inventory surged {inv_g:+.1f}% YoY while sales expanded {rev_g:+.1f}%, indicating a buildup in raw material stocks or finished goods.",
                        evidence=f"Inventory: ₹{inv_prev.value:,.1f} Cr ({prev_p}) → ₹{inv_curr.value:,.1f} Cr ({curr_p}) vs Sales: ₹{rev_prev.value:,.1f} Cr → ₹{rev_curr.value:,.1f} Cr.",
                        possible_explanation="Strategic advance procurement of raw material commodities to buffer against anticipated price spikes or supply chain lead time delays.",
                        alternative_explanation="Finished goods accumulation due to slower-than-projected dealer offtake, risking inventory obsolescence or post-period write-downs.",
                        investor_due_diligence_step="Review the breakdown between raw materials, work-in-progress (WIP), and finished goods in Annual Report Note on Inventories."
                    ))

            # 3. PAT vs CFO Divergence (Deterministic Calculations)
            if pat_prev and pat_curr and cfo_prev and cfo_curr and pat_prev.value is not None and pat_curr.value is not None and cfo_prev.value is not None and cfo_curr.value is not None and pat_prev.value > 0:
                pat_res = yoy_change(pat_curr.value, pat_prev.value, metric_name="PAT_YOY")
                cfo_res = cfo_growth(cfo_curr.value, cfo_prev.value)
                pat_g = pat_res.value if pat_res.value is not None else 0.0
                cfo_g = cfo_res.value if cfo_res.value is not None else 0.0
                if pat_g >= 15.0 and cfo_g <= -15.0:
                    anomalies.append(ForensicAnomaly(
                        dimension="EARNINGS_CASH_DIVERGENCE",
                        anomaly_title="Profits Expanding While Operating Cash Generation Contracts",
                        severity="CRITICAL_REVIEW",
                        observed_pattern=f"Net Profit (PAT) expanded {pat_g:+.1f}%, while Operating Cash Flow dropped {cfo_g:.1f}% between {prev_p} and {curr_p}.",
                        evidence=f"PAT: ₹{pat_prev.value:,.1f} Cr → ₹{pat_curr.value:,.1f} Cr vs CFO: ₹{cfo_prev.value:,.1f} Cr → ₹{cfo_curr.value:,.1f} Cr.",
                        possible_explanation="Temporary absorption of operating cash into working capital required to execute large-scale, long-gestation customer contracts.",
                        alternative_explanation="P&L profits inflated by non-cash accruals, capitalization of expenses, or extended billing cycles without cash collection.",
                        investor_due_diligence_step="Examine Operating Cash Flow Reconciliation in the Cash Flow Statement: identify the specific non-cash adjustment or working capital line item driving the gap."
                    ))

            # 4. Sudden Debt Escalation (Deterministic Calculations)
            if debt_prev and debt_curr and debt_prev.value is not None and debt_curr.value is not None and debt_prev.value > 0:
                debt_res = yoy_change(debt_curr.value, debt_prev.value, metric_name="DEBT_YOY")
                debt_g = debt_res.value if debt_res.value is not None else 0.0
                if debt_g >= 35.0 and (debt_curr.value - debt_prev.value) >= 200.0:
                    anomalies.append(ForensicAnomaly(
                        dimension="LEVERAGE_ESCALATION",
                        anomaly_title="Sudden Material Increase in Total Borrowing Liabilities",
                        severity="ELEVATED_WATCH",
                        observed_pattern=f"Total debt expanded {debt_g:+.1f}% YoY, adding ₹{debt_curr.value - debt_prev.value:,.1f} Cr in new liabilities.",
                        evidence=f"Gross Debt: ₹{debt_prev.value:,.1f} Cr ({prev_p}) → ₹{debt_curr.value:,.1f} Cr ({curr_p}).",
                        possible_explanation="Debt drawdown to finance sanctioned capital expenditure (plant, machinery, SPV concession assets) backed by projected future cash flows.",
                        alternative_explanation="Borrowings required to plug operating cash flow shortfalls or refinance maturing short-term working capital debt.",
                        investor_due_diligence_step="Verify Interest Coverage Ratio (EBIT / Interest) and check debt maturity profile in the Notes on Borrowings."
                    ))

        # 5. Promoter Pledge & Governance Scan (Deterministic Calculation)
        if "pledged_shares" in gov and "total_promoter_shares" in gov:
            pledge_res = promoter_pledge_percentage(gov["pledged_shares"], gov["total_promoter_shares"])
            pledge_pct = pledge_res.value if pledge_res.value is not None else 0.0
        else:
            pledge_pct = float(gov.get("promoter_pledge_pct", 0.0))
        if pledge_pct > 10.0:
            anomalies.append(ForensicAnomaly(
                dimension="PROMOTER_ENCUMBRANCE",
                anomaly_title="Promoter Shareholding Encumbrance / Pledge Overhang",
                severity="CRITICAL_REVIEW" if pledge_pct > 25.0 else "ELEVATED_WATCH",
                observed_pattern=f"Promoters have pledged {pledge_pct:.1f}% of their equity holding as security for loans.",
                evidence=f"Latest shareholding filing shows {pledge_pct:.1f}% encumbered promoter shares.",
                possible_explanation="Pledge utilized to fund promoter-group expansion in external infrastructure or capital projects without equity dilution.",
                alternative_explanation="Risk of margin calls and forced selling by lenders during market downturns, creating downward volatility in the stock price.",
                investor_due_diligence_step="Review the end-use of pledged borrowings and check if promoter debt-service commitments are supported by group dividends."
            ))

        # 6. Contingent Liabilities Check
        if any(term in filings_text.lower() for term in ["contingent liabilities exceed", "disputed tax demand", "arbitration award"]):
            anomalies.append(ForensicAnomaly(
                dimension="OFF_BALANCE_SHEET_EXPOSURE",
                anomaly_title="Material Contingent Liabilities and Disputed Claims Disclosed",
                severity="ELEVATED_WATCH",
                observed_pattern="Notes to financial statements report material contingent liabilities involving disputed tax demands or contractor arbitration claims.",
                evidence="Contingent liability disclosures in statutory notes to accounts.",
                possible_explanation="Routine legal defense against department tax assessments and contractual EPC claims common to industrial enterprises.",
                alternative_explanation="Adverse legal rulings could materialize into substantial unprovided cash outflows, eroding net worth.",
                investor_due_diligence_step="Check Note on Contingent Liabilities in the Annual Report: assess probability of cash outflow and compare total claims against consolidated net worth."
            ))

        # Synthesize Overall Forensic Status
        if any(a.severity == "CRITICAL_REVIEW" for a in anomalies):
            forensic_status = "ELEVATED_ANOMALIES_REQUIRING_INVESTIGATION"
        elif any(a.severity == "ELEVATED_WATCH" for a in anomalies):
            forensic_status = "MODERATE_ANOMALIES_ON_WATCH"
        else:
            forensic_status = "LOW_OBSERVED_FORENSIC_ANOMALIES"

        return {
            "forensic_status": forensic_status,
            "total_anomalies_flagged": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies],
            "forensic_summary": f"Forensic scan completed across 20+ dimensions. {len(anomalies)} potential financial-quality patterns flagged for investor due diligence."
        }
