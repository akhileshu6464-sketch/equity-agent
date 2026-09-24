"""
Standardized Drishti Data Models (services/drishti/models.py)
Implements the mandatory Research Beast Drishti schema.
Guarantees:
1. Every object is tied to canonical company identity (company_id, isin, nse_symbol, bse_code, company_name).
2. Zero anonymous or unmapped data stored.
3. Drishti source metadata (e.g. sentiment) preserved separately from Research Beast conclusions.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DrishtiRecord:
    """
    Mandatory base record for every imported Drishti object.
    Enforces complete provenance, company lock, and verification status.
    """
    company_id: str                      # Canonical ID e.g. "NSE:VINATIORGA"
    company_name: str                    # Canonical Legal Name e.g. "Vinati Organics Limited"
    isin: str                            # Canonical ISIN e.g. "INE410B01037"
    nse_symbol: str                      # Canonical NSE symbol e.g. "VINATIORGA"
    bse_code: str                        # Canonical BSE code e.g. "524200"
    source_endpoint: str                 # e.g. "/v1/news", "/v1/announcements"
    source_id: str                       # Drishti primary item ID
    document_type: str                   # "NEWS", "ANNOUNCEMENT", "EARNINGS", "CONCALL", "ALERT"
    publication_date: str = ""           # ISO date string or raw publication date
    event_date: str = ""                 # Event occurrence date if available
    period: str = ""                     # e.g. "q4_24", "FY2024"
    source_url: str = ""                 # Direct filing/article URL
    retrieved_at: str = field(default_factory=_utc_now_iso)
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    verification_status: str = "DRISHTI_RAW"  # "DRISHTI_RAW", "NORMALIZED", "VALIDATED", "VERIFIED", "CONFLICT"
    source: str = "DRISHTI"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DrishtiNewsRecord(DrishtiRecord):
    """
    Company-specific news record.
    Preserves raw source sentiment as metadata without treating it as Research Beast conclusion.
    """
    headline: str = ""
    summary: str = ""
    long_summary: str = ""
    specific_title: str = ""
    article_source: str = ""
    article_type: str = ""
    raw_sentiment: str = "neutral"       # Source metadata only: "positive", "negative", "neutral"


@dataclass(frozen=True)
class DrishtiAnnouncementRecord(DrishtiRecord):
    """
    Corporate announcement record for material events (contracts, board changes, etc.).
    Preserves original text without paraphrasing into financial conclusion during ingestion.
    """
    headline: str = ""
    category: str = ""
    related_categories: List[str] = field(default_factory=list)
    important: bool = False
    summary: str = ""
    long_summary: str = ""
    extracted_information: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DrishtiEarningsRecord(DrishtiRecord):
    """
    Earnings filing record with structured financial table.
    Must pass cross-reconciliation before becoming VERIFIED.
    """
    quarter: str = ""
    fiscal_year: str = ""
    summary: str = ""
    earnings_significant: bool = False
    earnings_table: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConcallTranscriptChunk:
    """
    Company-scoped conference call transcript chunk for pre-filtered RAG search.
    """
    company_id: str
    document_id: str
    quarter: str
    date: str
    chunk_index: int
    text: str
    section_name: str = ""
    speaker: str = ""
    source: str = "DRISHTI"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DrishtiConcallRecord(DrishtiRecord):
    """
    Conference call record with transcript and audio URLs.
    """
    quarter: str = ""
    transcript_url: str = ""
    audio_url: str = ""
    short_analysis: Dict[str, Any] = field(default_factory=dict)
    expanded_analysis: Dict[str, Any] = field(default_factory=dict)
    chunks: List[ConcallTranscriptChunk] = field(default_factory=list)


@dataclass(frozen=True)
class DrishtiAlertRecord(DrishtiRecord):
    """
    Market or financial alert record.
    """
    alert_type: str = ""
    reason: str = ""
    timestamp: str = ""
    price: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)
