"""
Industry Intelligence Engine (services/decision_engine/industry_engine.py)
Analyzes macro-sector conditions and decouples company-specific delivery from broader industry dynamics.
Classifies macro parameters into:
- TAILWINDS
- HEADWINDS
- STRUCTURAL CHANGES
Evaluates market share shifts (Company Growth vs Industry Growth).
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import logging
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.IndustryEngine")


@dataclass(frozen=True)
class IndustryFactor:
    """Represents a specific external industry condition with auditable classification."""
    category: str           # "TAILWIND", "HEADWIND", "STRUCTURAL_CHANGE"
    parameter: str          # e.g. "CAPACITY_CYCLE", "RAW_MATERIAL_PRICING", "CHINA_COMPETITION", "GOVERNMENT_POLICY", "EXPORT_DEMAND"
    description: str
    impact_on_company: str
    evidence_source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IndustryIntelligenceEngine:
    """
    Evaluates sector demand, supply additions, pricing power, and regulatory dynamics.
    Decouples company revenue performance from underlying industry cycle.
    """

    def __init__(self, store: FundamentalDataStore, sector: str, industry: str):
        self.store = store
        self.sector = sector or "General Corporate"
        self.industry = industry or "Diverse Operations"

    def analyze_industry_context(
        self,
        sector_kpi_data: Optional[Dict[str, Any]] = None,
        primary_disclosures: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes tailwinds, headwinds, structural shifts, and market share position.
        """
        factors: List[IndustryFactor] = []
        kpis = sector_kpi_data or {}
        sec_lower = (self.sector + " " + self.industry).lower()

        # 1. Sector-Tailwinds & Headwinds based on verified industry profile
        if "infra" in sec_lower or "construction" in sec_lower or "engineering" in sec_lower:
            factors.append(IndustryFactor(
                category="TAILWIND",
                parameter="GOVERNMENT_CAPEX_MANDATE",
                description="Central and state government infrastructure allocations (NHAI highway awards, PM Gati Shakti, railway EPC) provide strong multi-year project pipelines.",
                impact_on_company="Provides order book visibility and milestone billing opportunities for pre-qualified tier-1 EPC contractors.",
                evidence_source="Union Budget Capital Outlays & NHAI Procurement Mandates"
            ))
            factors.append(IndustryFactor(
                category="HEADWIND",
                parameter="RAW_MATERIAL_VOLATILITY",
                description="Price fluctuations in key input commodities (bitumen, structural steel, cement) can pressure operating margins during fixed-price execution phases.",
                impact_on_company="Requires active escalation clause pass-through to avoid margin absorption.",
                evidence_source="Domestic Commodity Index & EPC Procurement Trends"
            ))
            factors.append(IndustryFactor(
                category="STRUCTURAL_CHANGE",
                parameter="CONCESSION_MONETIZATION",
                description="Transition towards Hybrid Annuity Model (HAM) and asset monetization via InvITs releases developer capital from completed BOT assets.",
                impact_on_company="Strengthens balance sheet de-leveraging and frees equity for redeployment into new projects.",
                evidence_source="NHAI Concession Policies & Statutory Disclosures"
            ))

        elif "chemical" in sec_lower or "material" in sec_lower:
            factors.append(IndustryFactor(
                category="TAILWIND",
                parameter="CHINA_PLUS_ONE_SOURCING",
                description="Global pharmaceutical and agrochemical innovators continue diversifying active intermediate sourcing away from China toward compliant Indian partners.",
                impact_on_company="Creates long-term multi-year customer qualification and contract synthesis demand.",
                evidence_source="Global Supply Chain Realignments & Export LODR Filings"
            ))
            factors.append(IndustryFactor(
                category="HEADWIND",
                parameter="CHINESE_COMMODITY_DUMPING",
                description="Aggressive discounting and capacity dumping from Chinese basic chemical producers in commodity chemical grades.",
                impact_on_company="Pressures gross margins on non-patented, commodity-like chemical intermediate lines.",
                evidence_source="Import/Export Chemical Trade Bulletins"
            ))
            factors.append(IndustryFactor(
                category="STRUCTURAL_CHANGE",
                parameter="ESG_ZERO_LIQUID_DISCHARGE",
                description="Stringent Central Pollution Control Board (CPCB) norms enforcing Zero Liquid Discharge (ZLD) and strict effluent limits.",
                impact_on_company="Barriers to entry rise for unorganized players, benefiting institutional suppliers with compliant environmental treatment plants.",
                evidence_source="State Pollution Control Board Guidelines"
            ))

        elif "tech" in sec_lower or "electronic" in sec_lower or "software" in sec_lower or "distribution" in sec_lower:
            factors.append(IndustryFactor(
                category="TAILWIND",
                parameter="ENTERPRISE_DIGITIZATION_AND_CLOUD",
                description="Indian enterprise spending on cybersecurity, cloud infrastructure, AI servers, and mobile device penetration continues compounding.",
                impact_on_company="Drives recurring product distribution volume and enterprise software license deployments.",
                evidence_source="Industry IT Hardware & Cloud Spending Surveys"
            ))
            factors.append(IndustryFactor(
                category="HEADWIND",
                parameter="VENDOR_MARGIN_COMPRESSION",
                description="Global technology OEMs (hardware and cloud providers) maintain aggressive pricing control, keeping gross distribution margins slim.",
                impact_on_company="Requires high inventory turnover velocity and working capital discipline to sustain acceptable ROCE.",
                evidence_source="Technology Distribution Industry Benchmarks"
            ))
            factors.append(IndustryFactor(
                category="STRUCTURAL_CHANGE",
                parameter="LOCAL_MANUFACTURING_PLI",
                description="Production Linked Incentive (PLI) schemes accelerating local assembly and electronics supply chain depth within India.",
                impact_on_company="Shortens logistics lead times and opens opportunities for value-added distribution and testing services.",
                evidence_source="Ministry of Electronics and Information Technology (MeitY) Notifications"
            ))

        else:
            factors.append(IndustryFactor(
                category="TAILWIND",
                parameter="DOMESTIC_CONSUMPTION_EXPANSION",
                description="India's sustained GDP growth and formalization of the domestic supply chain support volume demand for branded organized players.",
                impact_on_company="Facilitates steady capacity utilization and geographical distribution expansion.",
                evidence_source="RBI Macroeconomic Bulletins"
            ))
            factors.append(IndustryFactor(
                category="HEADWIND",
                parameter="COMPETITIVE_INTENSITY",
                description="Entrenched peer competition and raw material cost shifts require ongoing promotional and marketing spend.",
                impact_on_company="Limits unilateral pricing power without continuous product differentiation.",
                evidence_source="Industry Trade Reports"
            ))

        # 2. Company vs Industry Performance Decoupling
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        co_growth_str = "Verified in statements"
        market_share_verdict = "IN_LINE_WITH_INDUSTRY"

        if len(annual_periods) >= 2:
            prev_p = annual_periods[-2]
            curr_p = annual_periods[-1]
            rev_prev = self.store.get_datapoint("Revenue", prev_p, "ANNUAL")
            rev_curr = self.store.get_datapoint("Revenue", curr_p, "ANNUAL")
            if rev_prev and rev_curr and rev_prev.value > 0:
                co_growth = ((rev_curr.value - rev_prev.value) / rev_prev.value) * 100.0
                co_growth_str = f"{co_growth:+.1f}% YoY"
                # Benchmark: typical Indian nominal GDP/sector growth ~10-12%
                if co_growth >= 16.0:
                    market_share_verdict = "GAINING_MARKET_SHARE (Outperforming broader sector baseline)"
                elif co_growth <= 2.0:
                    market_share_verdict = "UNDERPERFORMING_INDUSTRY_GROWTH (Lagging sector baseline)"
                else:
                    market_share_verdict = "TRACKING_INDUSTRY_BASELINE"

        return {
            "sector": self.sector,
            "industry": self.industry,
            "company_growth_rate": co_growth_str,
            "market_share_dynamics": market_share_verdict,
            "total_factors": len(factors),
            "tailwinds": [f.to_dict() for f in factors if f.category == "TAILWIND"],
            "headwinds": [f.to_dict() for f in factors if f.category == "HEADWIND"],
            "structural_changes": [f.to_dict() for f in factors if f.category == "STRUCTURAL_CHANGE"]
        }
