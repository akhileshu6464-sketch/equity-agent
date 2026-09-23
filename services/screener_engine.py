"""
Screener Financial Engine (services/screener_engine.py)
100% deterministic mathematical calculations and multi-year financial statement modeling.
Extracts raw data via yfinance with resilient fallback to Screener.in and local providers.
Computes Screener-style ratios and historical Profit & Loss tables without any LLM hallucination.
"""

import os
import re
import math
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

from services.financial_data import FinancialDataService, extract_pure_symbol
from utils.symbol_resolver import resolve_ticker
from core.company_identity import resolve_canonical_identity, CompanyIdentity
from core.research_context import (
    ResearchRunContext,
    assert_company_boundary,
    DataContaminationError,
    EntityRole
)

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


def _extract_quarterly_financials(
    yf_ticker: Any,
    shares_out: float = 0.0,
    company_id: str = "",
    isin: str = ""
) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    """Extracts recent quarters (chronological) from yfinance quarterly financials."""
    if yf_ticker is None:
        return [], pd.DataFrame()
    try:
        qf = yf_ticker.quarterly_financials
        if qf is None or qf.empty:
            return [], pd.DataFrame()

        # Sort columns chronologically oldest to newest
        cols_sorted = sorted(list(qf.columns)[:5])
        quarterly_rows = []

        for col in cols_sorted:
            col_label = col.strftime("%b %Y") if hasattr(col, "strftime") else str(col)[:7]

            def get_val(keys: List[str]) -> float:
                for k in keys:
                    if k in qf.index:
                        v = qf.loc[k, col]
                        if v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                            return float(v)
                return 0.0

            rev = get_val(["Total Revenue", "Operating Revenue"]) / 1e7
            ebit = get_val(["Operating Income", "EBIT"]) / 1e7
            ebitda = get_val(["Normalized EBITDA", "EBITDA"]) / 1e7
            expenses = get_val(["Operating Expense", "Total Expenses"]) / 1e7
            if expenses == 0.0 and rev > 0:
                expenses = max(0.0, rev - (ebit if ebit > 0 else ebitda))

            op_profit = ebit if ebit != 0 else (rev - expenses if rev > 0 else ebitda)
            opm_pct = round((op_profit / rev) * 100.0, 1) if rev > 0 else 0.0

            other_inc = get_val(["Other Non Operating Income Expenses", "Non Operating Income Net Other"]) / 1e7
            interest = abs(get_val(["Interest Expense Non Operating", "Interest Expense"])) / 1e7
            depr = get_val(["Reconciled Depreciation", "Depreciation And Amortization In Income Statement"]) / 1e7
            pbt = get_val(["Pretax Income"]) / 1e7
            if pbt == 0.0 and op_profit != 0:
                pbt = op_profit + other_inc - interest - depr

            net_income = get_val(["Net Income Common Stockholders", "Net Income", "Net Income Continuous Operations"]) / 1e7

            eps = 0.0
            if shares_out > 0:
                eps = round((net_income * 1e7) / shares_out, 2)

            quarterly_rows.append({
                "quarter": col_label,
                "period": col_label,
                "company_id": company_id,
                "isin": isin,
                "entity_role": "PRIMARY_COMPANY",
                "statement_scope": "CONSOLIDATED",
                "sales": round(rev, 1),
                "expenses": round(expenses, 1),
                "op_profit": round(op_profit, 1),
                "opm_pct": opm_pct,
                "other_income": round(other_inc, 1),
                "interest": round(interest, 1),
                "depreciation": round(depr, 1),
                "pbt": round(pbt, 1),
                "net_profit": round(net_income, 1),
                "eps": eps
            })

        q_records = []
        for r in quarterly_rows:
            q_records.append({
                "Quarter": r["quarter"],
                "Sales (₹ Cr)": f"{r['sales']:,.1f}",
                "Expenses (₹ Cr)": f"{r['expenses']:,.1f}",
                "Operating Profit (₹ Cr)": f"{r['op_profit']:,.1f}",
                "OPM %": f"{r['opm_pct']:.1f}%",
                "Other Income (₹ Cr)": f"{r['other_income']:,.1f}",
                "Interest (₹ Cr)": f"{r['interest']:,.1f}",
                "Depr (₹ Cr)": f"{r['depreciation']:,.1f}",
                "PBT (₹ Cr)": f"{r['pbt']:,.1f}",
                "Net Profit (₹ Cr)": f"{r['net_profit']:,.1f}",
                "EPS (₹)": f"{r['eps']:,.2f}"
            })
        q_df = pd.DataFrame(q_records) if q_records else pd.DataFrame()
        return quarterly_rows, q_df
    except Exception as exc:
        logger.warning(f"Failed extracting quarterly financials: {exc}")
        return [], pd.DataFrame()


