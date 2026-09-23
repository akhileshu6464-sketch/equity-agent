"""
Future Opportunity Engine (services/decision_engine/opportunity_engine.py)
Identifies evidence-grounded growth opportunities, operational leverage mechanisms, and expansion catalysts.
Separates:
- COMPANY_GUIDANCE
- EXTERNAL_ESTIMATE
- RESEARCH_BEAST_INFERENCE
- MODEL_ASSUMPTION
Each opportunity defines:
Opportunity, Evidence, Business Mechanism, Dependencies, Time Horizon, and Risks.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.OpportunityEngine")


@dataclass(frozen=True)
class FutureOpportunity:
    """Represents an evidence-backed growth opportunity with explicit mechanism and dependencies."""
    opportunity_title: str
    epistemological_type: str   # "COMPANY_GUIDANCE", "RESEARCH_BEAST_INFERENCE", "MODEL_ASSUMPTION", "EXTERNAL_ESTIMATE"
    business_mechanism: str
    evidence: str
    dependencies: List[str]
    time_horizon: str           # "6-12 MONTHS", "1-3 YEARS", "3-5 YEARS"
    associated_execution_risks: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FutureOpportunityEngine:
    """
    Synthesizes concrete, evidence-backed commercial expansion drivers and capacity milestones.
    """

    def __init__(self, store: FundamentalDataStore, sector: str):
        self.store = store
        self.sector = sector or "General Corporate"

    def identify_opportunities(
        self,
        primary_disclosures: Optional[Dict[str, Any]] = None,
        concall_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Identifies specific opportunities supported by filings, concall commentary, or balance sheet capacity.
        """
        opps: List[FutureOpportunity] = []
        disclosures = primary_disclosures or {}
        concall = concall_data or {}
        filings_text = str(disclosures.get("regulatory_announcements", "")) + " " + str(disclosures.get("annual_report_excerpts", ""))

        # 1. Operating Leverage Opportunity (from fundamental store)
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        if len(annual_periods) >= 2:
            curr_p = annual_periods[-1]
            rev_curr = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
            ebitda_m_curr = self.store.get_datapoint("EBITDA Margin", curr_p, "ANNUAL")
            if rev_curr and ebitda_m_curr:
                opps.append(FutureOpportunity(
                    opportunity_title="Fixed Asset Turnover Scaling & Operating Leverage",
                    epistemological_type="RESEARCH_BEAST_INFERENCE",
                    business_mechanism="As production volume ramps across existing manufacturing/operational assets, fixed overhead absorption expands operating EBITDA margins.",
                    evidence=f"Audited revenue delivered ₹{rev_curr.value:,.1f} Cr at {ebitda_m_curr.value:.1f}% EBITDA margin in {curr_p}.",
                    dependencies=["Sustained customer volume offtake", "Absence of unforeseen plant shutdown or execution bottlenecks"],
                    time_horizon="1-3 YEARS",
                    associated_execution_risks=["Subdued industry demand leading to underutilized capacity blocks"]
                ))

        # 2. Capacity Additions / Project Pipeline (from filings/concall)
        capex_text = concall.get("committed_capex", "")
        if capex_text and capex_text != "Verified information unavailable.":
            opps.append(FutureOpportunity(
                opportunity_title="Commercialization of Sanctioned Capital Expenditure",
                epistemological_type="COMPANY_GUIDANCE",
                business_mechanism="Commissioning of ongoing fixed asset expansion adds incremental revenue capacity and allows entry into higher-margin product/project segments.",
                evidence=f"Management disclosures in earnings calls: '{capex_text}'.",
                dependencies=["Timely statutory environmental/regulatory clearances", "On-schedule equipment installation and trial runs"],
                time_horizon="12-24 MONTHS",
                associated_execution_risks=["Project cost overruns", "Commissioning delays", "Lower-than-modeled initial capacity utilization"]
            ))
        elif any(term in filings_text.lower() for term in ["order inflow", "contract award", "loi", "tender win"]):
            opps.append(FutureOpportunity(
                opportunity_title="Order Book Execution Ramp-Up and Billing Velocity",
                epistemological_type="COMPANY_GUIDANCE",
                business_mechanism="Conversion of certified order backlogs into billable operational milestones accelerates revenue compounding.",
                evidence="BSE/NSE LODR regulatory filings report ongoing contract wins and project milestone agreements.",
                dependencies=["Timely right-of-way (ROW) and client site handover", "Adequate non-fund-based bank guarantee limits"],
                time_horizon="6-18 MONTHS",
                associated_execution_risks=["Client milestone certification delays", "Working capital absorption during peak billing cycles"]
            ))

        # 3. Market Share & Industry Tailwinds
        sec_lower = self.sector.lower()
        if "infra" in sec_lower or "construction" in sec_lower:
            opps.append(FutureOpportunity(
                opportunity_title="Government Infrastructure Capex Allocations",
                epistemological_type="MODEL_ASSUMPTION",
                business_mechanism="High budgetary highway and multimodal logistics outlays increase the total addressable bidding pool for pre-qualified contractors.",
                evidence="Union Budget capital allocation framework and NHAI national project pipeline.",
                dependencies=["Sustained central budgetary allocations", "Disciplined bidding without aggressive peer margin undercutting"],
                time_horizon="1-3 YEARS",
                associated_execution_risks=["Tender award deferrals by project authorities during election or monsoon windows"]
            ))
        elif "chemical" in sec_lower:
            opps.append(FutureOpportunity(
                opportunity_title="Global Innovator Sourcing Diversification (China+1)",
                epistemological_type="MODEL_ASSUMPTION",
                business_mechanism="Western innovator customers qualifying compliant Indian chemical partners under long-term supply arrangements.",
                evidence="Export volume trajectories and customer qualification disclosures in statutory filings.",
                dependencies=["Maintaining zero-liquid discharge environmental compliance", "Stringent customer quality audits"],
                time_horizon="2-4 YEARS",
                associated_execution_risks=["Price competition from low-cost Asian commodity chemical producers"]
            ))
        else:
            opps.append(FutureOpportunity(
                opportunity_title="Domestic Consumption Scaling and Distribution Deepening",
                epistemological_type="MODEL_ASSUMPTION",
                business_mechanism="Deepening channel distribution into tier-2/3 geographies drives volume growth beyond urban clusters.",
                evidence="Corporate geographic presence and distribution disclosures.",
                dependencies=["Channel partner credit discipline", "Effective marketing spend"],
                time_horizon="1-3 YEARS",
                associated_execution_risks=["Local regional competitive price undercutting"]
            ))

        return [o.to_dict() for o in opps]
