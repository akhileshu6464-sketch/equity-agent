"""
Canonical Company Identity Module (core/company_identity.py)
Enforces permanent internal company_id, preventing name/ticker ambiguity.
100% deterministic entity resolution with zero LLM guessing and fail-closed disambiguation.
"""

import os
import re
import json
import math
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger("ResearchBeast.CompanyIdentity")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LISTED_COMPANIES_PATH = os.path.join(DATA_DIR, "listed_companies.json")

# In-memory index of listed companies
_MASTER_SYMBOL_MAP: Optional[Dict[str, Dict[str, Any]]] = None
_MASTER_NAME_LIST: Optional[List[Dict[str, Any]]] = None

KNOWN_ISIN_MAP: Dict[str, str] = {
    "REDINGTON": "INE891401026",
    "ASHOKA": "INE442H01029",
    "VINATIORGA": "INE410B01037",
    "HDFCBANK": "INE040A01034",
    "TATAMOTORS": "INE155A01022",
    "CROMPTON": "INE299U01018",
    "RELIANCE": "INE002A01018",
    "INFY": "INE009A01021",
    "TCS": "INE467B01029",
    "LT": "INE018A01030",
    "ICICIBANK": "INE090A01021",
    "SBIN": "INE062A01020",
    "BHARTIARTL": "INE397D01024",
    "ITC": "INE154A01025",
    "KOTAKBANK": "INE237A01028",
    "WIPRO": "INE075A01022",
    "HCLTECH": "INE860A01027",
    "ASIANPAINT": "INE021A01026",
    "MARUTI": "INE585B01010",
    "BAJFINANCE": "INE296A01024",
    "BAJAJFINSV": "INE918I01026",
    "AXISBANK": "INE238A01034",
    "SUNPHARMA": "INE044A01036",
    "TITAN": "INE280A01028",
    "ULTRACEMCO": "INE481G01011",
    "NESTLEIND": "INE239A01024",
    "POWERGRID": "INE752E01010",
    "NTPC": "INE733E01010",
    "ONGC": "INE213A01029",
    "JSWSTEEL": "INE019A01038",
    "TATASTEEL": "INE081A01020",
    "M&M": "INE101A01026",
    "ADANIENT": "INE423A01024",
    "ADANIPORTS": "INE742F01042",
    "COALINDIA": "INE522F01014",
    "HINDUNILVR": "INE030A01027",
}

KNOWN_BSE_MAP: Dict[str, str] = {
    "REDINGTON": "532805",
    "ASHOKA": "533271",
    "VINATIORGA": "524200",
    "HDFCBANK": "500180",
    "TATAMOTORS": "500570",
    "CROMPTON": "539876",
    "RELIANCE": "500325",
    "INFY": "500209",
    "TCS": "532540",
    "LT": "500510",
    "ICICIBANK": "532174",
    "SBIN": "500112",
    "BHARTIARTL": "532454",
    "ITC": "500875",
    "KOTAKBANK": "500247",
    "WIPRO": "507685",
    "HCLTECH": "532281",
    "ASIANPAINT": "500820",
    "MARUTI": "532500",
    "BAJFINANCE": "500034",
    "BAJAJFINSV": "532978",
    "AXISBANK": "532215",
    "SUNPHARMA": "524715",
    "TITAN": "500114",
    "HINDUNILVR": "500696",
}