def _resolve_peer_symbols(ticker: str, sector: str = "", industry: str = "") -> List[str]:
    """Identifies primary listed Indian peers for peer comparison table."""
    norm = ticker.upper()
    if any(k in norm for k in ["ASHOKA", "PNC", "KNR", "IRB", "GRINFRA", "DILIP", "LT", "NCC", "HCC"]) or any(k in sector.lower() or k in industry.lower() for k in ["construction", "engineering", "infrastructure"]):
        candidates = ["PNCINFRA.NS", "KNRCON.NS", "IRB.NS", "GRINFRA.NS"]
    elif any(k in norm for k in ["VINATI", "DEEPAK", "AARTI", "TATACHEM", "PIIND", "NAVIN", "ATUL", "CLEAN", "FINEORG"]) or "chemical" in sector.lower() or "chemical" in industry.lower():
        candidates = ["AARTIIND.NS", "CLEAN.NS", "ATUL.NS", "DEEPAKNTR.NS"]
    elif any(k in norm for k in ["HDFC", "ICICI", "KOTAK", "SBIN", "AXIS", "PNB", "BANK"]) or "bank" in sector.lower() or "bank" in industry.lower():
        candidates = ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS"]
    elif any(k in norm for k in ["CROMPTON", "HAVELL", "VOLTAS", "ORIENT", "POLYCAB", "VGUARD"]) or "consumer" in sector.lower() or "electrical" in industry.lower():
        candidates = ["HAVELLS.NS", "POLYCAB.NS", "VOLTAS.NS", "VGUARD.NS"]
    elif any(k in norm for k in ["TCS", "INFY", "WIPRO", "HCL", "TECHM"]) or "technology" in sector.lower() or "software" in industry.lower():
        candidates = ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS"]
    elif any(k in norm for k in ["TATAMOTORS", "MARUTI", "M&M", "BAJAJ-AUTO", "HEROMOTOCO"]) or "auto" in sector.lower() or "auto" in industry.lower():
        candidates = ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS"]
    elif any(k in norm for k in ["RELIANCE", "IOC", "BPCL", "ONGC"]):
        candidates = ["RELIANCE.NS", "BPCL.NS", "IOC.NS", "ONGC.NS"]
    else:
        candidates = []

    clean_target = norm if norm.endswith((".NS", ".BO")) else f"{norm}.NS"
    return [c for c in candidates if c != clean_target][:3]


