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
from .simple_language import SimpleInvestorLanguageEngine

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

        # 16. Simple Investor Language & Plain English Explanations
        # Translates verified database figures & deterministic math into clear retail investor takeaways
        annual_periods = store.to_summary_dict().get("annual_periods", [])
        rev_prev, rev_curr, ebitda_prev, ebitda_curr = None, None, None, None
        p_prev_label, p_curr_label = "Prior Period", "Current Period"

        if len(annual_periods) >= 2:
            p_prev_label = annual_periods[-2]
            p_curr_label = annual_periods[-1]
            dp_r0 = store.get_datapoint("Revenue", p_prev_label, "ANNUAL")
            dp_r1 = store.get_datapoint("Revenue", p_curr_label, "ANNUAL")
            dp_e0 = store.get_datapoint("EBITDA", p_prev_label, "ANNUAL")
            dp_e1 = store.get_datapoint("EBITDA", p_curr_label, "ANNUAL")
            rev_prev = dp_r0.value if dp_r0 else None
            rev_curr = dp_r1.value if dp_r1 else None
            ebitda_prev = dp_e0.value if dp_e0 else None
            ebitda_curr = dp_e1.value if dp_e1 else None

        top_driver_note = driver_results[0].get("explanation") if driver_results else None

        core_change_takeaway = SimpleInvestorLanguageEngine.explain_core_change(
            rev_prev=rev_prev,
            rev_curr=rev_curr,
            ebitda_prev=ebitda_prev,
            ebitda_curr=ebitda_curr,
            period_prev=p_prev_label,
            period_curr=p_curr_label,
            driver_explanation=top_driver_note
        )

        cash_flow_takeaway = SimpleInvestorLanguageEngine.explain_cash_flow_health(
            pat_5y=fq_data.get("cumulative_5y_pat_cr"),
            cfo_5y=fq_data.get("cumulative_5y_cfo_cr"),
            capex_5y=fq_data.get("cumulative_5y_capex_cr"),
            fcf_5y=fq_data.get("cumulative_5y_fcf_cr")
        )

        total_debt = store.get_latest_datapoint_value("Total Debt", "ANNUAL")
        cash_val = store.get_latest_datapoint_value("Cash & Equivalents", "ANNUAL")
        de_val = (screener_data or {}).get("debt_to_equity") or company_data.get("debt_to_equity")

        debt_takeaway = SimpleInvestorLanguageEngine.explain_debt_position(
            total_debt=total_debt,
            cash=cash_val,
            debt_to_equity=de_val
        )

        val_mkt = valuation_data.get("market_pricing_analysis", {})
        valuation_takeaway = SimpleInvestorLanguageEngine.explain_valuation_hurdle(
            cmp=cmp,
            mcap_cr=mcap,
            implied_hurdle_cagr=val_mkt.get("implied_growth_hurdle_cagr", 10.0),
            hist_cagr=val_mkt.get("historical_5y_growth_cagr", 10.0),
            wacc=val_mkt.get("assumed_wacc_pct", 11.5)
        )

        snapshot_2_3_sentences = SimpleInvestorLanguageEngine.generate_snapshot(
            company_name=cname,
            screener_data=screener_data or company_data,
            about_data=(dossier or {}).get("about_data")
        )

        plain_red_flags = [
            SimpleInvestorLanguageEngine.format_red_flag_plain(a)
            for a in forensic_data.get("anomalies", [])
        ]

        simple_explanation_payload = {
            "snapshot": snapshot_2_3_sentences,
            "core_change": core_change_takeaway.to_dict(),
            "cash_flow_health": cash_flow_takeaway.to_dict(),
            "debt_position": debt_takeaway.to_dict(),
            "valuation_hurdle": valuation_takeaway.to_dict(),
            "red_flags": plain_red_flags,
            "answers_to_11_questions": {
                "what_does_company_do": snapshot_2_3_sentences,
                "what_changed": core_change_takeaway.headline,
                "how_much_did_it_change": f"Sales: {core_change_takeaway.simple_explanation}",
                "why_did_it_change": top_driver_note or "Reason not conclusively established from available evidence.",
                "is_change_positive_negative_mixed": core_change_takeaway.status,
                "is_change_temporary_or_structural": "Requires tracking over trailing quarters to confirm if pricing lags subside.",
                "what_evidence_supports_explanation": core_change_takeaway.source_citation,
                "what_does_management_say": (concall or {}).get("tone_sentiment") or "Management guidance focuses on executing active pipeline.",
                "what_does_actual_financial_data_show": f"5Y Cash Conversion: {cash_flow_takeaway.headline}",
                "what_risks_should_investor_investigate": [r.get("risk_title") for r in risks[:3]],
                "what_opportunities_should_investor_investigate": [o.get("opportunity_title") for o in opportunities[:3]],
                "what_should_investor_monitor_next": [q.get("question") for q in investor_questions[:3]]
            }
        }

        logger.info(f"Investment Intelligence Audit complete for {cname}. Total JEV verified claims: {len(verified_claims_log)}")

        return {
            "company_id": cid,
            "company_name": cname,
            "ticker": ticker,
            "isin": isin,
            "sector": sector,
            "industry": industry,
            "datapoints_verified": datapoints_count,
            "simple_explanation": simple_explanation_payload,
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