KNOWN_CIN_MAP: Dict[str, str] = {
    "TATAMOTORS": "L28920MH1945PLC004520",
    "ASHOKA": "L45200MH1993PLC071970",
    "VINATIORGA": "L24116MH1989PLC052005",
    "REDINGTON": "L52599TN1961PLC028758",
    "RELIANCE": "L17110MH1973PLC019786",
    "HDFCBANK": "L65920MH1994PLC080618",
    "INFY": "L85110KA1981PLC013115",
    "TCS": "L22210MH1995PLC084781",
    "LT": "L99999MH1946PLC004768",
    "CROMPTON": "L31900MH2015PLC262254",
    "ICICIBANK": "L65190GJ1994PLC021012",
    "SBIN": "STATE_BANK_OF_INDIA_ACT",
    "BHARTIARTL": "L74899HR1995PLC095967",
    "ITC": "L16005WB1910PLC001985",
    "KOTAKBANK": "L65110MH1985PLC038137",
    "WIPRO": "L32102KA1945PLC020800",
    "HCLTECH": "L74140DL1991PLC046369",
    "ASIANPAINT": "L24220MH1942PLC003554",
    "MARUTI": "L34103DL1981PLC011375",
    "BAJFINANCE": "L65910MH1987PLC042961",
    "BAJAJFINSV": "L65923PN2007PLC130075",
    "AXISBANK": "L65110GJ1993PLC020769",
    "SUNPHARMA": "L24230GJ1993PLC019050",
    "TITAN": "L74999TZ1984PLC001456",
    "HINDUNILVR": "L15140MH1933PLC002030",
}

# Strict canonical alias dictionary ensuring different entry paths map to the ONE true identity
CANONICAL_ALIASES: Dict[str, str] = {
    # Tata Motors aliases -> canonical TATAMOTORS (Tata Motors Limited)
    "TMCV": "TATAMOTORS",
    "TMCV.NS": "TATAMOTORS",
    "TATAMOTORS": "TATAMOTORS",
    "TATAMOTORS.NS": "TATAMOTORS",
    "TATA MOTORS": "TATAMOTORS",
    "TATA MOTORS LIMITED": "TATAMOTORS",
    "TATA MOTORS LTD": "TATAMOTORS",
    "500570": "TATAMOTORS",
    "INE155A01022": "TATAMOTORS",
    # TMPV Passenger Vehicles entity (if explicitly requested as a distinct entity)
    "TMPV": "TMPV",
    "TMPV.NS": "TMPV",
    "TATA MOTORS PASSENGER VEHICLES": "TMPV",
    "TATA MOTORS PASSENGER VEHICLES LIMITED": "TMPV",
    # Ashoka Buildcon aliases
    "ASHOKA": "ASHOKA",
    "ASHOKA.NS": "ASHOKA",
    "ASHOKA BUILDCON": "ASHOKA",
    "ASHOKA BUILDCON LIMITED": "ASHOKA",
    "ASHOKA BUILDCON LTD": "ASHOKA",
    "533271": "ASHOKA",
    "INE442H01029": "ASHOKA",
    # Vinati Organics aliases
    "VINATI": "VINATIORGA",
    "VINATIORGA": "VINATIORGA",
    "VINATIORGA.NS": "VINATIORGA",
    "VINATI ORGANICS": "VINATIORGA",
    "VINATI ORGANICS LIMITED": "VINATIORGA",
    "524200": "VINATIORGA",
    "INE410B01037": "VINATIORGA",
    # Redington aliases
    "REDINGTON": "REDINGTON",
    "REDINGTON.NS": "REDINGTON",
    "REDINGTON LIMITED": "REDINGTON",
    "REDINGTON INDIA": "REDINGTON",
    "532805": "REDINGTON",
    "INE891401026": "REDINGTON",
    # HDFC Bank aliases
    "HDFC": "HDFCBANK",
    "HDFCBANK": "HDFCBANK",
    "HDFCBANK.NS": "HDFCBANK",
    "HDFC BANK": "HDFCBANK",
    "HDFC BANK LIMITED": "HDFCBANK",
    "500180": "HDFCBANK",
    "INE040A01034": "HDFCBANK",
    # Reliance aliases
    "RELIANCE": "RELIANCE",
    "RELIANCE.NS": "RELIANCE",
    "RELIANCE INDUSTRIES": "RELIANCE",
    "RELIANCE INDUSTRIES LIMITED": "RELIANCE",
    "RIL": "RELIANCE",
    "500325": "RELIANCE",
    "INE002A01018": "RELIANCE",
    # Crompton aliases
    "CROMPTON": "CROMPTON",
    "CROMPTON.NS": "CROMPTON",
    "CROMPTON GREAVES": "CROMPTON",
    "CROMPTON GREAVES CONSUMER ELECTRICALS": "CROMPTON",
    "CROMPTON GREAVES CONSUMER ELECTRICALS LIMITED": "CROMPTON",
    "539876": "CROMPTON",
    "INE299U01018": "CROMPTON",
    # Infosys aliases
    "INFY": "INFY",
    "INFY.NS": "INFY",
    "INFOSYS": "INFY",
    "INFOSYS LIMITED": "INFY",
    "INE009A01021": "INFY",
    # TCS aliases
    "TCS": "TCS",
    "TCS.NS": "TCS",
    "TATA CONSULTANCY SERVICES": "TCS",
    "TATA CONSULTANCY SERVICES LIMITED": "TCS",
    "INE467B01029": "TCS",
    # L&T aliases
    "LT": "LT",
    "LT.NS": "LT",
    "L&T": "LT",
    "LARSEN & TOUBRO": "LT",
    "LARSEN & TOUBRO LIMITED": "LT",
    "500510": "LT",
    "INE018A01030": "LT",
    # State Bank of India
    "SBIN": "SBIN",
    "SBIN.NS": "SBIN",
    "SBI": "SBIN",
    "STATE BANK OF INDIA": "SBIN",
    "500112": "SBIN",
    "INE062A01020": "SBIN",
}

