"""
Unit Tests for Decision Engine Wiring with Deterministic Calculations
Verifies that ChangeDetectionEngine, FinancialQualityEngine, ValuationExpectationsEngine,
and ForensicInvestigationEngine consume pure-Python calculations from services.calculations.
"""

import unittest
from services.decision_engine.fundamental_store import FundamentalDataStore
from services.decision_engine.change_detector import ChangeDetectionEngine
from services.decision_engine.financial_quality import FinancialQualityEngine
from services.decision_engine.valuation_expectations import ValuationExpectationsEngine
from services.decision_engine.forensic_engine import ForensicInvestigationEngine


class TestDecisionEngineWiring(unittest.TestCase):

    def setUp(self):
        self.store = FundamentalDataStore(
            company_id="TEST_INC",
            ticker="TEST",
            exchange="NSE",
            isin="INE999A01019"
        )
        # Populate 3 years of multi-period fundamental data
        periods = [
            ("FY21", 1000.0, 200.0, 100.0, 90.0, 150.0, 120.0, 300.0, 50.0),
            ("FY22", 1200.0, 240.0, 130.0, 120.0, 180.0, 140.0, 280.0, 60.0),
            ("FY23", 1500.0, 330.0, 180.0, 170.0, 240.0, 170.0, 250.0, 80.0),
            ("FY24", 1950.0, 390.0, 210.0, 150.0, 360.0, 230.0, 350.0, 90.0),
        ]
        for p, rev, ebitda, pat, cfo, rec, inv, debt, cash in periods:
            self.store.add_datapoint("Revenue", p, "ANNUAL", rev, unit="INR_CR")
            self.store.add_datapoint("EBITDA", p, "ANNUAL", ebitda, unit="INR_CR")
            self.store.add_datapoint("EBITDA Margin", p, "ANNUAL", (ebitda / rev) * 100.0, unit="PERCENT")
            self.store.add_datapoint("PAT", p, "ANNUAL", pat, unit="INR_CR")
            self.store.add_datapoint("Operating Cash Flow", p, "ANNUAL", cfo, unit="INR_CR")
            self.store.add_datapoint("Capital Expenditures", p, "ANNUAL", 40.0, unit="INR_CR")
            self.store.add_datapoint("Free Cash Flow", p, "ANNUAL", cfo - 40.0, unit="INR_CR")
            self.store.add_datapoint("Receivables", p, "ANNUAL", rec, unit="INR_CR")
            self.store.add_datapoint("Inventory", p, "ANNUAL", inv, unit="INR_CR")
            self.store.add_datapoint("Total Debt", p, "ANNUAL", debt, unit="INR_CR")
            self.store.add_datapoint("Cash & Equivalents", p, "ANNUAL", cash, unit="INR_CR")
            self.store.add_datapoint("ROCE", p, "ANNUAL", 18.5, unit="PERCENT")
            self.store.add_datapoint("ROE", p, "ANNUAL", 16.0, unit="PERCENT")

    # -------------------------------------------------------------------------
    # 1. Change Detection Engine Wiring
    # -------------------------------------------------------------------------
    def test_change_detection_engine(self):
        engine = ChangeDetectionEngine(self.store)
        results = engine.detect_all_changes()

        self.assertIn("annual_changes", results)
        self.assertIn("divergence_alerts", results)
        self.assertIn("summary_trajectory", results)

        annual_changes = results["annual_changes"]
        rev_change = next((c for c in annual_changes if c["metric"] == "Revenue" and c["change_type"] == "YOY"), None)
        self.assertIsNotNone(rev_change)
        # FY23 (1500) -> FY24 (1950) = +30.0%
        self.assertAlmostEqual(rev_change["percentage_change"], 30.0)
        self.assertEqual(rev_change["direction"], "IMPROVING")

        # Receivables grew 1500->1950 (30%) vs Rec 240->360 (50%), spread = 20% -> triggers divergence
        rec_alert = next((a for a in results["divergence_alerts"] if a["type"] == "RECEIVABLES_OUTPACING_SALES"), None)
        self.assertIsNotNone(rec_alert)
        self.assertEqual(rec_alert["severity"], "HIGH")

    # -------------------------------------------------------------------------
    # 2. Financial Quality Engine Wiring
    # -------------------------------------------------------------------------
    def test_financial_quality_engine(self):
        fq_engine = FinancialQualityEngine(self.store)
        fq_data = fq_engine.evaluate_financial_quality()

        self.assertIn("cfo_to_pat_5y_pct", fq_data)
        self.assertIn("signals", fq_data)
        self.assertGreater(fq_data["cfo_to_pat_5y_pct"], 0.0)

        # Receivables stretch signal
        rec_signal = next((s for s in fq_data["signals"] if s["signal_type"] == "RECEIVABLES_STRETCH"), None)
        self.assertIsNotNone(rec_signal)
        self.assertEqual(rec_signal["status"], "VULNERABLE")

    # -------------------------------------------------------------------------
    # 3. Valuation Expectations Engine Wiring
    # -------------------------------------------------------------------------
    def test_valuation_expectations_engine(self):
        val_engine = ValuationExpectationsEngine(self.store)
        val_data = val_engine.evaluate_valuation_and_expectations(
            current_price=550.0,
            market_cap_cr=4500.0,
            pe_ratio=21.4,
            pb_ratio=3.5,
            peer_data=[{"name": "PeerA", "cmp": 300, "pe": 25.0, "mcap": 3000, "roce": 15.0}]
        )

        self.assertIn("company_valuation", val_data)
        self.assertIn("market_pricing_analysis", val_data)
        self.assertIn("peer_comparison_context", val_data)

        comp_val = val_data["company_valuation"]
        self.assertGreater(comp_val["ev_ebitda"], 0.0)
        self.assertGreater(comp_val["fcf_yield_pct"], 0.0)

        pricing = val_data["market_pricing_analysis"]
        self.assertGreater(pricing["implied_growth_hurdle_cagr"], 0.0)
        self.assertEqual(len(pricing["pricing_insights"]), 5)

    # -------------------------------------------------------------------------
    # 4. Forensic Investigation Engine Wiring
    # -------------------------------------------------------------------------
    def test_forensic_engine_wiring(self):
        forensic_engine = ForensicInvestigationEngine(self.store)
        gov_data = {
            "pledged_shares": 5000000.0,
            "total_promoter_shares": 20000000.0  # 25% pledge
        }
        res = forensic_engine.run_forensic_audit(governance_data=gov_data)

        self.assertIn("forensic_status", res)
        self.assertIn("anomalies", res)
        self.assertGreaterEqual(res["total_anomalies_flagged"], 1)

        # Check promoter encumbrance anomaly
        pledge_anomaly = next((a for a in res["anomalies"] if a["dimension"] == "PROMOTER_ENCUMBRANCE"), None)
        self.assertIsNotNone(pledge_anomaly)
        self.assertIn("25.0%", pledge_anomaly["observed_pattern"])


if __name__ == "__main__":
    unittest.main()
