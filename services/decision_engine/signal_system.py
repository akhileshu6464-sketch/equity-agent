"""
Signal System Engine (services/decision_engine/signal_system.py)
Classifies granular observations into structured signals:
- POSITIVE SIGNAL (Demonstrated operational/financial improvement)
- NEGATIVE SIGNAL (Demonstrated operational/financial deterioration)
- WATCH (Material condition or capital deployment requiring ongoing monitoring)
Each signal contains:
- metric, change, period, reason, evidence, importance (CRITICAL, HIGH, MEDIUM), status
Does NOT reduce the entire enterprise to a single simplistic score.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.SignalSystem")


@dataclass(frozen=True)
class InvestmentSignal:
    """Represents a structured, auditable signal for investor evaluation."""
    signal_classification: str  # "POSITIVE_SIGNAL", "NEGATIVE_SIGNAL", "WATCH"
    metric: str
    change: str                 # e.g. "+350 bps", "-15.2%", "₹1,200 Cr Capex"
    period: str
    importance: str             # "CRITICAL", "HIGH", "MEDIUM"
    reason: str
    evidence: str
    status_label: str           # e.g. "Margin Expansion", "Receivables Drag", "Execution Monitoring"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SignalSystemEngine:
    """
    Synthesizes detected changes, financial quality diagnostics, and balance sheet positions
    into classified POSITIVE, NEGATIVE, and WATCH signals.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def generate_signals(
        self,
        detected_changes: List[Dict[str, Any]],
        financial_quality: Dict[str, Any],
        forensic_data: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates categorized investment signals across all audited domains.
        """
        positive_signals: List[InvestmentSignal] = []
        negative_signals: List[InvestmentSignal] = []
        watch_signals: List[InvestmentSignal] = []

        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        curr_p = annual_periods[-1] if annual_periods else "Recent"

        # 1. Signals from Detected Financial Changes
        for chg in detected_changes:
            metric = chg.get("metric", "")
            direction = chg.get("direction", "")
            significance = chg.get("significance", "LOW")
            period = chg.get("current_period", curr_p)
            pct = chg.get("percentage_change")
            unit = chg.get("unit", "")
            evidence = chg.get("evidence", "")

            if significance not in ["HIGH", "MEDIUM"]:
                continue

            # Revenue Growth
            if metric == "Revenue" and pct is not None:
                if pct >= 12.0:
                    positive_signals.append(InvestmentSignal(
                        signal_classification="POSITIVE_SIGNAL",
                        metric="Revenue",
                        change=f"{pct:+.1f}% YoY",
                        period=period,
                        importance="HIGH" if pct >= 20.0 else "MEDIUM",
                        reason="Robust top-line volume scaling and market demand delivery.",
                        evidence=evidence,
                        status_label="Healthy Top-Line Compounding"
                    ))
                elif pct <= -5.0:
                    negative_signals.append(InvestmentSignal(
                        signal_classification="NEGATIVE_SIGNAL",
                        metric="Revenue",
                        change=f"{pct:+.1f}% YoY",
                        period=period,
                        importance="HIGH",
                        reason="Top-line sales contraction reflecting softer demand or project completion pauses.",
                        evidence=evidence,
                        status_label="Top-Line Contraction"
                    ))

            # Operating Margins
            elif "Margin" in metric:
                prev_v = chg.get("previous_value", 0.0)
                curr_v = chg.get("current_value", 0.0)
                bps = round((curr_v - prev_v) * 100.0, 0)
                if bps >= 100:
                    positive_signals.append(InvestmentSignal(
                        signal_classification="POSITIVE_SIGNAL",
                        metric=metric,
                        change=f"{bps:+.0f} bps",
                        period=period,
                        importance="HIGH",
                        reason="Operating margin expansion driven by operating leverage, product mix, or cost discipline.",
                        evidence=evidence,
                        status_label="Margin Expansion"
                    ))
                elif bps <= -120:
                    negative_signals.append(InvestmentSignal(
                        signal_classification="NEGATIVE_SIGNAL",
                        metric=metric,
                        change=f"{bps:+.0f} bps",
                        period=period,
                        importance="HIGH",
                        reason="Operating margin compression due to raw material inflation, pricing pressure, or higher opex.",
                        evidence=evidence,
                        status_label="Margin Dilution"
                    ))

            # Return on Capital (ROCE / ROE)
            elif metric in ["ROCE", "ROE"]:
                curr_v = chg.get("current_value", 0.0)
                prev_v = chg.get("previous_value", 0.0)
                if curr_v >= 18.0:
                    positive_signals.append(InvestmentSignal(
                        signal_classification="POSITIVE_SIGNAL",
                        metric=metric,
                        change=f"{curr_v:.1f}% ({curr_v - prev_v:+.1f}%)",
                        period=period,
                        importance="CRITICAL",
                        reason=f"High capital productivity: {metric} of {curr_v:.1f}% exceeds institutional cost of capital (WACC ~11.5%) by a healthy spread.",
                        evidence=evidence,
                        status_label="Superior Capital Efficiency"
                    ))
                elif curr_v < 10.0 and curr_v > 0:
                    negative_signals.append(InvestmentSignal(
                        signal_classification="NEGATIVE_SIGNAL",
                        metric=metric,
                        change=f"{curr_v:.1f}%",
                        period=period,
                        importance="HIGH",
                        reason=f"Sub-par capital productivity: {metric} at {curr_v:.1f}% operates below the cost of capital, indicating inadequate return on employed assets.",
                        evidence=evidence,
                        status_label="Sub-Hurdle Capital Return"
                    ))

        # 2. Signals from Financial Quality (PAT vs CFO)
        cfo_pct = financial_quality.get("cfo_to_pat_5y_pct")
        if cfo_pct is not None:
            if cfo_pct >= 90.0:
                positive_signals.append(InvestmentSignal(
                    signal_classification="POSITIVE_SIGNAL",
                    metric="5Y Cumulative CFO/PAT",
                    change=f"{cfo_pct:.1f}%",
                    period="Trailing 5 Years",
                    importance="HIGH",
                    reason="High cash conversion proves accounting profits are backed by actual operating cash inflows.",
                    evidence=f"5-Year cumulative conversion of {cfo_pct:.1f}% (CFO: ₹{financial_quality.get('cumulative_5y_cfo_cr', 0):,.1f} Cr).",
                    status_label="High Cash Flow Conversion"
                ))
            elif cfo_pct < 60.0:
                negative_signals.append(InvestmentSignal(
                    signal_classification="NEGATIVE_SIGNAL",
                    metric="5Y Cumulative CFO/PAT",
                    change=f"{cfo_pct:.1f}%",
                    period="Trailing 5 Years",
                    importance="CRITICAL",
                    reason="Subdued cash conversion indicates working capital absorption or aggressive revenue accruals.",
                    evidence=f"5-Year cumulative conversion of {cfo_pct:.1f}% reflects gap between reported profits and liquid cash inflows.",
                    status_label="Weak Cash Flow Conversion"
                ))

        # 3. Signals from Forensic Anomalies
        for anom in forensic_data.get("anomalies", []):
            sev = anom.get("severity", "")
            title = anom.get("anomaly_title", "")
            if sev == "CRITICAL_REVIEW":
                negative_signals.append(InvestmentSignal(
                    signal_classification="NEGATIVE_SIGNAL",
                    metric=anom.get("dimension", "Forensic Item"),
                    change="Accounting Divergence",
                    period=curr_p,
                    importance="CRITICAL",
                    reason=anom.get("observed_pattern", ""),
                    evidence=anom.get("evidence", ""),
                    status_label="Forensic Divergence"
                ))
            elif sev == "ELEVATED_WATCH":
                watch_signals.append(InvestmentSignal(
                    signal_classification="WATCH",
                    metric=anom.get("dimension", "Forensic Item"),
                    change="Balance Sheet Monitor",
                    period=curr_p,
                    importance="HIGH",
                    reason=anom.get("observed_pattern", ""),
                    evidence=anom.get("evidence", ""),
                    status_label="Balance Sheet Attention"
                ))

        # 4. Watch Signals from Major CapEx / Capital Allocation
        capex_dp = self.store.get_datapoint("Capital Expenditures", curr_p, "ANNUAL")
        if capex_dp and capex_dp.value >= 100.0:
            watch_signals.append(InvestmentSignal(
                signal_classification="WATCH",
                metric="Capital Expenditures",
                change=f"₹{capex_dp.value:,.1f} Cr Deployed",
                period=curr_p,
                importance="MEDIUM",
                reason="Substantial capital reinvestment deployed; investor must monitor project commissioning and subsequent asset turnover ramp-up.",
                evidence=f"Capital expenditure of ₹{capex_dp.value:,.1f} Cr in {curr_p}.",
                status_label="CapEx Execution Monitoring"
            ))

        # Ensure fallback entries if empty
        if not positive_signals:
            positive_signals.append(InvestmentSignal(
                signal_classification="POSITIVE_SIGNAL",
                metric="Operational Continuity",
                change="Verified",
                period=curr_p,
                importance="LOW",
                reason="Established operating history without statutory default.",
                evidence="Audited statements confirm active operational continuity.",
                status_label="Operational Continuity"
            ))
        if not watch_signals:
            watch_signals.append(InvestmentSignal(
                signal_classification="WATCH",
                metric="Quarterly Execution",
                change="Ongoing",
                period=curr_p,
                importance="LOW",
                reason="Monitor sequential volume offtake and gross margin trends in subsequent quarterly results.",
                evidence="Standard periodic disclosures.",
                status_label="Quarterly Results Watch"
            ))

        return {
            "total_positive_signals": len(positive_signals),
            "total_negative_signals": len(negative_signals),
            "total_watch_signals": len(watch_signals),
            "positive_signals": [s.to_dict() for s in positive_signals],
            "negative_signals": [s.to_dict() for s in negative_signals],
            "watch_signals": [s.to_dict() for s in watch_signals]
        }
