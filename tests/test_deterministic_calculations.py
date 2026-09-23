"""
Unit Tests for Deterministic Financial Calculation Engine
Verifies all pure Python accounting, valuation, and financial formulas.
Validates zero-denominator handling, negative starting values, sign-change logic,
audit reproducibility, and strict absence of hardcoded fallbacks.
"""

import unittest
import math
from calculations.growth import revenue_growth, yoy_change, qoq_change, cagr, cfo_growth
from calculations.margins import ebitda_margin, ebit_margin, pat_margin, gross_margin, margin_change_bps
from calculations.profitability import roe, roce, roic, asset_turnover
from calculations.cashflow import cfo_to_pat, free_cash_flow, fcf_yield, cash_flow_reconciliation
from calculations.leverage import debt_to_equity, net_debt, net_debt_to_ebitda, interest_coverage
from calculations.working_capital import receivable_days, inventory_days, payable_days, cash_conversion_cycle
from calculations.valuation import pe_ratio, pb_ratio, market_capitalization, enterprise_value, ev_to_ebitda, ev_to_sales
from calculations.shareholding import promoter_holding_change, promoter_pledge_percentage
from calculations.validation import validate_calculation, reconcile_reported_vs_calculated, detect_sign_change
from calculations.audit import CalculationAuditRegistry
from calculations.normalization import normalize_to_inr, format_inr_crores, format_percentage


