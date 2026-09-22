"""
Symbol Resolver Utility (utils/symbol_resolver.py)
Auto-resolves company names and unformatted ticker inputs into clean NSE/BSE symbols.
Uses yfinance.Search to discover Indian equity quotes with fallback to standard ticker formatting.
"""

import logging
from typing import Optional, Tuple

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger("ResearchBeast.SymbolResolver")


def resolve_ticker(user_input: str) -> str:
    """
    Resolves user input (company name or raw ticker) into a canonical NSE/BSE symbol.
    - If already clean (e.g. 'VINATIORGA.NS' or 'HDFCBANK.BO'), returns upper-case symbol.
    - If company name or un-suffixed (e.g. 'vinati organics', 'tata motors'), looks up
      matching equity quotes on NSE/BSE via yfinance.Search, preferring .NS.
    - Falls back to uppercase symbol with .NS suffix.
    """
    sym, _ = resolve_ticker_info(user_input)
    return sym


def resolve_ticker_info(user_input: str) -> Tuple[str, Optional[str]]:
    """
    Resolves user input and returns a tuple of (resolved_symbol, matched_name).
    """
    cleaned = str(user_input or "").strip()
    if not cleaned:
        return "", None

    # 1. Check if already a clean ticker with exchange suffix and no spaces
    if "." in cleaned and " " not in cleaned:
        up = cleaned.upper()
        if up.endswith((".NS", ".BO")):
            return up, None
        if up.endswith(".NSE"):
            return up[:-4] + ".NS", None
        if up.endswith(".BSE"):
            return up[:-4] + ".BO", None

    # 2. Search Yahoo Finance for matching equity quotes
    if yf is not None:
        try:
            s = yf.Search(cleaned, max_results=8)
            quotes = s.quotes or []

            # 2a. Priority 1: Indian equity quotes ending in .NS
            for q in quotes:
                sym = str(q.get("symbol", "")).strip().upper()
                qtype = str(q.get("quoteType", "")).upper()
                if sym.endswith(".NS") and qtype in ["EQUITY", "ETF", ""]:
                    name = q.get("longname") or q.get("shortname")
                    return sym, name

            # 2b. Priority 2: Indian equity quotes ending in .BO
            for q in quotes:
                sym = str(q.get("symbol", "")).strip().upper()
                qtype = str(q.get("quoteType", "")).upper()
                if sym.endswith(".BO") and qtype in ["EQUITY", "ETF", ""]:
                    name = q.get("longname") or q.get("shortname")
                    return sym, name

            # 2c. Priority 3: Check exchange attribute (NSI / NSE / BSE)
            for q in quotes:
                exch = str(q.get("exchange", "")).upper()
                sym = str(q.get("symbol", "")).strip().upper()
                qtype = str(q.get("quoteType", "")).upper()
                if qtype in ["EQUITY", "ETF", ""]:
                    if exch in ["NSI", "NSE"]:
                        full_sym = sym if "." in sym else f"{sym}.NS"
                        return full_sym, q.get("longname") or q.get("shortname")
                    if exch == "BSE":
                        full_sym = sym if "." in sym else f"{sym}.BO"
                        return full_sym, q.get("longname") or q.get("shortname")

            # 2d. Priority 4: Any quote with .NS or .BO
            for q in quotes:
                sym = str(q.get("symbol", "")).strip().upper()
                if sym.endswith((".NS", ".BO")):
                    return sym, q.get("longname") or q.get("shortname")

            # 2e. If only US/Global quote found and input was a single word without spaces
            if " " not in cleaned and quotes:
                first_sym = str(quotes[0].get("symbol", "")).strip().upper()
                if first_sym.endswith((".NS", ".BO")):
                    return first_sym, quotes[0].get("longname")

        except Exception as exc:
            logger.debug(f"yfinance symbol resolution search error for '{cleaned}': {exc}")

    # 3. Fallback: Strip spaces and append .NS
    clean_raw = cleaned.replace(" ", "").upper()
    if clean_raw.endswith((".NS", ".BO")):
        return clean_raw, None
    return f"{clean_raw}.NS", None
