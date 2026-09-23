"""
Unit Test Suite: Research Beast Investment Intelligence & Decision-Support Engine
Verifies:
1. Fundamental Data Store: Deterministic extraction, multi-period indexing, auditable metadata.
2. Change Detection Engine: YoY, QoQ, 5Y CAGR, margin basis point shifts, divergence alerts.
3. Driver Analysis Engine: Causal driver decomposition (Verified, Possible, Unknown).
4. Financial Quality Engine: 5-year cumulative CFO/PAT conversion and receivables divergence diagnostics.
5. Forensic Investigation Engine: Non-accusatory anomaly identification with alternative explanations.
6. Valuation Expectations: Reverse DCF implied hurdle and Fact/Inference/Assumption separation.
7. JEV Verification Layer: Hard company identity check, claim verification, epistemological classification.
8. Decision Engine Coordinator: End-to-end investment intelligence audit across canonical equities.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.company_identity import resolve_canonical_identity
from core.research_context import create_research_context
from services.financial_data import FinancialDataService
from services.decision_engine import (
    FundamentalDataStore,
    ChangeDetectionEngine,
    DriverAnalysisEngine,
    FinancialQualityEngine,
    ForensicInvestigationEngine,
    ValuationExpectationsEngine,
    SignalSystemEngine,
    InvestorQuestionsEngine,
    InvestorDecisionFramework,
    JevVerificationLayer,
    AnalyticalClaim,
    DecisionEngineCoordinator
)


class TestInvestmentIntelligenceEngine(unittest.TestCase):
    """Verifies all components of the Research Beast Decision Support Engine."""

    def setUp(self):
        self.identity = resolve_canonical_identity("REDINGTON")
        self.context = create_research_context(self.identity)
        self.store = FundamentalDataStore(
            company_id=self.context.company_id,
            ticker=self.context.ticker,
            exchange=self.context.exchange,
            isin=self.context.isin
        )

        # Mock multi-year audited fundamental history
        self.mock_company_data = {
            "symbol": "REDINGTON.NS",
            "clean_symbol": "REDINGTON",
            "company_name": "Redington Limited",
            "sector": "Technology",
            "industry": "Electronic Components",
            "current_price": 235.0,
            "market_cap_cr": 18500.0,
            "pe_ratio": 14.5,
            "pb_ratio": 2.3,
            "history_years": [
                {
                    "year": "FY20",
                    "revenue": 47000.0,
                    "ebitda": 1100.0,
                    "operating_income": 950.0,
                    "net_income": 520.0,
                    "eps": 6.8,
                    "total_debt": 1800.0,
                    "cash_and_equivalents": 850.0,
                    "operating_cash_flow": 1200.0,
                    "capital_expenditures": -80.0,
                    "free_cash_flow": 1120.0,
                    "receivables": 4500.0,
                    "inventory": 2900.0,
                    "stockholders_equity": 4200.0,
                    "total_assets": 14000.0
                },
                {
                    "year": "FY21",
                    "revenue": 56000.0,
                    "ebitda": 1350.0,
                    "operating_income": 1200.0,
                    "net_income": 750.0,
                    "eps": 9.6,
                    "total_debt": 1500.0,
                    "cash_and_equivalents": 950.0,
                    "operating_cash_flow": 1400.0,
                    "capital_expenditures": -90.0,
                    "free_cash_flow": 1310.0,
                    "receivables": 5200.0,
                    "inventory": 3400.0,
                    "stockholders_equity": 4800.0,
                    "total_assets": 16000.0
                },
                {
                    "year": "FY22",
                    "revenue": 62000.0,
                    "ebitda": 1650.0,
                    "operating_income": 1480.0,
                    "net_income": 1280.0,
                    "eps": 16.4,
                    "total_debt": 1200.0,
                    "cash_and_equivalents": 1100.0,
                    "operating_cash_flow": 1800.0,
                    "capital_expenditures": -110.0,
                    "free_cash_flow": 1690.0,
                    "receivables": 6100.0,
                    "inventory": 3900.0,
                    "stockholders_equity": 5600.0,
                    "total_assets": 18500.0
                },
                {
                    "year": "FY23",
                    "revenue": 79000.0,
                    "ebitda": 2100.0,
                    "operating_income": 1890.0,
                    "net_income": 1390.0,
                    "eps": 17.8,
                    "total_debt": 1400.0,
                    "cash_and_equivalents": 1250.0,
                    "operating_cash_flow": 1600.0,
                    "capital_expenditures": -130.0,
                    "free_cash_flow": 1470.0,
                    "receivables": 8400.0,
                    "inventory": 5200.0,
                    "stockholders_equity": 6500.0,
                    "total_assets": 23000.0
                },
                {
                    "year": "FY24",
                    "revenue": 89000.0,
                    "ebitda": 2050.0,
                    "operating_income": 1780.0,
                    "net_income": 1220.0,
                    "eps": 15.6,
                    "total_debt": 1750.0,
                    "cash_and_equivalents": 1300.0,
                    "operating_cash_flow": 1100.0,
                    "capital_expenditures": -150.0,
                    "free_cash_flow": 950.0,
                    "receivables": 11200.0,
                    "inventory": 6400.0,
                    "stockholders_equity": 7300.0,
                    "total_assets": 27000.0
                }
            ]
        }

    def test_fundamental_store_auditable_tagging(self):
        """1. Every datapoint must contain canonical metadata and auditable sources."""
        count = self.store.populate_from_raw_sources(self.mock_company_data)
        self.assertGreater(count, 30)

        dp = self.store.get_datapoint("Revenue", "FY24", "ANNUAL")
        self.assertIsNotNone(dp)
        self.assertEqual(dp.company_id, self.context.company_id)
        self.assertEqual(dp.isin, "INE891401026")
        self.assertEqual(dp.value, 89000.0)
        self.assertEqual(dp.unit, "INR_CR")
        self.assertIn("Audited", dp.source)

    def test_change_detection_and_divergence_triggers(self):
        """2. Detects YoY, margin bps shifts, and flags divergence triggers."""
        self.store.populate_from_raw_sources(self.mock_company_data)
        engine = ChangeDetectionEngine(self.store)
        res = engine.detect_all_changes()

        changes = res["annual_changes"]
        alerts = res["divergence_alerts"]

        # Check Revenue YoY change
        rev_chg = next((c for c in changes if c["metric"] == "Revenue" and c["change_type"] == "YOY"), None)
        self.assertIsNotNone(rev_chg)
        self.assertAlmostEqual(rev_chg["percentage_change"], 12.7, delta=0.2)

        # Check EBITDA margin contraction
        margin_chg = next((c for c in changes if c["metric"] == "EBITDA Margin" and c["change_type"] == "YOY"), None)
        self.assertIsNotNone(margin_chg)
        self.assertEqual(margin_chg["direction"], "CONTRACTING")

        # Receivables grew from 8,400 to 11,200 (+33.3%) vs Sales (+12.7%) -> Must trigger divergence alert
        rec_alert = next((a for a in alerts if a["type"] == "RECEIVABLES_OUTPACING_SALES"), None)
        self.assertIsNotNone(rec_alert)
        self.assertEqual(rec_alert["severity"], "HIGH")

    def test_driver_analysis_decomposition(self):
        """3. Decomposes changes into verified or possible drivers with evidence."""
        self.store.populate_from_raw_sources(self.mock_company_data)
        chg_engine = ChangeDetectionEngine(self.store)
        chg_data = chg_engine.detect_all_changes()

        driver_engine = DriverAnalysisEngine(self.store)
        drivers = driver_engine.analyze_drivers(
            changes=chg_data["annual_changes"],
            primary_disclosures={"regulatory_announcements": "Commissioned cloud distribution center and expanded Apple enterprise footprint."},
            concall_data={"revenue_growth_guidance": "Management reported 12% top-line volume growth."}
        )

        self.assertGreater(len(drivers), 0)
        rev_driver = next((d for d in drivers if d["metric"] == "Revenue"), None)
        self.assertIsNotNone(rev_driver)
        self.assertIn(rev_driver["driver_classification"], ["VERIFIED_DRIVER", "POSSIBLE_DRIVER"])
        self.assertTrue(len(rev_driver["causation_caveat"]) > 10)

    def test_financial_quality_and_cash_conversion(self):
        """4. Evaluates 5-year cumulative CFO/PAT conversion and receivables diagnostics."""
        self.store.populate_from_raw_sources(self.mock_company_data)
        fq_engine = FinancialQualityEngine(self.store)
        fq_data = fq_engine.evaluate_financial_quality()

        self.assertIsNotNone(fq_data["cfo_to_pat_5y_pct"])
        self.assertGreater(fq_data["cfo_to_pat_5y_pct"], 50.0)
        self.assertTrue(len(fq_data["signals"]) > 0)

        # Check that signals contain why it matters, explanations, and what to investigate
        sig = fq_data["signals"][0]
        self.assertTrue(len(sig["why_it_matters"]) > 10)
        self.assertTrue(len(sig["possible_explanations"]) > 0)
        self.assertTrue(len(sig["alternative_explanations"]) > 0)
        self.assertTrue(len(sig["what_to_investigate"]) > 0)

    def test_forensic_engine_non_accusatory_standards(self):
        """5. Scans 20+ dimensions without alleging fraud; provides alternate explanations."""
        self.store.populate_from_raw_sources(self.mock_company_data)
        forensic_engine = ForensicInvestigationEngine(self.store)
        forensic_data = forensic_engine.run_forensic_audit()

        anomalies = forensic_data["anomalies"]
        self.assertGreater(len(anomalies), 0)

        for anom in anomalies:
            # Strictly verify non-accusatory framing
            self.assertNotIn("fraud", anom["anomaly_title"].lower())
            self.assertNotIn("fraud", anom["observed_pattern"].lower())
            self.assertTrue(len(anom["possible_explanation"]) > 10)
            self.assertTrue(len(anom["alternative_explanation"]) > 10)
            self.assertTrue(len(anom["investor_due_diligence_step"]) > 10)

    def test_valuation_expectations_reverse_dcf(self):
        """6. Calculates Reverse DCF growth hurdle and categorizes Fact vs Inference vs Assumption."""
        self.store.populate_from_raw_sources(self.mock_company_data)
        val_engine = ValuationExpectationsEngine(self.store)
        val_res = val_engine.evaluate_valuation_and_expectations(
            current_price=235.0,
            market_cap_cr=18500.0,
            pe_ratio=14.5,
            pb_ratio=2.3
        )

        mkt = val_res["market_pricing_analysis"]
        self.assertGreater(mkt["implied_growth_hurdle_cagr"], 0.0)
        self.assertGreater(mkt["historical_5y_growth_cagr"], 0.0)

        insights = mkt["pricing_insights"]
        categories = set(i["category"] for i in insights)
        self.assertIn("FACT", categories)
        self.assertIn("INFERENCE", categories)
        self.assertIn("ASSUMPTION", categories)

    def test_jev_verification_layer(self):
        """7. Tests JEV verification gate: company isolation, evidence validation, and classification."""
        jev = JevVerificationLayer()

        # Valid Claim
        valid_claim = AnalyticalClaim(
            company_id=self.context.company_id,
            company_name=self.context.company_name,
            claim="Revenue expanded 12.7% YoY to ₹89,000 Cr in FY24.",
            evidence=["Audited FY24 Annual Financial Statements report consolidated sales of ₹89,000 Cr."],
            period="FY24",
            source=["BSE/NSE Annual Disclosures"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[89000.0, 12.7]
        )

        res_valid = jev.verify_claim(valid_claim, self.context.company_id, verified_numbers=[89000.0, 12.7])
        self.assertEqual(res_valid.status, "PASS")
        self.assertTrue(res_valid.identity_verified)
        self.assertTrue(res_valid.evidence_supported)

        # Contaminated Company ID Claim -> MUST REJECT
        contaminated_claim = AnalyticalClaim(
            company_id="NSE:ASHOKA",  # Wrong company ID
            company_name="Ashoka Buildcon Limited",
            claim="Highway EPC milestones reached NHAI targets.",
            evidence=["BSE Disclosures"],
            period="FY24",
            source=["BSE Disclosures"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[]
        )
        res_contam = jev.verify_claim(contaminated_claim, self.context.company_id)
        self.assertEqual(res_contam.status, "REJECT")
        self.assertFalse(res_contam.identity_verified)
        self.assertIn("CRITICAL REJECTION", res_contam.review_notes)

    def test_coordinator_end_to_end_audit(self):
        """8. Runs full DecisionEngineCoordinator pipeline verifying all 15 intelligence outputs."""
        coordinator = DecisionEngineCoordinator()
        audit_res = coordinator.run_investment_intelligence_audit(
            company_data=self.mock_company_data,
            screener_data=None,
            dossier=None,
            run_context=self.context
        )

        self.assertEqual(audit_res["company_id"], self.context.company_id)
        self.assertEqual(audit_res["isin"], self.context.isin)
        self.assertIn("decision_map", audit_res)
        self.assertIn("changes_detected", audit_res)
        self.assertIn("driver_analysis", audit_res)
        self.assertIn("financial_quality", audit_res)
        self.assertIn("forensic_audit", audit_res)
        self.assertIn("valuation_and_expectations", audit_res)
        self.assertIn("investor_investigation_questions", audit_res)
        self.assertIn("jev_verification_log", audit_res)

        # Verify dynamic investor questions were generated
        questions = audit_res["investor_investigation_questions"]
        self.assertGreater(len(questions), 0)
        self.assertTrue(len(questions[0]["question"]) > 15)

        # Verify JEV verification log ran
        jev_log = audit_res["jev_verification_log"]
        self.assertGreater(len(jev_log), 0)
        self.assertTrue(all(item["status"] in ["PASS", "REVIEW", "REJECT"] for item in jev_log))


if __name__ == "__main__":
    unittest.main()
