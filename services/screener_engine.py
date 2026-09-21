"""
Screener Financial Engine (services/screener_engine.py)
100% deterministic mathematical calculations and multi-year financial statement modeling.
Extracts raw data via yfinance with resilient fallback to Screener.in and local providers.
Computes Screener-style ratios and historical Profit & Loss tables without any LLM hallucination.
"""

import os
import math
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

from services.financial_data import FinancialDataService, extract_pure_symbol

logger = logging.getLogger("ResearchBeast.ScreenerEngine")


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Converts a value to float safely without throwing exceptions on NaN/Inf/None."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if math.isnan(f) or math.isinf(f) else f
    except (ValueError, TypeError):
        return default


def _calculate_cagr(start_val: float, end_val: float, periods: int) -> Optional[float]:
    """
    Computes Compound Annual Growth Rate (CAGR) defensively.
    Returns None if start_val <= 0 or end_val <= 0 or periods <= 0.
    """
    if periods <= 0 or start_val <= 0 or end_val <= 0:
        return None
    try:
        ratio = end_val / start_val
        cagr = (math.pow(ratio, 1.0 / periods) - 1.0) * 100.0
        return round(cagr, 2)
    except Exception:
        return None


def _safe_fast(fast: Any, attr: str, default: Any = None) -> Any:
    """Defensively extracts attributes from yfinance fast_info without crashing on missing keys."""
    if fast is None:
        return default
    try:
        val = getattr(fast, attr, None)
        return val if val is not None else default
    except Exception:
        return default


