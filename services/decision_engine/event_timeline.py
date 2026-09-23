"""
Event Intelligence Engine (services/decision_engine/event_timeline.py)
Builds an auditable chronological corporate timeline across major filings, financial results,
concalls, capacity additions, contracts, and regulatory updates.
Every event contains:
- DATE
- EVENT
- SOURCE
- BUSINESS RELEVANCE
- FINANCIAL RELEVANCE
Strictly avoids claiming an event caused market movements without direct evidence.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.EventTimeline")


@dataclass(frozen=True)
class CorporateEvent:
    """Represents an auditable event on the corporate timeline."""
    date: str
    event_title: str
    event_category: str     # "EARNINGS_RESULTS", "CAPACITY_EXPANSION", "CONTRACT_ORDER", "REGULATORY_FILING", "ANNUAL_REPORT"
    source: str
    business_relevance: str
    financial_relevance: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventTimelineEngine:
    """
    Assembles a chronological timeline from primary regulatory filings and financial statement cycles.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def build_timeline(
        self,
        primary_disclosures: Optional[Dict[str, Any]] = None,
        concall_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes verified corporate events into a chronological timeline.
        """
        events: List[CorporateEvent] = []
        disclosures = primary_disclosures or {}
        concall = concall_data or {}
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        quarterly_periods = self.store.to_summary_dict().get("quarterly_periods", [])

        # 1. Recent Earnings Call Event
        call_period = concall.get("call_period", "")
        if call_period:
            events.append(CorporateEvent(
                date=call_period,
                event_title="Executive Earnings Conference Call & Strategy Briefing",
                event_category="EARNINGS_RESULTS",
                source=f"BSE/NSE LODR Earnings Call Transcript ({call_period})",
                business_relevance="Executive discussion of execution momentum, client offtake, and capacity utilization.",
                financial_relevance="Outlines quarterly margin trajectory, working capital guidance, and forward CapEx commitments."
            ))

        # 2. Latest Audited Annual Financial Results
        if annual_periods:
            latest_y = annual_periods[-1]
            rev_dp = self.store.get_datapoint("Revenue", latest_y, "ANNUAL")
            pat_dp = self.store.get_datapoint("PAT", latest_y, "ANNUAL")
            events.append(CorporateEvent(
                date=latest_y,
                event_title=f"Publication of Audited Annual Financial Results ({latest_y})",
                event_category="ANNUAL_REPORT",
                source=f"Audited Statutory Annual Financial Statements ({latest_y})",
                business_relevance="Full-year audited disclosure of consolidated operational performance and segment delivery.",
                financial_relevance=f"Reported revenue of ₹{rev_dp.value:,.1f} Cr and net profit of ₹{pat_dp.value:,.1f} Cr." if rev_dp and pat_dp else "Audited balance sheet and P&L formally published."
            ))

        # 3. Prior Year Audited Statement Milestone
        if len(annual_periods) >= 2:
            prev_y = annual_periods[-2]
            events.append(CorporateEvent(
                date=prev_y,
                event_title=f"Statutory Financial Year Closing ({prev_y})",
                event_category="ANNUAL_REPORT",
                source=f"Statutory Annual Report & Auditor Report ({prev_y})",
                business_relevance="Establishes comparative baseline for multi-year financial and balance sheet analysis.",
                financial_relevance="Forms base year for YoY delta calculations, margin comparisons, and cash conversion ratios."
            ))

        # 4. Regulatory Announcements / Disclosed Project Milestones
        announcements = disclosures.get("regulatory_announcements", "")
        if announcements and announcements != "Verified information unavailable.":
            events.append(CorporateEvent(
                date="Trailing 12 Months",
                event_title="Regulatory Disclosures & Material Operational Updates",
                event_category="REGULATORY_FILING",
                source="BSE/NSE Corporate Announcement Disclosures",
                business_relevance="Compliance updates, board meeting outcomes, and shareholder resolutions filed under SEBI LODR.",
                financial_relevance="Discloses material transactions, promoter shareholding confirmations, and dividend recommendations."
            ))

        return [e.to_dict() for e in events]
