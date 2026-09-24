"""
Unit Test Suite: Drishti Integration & Verification Firewall (tests/test_drishti_integration.py)
Tests:
1. Server-side credential isolation (DRISHTI_API_KEY).
2. Data model validation: mandatory company tags and provenance.
3. Persistent caching: key hashing, TTL expiry, and stale fallback under HTTP 429.
4. Company Identity Firewall: multi-factor regulatory alignment and rejection of mismatches.
5. Financial Reconciliation: cross-checking numbers, VERIFIED vs CONFLICT flagging.
6. Concall store: chunking and company_id pre-filtering for RAG isolation.
7. Client adapter and Service ingestion fail-open behavior.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import json
import tempfile
import shutil

from core.company_identity import CompanyIdentity
from services.drishti.config import (
    get_drishti_api_key,
    is_drishti_configured,
    mask_api_key,
)
from services.drishti.models import (
    DrishtiRecord,
    DrishtiNewsRecord,
    DrishtiAnnouncementRecord,
    DrishtiEarningsRecord,
    DrishtiConcallRecord,
    ConcallTranscriptChunk,
    DrishtiAlertRecord,
)
from services.drishti.cache import DrishtiCache
from services.drishti.identity_firewall import (
    DrishtiIdentityFirewall,
    DrishtiIdentityMismatchError,
)
from services.drishti.reconciler import FinancialReconciler
from services.drishti.concall_store import ConcallStore
from services.drishti.client import (
    DrishtiApiClient,
    DrishtiAuthError,
    DrishtiRateLimitError,
)
from services.drishti.service import DrishtiService


class TestDrishtiIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache = DrishtiCache(cache_dir=os.path.join(self.test_dir, "cache"))
        self.concall_store = ConcallStore(store_dir=os.path.join(self.test_dir, "transcripts"))
        self.target_ident = CompanyIdentity(
            company_id="NSE:VINATIORGA",
            legal_name="Vinati Organics Limited",
            display_name="Vinati Organics",
            isin="INE410B01037",
            primary_exchange="NSE",
            primary_symbol="VINATIORGA",
            nse_symbol="VINATIORGA",
            bse_code="524200",
            sector="Basic Materials",
            industry="Specialty Chemicals"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_credential_isolation(self):
        """1. Verify server-side API key retrieval and masking."""
        with patch.dict(os.environ, {"DRISHTI_API_KEY": "test_drishti_secret_key_12345"}):
            self.assertEqual(get_drishti_api_key(), "test_drishti_secret_key_12345")
            self.assertTrue(is_drishti_configured())
            masked = mask_api_key(get_drishti_api_key())
            self.assertIn("...", masked)
            self.assertNotIn("secret", masked)

        with patch.dict(os.environ, {"DRISHTI_API_KEY": ""}, clear=True):
            self.assertFalse(is_drishti_configured())
            self.assertEqual(mask_api_key(None), "[NOT_SET]")

    def test_drishti_models_mandatory_fields(self):
        """2. Verify Drishti records contain all required provenance fields."""
        news = DrishtiNewsRecord(
            company_id=self.target_ident.company_id,
            company_name=self.target_ident.legal_name,
            isin=self.target_ident.isin,
            nse_symbol=self.target_ident.nse_symbol,
            bse_code=self.target_ident.bse_code,
            source_endpoint="/v1/news",
            source_id="news_101",
            document_type="NEWS",
            headline="Chemical Capacity Expansion Underway",
            raw_sentiment="positive",
            publication_date="2025-05-10"
        )
        d = news.to_dict()
        self.assertEqual(d["company_id"], "NSE:VINATIORGA")
        self.assertEqual(d["source"], "DRISHTI")
        self.assertEqual(d["isin"], "INE410B01037")
        self.assertEqual(d["raw_sentiment"], "positive")

    def test_cache_key_and_stale_fallback(self):
        """3. Verify deterministic cache keys and rate-limit stale data serving."""
        key = self.cache.build_cache_key("NSE:VINATIORGA", "/v1/news", {"symbols": ["VINATIORGA"], "limit": 10})
        self.assertIn("NSE_VINATIORGA", key)
        self.assertIn("v1_news", key)

        data_payload = [{"id": "1", "title": "Test News"}]
        # Set with 0 TTL to immediately expire
        self.cache.set(key, data_payload, ttl_seconds=-10)

        # Standard get should be None because it's expired
        self.assertIsNone(self.cache.get(key))

        # Stale get should return data marked as stale
        stale = self.cache.get_stale_or_any(key)
        self.assertIsNotNone(stale)
        self.assertTrue(stale["is_stale"])
        self.assertEqual(stale["data"], data_payload)

    def test_identity_firewall_matching_and_rejection(self):
        """4. Verify Company Identity Firewall accepts aligned records and strictly rejects mismatches."""
        # Valid matching item
        valid_item = {
            "symbol": "VINATIORGA",
            "scrip_code": "524200",
            "title": "Quarterly Financial Results",
            "company_name": "Vinati Organics Limited"
        }
        aligned = DrishtiIdentityFirewall.verify_and_align_item(valid_item, self.target_ident, "/v1/news")
        self.assertIsNotNone(aligned)
        self.assertEqual(aligned["company_id"], "NSE:VINATIORGA")
        self.assertEqual(aligned["verification_status"], "VALIDATED")

        # Cross-company mismatch item (e.g. Reliance record arriving for Vinati)
        mismatch_item = {
            "symbol": "RELIANCE",
            "scrip_code": "500325",
            "title": "Telecom Launch",
            "company_name": "Reliance Industries Limited"
        }
        rejected = DrishtiIdentityFirewall.verify_and_align_item(mismatch_item, self.target_ident, "/v1/news")
        self.assertIsNone(rejected)

        # Attempt to match on company name alone without valid symbol or scrip code
        name_only_item = {
            "symbol": "UNKNOWN",
            "scrip_code": "999999",
            "title": "Random Event",
            "company_name": "Vinati Organics"
        }
        rejected_name = DrishtiIdentityFirewall.verify_and_align_item(name_only_item, self.target_ident, "/v1/news")
        self.assertIsNone(rejected_name)

        # Test batch filtering
        batch = [valid_item, mismatch_item, name_only_item]
        filtered = DrishtiIdentityFirewall.filter_and_validate_batch(batch, self.target_ident, "/v1/news")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["symbol"], "VINATIORGA")

    def test_financial_reconciler_verified_and_conflict(self):
        """5. Verify FinancialReconciler flags matches as VERIFIED and discrepancies as CONFLICT."""
        # Case A: Matching figures
        drishti_a = {"revenue": "2,248", "operating_profit": "582", "net_profit": "405"}
        primary_a = {"Sales": 2248.0, "Operating Profit": 582.0, "Net Profit": 405.0}

        recon_a = FinancialReconciler.reconcile_metrics(drishti_a, primary_a)
        self.assertEqual(recon_a["overall_status"], "VERIFIED")
        self.assertEqual(len(recon_a["matches"]), 3)
        self.assertEqual(len(recon_a["conflicts"]), 0)

        # Case B: Numerical Discrepancy -> CONFLICT
        drishti_b = {"revenue": "2,500", "operating_profit": "582", "net_profit": "405"}  # Divergent revenue
        primary_b = {"Sales": 2248.0, "Operating Profit": 582.0, "Net Profit": 405.0}

        recon_b = FinancialReconciler.reconcile_metrics(drishti_b, primary_b)
        self.assertEqual(recon_b["overall_status"], "CONFLICT")
        self.assertTrue(recon_b["requires_investigation"])
        self.assertEqual(len(recon_b["conflicts"]), 1)
        self.assertEqual(recon_b["conflicts"][0]["metric"], "REVENUE")

    def test_concall_store_rag_isolation(self):
        """6. Verify ConcallStore chunks and strictly pre-filters by company_id before retrieval."""
        sample_text = (
            "Management discussed domestic volume growth of 12% across primary business lines. "
            "Capex commissioning is scheduled for Q3 FY26 with payback expected in 3 years."
        )
        chunks = self.concall_store.add_transcript(
            company_id="NSE:VINATIORGA",
            document_id="call_001",
            quarter="Q4_25",
            date="2025-05-15",
            text=sample_text
        )
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].company_id, "NSE:VINATIORGA")
        self.assertEqual(chunks[0].source, "DRISHTI")

        # Query for Vinati should return chunk
        results_vinati = self.concall_store.retrieve_chunks("NSE:VINATIORGA", "Capex commissioning")
        self.assertGreater(len(results_vinati), 0)

        # Query for another company MUST return empty (RAG isolation)
        results_other = self.concall_store.retrieve_chunks("NSE:TATAMOTORS", "Capex commissioning")
        self.assertEqual(len(results_other), 0)

    def test_drishti_service_fail_open(self):
        """7. Verify DrishtiService returns safe empty package when unconfigured without crashing."""
        mock_client = MagicMock(spec=DrishtiApiClient)
        mock_client.is_configured.return_value = False

        service = DrishtiService(client=mock_client, cache=self.cache, concall_store=self.concall_store)
        res = service.fetch_all_company_intelligence("VINATIORGA")
        self.assertFalse(res["is_configured"])
        self.assertEqual(res["status"], "NOT_CONFIGURED")
        self.assertEqual(len(res["news"]), 0)


if __name__ == "__main__":
    unittest.main()