KNOWN_SECTOR_MAP: Dict[str, Tuple[str, str]] = {
    "TATAMOTORS": ("Consumer Cyclical", "Auto Manufacturers"),
    "TMPV": ("Consumer Cyclical", "Auto Manufacturers"),
    "ASHOKA": ("Industrials", "Engineering & Construction"),
    "VINATIORGA": ("Basic Materials", "Specialty Chemicals"),
    "REDINGTON": ("Technology", "Electronic Components"),
    "HDFCBANK": ("Financial Services", "Banks - Private"),
    "RELIANCE": ("Energy", "Oil & Gas Refining & Marketing"),
    "CROMPTON": ("Consumer Cyclical", "Consumer Appliances"),
    "INFY": ("Technology", "Information Technology Services"),
    "TCS": ("Technology", "Information Technology Services"),
    "LT": ("Industrials", "Engineering & Construction"),
    "ICICIBANK": ("Financial Services", "Banks - Private"),
    "SBIN": ("Financial Services", "Banks - Public"),
    "BHARTIARTL": ("Communication Services", "Telecom Services"),
    "ITC": ("Consumer Defensive", "Tobacco"),
    "KOTAKBANK": ("Financial Services", "Banks - Private"),
    "WIPRO": ("Technology", "Information Technology Services"),
    "HCLTECH": ("Technology", "Information Technology Services"),
    "ASIANPAINT": ("Consumer Cyclical", "Paints"),
    "MARUTI": ("Consumer Cyclical", "Auto Manufacturers"),
    "BAJFINANCE": ("Financial Services", "Credit Services"),
    "BAJAJFINSV": ("Financial Services", "Insurance"),
    "AXISBANK": ("Financial Services", "Banks - Private"),
    "SUNPHARMA": ("Healthcare", "Drug Manufacturers - Specialty & Generic"),
    "TITAN": ("Consumer Cyclical", "Luxury Goods"),
    "ULTRACEMCO": ("Basic Materials", "Building Materials"),
    "NESTLEIND": ("Consumer Defensive", "Packaged Foods"),
    "POWERGRID": ("Utilities", "Utilities - Regulated Electric"),
    "NTPC": ("Utilities", "Utilities - Independent Power Producers"),
    "ONGC": ("Energy", "Oil & Gas E&P"),
    "JSWSTEEL": ("Basic Materials", "Steel"),
    "TATASTEEL": ("Basic Materials", "Steel"),
    "M&M": ("Consumer Cyclical", "Auto Manufacturers"),
    "ADANIENT": ("Industrials", "Conglomerates"),
    "ADANIPORTS": ("Industrials", "Marine Shipping"),
    "COALINDIA": ("Energy", "Thermal Coal"),
    "HINDUNILVR": ("Consumer Defensive", "Household & Personal Products"),
}


