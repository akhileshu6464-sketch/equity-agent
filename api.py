"""
Research Beast - Production FastAPI Backend
Decoupled API serving 7-agent autonomous institutional equity research audits.
Mounts and serves the single-page dark UI frontend at `/`.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

# Ensure application root directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import json
from agents.pipeline import run_deep_institutional_pipeline
from services.financial_data import FinancialDataService
from pdf_generator import build_institutional_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ResearchBeast.API")

# Initialize FastAPI Application
app = FastAPI(
    title="Research Beast Institutional Equity Engine API",
    description="Production FastAPI backend serving 7-agent autonomous institutional equity research audits.",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://researchbeast.in"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., description="NSE/BSE ticker symbol (e.g. CROMPTON, RELIANCE, HDFCBANK)")
    wacc: Optional[float] = Field(0.115, description="Weighted Average Cost of Capital hurdle")
    terminal_growth: Optional[float] = Field(0.055, description="Terminal growth rate assumption")
    base_growth: Optional[float] = Field(0.12, description="Base revenue growth assumption")


class ExportPDFRequest(BaseModel):
    ticker: str = Field(..., description="NSE/BSE ticker symbol (e.g. CROMPTON, RELIANCE, TATACONSUM.NS)")
    dossier: Optional[Dict[str, Any]] = Field(None, description="Optional completed audit dossier payload")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


# -------------------------------------------------------------------------
# Defensive Serialization Helpers
# -------------------------------------------------------------------------

def _sanitize_for_json(obj: Any) -> Any:
    """Recursively converts NumPy, Pandas, MarkdownDict, or complex types to native JSON-serializable primitives."""
    if obj is None:
        return None
    if isinstance(obj, (int, str, bool)):
        return obj
    if isinstance(obj, float):
        if obj != obj or obj == float('inf') or obj == float('-inf'):  # NaN or Inf check
            return 0.0
        return obj
    if hasattr(obj, "item"):  # NumPy scalar
        return obj.item()
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(x) for x in obj]
    if hasattr(obj, "to_dict"):
        try:
            return _sanitize_for_json(obj.to_dict())
        except Exception:
            return str(obj)
    return str(obj)


# -------------------------------------------------------------------------
# Exchange Tickers In-Memory Cache & Search
# -------------------------------------------------------------------------

_CACHED_TICKERS: Optional[List[Dict[str, str]]] = None


def _get_cached_tickers() -> List[Dict[str, str]]:
    """Loads and caches the master list of NSE/BSE listed companies in memory."""
    global _CACHED_TICKERS
    if _CACHED_TICKERS is None:
        json_path = os.path.join(CURRENT_DIR, "data", "listed_companies.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    _CACHED_TICKERS = json.load(f)
                logger.info(f"Loaded {len(_CACHED_TICKERS)} tickers into memory cache.")
            except Exception as e:
                logger.error(f"Error reading {json_path}: {e}")
        if not _CACHED_TICKERS:
            _CACHED_TICKERS = [
                {"symbol": "CROMPTON", "name": "Crompton Greaves Consumer Electricals Limited", "ticker": "CROMPTON.NS", "exchange": "NSE"},
                {"symbol": "RELIANCE", "name": "Reliance Industries Limited", "ticker": "RELIANCE.NS", "exchange": "NSE"},
                {"symbol": "HDFCBANK", "name": "HDFC Bank Limited", "ticker": "HDFCBANK.NS", "exchange": "NSE"},
                {"symbol": "TCS", "name": "Tata Consultancy Services Limited", "ticker": "TCS.NS", "exchange": "NSE"},
                {"symbol": "INFY", "name": "Infosys Limited", "ticker": "INFY.NS", "exchange": "NSE"},
                {"symbol": "TATACONSUM", "name": "Tata Consumer Products Limited", "ticker": "TATACONSUM.NS", "exchange": "NSE"},
                {"symbol": "ICICIBANK", "name": "ICICI Bank Limited", "ticker": "ICICIBANK.NS", "exchange": "NSE"},
                {"symbol": "ANDHRAPET", "name": "Andhra Petrochemicals Limited", "ticker": "500012.BO", "exchange": "BSE"},
                {"symbol": "AMBALALSA", "name": "Ambalal Sarabhai Enterprises Ltd", "ticker": "500009.BO", "exchange": "BSE"},
            ]
    return _CACHED_TICKERS


# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container uptime and proxy probes."""
    return {
        "status": "ok",
        "service": "Research Beast API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/tickers")
async def get_tickers(q: Optional[str] = "", limit: int = 15):
    """
    Search endpoint for NSE & BSE listed equity tickers.
    Supports instant prefix, substring, and company name matching without duplicate exchange listings.
    """
    query = (q or "").strip().lower()
    tickers = _get_cached_tickers()
    if len(query) < 2:
        return []

    exact_sym = []
    prefix_sym = []
    exact_word_in_name = []
    prefix_name = []
    sub_match = []

    for c in tickers:
        sym = c.get("symbol", "").lower()
        name = c.get("name", "").lower()

        clean_sym = sym.replace(".ns", "").replace(".bo", "")
        words = name.split()

        if clean_sym == query:
            exact_sym.append(c)
        elif clean_sym.startswith(query):
            prefix_sym.append(c)
        elif any(w == query for w in words):
            exact_word_in_name.append(c)
        elif any(w.startswith(query) for w in words):
            prefix_name.append(c)
        elif query in sym or query in name:
            sub_match.append(c)

        if len(exact_sym) + len(prefix_sym) + len(exact_word_in_name) + len(prefix_name) >= limit * 2:
            break

    results = (exact_sym + prefix_sym + exact_word_in_name + prefix_name + sub_match)[:limit]
    return results


