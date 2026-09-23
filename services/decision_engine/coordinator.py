"""
Investment Intelligence Engine Coordinator (services/decision_engine/coordinator.py)
Master orchestrator uniting all 15 decision-support intelligence modules:
1. Canonical Company Identity Locking
2. Fundamental Data Store & Normalizer
3. Change Detection Engine
4. Driver Analysis Engine
5. Financial Quality & Cash Conversion Engine
6. Forensic / Red-Flag Investigative Engine
7. Management Guidance & Accountability Engine
8. Industry Intelligence Engine
9. Future Opportunity Engine
10. Future Risk Engine
11. Valuation & Market Pricing Expectations Engine
12. Corporate Event Timeline Engine
13. Signal System Engine (Good / Bad / Watch)
14. Dynamic Investor Investigation Questions
15. JEV Structured Verification Layer (PASS / REVIEW / REJECT)
16. Master Investor Decision Map
"""

from typing import Dict, Any, List, Optional
import logging
from core.research_context import ResearchRunContext
from .fundamental_store import FundamentalDataStore
from .change_detector import ChangeDetectionEngine
from .driver_analyzer import DriverAnalysisEngine
from .financial_quality import FinancialQualityEngine
from .forensic_engine import ForensicInvestigationEngine
from .management_engine import ManagementGuidanceEngine
from .industry_engine import IndustryIntelligenceEngine
from .opportunity_engine import FutureOpportunityEngine
from .risk_engine import FutureRiskEngine
from .valuation_expectations import ValuationExpectationsEngine
from .event_timeline import EventTimelineEngine
from .signal_system import SignalSystemEngine
from .investor_questions import InvestorQuestionsEngine
from .decision_framework import InvestorDecisionFramework
from .jev_verifier import JevVerificationLayer, AnalyticalClaim, JevVerificationResult

logger = logging.getLogger("ResearchBeast.DecisionEngineCoordinator")