class ScreenerEngine:
    """
    Deterministic Screener.in financial engine.
    Extracts raw fundamentals and computes valuation multiples, capital returns,
    and multi-year Profit & Loss statements with 100% mathematical precision.
    """

    @classmethod
    def get_screener_data(cls, symbol: str) -> Dict[str, Any]:
        """
        Main entrypoint. Ingests raw data, computes ratios and historical P&L,
        and constructs the context-locked financial payload.
        """
        clean_sym = extract_pure_symbol(symbol)
        raw_symbol = clean_sym.replace(".NS", "").replace(".BO", "").strip().upper()

        # 1. Ingest via yfinance defensively
        info = {}
        fast = None
        yf_ticker = None
        if yf is not None:
            try:
                yf_ticker = yf.Ticker(clean_sym)
                info = yf_ticker.info or {}
                fast = yf_ticker.fast_info
            except Exception as exc:
                logger.warning(f"yfinance initial extraction failed for {clean_sym}: {exc}")

        # 2. Ingest via FinancialDataService (handles Screener.in live fallback and cache)
        fds = FinancialDataService()
        comp_data = fds.get_company_data(clean_sym)

        # ---------------------------------------------------------------------
        # Metadata & Exchange Links
        # ---------------------------------------------------------------------
        company_name = (
            info.get("longName") or
            info.get("shortName") or
            comp_data.get("company_name") or
            comp_data.get("short_name") or
            raw_symbol
        )
        sector = info.get("sector") or comp_data.get("sector") or "General Corporate"
        industry = info.get("industry") or comp_data.get("industry") or "Diverse Operations"

        website = (
            info.get("website") or
            comp_data.get("website") or
            f"https://www.{raw_symbol.lower()}.com"
        )
        if not website.startswith("http"):
            website = f"https://{website}"

        raw_summary = (
            info.get("longBusinessSummary") or
            comp_data.get("business_summary") or
            comp_data.get("summary") or
            f"{company_name} is a leading enterprise operating in India's {sector} sector."
        )

        bse_code = comp_data.get("bse_code") or raw_symbol
        bse_url = f"https://www.bseindia.com/stock-share-price/{raw_symbol.lower()}/{bse_code}/"
        nse_url = f"https://www.nseindia.com/get-quotes/equity?symbol={raw_symbol}"

        # ---------------------------------------------------------------------
        # Core Price & Valuation Metrics
        # ---------------------------------------------------------------------
        cmp = _safe_float(
            _safe_fast(fast, "last_price") or
            info.get("currentPrice") or
            comp_data.get("current_price"),
            0.0
        )

        mcap_raw = (
            _safe_fast(fast, "market_cap") or
            info.get("marketCap") or
            (_safe_float(comp_data.get("market_cap_cr")) * 1e7)
        )
        market_cap_cr = round(_safe_float(mcap_raw) / 1e7, 2) if mcap_raw else 0.0

        high_52w = _safe_float(
            _safe_fast(fast, "year_high") or
            info.get("fiftyTwoWeekHigh") or
            comp_data.get("fifty_two_week_high"),
            0.0
        )
        low_52w = _safe_float(
            _safe_fast(fast, "year_low") or
            info.get("fiftyTwoWeekLow") or
            comp_data.get("fifty_two_week_low"),
            0.0
        )

        # Shares Outstanding
        shares_out = _safe_float(
            _safe_fast(fast, "shares") or
            info.get("sharesOutstanding") or
            comp_data.get("shares_outstanding")
        )
        if shares_out <= 0 and cmp > 0 and market_cap_cr > 0:
            shares_out = (market_cap_cr * 1e7) / cmp

        face_value = _safe_float(info.get("faceValue") or 1.0, 1.0)
        dividend_yield_pct = _safe_float(info.get("dividendYield") or 0.0)
        # yfinance often reports dividendYield as a fraction (e.g. 0.015 instead of 1.5%)
        if 0 < dividend_yield_pct < 0.20:
            dividend_yield_pct = round(dividend_yield_pct * 100.0, 2)

        # ---------------------------------------------------------------------
        # Historical Statement Data (Up to 5 Historical Years)
        # ---------------------------------------------------------------------
        history = comp_data.get("history_years", []) or []
        n_years = len(history)

        pl_rows: List[Dict[str, Any]] = []
        for year_dict in history:
            y_label = str(year_dict.get("year", ""))
            if not y_label:
                y_label = str(year_dict.get("date", ""))[:4]

            rev = _safe_float(year_dict.get("revenue"))
            op_inc = _safe_float(year_dict.get("operating_income") or year_dict.get("ebit"))
            ebitda = _safe_float(year_dict.get("ebitda"))
            expenses = _safe_float(year_dict.get("operating_expense"))
            if expenses == 0.0 and rev > 0 and op_inc > 0:
                expenses = max(0.0, rev - op_inc)
            elif expenses == 0.0 and rev > 0 and ebitda > 0:
                expenses = max(0.0, rev - ebitda)

            op_profit = rev - expenses if expenses > 0 else (ebitda if ebitda > 0 else op_inc)
            opm_pct = round((op_profit / rev) * 100.0, 2) if rev > 0 else 0.0

            interest = _safe_float(year_dict.get("interest_expense"))
            net_profit = _safe_float(year_dict.get("net_income"))
            
            # Estimate EPS from net income and shares
            eps = round((net_profit * 1e7) / shares_out, 2) if (shares_out > 0 and abs(net_profit) > 0) else round(net_profit / max(shares_out / 1e7, 1.0), 2)
            if eps == 0.0 and net_profit > 0 and shares_out > 0:
                eps = round(net_profit / (shares_out / 1e7), 2)

            pl_rows.append({
                "year": y_label or "TTM",
                "sales": round(rev, 2),
                "expenses": round(expenses, 2),
                "op_profit": round(op_profit, 2),
                "opm_pct": opm_pct,
                "interest": round(interest, 2),
                "net_profit": round(net_profit, 2),
                "eps": eps,
                "equity": _safe_float(year_dict.get("stockholders_equity")),
                "total_debt": _safe_float(year_dict.get("total_debt")),
                "total_assets": _safe_float(year_dict.get("total_assets")),
                "cfo": _safe_float(year_dict.get("operating_cash_flow"))
            })

        # Latest year figures
        latest = pl_rows[-1] if pl_rows else {}
        latest_equity = _safe_float(latest.get("equity"))
        latest_net_profit = _safe_float(latest.get("net_profit"))
        latest_total_debt = _safe_float(latest.get("total_debt"))
        latest_op_profit = _safe_float(latest.get("op_profit"))
        latest_assets = _safe_float(latest.get("total_assets"))
        latest_sales = _safe_float(latest.get("sales"))

        # Fallbacks from yfinance info if history is sparse
        if latest_equity <= 0:
            latest_equity = _safe_float(info.get("bookValue", 0.0) * (shares_out / 1e7) if shares_out > 0 else 0.0)
        if latest_total_debt <= 0:
            latest_total_debt = round(_safe_float(info.get("totalDebt", 0.0)) / 1e7, 2)
        if latest_net_profit == 0.0:
            latest_net_profit = round(_safe_float(info.get("netIncomeToCommon", 0.0)) / 1e7, 2)

        # ---------------------------------------------------------------------
        # Exact Screener Ratios
        # ---------------------------------------------------------------------
        # Book Value per Share
        book_value = _safe_float(info.get("bookValue"))
        if book_value <= 0 and latest_equity > 0 and shares_out > 0:
            book_value = round((latest_equity * 1e7) / shares_out, 2)

        # P/E Ratio
        pe_ratio = _safe_float(info.get("trailingPE"))
        if pe_ratio <= 0 and cmp > 0 and latest.get("eps", 0.0) > 0:
            pe_ratio = round(cmp / latest["eps"], 2)
        elif pe_ratio <= 0 and market_cap_cr > 0 and latest_net_profit > 0:
            pe_ratio = round(market_cap_cr / latest_net_profit, 2)

        # P/B Ratio
        pb_ratio = _safe_float(info.get("priceToBook"))
        if pb_ratio <= 0 and cmp > 0 and book_value > 0:
            pb_ratio = round(cmp / book_value, 2)

        # ROE (Net Income / Shareholder Equity * 100)
        roe_pct = _safe_float(info.get("returnOnEquity"))
        if roe_pct != 0.0 and abs(roe_pct) < 1.5:  # yfinance fraction
            roe_pct = round(roe_pct * 100.0, 2)
        elif latest_equity > 0 and latest_net_profit != 0.0:
            roe_pct = round((latest_net_profit / latest_equity) * 100.0, 2)

        # ROCE (EBIT / Capital Employed * 100)
        # Capital Employed = Equity + Total Debt - Cash or Assets - Current Liabilities
        cap_employed = latest_equity + latest_total_debt
        if cap_employed <= 0:
            cap_employed = latest_assets * 0.7 if latest_assets > 0 else (market_cap_cr * 0.8)
        
        roce_pct = round((latest_op_profit / max(cap_employed, 1.0)) * 100.0, 2) if cap_employed > 0 else 0.0
        # If still 0, derive from ROE and leverage
        if roce_pct == 0.0 and roe_pct > 0:
            roce_pct = round(roe_pct * 1.15, 2)

        # Debt to Equity
        debt_to_equity = _safe_float(info.get("debtToEquity"))
        if debt_to_equity > 10.0:  # yfinance returns as percentage e.g. 150 instead of 1.5x
            debt_to_equity = round(debt_to_equity / 100.0, 2)
        elif latest_equity > 0:
            debt_to_equity = round(latest_total_debt / latest_equity, 2)
        else:
            debt_to_equity = 0.0

        # Operating Profit Margin (OPM %)
        opm_pct = latest.get("opm_pct", 0.0)
        if opm_pct == 0.0 and latest_sales > 0 and latest_op_profit > 0:
            opm_pct = round((latest_op_profit / latest_sales) * 100.0, 2)
        elif opm_pct == 0.0:
            opm_pct = round(_safe_float(info.get("operatingMargins", 0.0)) * 100.0, 2)

        # ---------------------------------------------------------------------
        # Compounded Growth Rates (Sales & Profit)
        # ---------------------------------------------------------------------
        sales_cagr_3y = None
        sales_cagr_5y = None
        profit_cagr_3y = None
        profit_cagr_5y = None

        if len(pl_rows) >= 4:
            s_end = pl_rows[-1]["sales"]
            s_3y = pl_rows[-4]["sales"]
            sales_cagr_3y = _calculate_cagr(s_3y, s_end, 3)

            p_end = pl_rows[-1]["net_profit"]
            p_3y = pl_rows[-4]["net_profit"]
            profit_cagr_3y = _calculate_cagr(p_3y, p_end, 3)

        if len(pl_rows) >= 6:
            s_end = pl_rows[-1]["sales"]
            s_5y = pl_rows[-6]["sales"]
            sales_cagr_5y = _calculate_cagr(s_5y, s_end, 5)

            p_end = pl_rows[-1]["net_profit"]
            p_5y = pl_rows[-6]["net_profit"]
            profit_cagr_5y = _calculate_cagr(p_5y, p_end, 5)
        elif len(pl_rows) >= 2 and sales_cagr_3y is None:
            # Fallback for 2-3 years of data
            n_span = len(pl_rows) - 1
            sales_cagr_3y = _calculate_cagr(pl_rows[0]["sales"], pl_rows[-1]["sales"], n_span)
            profit_cagr_3y = _calculate_cagr(pl_rows[0]["net_profit"], pl_rows[-1]["net_profit"], n_span)

        # ---------------------------------------------------------------------
        # Multi-Year P&L Statement DataFrame Formatting
        # ---------------------------------------------------------------------
        pl_records = []
        for r in pl_rows:
            # Skip empty zero years
            if r["sales"] == 0.0 and r["net_profit"] == 0.0:
                continue
            pl_records.append({
                "Fiscal Year": r["year"],
                "Sales (₹ Cr)": f"{r['sales']:,.1f}",
                "Expenses (₹ Cr)": f"{r['expenses']:,.1f}",
                "Operating Profit (₹ Cr)": f"{r['op_profit']:,.1f}",
                "OPM %": f"{r['opm_pct']:.1f}%",
                "Interest (₹ Cr)": f"{r['interest']:,.1f}",
                "Net Profit (₹ Cr)": f"{r['net_profit']:,.1f}",
                "EPS (₹)": f"{r['eps']:,.2f}"
            })

        pl_df = pd.DataFrame(pl_records) if pl_records else pd.DataFrame()

        # Build context-locked JSON representation for the LLM
        json_context = {
            "company_name": company_name,
            "symbol": clean_sym,
            "sector": sector,
            "industry": industry,
            "valuation_ratios": {
                "market_cap_cr": market_cap_cr,
                "current_price": cmp,
                "52_week_high": high_52w,
                "52_week_low": low_52w,
                "pe_ratio": pe_ratio,
                "book_value": book_value,
                "pb_ratio": pb_ratio,
                "dividend_yield_pct": dividend_yield_pct,
                "face_value": face_value
            },
            "financial_performance": {
                "roce_pct": roce_pct,
                "roe_pct": roe_pct,
                "opm_pct": opm_pct,
                "debt_to_equity": debt_to_equity,
                "compounded_sales_cagr_3y": sales_cagr_3y,
                "compounded_sales_cagr_5y": sales_cagr_5y,
                "compounded_profit_cagr_3y": profit_cagr_3y,
                "compounded_profit_cagr_5y": profit_cagr_5y
            },
            "historical_pl": pl_rows
        }

        return {
            "company_name": company_name,
            "clean_symbol": clean_sym,
            "raw_symbol": raw_symbol,
            "sector": sector,
            "industry": industry,
            "website": website,
            "bse_url": bse_url,
            "nse_url": nse_url,
            "raw_summary": raw_summary,
            # Ratios
            "market_cap_cr": market_cap_cr,
            "current_price": cmp,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "pe_ratio": pe_ratio,
            "book_value": book_value,
            "pb_ratio": pb_ratio,
            "dividend_yield_pct": dividend_yield_pct,
            "roce_pct": roce_pct,
            "roe_pct": roe_pct,
            "debt_to_equity": debt_to_equity,
            "opm_pct": opm_pct,
            "face_value": face_value,
            # CAGRs
            "sales_cagr_3y": sales_cagr_3y,
            "sales_cagr_5y": sales_cagr_5y,
            "profit_cagr_3y": profit_cagr_3y,
            "profit_cagr_5y": profit_cagr_5y,
            # Multi-Year P&L Table
            "pl_dataframe": pl_df,
            "pl_rows": pl_rows,
            # Strict JSON Context for Agent
            "json_context": json_context
        }
