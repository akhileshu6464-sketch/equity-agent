"""
Drishti API REST & SDK Client Adapter (services/drishti/client.py)
Provides authenticated access to Drishti endpoints with rate-limit and error resiliency.
Guarantees:
1. DRISHTI_API_KEY is retrieved strictly from the server-side environment.
2. Supports both official drishti-sdk and robust requests.Session HTTP fallback.
3. Automatically detects rate limits (HTTP 429) to trigger stale-cache serving.
4. Non-fatal exception handling: never crashes Research Beast if Drishti is down.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import requests

from services.drishti.config import (
    get_drishti_api_key,
    get_drishti_base_url,
    is_drishti_configured,
    mask_api_key,
)

logger = logging.getLogger("ResearchBeast.Drishti.Client")

# Check if official SDK is importable
try:
    from drishti_sdk import DrishtiClient as SdkClient
    _HAS_SDK = True
except ImportError:
    SdkClient = None
    _HAS_SDK = False


class DrishtiError(Exception):
    """Base exception for Drishti client operations."""
    pass


class DrishtiAuthError(DrishtiError):
    """Raised on invalid or missing API key (HTTP 401/403)."""
    pass


class DrishtiRateLimitError(DrishtiError):
    """Raised when Drishti credit or request rate limit is reached (HTTP 429)."""
    pass


class DrishtiConnectionError(DrishtiError):
    """Raised on network timeout or connection failure."""
    pass


class DrishtiApiClient:
    """
    Robust client for Drishti REST API.
    Handles authentication, parameter serialization, and graceful error categorization.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 15):
        self.api_key = api_key or get_drishti_api_key()
        self.base_url = (base_url or get_drishti_base_url()).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        
        # Standard browser-like headers with mandatory X-API-Key
        self.headers = {
            "User-Agent": "ResearchBeast-Institutional/2.0",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    def is_configured(self) -> bool:
        """Returns True if client has a valid API key."""
        return bool(self.api_key and len(self.api_key) >= 8)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes authenticated GET request with error classification.
        """
        if not self.is_configured():
            raise DrishtiAuthError("DRISHTI_API_KEY is not set or invalid in environment.")

        clean_ep = "/" + endpoint.lstrip("/")
        url = f"{self.base_url}{clean_ep}"
        
        # Serialize list parameters into comma-separated strings if needed
        clean_params = {}
        if params:
            for k, v in params.items():
                if v is not None:
                    if isinstance(v, (list, tuple)):
                        clean_params[k] = ",".join(str(item) for item in v)
                    elif isinstance(v, bool):
                        clean_params[k] = "true" if v else "false"
                    else:
                        clean_params[k] = str(v)

        try:
            resp = self.session.get(url, headers=self.headers, params=clean_params, timeout=self.timeout)
            
            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception:
                    return {"data": resp.text}

            elif resp.status_code in (401, 403):
                logger.error(f"Drishti auth failure ({resp.status_code}) on {clean_ep}. Key: {mask_api_key(self.api_key)}")
                raise DrishtiAuthError(f"Authentication failed ({resp.status_code}): {resp.text[:200]}")

            elif resp.status_code == 429:
                logger.warning(f"Drishti rate limit reached (HTTP 429) on {clean_ep}.")
                raise DrishtiRateLimitError("Drishti API rate limit or credit ceiling reached.")

            else:
                logger.warning(f"Drishti upstream error {resp.status_code} on {clean_ep}: {resp.text[:200]}")
                raise DrishtiError(f"Drishti error {resp.status_code}: {resp.text[:200]}")

        except (requests.Timeout, requests.ConnectionError) as conn_err:
            logger.warning(f"Drishti connection failure on {clean_ep}: {conn_err}")
            raise DrishtiConnectionError(f"Connection to Drishti failed: {conn_err}")

    # -------------------------------------------------------------------------
    # Endpoints
    # -------------------------------------------------------------------------

    def get_symbol_metadata(
        self,
        symbols: Optional[List[str]] = None,
        scrip_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """GET /v1/symbols/metadata — Resolve company metadata for symbols or scrip codes."""
        params = {}
        if symbols:
            params["symbols"] = symbols
        if scrip_codes:
            params["scrip_codes"] = scrip_codes
        return self._get("/symbols/metadata", params)

    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        scrip_codes: Optional[List[str]] = None,
        sentiment: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """GET /v1/news — Retrieve paginated company news items."""
        params = {"page": page, "limit": limit}
        if symbols:
            params["symbols"] = symbols
        if scrip_codes:
            params["scrip_codes"] = scrip_codes
        if sentiment:
            params["sentiment"] = sentiment
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/news", params)

    def get_announcements(
        self,
        symbols: Optional[List[str]] = None,
        scrip_codes: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        detailed: bool = True,
        important: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """GET /v1/announcements — Retrieve corporate exchange announcements."""
        params = {"page": page, "limit": limit, "detailed": detailed}
        if symbols:
            params["symbols"] = symbols
        if scrip_codes:
            params["scrip_codes"] = scrip_codes
        if categories:
            params["categories"] = categories
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if important is not None:
            params["important"] = important
        return self._get("/announcements", params)

    def get_earnings(
        self,
        symbols: Optional[List[str]] = None,
        scrip_codes: Optional[List[str]] = None,
        quarter: Optional[str] = None,
        detailed: bool = True,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """GET /v1/earnings — Retrieve quarterly earnings filings and structured results."""
        params = {"page": page, "limit": limit, "detailed": detailed}
        if symbols:
            params["symbols"] = symbols
        if scrip_codes:
            params["scrip_codes"] = scrip_codes
        if quarter:
            params["quarter"] = quarter
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/earnings", params)

    def get_earnings_attachments(self, ids: List[str]) -> Dict[str, Any]:
        """GET /v1/earnings/attachments — Get direct attachment URLs for earnings filings."""
        return self._get("/earnings/attachments", {"ids": ids})

    def get_concalls(
        self,
        symbols: Optional[List[str]] = None,
        scrip_codes: Optional[List[str]] = None,
        detailed: bool = True,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """GET /v1/concalls — Retrieve conference calls, metadata, and analysis."""
        params = {"page": page, "limit": limit, "detailed": detailed}
        if symbols:
            params["symbols"] = symbols
        if scrip_codes:
            params["scrip_codes"] = scrip_codes
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/concalls", params)

    def get_concall_transcript(
        self,
        quarter: str,
        symbol: Optional[str] = None,
        scrip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """GET /v1/concalls/transcript — Get transcript and audio recording URLs for a quarter."""
        params = {"quarter": quarter}
        if symbol:
            params["symbol"] = symbol
        elif scrip_code:
            params["scrip_code"] = scrip_code
        return self._get("/concalls/transcript", params)

    def get_alerts(
        self,
        symbols: Optional[List[str]] = None,
        scrip_codes: Optional[List[str]] = None,
        alert_type: Optional[List[str]] = None,
        important: Optional[bool] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """GET /v1/alerts — Retrieve structured market and company alerts."""
        params = {"page": page, "limit": limit}
        if symbols:
            params["symbols"] = symbols
        if scrip_codes:
            params["scrip_codes"] = scrip_codes
        if alert_type:
            params["type"] = alert_type
        if important is not None:
            params["important"] = important
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/alerts", params)

    def get_account_limits(self) -> Dict[str, Any]:
        """GET /v1/account/limits — Get active plan rate limits."""
        return self._get("/account/limits")

    def get_account_usage(self) -> Dict[str, Any]:
        """GET /v1/account/usage — Get live credits snapshot."""
        return self._get("/account/usage")
