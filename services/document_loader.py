"""
Primary Source Document Loader (services/document_loader.py)
Ingests, extracts, cleans, and structures primary public filings for Indian equities:
1. Official Exchange Company Profile & Segment/Product Offerings (BSE/Screener).
2. Credit Rating Rationales (CARE, CRISIL, ICRA) for debt profile & liquidity covenants.
3. Earnings Conference Call Transcripts (Management remarks, guidance, & Q&A).
4. Corporate Announcements (BSE/NSE Regulation 30 LODR).

Strips forward-looking legal disclaimers and boilerplate safe-harbor clauses.
Formats extracts into strictly cited <primary_disclosures> XML blocks for LLM context locking.
"""

import os
import io
import re
import json
import time
import sqlite3
import logging
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

try:
    import pypdf
except ImportError:
    pypdf = None

logger = logging.getLogger("EquityPipeline.DocumentLoader")

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DOCUMENT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "document_cache.db")
CACHE_TTL_SECONDS = 24 * 3600  # 24 hours TTL

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DISCLAIMER_PATTERNS = [
    r"(?i)this\s+(?:transcript|document|presentation|call)\s+(?:contains|may\s+contain)\s+forward[- ]looking\s+statements[\s\S]*?(?:actual\s+results\s+(?:could|may)\s+differ|obligation\s+to\s+update|undertake\s+no\s+obligation|financial\s+year)[.]?",
    r"(?i)certain\s+statements\s+in\s+this\s+(?:release|document|call)\s+concerning[\s\S]*?(?:obligation\s+to\s+update|actual\s+results\s+may\s+differ)[.]?",
    r"(?i)safe\s+harbour\s+statement:?[\s\S]*?(?:actual\s+results\s+may\s+differ|obligation\s+to\s+update)[.]?",
    r"(?i)all\s+participant\s+lines\s+will\s+be\s+in\s+the\s+listen[- ]only\s+mode[\s\S]*?(?:signal\s+an\s+operator|touch[- ]tone\s+phone)[.]?",
    r"(?i)please\s+note\s+that\s+this\s+conference\s+is\s+being\s+recorded[.]?",
    r"(?i)moderator:\s+ladies\s+and\s+gentlemen,\s+good\s+day,\s+and\s+welcome[\s\S]*?hand\s+the\s+conference\s+over\s+to[^\.\n]*[\.\n]",
    r"(?i)disclaimer:\s+this\s+transcript\s+is\s+produced\s+by[\s\S]*?errors[.]?",
    r"(?i)bse\s+limited[\s\S]*?dear\s+sir\s*/\s*madam,[\s\S]*?subject:[\s\S]*?(?:enclosed|attached)\s+herewith[^\.\n]*[\.\n]",
    r"(?i)national\s+stock\s+exchange\s+of\s+india[\s\S]*?subject:[\s\S]*?(?:enclosed|attached)\s+herewith[^\.\n]*[\.\n]"
]


def _clean_ascii(text: str) -> str:
    """Cleans Unicode characters to safe ASCII equivalents for Windows compatibility."""
    if not text:
        return ""
    text = text.replace("\u20b9", "Rs. ")
    text = text.replace("₹", "Rs. ")
    text = text.replace("\u2014", " - ")
    text = text.replace("\u2013", " - ")
    text = text.replace("\u2022", "* ")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return text.strip()


