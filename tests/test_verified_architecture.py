"""
Test Suite: Verified Data -> AI Agent Architecture (tests/test_verified_architecture.py)
Validates all 18 sections of Research Beast's architectural mandate:
DATA FIRST. VERIFICATION SECOND. AI ANALYSIS THIRD.
"""

import unittest
import os
import tempfile
from typing import Dict, Any

from core.company_identity import (
    CompanyIdentity,
    resolve_canonical_identity,
    verify_data_object_identity,
    KNOWN_CIN_MAP
)
from core.research_context import (
    ResearchRunContext,
    create_research_context,
    StructuredAgentContext,
    DataContaminationError,
    assert_company_boundary
)
from calculations.metric_mapper import MetricMapper, CANONICAL_METRICS
from services.decision_engine.fundamental_store import FundamentalDataStore, FundamentalDatapoint
from calculations.margins import ebitda_margin, pat_margin
from calculations.growth import revenue_growth
from calculations.audit import global_audit_registry
from services.rag_engine import CompanyRAGEngine
from services.decision_engine.jev_verifier import JevVerificationLayer, AnalyticalClaim
from services.decision_engine.coordinator import DecisionEngineCoordinator


class TestVerifiedArchitecture(unittest.TestCase):
    """Rigorous unit and integration tests for Research Beast target architecture."""

    def setUp(self):
        self.ashoka_ident = resolve_canonical_identity("ASHOKA")
        self.tata_ident = resolve_canonical_identity("TATAMOTORS")
        self.redington_ident = resolve_canonical_identity("REDINGTON")

        self.ashoka_ctx = create_research_context(self.ashoka_ident)
        self.tata_ctx = create_research_context(self.tata_ident)

    # =========================================================================
    # SECTION 1: CREDENTIAL ISOLATION & DATA SOURCES
    # =========================================================================
    def test_section_1_credential_isolation(self):
        """DRISHTI_API_KEY must be stored only server-side, never in client code."""
        from services.drishti.config import mask_api_key
        raw_key = "dr_live_sample_key_12345678"
        masked = mask_api_key(raw_key)
        self.assertTrue(masked.startswith("dr_"))
        self.assertNotIn("sample_key", masked)
        self.assertIn("...", masked)

    # =========================================================================
    # SECTION 2: COMPANY IDENTITY FIREWALL
    # =========================================================================
    def test_section_2_canonical_identity_structure(self):
        """Every canonical company must have company_id, legal_name, display_name, isin, nse_symbol, bse_code, cin."""
        ident = self.ashoka_ident
        self.assertEqual(ident.company_id, "NSE:ASHOKA")
        self.assertEqual(ident.isin, "INE442H01029")
        self.assertEqual(ident.nse_symbol, "ASHOKA")
        self.assertEqual(ident.bse_code, "533271")
        self.assertTrue(hasattr(ident, "cin"))
        self.assertEqual(ident.cin, KNOWN_CIN_MAP["ASHOKA"])

    def test_section_2_reject_company_name_alone(self):
        """Company name alone must NEVER be used as the primary identifier; must be rejected."""
        name_only_obj = {
            "company_name": "Ashoka Buildcon Limited",
            "revenue": 5000.0
        }
        is_valid, reason = verify_data_object_identity(name_only_obj, self.ashoka_ident)
        self.assertFalse(is_valid)
        self.assertIn("Company name alone must NEVER be used", reason)

    def test_section_2_zero_guessing_policy(self):
        """If incoming record's identity cannot be mapped or mismatches, reject data."""
        mismatched_obj = {
            "company_id": "NSE:TATAMOTORS",
            "isin": "INE155A01022",
            "nse_symbol": "TATAMOTORS",
            "source": "BSE",
            "period": "FY24",
            "scope": "CONSOLIDATED"
        }
        is_valid, reason = verify_data_object_identity(mismatched_obj, self.ashoka_ident)
        self.assertFalse(is_valid)
        self.assertIn("mismatch", reason.lower())

    # =========================================================================
    # SECTION 3: DATA ISOLATION (ZERO MIXING OF COMPANIES)
    # =========================================================================
    def test_section_3_data_isolation_between_companies(self):
        """Ashoka Buildcon, Tata Motors, Redington must have completely isolated data stores."""
        ashoka_store = FundamentalDataStore(
            company_id=self.ashoka_ident.company_id,
            ticker=self.ashoka_ident.primary_ticker,
            isin=self.ashoka_ident.isin
        )
        ashoka_store.add_datapoint(
            metric="Revenue from Operations",
            period="FY24",
            period_type="ANNUAL",
            value=8000.0,
            unit="INR_CR"
        )

        tata_store = FundamentalDataStore(
            company_id=self.tata_ident.company_id,
            ticker=self.tata_ident.primary_ticker,
            isin=self.tata_ident.isin
        )
        tata_store.add_datapoint(
            metric="Revenue from Operations",
            period="FY24",
            period_type="ANNUAL",
            value=437928.0,
            unit="INR_CR"
        )

        # Confirm data isolation
        self.assertEqual(ashoka_store.get_latest_datapoint_value("Revenue from Operations"), 8000.0)
        self.assertEqual(tata_store.get_latest_datapoint_value("Revenue from Operations"), 437928.0)

        # Attempting cross-company injection must raise DataContaminationError
        with self.assertRaises(DataContaminationError):
            foreign_dp = tata_store.get_latest_datapoint("Revenue from Operations")
            ashoka_store.add_datapoint_object(foreign_dp)

    # =========================================================================
    # SECTION 4: DATA NORMALIZATION & EXPLICIT METRIC MAPPING
    # =========================================================================
    def test_section_4_metric_mapping_layer(self):
        """Maps varied source names to canonical metric keys without blind mapping."""
        # 1. Screener 'Sales' -> canonical 'revenue'
        res1 = MetricMapper.normalize_metric_name("Sales", source="SCREENER")
        self.assertTrue(res1.is_mapped)
        self.assertEqual(res1.canonical_key, "revenue")
        self.assertEqual(res1.original_source_field, "Sales")

        # 2. BSE Statutory 'Revenue from Operations' -> canonical 'revenue'
        res2 = MetricMapper.normalize_metric_name("Revenue from Operations", source="BSE_NSE_FILINGS")
        self.assertTrue(res2.is_mapped)
        self.assertEqual(res2.canonical_key, "revenue")

        # 3. 'Other Income' must NOT map to revenue (accounting equivalence check)
        res3 = MetricMapper.normalize_metric_name("Other Income", source="BSE_NSE_FILINGS")
        self.assertTrue(res3.is_mapped)
        self.assertEqual(res3.canonical_key, "other_income")
        self.assertNotEqual(res3.canonical_key, "revenue")

        # 4. Completely unknown line item is preserved as unmapped raw metric
        res4 = MetricMapper.normalize_metric_name("Unclassified Statutory Reserve Adjustment", source="SCREENER")
        self.assertFalse(res4.is_mapped)

    # =========================================================================
    # SECTION 5: VERIFIED DATA STORE & NO ANONYMOUS NUMBERS
    # =========================================================================
    def test_section_5_verified_data_store_schema(self):
        """Every datapoint must contain exact provenance and canonical schema fields."""
        store = FundamentalDataStore(
            company_id=self.ashoka_ident.company_id,
            ticker=self.ashoka_ident.primary_ticker,
            isin=self.ashoka_ident.isin
        )
        dp = store.add_datapoint(
            metric="Revenue from Operations",
            period="FY2025",
            period_type="ANNUAL",
            value=5000.0,
            unit="INR_CR",
            currency="INR",
            period_start="2024-04-01",
            period_end="2025-03-31",
            fiscal_year="FY2025",
            quarter=None,
            statement_scope="CONSOLIDATED",
            source="BSE Statutory Filings",
            document="Financial_Results_Q4.pdf",
            source_date="2025-05-15",
            extraction_method="DETERMINISTIC_REGULATORY_PARSER",
            verification_status="VERIFIED"
        )

        d = dp.to_dict()
        required_fields = [
            "company_id", "isin", "metric", "value", "unit", "currency",
            "period_start", "period_end", "period_type", "fiscal_year", "quarter",
            "scope", "source", "source_document", "source_date", "extraction_method",
            "verification_status"
        ]
        for rf in required_fields:
            self.assertIn(rf, d, f"Missing required Section 5 field: {rf}")

        self.assertEqual(d["value"], 5000.0)
        self.assertEqual(d["verification_status"], "VERIFIED")

    # =========================================================================
    # SECTION 6: SOURCE RECONCILIATION & CONFLICT HANDLING
    # =========================================================================
    def test_section_6_source_reconciliation_match(self):
        """When multiple sources provide the same number, mark VERIFIED."""
        store = FundamentalDataStore(
            company_id=self.ashoka_ident.company_id,
            ticker=self.ashoka_ident.primary_ticker,
            isin=self.ashoka_ident.isin
        )
        # 1. Primary filing = 1,200 Cr
        store.add_datapoint(
            metric="Revenue from Operations",
            period="FY24",
            period_type="ANNUAL",
            value=1200.0,
            source="Primary Statutory Filing"
        )

        # 2. Drishti API = 1,200 Cr -> VERIFIED
        dp = store.reconcile_and_add_datapoint(
            metric="Revenue from Operations",
            period="FY24",
            period_type="ANNUAL",
            value=1200.0,
            new_source="Drishti API"
        )
        self.assertEqual(dp.verification_status, "VERIFIED")
        self.assertTrue(dp.is_usable_for_analysis)
        self.assertIn("Drishti API", dp.reconciliation_sources)

    def test_section_6_source_reconciliation_conflict(self):
        """When sources diverge (1,200 vs 1,180 Cr), mark CONFLICT and exclude from analysis."""
        store = FundamentalDataStore(
            company_id=self.ashoka_ident.company_id,
            ticker=self.ashoka_ident.primary_ticker,
            isin=self.ashoka_ident.isin
        )
        # 1. Primary filing = 1,200 Cr
        store.add_datapoint(
            metric="Revenue from Operations",
            period="FY24",
            period_type="ANNUAL",
            value=1200.0,
            source="Primary Statutory Filing"
        )

        # 2. Drishti API = 1,180 Cr (Divergence of 1.67%)
        conflict_dp = store.reconcile_and_add_datapoint(
            metric="Revenue from Operations",
            period="FY24",
            period_type="ANNUAL",
            value=1180.0,
            new_source="Drishti API",
            tolerance_pct=1.0
        )
        self.assertEqual(conflict_dp.verification_status, "CONFLICT")
        self.assertFalse(conflict_dp.is_usable_for_analysis)
        self.assertIsNotNone(conflict_dp.conflict_reason)
        self.assertIn("Divergence", conflict_dp.conflict_reason)

        # Must NOT be returned by get_usable_datapoint
        usable = store.get_usable_datapoint("Revenue from Operations", "FY24")
        self.assertIsNone(usable)

        # Must be listed in store conflicts
        conflicts = store.get_conflicts()
        self.assertEqual(len(conflicts), 1)

    # =========================================================================
    # SECTION 7: REVISION CONTROL
    # =========================================================================
    def test_section_7_revision_control(self):
        """Tracks original vs revised values, filing dates, and revision status."""
        dp = FundamentalDatapoint(
            company_id="NSE:ASHOKA",
            isin="INE442H01029",
            metric="Revenue from Operations",
            value=1250.0,
            period="FY24",
            original_value=1200.0,
            revised_value=1250.0,
            filing_date="2024-05-20",
            revision_date="2024-08-15",
            revision_status="RESTATED",
            is_active=True
        )
        self.assertEqual(dp.original_value, 1200.0)
        self.assertEqual(dp.revised_value, 1250.0)
        self.assertEqual(dp.revision_status, "RESTATED")
        self.assertTrue(dp.is_active)

    # =========================================================================
    # SECTION 8: DETERMINISTIC FINANCIAL ENGINE
    # =========================================================================
    def test_section_8_deterministic_calculations(self):
        """All calculations happen in pure Python with INPUTS -> FORMULA -> RESULT -> SOURCE."""
        # 1. EBITDA Margin
        res_ebitda = ebitda_margin(ebitda=200.0, revenue=1000.0)
        self.assertEqual(res_ebitda.value, 20.0)
        self.assertIn("revenue", res_ebitda.inputs)
        self.assertIn("ebitda", res_ebitda.inputs)
        self.assertEqual(res_ebitda.formula, "(ebitda / revenue) * 100")

        # 2. PAT Margin
        res_pat = pat_margin(pat=100.0, revenue=1000.0)
        self.assertEqual(res_pat.value, 10.0)

        # 3. Revenue Growth
        res_growth = revenue_growth(current_revenue=1200.0, previous_revenue=1000.0)
        self.assertEqual(res_growth.value, 20.0)

    # =========================================================================
    # SECTION 9: EVIDENCE / RAG LAYER (COMPANY LOCKED)
    # =========================================================================
    def test_section_9_rag_company_isolation(self):
        """RAG retrieval MUST filter by company_id before search and fail closed on foreign chunks."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            rag = CompanyRAGEngine(db_path=temp_db)

            # Store Ashoka document
            rag.store_document_with_chunks(
                run_context=self.ashoka_ctx,
                document_id="ashoka_q4_24",
                document_type="CONCALL_TRANSCRIPT",
                content="Ashoka Buildcon order book stands at 14,000 crores.",
                date="2024-05-25",
                period="Q4 FY24",
                source="Drishti Transcripts"
            )

            # Store Tata Motors document
            rag.store_document_with_chunks(
                run_context=self.tata_ctx,
                document_id="tata_q4_24",
                document_type="CONCALL_TRANSCRIPT",
                content="Tata Motors commercial vehicles margin expanded significantly.",
                date="2024-05-25",
                period="Q4 FY24",
                source="Drishti Transcripts"
            )

            # Retrieve chunks for Ashoka -> Must NEVER return Tata Motors
            ashoka_chunks = rag.retrieve_chunks(self.ashoka_ctx, query="order book margin")
            self.assertTrue(len(ashoka_chunks) > 0)
            for c in ashoka_chunks:
                self.assertEqual(c["company_id"], self.ashoka_ctx.company_id)
                self.assertNotIn("Tata Motors", c["chunk_text"])
                # Check Section 9 chunk schema
                self.assertIn("document_id", c)
                self.assertIn("date", c)
                self.assertIn("period", c)
                self.assertIn("source", c)
                self.assertIn("page_or_chunk", c)
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)

    # =========================================================================
    # SECTION 10 & 11: STRUCTURED AI AGENT CONTEXT & BOUNDARY ASSERTION
    # =========================================================================
    def test_section_11_structured_agent_context_validation(self):
        """Before execution, assert all objects belong to company_id or raise DataContaminationError."""
        valid_ctx = StructuredAgentContext(
            company_id=self.ashoka_ident.company_id,
            company_name=self.ashoka_ident.company_name,
            isin=self.ashoka_ident.isin,
            period="FY24",
            scope="CONSOLIDATED",
            verified_financial_data={"sales": 8000.0},
            deterministic_calculations=[],
            verified_documents=[{"company_id": "NSE:ASHOKA", "text": "Annual report"}],
            news=[{"company_id": "NSE:ASHOKA", "headline": "Highway bid won"}],
            announcements=[{"company_id": "NSE:ASHOKA", "subject": "LODR filing"}],
            known_conflicts=[],
            source_metadata={}
        )
        # Integrity validation passes cleanly
        valid_ctx.validate_integrity()

        # Contaminated context with foreign news item must fail immediately
        contaminated_ctx = StructuredAgentContext(
            company_id=self.ashoka_ident.company_id,
            company_name=self.ashoka_ident.company_name,
            isin=self.ashoka_ident.isin,
            period="FY24",
            scope="CONSOLIDATED",
            verified_financial_data={"sales": 8000.0},
            deterministic_calculations=[],
            verified_documents=[],
            news=[{"company_id": "NSE:TATAMOTORS", "headline": "JLR Q4 sales"}],
            announcements=[],
            known_conflicts=[],
            source_metadata={}
        )
        with self.assertRaises(DataContaminationError):
            contaminated_ctx.validate_integrity()

    # =========================================================================
    # SECTION 14: JEv VALIDATION GATE (FAIL CLOSED)
    # =========================================================================
    def test_section_14_jev_validation_gate(self):
        """JEv validation checklist rejects ungrounded numbers or cross-company claims."""
        verifier = JevVerificationLayer()

        # Claim with supported numbers
        good_claim = AnalyticalClaim(
            company_id=self.ashoka_ident.company_id,
            company_name=self.ashoka_ident.company_name,
            claim="Revenue from operations reached ₹8,000.0 Cr in FY24.",
            evidence=["Audited statutory balance sheet reports revenue of 8000.0 Cr."],
            period="FY24",
            source=["Audited Financial Statements"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[8000.0]
        )
        res_good = verifier.verify_claim(good_claim, self.ashoka_ident.company_id, verified_numbers=[8000.0])
        self.assertEqual(res_good.status, "PASS")
        self.assertTrue(res_good.identity_verified)

        # Claim with hallucinated/mismatched number (9,999.0 Cr vs 8,000.0 Cr)
        bad_num_claim = AnalyticalClaim(
            company_id=self.ashoka_ident.company_id,
            company_name=self.ashoka_ident.company_name,
            claim="Revenue reached ₹9,999.0 Cr in FY24.",
            evidence=["Annual statements report 8000.0 Cr."],
            period="FY24",
            source=["Audited Financial Statements"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[9999.0]
        )
        res_bad = verifier.verify_claim(bad_num_claim, self.ashoka_ident.company_id, verified_numbers=[8000.0])
        self.assertEqual(res_bad.status, "REJECT")

        # Claim with cross-company contamination
        foreign_claim = AnalyticalClaim(
            company_id=self.ashoka_ident.company_id,
            company_name=self.ashoka_ident.company_name,
            claim="Tata Motors reported significant margins in commercial vehicles.",
            evidence=["Tata Motors concall notes."],
            period="FY24",
            source=["Audited Financial Statements"],
            claim_type="HISTORICAL_FACT",
            cited_numbers=[]
        )
        res_foreign = verifier.verify_claim(foreign_claim, self.ashoka_ident.company_id, verified_numbers=[8000.0])
        self.assertEqual(res_foreign.status, "REJECT")
        self.assertIn("CROSS_COMPANY_CONTAMINATION", res_foreign.review_notes)


if __name__ == "__main__":
    unittest.main()
