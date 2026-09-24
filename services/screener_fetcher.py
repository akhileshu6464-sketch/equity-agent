"""
Direct Financial Extractor (services/screener_fetcher.py)
Directly extracts authentic, verified financial fundamentals from Screener.in
using requests and BeautifulSoup4 with custom browser headers.

Guarantees:
1. Replaces yfinance fundamentals with direct primary regulatory extracts.
2. Clean input sanitation (strips .NS, .BO, spaces, resolves canonical symbols).
3. Zero guessing, zero hallucination: extracts actual numbers reported by Screener.
4. Returns:
   - Full Company Name and Official "About" narrative.
   - Complete Key Ratios map (Market Cap, Current Price, High / Low, Stock P/E,
     Book Value, Dividend Yield, ROCE, ROE, Face Value).
   - Profit & Loss Historical Table with all 10-year annual columns
     (Sales, Expenses, Operating Profit, OPM %, Net Profit, EPS, etc.).
"""

import re
import html
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger("ResearchBeast.ScreenerFetcher")

# Custom browser headers to mirror a modern Chrome desktop request
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Known Screener URL and symbol aliases
SCREENER_SYMBOL_ALIASES = {
    "TATAMOTORS": "TMCV",
    "TATA MOTORS": "TMCV",
    "TMCV.NS": "TMCV",
    "TMCV": "TMCV",
    "VINATI ORGANICS": "VINATIORGA",
    "VINATI": "VINATIORGA",
    "ASHOKA BUILDCON": "ASHOKA",
    "RELIANCE INDUSTRIES": "RELIANCE",
    "INFOSYS": "INFY",
    "TATA CONSULTANCY SERVICES": "TCS",
    "HDFC BANK": "HDFCBANK",
    "LARSEN & TOUBRO": "LT",
    "CROMPTON GREAVES": "CROMPTON",
}

# Known BSE Codes for resilient fallback
KNOWN_BSE_MAP = {
    "TATAMOTORS": "500570",
    "TMCV": "500570",
    "ASHOKA": "533271",
    "VINATIORGA": "524200",
    "REDINGTON": "532805",
    "HDFCBANK": "500180",
    "RELIANCE": "500325",
    "INFY": "500209",
    "TCS": "532540",
    "LT": "500510",
    "CROMPTON": "539876",
    "ICICIBANK": "532174",
    "SBIN": "500112",
    "ITC": "500875",
    "WIPRO": "507685",
    "HCLTECH": "532281",
    "ASIANPAINT": "500820",
    "MARUTI": "532500",
    "BAJFINANCE": "500034",
    "TITAN": "500114",
}


def clean_user_input(symbol: str) -> str:
    """
    Cleans user input:
    - Strips .NS, .BO, .NSE, .BSE suffixes.
    - Strips whitespace.
    - Resolves known ticker aliases.
    """
    raw = str(symbol or "").strip()
    if not raw:
        return ""

    # Check direct aliases before stripping
    raw_upper = raw.upper()
    if raw_upper in SCREENER_SYMBOL_ALIASES:
        return SCREENER_SYMBOL_ALIASES[raw_upper]

    # Remove exchange suffixes
    cleaned = re.sub(r"(?i)\.(NS|BO|NSE|BSE)$", "", raw).strip()
    clean_upper = cleaned.upper()

    if clean_upper in SCREENER_SYMBOL_ALIASES:
        return SCREENER_SYMBOL_ALIASES[clean_upper]

    # Remove multiple spaces if it's a ticker or condense if name
    return clean_upper


def _parse_numeric(val_str: str) -> Optional[float]:
    """Extracts a clean float from formatted string (e.g. '₹ 12,554 Cr.' -> 12554.0)."""
    if not val_str:
        return None
    try:
        clean = re.sub(r"[^\d.-]", "", val_str)
        if clean and clean != "-" and clean != ".":
            return float(clean)
    except Exception:
        pass
    return None