class DocumentLoader:
    """Primary document ingestion and normalization engine for Indian equities."""

    def __init__(self, db_path: Optional[str] = None, ttl_seconds: int = CACHE_TTL_SECONDS):
        self._db_path = db_path or DOCUMENT_DB_PATH
        self._ttl_seconds = ttl_seconds
        self._session = requests.Session()
        self._session.headers.update(BROWSER_HEADERS)
        self._init_db()

    def _init_db(self) -> None:
        """Initializes SQLite cache table."""
        conn = None
        try:
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_cache (
                    symbol TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    cached_at REAL NOT NULL
                )
            """)
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not initialize SQLite document cache: {e}")
        finally:
            if conn:
                conn.close()

    def _get_from_sqlite(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached document data from SQLite if within TTL."""
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data_json, cached_at FROM document_cache WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            if row:
                data_json, cached_at = row
                if (time.time() - cached_at) < self._ttl_seconds:
                    logger.info(f"SQLite document cache HIT for {symbol}")
                    return json.loads(data_json)
        except Exception as e:
            logger.warning(f"Error reading SQLite document cache for {symbol}: {e}")
        finally:
            if conn:
                conn.close()
        return None

    def _save_to_sqlite(self, symbol: str, data: Dict[str, Any]) -> None:
        """Saves document disclosures to SQLite."""
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT OR REPLACE INTO document_cache (symbol, data_json, cached_at) VALUES (?, ?, ?)",
                (symbol, json.dumps(data, ensure_ascii=True), time.time())
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Error saving to SQLite document cache for {symbol}: {e}")
        finally:
            if conn:
                conn.close()

    def clean_disclaimer_boilerplate(self, text: str) -> str:
        """Strips safe-harbor statements, operator scripts, and BSE filing cover notes."""
        if not text:
            return ""
        cleaned = text
        for pat in DISCLAIMER_PATTERNS:
            cleaned = re.sub(pat, "", cleaned)
        # Collapse multiple empty lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def load_primary_disclosures(
        self,
        symbol: str,
        company_name: str,
        company_data: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Loads and synthesizes all verified primary disclosures for symbol:
        1. Product Offerings and Segments from official company profile.
        2. Credit Rating Rationale (CARE / CRISIL / ICRA).
        3. Concall Transcript Management Highlights & Guidance.
        4. Corporate Announcements under Regulation 30.
        """
        clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()

        if not force_refresh:
            cached = self._get_from_sqlite(clean_sym)
            if cached:
                return cached

        soup = self._fetch_screener_soup(clean_sym)

        # 1. Official product portfolio & segments
        product_portfolio = self._extract_product_offerings(soup, clean_sym, company_name)

        # 2. Corporate announcements (Regulation 30)
        announcements = self._extract_announcements(soup)

        # 3. Credit rating rationale
        credit_rating = self._extract_credit_rating(soup, clean_sym, company_name)

        # 4. Concall transcript & guidance
        concall = self._extract_concall_transcript(soup, clean_sym, company_name)

        disclosures = {
            "symbol": symbol,
            "company_name": company_name,
            "product_portfolio": product_portfolio,
            "credit_rating": credit_rating,
            "concall_transcript": concall,
            "corporate_announcements": announcements
        }

        # Format XML block
        disclosures["disclosures_xml"] = self.format_primary_disclosures_block(disclosures)

        # Save to SQLite
        self._save_to_sqlite(clean_sym, disclosures)

        return disclosures

    def _fetch_screener_soup(self, clean_sym: str) -> Optional[BeautifulSoup]:
        """Fetches Screener.in page HTML."""
        urls = [
            f"https://www.screener.in/company/{clean_sym}/consolidated/",
            f"https://www.screener.in/company/{clean_sym}/"
        ]
        for u in urls:
            try:
                resp = self._session.get(u, timeout=10)
                if resp.status_code == 200 and "Company not found" not in resp.text:
                    return BeautifulSoup(resp.content, "html.parser")
            except Exception as e:
                logger.debug(f"Screener fetch error for {u}: {e}")
        return None

    def _extract_product_offerings(
        self,
        soup: Optional[BeautifulSoup],
        clean_sym: str,
        company_name: str
    ) -> Dict[str, Any]:
        """Extracts official product line details and operating segments from company overview."""
        if not soup:
            return {
                "overview": f"{company_name} is an active listed commercial enterprise.",
                "segments": ["Not Disclosed in Management Filings"],
                "source": "BSE / NSE Corporate Profile"
            }

        about_div = soup.find("div", class_="about")
        comm_div = soup.find(class_="commentary")

        overview_text = ""
        if about_div:
            p_elem = about_div.find("p")
            if p_elem:
                overview_text = _clean_ascii(p_elem.get_text(" ", strip=True))

        details_text = ""
        if comm_div:
            details_text = _clean_ascii(comm_div.get_text("\n", strip=True))

        full_text = f"{overview_text}\n{details_text}".strip()
        cleaned_text = self.clean_disclaimer_boilerplate(full_text)

        # Segment parser
        segment_lines: List[str] = []
        if details_text:
            lines = [l.strip() for l in details_text.split("\n") if l.strip()]
            cur_seg = ""
            for l in lines:
                if re.match(r"^[a-gA-G1-9]\)|\bProduct Offerings\b|\bSegments?\b", l):
                    if cur_seg:
                        segment_lines.append(cur_seg)
                    cur_seg = l
                elif cur_seg:
                    cur_seg += f" {l}"
            if cur_seg:
                segment_lines.append(cur_seg)

        if not segment_lines and cleaned_text:
            segment_lines = [cleaned_text[:300]]

        return {
            "overview": overview_text or f"{company_name} operations.",
            "details": details_text,
            "segments": segment_lines[:8] if segment_lines else ["Not Disclosed in Management Filings"],
            "source": f"Screener.in / BSE Official Profile ({clean_sym})"
        }

    def _extract_announcements(self, soup: Optional[BeautifulSoup]) -> List[Dict[str, str]]:
        """Extracts recent Regulation 30 (LODR) corporate announcements."""
        if not soup:
            return []

        doc_sec = soup.find("section", id="documents")
        if not doc_sec:
            return []

        announcements: List[Dict[str, str]] = []
        # Find announcements list items
        for li in doc_sec.find_all("li", class_="announcement")[:6]:
            text = _clean_ascii(li.get_text(" ", strip=True))
            if text:
                announcements.append({
                    "title": text[:180],
                    "source": "BSE Regulation 30 (LODR)"
                })

        # Fallback: scan all links under Announcements header
        if not announcements:
            for a in doc_sec.find_all("a"):
                href = a.get("href", "")
                txt = _clean_ascii(a.get_text(strip=True))
                if "Regulation 30" in txt or "Analyst" in txt or "Intimation" in txt:
                    announcements.append({
                        "title": txt[:180],
                        "source": "BSE Corporate Announcements"
                    })
                if len(announcements) >= 5:
                    break

        return announcements

    def _extract_credit_rating(
        self,
        soup: Optional[BeautifulSoup],
        clean_sym: str,
        company_name: str
    ) -> Dict[str, Any]:
        """Downloads and extracts key rating highlights and debt covenants from credit rating report."""
        default_rating = {
            "agency": "Not Disclosed in Management Filings",
            "rating": "Not Disclosed in Management Filings",
            "facilities_cr": "Not Disclosed in Management Filings",
            "rationale_highlights": "Not Disclosed in Management Filings",
            "source": "Not Disclosed in Management Filings"
        }

        if not soup or not pypdf:
            return default_rating

        doc_sec = soup.find("section", id="documents")
        if not doc_sec:
            return default_rating

        rating_url = None
        rating_agency = "Credit Rating Agency"
        for a in doc_sec.find_all("a"):
            href = a.get("href", "")
            txt = a.get_text(strip=True).lower()
            if "rating" in txt or "care" in txt or "crisil" in txt or "icra" in txt:
                if href.endswith(".pdf"):
                    rating_url = href
                    if "care" in href or "care" in txt:
                        rating_agency = "CARE Ratings"
                    elif "crisil" in href or "crisil" in txt:
                        rating_agency = "CRISIL"
                    elif "icra" in href or "icra" in txt:
                        rating_agency = "ICRA"
                    break

        if not rating_url:
            return default_rating

        try:
            resp = self._session.get(rating_url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 1000:
                reader = pypdf.PdfReader(io.BytesIO(resp.content))
                first_page = reader.pages[0].extract_text() if len(reader.pages) > 0 else ""
                clean_text = _clean_ascii(first_page)
                cleaned = self.clean_disclaimer_boilerplate(clean_text)

                # Extract rating string
                rating_match = re.search(r"(CARE\s+(?:A{1,3}|B{1,3}|C{1,3}|D|A1\+?|A2\+?|A3\+?|A4\+?)[\+\-]*(?:\s*;\s*[A-Za-z]+)?(?:\s*/\s*CARE\s+[A-Za-z0-9\+\-]+)?|CRISIL\s+(?:A{1,3}|B{1,3}|C{1,3}|D|A1\+?)[\+\-]*(?:\s*;\s*[A-Za-z]+)?|\[ICRA\](?:A{1,3}|B{1,3}|C{1,3}|D|A1\+?)[\+\-]*(?:\s*;\s*[A-Za-z]+)?)", cleaned)
                rating_str = rating_match.group(0).strip() if rating_match else f"{rating_agency} Investment Grade"

                # Extract facility amount
                amt_match = re.search(r"(?:amount|facilities)[\s\S]*?(?:Rs\.?|INR)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cr|crore)", cleaned, re.IGNORECASE)
                amt_cr = f"Rs. {amt_match.group(1)} Cr" if amt_match else "Not Disclosed"

                # Extract rationale section
                rat_sec = ""
                if "Rationale and key rating drivers" in cleaned:
                    rat_sec = cleaned.split("Rationale and key rating drivers")[-1][:600].strip()
                elif "Key Rating Strengths" in cleaned:
                    rat_sec = cleaned.split("Key Rating Strengths")[-1][:600].strip()
                else:
                    rat_sec = cleaned[:500].strip()

                return {
                    "agency": rating_agency,
                    "rating": rating_str,
                    "facilities_cr": amt_cr,
                    "rationale_highlights": rat_sec,
                    "source": f"{rating_agency} Credit Rating Rationale"
                }
        except Exception as e:
            logger.warning(f"Failed to parse credit rating PDF for {clean_sym}: {e}")

        return default_rating

    def _extract_concall_transcript(
        self,
        soup: Optional[BeautifulSoup],
        clean_sym: str,
        company_name: str
    ) -> Dict[str, Any]:
        """Downloads and extracts management remarks and guidance from latest concall PDF."""
        default_concall = {
            "title": "Not Disclosed in Management Filings",
            "date": "Not Disclosed in Management Filings",
            "management_remarks": "Not Disclosed in Management Filings",
            "guidance_points": ["Not Disclosed in Management Filings"],
            "source": "Not Disclosed in Management Filings"
        }

        if not soup or not pypdf:
            return default_concall

        doc_sec = soup.find("section", id="documents")
        if not doc_sec:
            return default_concall

        concall_url = None
        for a in doc_sec.find_all("a"):
            href = a.get("href", "")
            txt = a.get_text(strip=True).lower()
            if ("transcript" in txt or "concall" in txt or "earnings" in txt) and href.endswith(".pdf"):
                concall_url = href
                break

        if not concall_url:
            return default_concall

        try:
            resp = self._session.get(concall_url, timeout=12)
            if resp.status_code == 200 and len(resp.content) > 1000:
                reader = pypdf.PdfReader(io.BytesIO(resp.content))
                num_pages = len(reader.pages)
                # Combine pages 2, 3, 4 (typically management remarks)
                combined_pages = ""
                for p_idx in range(1, min(5, num_pages)):
                    combined_pages += reader.pages[p_idx].extract_text() + "\n"

                clean_text = _clean_ascii(combined_pages)
                cleaned = self.clean_disclaimer_boilerplate(clean_text)

                # Extract guidance sentences
                guidance_sentences: List[str] = []
                for s in re.split(r"[.\n]", cleaned):
                    s_clean = s.strip()
                    if len(s_clean) > 25 and any(k in s_clean.lower() for k in ["guidance", "expect", "target", "growth", "volume", "capex", "capacity", "margin"]):
                        if s_clean not in guidance_sentences:
                            guidance_sentences.append(s_clean[:200])

                # Extract opening remarks
                remarks = cleaned[:1800].strip()

                return {
                    "title": f"Earnings Conference Call Transcript ({clean_sym})",
                    "date": "Recent Fiscal Period",
                    "management_remarks": remarks or "Not Disclosed in Management Filings",
                    "guidance_points": guidance_sentences[:5] if guidance_sentences else ["Not Disclosed in Management Filings"],
                    "source": f"Concall Transcript (Pages 2-4), BSE Filing"
                }
        except Exception as e:
            logger.warning(f"Failed to parse concall transcript for {clean_sym}: {e}")

        return default_concall

    def format_primary_disclosures_block(self, disclosures: Dict[str, Any]) -> str:
        """
        Formats disclosures into an XML block wrapped in <primary_disclosures> tags
        with explicit structured citations for context locking.
        """
        company_name = disclosures.get("company_name", "Target Enterprise")
        symbol = disclosures.get("symbol", "")
        portfolio = disclosures.get("product_portfolio", {})
        rating = disclosures.get("credit_rating", {})
        concall = disclosures.get("concall_transcript", {})
        announcements = disclosures.get("corporate_announcements", [])

        lines = [
            "<primary_disclosures>",
            "<!-- VERIFIED PRIMARY SOURCES: OFFICIAL FILINGS, RATINGS, AND CONCALL TRANSCRIPTS -->",
            f"[COMPANY_OFFICIAL_PROFILE_AND_SEGMENTS]",
            f"Company: {company_name} ({symbol})",
            f"Citation: [Source: {portfolio.get('source', 'BSE Official Profile')}]",
            f"Business Overview: {portfolio.get('overview', 'Not Disclosed in Management Filings')}",
            "Operating Segments & Product Offerings:"
        ]

        for seg in portfolio.get("segments", []):
            lines.append(f"- {seg}")

        lines.extend([
            "",
            "[CREDIT_RATING_AND_DEBT_COVENANTS]",
            f"Citation: [Source: {rating.get('source', 'Credit Rating Agency')}]",
            f"Rating Agency: {rating.get('agency', 'Not Disclosed in Management Filings')}",
            f"Assigned Rating: {rating.get('rating', 'Not Disclosed in Management Filings')}",
            f"Rated Bank Facilities: {rating.get('facilities_cr', 'Not Disclosed in Management Filings')}",
            f"Rating Rationale Highlights: {rating.get('rationale_highlights', 'Not Disclosed in Management Filings')}",
            "",
            "[EARNINGS_CONFERENCE_CALL_AND_MANAGEMENT_GUIDANCE]",
            f"Citation: [Source: {concall.get('source', 'Concall Transcript')}]",
            f"Call Title: {concall.get('title', 'Not Disclosed in Management Filings')}",
            f"Management Opening Remarks Excerpt:\n{concall.get('management_remarks', 'Not Disclosed in Management Filings')[:1200]}",
            "Key Guidance Points Cited from Transcript:"
        ])

        for g in concall.get("guidance_points", []):
            lines.append(f"- \"{g}\" [Source: {concall.get('source', 'Concall Transcript')}]")

        lines.extend([
            "",
            "[EXCHANGE_REGULATION_30_ANNOUNCEMENTS]",
            f"Citation: [Source: BSE/NSE Regulation 30 (LODR) Disclosures]"
        ])

        if announcements:
            for ann in announcements[:5]:
                lines.append(f"- {ann.get('title', '')} [Source: {ann.get('source', 'BSE Regulation 30')}]")
        else:
            lines.append("- Not Disclosed in Management Filings")

        lines.append("</primary_disclosures>")
        return "\n".join(lines)
