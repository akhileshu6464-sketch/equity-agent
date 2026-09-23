"""
Investor Investigation Questions Generator (services/decision_engine/investor_questions.py)
Dynamically synthesizes company-specific, high-impact due diligence questions directly from:
- Detected multi-period changes and margin shifts
- Driver divergences (e.g. receivables outpacing sales, margin compression)
- Financial quality and cash conversion gaps
- Forensic anomalies and promoter pledge overhangs
- Embedded valuation hurdle expectations
Strictly avoids generic boilerplate questions.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.InvestorQuestions")


@dataclass(frozen=True)
class InvestigationQuestion:
    """Represents a specific, actionable question an investor must investigate before allocating capital."""
    question: str
    originating_signal: str     # Which specific metric/anomaly triggered this question
    why_crucial: str            # Financial impact on investment thesis
    where_to_investigate: str   # Exact document / section to check

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InvestorQuestionsEngine:
    """
    Synthesizes dynamically generated, company-specific due diligence questions.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def generate_questions(
        self,
        divergence_alerts: List[Dict[str, Any]],
        forensic_data: Dict[str, Any],
        financial_quality: Dict[str, Any],
        valuation_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Dynamically constructs company-specific due diligence questions from actual findings.
        """
        questions: List[InvestigationQuestion] = []

        # 1. Questions from Divergence Alerts
        for alert in divergence_alerts:
            a_type = alert.get("type", "")
            desc = alert.get("description", "")
            ev = alert.get("evidence", "")

            if a_type == "TOPLINE_GROWTH_MARGIN_DILUTION":
                questions.append(InvestigationQuestion(
                    question="What specific raw material price increases or contractual pricing lags caused operating margins to contract despite strong top-line revenue expansion?",
                    originating_signal=f"Top-Line Expansion with Margin Contraction ({ev})",
                    why_crucial="If margin dilution is structural rather than temporary commodity lag, top-line growth will not create shareholder value or ROCE expansion.",
                    where_to_investigate="Review quarterly concall transcript discussion on raw material pass-through clauses and inspect cost of materials consumed in P&L notes."
                ))
            elif a_type == "PROFIT_CASH_DIVERGENCE":
                questions.append(InvestigationQuestion(
                    question="Why did accounting net profit (PAT) expand while Operating Cash Flow (CFO) contracted between reporting periods?",
                    originating_signal=f"Profit vs Cash Flow Divergence ({ev})",
                    why_crucial="Profits not converting into cash indicate that earnings are locked up in receivables or inventories, creating potential liquidity strain.",
                    where_to_investigate="Inspect the Cash Flow Statement: check working capital adjustments (trade receivables and inventory lines) and verify non-cash revenue items."
                ))
            elif a_type == "RECEIVABLES_OUTPACING_SALES":
                questions.append(InvestigationQuestion(
                    question="What commercial factors caused trade receivables to compound materially faster than top-line revenue?",
                    originating_signal=f"Receivables Outpacing Sales ({ev})",
                    why_crucial="Could indicate channel stuffing, delayed customer acceptance of billed milestones, or customer credit deterioration.",
                    where_to_investigate="Check Note on Trade Receivables in the Annual Report: analyze aging schedule (>6 months and >1 year buckets) and disputed dues."
                ))
            elif a_type == "INVENTORY_ACCUMULATION":
                questions.append(InvestigationQuestion(
                    question="Is the sharp surge in inventory due to strategic advance raw material procurement or finished goods accumulation from slower dealer sales?",
                    originating_signal=f"Inventory Accumulation Divergence ({ev})",
                    why_crucial="Excess finished goods inventory risks post-period discounted clearances, write-downs, and working capital drag.",
                    where_to_investigate="Examine the breakdown between raw materials, work-in-progress (WIP), and finished goods in Note on Inventories."
                ))

        # 2. Questions from Forensic Anomalies
        for anom in forensic_data.get("anomalies", []):
            dim = anom.get("dimension", "")
            pattern = anom.get("observed_pattern", "")
            step = anom.get("investor_due_diligence_step", "")

            if dim == "PROMOTER_ENCUMBRANCE":
                questions.append(InvestigationQuestion(
                    question="What is the exact end-use of borrowings secured by pledged promoter shares, and what is the debt-service capacity of the promoter group?",
                    originating_signal="Promoter Shareholding Encumbrance / Pledge",
                    why_crucial="High pledge percentages expose minority shareholders to margin call volatility and forced market liquidations during drawdowns.",
                    where_to_investigate="Check latest BSE/NSE SAST filings and pledge disclosure declarations by promoters."
                ))
            elif dim == "OFF_BALANCE_SHEET_EXPOSURE":
                questions.append(InvestigationQuestion(
                    question="What is the probability of contingent liabilities and disputed tax demands materializing into actual cash outflows?",
                    originating_signal="Material Contingent Liabilities and Disputed Claims",
                    why_crucial="Unprovided claims exceeding 15% of net worth could impair book value and deplete cash buffers upon adverse legal outcomes.",
                    where_to_investigate="Review Note on Contingent Liabilities and Legal Commitments in the Annual Report."
                ))

        # 3. Questions from Valuation & Embedded Growth Expectations
        mkt_analysis = valuation_data.get("market_pricing_analysis", {})
        implied_cagr = mkt_analysis.get("implied_growth_hurdle_cagr", 10.0)
        hist_cagr = mkt_analysis.get("historical_5y_growth_cagr", 10.0)

        if implied_cagr > hist_cagr + 3.0:
            questions.append(InvestigationQuestion(
                question=f"What concrete capacity additions or market share gains justify the market pricing in a {implied_cagr:.1f}% 10-year cash flow CAGR when historical delivery was {hist_cagr:.1f}%?",
                originating_signal=f"Reverse DCF Implied Hurdle ({implied_cagr:.1f}%) > Historical 5Y Delivery ({hist_cagr:.1f}%)",
                why_crucial="High embedded expectations compress the margin of safety; any execution stumble or sector slowdown could trigger valuation de-rating.",
                where_to_investigate="Assess ongoing CapEx commissioning timelines, order-book book-to-bill ratio, and peer capacity additions."
            ))
        else:
            questions.append(InvestigationQuestion(
                question="Are current operating profit margins sustainable through cyclical input cost shifts over the next 3 years?",
                originating_signal="Through-Cycle Operating Margin Defense",
                why_crucial="Sustaining projected cash flows requires the enterprise to defend gross margins without losing volume to peers.",
                where_to_investigate="Analyze 5-year gross margin corridors and contractual price escalation clauses."
            ))

        # 4. Question on Cash Flow Conversion
        cfo_pct = financial_quality.get("cfo_to_pat_5y_pct")
        if cfo_pct is not None and cfo_pct < 70.0:
            questions.append(InvestigationQuestion(
                question=f"Why has cumulative 5-year operating cash conversion (CFO/PAT) averaged only {cfo_pct:.1f}%, and when will working capital cycles normalize?",
                originating_signal=f"Subdued 5-Year Cumulative Cash Conversion ({cfo_pct:.1f}%)",
                why_crucial="A persistent cash conversion gap forces reliance on external bank debt to fund ongoing operations.",
                where_to_investigate="Review Working Capital Changes in the Consolidated Cash Flow Statement across the last 3 annual reports."
            ))

        return [q.to_dict() for q in questions[:6]]
