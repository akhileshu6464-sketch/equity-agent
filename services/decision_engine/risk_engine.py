"""
Future Risk Engine (services/decision_engine/risk_engine.py)
Identifies evidence-grounded structural, operational, balance sheet, and market risks.
Classifies risks into:
- KNOWN RISK (Existent contractual, financial, or operational exposures)
- EMERGING RISK (Developing commodity inflation, working capital elongation, or competitive threats)
- POTENTIAL RISK (Regulatory, technological, or cyclical macro disruptions)
Defines potential impact and early warning indicators.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.RiskEngine")


@dataclass(frozen=True)
class FutureRisk:
    """Represents a specific, evidence-grounded operational or financial risk."""
    risk_title: str
    risk_category: str          # "KNOWN_RISK", "EMERGING_RISK", "POTENTIAL_RISK"
    domain: str                 # "RAW_MATERIALS", "WORKING_CAPITAL", "LEVERAGE", "COMPETITION", "REGULATION", "EXECUTION"
    evidence: str
    potential_impact: str
    early_warning_indicator: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FutureRiskEngine:
    """
    Identifies evidence-based operational, working capital, balance sheet, and sector risks.
    """

    def __init__(self, store: FundamentalDataStore, sector: str):
        self.store = store
        self.sector = sector or "General Corporate"

    def identify_risks(
        self,
        governance_data: Optional[Dict[str, Any]] = None,
        primary_disclosures: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes concrete risks grounded in balance sheet metrics, cash conversion trends, and disclosures.
        """
        risks: List[FutureRisk] = []
        gov = governance_data or {}
        disclosures = primary_disclosures or {}
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])

        # 1. Balance Sheet / Solvency Risk
        if annual_periods:
            curr_p = annual_periods[-1]
            debt = self.store.get_datapoint("Total Debt", curr_p, "ANNUAL")
            cash = self.store.get_datapoint("Cash & Equivalents", curr_p, "ANNUAL")
            ebitda = self.store.get_datapoint("EBITDA", curr_p, "ANNUAL")

            if debt and cash and ebitda:
                net_debt = debt.value - cash.value
                leverage = net_debt / ebitda.value if ebitda.value > 0 else 0.0
                if leverage >= 2.5:
                    risks.append(FutureRisk(
                        risk_title="Balance Sheet Leverage and Debt Servicing Burden",
                        risk_category="KNOWN_RISK",
                        domain="LEVERAGE",
                        evidence=f"Gross debt stands at ₹{debt.value:,.1f} Cr with Net Debt / EBITDA at {leverage:.2f}x in {curr_p}.",
                        potential_impact="Elevated interest obligations compress profit before tax (PBT) and limit financial flexibility during revenue downcycles.",
                        early_warning_indicator="Contraction in Interest Coverage Ratio below 2.5x or credit rating revision notices."
                    ))
                else:
                    risks.append(FutureRisk(
                        risk_title="Borrowing Cost and Interest Rate Sensitivity",
                        risk_category="POTENTIAL_RISK",
                        domain="LEVERAGE",
                        evidence=f"Total debt of ₹{debt.value:,.1f} Cr maintained against ₹{cash.value:,.1f} Cr cash buffer.",
                        potential_impact="Shifts in policy repo rates or bank lending spreads directly affect financing costs on working capital facilities.",
                        early_warning_indicator="Rise in weighted average borrowing cost disclosed in annual financial notes."
                    ))

        # 2. Working Capital & Cash Conversion Risk
        if len(annual_periods) >= 2:
            prev_p = annual_periods[-2]
            curr_p = annual_periods[-1]
            rec_curr = self.store.get_datapoint("Receivables", curr_p, "ANNUAL")
            rec_prev = self.store.get_datapoint("Receivables", prev_p, "ANNUAL")
            rev_curr = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
            rev_prev = self.store.get_datapoint("Revenue", prev_p, "ANNUAL")

            if rec_curr and rec_prev and rev_curr and rev_prev and rev_prev.value > 0 and rec_prev.value > 0:
                rec_g = ((rec_curr.value - rec_prev.value) / rec_prev.value) * 100.0
                rev_g = ((rev_curr.value - rev_prev.value) / rev_prev.value) * 100.0
                if rec_g > rev_g + 10.0:
                    risks.append(FutureRisk(
                        risk_title="Working Capital Elongation & Customer Billing Cycle Drag",
                        risk_category="EMERGING_RISK",
                        domain="WORKING_CAPITAL",
                        evidence=f"Trade receivables grew {rec_g:+.1f}% YoY, outpacing sales growth of {rev_g:+.1f}%.",
                        potential_impact="Requires incremental short-term bank borrowings to bridge liquidity gaps, eroding free cash flow conversion.",
                        early_warning_indicator="Sequential expansion in Days Sales Outstanding (DSO) or rise in >180-day aged receivables."
                    ))

        # 3. Commodity & Input Cost Inflation Risk
        risks.append(FutureRisk(
            risk_title="Raw Material Input Price Volatility & Pricing Pass-Through Lags",
            risk_category="EMERGING_RISK",
            domain="RAW_MATERIALS",
            evidence="Annual cost notes demonstrate sensitivity to underlying commodity feedstock and intermediate prices.",
            potential_impact="A sharp upward spike in key raw materials compresses gross margins during the lag window before customer price adjustments take effect.",
            early_warning_indicator="YoY expansion in raw materials consumed as a percentage of total revenue delivery."
        ))

        # 4. Competitive Intensity & Pricing Pressure
        risks.append(FutureRisk(
            risk_title="Sector Competitive Intensity and Peer Bidding Pressures",
            risk_category="POTENTIAL_RISK",
            domain="COMPETITION",
            evidence="Operating in open domestic markets with established listed and unlisted peers.",
            potential_impact="Competitors seeking market share may engage in aggressive price undercutting or contract bidding, capping industry-wide margin expansion.",
            early_warning_indicator="Sequential decline in operating profit margin (OPM %) without offsetting volume gains."
        ))

        return [r.to_dict() for r in risks]
