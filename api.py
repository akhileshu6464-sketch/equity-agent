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

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

# Ensure application root directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from agents.pipeline import run_deep_institutional_pipeline

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

    # Normalize ticker (NSE default)
    clean_ticker = raw_ticker.upper()
    if not (clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO")):
        clean_ticker += ".NS"

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

        if any(k in err_str.lower() for k in ["rate limit", "429", "resourceexhausted", "quota"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI API rate limit temporarily reached. Please wait 30-60 seconds before re-auditing."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit equity {clean_ticker}: {err_str}"
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
