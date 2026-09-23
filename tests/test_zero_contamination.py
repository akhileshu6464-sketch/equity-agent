"""
Comprehensive Adversarial Test Suite: Zero Company Data Contamination (tests/test_zero_contamination.py)
Validates:
1. Complete isolation across company switches (Ashoka -> Tata Motors -> Vinati -> Redington -> HDFC Bank).
2. Fail-closed rejection of missing or ambiguous company identities.
3. RAG document and chunk boundary enforcement.
4. Peer data quarantine from primary financial statements.
5. Strict scoping of calculation audit queries.
6. JEV decision layer rejection of cross-company claims.
7. Fact-checking verifier universal foreign-entity purging.
8. Unification of historical Tata Motors aliases without bifurcation.
"""

import os
import sys
import unittest
import sqlite3
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.company_identity import resolve_canonical_identity, CompanyIdentity, CANONICAL_ALIASES
from core.research_context import (
    ResearchRunContext,
    create_research_context,
    DataContaminationError,
    EntityRole,
    assert_company_boundary,
    validate_everything_belongs_to
)
from services.screener_engine import ScreenerEngine
from services.financial_data import FinancialDataService
from services.decision_engine.fundamental_store import FundamentalDataStore, FundamentalDatapoint
from services.rag_engine import CompanyRAGEngine
from calculations.audit import CalculationAuditRegistry
from agents.verifier import FactCheckingVerifier
from services.decision_engine.jev_verifier import JevVerificationLayer, AnalyticalClaim


