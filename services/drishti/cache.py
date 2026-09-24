"""
Intelligent Persistent Cache for Drishti API (services/drishti/cache.py)
Prevents exhausting Drishti Sandbox credit limits.
Features:
1. Deterministic cache key based on company_id, endpoint, and query parameters.
2. In-memory L1 cache + Disk-backed L2 JSON cache.
3. TTL enforcement with graceful stale-data fallback during rate limits (HTTP 429).
4. Tracks retrieval and expiration timestamps.
"""

import os
import json
import hashlib
import logging
import threading
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("ResearchBeast.Drishti.Cache")

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cache", "drishti")


class DrishtiCache:
    """Thread-safe persistent and in-memory cache for Drishti responses."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create Drishti cache dir '{cache_dir}': {e}")

    @staticmethod
    def build_cache_key(company_id: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Creates a deterministic cache key from company_id, endpoint, and sorted params.
        Format: {sanitized_company_id}_{clean_endpoint}_{param_hash}
        """
        clean_cid = company_id.replace(":", "_").replace("/", "_").replace("\\", "_").upper()
        clean_ep = endpoint.strip("/").replace("/", "_")
        
        param_str = ""
        if params:
            # Sort keys to guarantee deterministic hash
            sorted_items = sorted((str(k), str(v)) for k, v in params.items() if v is not None)
            param_str = json.dumps(sorted_items, sort_keys=True)
        
        param_hash = hashlib.sha256(param_str.encode("utf-8")).hexdigest()[:12] if param_str else "default"
        return f"{clean_cid}__{clean_ep}__{param_hash}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached response if valid and not expired.
        Returns: Dict with {"data": ..., "retrieved_at": ..., "expires_at": ..., "is_stale": False} or None
        """
        with self._lock:
            # 1. Check in-memory cache
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if self._is_valid(entry):
                    return entry

            # 2. Check disk cache
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        entry = json.load(f)
                    if self._is_valid(entry):
                        self._memory_cache[key] = entry
                        return entry
                except Exception as e:
                    logger.warning(f"Error reading disk cache for {key}: {e}")

        return None

    def get_stale_or_any(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Returns cached response even if expired.
        Used as a safety net during rate-limiting (HTTP 429) or upstream outages.
        """
        with self._lock:
            if key in self._memory_cache:
                entry = dict(self._memory_cache[key])
                entry["is_stale"] = True
                return entry

            file_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        entry = json.load(f)
                    entry["is_stale"] = True
                    self._memory_cache[key] = entry
                    return entry
                except Exception:
                    pass

        return None

    def set(self, key: str, data: Any, ttl_seconds: int = 3600) -> None:
        """
        Persists response payload to memory and disk with expiration timestamp.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        entry = {
            "key": key,
            "data": data,
            "retrieved_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "source": "DRISHTI",
            "is_stale": False,
        }

        with self._lock:
            self._memory_cache[key] = entry
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(entry, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Error writing Drishti disk cache for {key}: {e}")

    @staticmethod
    def _is_valid(entry: Dict[str, Any]) -> bool:
        """Checks if a cache entry is within its expiration window."""
        exp_str = entry.get("expires_at")
        if not exp_str:
            return False
        try:
            exp_dt = datetime.fromisoformat(exp_str)
            now = datetime.now(timezone.utc)
            return now < exp_dt
        except Exception:
            return False


# Global default cache singleton
_DRISHTI_CACHE = DrishtiCache()

def get_drishti_cache() -> DrishtiCache:
    """Returns the process-wide DrishtiCache instance."""
    return _DRISHTI_CACHE
