"""
Drishti Data Integration Service (services/drishti/service.py)
Orchestrates Drishti ingestion, caching, identity firewalling, and reconciliation.
Guarantees:
1. DRISHTI is an input data source, NEVER the database.
2. AI agents analyze verified data; they do not browse or extract raw facts.
3. Every response is verified against canonical CompanyIdentity before storage.
4. Non-fatal fail-open: If Drishti is unavailable or rate-limited, Research Beast continues running.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.company_identity import CompanyIdentity, resolve_canonical_identity
from services.drishti.config import (
    is_drishti_configured,
    TTL_METADATA,
    TTL_EARNINGS,
    TTL_CONCALLS,
    TTL_ANNOUNCEMENTS,
    TTL_NEWS,
    TTL_ALERTS,
)
from services.drishti.client import (
    DrishtiApiClient,
    DrishtiError,
    DrishtiAuthError,
    DrishtiRateLimitError,
    DrishtiConnectionError,
)
from services.drishti.cache import get_drishti_cache, DrishtiCache
from services.drishti.identity_firewall import DrishtiIdentityFirewall
from services.drishti.reconciler import FinancialReconciler
from services.drishti.concall_store import get_concall_store, ConcallStore
from services.drishti.models import (
    DrishtiRecord,
    DrishtiNewsRecord,
    DrishtiAnnouncementRecord,
    DrishtiEarningsRecord,
    DrishtiConcallRecord,
    DrishtiAlertRecord,
)

logger = logging.getLogger("ResearchBeast.Drishti.Service")


class DrishtiService:
    """
    Central orchestration service for Drishti financial intelligence.
    """

    def __init__(
        self,
        client: Optional[DrishtiApiClient] = None,
        cache: Optional[DrishtiCache] = None,
        concall_store: Optional[ConcallStore] = None
    ):
        self.client = client or DrishtiApiClient()
        self.cache = cache or get_drishti_cache()
        self.concall_store = concall_store or get_concall_store()

    def is_available(self) -> bool:
        """Returns True if Drishti client is configured with an active API key."""
        return self.client.is_configured()

    # -------------------------------------------------------------------------
    # 1. NEWS INGESTION
    # -------------------------------------------------------------------------
    def fetch_company_news(
        self,
        identity: CompanyIdentity,
        limit: int = 15
    ) -> List[DrishtiNewsRecord]:
        """
        Retrieves company-specific news items filtered and locked to canonical company identity.
        Sentiment is preserved as source metadata only.
        """
        if not self.is_available():
            return []

        clean_sym = identity.nse_symbol or identity.primary_symbol
        scrip = identity.bse_code
        params = {"symbols": [clean_sym], "limit": limit}
        if scrip:
            params["scrip_codes"] = [scrip]

        cache_key = self.cache.build_cache_key(identity.company_id, "/v1/news", params)
        cached = self.cache.get(cache_key)

        raw_items = []
        if cached:
            raw_items = cached.get("data", [])
        else:
            try:
                resp = self.client.get_news(
                    symbols=[clean_sym] if clean_sym else None,
                    scrip_codes=[scrip] if scrip else None,
                    limit=limit
                )
                raw_items = resp.get("data", []) if isinstance(resp, dict) else []
                self.cache.set(cache_key, raw_items, ttl_seconds=TTL_NEWS)
            except DrishtiRateLimitError:
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])
            except Exception as e:
                logger.warning(f"Drishti news fetch failed for {identity.company_id}: {e}")
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])

        # Pass through identity firewall
        validated = DrishtiIdentityFirewall.filter_and_validate_batch(raw_items, identity, "/v1/news")

        news_records: List[DrishtiNewsRecord] = []
        for item in validated:
            rec = DrishtiNewsRecord(
                company_id=identity.company_id,
                company_name=identity.legal_name or identity.display_name,
                isin=identity.isin,
                nse_symbol=identity.nse_symbol,
                bse_code=identity.bse_code,
                source_endpoint="/v1/news",
                source_id=str(item.get("id") or ""),
                document_type="NEWS",
                publication_date=str(item.get("date") or ""),
                event_date=str(item.get("date") or ""),
                source_url=str(item.get("link") or ""),
                raw_payload=item,
                verification_status="VALIDATED",
                headline=str(item.get("title") or item.get("specific_title") or "Corporate News"),
                summary=str(item.get("summary") or ""),
                long_summary=str(item.get("long_summary") or ""),
                specific_title=str(item.get("specific_title") or ""),
                article_source=str(item.get("source") or "Drishti News Feed"),
                article_type=str(item.get("article_type") or "News"),
                raw_sentiment=str(item.get("sentiment") or "neutral").lower()
            )
            news_records.append(rec)

        return news_records

    # -------------------------------------------------------------------------
    # 2. ANNOUNCEMENTS INGESTION
    # -------------------------------------------------------------------------
    def fetch_company_announcements(
        self,
        identity: CompanyIdentity,
        limit: int = 15
    ) -> List[DrishtiAnnouncementRecord]:
        """
        Retrieves company corporate announcements without paraphrasing into financial conclusions.
        """
        if not self.is_available():
            return []

        clean_sym = identity.nse_symbol or identity.primary_symbol
        scrip = identity.bse_code
        params = {"symbols": [clean_sym], "detailed": True, "limit": limit}
        if scrip:
            params["scrip_codes"] = [scrip]

        cache_key = self.cache.build_cache_key(identity.company_id, "/v1/announcements", params)
        cached = self.cache.get(cache_key)

        raw_items = []
        if cached:
            raw_items = cached.get("data", [])
        else:
            try:
                resp = self.client.get_announcements(
                    symbols=[clean_sym] if clean_sym else None,
                    scrip_codes=[scrip] if scrip else None,
                    detailed=True,
                    limit=limit
                )
                raw_items = resp.get("data", []) if isinstance(resp, dict) else []
                self.cache.set(cache_key, raw_items, ttl_seconds=TTL_ANNOUNCEMENTS)
            except DrishtiRateLimitError:
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])
            except Exception as e:
                logger.warning(f"Drishti announcements fetch failed for {identity.company_id}: {e}")
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])

        validated = DrishtiIdentityFirewall.filter_and_validate_batch(raw_items, identity, "/v1/announcements")

        announcement_records: List[DrishtiAnnouncementRecord] = []
        for item in validated:
            rec = DrishtiAnnouncementRecord(
                company_id=identity.company_id,
                company_name=identity.legal_name or identity.display_name,
                isin=identity.isin,
                nse_symbol=identity.nse_symbol,
                bse_code=identity.bse_code,
                source_endpoint="/v1/announcements",
                source_id=str(item.get("id") or ""),
                document_type="ANNOUNCEMENT",
                publication_date=str(item.get("date") or ""),
                event_date=str(item.get("date") or ""),
                source_url="",
                raw_payload=item,
                verification_status="VALIDATED",
                headline=str(item.get("summary") or "Corporate Regulatory Disclosure"),
                category=str(item.get("category") or "General"),
                related_categories=item.get("related_categories", []),
                important=bool(item.get("important", False)),
                summary=str(item.get("summary") or ""),
                long_summary=str(item.get("long_summary") or ""),
                extracted_information=item.get("extracted_information", {}) if isinstance(item.get("extracted_information"), dict) else {}
            )
            announcement_records.append(rec)

        return announcement_records

    # -------------------------------------------------------------------------
    # 3. EARNINGS INGESTION & RECONCILIATION
    # -------------------------------------------------------------------------
    def fetch_company_earnings(
        self,
        identity: CompanyIdentity,
        primary_financials: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[DrishtiEarningsRecord]:
        """
        Retrieves earnings filings and performs strict financial reconciliation against primary filings.
        """
        if not self.is_available():
            return []

        clean_sym = identity.nse_symbol or identity.primary_symbol
        scrip = identity.bse_code
        params = {"symbols": [clean_sym], "detailed": True, "limit": limit}
        if scrip:
            params["scrip_codes"] = [scrip]

        cache_key = self.cache.build_cache_key(identity.company_id, "/v1/earnings", params)
        cached = self.cache.get(cache_key)

        raw_items = []
        if cached:
            raw_items = cached.get("data", [])
        else:
            try:
                resp = self.client.get_earnings(
                    symbols=[clean_sym] if clean_sym else None,
                    scrip_codes=[scrip] if scrip else None,
                    detailed=True,
                    limit=limit
                )
                raw_items = resp.get("data", []) if isinstance(resp, dict) else []
                self.cache.set(cache_key, raw_items, ttl_seconds=TTL_EARNINGS)
            except Exception as e:
                logger.warning(f"Drishti earnings fetch failed for {identity.company_id}: {e}")
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])

        validated = DrishtiIdentityFirewall.filter_and_validate_batch(raw_items, identity, "/v1/earnings")

        earnings_records: List[DrishtiEarningsRecord] = []
        for item in validated:
            earnings_tbl = item.get("earnings_table") or {}
            
            # Cross-reconcile with primary numbers if provided
            verification_status = "VALIDATED"
            if primary_financials and isinstance(earnings_tbl, dict):
                recon = FinancialReconciler.reconcile_metrics(earnings_tbl, primary_financials)
                verification_status = recon.get("overall_status", "VALIDATED")

            rec = DrishtiEarningsRecord(
                company_id=identity.company_id,
                company_name=identity.legal_name or identity.display_name,
                isin=identity.isin,
                nse_symbol=identity.nse_symbol,
                bse_code=identity.bse_code,
                source_endpoint="/v1/earnings",
                source_id=str(item.get("id") or ""),
                document_type="EARNINGS",
                publication_date=str(item.get("date") or ""),
                event_date=str(item.get("date") or ""),
                period=str(item.get("quarter") or ""),
                source_url="",
                raw_payload=item,
                verification_status=verification_status,
                quarter=str(item.get("quarter") or ""),
                summary=str(item.get("summary") or ""),
                earnings_significant=bool(item.get("earnings_significant", False)),
                earnings_table=earnings_tbl if isinstance(earnings_tbl, dict) else {}
            )
            earnings_records.append(rec)

        return earnings_records

    # -------------------------------------------------------------------------
    # 4. CONCALLS INGESTION & CHUNKING
    # -------------------------------------------------------------------------
    def fetch_company_concalls(
        self,
        identity: CompanyIdentity,
        limit: int = 5
    ) -> List[DrishtiConcallRecord]:
        """
        Retrieves conference calls, transcripts, and generates company-scoped RAG chunks.
        """
        if not self.is_available():
            return []

        clean_sym = identity.nse_symbol or identity.primary_symbol
        scrip = identity.bse_code
        params = {"symbols": [clean_sym], "detailed": True, "limit": limit}
        if scrip:
            params["scrip_codes"] = [scrip]

        cache_key = self.cache.build_cache_key(identity.company_id, "/v1/concalls", params)
        cached = self.cache.get(cache_key)

        raw_items = []
        if cached:
            raw_items = cached.get("data", [])
        else:
            try:
                resp = self.client.get_concalls(
                    symbols=[clean_sym] if clean_sym else None,
                    scrip_codes=[scrip] if scrip else None,
                    detailed=True,
                    limit=limit
                )
                raw_items = resp.get("data", []) if isinstance(resp, dict) else []
                self.cache.set(cache_key, raw_items, ttl_seconds=TTL_CONCALLS)
            except Exception as e:
                logger.warning(f"Drishti concalls fetch failed for {identity.company_id}: {e}")
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])

        validated = DrishtiIdentityFirewall.filter_and_validate_batch(raw_items, identity, "/v1/concalls")

        concall_records: List[DrishtiConcallRecord] = []
        for item in validated:
            call_id = str(item.get("id") or "")
            quarter = str(item.get("quarter") or "")
            date_str = str(item.get("date") or "")
            
            # Extract transcript text or analysis to chunk
            short_an = item.get("short_analysis", {}) if isinstance(item.get("short_analysis"), dict) else {}
            exp_an = item.get("expanded_analysis", {}) if isinstance(item.get("expanded_analysis"), dict) else {}
            
            # Combine available narrative for RAG chunking
            narrative_parts = []
            if isinstance(short_an, dict):
                for k, v in short_an.items():
                    if isinstance(v, str): narrative_parts.append(v)
            if isinstance(exp_an, dict):
                for k, v in exp_an.items():
                    if isinstance(v, str): narrative_parts.append(v)
            full_narrative = "\n\n".join(narrative_parts)

            chunks = []
            if full_narrative:
                chunks = self.concall_store.add_transcript(
                    company_id=identity.company_id,
                    document_id=call_id,
                    quarter=quarter,
                    date=date_str,
                    text=full_narrative
                )

            rec = DrishtiConcallRecord(
                company_id=identity.company_id,
                company_name=identity.legal_name or identity.display_name,
                isin=identity.isin,
                nse_symbol=identity.nse_symbol,
                bse_code=identity.bse_code,
                source_endpoint="/v1/concalls",
                source_id=call_id,
                document_type="CONCALL",
                publication_date=date_str,
                event_date=date_str,
                period=quarter,
                source_url=str(item.get("transcript_url") or ""),
                raw_payload=item,
                verification_status="VALIDATED",
                quarter=quarter,
                transcript_url=str(item.get("transcript_url") or ""),
                audio_url=str(item.get("audio_url") or ""),
                short_analysis=short_an,
                expanded_analysis=exp_an,
                chunks=chunks
            )
            concall_records.append(rec)

        return concall_records

    # -------------------------------------------------------------------------
    # 5. ALERTS INGESTION
    # -------------------------------------------------------------------------
    def fetch_company_alerts(
        self,
        identity: CompanyIdentity,
        limit: int = 10
    ) -> List[DrishtiAlertRecord]:
        """
        Retrieves company alerts filtered by identity.
        """
        if not self.is_available():
            return []

        clean_sym = identity.nse_symbol or identity.primary_symbol
        scrip = identity.bse_code
        params = {"symbols": [clean_sym], "limit": limit}
        if scrip:
            params["scrip_codes"] = [scrip]

        cache_key = self.cache.build_cache_key(identity.company_id, "/v1/alerts", params)
        cached = self.cache.get(cache_key)

        raw_items = []
        if cached:
            raw_items = cached.get("data", [])
        else:
            try:
                resp = self.client.get_alerts(
                    symbols=[clean_sym] if clean_sym else None,
                    scrip_codes=[scrip] if scrip else None,
                    limit=limit
                )
                raw_items = resp.get("data", []) if isinstance(resp, dict) else []
                self.cache.set(cache_key, raw_items, ttl_seconds=TTL_ALERTS)
            except Exception as e:
                logger.warning(f"Drishti alerts fetch failed for {identity.company_id}: {e}")
                stale = self.cache.get_stale_or_any(cache_key)
                if stale:
                    raw_items = stale.get("data", [])

        validated = DrishtiIdentityFirewall.filter_and_validate_batch(raw_items, identity, "/v1/alerts")

        alert_records: List[DrishtiAlertRecord] = []
        for item in validated:
            rec = DrishtiAlertRecord(
                company_id=identity.company_id,
                company_name=identity.legal_name or identity.display_name,
                isin=identity.isin,
                nse_symbol=identity.nse_symbol,
                bse_code=identity.bse_code,
                source_endpoint="/v1/alerts",
                source_id=str(item.get("id") or ""),
                document_type="ALERT",
                publication_date=str(item.get("timestamp") or ""),
                event_date=str(item.get("timestamp") or ""),
                raw_payload=item,
                verification_status="VALIDATED",
                alert_type=str(item.get("type") or "Market Alert"),
                reason=str(item.get("reason") or ""),
                timestamp=str(item.get("timestamp") or ""),
                price=float(item["price"]) if item.get("price") is not None else None,
                meta=item.get("meta", {}) if isinstance(item.get("meta"), dict) else {}
            )
            alert_records.append(rec)

        return alert_records

    # -------------------------------------------------------------------------
    # 6. ALL-IN-ONE STRUCTURED COMPANY INTELLIGENCE
    # -------------------------------------------------------------------------
    def fetch_all_company_intelligence(
        self,
        symbol: str,
        primary_financials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gathers all company intelligence across News, Announcements, Earnings, Concalls, and Alerts.
        Returns a structured package with complete data provenance and identity verification.
        """
        canonical_identity = resolve_canonical_identity(symbol)

        if not self.is_available():
            return {
                "is_configured": False,
                "company_id": canonical_identity.company_id,
                "news": [],
                "announcements": [],
                "earnings": [],
                "concalls": [],
                "alerts": [],
                "source": "DRISHTI",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "status": "NOT_CONFIGURED"
            }

        news = self.fetch_company_news(canonical_identity)
        announcements = self.fetch_company_announcements(canonical_identity)
        earnings = self.fetch_company_earnings(canonical_identity, primary_financials)
        concalls = self.fetch_company_concalls(canonical_identity)
        alerts = self.fetch_company_alerts(canonical_identity)

        return {
            "is_configured": True,
            "company_id": canonical_identity.company_id,
            "company_name": canonical_identity.legal_name,
            "isin": canonical_identity.isin,
            "nse_symbol": canonical_identity.nse_symbol,
            "bse_code": canonical_identity.bse_code,
            "news": news,
            "announcements": announcements,
            "earnings": earnings,
            "concalls": concalls,
            "alerts": alerts,
            "source": "DRISHTI",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "status": "SUCCESS"
        }


# Global singleton instance
_DRISHTI_SERVICE: Optional[DrishtiService] = None

def get_drishti_service() -> DrishtiService:
    """Returns the shared DrishtiService singleton."""
    global _DRISHTI_SERVICE
    if _DRISHTI_SERVICE is None:
        _DRISHTI_SERVICE = DrishtiService()
    return _DRISHTI_SERVICE