@app.post("/api/analyze")
async def analyze_equity(request: AnalyzeRequest):
    """
    Executes the comprehensive 7-agent institutional equity research pipeline.
    Returns complete structured equity chapters, 4-pillar moat deconstructions,
    forensics, governance, valuation hurdle rates, and Stage 1 calculated metrics.
    """
    raw_ticker = request.ticker.strip()
    if not raw_ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock ticker symbol cannot be empty."
        )

    # Normalize ticker using institutional standard normalizer (handles NSE, BSE, scrip codes)
    clean_ticker = FinancialDataService.normalize_ticker(raw_ticker)

    logger.info(f"Incoming audit request for ticker: '{raw_ticker}' -> resolved as '{clean_ticker}'")

    try:
        # Run blocking mathematical and scraping pipeline asynchronously in worker threadpool
        dossier = await run_in_threadpool(
            run_deep_institutional_pipeline,
            ticker=clean_ticker,
            wacc=request.wacc or 0.115,
            terminal_growth=request.terminal_growth or 0.055,
            base_growth=request.base_growth or 0.12,
            force_refresh=True
        )

        if not dossier or not isinstance(dossier, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"The institutional pipeline returned an invalid payload for {clean_ticker}."
            )

        # Sanitize entire dossier structure for clean JSON serialization
        clean_payload = _sanitize_for_json(dossier)
        return JSONResponse(content=clean_payload)

    except HTTPException:
        raise
    except Exception as exc:
        err_str = str(exc)
        logger.error(f"Error executing institutional pipeline for {clean_ticker}: {err_str}", exc_info=True)

        if "real-time fundamental data unavailable" in err_str.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Real-time fundamental data unavailable for {clean_ticker}"
            )

        if any(k in err_str.lower() for k in ["rate limit", "429", "resourceexhausted", "quota"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI API rate limit temporarily reached. Please wait 30-60 seconds before re-auditing."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit equity {clean_ticker}: {err_str}"
        )


@app.post("/api/export-pdf")
async def export_pdf(request: ExportPDFRequest):
    """
    Compiles and downloads a publication-grade institutional equity research PDF report.
    If a completed dossier dictionary is passed from the client, compiles immediately;
    otherwise retrieves/audits the equity autonomously.
    """
    raw_ticker = request.ticker.strip()
    if not raw_ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock ticker symbol cannot be empty."
        )

    clean_ticker = FinancialDataService.normalize_ticker(raw_ticker)
    dossier = request.dossier

    try:
        # If dossier is not provided or incomplete, run pipeline to generate it
        if not dossier or not isinstance(dossier, dict) or not dossier.get("moat"):
            logger.info(f"Generating fresh dossier for PDF export of {clean_ticker}...")
            dossier = await run_in_threadpool(
                run_deep_institutional_pipeline,
                ticker=clean_ticker,
                force_refresh=False
            )

        if not dossier:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to construct equity dossier for {clean_ticker}."
            )

        company_name = (
            dossier.get("company_name")
            or dossier.get("short_name")
            or dossier.get("long_name")
            or clean_ticker
        )

        pdf_metrics = {
            "current_price": dossier.get("current_price", 0.0),
            "market_cap_cr": dossier.get("market_cap_cr", 0.0),
            "sector": dossier.get("sector", "N/A"),
            "industry": dossier.get("industry", "N/A"),
            "pe_ratio": dossier.get("trailing_pe", 0.0),
            "pb_ratio": dossier.get("price_to_book", 0.0),
            "ev_to_ebitda": dossier.get("ev_to_ebitda", 0.0),
            "fifty_two_week_high": dossier.get("fifty_two_week_high", 0.0),
            "fifty_two_week_low": dossier.get("fifty_two_week_low", 0.0),
        }

        # Compile presentation-grade institutional PDF
        pdf_bytes = await run_in_threadpool(
            build_institutional_pdf,
            ticker=clean_ticker,
            company_name=company_name,
            metrics=pdf_metrics,
            dossier_dict=dossier
        )

        safe_comp_name = "".join(c for c in company_name if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_filename = f"{safe_comp_name or clean_ticker} - Institutional Equity Research Report.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        err_str = str(exc)
        logger.error(f"Error compiling institutional PDF for {clean_ticker}: {err_str}", exc_info=True)
        if "real-time fundamental data unavailable" in err_str.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Real-time fundamental data unavailable for {clean_ticker}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate institutional PDF report: {err_str}"
        )


# -------------------------------------------------------------------------
# Static Frontend Mount & Root Route
# -------------------------------------------------------------------------

STATIC_DIR = os.path.join(CURRENT_DIR, "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the single-page dark UI frontend application."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {
        "message": "Research Beast API running.",
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
