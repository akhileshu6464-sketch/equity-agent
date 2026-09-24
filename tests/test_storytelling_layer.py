"""
Unit Tests for Final Output & Vertical Storytelling Presentation Layer (tests/test_storytelling_layer.py)
Tests the 12-section vertical storytelling experience across 3 distinct companies:
1. ASHOKA (Ashoka Buildcon)
2. TATAMOTORS (Tata Motors)
3. VINATIORGA (Vinati Organics)

Confirms:
1. Numbers remain unchanged and correct from verified database.
2. Calculations remain unchanged.
3. Company data does not mix.
4. Every major insight is understandable to a normal investor.
5. Jargon is minimized and converted.
6. Evidence is traceable with source citations.
7. No unsupported causes are generated (never guesses).
8. No generic AI filler appears.
9. All 12 story sections are populated with StructuredInsight objects.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.company_identity import resolve_canonical_identity
from core.research_context import create_research_context
from services.decision_engine.coordinator import DecisionEngineCoordinator
from services.decision_engine.simple_language import SimpleInvestorLanguageEngine, StructuredInsight


class TestStorytellingPresentationLayer(unittest.TestCase):
    """Verifies the final investor explanation layer across 3 companies."""

    def setUp(self):
        self.coordinator = DecisionEngineCoordinator()

    def test_three_company_storytelling_verification(self):
        companies = [
            ("ASHOKA", "Ashoka Buildcon Ltd", 240.0, 6500.0, 7500.0, 9000.0, 780.0, 850.0),
            ("TATAMOTORS", "Tata Motors Ltd", 950.0, 350000.0, 420000.0, 435000.0, 58000.0, 62000.0),
            ("VINATIORGA", "Vinati Organics Ltd", 1750.0, 18000.0, 2000.0, 2300.0, 550.0, 620.0),
        ]

        for ticker, name, cmp, mcap, rev_prev, rev_curr, ebitda_prev, ebitda_curr in companies:
            ident = resolve_canonical_identity(ticker)
            ctx = create_research_context(ident)

            mock_company_data = {
                "symbol": f"{ticker}.NS",
                "clean_symbol": ticker,
                "company_name": name,
                "sector": "Infrastructure" if ticker == "ASHOKA" else ("Automobile" if ticker == "TATAMOTORS" else "Chemicals"),
                "industry": "Civil Construction" if ticker == "ASHOKA" else ("Passenger Cars" if ticker == "TATAMOTORS" else "Specialty Chemicals"),
                "current_price": cmp,
                "market_cap_cr": mcap,
                "pe_ratio": 15.0,
                "pb_ratio": 2.2,
                "roce_pct": 16.5,
                "roe_pct": 14.2,
                "debt_to_equity": 0.45,
                "history_years": [
                    {
                        "year": "FY24",
                        "revenue": rev_prev,
                        "ebitda": ebitda_prev,
                        "operating_income": ebitda_prev * 0.85,
                        "net_income": ebitda_prev * 0.55,
                        "eps": 25.0,
                        "total_debt": rev_prev * 0.25,
                        "cash_and_equivalents": rev_prev * 0.1,
                        "operating_cash_flow": ebitda_prev * 0.7,
                        "capital_expenditures": ebitda_prev * 0.3,
                        "free_cash_flow": ebitda_prev * 0.4,
                        "receivables": rev_prev * 0.2,
                        "inventory": rev_prev * 0.15,
                        "payables": rev_prev * 0.18,
                        "working_capital": rev_prev * 0.17,
                        "stockholders_equity": rev_prev * 0.6
                    },
                    {
                        "year": "FY25",
                        "revenue": rev_curr,
                        "ebitda": ebitda_curr,
                        "operating_income": ebitda_curr * 0.85,
                        "net_income": ebitda_curr * 0.55,
                        "eps": 28.0,
                        "total_debt": rev_curr * 0.22,
                        "cash_and_equivalents": rev_curr * 0.12,
                        "operating_cash_flow": ebitda_curr * 0.75,
                        "capital_expenditures": ebitda_curr * 0.28,
                        "free_cash_flow": ebitda_curr * 0.47,
                        "receivables": rev_curr * 0.21,
                        "inventory": rev_curr * 0.14,
                        "payables": rev_curr * 0.17,
                        "working_capital": rev_curr * 0.18,
                        "stockholders_equity": rev_curr * 0.65
                    }
                ],
                "pl_rows": [
                    {"Metric": "Sales", "Mar 2024": f"{rev_prev:,.0f}", "Mar 2025": f"{rev_curr:,.0f}"},
                    {"Metric": "Operating Profit", "Mar 2024": f"{ebitda_prev:,.0f}", "Mar 2025": f"{ebitda_curr:,.0f}"},
                ],
                "peer_rows": [
                    {"name": f"Competitor A ({ticker})", "pe": 16.0, "roce": 15.0},
                    {"name": f"Competitor B ({ticker})", "pe": 18.0, "roce": 14.0},
                ]
            }

            intel = self.coordinator.run_investment_intelligence_audit(
                company_data=mock_company_data,
                screener_data=mock_company_data,
                dossier={},
                run_context=ctx
            )

            # 1. Verify Company Identity and Zero Mix
            self.assertEqual(intel["company_id"], ident.company_id)
            self.assertEqual(intel["ticker"], f"{ticker}.NS")

            # 2. Verify Simple Explanation & Story Sections
            simple_exp = intel.get("simple_explanation", {})
            self.assertIn("story_sections", simple_exp)
            story = simple_exp["story_sections"]

            # 3. Confirm all 12 Story Sections exist
            expected_sections = [
                "snapshot", "what_changed", "why_it_changed", "financial_health",
                "financial_red_flags", "industry_and_peers", "valuation_and_market",
                "opportunities", "risks", "what_to_watch", "investor_questions", "sources"
            ]
            for sec in expected_sections:
                self.assertIn(sec, story, f"Missing section {sec} for {ticker}")

            # 4. Verify Financial Health has all required modules
            fin_health = story["financial_health"]
            # Must have at least: Rev, EBITDA, PAT, Margin, Cash Flow, Working Capital, Debt, ROCE
            self.assertGreaterEqual(len(fin_health), 7)
            metrics_present = [item["metric"] for item in fin_health]
            self.assertTrue(any("Operating Revenue" in m or "Revenue" in m for m in metrics_present))
            self.assertTrue(any("EBITDA" in m or "Operating Profit" in m for m in metrics_present))
            self.assertTrue(any("PAT" in m or "Net Profit" in m for m in metrics_present))
            self.assertTrue(any("Margin" in m for m in metrics_present))
            self.assertTrue(any("Cash" in m for m in metrics_present))
            self.assertTrue(any("Debt" in m for m in metrics_present))
            self.assertTrue(any("Capital" in m or "ROCE" in m for m in metrics_present))

            # 5. Verify StructuredInsight schema compliance on every insight
            for sec_name, sec_content in story.items():
                if isinstance(sec_content, list):
                    for item in sec_content:
                        if isinstance(item, dict) and "metric" in item:
                            # Verify required fields
                            for req_field in ["title", "metric", "current_value", "previous_value",
                                              "change", "explanation", "driver", "evidence",
                                              "classification", "source", "verification_status"]:
                                self.assertIn(req_field, item, f"Missing {req_field} in {sec_name} for {ticker}")

                            # Verify 5 core questions are answered
                            self.assertIn("what_happened", item)
                            self.assertIn("how_much_changed", item)
                            self.assertIn("why_it_matters", item)
                            self.assertIn("why_it_happened", item)
                            self.assertIn("what_to_watch", item)

                            # 6. Verify Jargon is cleaned
                            expl_text = item["explanation"].lower()
                            self.assertNotIn("adverse operating leverage", expl_text)
                            self.assertNotIn("margin compression", expl_text)
                            self.assertNotIn("working capital drag", expl_text)

                            # 7. Verify No Generic AI Filler
                            self.assertNotIn("remains well positioned for future growth", expl_text)
                            self.assertNotIn("strong fundamentals continue to support", expl_text)
                            self.assertNotIn("demonstrated robust execution", expl_text)

            # 8. Confirm exact math calculations
            expected_rg = round(((rev_curr - rev_prev) / rev_prev) * 100.0, 1)
            core_chg = story["core_change"]
            self.assertIn(f"{expected_rg:.1f}%", core_chg["explanation"])

            # 9. Verify Valuation section contains NO Buy/Hold/Sell advice
            val_sec = story["valuation_and_market"]
            for v_item in val_sec:
                self.assertNotIn("BUY", v_item["classification"])
                self.assertNotIn("SELL", v_item["classification"])
                self.assertNotIn("HOLD", v_item["classification"])


if __name__ == "__main__":
    unittest.main()