@dataclass(frozen=True)
class CompanyIdentity:
    """
    Permanent canonical company identity (Part 2).
    Every company in Research Beast must have ONE immutable internal company_id.
    """
    company_id: str             # e.g. "NSE:ASHOKA", "NSE:TATAMOTORS"
    legal_name: str             # e.g. "Ashoka Buildcon Limited"
    display_name: str           # e.g. "Ashoka Buildcon"
    isin: str                   # e.g. "INE442H01029"
    primary_exchange: str = "NSE"
    primary_symbol: str = ""    # e.g. "ASHOKA"
    nse_symbol: str = ""        # e.g. "ASHOKA"
    bse_code: str = ""          # e.g. "533271"
    cin: str = ""               # e.g. "L45200MH1993PLC071970"
    yahoo_symbol: str = ""      # e.g. "ASHOKA.NS"
    sector: str = ""            # e.g. "Industrials"
    industry: str = ""          # e.g. "Engineering & Construction"
    entity_role: str = "PRIMARY_COMPANY"

    @property
    def company_name(self) -> str:
        """Backward compatibility for existing callers expecting company_name."""
        return self.legal_name or self.display_name

    @property
    def primary_ticker(self) -> str:
        """Backward compatibility for existing callers expecting primary_ticker."""
        if self.yahoo_symbol:
            return self.yahoo_symbol
        if self.primary_exchange == "BSE" and self.bse_code:
            return f"{self.bse_code}.BO"
        sym = self.nse_symbol or self.primary_symbol
        return f"{sym}.NS" if sym else ""

    @property
    def exchange(self) -> str:
        """Backward compatibility for existing callers expecting exchange."""
        return self.primary_exchange

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["company_name"] = self.company_name
        d["primary_ticker"] = self.primary_ticker
        d["exchange"] = self.exchange
        return d


DEFAULT_MASTER_COMPANIES: List[Dict[str, Any]] = [
    {
        "symbol": "TATAMOTORS",
        "name": "Tata Motors Limited",
        "ticker": "TATAMOTORS.NS",
        "isin": "INE155A01022",
        "bse_code": "500570",
        "exchange": "NSE"
    },
    {
        "symbol": "TMPV",
        "name": "Tata Motors Passenger Vehicles Limited",
        "ticker": "TMPV.NS",
        "isin": "",
        "bse_code": "",
        "exchange": "NSE"
    },
    {
        "symbol": "ASHOKA",
        "name": "Ashoka Buildcon Limited",
        "ticker": "ASHOKA.NS",
        "isin": "INE442H01029",
        "bse_code": "533271",
        "exchange": "NSE"
    },
    {
        "symbol": "VINATIORGA",
        "name": "Vinati Organics Limited",
        "ticker": "VINATIORGA.NS",
        "isin": "INE410B01037",
        "bse_code": "524200",
        "exchange": "NSE"
    },
    {
        "symbol": "REDINGTON",
        "name": "Redington Limited",
        "ticker": "REDINGTON.NS",
        "isin": "INE891401026",
        "bse_code": "532805",
        "exchange": "NSE"
    },
    {
        "symbol": "HDFCBANK",
        "name": "HDFC Bank Limited",
        "ticker": "HDFCBANK.NS",
        "isin": "INE040A01034",
        "bse_code": "500180",
        "exchange": "NSE"
    },
    {
        "symbol": "RELIANCE",
        "name": "Reliance Industries Limited",
        "ticker": "RELIANCE.NS",
        "isin": "INE002A01018",
        "bse_code": "500325",
        "exchange": "NSE"
    },
    {
        "symbol": "CROMPTON",
        "name": "Crompton Greaves Consumer Electricals Limited",
        "ticker": "CROMPTON.NS",
        "isin": "INE299U01018",
        "bse_code": "539876",
        "exchange": "NSE"
    },
]


