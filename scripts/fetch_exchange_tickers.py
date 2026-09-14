"""
Exchange Tickers Data Ingestion & Seed Script
Fetches and standardizes all active equity tickers listed on the National Stock Exchange (NSE)
and Bombay Stock Exchange (BSE) to power instant company search and autocomplete.

Outputs: data/listed_companies.json
Schema: [
    {"symbol": "INFY.NS", "name": "Infosys Limited", "exchange": "NSE"},
    {"symbol": "500209.BO", "name": "Infosys Limited", "exchange": "BSE"},
    ...
]
"""

import os
import sys
import json
import csv
import io
import logging
import urllib.request
from typing import List, Dict, Any

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


def fetch_nse_equities() -> List[Dict[str, str]]:
    """
    Downloads and parses the official NSE equity list (EQUITY_L.csv).
    Filters out debt instruments, mutual funds, ETFs, and retains active equity series (EQ, BE).
    """
    logger.info("Fetching official NSE equity list from archives.nseindia.com...")
    companies = []
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

                # Filter for active common equity shares (EQ = Normal, BE = Trade to Trade)
                if series in ["EQ", "BE"] and symbol and name:
                    companies.append({
                        "symbol": f"{symbol}.NS",
                        "name": name,
                        "exchange": "NSE"
                    })

            logger.info(f"Successfully processed {len(companies)} active NSE equities.")
            break
        except Exception as e:
            logger.warning(f"NSE fetch attempt {attempt} failed: {e}")
            if attempt == 3:
                logger.error("All NSE fetch attempts failed.")

    return companies


def fetch_bse_equities() -> List[Dict[str, str]]:
    """
    Downloads and parses the official BSE active equity scrip directory.
    Filters out debt, warrants, preference shares, and inactive scrips.
    """
    logger.info("Fetching official BSE active scrips from api.bseindia.com...")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bseindia.com/",
        "Origin": "https://www.bseindia.com"
    }

    companies = []
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

            for item in data:
                segment = item.get("Segment", "")
                status = item.get("Status", "")
                scrip_cd = str(item.get("SCRIP_CD", "")).strip()
                scrip_name = str(item.get("Scrip_Name", "")).strip()

                if segment == "Equity" and status == "Active" and scrip_cd and scrip_name:
                    name_lower = scrip_name.lower()
                    if any(kw in name_lower for kw in exclude_keywords):
                        continue
                    if scrip_name.endswith("-W") or scrip_name.endswith("-PP"):
                        continue

                    companies.append({
                        "symbol": f"{scrip_cd}.BO",
                        "name": scrip_name,
                        "exchange": "BSE"
                    })

            logger.info(f"Successfully processed {len(companies)} active BSE equities.")
            break
        except Exception as e:
            logger.warning(f"BSE fetch attempt {attempt} failed: {e}")
            if attempt < 3:
                import time
                time.sleep(3)
            else:
                logger.error("All BSE fetch attempts failed.")

    return companies


def get_fallback_tickers() -> List[Dict[str, str]]:
    """
    Institutional fallback list in case exchange endpoints are temporarily blocked/offline.
    """
    return [
        {"symbol": "RELIANCE.NS", "name": "Reliance Industries Limited", "exchange": "NSE"},
        {"symbol": "TCS.NS", "name": "Tata Consultancy Services Limited", "exchange": "NSE"},
        {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Limited", "exchange": "NSE"},
        {"symbol": "INFY.NS", "name": "Infosys Limited", "exchange": "NSE"},
        {"symbol": "CROMPTON.NS", "name": "Crompton Greaves Consumer Electricals Limited", "exchange": "NSE"},
        {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products Limited", "exchange": "NSE"},
        {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Limited", "exchange": "NSE"},
        {"symbol": "ITC.NS", "name": "ITC Limited", "exchange": "NSE"},
        {"symbol": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE"},
        {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Limited", "exchange": "NSE"},
        {"symbol": "LT.NS", "name": "Larsen & Toubro Limited", "exchange": "NSE"},
        {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Limited", "exchange": "NSE"},
        {"symbol": "500325.BO", "name": "Reliance Industries Limited", "exchange": "BSE"},
        {"symbol": "532540.BO", "name": "Tata Consultancy Services Limited", "exchange": "BSE"},
        {"symbol": "500180.BO", "name": "HDFC Bank Limited", "exchange": "BSE"},
        {"symbol": "500209.BO", "name": "Infosys Limited", "exchange": "BSE"},
        {"symbol": "539876.BO", "name": "Crompton Greaves Consumer Electricals Ltd", "exchange": "BSE"},
        {"symbol": "500800.BO", "name": "Tata Consumer Products Limited", "exchange": "BSE"},
    ]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    nse_equities = fetch_nse_equities()
    bse_equities = fetch_bse_equities()

    if not bse_equities:
        logger.warning("BSE list empty; supplementing with institutional BSE fallbacks.")
        fallback_bse = [t for t in get_fallback_tickers() if t["exchange"] == "BSE"]
        bse_equities.extend(fallback_bse)

    if not nse_equities:
        logger.warning("NSE list empty; supplementing with institutional NSE fallbacks.")
        fallback_nse = [t for t in get_fallback_tickers() if t["exchange"] == "NSE"]
        nse_equities.extend(fallback_nse)

    combined = nse_equities + bse_equities

    if not combined:
        logger.warning("Both exchange endpoints failed. Generating fallback institutional list.")
        combined = get_fallback_tickers()

    # Deduplicate by symbol
    seen_symbols = set()
    deduped = []
    for item in combined:
        sym = item["symbol"].upper()
        if sym not in seen_symbols:
            seen_symbols.add(sym)
            deduped.append(item)

    # Sort: NSE entries first, then BSE, alphabetically by name
    deduped.sort(key=lambda x: (0 if x["exchange"] == "NSE" else 1, x["name"].lower()))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    logger.info(
        f"Master tickers file successfully created at {OUTPUT_FILE}: "
        f"{len(deduped)} total companies ({size_kb:.1f} KB)."
    )
    print(f"Total equities: {len(deduped)} (NSE: {len(nse_equities)}, BSE: {len(bse_equities)})")
    print(f"Output saved to: {OUTPUT_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