class TestDeterministicCalculationEngine(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. Growth Calculations
    # -------------------------------------------------------------------------
    def test_revenue_growth_normal(self):
        res = revenue_growth(120.0, 100.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, 20.0)
        self.assertEqual(res.formula, "((current_revenue - previous_revenue) / abs(previous_revenue)) * 100")

    def test_revenue_growth_zero_or_none(self):
        res_zero = revenue_growth(100.0, 0.0)
        self.assertIsNone(res_zero.value)
        self.assertEqual(res_zero.status, "NOT_APPLICABLE")

        res_none = revenue_growth(100.0, None)
        self.assertIsNone(res_none.value)
        self.assertEqual(res_none.status, "INSUFFICIENT_DATA")

    def test_cagr_normal(self):
        # 100 -> 121 in 2 years = 10% CAGR
        res = cagr(100.0, 121.0, 2.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, 10.0, places=2)

    def test_cagr_negative_or_zero_base(self):
        # Section 17: For negative starting values, do NOT force CAGR. Return NOT_APPLICABLE.
        res_neg = cagr(-100.0, 120.0, 2.0)
        self.assertIsNone(res_neg.value)
        self.assertEqual(res_neg.status, "NOT_APPLICABLE")

        res_zero = cagr(0.0, 100.0, 3.0)
        self.assertIsNone(res_zero.value)
        self.assertEqual(res_zero.status, "NOT_APPLICABLE")

    def test_cfo_growth_sign_change(self):
        # Section 38 & 55: Never present misleading 200% growth on negative to positive sign change
        res = cfo_growth(200.0, -100.0)
        self.assertTrue(res.is_valid)
        self.assertIn("Turnaround to positive", res.notes)

    # -------------------------------------------------------------------------
    # 2. Margins and Basis-Point Shifts
    # -------------------------------------------------------------------------
    def test_ebitda_margin(self):
        res = ebitda_margin(500.0, 2500.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, 20.0)

    def test_margin_zero_revenue(self):
        res = ebitda_margin(500.0, 0.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

    def test_margin_change_bps(self):
        # Section 16: 22.5% -> 19.8% = -2.7% = -270 bps
        res = margin_change_bps(19.8, 22.5)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, -270.0)

        # 18.0% -> 20.0% = +200 bps
        res_exp = margin_change_bps(20.0, 18.0)
        self.assertAlmostEqual(res_exp.value, 200.0)

    # -------------------------------------------------------------------------
    # 3. Profitability Ratios (ROE, ROCE, ROIC)
    # -------------------------------------------------------------------------
    def test_roe_with_average_equity(self):
        # PAT = 150, Beg Eq = 900, End Eq = 1100 -> Avg Eq = 1000 -> ROE = 15%
        res = roe(150.0, 900.0, 1100.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, 15.0)

    def test_roe_zero_equity(self):
        res = roe(100.0, 0.0, 0.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

    def test_roce(self):
        # EBIT = 200, Cap Employed = 1000 -> ROCE = 20%
        res = roce(200.0, 1000.0, 1000.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, 20.0)

    # -------------------------------------------------------------------------
    # 4. Cash Flow & Quality Ratios
    # -------------------------------------------------------------------------
    def test_cfo_to_pat(self):
        # CFO = 900, PAT = 1000 -> 0.90x
        res = cfo_to_pat(900.0, 1000.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, 0.90)

    def test_cfo_to_pat_negative_pat(self):
        res = cfo_to_pat(100.0, -50.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

    def test_free_cash_flow_sign_normalization(self):
        # CFO = 500, Capex entered as negative -200 or positive 200 -> FCF should be 300
        res1 = free_cash_flow(500.0, 200.0)
        self.assertAlmostEqual(res1.value, 300.0)

        res2 = free_cash_flow(500.0, -200.0)
        self.assertAlmostEqual(res2.value, 300.0)

    # -------------------------------------------------------------------------
    # 5. Leverage and Solvency
    # -------------------------------------------------------------------------
    def test_net_debt(self):
        # Total Debt = 500, Cash = 200 -> Net Debt = 300
        res = net_debt(500.0, 200.0)
        self.assertAlmostEqual(res.value, 300.0)

        # Net cash positive
        res_cash = net_debt(200.0, 500.0)
        self.assertAlmostEqual(res_cash.value, -300.0)

    def test_net_debt_to_ebitda_negative_ebitda(self):
        # Section 26: If EBITDA <= 0, return None/N/A (never default to 5.0)
        res = net_debt_to_ebitda(300.0, -50.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

    def test_interest_coverage_zero_interest(self):
        # Section 27: If interest <= 0, return None/N/A (never default to 50.0)
        res = interest_coverage(200.0, 0.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

    # -------------------------------------------------------------------------
    # 6. Working Capital Days
    # -------------------------------------------------------------------------
    def test_inventory_days_uses_cogs(self):
        # Section 32: Inventory Days = (Inventory / COGS) * 365. Never divide by revenue!
        res = inventory_days(200.0, 1000.0, 365.0)
        self.assertAlmostEqual(res.value, 73.0)

        # If COGS is missing, must return INSUFFICIENT_DATA (not substitute revenue)
        res_missing = inventory_days(200.0, None)
        self.assertIsNone(res_missing.value)
        self.assertEqual(res_missing.status, "INSUFFICIENT_DATA")

    def test_cash_conversion_cycle(self):
        # CCC = DSO (45) + DIO (60) - DPO (35) = 70 days
        res = cash_conversion_cycle(45.0, 60.0, 35.0)
        self.assertAlmostEqual(res.value, 70.0)

    # -------------------------------------------------------------------------
    # 7. Valuation Multiples
    # -------------------------------------------------------------------------
    def test_pe_ratio_negative_eps(self):
        # Section 19: If EPS <= 0, return None/N/A. Do not produce negative P/E!
        res = pe_ratio(500.0, -10.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

        res_pos = pe_ratio(500.0, 25.0)
        self.assertAlmostEqual(res_pos.value, 20.0)

    def test_ev_to_ebitda_negative_ebitda(self):
        # Section 47: If EBITDA <= 0, return None/N/A
        res = ev_to_ebitda(1000.0, -50.0)
        self.assertIsNone(res.value)
        self.assertEqual(res.status, "NOT_APPLICABLE")

    # -------------------------------------------------------------------------
    # 8. Shareholding & Governance
    # -------------------------------------------------------------------------
    def test_promoter_holding_change(self):
        # Section 50: 52% -> 51% = -1 percentage point, relative change = -1.92%
        res = promoter_holding_change(51.0, 52.0)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.value, -1.0)
        self.assertIn("Absolute change: -1.00 percentage points", res.notes)
        self.assertIn("Relative change: -1.92%", res.notes)

    # -------------------------------------------------------------------------
    # 9. Validation, Cross-Check Reconciliation & Sign Changes
    # -------------------------------------------------------------------------
    def test_reconcile_reported_vs_calculated(self):
        # Section 62: Tolerance check
        reconciled = reconcile_reported_vs_calculated(100.0, 101.0, tolerance_pct=2.0)
        self.assertFalse(reconciled["reconciliation_required"])

        discrepancy = reconcile_reported_vs_calculated(100.0, 110.0, tolerance_pct=2.0)
        self.assertTrue(discrepancy["reconciliation_required"])
        self.assertIn("CALCULATION RECONCILIATION REQUIRED", discrepancy["message"])

    def test_detect_sign_change(self):
        # Section 55: -100 -> +100
        sc = detect_sign_change(100.0, -100.0, "Operating Cash Flow")
        self.assertTrue(sc["has_sign_change"])
        self.assertEqual(sc["direction"], "TURNAROUND_POSITIVE")

    # -------------------------------------------------------------------------
    # 10. Audit Record Reproducibility
    # -------------------------------------------------------------------------
    def test_audit_registry(self):
        # Section 60: Every calculation stores its formula, inputs, period, company, and result
        reg = CalculationAuditRegistry()
        calc = ebitda_margin(5000000000.0, 25000000000.0)
        record = reg.record_calculation(
            company_id="XYZ",
            metric="EBITDA_MARGIN",
            period="FY2026",
            calc_result=calc,
            formatted_result="20.00%",
            source_ids=["source_123", "source_124"]
        )

        retrieved = reg.get_record("XYZ", "EBITDA_MARGIN", "FY2026")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.formula, "(ebitda / revenue) * 100")
        self.assertEqual(retrieved.result, 20.0)
        self.assertEqual(retrieved.inputs["ebitda"], 5000000000.0)
        self.assertEqual(retrieved.inputs["revenue"], 25000000000.0)

    # -------------------------------------------------------------------------
    # 11. Banking & NBFC Deterministic Calculations
    # -------------------------------------------------------------------------
    def test_banking_calculations(self):
        from calculations.banking import (
            net_interest_margin,
            cost_to_income_ratio,
            gross_npa_ratio,
            net_npa_ratio,
            provision_coverage_ratio,
            crar,
            tier1_ratio,
            casa_ratio,
            credit_cost_ratio,
        )
        # NIM: NII = 400, Earning Assets = 10000 -> 4.0%
        nim_res = net_interest_margin(400.0, 10000.0)
        self.assertTrue(nim_res.is_valid)
        self.assertAlmostEqual(nim_res.value, 4.0)

        # Cost to Income: OpEx = 450, Total Income = 1000 -> 45.0%
        c2i_res = cost_to_income_ratio(450.0, 1000.0)
        self.assertTrue(c2i_res.is_valid)
        self.assertAlmostEqual(c2i_res.value, 45.0)

        # GNPA: Gross NPAs = 250, Gross Advances = 10000 -> 2.5%
        gnpa_res = gross_npa_ratio(250.0, 10000.0)
        self.assertTrue(gnpa_res.is_valid)
        self.assertAlmostEqual(gnpa_res.value, 2.5)

        # Missing inputs must return NOT_DISCLOSED (zero hallucination)
        nim_missing = net_interest_margin(None, 10000.0)
        self.assertIsNone(nim_missing.value)
        self.assertEqual(nim_missing.status, "NOT_DISCLOSED")

    # -------------------------------------------------------------------------
    # 12. Services.calculations Parity
    # -------------------------------------------------------------------------
    def test_services_calculations_parity(self):
        import services.calculations as sc
        import calculations as c
        self.assertEqual(sc.pe_ratio, c.pe_ratio)
        self.assertEqual(sc.ebitda_margin, c.ebitda_margin)
        self.assertEqual(sc.net_interest_margin, c.net_interest_margin)
        self.assertEqual(sc.cagr, c.cagr)

    # -------------------------------------------------------------------------
    # 13. FundamentalDataStore SQLite Persistence
    # -------------------------------------------------------------------------
    def test_fundamental_store_sqlite_persistence(self):
        import tempfile
        import os
        from services.decision_engine.fundamental_store import FundamentalDataStore
        from services.financial_data import FinancialDataService

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            temp_db = tf.name

        try:
            # Initialize tables
            fds = FinancialDataService(db_path=temp_db)

            store1 = FundamentalDataStore(company_id="TEST_CO", ticker="TEST", exchange="NSE", isin="INE000000001")
            store1.add_datapoint("Revenue", "FY24", "ANNUAL", 1500.0, unit="INR_CR")
            store1.add_datapoint("PAT", "FY24", "ANNUAL", 180.0, unit="INR_CR")
            store1.save_to_sqlite(db_path=temp_db)

            # Load into fresh store
            store2 = FundamentalDataStore(company_id="TEST_CO", ticker="TEST")
            loaded_count = store2.load_from_sqlite(db_path=temp_db)
            self.assertEqual(loaded_count, 2)
            rev_dp = store2.get_datapoint("Revenue", "FY24", "ANNUAL")
            self.assertIsNotNone(rev_dp)
            self.assertEqual(rev_dp.value, 1500.0)
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)

    # -------------------------------------------------------------------------
    # 14. CalculationAuditRegistry SQLite Persistence
    # -------------------------------------------------------------------------
    def test_audit_registry_sqlite_persistence(self):
        import tempfile
        import os
        from calculations.audit import CalculationAuditRegistry
        from services.financial_data import FinancialDataService

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            temp_db = tf.name

        try:
            # Initialize tables
            FinancialDataService(db_path=temp_db)

            reg1 = CalculationAuditRegistry()
            calc = ebitda_margin(200.0, 1000.0)
            reg1.record_calculation("INFY", "EBITDA_MARGIN", "FY24", calc, "20.00%")
            reg1.save_to_sqlite(db_path=temp_db)

            reg2 = CalculationAuditRegistry()
            loaded = reg2.load_from_sqlite(db_path=temp_db, company_id="INFY")
            self.assertEqual(loaded, 1)
            rec = reg2.get_record("INFY", "EBITDA_MARGIN", "FY24")
            self.assertIsNotNone(rec)
            self.assertEqual(rec.result, 20.0)
            self.assertEqual(rec.formula, "(ebitda / revenue) * 100")
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)


if __name__ == "__main__":
    unittest.main()

