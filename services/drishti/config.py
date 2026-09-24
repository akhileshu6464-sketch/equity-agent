"""
Drishti Configuration & Credentials Gate (services/drishti/config.py)
Strictly enforces server-side credential isolation for Drishti API.
Never exposes DRISHTI_API_KEY to frontend or client-facing responses.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("ResearchBeast.Drishti.Config")

DEFAULT_DRISHTI_BASE_URL = "https://developers.manasija.in/v1"
DRISHTI_ENV_VAR = "DRISHTI_API_KEY"

# Cache TTL settings in seconds
TTL_METADATA = 86400 * 7       # 7 days for company metadata
TTL_EARNINGS = 86400 * 3       # 3 days for earnings filings
TTL_CONCALLS = 86400 * 3       # 3 days for concalls
TTL_ANNOUNCEMENTS = 3600 * 4   # 4 hours for corporate announcements
TTL_NEWS = 3600 * 2            # 2 hours for news
TTL_ALERTS = 3600 * 1          # 1 hour for market alerts


def get_drishti_api_key() -> Optional[str]:
    """
    Retrieves the Drishti API key strictly from the server-side environment.
    Never exposes or logs the raw API key.
    """
    key = os.environ.get(DRISHTI_ENV_VAR, "").strip()
    return key if key else None


def is_drishti_configured() -> bool:
    """Returns True if a valid Drishti API key is configured on the server."""
    key = get_drishti_api_key()
    return bool(key and len(key) >= 8)


def get_drishti_base_url() -> str:
    """Returns the Drishti API base URL."""
    return os.environ.get("DRISHTI_BASE_URL", DEFAULT_DRISHTI_BASE_URL).rstrip("/")


def mask_api_key(key: Optional[str]) -> str:
    """Safely masks API key for internal server logging."""
    if not key:
        return "[NOT_SET]"
    if len(key) <= 8:
        return "***"
    return f"{key[:3]}...{key[-4:]}"