class TestZeroCompanyContamination(unittest.TestCase):
    """Rigorous adversarial test suite verifying absolute zero cross-company data contamination."""

    def setUp(self):
        self.temp_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_contamination.db"))
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Test 1: Ashoka Buildcon -> Tata Motors Switch
    # -------------------------------------------------------------------------
    def test_ashoka_to_tatamotors_switch(self):
        """Switching from Ashoka Buildcon to Tata Motors must strictly isolate state."""
        ctx_ashoka = create_research_context("ASHOKA")
        ctx_tata = create_research_context("TATAMOTORS")

        self.assertEqual(ctx_ashoka.company_id, "NSE:ASHOKA")
        self.assertEqual(ctx_tata.company_id, "NSE:TATAMOTORS")

        # Ingest simulated Ashoka dataset
        ashoka_data = {
            "company_id": ctx_ashoka.company_id,
            "isin": ctx_ashoka.isin,
            "entity_role": "PRIMARY_COMPANY",
            "company_name": ctx_ashoka.company_name,
            "current_price": 220.0,
            "market_cap_cr": 6000.0,
            "pl_rows": [
                {"period": "FY24", "company_id": ctx_ashoka.company_id, "sales": 8000.0, "net_profit": 500.0}
            ]
        }

        # Assert Ashoka data validates against Ashoka context
        assert_company_boundary(ashoka_data, ctx_ashoka.company_id)

        # Assert Ashoka data triggers DataContaminationError if evaluated under Tata Motors context
        with self.assertRaises(DataContaminationError):
            assert_company_boundary(ashoka_data, ctx_tata.company_id)

    # -------------------------------------------------------------------------
    # Test 2: Tata Motors -> Ashoka Buildcon Switch
    # -------------------------------------------------------------------------
    def test_tatamotors_to_ashoka_switch(self):
        """Switching from Tata Motors to Ashoka Buildcon must not leave residual Tata data."""
        ctx_tata = create_research_context("Tata Motors")
        ctx_ashoka = create_research_context("Ashoka Buildcon")

        tata_record = {
            "company_id": ctx_tata.company_id,
            "isin": ctx_tata.isin,
            "entity_role": "PRIMARY_COMPANY",
            "clean_symbol": "TATAMOTORS.NS"
        }

        with self.assertRaises(DataContaminationError):
            ctx_ashoka.assert_same_company(tata_record["company_id"])

        with self.assertRaises(DataContaminationError):
            assert_company_boundary(tata_record, ctx_ashoka.company_id)

    # -------------------------------------------------------------------------
    # Test 3: Multi-Company Sequential Switch (5 Stocks)
    # -------------------------------------------------------------------------
    def test_multi_company_switch_isolation(self):
        """Sequential switching across 5 stocks must retain zero cross-contamination."""
        sequence = ["VINATIORGA", "REDINGTON", "ASHOKA", "HDFCBANK", "TATAMOTORS"]
        contexts = [create_research_context(s) for s in sequence]

        mock_session_state = {}
        for ctx in contexts:
            # Simulate app.py session state switch
            mock_session_state["active_company_id"] = ctx.company_id
            mock_session_state["active_symbol"] = ctx.nse_symbol
            mock_session_state[f"screener_data:{ctx.company_id}"] = {
                "company_id": ctx.company_id,
                "isin": ctx.isin,
                "entity_role": "PRIMARY_COMPANY"
            }

            # Verify active company data
            active_data = mock_session_state[f"screener_data:{ctx.company_id}"]
            assert_company_boundary(active_data, ctx.company_id)

            # Verify all previous companies are completely distinct
            for other_ctx in contexts:
                if other_ctx.company_id != ctx.company_id:
                    with self.assertRaises(DataContaminationError):
                        assert_company_boundary(active_data, other_ctx.company_id)

    # -------------------------------------------------------------------------
    # Test 4: Missing Company Identity Fails Closed
    # -------------------------------------------------------------------------
    def test_missing_company_id_fails_closed(self):
        """Empty, unknown, or ambiguous company inputs must fail closed."""
        with self.assertRaises(ValueError):
            resolve_canonical_identity("")

        with self.assertRaises(ValueError):
            resolve_canonical_identity("   ")

        with self.assertRaises(ValueError):
            # Nonexistent stock query
            resolve_canonical_identity("NON_EXISTENT_XYZ_UNKNOWN_STOCK_12345")

    # -------------------------------------------------------------------------
    # Test 5: Foreign Document Chunk Injection into RAG Fails
    # -------------------------------------------------------------------------
    def test_foreign_document_chunk_injection_fails(self):
        """Storing or retrieving foreign company chunks must trigger DataContaminationError."""
        rag = CompanyRAGEngine(db_path=self.temp_db_path)
        ctx_ashoka = create_research_context("ASHOKA")
        ctx_tata = create_research_context("TATAMOTORS")

        # Attempt to store document with mismatched company_id in kwargs
        with self.assertRaises(DataContaminationError):
            rag.store_document_with_chunks(
                run_context=ctx_ashoka,
                document_id="doc_rogue_1",
                document_type="ANNUAL_REPORT",
                content="Tata Motors commercial vehicle deliveries grew by 15%.",
                company_id=ctx_tata.company_id
            )

    # -------------------------------------------------------------------------
    # Test 6: Foreign Peer Injection into Primary Store Fails
    # -------------------------------------------------------------------------
    def test_foreign_peer_injection_into_primary_store_fails(self):
        """Attempting to add a PEER entity into FundamentalDataStore must raise DataContaminationError."""
        store = FundamentalDataStore(company_id="NSE:ASHOKA", ticker="ASHOKA.NS")

        with self.assertRaises(DataContaminationError):
            store.add_datapoint(
                metric="Revenue",
                period="FY24",
                period_type="ANNUAL",
                value=5000.0,
                entity_role="PEER"
            )

        # Attempting to add FundamentalDatapoint with different company_id
        foreign_dp = FundamentalDatapoint(
            company_id="NSE:TATAMOTORS",
            ticker="TATAMOTORS.NS",
            exchange="NSE",
            isin="INE155A01022",
            metric="Revenue",
            period="FY24",
            period_type="ANNUAL",
            value=400000.0,
            entity_role="PRIMARY_COMPANY"
        )
        with self.assertRaises(DataContaminationError):
            store.add_datapoint_object(foreign_dp)

    # -------------------------------------------------------------------------
    # Test 7: Calculation Audit Load Requires company_id
    # -------------------------------------------------------------------------
    def test_calculation_audit_load_requires_company_id(self):
        """CalculationAuditRegistry.load_from_sqlite() requires company_id to prevent unscoped cross-company loads."""
        registry = CalculationAuditRegistry()
        with self.assertRaises(ValueError):
            registry.load_from_sqlite(company_id=None, db_path=self.temp_db_path)

        with self.assertRaises(ValueError):
            registry.load_from_sqlite(company_id="", db_path=self.temp_db_path)

    # -------------------------------------------------------------------------
    # Test 8: JEV Decision Layer Rejection of Cross-Company Claims
    # -------------------------------------------------------------------------
    def test_jev_verifier_foreign_entity_rejection(self):
        """Claims referencing foreign company signatures must be rejected by JEV."""
        jev = JevVerificationLayer()

        claim = AnalyticalClaim(
            company_id="NSE:ASHOKA",
            company_name="Ashoka Buildcon Limited",
            claim="Ashoka Buildcon expanded its commercial vehicle segment through Jaguar Land Rover sales.",
            evidence=["Management highlighted strong luxury SUV demand."],
            period="FY24",
            source=["Annual Report"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[]
        )

        result = jev.verify_claim(claim, active_company_id="NSE:ASHOKA")
        self.assertEqual(result.status, "REJECT")
        self.assertIn("CROSS_COMPANY_CONTAMINATION", result.review_notes)

    # -------------------------------------------------------------------------
    # Test 9: Universal Fact-Checking Verifier Entity Purge
    # -------------------------------------------------------------------------
    def test_verifier_universal_foreign_entity_purge(self):
        """Prose containing foreign entity signatures must be purged regardless of which stock is active."""
        verifier = FactCheckingVerifier()

        # Ashoka report contaminated with Vinati Organics ATBS and Tata Motors JLR
        dirty_prose = "The company recorded strong growth in its ATBS chemical business and Jaguar Land Rover operations."
        cleaned, violations, remediations = verifier.verify_text(
            text=dirty_prose,
            verified_financials={"current_price": 220.0},
            primary_disclosures={"symbol": "ASHOKA.NS"},
            sec_category="GENERAL_MANUFACTURING"
        )

        self.assertTrue(len(violations) >= 2)
        self.assertNotIn("ATBS", cleaned)
        self.assertNotIn("Jaguar Land Rover", cleaned)

    # -------------------------------------------------------------------------
    # Test 10: TMCV and TATAMOTORS Alias Resolution
    # -------------------------------------------------------------------------
    def test_tmcv_tatamotors_canonical_unification(self):
        """All historical aliases for Tata Motors must resolve to the single canonical identity NSE:TATAMOTORS."""
        aliases = [
            "TATAMOTORS",
            "TATAMOTORS.NS",
            "TMCV",
            "TMCV.NS",
            "Tata Motors",
            "Tata Motors Limited",
            "500570",
            "INE155A01022"
        ]

        for a in aliases:
            identity = resolve_canonical_identity(a)
            self.assertEqual(identity.company_id, "NSE:TATAMOTORS")
            self.assertEqual(identity.isin, "INE155A01022")
            self.assertEqual(identity.legal_name, "Tata Motors Limited")

    # -------------------------------------------------------------------------
    # Test 11: Screener Engine Output Isolation
    # -------------------------------------------------------------------------
    def test_screener_engine_output_isolation(self):
        """ScreenerEngine output payload and all historical/quarterly rows must be tagged with company_id."""
        ctx = create_research_context("ASHOKA")
        # Run screener engine with mock data or live fallback
        scr_data = ScreenerEngine.get_screener_data("ASHOKA", run_context=ctx)

        self.assertEqual(scr_data["company_id"], "NSE:ASHOKA")
        self.assertEqual(scr_data["isin"], "INE442H01029")
        self.assertEqual(scr_data["entity_role"], "PRIMARY_COMPANY")

        for r in scr_data.get("pl_rows", []):
            self.assertEqual(r["company_id"], "NSE:ASHOKA")
            self.assertEqual(r["entity_role"], "PRIMARY_COMPANY")

        for qr in scr_data.get("quarterly_rows", []):
            self.assertEqual(qr["company_id"], "NSE:ASHOKA")
            self.assertEqual(qr["entity_role"], "PRIMARY_COMPANY")

        # Verify peers are strictly marked with entity_role=PEER
        for pr in scr_data.get("peer_rows", []):
            if not pr.get("is_target"):
                self.assertEqual(pr.get("entity_role"), "PEER")
                self.assertNotEqual(pr.get("company_id"), "NSE:ASHOKA")


if __name__ == "__main__":
    unittest.main()
