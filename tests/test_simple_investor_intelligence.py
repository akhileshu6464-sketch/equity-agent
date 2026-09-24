"""
Unit Tests for Simple Investor Intelligence & Single Source of Financial Truth
(tests/test_simple_investor_intelligence.py)

Tests the fundamental architecture rules:
1. AI is NOT the database or source of financial truth.
2. Verified Database -> Deterministic Calculations -> Evidence -> Simple Investor Explanation.
3. Missing data outputs "Data unavailable", never guessed or estimated.
4. Banned financial jargon is cleaned and replaced with plain retail investor English.
5. Zero BUY/HOLD/SELL recommendation badges.
6. Epistemological status is strictly preserved (FACT vs CALCULATION vs INFERENCE).
"""

import unittest
from services.decision_engine.fundamental_store import FundamentalDataStore, FundamentalDatapoint
from services.decision_engine.simple_language import SimpleInvestorLanguageEngine, SimpleTakeaway
from services.decision_engine.coordinator import DecisionEngineCoordinator
from core.research_context import create_research_context
from calculations.growth import revenue_growth, yoy_change
from calculations.margins import margin_change_bps


class TestSimpleInvestorIntelligence(unittest.TestCase):

    def setUp(self):
        self.store = FundamentalDataStore(
            company_id="NSE:ASHOKA",
            ticker="ASHOKA.NS",
            exchange="NSE",
            isin="INE442H01029"
        )

    def test_example_from_user_prompt_exact_translation(self):
        """
        Tests the exact canonical example provided by the user:
        Database:
          Revenue FY24 = ₹1,000 Cr, Revenue FY25 = ₹1,200 Cr
          EBITDA FY24 = ₹180 Cr, EBITDA FY25 = ₹192 Cr
        Deterministic engine:
          Revenue Growth = 20%
          EBITDA Growth = 6.7%
          EBITDA Margin = 18% -> 16% (-200 bps)
        AI Explanation:
          "Sales increased 20.0%, but operating profit increased only 6.7%..."
        """
        # 1. Populate verified database
        self.store.add_datapoint("Revenue", "FY24", "ANNUAL", 1000.0, "INR_CR")
        self.store.add_datapoint("Revenue", "FY25", "ANNUAL", 1200.0, "INR_CR")
        self.store.add_datapoint("EBITDA", "FY24", "ANNUAL", 180.0, "INR_CR")
        self.store.add_datapoint("EBITDA", "FY25", "ANNUAL", 192.0, "INR_CR")

        # 2. Extract verified values from store (NOT from AI memory)
        dp_r0 = self.store.get_datapoint("Revenue", "FY24", "ANNUAL")
        dp_r1 = self.store.get_datapoint("Revenue", "FY25", "ANNUAL")
        dp_e0 = self.store.get_datapoint("EBITDA", "FY24", "ANNUAL")
        dp_e1 = self.store.get_datapoint("EBITDA", "FY25", "ANNUAL")

        self.assertIsNotNone(dp_r0)
        self.assertIsNotNone(dp_r1)
        self.assertIsNotNone(dp_e0)
        self.assertIsNotNone(dp_e1)

        # 3. Deterministic calculations in code
        calc_rg = yoy_change(dp_r1.value, dp_r0.value)
        calc_eg = yoy_change(dp_e1.value, dp_e0.value)

        self.assertAlmostEqual(calc_rg.value, 20.0, places=1)
        self.assertAlmostEqual(calc_eg.value, 6.7, places=1)

        # 4. Generate Simple Investor Explanation
        takeaway = SimpleInvestorLanguageEngine.explain_core_change(
            rev_prev=dp_r0.value,
            rev_curr=dp_r1.value,
            ebitda_prev=dp_e0.value,
            ebitda_curr=dp_e1.value,
            period_prev="FY24",
            period_curr="FY25"
        )

        self.assertIsInstance(takeaway, SimpleTakeaway)
        self.assertEqual(takeaway.status, "CONCERN")
        self.assertEqual(takeaway.direction, "DOWN")
        self.assertEqual(takeaway.epistemological_type, "CALCULATION")
        
        # Verify the numbers in explanation match verified database values
        self.assertIn("20.0%", takeaway.simple_explanation)
        self.assertIn("6.7%", takeaway.simple_explanation)
        self.assertIn("18.0%", takeaway.simple_explanation)
        self.assertIn("16.0%", takeaway.simple_explanation)
        self.assertIn("less profit from every ₹100 of sales", takeaway.simple_explanation)

    def test_missing_data_fails_closed_never_estimates(self):
        """
        Verifies that if verified data is unavailable, the engine outputs 'data unavailable'
        rather than guessing, estimating, or hallucinating synthetic figures.
        """
        # Store is empty for FY24/FY25
        takeaway = SimpleInvestorLanguageEngine.explain_core_change(
            rev_prev=None,
            rev_curr=None,
            ebitda_prev=None,
            ebitda_curr=None
        )

        self.assertEqual(takeaway.headline, "Revenue data unavailable for comparative periods")
        self.assertIn("unavailable", takeaway.simple_explanation.lower())
        self.assertEqual(takeaway.status, "WATCH")
        self.assertEqual(takeaway.numbers_used, [])

    def test_jargon_cleaning_and_plain_language_conversion(self):
        """
        Verifies that unnecessary institutional jargon is cleanly translated into everyday investor terms.
        """
        jargon_text = (
            "The company experienced adverse operating leverage and margin compression due to input cost inflation. "
            "Working capital intensity deteriorated while secular growth was offset by structural headwinds."
        )

        cleaned = SimpleInvestorLanguageEngine.clean_jargon(jargon_text)

        # Ensure prohibited jargon is removed
        self.assertNotIn("adverse operating leverage", cleaned.lower())
        self.assertNotIn("margin compression", cleaned.lower())
        self.assertNotIn("secular growth", cleaned.lower())
        self.assertNotIn("structural headwinds", cleaned.lower())

        # Ensure plain replacements exist
        self.assertIn("operating costs growing faster than sales", cleaned.lower())
        self.assertIn("making less profit from each ₹100 of sales", cleaned.lower())

    def test_cash_flow_health_conversion(self):
        """
        Tests plain English translation of cash flow conversion (CFO vs PAT).
        """
        # Case A: Good cash conversion
        good_takeaway = SimpleInvestorLanguageEngine.explain_cash_flow_health(
            pat_5y=500.0,
            cfo_5y=520.0,
            capex_5y=200.0,
            fcf_5y=320.0
        )
        self.assertEqual(good_takeaway.status, "GOOD")
        self.assertIn("converting into real bank cash", good_takeaway.headline)
        self.assertIn("104%", good_takeaway.simple_explanation)

        # Case B: Poor cash conversion (profits on paper only)
        poor_takeaway = SimpleInvestorLanguageEngine.explain_cash_flow_health(
            pat_5y=500.0,
            cfo_5y=200.0,
            capex_5y=150.0,
            fcf_5y=50.0
        )
        self.assertEqual(poor_takeaway.status, "CONCERN")
        self.assertIn("much less cash is entering the bank", poor_takeaway.headline)
        self.assertIn("40%", poor_takeaway.simple_explanation)

    def test_debt_solvency_plain_english(self):
        """
        Tests debt breakdown in simple retail investor language.
        """
        # Virtually debt free
        net_cash_takeaway = SimpleInvestorLanguageEngine.explain_debt_position(
            total_debt=100.0,
            cash=250.0,
            debt_to_equity=0.1
        )
        self.assertEqual(net_cash_takeaway.status, "GOOD")
        self.assertIn("virtually debt-free", net_cash_takeaway.headline)

        # High debt burden
        high_debt_takeaway = SimpleInvestorLanguageEngine.explain_debt_position(
            total_debt=1500.0,
            cash=100.0,
            debt_to_equity=1.85
        )
        self.assertEqual(high_debt_takeaway.status, "CONCERN")
        self.assertIn("high debt burden", high_debt_takeaway.headline.lower())

    def test_reverse_dcf_valuation_hurdle_no_buy_sell(self):
        """
        Tests Reverse DCF hurdle translation: verifies ZERO Buy/Hold/Sell advice is generated.
        """
        val_takeaway = SimpleInvestorLanguageEngine.explain_valuation_hurdle(
            cmp=350.0,
            mcap_cr=9800.0,
            implied_hurdle_cagr=18.5,
            hist_cagr=11.2,
            wacc=11.5
        )

        # Must not contain Buy, Hold, or Sell
        explanation = val_takeaway.simple_explanation.upper()
        self.assertNotIn("BUY", explanation)
        self.assertNotIn("HOLD", explanation)
        self.assertNotIn("SELL", explanation)

        # Must explain expectations vs history
        self.assertIn("18.5%", val_takeaway.simple_explanation)
        self.assertIn("11.2%", val_takeaway.simple_explanation)
        self.assertIn("past delivery", val_takeaway.headline)

    def test_coordinator_generates_simple_explanation_payload(self):
        """
        Verifies that DecisionEngineCoordinator includes simple_explanation payload
        adhering to the verified single-source-of-truth flow.
        """
        r_ctx = create_research_context("NSE:ASHOKA")
        coordinator = DecisionEngineCoordinator()

        sample_company_data = {
            "company_id": "NSE:ASHOKA",
            "clean_symbol": "ASHOKA",
            "company_name": "Ashoka Buildcon Limited",
            "current_price": 240.0,
            "market_cap_cr": 6700.0,
            "sector": "Industrials",
            "industry": "Engineering & Construction",
            "history_years": [
                {
                    "year": "FY23",
                    "revenue": 5000.0,
                    "ebitda": 550.0,
                    "operating_income": 450.0,
                    "net_income": 300.0,
                    "total_debt": 2200.0,
                    "cash_and_equivalents": 300.0,
                    "stockholders_equity": 3000.0
                },
                {
                    "year": "FY24",
                    "revenue": 6000.0,
                    "ebitda": 630.0,
                    "operating_income": 520.0,
                    "net_income": 360.0,
                    "total_debt": 2100.0,
                    "cash_and_equivalents": 350.0,
                    "stockholders_equity": 3300.0
                }
            ]
        }

        sample_screener_data = dict(sample_company_data)
        sample_screener_data["debt_to_equity"] = 0.63

        intel = coordinator.run_investment_intelligence_audit(
            company_data=sample_company_data,
            screener_data=sample_screener_data,
            dossier={},
            run_context=r_ctx
        )

        self.assertIn("simple_explanation", intel)
        simple_exp = intel["simple_explanation"]

        self.assertIn("snapshot", simple_exp)
        self.assertIn("core_change", simple_exp)
        self.assertIn("cash_flow_health", simple_exp)
        self.assertIn("debt_position", simple_exp)
        self.assertIn("valuation_hurdle", simple_exp)
        self.assertIn("answers_to_11_questions", simple_exp)

        # Verify exact math for Revenue & EBITDA
        # Rev: (6000 - 5000) / 5000 = +20.0%
        # EBITDA: (630 - 550) / 550 = +14.5%
        core = simple_exp["core_change"]
        self.assertEqual(core["status"], "CONCERN") # Because profit (14.5%) grew slower than sales (20.0%)
        self.assertIn("20.0%", core["simple_explanation"])
        self.assertIn("14.5%", core["simple_explanation"])


if __name__ == "__main__":
    unittest.main()
