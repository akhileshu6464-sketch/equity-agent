"""
Exchange Tickers Data Ingestion & Seed Script
Fetches and standardizes equity tickers listed on NSE and BSE.

Deduplication & Formatting Rules:
1. Strict NSE Priority: If a company exists on both NSE and BSE, keep ONLY the NSE listing.
2. Textual Symbols Only: Strip all numeric scrip codes (e.g. 500325). For BSE-only companies,
   use their textual scrip ID (e.g. ANDHRAPET).
3. Background Ticker Resolution: Include internal 'ticker' field (e.g. CROMPTON.NS) for backend
   financial data fetching while keeping 'symbol' clean (CROMPTON).

Outputs: data/listed_companies.json
Schema: [
    {"symbol": "INFY", "name": "Infosys Limited", "ticker": "INFY.NS", "exchange": "NSE"},
    {"symbol": "ANDHRAPET", "name": "Andhra Petrochemicals Ltd", "ticker": "500012.BO", "exchange": "BSE"},
    ...
]
"""

import os
import sys
import json
import csv
import io
import re
import logging
import urllib.request
from typing import List, Dict, Any, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ExchangeTickersSeed")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "listed_companies.json")

# Official Data Sources
NSE_EQUITY_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
BSE_EQUITY_URL = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&Industry=&segment=Equity&status=Active"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def normalize_company_name(name: str) -> str:
    """Normalizes company names for robust cross-exchange deduplication."""
    if not name:
        return ""
    name = name.upper()
    # Remove parenthetical descriptions, e.g. (India), (Holdings)
    name = re.sub(r"[\(\[].*?[\)\]]", "", name)
    # Remove corporate designations
    name = re.sub(r"\b(LIMITED|LTD|PVT|PRIVATE|CORP|CORPORATION|INDIA|HOLDINGS|HOLDING|ENTERPRISES|INDUSTRIES|CO)\b", "", name)
    # Keep only alphanumeric
    name = re.sub(r"[^A-Z0-9]", "", name)
    return name.strip()


def fetch_nse_equities() -> Tuple[List[Dict[str, str]], Set[str], Set[str], Set[str]]:
    """
    Downloads and parses the official NSE equity list (EQUITY_L.csv).
    Returns (companies, nse_isins, nse_symbols, nse_normalized_names).
    """
    logger.info("Fetching official NSE equity list from archives.nseindia.com...")
    companies = []
    nse_isins = set()
    nse_symbols = set()
    nse_names = set()

    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(
                NSE_EQUITY_URL,
                headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k}
                series = cleaned_row.get("SERIES", "").upper()
                symbol = cleaned_row.get("SYMBOL", "").strip().upper()
                name = cleaned_row.get("NAME OF COMPANY", "").strip()
                isin = cleaned_row.get("ISIN NUMBER", "").strip().upper()

                # Filter for active common equity shares (EQ = Normal, BE = Trade to Trade)
                if series in ["EQ", "BE"] and symbol and name:
                    # Pure textual symbol without .NS suffix
                    companies.append({
                        "symbol": symbol,
                        "name": name,
                        "ticker": f"{symbol}.NS",
                        "exchange": "NSE"
                    })
                    if isin:
                        nse_isins.add(isin)
                    nse_symbols.add(symbol)
                    c_name = normalize_company_name(name)
                    if c_name:
                        nse_names.add(c_name)

            logger.info(f"Successfully processed {len(companies)} active NSE equities.")
            break
        except Exception as e:
            logger.warning(f"NSE fetch attempt {attempt} failed: {e}")
            if attempt == 3:
                logger.error("All NSE fetch attempts failed.")

    return companies, nse_isins, nse_symbols, nse_names


