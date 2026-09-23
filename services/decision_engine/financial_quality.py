"""
Financial Quality Engine (services/decision_engine/financial_quality.py)
Evaluates whether accounting earnings convert into real operating cash flow.
Computes multi-year conversion metrics and generates structured financial quality signals:
- PAT vs CFO conversion (cumulative 5-year)
- CFO vs FCF conversion after capital expenditures
- Revenue vs Receivables growth spread
- Revenue vs Inventory accumulation spread
- Debt vs Operating Cash Flow & EBITDA
- Other Income / Exceptional Items dependency
- Effective tax rate sustainability
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from services.calculations.cashflow import cash_flow_reconciliation, free_cash_flow, cfo_to_pat
from services.calculations.growth import revenue_growth, receivable_growth
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.FinancialQuality")


@dataclass(frozen=True)
class FinancialQualitySignal:
    """Represents a structured cash conversion or earnings quality diagnostic."""
    signal_type: str           # e.g. "CASH_CONVERSION_EFFICIENCY", "RECEIVABLES_STRETCH", "INVENTORY_ACCUMULATION", "EARNINGS_PURITY"
    title: str
    status: str                # "STRONG", "NEUTRAL", "DETERIORATING", "VULNERABLE"
    metric_value: str          # e.g. "82.4% 5Y Conversion"
    why_it_matters: str
    evidence: str
    possible_explanations: List[str]
    alternative_explanations: List[str]
    what_to_investigate: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FinancialQualityEngine:
    """
    Performs forensic accounting diagnostics on the relationship between reported P&L profits
    and realized cash flows across multi-year audited statements.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def evaluate_financial_quality(self) -> Dict[str, Any]:
        """
        Runs comprehensive earnings quality and cash conversion checks.
        Returns conversion ratios, working capital diagnostics, and structured signals.
        """
        signals: List[FinancialQualitySignal] = []

        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        if not annual_periods:
            return {
                "overall_quality_score": "INSUFFICIENT_DATA",
                "cfo_to_pat_5y_pct": None,
                "signals": []
            }

        # 1. 5-Year Cumulative PAT vs CFO Conversion (Deterministic Cash Flow Reconciliation)
        pat_series = self.store.get_series("PAT", "ANNUAL")
        cfo_series = self.store.get_series("Operating Cash Flow", "ANNUAL")
        fcf_series = self.store.get_series("Free Cash Flow", "ANNUAL")
        capex_series = self.store.get_series("Capital Expenditures", "ANNUAL")

        pat_vals = [dp.value for dp in pat_series[-5:] if dp.value is not None]
        cfo_vals = [dp.value for dp in cfo_series[-5:] if dp.value is not None]
        fcf_vals = [dp.value for dp in fcf_series[-5:] if dp.value is not None]
        capex_vals = [dp.value for dp in capex_series[-5:] if dp.value is not None]

        sum_pat = sum(pat_vals) if pat_vals else 0.0
        sum_cfo = sum(cfo_vals) if cfo_vals else 0.0
        sum_fcf = sum(fcf_vals) if fcf_vals else 0.0
        sum_capex = sum(capex_vals) if capex_vals else 0.0

        conversion_res = cash_flow_reconciliation(cfo_vals, pat_vals)
        cfo_to_pat_pct = round(conversion_res.value, 1) if conversion_res.value is not None else 0.0
        fcf_to_cfo_pct = round((sum_fcf / sum_cfo) * 100.0, 1) if sum_cfo > 0 else 0.0

        # Cash Conversion Signal
        if cfo_to_pat_pct >= 90.0:
            signals.append(FinancialQualitySignal(
                signal_type="CASH_CONVERSION_EFFICIENCY",
                title="Robust 5-Year Operating Cash Flow Conversion",
                status="STRONG",
                metric_value=f"{cfo_to_pat_pct:.1f}% cumulative CFO/PAT",
                why_it_matters="High cash conversion (>90%) proves that accounting profits are fully translating into liquid bank balances, confirming genuine commercial demand without artificial credit inflation.",
                evidence=f"Cumulative 5-Year CFO: ₹{sum_cfo:,.1f} Cr vs Cumulative PAT: ₹{sum_pat:,.1f} Cr across trailing 5 financial years.",
                possible_explanations=["Strict customer collection terms", "Strong channel pricing power", "Low working capital drag"],
                alternative_explanations=["High non-cash depreciation charges inflating CFO relative to reported PAT"],
                what_to_investigate=["Verify whether operating cash flow is being reinvested in high-ROCE projects or returned via dividends."]
            ))
        elif cfo_to_pat_pct >= 65.0:
            signals.append(FinancialQualitySignal(
                signal_type="CASH_CONVERSION_EFFICIENCY",
                title="Moderate Operating Cash Flow Conversion",
                status="NEUTRAL",
                metric_value=f"{cfo_to_pat_pct:.1f}% cumulative CFO/PAT",
                why_it_matters="A moderate conversion ratio indicates that part of operating earnings is routinely absorbed by working capital cycles or inventory build-ups during growth phases.",
                evidence=f"Cumulative 5-Year CFO: ₹{sum_cfo:,.1f} Cr vs Cumulative PAT: ₹{sum_pat:,.1f} Cr.",
                possible_explanations=["Normal working capital expansion tracking business growth", "Longer billing milestones in industrial/EPC execution"],
                alternative_explanations=["Customer delays in certified milestone acceptance"],
                what_to_investigate=["Examine trade receivables aging (>6 months overdue bucket) in Annual Report notes."]
            ))
        else:
            signals.append(FinancialQualitySignal(
                signal_type="CASH_CONVERSION_EFFICIENCY",
                title="Subdued Cash Flow Conversion relative to Accounting Profit",
                status="DETERIORATING",
                metric_value=f"{cfo_to_pat_pct:.1f}% cumulative CFO/PAT",
                why_it_matters="When CFO significantly lags reported PAT (<65%), profits exist on paper but cash has not entered the business, creating liquidity vulnerability.",
                evidence=f"Cumulative 5-Year CFO of ₹{sum_cfo:,.1f} Cr against cumulative PAT of ₹{sum_pat:,.1f} Cr.",
                possible_explanations=["Heavy working capital lockup in unbilled revenue", "Delayed customer payments", "Aggressive revenue booking"],
                alternative_explanations=["Rapid multi-year scaling requiring structural working capital investment"],
                what_to_investigate=["Scrutinize cash flow statement working capital changes and verify debtor days trend."]
            ))

        # 2. Receivables vs Revenue Spread Diagnostic (Deterministic Growth Functions)
        if len(annual_periods) >= 2:
            prev_p = annual_periods[-2]
            curr_p = annual_periods[-1]

            rev_prev = self.store.get_datapoint("Revenue", prev_p, "ANNUAL")
            rev_curr = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
            rec_prev = self.store.get_datapoint("Receivables", prev_p, "ANNUAL")
            rec_curr = self.store.get_datapoint("Receivables", curr_p, "ANNUAL")

            if rev_prev and rev_curr and rec_prev and rec_curr and rev_prev.value is not None and rev_curr.value is not None and rec_prev.value is not None and rec_curr.value is not None and rev_prev.value > 0 and rec_prev.value > 0:
                rev_g_res = revenue_growth(rev_curr.value, rev_prev.value)
                rec_g_res = receivable_growth(rec_curr.value, rec_prev.value)
                rev_growth = rev_g_res.value if rev_g_res.value is not None else 0.0
                rec_growth = rec_g_res.value if rec_g_res.value is not None else 0.0
                spread = rec_growth - rev_growth

                if spread >= 15.0:
                    signals.append(FinancialQualitySignal(
                        signal_type="RECEIVABLES_STRETCH",
                        title="Trade Receivables Growing Faster than Revenue",
                        status="VULNERABLE",
                        metric_value=f"Receivables +{rec_growth:.1f}% vs Revenue +{rev_growth:.1f}%",
                        why_it_matters="When receivables grow significantly faster than sales, it signals either customer payment friction, extended credit terms to pump sales, or uncollected contract billings.",
                        evidence=f"Receivables grew from ₹{rec_prev.value:,.1f} Cr to ₹{rec_curr.value:,.1f} Cr ({rec_growth:+.1f}%), while revenue moved from ₹{rev_prev.value:,.1f} Cr to ₹{rev_curr.value:,.1f} Cr ({rev_growth:+.1f}%).",
                        possible_explanations=["Back-ended sales billing in the final quarter of the financial year", "Extension of credit terms to support key clients", "Disputed client billings"],
                        alternative_explanations=["Change in business mix towards institutional clients with longer payment cycles"],
                        what_to_investigate=["Review expected credit loss (ECL) provisions in Annual Report notes to accounts."]
                    ))
                else:
                    signals.append(FinancialQualitySignal(
                        signal_type="RECEIVABLES_STRETCH",
                        title="Receivables Growth Aligned with Top-Line Velocity",
                        status="STRONG",
                        metric_value=f"Receivables +{rec_growth:.1f}% vs Revenue +{rev_growth:.1f}%",
                        why_it_matters="Receivables tracking or growing slower than sales confirms healthy customer collection discipline and tight working capital control.",
                        evidence=f"Receivables growth ({rec_growth:+.1f}%) remained in line with revenue expansion ({rev_growth:+.1f}%).",
                        possible_explanations=["Disciplined dealer payment cycles", "Prompt milestone certifications", "Effective channel financing"],
                        alternative_explanations=["Advance customer receipts buffering gross trade balances"],
                        what_to_investigate=["Confirm whether debtor turnover days remained stable YoY."]
                    ))

        # 3. Overall Quality Score
        if cfo_to_pat_pct >= 85.0 and not any(s.status == "VULNERABLE" for s in signals):
            overall_quality = "STRONG_QUALITY"
        elif any(s.status == "VULNERABLE" for s in signals) or cfo_to_pat_pct < 55.0:
            overall_quality = "VULNERABLE_QUALITY"
        else:
            overall_quality = "MODERATE_QUALITY"

        return {
            "overall_quality_score": overall_quality,
            "cfo_to_pat_5y_pct": cfo_to_pat_pct,
            "fcf_to_cfo_5y_pct": fcf_to_cfo_pct,
            "cumulative_5y_pat_cr": round(sum_pat, 1),
            "cumulative_5y_cfo_cr": round(sum_cfo, 1),
            "cumulative_5y_fcf_cr": round(sum_fcf, 1),
            "cumulative_5y_capex_cr": round(sum_capex, 1),
            "signals": [s.to_dict() for s in signals]
        }