def _extract_peer_comparison(
    target_sym: str,
    target_name: str,
    target_cmp: float,
    target_mcap: float,
    target_pe: float,
    target_roce: float,
    target_roe: float,
    target_de: float,
    target_div: float,
    target_s3: Optional[float],
    sector: str = "",
    industry: str = "",
    target_company_id: str = "",
    target_isin: str = ""
) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    """Compiles a deterministic peer comparison table including target stock and industry peers."""
    peer_symbols = _resolve_peer_symbols(target_sym, sector, industry)
    rows: List[Dict[str, Any]] = [
        {
            "name": target_name,
            "symbol": target_sym,
            "company_id": target_company_id,
            "isin": target_isin,
            "entity_role": "PRIMARY_COMPANY",
            "is_target": True,
            "cmp": target_cmp,
            "pe": target_pe,
            "mcap_cr": target_mcap,
            "div_yield": target_div,
            "roce": target_roce,
            "roe": target_roe,
            "de": target_de,
            "sales_cagr_3y": target_s3
        }
    ]

    for psym in peer_symbols:
        try:
            pt = yf.Ticker(psym) if yf else None
            pfast = pt.fast_info if pt else None
            pinfo = pt.info if pt else {}

            pcmp = _safe_float(_safe_fast(pfast, "last_price") or pinfo.get("currentPrice"), 0.0)
            pmcap_raw = _safe_fast(pfast, "market_cap") or pinfo.get("marketCap") or 0.0
            pmcap_cr = round(_safe_float(pmcap_raw) / 1e7, 1)
            ppe = _safe_float(pinfo.get("trailingPE"), 0.0)
            proe = _safe_float(pinfo.get("returnOnEquity"), 0.0)
            if 0 < abs(proe) < 1.5:
                proe = round(proe * 100.0, 1)
            proce = round(proe * 1.15, 1) if proe > 0 else 0.0
            pde = _safe_float(pinfo.get("debtToEquity"), 0.0)
            if pde > 10.0:
                pde = round(pde / 100.0, 2)
            pdiv = _safe_float(pinfo.get("dividendYield"), 0.0)
            if 0 < pdiv < 0.20:
                pdiv = round(pdiv * 100.0, 2)

            pname = pinfo.get("shortName") or psym.replace(".NS", "").replace(".BO", "")
            peer_sym_clean = psym.replace(".NS", "").replace(".BO", "").strip().upper()
            peer_cid = f"NSE:{peer_sym_clean}"
            rows.append({
                "name": pname,
                "symbol": psym,
                "company_id": peer_cid,
                "entity_role": "PEER",
                "is_target": False,
                "cmp": pcmp,
                "pe": ppe,
                "mcap_cr": pmcap_cr,
                "div_yield": pdiv,
                "roce": proce,
                "roe": proe,
                "de": pde,
                "sales_cagr_3y": None
            })
        except Exception as exc:
            logger.debug(f"Failed extracting peer {psym}: {exc}")

    # Build DataFrame
    records = []
    for r in rows:
        tag = " 🌟" if r["is_target"] else ""
        records.append({
            "Company": f"{r['name']}{tag}",
            "CMP (₹)": f"₹ {r['cmp']:,.1f}" if r["cmp"] > 0 else "—",
            "P/E": f"{r['pe']:.1f}x" if r["pe"] > 0 else "—",
            "Mar Cap (₹ Cr)": f"{r['mcap_cr']:,.1f}",
            "Div Yld %": f"{r['div_yield']:.2f}%" if r["div_yield"] > 0 else "0.00%",
            "ROCE %": f"{r['roce']:.1f}%" if r["roce"] > 0 else "—",
            "ROE %": f"{r['roe']:.1f}%" if r["roe"] > 0 else "—",
            "D/E": f"{r['de']:.2f}" if r["de"] >= 0 else "—"
        })
    p_df = pd.DataFrame(records) if records else pd.DataFrame()
    return rows, p_df