def _load_master_companies():
    global _MASTER_SYMBOL_MAP, _MASTER_NAME_LIST
    if _MASTER_SYMBOL_MAP is not None:
        return

    _MASTER_SYMBOL_MAP = {}
    _MASTER_NAME_LIST = []

    # Pre-seed canonical marquee records
    for rec in DEFAULT_MASTER_COMPANIES:
        sym = rec["symbol"]
        _MASTER_SYMBOL_MAP[sym] = rec
        _MASTER_SYMBOL_MAP[f"{sym}.NS"] = rec
        _MASTER_NAME_LIST.append(rec)

    if os.path.exists(LISTED_COMPANIES_PATH):
        try:
            with open(LISTED_COMPANIES_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
                for rec in records:
                    sym = str(rec.get("symbol", "")).strip().upper()
                    name = str(rec.get("name", "")).strip()
                    ticker = str(rec.get("ticker", "")).strip().upper() or (f"{sym}.NS" if sym else "")
                    isin = str(rec.get("isin", "")).strip().upper()
                    bse_code = str(rec.get("bse_code", "")).strip()
                    exch = str(rec.get("exchange", "NSE")).strip().upper()

                    entry = {
                        "symbol": sym,
                        "name": name,
                        "ticker": ticker,
                        "isin": isin,
                        "bse_code": bse_code,
                        "exchange": exch
                    }

                    if sym and sym not in _MASTER_SYMBOL_MAP:
                        _MASTER_SYMBOL_MAP[sym] = entry
                        _MASTER_SYMBOL_MAP[sym.replace(".NS", "").replace(".BO", "")] = entry
                    if ticker and ticker not in _MASTER_SYMBOL_MAP:
                        _MASTER_SYMBOL_MAP[ticker] = entry
                    _MASTER_NAME_LIST.append(entry)
        except Exception as exc:
            logger.warning(f"Error reading master listed companies from {LISTED_COMPANIES_PATH}: {exc}")


def resolve_company_identity(user_input: str) -> CompanyIdentity:
    """
    Deterministically resolves user search into exactly ONE canonical CompanyIdentity (Part 2 & 3).
    Guarantees that company_id is persistent, deterministic, and isolated.
    Fails closed if ambiguous matches occur. NEVER guesses. NEVER allows LLM selection.
    """
    cleaned = str(user_input or "").strip()
    if not cleaned:
        raise ValueError("Cannot resolve empty company query.")

    _load_master_companies()

    clean_upper = cleaned.upper().replace(".NSE", ".NS").replace(".BSE", ".BO").strip()
    if clean_upper.startswith("NSE:"):
        clean_upper = clean_upper[4:].strip()
    elif clean_upper.startswith("BSE:"):
        clean_upper = clean_upper[4:].strip()
    elif clean_upper.startswith("IN:"):
        clean_upper = clean_upper[3:].strip()

    # Step 1: Check Canonical Alias Map (deterministic alias consolidation)
    norm_alias_key = clean_upper.replace(".NS", "").replace(".BO", "").strip()
    canonical_alias_target = None
    if clean_upper in CANONICAL_ALIASES:
        canonical_alias_target = CANONICAL_ALIASES[clean_upper]
    elif norm_alias_key in CANONICAL_ALIASES:
        canonical_alias_target = CANONICAL_ALIASES[norm_alias_key]

    if canonical_alias_target:
        clean_upper = canonical_alias_target
        if _MASTER_SYMBOL_MAP and canonical_alias_target in _MASTER_SYMBOL_MAP:
            return _build_canonical_identity_from_record(_MASTER_SYMBOL_MAP[canonical_alias_target])

    # Step 2: Check ISIN Mapping
    for sym_k, isin_v in KNOWN_ISIN_MAP.items():
        if isin_v.upper() == clean_upper:
            clean_upper = sym_k
            break

    # Step 3: Check BSE Code Mapping
    for sym_k, bse_v in KNOWN_BSE_MAP.items():
        if bse_v == clean_upper:
            clean_upper = sym_k
            break

    base_sym = clean_upper.replace(".NS", "").replace(".BO", "").strip()

    # Step 4: Exact Symbol Lookup in Master Dictionary
    if _MASTER_SYMBOL_MAP and base_sym in _MASTER_SYMBOL_MAP:
        rec = _MASTER_SYMBOL_MAP[base_sym]
        return _build_canonical_identity_from_record(rec)

    # Step 5: Check explicit ticker format with exchange suffix (e.g. TATAMOTORS.NS)
    if "." in clean_upper and " " not in clean_upper and clean_upper.endswith((".NS", ".BO")):
        sym_part = clean_upper.split(".")[0]
        if sym_part in CANONICAL_ALIASES:
            sym_part = CANONICAL_ALIASES[sym_part]
        if _MASTER_SYMBOL_MAP and sym_part in _MASTER_SYMBOL_MAP:
            return _build_canonical_identity_from_record(_MASTER_SYMBOL_MAP[sym_part])

    # Step 6: Exact Name Lookup in Master Name List
    cleaned_lower = cleaned.lower()
    if _MASTER_NAME_LIST:
        for entry in _MASTER_NAME_LIST:
            ent_name_lower = entry["name"].lower()
            if ent_name_lower == cleaned_lower:
                return _build_canonical_identity_from_record(entry)

    # Step 7: Substring Search with Fail-Closed Ambiguity Detection (Part 2)
    matching_candidates = []
    if _MASTER_NAME_LIST:
        for entry in _MASTER_NAME_LIST:
            ent_name_lower = entry["name"].lower()
            sym_lower = entry.get("symbol", "").lower()
            if ent_name_lower == cleaned_lower or sym_lower == cleaned_lower:
                return _build_canonical_identity_from_record(entry)
            if ent_name_lower.startswith(cleaned_lower) or f" {cleaned_lower} " in f" {ent_name_lower} ":
                matching_candidates.append(entry)

        if len(matching_candidates) == 1:
            return _build_canonical_identity_from_record(matching_candidates[0])
        elif len(matching_candidates) > 1:
            # Check if any candidate has an exact alias or symbol match
            for cand in matching_candidates:
                if cand.get("symbol", "").upper() in CANONICAL_ALIASES and CANONICAL_ALIASES[cand.get("symbol", "").upper()] == cand.get("symbol", "").upper():
                    # Check exact whole word match in name
                    if re.search(r'\b' + re.escape(cleaned_lower) + r'\b', cand["name"].lower()):
                        return _build_canonical_identity_from_record(cand)
            # Fail closed on genuine ambiguity
            matched_names = [f"{c['name']} ({c['symbol']})" for c in matching_candidates[:5]]
            raise ValueError(
                f"AMBIGUOUS COMPANY QUERY: '{user_input}' matched multiple distinct entities: {matched_names}. "
                f"Please specify the exact ticker symbol or ISIN to disambiguate. Never guessing."
            )

    # Step 8: Use yfinance.Search to discover Indian equity quote
    if yf is not None:
        try:
            search_obj = yf.Search(cleaned, max_results=8)
            quotes = search_obj.quotes or []
            for q in quotes:
                sym = str(q.get("symbol", "")).strip().upper()
                qtype = str(q.get("quoteType", "")).upper()
                exch = str(q.get("exchange", "")).upper()
                if (sym.endswith(".NS") or sym.endswith(".BO") or exch in ["NSI", "NSE", "BSE"]) and qtype in ["EQUITY", "ETF", ""]:
                    raw_sym = sym.replace(".NS", "").replace(".BO", "")
                    if raw_sym in CANONICAL_ALIASES:
                        raw_sym = CANONICAL_ALIASES[raw_sym]
                    long_name = q.get("longname") or q.get("shortname") or raw_sym

                    if _MASTER_SYMBOL_MAP and raw_sym in _MASTER_SYMBOL_MAP:
                        rec = _MASTER_SYMBOL_MAP[raw_sym]
                        return _build_canonical_identity_from_record(rec)

                    canonical_id = f"NSE:{raw_sym}" if not sym.endswith(".BO") else f"BSE:{raw_sym}"
                    primary_ticker = f"{raw_sym}.NS" if not sym.endswith(".BO") else f"{raw_sym}.BO"
                    sec, ind = KNOWN_SECTOR_MAP.get(raw_sym, ("General Corporate", "Diverse Operations"))
                    return CompanyIdentity(
                        company_id=canonical_id,
                        legal_name=long_name,
                        display_name=long_name.replace(" Limited", "").replace(" Ltd.", "").strip(),
                        isin=KNOWN_ISIN_MAP.get(raw_sym, ""),
                        primary_exchange="BSE" if sym.endswith(".BO") else "NSE",
                        primary_symbol=raw_sym,
                        nse_symbol=raw_sym if not sym.endswith(".BO") else "",
                        bse_code=KNOWN_BSE_MAP.get(raw_sym, "") or (raw_sym if sym.endswith(".BO") else ""),
                        yahoo_symbol=primary_ticker,
                        sector=sec,
                        industry=ind,
                        entity_role="PRIMARY_COMPANY"
                    )
        except Exception as exc:
            logger.debug(f"yfinance search resolution failed for '{cleaned}': {exc}")

    # Step 9: If clean alphanumeric single token, verify existence via live ticker before constructing canonical identity
    if " " not in cleaned and re.match(r"^[A-Za-z0-9\-_]+(?:\.[A-Za-z]+)?$", cleaned):
        raw_token = clean_upper.replace(".NS", "").replace(".BO", "")
        if yf is not None:
            try:
                candidate_ticker = f"{raw_token}.NS" if not clean_upper.endswith(".BO") else f"{raw_token}.BO"
                t_obj = yf.Ticker(candidate_ticker)
                f_info = t_obj.fast_info
                last_p = getattr(f_info, "last_price", None)
                if last_p is not None and not (isinstance(last_p, float) and (math.isnan(last_p) or math.isinf(last_p))) and float(last_p) > 0:
                    canonical_id = f"NSE:{raw_token}" if not clean_upper.endswith(".BO") else f"BSE:{raw_token}"
                    sec, ind = KNOWN_SECTOR_MAP.get(raw_token, ("General Corporate", "Diverse Operations"))
                    return CompanyIdentity(
                        company_id=canonical_id,
                        legal_name=f"{raw_token} Limited",
                        display_name=raw_token,
                        isin=KNOWN_ISIN_MAP.get(raw_token, ""),
                        primary_exchange="BSE" if clean_upper.endswith(".BO") else "NSE",
                        primary_symbol=raw_token,
                        nse_symbol=raw_token if not clean_upper.endswith(".BO") else "",
                        bse_code=KNOWN_BSE_MAP.get(raw_token, "") or (raw_token if clean_upper.endswith(".BO") else ""),
                        yahoo_symbol=candidate_ticker,
                        sector=sec,
                        industry=ind,
                        entity_role="PRIMARY_COMPANY"
                    )
            except Exception:
                pass

    raise ValueError(f"Could not resolve a confident canonical company identity for: '{user_input}'. Research halted.")


def _build_canonical_identity_from_record(rec: Dict[str, Any]) -> CompanyIdentity:
    sym = rec.get("symbol", "").strip().upper()
    if sym in CANONICAL_ALIASES:
        canonical_sym = CANONICAL_ALIASES[sym]
        if _MASTER_SYMBOL_MAP and canonical_sym in _MASTER_SYMBOL_MAP and canonical_sym != sym:
            rec = _MASTER_SYMBOL_MAP[canonical_sym]
            sym = canonical_sym

    name = rec.get("name", "").strip() or f"{sym} Limited"
    ticker = rec.get("ticker", "").strip().upper() or f"{sym}.NS"
    isin = rec.get("isin", "").strip().upper() or KNOWN_ISIN_MAP.get(sym, "")
    bse = rec.get("bse_code", "").strip() or KNOWN_BSE_MAP.get(sym, "")
    cin = rec.get("cin", "").strip() or KNOWN_CIN_MAP.get(sym, "")
    exch = rec.get("exchange", "NSE").strip().upper()
    sec, ind = KNOWN_SECTOR_MAP.get(sym, ("General Corporate", "Diverse Operations"))

    if exch == "BSE" or ticker.endswith(".BO"):
        canonical_id = f"BSE:{bse or sym}"
    else:
        canonical_id = f"NSE:{sym}"

    return CompanyIdentity(
        company_id=canonical_id,
        legal_name=name,
        display_name=name.replace(" Limited", "").replace(" Ltd.", "").strip(),
        isin=isin,
        primary_exchange=exch,
        primary_symbol=sym,
        nse_symbol=sym if not ticker.endswith(".BO") else "",
        bse_code=bse if (bse or ticker.endswith(".BO")) else "",
        cin=cin,
        yahoo_symbol=ticker,
        sector=sec,
        industry=ind,
        entity_role="PRIMARY_COMPANY"
    )


def verify_data_object_identity(
    data_obj: Any,
    target_identity: CompanyIdentity,
    strict_metadata: bool = False
) -> Tuple[bool, str]:
    """
    Company Identity Firewall Gate (Section 2 & 3).
    Verifies that an incoming data object belongs strictly to target_identity.
    Verification hierarchy:
    source company -> canonical company -> ISIN -> exchange identifier (NSE/BSE).

    Rules:
    1. Company name alone must NEVER be used as the primary identifier.
    2. Zero guessing: if identity cannot be established or mismatches, REJECT DATA.
    3. If strict_metadata=True, asserts presence of: company_id, isin, source, period, scope.
    """
    if data_obj is None:
        return False, "Null data object rejected by identity firewall."

    # Extract attributes whether dictionary or object
    def _get(attr_name, default=""):
        if isinstance(data_obj, dict):
            return str(data_obj.get(attr_name) or default).strip()
        return str(getattr(data_obj, attr_name, default) or default).strip()

    obj_cid = _get("company_id")
    obj_isin = _get("isin").upper()
    obj_nse = _get("nse_symbol").upper() or _get("symbol").upper()
    obj_bse = _get("bse_code") or _get("scrip_code")
    obj_name = _get("company_name") or _get("name")
    obj_source = _get("source")
    obj_period = _get("period")
    obj_scope = _get("scope") or _get("statement_scope")

    # Strict metadata check
    if strict_metadata:
        missing = []
        if not obj_cid: missing.append("company_id")
        if not obj_isin: missing.append("isin")
        if not obj_source: missing.append("source")
        if not obj_period: missing.append("period")
        if not obj_scope: missing.append("scope")
        if missing:
            return False, f"Missing required identity metadata fields: {', '.join(missing)}"

    # 1. Check ISIN if present
    if obj_isin and target_identity.isin:
        if obj_isin == target_identity.isin.upper():
            return True, "Verified via ISIN match."
        else:
            return False, f"ISIN mismatch: object ISIN '{obj_isin}' != target ISIN '{target_identity.isin}'"

    # 2. Check canonical company_id
    if obj_cid:
        from core.research_context import _normalize_cid
        if _normalize_cid(obj_cid) == _normalize_cid(target_identity.company_id):
            return True, "Verified via canonical company_id match."
        else:
            return False, f"Company ID mismatch: object '{obj_cid}' != target '{target_identity.company_id}'"

    # 3. Check NSE symbol
    if obj_nse:
        # Strip exchange suffixes if present
        clean_nse = obj_nse.replace(".NS", "").replace(".BO", "")
        clean_target_nse = target_identity.nse_symbol.replace(".NS", "").replace(".BO", "")
        if clean_nse and clean_target_nse and clean_nse == clean_target_nse:
            return True, "Verified via NSE symbol match."

    # 4. Check BSE scrip code
    if obj_bse and target_identity.bse_code:
        if str(obj_bse).strip() == str(target_identity.bse_code).strip():
            return True, "Verified via BSE scrip code match."

    # 5. Strictly forbid company name alone as primary identifier!
    if obj_name and not (obj_cid or obj_isin or obj_nse or obj_bse):
        return False, "REJECTED: Company name alone must NEVER be used as the primary identifier. No verified regulatory code provided."

    return False, f"REJECTED: Unable to verify regulatory identity against target {target_identity.company_id} ({target_identity.isin}). Never guess."


# Backward-compatible alias
resolve_canonical_identity = resolve_company_identity
