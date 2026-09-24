"""
Drishti Financial Intelligence Service Package (services/drishti)
Direct structured data adapter for Drishti API in Research Beast.
Enforces:
- Server-side credentials (DRISHTI_API_KEY)
- Strict Company Identity Firewall (zero cross-company contamination)
- Normalization into immutable DrishtiRecord models
- Critical Financial Data Rule (reconciliation against primary filings)
- Intelligent disk/memory caching with graceful rate-limit handling
- Company-scoped transcript chunking for pre-filtered RAG search
"""

from services.drishti.config import (
    get_drishti_api_key,
    is_drishti_configured,
    get_drishti_base_url,
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
from services.drishti.cache import DrishtiCache, get_drishti_cache
from services.drishti.identity_firewall import (
    DrishtiIdentityFirewall,
    DrishtiIdentityMismatchError,
)
from services.drishti.client import (
    DrishtiApiClient,
    DrishtiError,
    DrishtiAuthError,
    DrishtiRateLimitError,
    DrishtiConnectionError,
)
from services.drishti.reconciler import FinancialReconciler
from services.drishti.concall_store import ConcallStore, get_concall_store
from services.drishti.service import DrishtiService, get_drishti_service

__all__ = [
    "get_drishti_api_key",
    "is_drishti_configured",
    "get_drishti_base_url",
    "mask_api_key",
    "DrishtiRecord",
    "DrishtiNewsRecord",
    "DrishtiAnnouncementRecord",
    "DrishtiEarningsRecord",
    "DrishtiConcallRecord",
    "ConcallTranscriptChunk",
    "DrishtiAlertRecord",
    "DrishtiCache",
    "get_drishti_cache",
    "DrishtiIdentityFirewall",
    "DrishtiIdentityMismatchError",
    "DrishtiApiClient",
    "DrishtiError",
    "DrishtiAuthError",
    "DrishtiRateLimitError",
    "DrishtiConnectionError",
    "FinancialReconciler",
    "ConcallStore",
    "get_concall_store",
    "DrishtiService",
    "get_drishti_service",
]