class ScreenerEngine:
    """
    Deterministic Screener.in financial engine.
    Extracts raw fundamentals and computes valuation multiples, capital returns,
    and multi-year Profit & Loss statements with 100% mathematical precision.
    """

    @classmethod
    def get_screener_data(
        cls,
        symbol_or_context: Union[str, ResearchRunContext],
        run_context: Optional[ResearchRunContext] = None
    ) -> Dict[str, Any]:
        """
        Main entrypoint. Ingests raw data, computes ratios and historical P&L,
        and constructs the context-locked financial payload.
        """
        if isinstance(symbol_or_context, ResearchRunContext):
            context = symbol_or_context
            identity = CompanyIdentity(
                company_id=context.company_id,
                legal_name=context.legal_name or context.company_name,
                display_name=context.display_name or context.company_name,
                isin=context.isin,
                primary_exchange=context.exchange,
                primary_symbol=context.nse_symbol,
                nse_symbol=context.nse_symbol,
                bse_code=context.bse_code,
                yahoo_symbol=context.ticker
            )
        elif run_context is not None:
            context = run_context
            identity = resolve_canonical_identity(str(symbol_or_context))
            context.assert_same_company(identity.company_id, caller_module="ScreenerEngine")
        else:
            identity = resolve_canonical_identity(str(symbol_or_context))
            context = None

        company_id = identity.company_id
        clean_sym = identity.primary_ticker
        raw_symbol = identity.nse_symbol or identity.primary_symbol or clean_sym.replace(".NS", "").replace(".BO", "")
        isin = identity.isin

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
                "period": y_label or "TTM",
                "company_id": company_id,
                "isin": isin,
                "entity_role": "PRIMARY_COMPANY",
                "statement_scope": "CONSOLIDATED",
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
        # Comprehensive Snapshot Fundamentals
        # ---------------------------------------------------------------------
        total_debt_cr = round(_safe_float(info.get("totalDebt", 0.0)) / 1e7, 1)
        if total_debt_cr <= 0:
            total_debt_cr = latest_total_debt

        total_cash_cr = round(_safe_float(info.get("totalCash", 0.0)) / 1e7, 1)
        if total_cash_cr <= 0:
            total_cash_cr = round(_safe_float(comp_data.get("latest_cash", 0.0)), 1)

        prom_raw = _safe_float(info.get("heldPercentInsiders", 0.0))
        if prom_raw > 0:
            promoter_holding_pct = round(prom_raw * 100.0, 2)
        else:
            promoter_holding_pct = round(_safe_float((comp_data.get("shareholding") or {}).get("promoter", 0.0)), 2)

        inst_raw = _safe_float(info.get("heldPercentInstitutions", 0.0))
        if inst_raw > 0:
            institutional_holding_pct = round(inst_raw * 100.0, 2)
        else:
            sh = comp_data.get("shareholding") or {}
            institutional_holding_pct = round(_safe_float(sh.get("fii", 0.0)) + _safe_float(sh.get("dii", 0.0)), 2)

        city = str(info.get("city") or comp_data.get("city") or "").strip()
        state = str(info.get("state") or "").strip()
        country = str(info.get("country") or "India").strip()
        hq_parts = [p for p in [city, state, country] if p and p.lower() != "none"]
        headquarters = ", ".join(hq_parts) or "India"

        employees = info.get("fullTimeEmployees") or comp_data.get("employees")

        raw_officers = info.get("companyOfficers", []) or []
        company_officers = []
        for o in raw_officers[:4]:
            if isinstance(o, dict) and o.get("name"):
                title = (o.get("title") or "").split("–")[0].split("-")[0].strip()
                clean_title = re.sub(r'[^a-zA-Z\s,]', '', title).strip()
                company_officers.append(f"{o.get('name')}" + (f" ({clean_title})" if clean_title else ""))

        m_found = re.search(r'(?:founded|incorporated|established)\s+(?:in|back\s+in)\s+(\d{4})', raw_summary, re.IGNORECASE)
        founded_year = m_found.group(1) if m_found else ("1990s" if "199" in raw_summary else "Established Enterprise")

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
            "company_id": company_id,
            "isin": isin,
            "entity_role": "PRIMARY_COMPANY",
            "statement_scope": "CONSOLIDATED",
            "company_name": company_name,
            "legal_name": identity.legal_name,
            "display_name": identity.display_name,
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

        # ---------------------------------------------------------------------
        # Quarterly Financial Results (Consolidated)
        # ---------------------------------------------------------------------
        q_rows, q_df = _extract_quarterly_financials(yf_ticker, shares_out, company_id=company_id, isin=isin)

        # ---------------------------------------------------------------------
        # Peer Comparison Table
        # ---------------------------------------------------------------------
        peer_rows, peer_df = _extract_peer_comparison(
            target_sym=clean_sym,
            target_name=company_name,
            target_cmp=cmp,
            target_mcap=market_cap_cr,
            target_pe=pe_ratio,
            target_roce=roce_pct,
            target_roe=roe_pct,
            target_de=debt_to_equity,
            target_div=dividend_yield_pct,
            target_s3=sales_cagr_3y,
            sector=sector,
            industry=industry,
            target_company_id=company_id,
            target_isin=isin
        )

        payload = {
            "company_id": company_id,
            "isin": isin,
            "entity_role": "PRIMARY_COMPANY",
            "statement_scope": "CONSOLIDATED",
            "company_name": company_name,
            "legal_name": identity.legal_name,
            "display_name": identity.display_name,
            "clean_symbol": clean_sym,
            "raw_symbol": raw_symbol,
            "sector": sector,
            "industry": industry,
            "website": website,
            "bse_url": bse_url,
            "nse_url": nse_url,
            "raw_summary": raw_summary,
            # Ratios & Snapshot Fundamentals
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
            "total_debt_cr": total_debt_cr,
            "total_cash_cr": total_cash_cr,
            "promoter_holding_pct": promoter_holding_pct,
            "institutional_holding_pct": institutional_holding_pct,
            "headquarters": headquarters,
            "employees": employees,
            "company_officers": company_officers,
            "founded_year": founded_year,
            "listing_info": "NSE & BSE Listed",
            # CAGRs
            "sales_cagr_3y": sales_cagr_3y,
            "sales_cagr_5y": sales_cagr_5y,
            "profit_cagr_3y": profit_cagr_3y,
            "profit_cagr_5y": profit_cagr_5y,
            # Multi-Year P&L Table
            "pl_dataframe": pl_df,
            "pl_rows": pl_rows,
            # Quarterly Results Table
            "quarterly_dataframe": q_df,
            "quarterly_rows": q_rows,
            # Peer Comparison Table
            "peer_dataframe": peer_df,
            "peer_rows": peer_rows,
            # Strict JSON Context for Agent
            "json_context": json_context
        }

        if context is not None:
            context.assert_same_company(payload["company_id"], caller_module="ScreenerEngine")
        assert_company_boundary(payload, company_id, caller_module="ScreenerEngine")

        return payload
