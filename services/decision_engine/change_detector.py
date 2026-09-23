"""
Change Detection Engine (services/decision_engine/change_detector.py)
Computes multi-period financial shifts (YoY, QoQ, 3Y/5Y CAGR, margin bps shifts, ROCE/ROE shifts).
Detects divergence anomalies and generates structured change records with auditable evidence.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import math
import logging
from services.calculations.growth import (
    yoy_change,
    qoq_change,
    cagr,
    revenue_growth,
    receivable_growth,
    inventory_growth,
    cfo_growth,
)
from services.calculations.margins import margin_change_bps
from .fundamental_store import FundamentalDataStore, FundamentalDatapoint

logger = logging.getLogger("ResearchBeast.ChangeDetector")


@dataclass(frozen=True)
class DetectedChange:
    """Represents an observed, mathematically verified change between periods."""
    metric: str
    previous_period: str
    current_period: str
    previous_value: float
    current_value: float
    absolute_change: float
    percentage_change: Optional[float]
    unit: str
    direction: str          # "IMPROVING", "DETERIORATING", "EXPANDING", "CONTRACTING", "STABLE"
    significance: str       # "HIGH", "MEDIUM", "LOW"
    change_type: str        # "YOY", "QOQ", "CAGR_5Y", "CAGR_3Y", "MARGIN_BPS"
    evidence: str
    divergence_flag: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ChangeDetectionEngine:
    """
    Evaluates historical fundamental series to detect, calculate, and classify
    all material financial shifts across multi-year and quarterly horizons.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def detect_all_changes(self) -> Dict[str, Any]:
        """
        Runs comprehensive change analysis across annual and quarterly series.
        Returns detected changes, key divergence alerts, and a synthesized trajectory summary.
        """
        annual_changes: List[DetectedChange] = []
        quarterly_changes: List[DetectedChange] = []
        divergence_alerts: List[Dict[str, Any]] = []

        # 1. Annual Trajectory Changes
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        if len(annual_periods) >= 2:
            prev_p = annual_periods[-2]
            curr_p = annual_periods[-1]

            metrics_to_track = [
                ("Revenue", "INR_CR", True),
                ("EBITDA", "INR_CR", True),
                ("EBIT", "INR_CR", True),
                ("PAT", "INR_CR", True),
                ("EPS", "INR", True),
                ("EBITDA Margin", "PERCENT", True),
                ("EBIT Margin", "PERCENT", True),
                ("Net Margin", "PERCENT", True),
                ("ROCE", "PERCENT", True),
                ("ROE", "PERCENT", True),
                ("Total Debt", "INR_CR", False),
                ("Net Debt", "INR_CR", False),
                ("Operating Cash Flow", "INR_CR", True),
                ("Free Cash Flow", "INR_CR", True),
                ("Receivables", "INR_CR", False),
                ("Inventory", "INR_CR", False),
                ("Working Capital", "INR_CR", False),
                ("Capital Expenditures", "INR_CR", True)
            ]

            for m_name, unit, higher_is_better in metrics_to_track:
                chg = self._compute_period_change(m_name, prev_p, curr_p, "ANNUAL", unit, higher_is_better)
                if chg:
                    annual_changes.append(chg)

            # 5-Year CAGR for Revenue, PAT, Operating Cash Flow
            if len(annual_periods) >= 5:
                start_p = annual_periods[-5]
                for cagr_m in ["Revenue", "PAT", "Operating Cash Flow"]:
                    cagr_chg = self._compute_cagr_change(cagr_m, start_p, curr_p, 4)
                    if cagr_chg:
                        annual_changes.append(cagr_chg)

            # Multi-Metric Divergence Triggers
            divergence_alerts = self._evaluate_divergence_triggers(prev_p, curr_p)

        # 2. Quarterly Trajectory Changes
        q_periods = self.store.to_summary_dict().get("quarterly_periods", [])
        if len(q_periods) >= 2:
            q_prev = q_periods[-2]
            q_curr = q_periods[-1]

            q_metrics = [
                ("Quarterly Sales", "INR_CR", True),
                ("Quarterly Operating Profit", "INR_CR", True),
                ("Quarterly OPM %", "PERCENT", True),
                ("Quarterly Net Profit", "INR_CR", True)
            ]
            for q_m, unit, higher_is_better in q_metrics:
                q_chg = self._compute_period_change(q_m, q_prev, q_curr, "QUARTERLY", unit, higher_is_better, is_qoq=True)
                if q_chg:
                    quarterly_changes.append(q_chg)

        # 3. Formulate Summary Verdict
        summary_trajectory = self._synthesize_trajectory_summary(annual_changes, divergence_alerts)

        return {
            "annual_changes": [c.to_dict() for c in annual_changes],
            "quarterly_changes": [c.to_dict() for c in quarterly_changes],
            "divergence_alerts": divergence_alerts,
            "summary_trajectory": summary_trajectory
        }

    def _compute_period_change(
        self,
        metric: str,
        prev_period: str,
        curr_period: str,
        period_type: str,
        unit: str,
        higher_is_better: bool,
        is_qoq: bool = False
    ) -> Optional[DetectedChange]:
        """Calculates exact delta, percentage change, and margin basis point movement."""
        dp_prev = self.store.get_datapoint(metric, prev_period, period_type)
        dp_curr = self.store.get_datapoint(metric, curr_period, period_type)

        if not dp_prev or not dp_curr:
            return None

        v_prev = dp_prev.value
        v_curr = dp_curr.value
        if v_prev is None or v_curr is None:
            return None

        abs_change = round(v_curr - v_prev, 2)

        # Deterministic Python Growth / Change
        if is_qoq:
            change_res = qoq_change(v_curr, v_prev, metric_name=metric)
        else:
            change_res = yoy_change(v_curr, v_prev, metric_name=metric)

        pct_change = round(change_res.value, 1) if change_res.value is not None else None

        # Direction determination
        if unit == "PERCENT":
            bps_res = margin_change_bps(v_curr, v_prev, metric_name=f"{metric}_BPS")
            bps_shift = round(bps_res.value, 0) if bps_res.value is not None else round((v_curr - v_prev) * 100.0, 0)
            if abs(bps_shift) < 25:
                direction = "STABLE"
            elif (bps_shift > 0 and higher_is_better) or (bps_shift < 0 and not higher_is_better):
                direction = "EXPANDING" if "Margin" in metric else "IMPROVING"
            else:
                direction = "CONTRACTING" if "Margin" in metric else "DETERIORATING"
            evidence = f"{metric} moved from {v_prev:.1f}% ({prev_period}) to {v_curr:.1f}% ({curr_period}), a shift of {bps_shift:+.0f} bps."
        else:
            if pct_change is not None and abs(pct_change) < 3.0:
                direction = "STABLE"
            elif (abs_change > 0 and higher_is_better) or (abs_change < 0 and not higher_is_better):
                direction = "IMPROVING"
            else:
                direction = "DETERIORATING"

            unit_str = "₹ Cr" if unit == "INR_CR" else ("₹" if unit == "INR" else "")
            pct_str = f" ({pct_change:+.1f}%)" if pct_change is not None else ""
            evidence = f"{metric} moved from {unit_str} {v_prev:,.1f} in {prev_period} to {unit_str} {v_curr:,.1f} in {curr_period}{pct_str}."

        # Significance classification
        significance = "LOW"
        if unit == "PERCENT" and abs(v_curr - v_prev) >= 1.5:
            significance = "HIGH"
        elif pct_change is not None and abs(pct_change) >= 15.0:
            significance = "HIGH"
        elif pct_change is not None and abs(pct_change) >= 7.0:
            significance = "MEDIUM"

        return DetectedChange(
            metric=metric,
            previous_period=prev_period,
            current_period=curr_period,
            previous_value=v_prev,
            current_value=v_curr,
            absolute_change=abs_change,
            percentage_change=pct_change,
            unit=unit,
            direction=direction,
            significance=significance,
            change_type="QOQ" if is_qoq else "YOY",
            evidence=evidence
        )

    def _compute_cagr_change(
        self,
        metric: str,
        start_period: str,
        end_period: str,
        years: int
    ) -> Optional[DetectedChange]:
        """Calculates verified multi-year compound annual growth rate using deterministic cagr function."""
        dp_start = self.store.get_datapoint(metric, start_period, "ANNUAL")
        dp_end = self.store.get_datapoint(metric, end_period, "ANNUAL")

        if not dp_start or not dp_end or dp_start.value is None or dp_end.value is None:
            return None

        cagr_res = cagr(dp_start.value, dp_end.value, years=float(years), metric_name=f"{metric}_CAGR")
        if cagr_res.value is None:
            return None

        cagr_val = round(cagr_res.value, 1)

        direction = "IMPROVING" if cagr_val >= 10.0 else ("STABLE" if cagr_val >= 0 else "DETERIORATING")
        evidence = f"{metric} compounded at {cagr_val:.1f}% CAGR over {years} years ({start_period} to {end_period}), moving from ₹ {dp_start.value:,.1f} Cr to ₹ {dp_end.value:,.1f} Cr."

        return DetectedChange(
            metric=f"{metric} (5Y CAGR)",
            previous_period=start_period,
            current_period=end_period,
            previous_value=dp_start.value,
            current_value=dp_end.value,
            absolute_change=round(dp_end.value - dp_start.value, 2),
            percentage_change=cagr_val,
            unit="PERCENT",
            direction=direction,
            significance="HIGH" if abs(cagr_val) >= 12.0 else "MEDIUM",
            change_type="CAGR_5Y",
            evidence=evidence
        )

    def _evaluate_divergence_triggers(self, prev_p: str, curr_p: str) -> List[Dict[str, Any]]:
        """
        Evaluates mathematical divergence patterns between sales, profitability, cash, and balance sheet items
        using deterministic calculation functions.
        """
        alerts = []

        rev_prev = self.store.get_datapoint("Revenue", prev_p, "ANNUAL")
        rev_curr = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
        ebitda_m_prev = self.store.get_datapoint("EBITDA Margin", prev_p, "ANNUAL")
        ebitda_m_curr = self.store.get_datapoint("EBITDA Margin", curr_p, "ANNUAL")
        pat_prev = self.store.get_datapoint("PAT", prev_p, "ANNUAL")
        pat_curr = self.store.get_datapoint("PAT", curr_p, "ANNUAL")
        cfo_prev = self.store.get_datapoint("Operating Cash Flow", prev_p, "ANNUAL")
        cfo_curr = self.store.get_datapoint("Operating Cash Flow", curr_p, "ANNUAL")
        rec_prev = self.store.get_datapoint("Receivables", prev_p, "ANNUAL")
        rec_curr = self.store.get_datapoint("Receivables", curr_p, "ANNUAL")
        inv_prev = self.store.get_datapoint("Inventory", prev_p, "ANNUAL")
        inv_curr = self.store.get_datapoint("Inventory", curr_p, "ANNUAL")

        if rev_prev and rev_curr and rev_prev.value is not None and rev_curr.value is not None and rev_prev.value > 0:
            rev_res = revenue_growth(rev_curr.value, rev_prev.value)
            rev_pct = rev_res.value if rev_res.value is not None else 0.0

            # 1. Top-line Growth with Margin Compression
            if ebitda_m_prev and ebitda_m_curr and ebitda_m_prev.value is not None and ebitda_m_curr.value is not None:
                margin_bps_res = margin_change_bps(ebitda_m_curr.value, ebitda_m_prev.value)
                margin_bps = margin_bps_res.value if margin_bps_res.value is not None else 0.0
                if rev_pct >= 10.0 and margin_bps <= -150:
                    alerts.append({
                        "type": "TOPLINE_GROWTH_MARGIN_DILUTION",
                        "severity": "HIGH",
                        "title": "Top-Line Expansion with Operating Margin Contraction",
                        "description": f"Revenue expanded {rev_pct:+.1f}% YoY, but EBITDA margin contracted by {margin_bps:.0f} bps (from {ebitda_m_prev.value:.1f}% to {ebitda_m_curr.value:.1f}%). Input-cost inflation or pricing lag absorbed top-line gains.",
                        "evidence": f"Revenue: ₹{rev_prev.value:,.1f}Cr → ₹{rev_curr.value:,.1f}Cr | EBITDA Margin: {ebitda_m_prev.value:.1f}% → {ebitda_m_curr.value:.1f}%"
                    })

            # 2. Profit Growth without Cash Conversion Divergence
            if pat_prev and pat_curr and cfo_prev and cfo_curr and pat_prev.value is not None and pat_curr.value is not None and pat_prev.value > 0:
                pat_res = yoy_change(pat_curr.value, pat_prev.value, metric_name="PAT_YOY")
                cfo_res = cfo_growth(cfo_curr.value, cfo_prev.value)
                pat_pct = pat_res.value if pat_res.value is not None else 0.0
                cfo_pct = cfo_res.value if cfo_res.value is not None else 0.0
                if pat_pct >= 10.0 and cfo_pct <= -10.0:
                    alerts.append({
                        "type": "PROFIT_CASH_DIVERGENCE",
                        "severity": "CRITICAL",
                        "title": "Profit Growth Diverging from Operating Cash Flow",
                        "description": f"PAT increased {pat_pct:+.1f}%, but Operating Cash Flow contracted by {cfo_pct:.1f}%. Accounting profits did not convert into real operating cash flow.",
                        "evidence": f"PAT: ₹{pat_prev.value:,.1f}Cr → ₹{pat_curr.value:,.1f}Cr | CFO: ₹{cfo_prev.value:,.1f}Cr → ₹{cfo_curr.value:,.1f}Cr"
                    })

            # 3. Receivables Outpacing Revenue
            if rec_prev and rec_curr and rec_prev.value is not None and rec_curr.value is not None and rec_prev.value > 0:
                rec_res = receivable_growth(rec_curr.value, rec_prev.value)
                rec_pct = rec_res.value if rec_res.value is not None else 0.0
                if rec_pct >= rev_pct + 15.0 and rec_pct >= 20.0:
                    alerts.append({
                        "type": "RECEIVABLES_OUTPACING_SALES",
                        "severity": "HIGH",
                        "title": "Receivables Growth Materially Outpacing Revenue Growth",
                        "description": f"Receivables grew {rec_pct:+.1f}% YoY while revenue grew {rev_pct:+.1f}%. Working capital is being absorbed in extended customer credit or uncollected billings.",
                        "evidence": f"Revenue YoY: {rev_pct:+.1f}% vs Receivables YoY: {rec_pct:+.1f}% (Spread: {rec_pct - rev_pct:+.1f}%)"
                    })

            # 4. Inventory Accumulation Divergence
            if inv_prev and inv_curr and inv_prev.value is not None and inv_curr.value is not None and inv_prev.value > 0:
                inv_res = inventory_growth(inv_curr.value, inv_prev.value)
                inv_pct = inv_res.value if inv_res.value is not None else 0.0
                if inv_pct >= rev_pct + 15.0 and inv_pct >= 20.0:
                    alerts.append({
                        "type": "INVENTORY_ACCUMULATION",
                        "severity": "MEDIUM",
                        "title": "Inventory Accumulation Outpacing Revenue Velocity",
                        "description": f"Inventories surged {inv_pct:+.1f}% YoY compared to {rev_pct:+.1f}% revenue growth, indicating warehouse accumulation or delayed channel offtake.",
                        "evidence": f"Revenue YoY: {rev_pct:+.1f}% vs Inventory YoY: {inv_pct:+.1f}% (Spread: {inv_pct - rev_pct:+.1f}%)"
                    })

        return alerts

    def _synthesize_trajectory_summary(
        self,
        changes: List[DetectedChange],
        alerts: List[Dict[str, Any]]
    ) -> str:
        """Synthesizes high-impact executive conclusion regarding fundamental trajectory."""
        rev_change = next((c for c in changes if c.metric == "Revenue" and c.change_type == "YOY"), None)
        pat_change = next((c for c in changes if c.metric == "PAT" and c.change_type == "YOY"), None)
        margin_change = next((c for c in changes if c.metric == "EBITDA Margin" and c.change_type == "YOY"), None)
        cfo_change = next((c for c in changes if c.metric == "Operating Cash Flow" and c.change_type == "YOY"), None)

        parts = []
        if rev_change:
            parts.append(f"Revenue moved {rev_change.percentage_change:+.1f}% YoY to ₹{rev_change.current_value:,.1f} Cr")
        if margin_change:
            bps = (margin_change.current_value - margin_change.previous_value) * 100.0
            parts.append(f"EBITDA margin shifted {bps:+.0f} bps to {margin_change.current_value:.1f}%")
        if pat_change:
            parts.append(f"PAT delivered {pat_change.percentage_change:+.1f}% YoY to ₹{pat_change.current_value:,.1f} Cr")

        base_summary = ". ".join(parts) + "." if parts else "Multi-period trajectory compiled."

        if alerts:
            alert_titles = "; ".join([a["title"] for a in alerts[:2]])
            return f"{base_summary} Key divergence alerts detected: {alert_titles}."
        return base_summary