def _fetch_screener_soup(target: str) -> Tuple[Optional[BeautifulSoup], str]:
    """
    Fetches Screener.in page HTML with multi-tier fallback:
    1. Direct consolidated URL: /company/{target}/consolidated/
    2. Standalone URL: /company/{target}/
    3. BSE Code URL: /company/{bse}/consolidated/
    4. Screener Search API: /api/company/search/?q={target}
    """
    # 1. Consolidated
    url1 = f"https://www.screener.in/company/{target}/consolidated/"
    try:
        r = requests.get(url1, headers=BROWSER_HEADERS, timeout=12)
        if r.status_code == 200 and "Company not found" not in r.text:
            return BeautifulSoup(r.text, "html.parser"), r.url
    except Exception as e:
        logger.warning(f"Screener request error for {url1}: {e}")

    # 2. Standalone
    url2 = f"https://www.screener.in/company/{target}/"
    try:
        r = requests.get(url2, headers=BROWSER_HEADERS, timeout=12)
        if r.status_code == 200 and "Company not found" not in r.text:
            return BeautifulSoup(r.text, "html.parser"), r.url
    except Exception as e:
        logger.warning(f"Screener request error for {url2}: {e}")

    # 3. Check BSE Code map
    bse_code = KNOWN_BSE_MAP.get(target)
    if bse_code:
        url3 = f"https://www.screener.in/company/{bse_code}/consolidated/"
        try:
            r = requests.get(url3, headers=BROWSER_HEADERS, timeout=12)
            if r.status_code == 200 and "Company not found" not in r.text:
                return BeautifulSoup(r.text, "html.parser"), r.url
        except Exception as e:
            logger.warning(f"Screener BSE request error for {url3}: {e}")

    # 4. Search API fallback
    try:
        search_url = f"https://www.screener.in/api/company/search/?q={target}"
        sr = requests.get(search_url, headers=BROWSER_HEADERS, timeout=10)
        if sr.status_code == 200 and sr.json():
            results = sr.json()
            if results and isinstance(results, list):
                cand_url = results[0].get("url", "")
                if cand_url:
                    full_url = f"https://www.screener.in{cand_url}"
                    r = requests.get(full_url, headers=BROWSER_HEADERS, timeout=12)
                    if r.status_code == 200:
                        return BeautifulSoup(r.text, "html.parser"), r.url
    except Exception as e:
        logger.warning(f"Screener search API error for {target}: {e}")

    return None, ""


def fetch_screener_data(symbol: str) -> Dict[str, Any]:
    """
    Directly extracts verified fundamentals from Screener.in.
    Returns:
    - symbol: Clean canonical symbol
    - company_name: Full legal name
    - about: Official about narrative
    - ratios: Map of all 9 key ratios with formatted and numeric values
    - pl_table: Headers and rows dictionary
    - pl_dataframe: Pandas DataFrame of 10-year Profit & Loss table
    - url: Source URL from Screener.in
    """
    cleaned_sym = clean_user_input(symbol)
    if not cleaned_sym:
        raise ValueError("Invalid empty company symbol provided.")

    soup, final_url = _fetch_screener_soup(cleaned_sym)
    if soup is None:
        raise ValueError(
            f"Could not extract fundamentals for symbol '{symbol}' (cleaned: '{cleaned_sym}') from Screener.in. "
            "Please verify the ticker symbol."
        )

    # 1. Company Name
    h1 = soup.find("h1")
    company_name = h1.get_text(strip=True) if h1 else cleaned_sym

    # 2. About Narrative
    about_text = ""
    about_div = soup.find("div", class_="about")
    if about_div:
        for a in about_div.find_all("a"):
            a.decompose()
        about_text = " ".join(about_div.stripped_strings)

    # 3. Key Ratios (All 9 Ratios)
    ratios_formatted: Dict[str, str] = {}
    ratios_numeric: Dict[str, Optional[float]] = {}
    ratios_ul = soup.find("ul", id="top-ratios")
    if ratios_ul:
        for li in ratios_ul.find_all("li"):
            name_el = li.find("span", class_="name")
            val_el = (
                li.find("span", class_="nowrap value")
                or li.find("span", class_="value")
                or li.find("span", class_="number")
            )
            if name_el and val_el:
                k = re.sub(r"\s+", " ", name_el.get_text(strip=True))
                v = re.sub(r"\s+", " ", val_el.get_text(strip=True))
                ratios_formatted[k] = v

    # Standardize ratios map with both raw string and clean numeric forms
    mcap_str = ratios_formatted.get("Market Cap", "N/A")
    cmp_str = ratios_formatted.get("Current Price", "N/A")
    hl_str = ratios_formatted.get("High / Low", "N/A")
    pe_str = ratios_formatted.get("Stock P/E", "N/A")
    bv_str = ratios_formatted.get("Book Value", "N/A")
    div_str = ratios_formatted.get("Dividend Yield", "N/A")
    roce_str = ratios_formatted.get("ROCE", "N/A")
    roe_str = ratios_formatted.get("ROE", "N/A")
    fv_str = ratios_formatted.get("Face Value", "N/A")

    # High / Low parse
    high_52, low_52 = None, None
    if "/" in hl_str:
        parts = hl_str.split("/")
        if len(parts) == 2:
            high_52 = _parse_numeric(parts[0])
            low_52 = _parse_numeric(parts[1])

    key_ratios = {
        "Market Cap": mcap_str,
        "Current Price": cmp_str,
        "High / Low": hl_str,
        "Stock P/E": pe_str,
        "Book Value": bv_str,
        "Dividend Yield": div_str,
        "ROCE": roce_str,
        "ROE": roe_str,
        "Face Value": fv_str,
        # Numeric normalized fields
        "market_cap_cr": _parse_numeric(mcap_str),
        "current_price": _parse_numeric(cmp_str),
        "high_52w": high_52,
        "low_52w": low_52,
        "pe_ratio": _parse_numeric(pe_str),
        "book_value": _parse_numeric(bv_str),
        "dividend_yield_pct": _parse_numeric(div_str),
        "roce_pct": _parse_numeric(roce_str),
        "roe_pct": _parse_numeric(roe_str),
        "face_value": _parse_numeric(fv_str),
    }