def fetch_bse_equities(nse_isins: Set[str], nse_symbols: Set[str], nse_names: Set[str]) -> List[Dict[str, str]]:
    """
    Downloads and parses BSE equities.
    Deduplicates against NSE (strict NSE priority).
    For BSE-only companies, replaces numeric scrip codes with textual scrip IDs.
    """
    logger.info("Fetching official BSE active scrips from api.bseindia.com...")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bseindia.com/",
        "Origin": "https://www.bseindia.com"
    }

    bse_only_companies = []
    # Non-equity / debt keywords to filter out
    exclude_keywords = [
        "warrant", "debenture", "pref. share", "preference share",
        "perpetual debt", "partly paid", "ncd", "bonds"
    ]

    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(BSE_EQUITY_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw_data = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(raw_data)

            duplicates_dropped = 0
            seen_bse_symbols = set()

            for item in data:
                segment = item.get("Segment", "")
                status = item.get("Status", "")
                scrip_cd = str(item.get("SCRIP_CD", "")).strip()
                scrip_id = str(item.get("scrip_id", "")).strip().upper()
                isin = str(item.get("ISIN_NUMBER", "")).strip().upper()
                name = str(item.get("Issuer_Name") or item.get("Scrip_Name", "")).strip()

                if segment == "Equity" and status == "Active" and scrip_cd and name:
                    name_lower = name.lower()
                    if any(kw in name_lower for kw in exclude_keywords):
                        continue
                    if name.endswith("-W") or name.endswith("-PP"):
                        continue

                    # Textual scrip ID (no numeric codes!)
                    clean_sym = scrip_id if (scrip_id and not scrip_id.isdigit()) else ""
                    if not clean_sym:
                        words = [w for w in re.sub(r"[^A-Z0-9\s]", "", name.upper()).split() if w]
                        clean_sym = words[0] if words else f"BSE{scrip_cd}"

                    # Strict NSE priority deduplication:
                    # Check if company exists on NSE via ISIN, Symbol, or Normalized Name
                    c_name = normalize_company_name(name)
                    is_duplicate_of_nse = (
                        (isin and isin in nse_isins) or
                        (clean_sym and clean_sym in nse_symbols) or
                        (c_name and c_name in nse_names)
                    )

                    if is_duplicate_of_nse:
                        duplicates_dropped += 1
                        continue

                    if clean_sym in seen_bse_symbols:
                        continue
                    seen_bse_symbols.add(clean_sym)

                    # BSE-only company: user sees clean textual scrip ID, backend uses scrip code
                    bse_only_companies.append({
                        "symbol": clean_sym,
                        "name": name,
                        "ticker": f"{scrip_cd}.BO",
                        "exchange": "BSE"
                    })

            logger.info(
                f"BSE Processing: Dropped {duplicates_dropped} dual-listed duplicates (strict NSE priority). "
                f"Retained {len(bse_only_companies)} BSE-only unique equities with textual scrip IDs."
            )
            break
        except Exception as e:
            logger.warning(f"BSE fetch attempt {attempt} failed: {e}")
            if attempt < 3:
                import time
                time.sleep(3)
            else:
                logger.error("All BSE fetch attempts failed.")

    return bse_only_companies


def get_fallback_tickers() -> List[Dict[str, str]]:
    """
    Fallback institutional dataset in case network endpoints are unavailable.
    Guarantees zero dual duplicates and clean textual symbols only.
    """
    return [
        {"symbol": "RELIANCE", "name": "Reliance Industries Limited", "ticker": "RELIANCE.NS", "exchange": "NSE"},
        {"symbol": "TCS", "name": "Tata Consultancy Services Limited", "ticker": "TCS.NS", "exchange": "NSE"},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Limited", "ticker": "HDFCBANK.NS", "exchange": "NSE"},
        {"symbol": "INFY", "name": "Infosys Limited", "ticker": "INFY.NS", "exchange": "NSE"},
        {"symbol": "CROMPTON", "name": "Crompton Greaves Consumer Electricals Limited", "ticker": "CROMPTON.NS", "exchange": "NSE"},
        {"symbol": "TATACONSUM", "name": "Tata Consumer Products Limited", "ticker": "TATACONSUM.NS", "exchange": "NSE"},
        {"symbol": "ICICIBANK", "name": "ICICI Bank Limited", "ticker": "ICICIBANK.NS", "exchange": "NSE"},
        {"symbol": "ITC", "name": "ITC Limited", "ticker": "ITC.NS", "exchange": "NSE"},
        {"symbol": "SBIN", "name": "State Bank of India", "ticker": "SBIN.NS", "exchange": "NSE"},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel Limited", "ticker": "BHARTIARTL.NS", "exchange": "NSE"},
        {"symbol": "LT", "name": "Larsen & Toubro Limited", "ticker": "LT.NS", "exchange": "NSE"},
        {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Limited", "ticker": "KOTAKBANK.NS", "exchange": "NSE"},
        {"symbol": "ANDHRAPET", "name": "Andhra Petrochemicals Limited", "ticker": "500012.BO", "exchange": "BSE"},
        {"symbol": "AMBALALSA", "name": "Ambalal Sarabhai Enterprises Ltd", "ticker": "500009.BO", "exchange": "BSE"},
    ]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    nse_equities, nse_isins, nse_symbols, nse_names = fetch_nse_equities()

    if nse_equities:
        bse_equities = fetch_bse_equities(nse_isins, nse_symbols, nse_names)
    else:
        logger.warning("NSE list empty; using fallback seed dataset.")
        combined = get_fallback_tickers()
        nse_equities = [c for c in combined if c["exchange"] == "NSE"]
        bse_equities = [c for c in combined if c["exchange"] == "BSE"]

    combined = nse_equities + bse_equities

    # Deduplicate strictly by symbol
    seen_symbols = set()
    deduped = []
    for item in combined:
        sym = item["symbol"].upper()
        if sym not in seen_symbols:
            seen_symbols.add(sym)
            deduped.append(item)

    # Sort: NSE entries first, then BSE, alphabetically by company name
    deduped.sort(key=lambda x: (0 if x["exchange"] == "NSE" else 1, x["name"].lower()))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    logger.info(
        f"Master tickers file successfully created at {OUTPUT_FILE}: "
        f"{len(deduped)} total companies ({size_kb:.1f} KB)."
    )
    print(f"Total equities: {len(deduped)} (NSE: {len(nse_equities)}, BSE-only: {len(bse_equities)})")
    print(f"Output saved to: {OUTPUT_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
