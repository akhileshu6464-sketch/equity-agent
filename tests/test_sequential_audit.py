"""
Sequential Cross-Company Audit Contamination Test
Verifies sequential audit execution across multiple companies:
VINATIORGA -> REDINGTON -> ASHOKA -> HDFCBANK -> VINATIORGA
Ensures strict company isolation, zero cross-talk, zero leaked context, and complete clean state resets.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.company_identity import resolve_canonical_identity
from core.research_context import create_research_context
from services.decision_engine import (
    FundamentalDataStore,
    JevVerificationLayer,
    AnalyticalClaim,
    DecisionEngineCoordinator
)


class TestSequentialCompanyAudit(unittest.TestCase):
    """Verifies that sequential company runs maintain 100% data isolation."""

    def test_sequential_run_isolation(self):
        sequence = [
            ("VINATIORGA", "NSE:VINATIORGA", "INE410B01037"),
            ("REDINGTON", "NSE:REDINGTON", "INE891401026"),
            ("ASHOKA", "NSE:ASHOKA", "INE442H01029"),
            ("HDFCBANK", "NSE:HDFCBANK", "INE040A01034"),
            ("VINATIORGA", "NSE:VINATIORGA", "INE410B01037"),
        ]

        coordinator = DecisionEngineCoordinator()
        cached_results = []

        for ticker, expected_cid, expected_isin in sequence:
            ident = resolve_canonical_identity(ticker)
            self.assertEqual(ident.company_id, expected_cid)
            self.assertEqual(ident.isin, expected_isin)

            ctx = create_research_context(ident)
            self.assertEqual(ctx.company_id, expected_cid)

            # Construct mock audited company data for this ticker
            mock_data = {
                "symbol": f"{ticker}.NS",
                "clean_symbol": ticker,
                "company_name": ident.company_name,
                "current_price": 500.0,
                "market_cap_cr": 10000.0,
                "pe_ratio": 25.0,
                "pb_ratio": 4.0,
                "roce_pct": 18.0,
                "roe_pct": 15.0,
                "pl_rows": [
                    {"Metric": "Sales", "Mar 2023": "1,000", "Mar 2024": "1,150"},
                    {"Metric": "Operating Profit", "Mar 2023": "180", "Mar 2024": "210"},
                    {"Metric": "Net Profit", "Mar 2023": "120", "Mar 2024": "145"},
                ],
                "cashflow_rows": [
                    {"Metric": "Cash from Operating Activity", "Mar 2023": "130", "Mar 2024": "160"},
                    {"Metric": "Fixed Assets Purchased", "Mar 2023": "-40", "Mar 2024": "-50"},
                ]
            }

            result = coordinator.run_investment_intelligence_audit(
                company_data=mock_data,
                screener_data=mock_data,
                dossier={},
                run_context=ctx
            )

            # Assert company identity integrity
            self.assertEqual(result["company_id"], expected_cid)
            self.assertTrue(ticker in result["ticker"])
            self.assertEqual(result["isin"], expected_isin)

            # Store result to check for leaks
            cached_results.append((ticker, expected_cid, result))

        # Check cross-run contamination
        for idx, (ticker, cid, res) in enumerate(cached_results):
            # The decision map and changes must only refer to this ticker/company
            changes = res.get("changes_detected", {}).get("annual_changes", [])
            for c in changes:
                self.assertEqual(c.get("company_id"), cid, f"Contamination in run {idx}: expected {cid}, got {c.get('company_id')}")

            # JEV verification log must match current company
            jev_log = res.get("jev_verification_log", [])
            for entry in jev_log:
                if "company_id" in entry:
                    self.assertEqual(entry["company_id"], cid)

        # Specifically verify that the 5th run (VINATIORGA) has ZERO contamination from run 4 (HDFCBANK)
        first_vinati = cached_results[0][2]
        final_vinati = cached_results[4][2]

        self.assertEqual(first_vinati["company_id"], final_vinati["company_id"])
        self.assertEqual(final_vinati["company_id"], "NSE:VINATIORGA")
        self.assertNotIn("HDFCBANK", final_vinati["company_name"])
        self.assertNotIn("ASHOKA", final_vinati["company_name"])
        self.assertNotIn("REDINGTON", final_vinati["company_name"])

    def test_jev_cross_company_rejection(self):
        """Verify JEV verification layer actively rejects a claim from a foreign company."""
        jev = JevVerificationLayer()
        vinati_ident = resolve_canonical_identity("VINATIORGA")
        vinati_ctx = create_research_context(vinati_ident)

        # Claim with Ashoka company_id submitted to Vinati context
        foreign_claim = AnalyticalClaim(
            company_id="NSE:ASHOKA",
            company_name="Ashoka Buildcon Limited",
            claim="Revenue grew by 15% in EPC highway projects.",
            evidence=["Reported 15% revenue growth in FY24"],
            period="FY24",
            source=["Ashoka FY24 Annual Report"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[15.0]
        )

        decision = jev.verify_claim(foreign_claim, active_company_id=vinati_ctx.company_id)
        self.assertEqual(decision.status, "REJECT")
        self.assertFalse(decision.identity_verified)
        self.assertIn("CROSS_COMPANY_CONTAMINATION", decision.review_notes)


if __name__ == "__main__":
    unittest.main()