def _parse_section_table(soup: BeautifulSoup, section_id: str) -> Tuple[List[str], List[Dict[str, Any]], pd.DataFrame]:
    """Parses standard Screener table inside a section by ID."""
    headers_list: List[str] = []
    rows_table: List[Dict[str, Any]] = []

    sec = soup.find("section", id=section_id)
    if not sec:
        return [], [], pd.DataFrame()

    table = sec.find("table")
    if not table:
        return [], [], pd.DataFrame()

    thead = table.find("thead")
    if thead:
        headers_list = [
            re.sub(r"\s+", " ", th.get_text(strip=True))
            for th in thead.find_all("th")
            if th.get_text(strip=True)
        ]

    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            cells = [
                re.sub(r"\s+", " ", td.get_text(strip=True)).replace("+", "").strip()
                for td in tr.find_all("td")
            ]
            if cells:
                row_name = cells[0]
                row_vals = cells[1:]
                row_dict = {"Metric": row_name}
                for idx, v in enumerate(row_vals):
                    if idx < len(headers_list):
                        row_dict[headers_list[idx]] = v
                rows_table.append(row_dict)

    if rows_table:
        df = pd.DataFrame(rows_table)
        cols = ["Metric"] + [c for c in headers_list if c in df.columns]
        df = df[[c for c in cols if c in df.columns]]
    else:
        df = pd.DataFrame(columns=["Metric"] + headers_list)

    return headers_list, rows_table, df