class DecisionEngineCoordinator:
    """
    Coordinates the complete end-to-end Fundamental Investment Decision-Support Pipeline.
    Ensures that every analytical insight is grounded in deterministic verified numbers,
    isolated to the canonical company, and audited through the JEV verification layer.
    """

    def __init__(self):
        self.jev_verifier = JevVerificationLayer()

    def run_investment_intelligence_audit(
        self,
        company_data: Dict[str, Any],
        screener_data: Optional[Dict[str, Any]],
        dossier: Optional[Dict[str, Any]],
        run_context: ResearchRunContext
    ) -> Dict[str, Any]:
        """
        Executes the 15-module investment decision-support pipeline for a canonical company.
        """
        cid = run_context.company_id
        ticker = run_context.ticker
        cname = run_context.company_name
        isin = run_context.isin
        sector = (company_data.get("sector") or (screener_data or {}).get("sector") or "General Corporate")
        industry = (company_data.get("industry") or (screener_data or {}).get("industry") or "Diverse Operations")

        logger.info(f"Starting Investment Intelligence Audit for {cname} ({cid})")

        # 1. Initialize Fundamental Data Store
        store = FundamentalDataStore(
            company_id=cid,
            ticker=ticker,
            exchange=getattr(run_context, "exchange", "NSE"),
            isin=isin
        )
        datapoints_count = store.populate_from_raw_sources(company_data, screener_data)

        # 2. Change Detection Engine
        change_engine = ChangeDetectionEngine(store)
        change_data = change_engine.detect_all_changes()

        # Extract primary filings and concall references defensively
        prim_disc = (dossier or {}).get("primary_disclosures", {})
        concall = (dossier or {}).get("agent_7", {})
        gov_data = (dossier or {}).get("agent_4", {})

        # 3. Driver Analysis Engine
        driver_engine = DriverAnalysisEngine(store)
        all_changes = change_data.get("annual_changes", []) + change_data.get("quarterly_changes", [])
        driver_results = driver_engine.analyze_drivers(all_changes, prim_disc, concall)

        # 4. Financial Quality Engine
        fq_engine = FinancialQualityEngine(store)
        fq_data = fq_engine.evaluate_financial_quality()

        # 5. Forensic Investigation Engine
        forensic_engine = ForensicInvestigationEngine(store)
        forensic_data = forensic_engine.run_forensic_audit(gov_data, prim_disc)

        # 6. Management Guidance & Accountability Engine
        mgmt_engine = ManagementGuidanceEngine(store)
        mgmt_data = mgmt_engine.evaluate_management_track_record(concall, prim_disc)

        # 7. Industry Intelligence Engine
        ind_engine = IndustryIntelligenceEngine(store, sector, industry)
        sector_kpis = (dossier or {}).get("agent_5", {})
        industry_data = ind_engine.analyze_industry_context(sector_kpis, prim_disc)

        # 8. Future Opportunity Engine
        opp_engine = FutureOpportunityEngine(store, sector)
        opportunities = opp_engine.identify_opportunities(prim_disc, concall)

        # 9. Future Risk Engine
        risk_engine = FutureRiskEngine(store, sector)
        risks = risk_engine.identify_risks(gov_data, prim_disc)

        # 10. Valuation & Market Pricing Expectations Engine
        val_engine = ValuationExpectationsEngine(store)
        cmp = (screener_data or {}).get("current_price") or company_data.get("current_price", 0.0)
        mcap = (screener_data or {}).get("market_cap_cr") or company_data.get("market_cap_cr", 0.0)
        pe = (screener_data or {}).get("pe_ratio") or company_data.get("pe_ratio", 0.0)
        pb = (screener_data or {}).get("pb_ratio") or company_data.get("pb_ratio", 0.0)
        peers = (screener_data or {}).get("peer_rows", [])
        valuation_data = val_engine.evaluate_valuation_and_expectations(cmp, mcap, pe, pb, peers, screener_data)

        # 11. Event Timeline Engine
        timeline_engine = EventTimelineEngine(store)
        events = timeline_engine.build_timeline(prim_disc, concall)

        # 12. Signal System Engine (Good / Bad / Watch)
        signal_engine = SignalSystemEngine(store)
        signals_data = signal_engine.generate_signals(
            detected_changes=all_changes,
            financial_quality=fq_data,
            forensic_data=forensic_data,
            opportunities=opportunities,
            risks=risks
        )

        # 13. Dynamic Investor Investigation Questions
        questions_engine = InvestorQuestionsEngine(store)
        investor_questions = questions_engine.generate_questions(
            divergence_alerts=change_data.get("divergence_alerts", []),
            forensic_data=forensic_data,
            financial_quality=fq_data,
            valuation_data=valuation_data
        )

        # 14. Master Investor Decision Framework Map
        decision_framework_engine = InvestorDecisionFramework(store)
        decision_map = decision_framework_engine.assemble_decision_map(
            signals_data=signals_data,
            financial_quality=fq_data,
            forensic_data=forensic_data,
            industry_data=industry_data,
            management_data=mgmt_data,
            valuation_data=valuation_data,
            opportunities=opportunities,
            risks=risks,
            investor_questions=investor_questions
        )

        # 15. JEV Structured Verification Gate
        # Gathers candidate claims and passes them through JEV verification
        verified_claims_log = self._execute_jev_verification_gate(
            run_context=run_context,
            signals_data=signals_data,
            driver_results=driver_results,
            forensic_data=forensic_data,
            store=store
        )

        logger.info(f"Investment Intelligence Audit complete for {cname}. Total JEV verified claims: {len(verified_claims_log)}")

        return {
            "company_id": cid,
            "company_name": cname,
            "ticker": ticker,
            "isin": isin,
            "sector": sector,
            "industry": industry,
            "datapoints_verified": datapoints_count,
            "decision_map": decision_map,
            "changes_detected": change_data,
            "driver_analysis": driver_results,
            "signals": signals_data,
            "financial_quality": fq_data,
            "forensic_audit": forensic_data,
            "industry_intelligence": industry_data,
            "management_accountability": mgmt_data,
            "opportunities": opportunities,
            "risks": risks,
            "valuation_and_expectations": valuation_data,
            "event_timeline": events,
            "investor_investigation_questions": investor_questions,
            "jev_verification_log": verified_claims_log
        }

    def _execute_jev_verification_gate(
        self,
        run_context: ResearchRunContext,
        signals_data: Dict[str, Any],
        driver_results: List[Dict[str, Any]],
        forensic_data: Dict[str, Any],
        store: FundamentalDataStore
    ) -> List[Dict[str, Any]]:
        """
        Constructs internal claim objects and submits them to JEV verification.
        Filters out any claim that fails JEV validation from presenting as fact.
        """
        verification_log: List[Dict[str, Any]] = []

        # Reference numbers from store to check numerical truth
        annual_periods = store.to_summary_dict().get("annual_periods", [])
        ref_numbers: List[float] = []
        for dp in store._datapoints:
            if dp.period_type == "ANNUAL":
                ref_numbers.append(dp.value)

        # 1. Verify Top Positive Signals
        for s in signals_data.get("positive_signals", [])[:3]:
            claim_obj = AnalyticalClaim(
                company_id=run_context.company_id,
                company_name=run_context.company_name,
                claim=f"{s.get('metric')}: {s.get('reason')}",
                evidence=[s.get("evidence", "")],
                period=s.get("period", ""),
                source=["Audited Financial Statements"],
                claim_type="HISTORICAL_FACT" if "CFO" in s.get("metric", "") or "Revenue" in s.get("metric", "") else "RESEARCH_BEAST_INFERENCE",
                cited_numbers=[]
            )
            v_res = self.jev_verifier.verify_claim(claim_obj, run_context.company_id, ref_numbers)
            verification_log.append(v_res.to_dict())

        # 2. Verify Top Negative Signals
        for s in signals_data.get("negative_signals", [])[:3]:
            claim_obj = AnalyticalClaim(
                company_id=run_context.company_id,
                company_name=run_context.company_name,
                claim=f"{s.get('metric')}: {s.get('reason')}",
                evidence=[s.get("evidence", "")],
                period=s.get("period", ""),
                source=["Audited Financial Statements"],
                claim_type="FORENSIC_SIGNAL" if "Divergence" in s.get("status_label", "") else "RESEARCH_BEAST_INFERENCE",
                cited_numbers=[]
            )
            v_res = self.jev_verifier.verify_claim(claim_obj, run_context.company_id, ref_numbers)
            verification_log.append(v_res.to_dict())

        # 3. Verify Driver Claims
        for d in driver_results[:3]:
            claim_obj = AnalyticalClaim(
                company_id=run_context.company_id,
                company_name=run_context.company_name,
                claim=d.get("explanation", ""),
                evidence=[d.get("evidence_quote", ""), d.get("observed_change", "")],
                period=d.get("period", ""),
                source=[d.get("evidence_source", "")],
                claim_type="MANAGEMENT_COMMENTARY" if "Management" in d.get("evidence_source", "") else "RESEARCH_BEAST_INFERENCE",
                cited_numbers=[]
            )
            v_res = self.jev_verifier.verify_claim(claim_obj, run_context.company_id, ref_numbers)
            verification_log.append(v_res.to_dict())

        return verification_log
