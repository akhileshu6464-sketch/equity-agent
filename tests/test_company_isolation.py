"""
Test Suite: Zero Company Data Contamination & Architectural Isolation
Verifies canonical identity resolution, strict RAG chunk boundary assertions,
cache isolation, zero foreign entity leaks, and 'Verified information unavailable.' fallbacks.
"""

import os
import sys
import unittest

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.company_identity import resolve_canonical_identity, CompanyIdentity
from core.research_context import create_research_context, ResearchRunContext
from services.rag_engine import CompanyRAGEngine
from agents.editorial_agent import EditorialAgent
from agents.pipeline import run_deep_institutional_pipeline
from services.financial_data import FinancialDataService
from services.document_loader import DocumentLoader


class TestCompanyIsolation(unittest.TestCase):
    """Verifies complete multi-dimensional isolation across all target stocks."""

    def setUp(self):
        self.stocks = [
            ("REDINGTON", "NSE:REDINGTON", "INE891401026"),
            ("ASHOKA", "NSE:ASHOKA", "INE442H01029"),
            ("VINATIORGA", "NSE:VINATIORGA", "INE410B01037"),
            ("HDFCBANK", "NSE:HDFCBANK", "INE040A01034"),
            ("TATAMOTORS", "NSE:TATAMOTORS", "INE155A01022"),
            ("CROMPTON", "NSE:CROMPTON", "INE299U01018"),
            ("RELIANCE", "NSE:RELIANCE", "INE002A01018"),
            ("INFY", "NSE:INFY", "INE009A01021"),
        ]

    def test_canonical_identity_resolution(self):
        """1. Every company must resolve to an immutable canonical identity with ISIN."""
        for sym, expected_id, expected_isin in self.stocks:
            identity = resolve_canonical_identity(sym)
            self.assertEqual(identity.company_id, expected_id)
            self.assertEqual(identity.isin, expected_isin)
            self.assertTrue(len(identity.company_name) > 2)

    def test_rag_chunk_hard_boundary_isolation(self):
        """2. RAG storage and retrieval MUST strictly isolate chunks by company_id."""
        db_path = "data/test_rag_isolation.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        rag = CompanyRAGEngine(db_path=db_path)

        ctx_vinati = create_research_context(resolve_canonical_identity("VINATIORGA"))
        ctx_ashoka = create_research_context(resolve_canonical_identity("ASHOKA"))

        # Store doc for Vinati
        rag.store_document_with_chunks(
            run_context=ctx_vinati,
            document_id="vinati_doc_1",
            document_type="ANNUAL_REPORT",
            content="Vinati Organics manufactures specialty monomers and aromatics in Maharashtra.",
            source="BSE Statutory Filing"
        )

        # Store doc for Ashoka
        rag.store_document_with_chunks(
            run_context=ctx_ashoka,
            document_id="ashoka_doc_1",
            document_type="CONCALL_TRANSCRIPT",
            content="Ashoka Buildcon delivered highway EPC milestones on NHAI packages.",
            source="BSE LODR Filing"
        )

        # Retrieve chunks for Vinati: must only return Vinati chunks
        chunks_vinati = rag.retrieve_chunks(ctx_vinati, "manufacturing operations", top_k=5)
        self.assertTrue(len(chunks_vinati) > 0)
        for c in chunks_vinati:
            self.assertEqual(c["company_id"], ctx_vinati.company_id)
            self.assertNotIn("Ashoka", c["content"])

        # Retrieve chunks for Ashoka: must only return Ashoka chunks
        chunks_ashoka = rag.retrieve_chunks(ctx_ashoka, "highway projects", top_k=5)
        self.assertTrue(len(chunks_ashoka) > 0)
        for c in chunks_ashoka:
            self.assertEqual(c["company_id"], ctx_ashoka.company_id)
            self.assertNotIn("Vinati", c["content"])

        # HARD ASSERTION: Querying chunks with mismatched company_id must raise RuntimeError
        with self.assertRaises(RuntimeError):
            # Attempt to sneak in an assertion violation by spoofing company_id in context check
            ctx_vinati.assert_same_company("NSE:ASHOKA")

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_editorial_zero_foreign_entities_and_fallbacks(self):
        """3. Editorial agent About section must have zero foreign entities and use verified fallbacks."""
        agent = EditorialAgent()

        # Test Redington
        about_red = agent.generate_comprehensive_about(
            summary_text="Redington Limited is an integrated technology solutions provider in India and internationally.",
            company_name="Redington Limited",
            symbol="REDINGTON",
            sector="Technology",
            industry="Electronic Components",
            screener_data={
                "market_cap_cr": 18500.0,
                "current_price": 235.0,
                "clean_symbol": "REDINGTON",
                "company_name": "Redington Limited"
            }
        )
        desc_red = str(about_red)
        self.assertNotIn("ATBS", desc_red)
        self.assertNotIn("Isobutyl Benzene", desc_red)
        self.assertNotIn("Veeral Organics", desc_red)
        self.assertNotIn("Ashoka Concessions", desc_red)
        self.assertNotIn("Ashok Katariya", desc_red)
        self.assertEqual(about_red["key_customers"], ["Verified information unavailable."])
        self.assertEqual(about_red["subsidiaries_jvs"][0]["entity"], "Verified information unavailable.")

        # Test Ashoka Buildcon
        about_ash = agent.generate_comprehensive_about(
            summary_text="Ashoka Buildcon Limited operates as an infrastructure development company in India.",
            company_name="Ashoka Buildcon Limited",
            symbol="ASHOKA",
            sector="Industrials",
            industry="Engineering & Construction",
            screener_data={
                "market_cap_cr": 6500.0,
                "current_price": 230.0,
                "clean_symbol": "ASHOKA",
                "company_name": "Ashoka Buildcon Limited"
            }
        )
        desc_ash = str(about_ash)
        self.assertNotIn("ATBS", desc_ash)
        self.assertNotIn("Isobutyl Benzene", desc_ash)
        self.assertNotIn("Veeral Organics", desc_ash)
        self.assertNotIn("ProConnect", desc_ash)
        self.assertNotIn("Ensure Support", desc_ash)
        self.assertEqual(about_ash["key_customers"], ["Verified information unavailable."])

        # Test HDFC Bank
        about_hdfc = agent.generate_comprehensive_about(
            summary_text="HDFC Bank Limited provides a range of banking and financial services to individuals and businesses in India.",
            company_name="HDFC Bank Limited",
            symbol="HDFCBANK",
            sector="Financial Services",
            industry="Banks - Private",
            screener_data={
                "market_cap_cr": 1250000.0,
                "current_price": 1650.0,
                "clean_symbol": "HDFCBANK",
                "company_name": "HDFC Bank Limited"
            }
        )
        desc_hdfc = str(about_hdfc)
        self.assertNotIn("ATBS", desc_hdfc)
        self.assertNotIn("Ashoka Concessions", desc_hdfc)
        self.assertNotIn("ProConnect", desc_hdfc)
        self.assertNotIn("Crompton", desc_hdfc)

    def test_pipeline_execution_isolation(self):
        """4. Pipeline execution must stamp canonical metadata and forbid foreign contamination."""
        stocks_to_test = ["REDINGTON", "ASHOKA", "CROMPTON"]

        for sym in stocks_to_test:
            canonical_id = resolve_canonical_identity(sym)
            ctx = create_research_context(canonical_id)

            dossier = run_deep_institutional_pipeline(
                ticker=sym,
                force_refresh=True,
                run_context=ctx
            )

            # Metadata isolation
            self.assertEqual(dossier.get("company_id"), ctx.company_id)
            self.assertEqual(dossier.get("isin"), ctx.isin)
            self.assertEqual(dossier.get("research_run_id"), ctx.research_run_id)

            # Text isolation: Redington must not contain Vinati or Ashoka entities
            all_text = (
                dossier.get("moat_markdown", "") + " " +
                dossier.get("forensics_markdown", "") + " " +
                dossier.get("gov_markdown", "") + " " +
                dossier.get("val_markdown", "")
            )

            if sym == "REDINGTON":
                self.assertNotIn("ATBS", all_text)
                self.assertNotIn("Isobutyl Benzene", all_text)
                self.assertNotIn("Veeral Organics", all_text)
                self.assertNotIn("Ashoka Concessions", all_text)
                self.assertNotIn("Ashok Katariya", all_text)

            elif sym == "ASHOKA":
                self.assertNotIn("ATBS", all_text)
                self.assertNotIn("Isobutyl Benzene", all_text)
                self.assertNotIn("Veeral Organics", all_text)
                self.assertNotIn("ProConnect", all_text)
                self.assertNotIn("Ensure Support", all_text)

            elif sym == "CROMPTON":
                self.assertNotIn("ATBS", all_text)
                self.assertNotIn("Isobutyl Benzene", all_text)
                self.assertNotIn("Veeral Organics", all_text)
                self.assertNotIn("Ashoka Concessions", all_text)
                self.assertNotIn("ProConnect", all_text)


if __name__ == "__main__":
    unittest.main()