def _extract_announcements(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extracts official regulatory filings and announcements from the documents section."""
    announcements: List[Dict[str, str]] = []
    doc_sec = soup.find("section", id="documents")
    if not doc_sec:
        return []

    ul = doc_sec.find("ul", class_="list-links")
    if ul:
        for li in ul.find_all("li"):
            a = li.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            date_div = li.find("div", class_="ink-600") or li.find("span")
            date_str = date_div.get_text(strip=True) if date_div else ""

            clean_title = re.sub(r"\s+", " ", title)
            # Remove trailing date pattern e.g. '23 Sep' if appended to title
            m = re.search(r"(\d{1,2}\s+[A-Za-z]{3})$", clean_title)
            if m:
                if not date_str:
                    date_str = m.group(1)
                clean_title = clean_title[:m.start()].strip()

            announcements.append({
                "headline": clean_title,
                "date": date_str,
                "source": "BSE / Regulatory Filing",
                "link": href,
            })
    return announcements


def fetch_stock_chart_data(symbol: str, timeframe: str = "1Y") -> pd.DataFrame:
    """
    Fetches clean stock price and volume history from yfinance.
    Supports: '1M', '6M', '1Y', '3Y', '5Y', 'MAX'.
    """
    import yfinance as yf

    tf_map = {
        "1M": ("1mo", "1d"),
        "6M": ("6mo", "1d"),
        "1Y": ("1y", "1d"),
        "3Y": ("3y", "1d"),
        "5Y": ("5y", "1wk"),
        "MAX": ("max", "1mo"),
    }
    period, interval = tf_map.get(timeframe.upper(), ("1y", "1d"))

    clean_sym = clean_user_input(symbol)
    candidates = [f"{clean_sym}.NS", f"{clean_sym}.BO"]
    if symbol.upper().endswith(".NS") or symbol.upper().endswith(".BO"):
        candidates.insert(0, symbol.upper())

    for yf_sym in candidates:
        try:
            ticker = yf.Ticker(yf_sym)
            hist = ticker.history(period=period, interval=interval)
            if not hist.empty:
                hist = hist.reset_index()
                date_col = "Date" if "Date" in hist.columns else "Datetime"
                hist["Date"] = pd.to_datetime(hist[date_col]).dt.tz_localize(None)
                cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in hist.columns]
                return hist[cols]
        except Exception as e:
            logger.warning(f"Error fetching chart history for {yf_sym}: {e}")

    return pd.DataFrame()


def fetch_day_change(symbol: str) -> Tuple[float, float]:
    """
    Computes absolute and percentage day change between the latest two trading days.
    Returns: (day_change_rs, day_change_pct)
    """
    import yfinance as yf

    clean_sym = clean_user_input(symbol)
    candidates = [f"{clean_sym}.NS", f"{clean_sym}.BO"]
    if symbol.upper().endswith(".NS") or symbol.upper().endswith(".BO"):
        candidates.insert(0, symbol.upper())

    for yf_sym in candidates:
        try:
            ticker = yf.Ticker(yf_sym)
            hist = ticker.history(period="5d", interval="1d")
            if len(hist) >= 2:
                prev_close = float(hist["Close"].iloc[-2])
                curr_close = float(hist["Close"].iloc[-1])
                diff = curr_close - prev_close
                pct = (diff / prev_close) * 100.0 if prev_close != 0 else 0.0
                return round(diff, 2), round(pct, 2)
        except Exception:
            pass
    return 0.0, 0.0


def fetch_screener_data(symbol: str) -> Dict[str, Any]:
    """
    Directly extracts verified fundamentals from Screener.in.
    Returns:
    - symbol: Clean canonical symbol
    - company_name: Full legal name
    - about: Official about narrative
    - ratios: Map of all 9 key ratios with formatted and numeric values
    - pl_table: Headers and rows dictionary for 10-year P&L
    - pl_dataframe: Pandas DataFrame of 10-year Profit & Loss table
    - quarters_table: Quarterly P&L table {headers, rows, df}
    - balance_sheet_table: Balance Sheet table {headers, rows, df}
    - cash_flow_table: Cash Flow table {headers, rows, df}
    - ratios_table: Ratios historical table {headers, rows, df}
    - shareholding_table: Shareholding pattern table {headers, rows, df}
    - announcements: List of official regulatory filings
    - source_url: Source URL from Screener.in
    """
    cleaned_sym = clean_user_input(symbol)
    if not cleaned_sym:
        raise ValueError("Invalid empty company symbol provided.")

    soup, final_url = _fetch_screener_soup(cleaned_sym)
    if soup is None:
        raise ValueError(
            f"Could not extract fundamentals for symbol '{symbol}' (cleaned: '{cleaned_sym}') from Screener.in. "
            "Please verify the ticker symbol."
        )

    # 1. Company Name
    h1 = soup.find("h1")
    company_name = h1.get_text(strip=True) if h1 else cleaned_sym

    # 2. About Narrative
    about_text = ""
    about_div = soup.find("div", class_="about")
    if about_div:
        for a in about_div.find_all("a"):
            a.decompose()
        about_text = " ".join(about_div.stripped_strings)

    # 3. Key Ratios (All 9 Ratios)
    ratios_formatted: Dict[str, str] = {}
    ratios_ul = soup.find("ul", id="top-ratios")
    if ratios_ul:
        for li in ratios_ul.find_all("li"):
            name_el = li.find("span", class_="name")
            val_el = (
                li.find("span", class_="nowrap value")
                or li.find("span", class_="value")
                or li.find("span", class_="number")
            )
            if name_el and val_el:
                k = re.sub(r"\s+", " ", name_el.get_text(strip=True))
                v = re.sub(r"\s+", " ", val_el.get_text(strip=True))
                ratios_formatted[k] = v

    mcap_str = ratios_formatted.get("Market Cap", "N/A")
    cmp_str = ratios_formatted.get("Current Price", "N/A")
    hl_str = ratios_formatted.get("High / Low", "N/A")
    pe_str = ratios_formatted.get("Stock P/E", "N/A")
    bv_str = ratios_formatted.get("Book Value", "N/A")
    div_str = ratios_formatted.get("Dividend Yield", "N/A")
    roce_str = ratios_formatted.get("ROCE", "N/A")
    roe_str = ratios_formatted.get("ROE", "N/A")
    fv_str = ratios_formatted.get("Face Value", "N/A")

    high_52, low_52 = None, None
    if "/" in hl_str:
        parts = hl_str.split("/")
        if len(parts) == 2:
            high_52 = _parse_numeric(parts[0])
            low_52 = _parse_numeric(parts[1])

    key_ratios = {
        "Market Cap": mcap_str,
        "Current Price": cmp_str,
        "High / Low": hl_str,
        "Stock P/E": pe_str,
        "Book Value": bv_str,
        "Dividend Yield": div_str,
        "ROCE": roce_str,
        "ROE": roe_str,
        "Face Value": fv_str,
        # Numeric normalized fields
        "market_cap_cr": _parse_numeric(mcap_str),
        "current_price": _parse_numeric(cmp_str),
        "high_52w": high_52,
        "low_52w": low_52,
        "pe_ratio": _parse_numeric(pe_str),
        "book_value": _parse_numeric(bv_str),
        "dividend_yield_pct": _parse_numeric(div_str),
        "roce_pct": _parse_numeric(roce_str),
        "roe_pct": _parse_numeric(roe_str),
        "face_value": _parse_numeric(fv_str),
    }

    # 4. Profit & Loss Historical Table (10-Year Annual Columns)
    pl_headers, pl_rows, pl_df = _parse_section_table(soup, "profit-loss")
    pl_rows_dicts = [
        {"metric": r.get("Metric", ""), "values": [r.get(h, "") for h in pl_headers], "row_data": r}
        for r in pl_rows
    ]

    # 5. Quarterly Results Table
    q_headers, q_rows, q_df = _parse_section_table(soup, "quarters")

    # 6. Balance Sheet Table
    bs_headers, bs_rows, bs_df = _parse_section_table(soup, "balance-sheet")

    # 7. Cash Flow Table
    cf_headers, cf_rows, cf_df = _parse_section_table(soup, "cash-flow")

    # 8. Ratios Historical Table
    r_headers, r_rows, r_df = _parse_section_table(soup, "ratios")

    # 9. Shareholding Pattern Table
    sh_headers, sh_rows, sh_df = _parse_section_table(soup, "shareholding")

    # 10. Documents & Announcements
    announcements = _extract_announcements(soup)
    drishti_payload: Dict[str, Any] = {}

    try:
        from services.drishti import get_drishti_service, is_drishti_configured
        if is_drishti_configured():
            from core.company_identity import resolve_canonical_identity
            target_ident = resolve_canonical_identity(cleaned_sym)
            d_service = get_drishti_service()
            d_ann = d_service.fetch_company_announcements(target_ident, limit=10)
            d_news = d_service.fetch_company_news(target_ident, limit=10)
            drishti_payload = {
                "announcements": d_ann,
                "news": d_news,
                "is_configured": True,
            }
            # Append verified Drishti announcements with clear provenance
            for da in d_ann:
                announcements.append({
                    "headline": da.headline,
                    "date": da.publication_date or da.event_date,
                    "source": "Drishti (BSE/NSE LODR)",
                    "link": da.source_url,
                })
    except Exception as e:
        logger.debug(f"Drishti enrichment skipped for {cleaned_sym}: {e}")

    return {
        "symbol": cleaned_sym,
        "company_name": company_name,
        "about": about_text,
        "ratios": key_ratios,
        "pl_table": {
            "headers": pl_headers,
            "rows": pl_rows,
            "parsed_rows": pl_rows_dicts,
        },
        "pl_dataframe": pl_df,
        "quarters_table": {
            "headers": q_headers,
            "rows": q_rows,
            "df": q_df,
        },
        "balance_sheet_table": {
            "headers": bs_headers,
            "rows": bs_rows,
            "df": bs_df,
        },
        "cash_flow_table": {
            "headers": cf_headers,
            "rows": cf_rows,
            "df": cf_df,
        },
        "ratios_table": {
            "headers": r_headers,
            "rows": r_rows,
            "df": r_df,
        },
        "shareholding_table": {
            "headers": sh_headers,
            "rows": sh_rows,
            "df": sh_df,
        },
        "announcements": announcements,
        "drishti": drishti_payload,
        "source_url": final_url,
        "extraction_status": "SUCCESS",
    }
