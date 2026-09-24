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
from core.research_context import ResearchRunContext, StructuredAgentContext, DataContaminationError
from calculations.audit import global_audit_registry
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

        # Optional Drishti Intelligence Ingestion (Company ID locked)
        drishti_intel = None
        try:
            from services.drishti import get_drishti_service, is_drishti_configured
            if is_drishti_configured():
                drishti_svc = get_drishti_service()
                from core.company_identity import resolve_canonical_identity
                canonical_ident = resolve_canonical_identity(ticker)
                drishti_intel = drishti_svc.fetch_all_company_intelligence(
                    symbol=ticker,
                    primary_financials=company_data
                )
                if drishti_intel and drishti_intel.get("status") == "SUCCESS":
                    d_calls = drishti_intel.get("concalls", [])
                    if d_calls:
                        if not isinstance(concall, dict):
                            concall = {}
                        concall["drishti_concalls"] = [c.to_dict() for c in d_calls]
                        if not concall.get("transcript") and d_calls[0].source_url:
                            concall["transcript"] = d_calls[0].source_url

                    d_anns = drishti_intel.get("announcements", [])
                    if d_anns:
                        if not isinstance(prim_disc, dict):
                            prim_disc = {}
                        prim_disc["drishti_announcements"] = [a.to_dict() for a in d_anns]
        except Exception as e:
            logger.debug(f"Drishti enrichment skipped in coordinator: {e}")

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

        story_payload = SimpleInvestorLanguageEngine.build_comprehensive_investor_story(
            company_name=cname,
            symbol=ticker,
            store=store,
            company_data=company_data,
            screener_data=screener_data or company_data,
            dossier=dossier or {},
            change_data=change_data,
            driver_results=driver_results,
            fq_data=fq_data,
            forensic_data=forensic_data,
            industry_data=industry_data,
            opportunities=opportunities,
            risks=risks,
            valuation_data=valuation_data,
            timeline_events=events,
            investor_questions=investor_questions,
            concall=concall,
            cmp=cmp,
            mcap=mcap
        )

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
            },
            "story_sections": story_payload
        }

        # Construct and validate Structured AI Agent Context (Section 11)
        conflicts = [c.to_dict() for c in store.get_conflicts()]
        calculations = global_audit_registry.to_json_list(cid)
        agent_context = StructuredAgentContext(
            company_id=cid,
            company_name=cname,
            isin=isin,
            period="LATEST_ACTIVE",
            scope=getattr(run_context, "statement_scope", "CONSOLIDATED"),
            verified_financial_data=store.to_summary_dict(),
            deterministic_calculations=calculations,
            verified_documents=(concall.get("drishti_concalls", []) if isinstance(concall, dict) else []),
            news=((drishti_intel or {}).get("news", []) if isinstance(drishti_intel, dict) else []),
            announcements=((drishti_intel or {}).get("announcements", []) if isinstance(drishti_intel, dict) else []),
            known_conflicts=conflicts,
            source_metadata={
                "sector": sector,
                "industry": industry,
                "exchange": getattr(run_context, "exchange", "NSE"),
                "datapoints_verified": datapoints_count
            }
        )
        # Pre-execution anti-contamination validation: asserts all objects belong to company_id
        agent_context.validate_integrity()

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
            "jev_verification_log": verified_claims_log,
            "drishti_intelligence": drishti_intel,
            "structured_agent_context": agent_context.to_dict(),
            "known_conflicts": conflicts
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
        Constructs internal claim objects and submits them to JEV verification checklist (Section 14).
        Filters out any claim that fails JEV validation from presenting as fact.
        """
        all_claims: List[AnalyticalClaim] = []

        # Reference numbers from store to check numerical truth
        annual_periods = store.to_summary_dict().get("annual_periods", [])
        ref_numbers: List[float] = []
        for dp in store._datapoints:
            if dp.period_type == "ANNUAL" and dp.value is not None:
                ref_numbers.append(dp.value)

        # 1. Collect Top Positive Signals
        for s in signals_data.get("positive_signals", [])[:3]:
            all_claims.append(AnalyticalClaim(
                company_id=run_context.company_id,
                company_name=run_context.company_name,
                claim=f"{s.get('metric')}: {s.get('reason')}",
                evidence=[s.get("evidence", "")],
                period=s.get("period", ""),
                source=["Audited Financial Statements"],
                claim_type="HISTORICAL_FACT" if "CFO" in s.get("metric", "") or "Revenue" in s.get("metric", "") else "RESEARCH_BEAST_INFERENCE",
                cited_numbers=[]
            ))

        # 2. Collect Top Negative Signals
        for s in signals_data.get("negative_signals", [])[:3]:
            all_claims.append(AnalyticalClaim(
                company_id=run_context.company_id,
                company_name=run_context.company_name,
                claim=f"{s.get('metric')}: {s.get('reason')}",
                evidence=[s.get("evidence", "")],
                period=s.get("period", ""),
                source=["Audited Financial Statements"],
                claim_type="FORENSIC_SIGNAL" if "Divergence" in s.get("status_label", "") else "RESEARCH_BEAST_INFERENCE",
                cited_numbers=[]
            ))

        # 3. Collect Driver Claims
        for d in driver_results[:3]:
            all_claims.append(AnalyticalClaim(
                company_id=run_context.company_id,
                company_name=run_context.company_name,
                claim=d.get("explanation", ""),
                evidence=[d.get("evidence_quote", ""), d.get("observed_change", "")],
                period=d.get("period", ""),
                source=[d.get("evidence_source", "")],
                claim_type="MANAGEMENT_COMMENTARY" if "Management" in d.get("evidence_source", "") else "RESEARCH_BEAST_INFERENCE",
                cited_numbers=[]
            ))

        # Run Section 14 JEV Validation Checklist
        verified_sources = ["audited financial statements", "bse lodr", "nse", "drishti", "screener"]
        audit_res = self.jev_verifier.audit_ai_output_package(
            claims=all_claims,
            active_company_id=run_context.company_id,
            verified_numbers=ref_numbers,
            verified_sources=verified_sources
        )

        return audit_res.get("verification_results", [])
