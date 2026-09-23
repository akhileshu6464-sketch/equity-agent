"""
Deterministic Financial Engine (services/financial_engine.py)
Computes all valuation, growth, operational, working capital, cash conversion,
solvency, and earnings quality metrics directly from raw financial statements
before any LLM invocation.

Wraps pre-calculated figures into strict <verified_financials> XML blocks
to enforce primary numerical truth and eliminate hallucinated constants.
"""

import math
import logging
from typing import Dict, Any, List, Optional

from calculations.growth import cagr as calc_cagr, revenue_growth as calc_revenue_growth, yoy_change as calc_yoy_change
from calculations.margins import (
    ebitda_margin as calc_ebitda_margin,
    ebit_margin as calc_ebit_margin,
    pat_margin as calc_pat_margin,
    gross_margin as calc_gross_margin,
    margin_change_bps as calc_margin_change_bps,
)
from calculations.profitability import (
    roe as calc_roe,
    roce as calc_roce,
    roic as calc_roic,
    asset_turnover as calc_asset_turnover,
)
from calculations.cashflow import (
    cfo_to_pat as calc_cfo_to_pat,
    free_cash_flow as calc_free_cash_flow,
    fcf_yield as calc_fcf_yield,
    cash_flow_reconciliation as calc_cash_flow_reconciliation,
)
from calculations.leverage import (
    debt_to_equity as calc_debt_to_equity,
    net_debt as calc_net_debt,
    net_debt_to_ebitda as calc_net_debt_to_ebitda,
    interest_coverage as calc_interest_coverage,
)
from calculations.working_capital import (
    net_working_capital as calc_net_working_capital,
    receivable_days as calc_receivable_days,
    inventory_days as calc_inventory_days,
    payable_days as calc_payable_days,
    cash_conversion_cycle as calc_cash_conversion_cycle,
)
from calculations.valuation import (
    pe_ratio as calc_pe_ratio,
    pb_ratio as calc_pb_ratio,
    market_capitalization as calc_market_cap,
    enterprise_value as calc_enterprise_value,
    ev_to_ebitda as calc_ev_to_ebitda,
    ev_to_sales as calc_ev_to_sales,
)
from calculations.shareholding import (
    promoter_holding_change as calc_promoter_holding_change,
    promoter_pledge_percentage as calc_promoter_pledge_percentage,
)
from calculations.normalization import normalize_to_inr, format_inr_crores, format_percentage
from calculations.audit import global_audit_registry

logger = logging.getLogger("EquityPipeline.FinancialEngine")


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Converts a value to float safely."""
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


def _to_cr(val: float) -> float:
    """Converts raw INR value to Crores (1 Cr = 1e7 INR) if > 1e6."""
    v = _safe_float(val)
    if abs(v) > 1e6:
        return round(v / 1e7, 2)
    return round(v, 2)


def calculate_dynamic_wacc(ticker_data: Dict[str, Any]) -> float:
    """
    Computes dynamic Weighted Average Cost of Capital (WACC) using CAPM and capital structure.

    1. Macro benchmarks (India G-Sec 10Y and ERP):
       - Risk-free rate = 7.0% (0.070)
       - Equity Risk Premium = 5.5% (0.055)
       - Indian corporate tax rate = 25.17% (0.2517 under Section 115BAA)

    2. Company-specific inputs:
       - Beta from exchange filings or fallback 1.0
       - Cost of Equity: Ke = Rf + Beta * ERP

    3. Capital structure:
       - Market Capitalization (E) and Total Debt (D)
       - Weight of Equity: We = E / (E + D)
       - Weight of Debt: Wd = D / (E + D)

    4. Cost of Debt (Kd):
       - Estimated from interest expense / total debt, or corporate lending rate fallback ~8.5%

    5. Weighted Average:
       - WACC = (We * Ke) + (Wd * Kd * (1 - TaxRate))
       - Returns round(wacc, 4)
    """
    if not isinstance(ticker_data, dict):
        return 0.115

    # 1. Macro benchmarks (India G-Sec 10Y and ERP)
    risk_free_rate = 0.070   # ~7.0%
    equity_risk_premium = 0.055 # ~5.5%
    tax_rate = 0.2517        # Indian standard corporate tax (25.17%)

    # 2. Company-specific inputs
    raw_info = ticker_data.get("raw_info") or {}
    beta_val = ticker_data.get("beta")
    if beta_val is None or _safe_float(beta_val) <= 0:
        beta_val = raw_info.get("beta") or 1.0
    beta = max(0.2, min(_safe_float(beta_val, 1.0), 3.0))
    cost_of_equity = risk_free_rate + (beta * equity_risk_premium)

    # 3. Capital structure
    history = ticker_data.get("history_years", [])
    latest_hist = history[-1] if history else {}

    market_cap = (
        _safe_float(ticker_data.get("marketCap")) or
        _safe_float(ticker_data.get("market_cap")) or
        (_safe_float(ticker_data.get("market_cap_cr")) * 1e7) or
        _safe_float(raw_info.get("marketCap")) or
        0.0
    )
    total_debt = (
        _safe_float(ticker_data.get("totalDebt")) or
        _safe_float(ticker_data.get("total_debt")) or
        (_safe_float(ticker_data.get("total_debt_cr")) * 1e7) or
        _safe_float(raw_info.get("totalDebt")) or
        _safe_float(latest_hist.get("total_debt")) or
        0.0
    )
    total_value = market_cap + total_debt

    if total_value == 0:
        return round(cost_of_equity, 4)

    weight_equity = market_cap / total_value
    weight_debt = total_debt / total_value

    # 4. Cost of debt (estimated from interest expense or synthetic rating)
    interest_expense = abs(
        _safe_float(ticker_data.get("interestExpense")) or
        _safe_float(ticker_data.get("interest_expense")) or
        _safe_float(raw_info.get("interestExpense")) or
        _safe_float(latest_hist.get("interest_expense")) or
        0.0
    )
    if total_debt > 0 and interest_expense > 0:
        cost_of_debt = interest_expense / total_debt
        # Bound between realistic lending rates [4.5%, 20%]
        if cost_of_debt > 0.20 or cost_of_debt < 0.045:
            cost_of_debt = 0.085
    else:
        cost_of_debt = 0.085  # Fallback corporate lending rate ~8.5%

    # 5. Weighted Average
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
    return round(wacc, 4)


class FinancialEngine:
    """Deterministic mathematical computation engine for financial and accounting ratios."""

    calculate_dynamic_wacc = staticmethod(calculate_dynamic_wacc)

    @staticmethod
    def compute_metrics(company_data: Dict[str, Any], is_bfsi: bool = False) -> Dict[str, Any]:
        """
        Computes all financial, operational, solvency, working capital, and valuation metrics
        from standardized company financial statements.
        """
        history: List[Dict[str, Any]] = company_data.get("history_years", []) or []
        cmp = _safe_float(company_data.get("current_price"), 0.0)
        mcap_cr = _safe_float(company_data.get("market_cap_cr"), 0.0)
        shares_out = _safe_float(company_data.get("shares_outstanding"), 0.0)
        if shares_out <= 0 and cmp > 0 and mcap_cr > 0:
            shares_out = (mcap_cr * 1e7) / cmp

        shareholding = company_data.get("shareholding", {}) or {}
        raw_pledge = shareholding.get("promoter_pledge_pct")
        promoter_pledge_pct = float(raw_pledge) if raw_pledge is not None and str(raw_pledge).strip() not in ["", "None", "N/A"] else 0.0

        raw_promoter = shareholding.get("promoter_holding_pct")
        promoter_holding_pct = float(raw_promoter) if raw_promoter is not None and str(raw_promoter).strip() not in ["", "None", "N/A"] else None

        raw_inst = shareholding.get("institutional_holding_pct")
        institutional_holding_pct = float(raw_inst) if raw_inst is not None and str(raw_inst).strip() not in ["", "None", "N/A"] else None

        # Slice historical years (most recent is last)
        n_years = len(history)
        latest = history[-1] if n_years > 0 else {}
        y_3yr_ago = history[-4] if n_years >= 4 else (history[0] if n_years > 1 else latest)
        y_5yr_ago = history[-6] if n_years >= 6 else (history[0] if n_years > 1 else latest)

        periods_3y = min(3, n_years - 1) if n_years > 1 else 1
        periods_5y = min(5, n_years - 1) if n_years > 1 else 1

        # ---------------------------------------------------------------------
        # 1. 3-Year & 5-Year Revenue and PAT CAGRs
        # ---------------------------------------------------------------------
        latest_rev = _safe_float(latest.get("revenue")) if latest.get("revenue") is not None else None
        rev_3y_ago = _safe_float(y_3yr_ago.get("revenue")) if y_3yr_ago.get("revenue") is not None else None
        rev_5y_ago = _safe_float(y_5yr_ago.get("revenue")) if y_5yr_ago.get("revenue") is not None else None

        r3_res = calc_cagr(rev_3y_ago, latest_rev, periods_3y)
        rev_cagr_3y = round(r3_res.value, 2) if r3_res.value is not None else None

        r5_res = calc_cagr(rev_5y_ago, latest_rev, periods_5y)
        rev_cagr_5y = round(r5_res.value, 2) if r5_res.value is not None else None

        latest_pat = _safe_float(latest.get("net_income")) if latest.get("net_income") is not None else None
        pat_3y_ago = _safe_float(y_3yr_ago.get("net_income")) if y_3yr_ago.get("net_income") is not None else None
        pat_5y_ago = _safe_float(y_5yr_ago.get("net_income")) if y_5yr_ago.get("net_income") is not None else None

        p3_res = calc_cagr(pat_3y_ago, latest_pat, periods_3y)
        pat_cagr_3y = round(p3_res.value, 2) if p3_res.value is not None else None

        p5_res = calc_cagr(pat_5y_ago, latest_pat, periods_5y)
        pat_cagr_5y = round(p5_res.value, 2) if p5_res.value is not None else None

        # ---------------------------------------------------------------------
        # 2. Working Capital & Cash Conversion Cycle (DIO + DSO - DPO)
        # ---------------------------------------------------------------------
        latest_rec = _safe_float(latest.get("receivables")) if latest.get("receivables") is not None else None
        latest_inv = _safe_float(latest.get("inventory")) if latest.get("inventory") is not None else None
        latest_pay = _safe_float(latest.get("payables")) if latest.get("payables") is not None else None
        latest_cogs = _safe_float(latest.get("operating_expense")) if latest.get("operating_expense") is not None else None

        if not is_bfsi and latest_rev and latest_rev > 0:
            dso_res = calc_receivable_days(latest_rec, latest_rev)
            dio_res = calc_inventory_days(latest_inv, latest_cogs)
            dpo_res = calc_payable_days(latest_pay, latest_cogs)
            dso_days = round(dso_res.value, 1) if dso_res.value is not None else None
            dio_days = round(dio_res.value, 1) if dio_res.value is not None else None
            dpo_days = round(dpo_res.value, 1) if dpo_res.value is not None else None
            ccc_res = calc_cash_conversion_cycle(dso_days, dio_days, dpo_days)
            ccc_days = round(ccc_res.value, 1) if ccc_res.value is not None else None
        else:
            dso_days = None
            dio_days = None
            dpo_days = None
            ccc_days = None

        # ---------------------------------------------------------------------
        # 3. Earnings Quality Score: Cumulative 5-Year CFO / 5-Year PAT
        # ---------------------------------------------------------------------
        cfo_5y_list = [_safe_float(y.get("operating_cash_flow")) for y in history[-5:]] if history else []
        pat_5y_list = [_safe_float(y.get("net_income")) for y in history[-5:]] if history else []

        total_cfo_5y_raw = sum(cfo_5y_list) if cfo_5y_list else 0.0
        total_pat_5y_raw = sum(pat_5y_list) if pat_5y_list else 0.0

        total_cfo_5y_cr = _to_cr(total_cfo_5y_raw)
        total_pat_5y_cr = _to_cr(total_pat_5y_raw)

        cfo_pat_res = calc_cash_flow_reconciliation(cfo_5y_list, pat_5y_list)
        cfo_to_pat_5y_pct = round(cfo_pat_res.value, 2) if cfo_pat_res.value is not None else None

        if cfo_to_pat_5y_pct is not None:
            earnings_quality_verdict = (
                "EXCELLENT (>100% Cash Realization)" if cfo_to_pat_5y_pct >= 95.0
                else ("GOOD (80%-95% Cash Realization)" if cfo_to_pat_5y_pct >= 80.0
                      else "ACCURAL HEAVY / CAUTION (<80% Cash Realization)")
            )
        else:
            earnings_quality_verdict = "INSUFFICIENT HISTORICAL CASH FLOW DATA"

        # ---------------------------------------------------------------------
        # 4. Solvency: Net Debt to EBITDA, Interest Coverage, Promoter Pledge
        # ---------------------------------------------------------------------
        raw_total_debt = _safe_float(latest.get("total_debt") or company_data.get("latest_total_debt")) if (latest.get("total_debt") is not None or company_data.get("latest_total_debt") is not None) else 0.0
        raw_cash = _safe_float(latest.get("cash_and_equivalents") or company_data.get("latest_cash")) if (latest.get("cash_and_equivalents") is not None or company_data.get("latest_cash") is not None) else 0.0
        raw_equity = _safe_float(latest.get("stockholders_equity")) if latest.get("stockholders_equity") is not None else None
        raw_assets = _safe_float(latest.get("total_assets")) if latest.get("total_assets") is not None else None

        total_debt_cr = _to_cr(raw_total_debt)
        cash_cr = _to_cr(raw_cash)
        net_debt_cr = round(total_debt_cr - cash_cr, 2)
        equity_cr = _to_cr(raw_equity) if raw_equity is not None else 0.0
        total_assets_cr = _to_cr(raw_assets) if raw_assets is not None else 0.0

        ebitda_latest = _safe_float(latest.get("ebitda")) if latest.get("ebitda") is not None else None
        ebit_latest = _safe_float(latest.get("ebit") or latest.get("operating_income")) if (latest.get("ebit") is not None or latest.get("operating_income") is not None) else None
        interest_latest = abs(_safe_float(latest.get("interest_expense"))) if latest.get("interest_expense") is not None else None

        nd_ebitda_res = calc_net_debt_to_ebitda(net_debt_cr, _to_cr(ebitda_latest) if ebitda_latest is not None else None)
        net_debt_to_ebitda = round(nd_ebitda_res.value, 2) if nd_ebitda_res.value is not None else None

        icr_res = calc_interest_coverage(ebit_latest, interest_latest)
        interest_coverage = round(icr_res.value, 2) if icr_res.value is not None else None

        de_res = calc_debt_to_equity(total_debt_cr, equity_cr)
        debt_to_equity = round(de_res.value, 2) if de_res.value is not None else None

        nde_res = calc_debt_to_equity(net_debt_cr, equity_cr)
        net_debt_to_equity = round(nde_res.value, 2) if nde_res.value is not None else None

        # ---------------------------------------------------------------------
        # 5. Profitability & Returns (ROCE, ROIC, ROE, ROA, Margins)
        # ---------------------------------------------------------------------
        invested_capital = (raw_equity + raw_total_debt - raw_cash) if (raw_equity is not None and (raw_equity + raw_total_debt - raw_cash) > 0) else None
        nopat = (ebit_latest * 0.7483) if ebit_latest is not None else None  # Section 115BAA corporate tax rate (25.17%)

        roic_res = calc_roic(nopat, invested_capital)
        roic_pct = round(roic_res.value, 2) if roic_res.value is not None else None

        roce_res = calc_roce(ebit_latest, None, invested_capital)
        roce_pct = round(roce_res.value, 2) if roce_res.value is not None else None

        roe_res = calc_roe(latest_pat, None, raw_equity)
        roe_pct = round(roe_res.value, 2) if roe_res.value is not None else None

        roa_res = calc_pat_margin(latest_pat, raw_assets)
        roa_pct = round(roa_res.value, 2) if roa_res.value is not None else None

        gm_res = calc_gross_margin(latest_rev, latest_cogs)
        gross_margin_pct = round(gm_res.value, 2) if gm_res.value is not None else None

        ebitda_m_res = calc_ebitda_margin(ebitda_latest, latest_rev)
        ebitda_margin_pct = round(ebitda_m_res.value, 2) if ebitda_m_res.value is not None else None

        pat_m_res = calc_pat_margin(latest_pat, latest_rev)
        pat_margin_pct = round(pat_m_res.value, 2) if pat_m_res.value is not None else None

        # ---------------------------------------------------------------------
        # 6. Valuation Multiples & Free Cash Flow
        # ---------------------------------------------------------------------
        pe_ratio = _safe_float(company_data.get("trailing_pe"))
        if (pe_ratio is None or pe_ratio <= 0) and latest_pat and latest_pat > 0 and mcap_cr > 0:
            pe_res = calc_pe_ratio(mcap_cr * 1e7, latest_pat)
            pe_ratio = round(pe_res.value, 2) if pe_res.value is not None else None

        ev_to_ebitda = _safe_float(company_data.get("ev_to_ebitda"))
        if (ev_to_ebitda is None or ev_to_ebitda <= 0) and ebitda_latest and ebitda_latest > 0 and mcap_cr > 0:
            ev_cr = mcap_cr + net_debt_cr
            ev_res = calc_ev_to_ebitda(ev_cr, _to_cr(ebitda_latest))
            ev_to_ebitda = round(ev_res.value, 2) if ev_res.value is not None else None

        pb_ratio = _safe_float(company_data.get("price_to_book"))
        if (pb_ratio is None or pb_ratio <= 0) and equity_cr and equity_cr > 0 and mcap_cr > 0:
            pb_res = calc_pb_ratio(mcap_cr, equity_cr)
            pb_ratio = round(pb_res.value, 2) if pb_res.value is not None else None

        latest_fcf_raw = latest.get("free_cash_flow")
        if latest_fcf_raw is None:
            cfo_lat = latest.get("operating_cash_flow")
            capex_lat = latest.get("capital_expenditure")
            if cfo_lat is not None:
                fcf_res = calc_free_cash_flow(_safe_float(cfo_lat), _safe_float(capex_lat) if capex_lat is not None else 0.0)
                latest_fcf_raw = fcf_res.value

        latest_fcf_cr = _to_cr(_safe_float(latest_fcf_raw)) if latest_fcf_raw is not None else None
        fcf_y_res = calc_fcf_yield(latest_fcf_cr, mcap_cr) if (latest_fcf_cr is not None and mcap_cr > 0) else None
        fcf_yield_pct = round(fcf_y_res.value, 2) if (fcf_y_res and fcf_y_res.value is not None) else None

        # ---------------------------------------------------------------------
        # 7. Sector-Specific Ratios (BFSI Banking vs Non-BFSI)
        # ---------------------------------------------------------------------
        if is_bfsi:
            banking_data = company_data.get("banking_ratios") or {}
            crar_pct = banking_data.get("crar_pct")
            tier1_cet1_pct = banking_data.get("tier1_cet1_pct")
            cost_to_income_pct = banking_data.get("cost_to_income_pct")
            nim_pct = banking_data.get("nim_pct")
            gnpa_pct = banking_data.get("gnpa_pct")
            nnpa_pct = banking_data.get("nnpa_pct")
            pcr_pct = banking_data.get("pcr_pct")
            credit_cost_pct = banking_data.get("credit_cost_pct")
            casa_pct = banking_data.get("casa_pct")
        else:
            crar_pct = None
            tier1_cet1_pct = None
            cost_to_income_pct = None
            nim_pct = None
            gnpa_pct = None
            nnpa_pct = None
            pcr_pct = None
            credit_cost_pct = None
            casa_pct = None

        # Dynamic WACC and Cost of Equity (CAPM)
        dynamic_wacc = calculate_dynamic_wacc(company_data)
        wacc_pct = round(dynamic_wacc * 100, 2)
        raw_info = company_data.get("raw_info") or {}
        beta_val = company_data.get("beta")
        if beta_val is None or _safe_float(beta_val) <= 0:
            beta_val = raw_info.get("beta") or 1.0
        beta = max(0.2, min(_safe_float(beta_val, 1.0), 3.0))
        coe_pct = round((0.070 + (beta * 0.055)) * 100, 2)

        return {
            "symbol": company_data.get("symbol", ""),
            "company_name": company_data.get("short_name", ""),
            "current_price": cmp,
            "market_cap_cr": mcap_cr,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "ev_to_ebitda": ev_to_ebitda,
            "shares_outstanding": shares_out,
            # Dynamic WACC & Cost of Capital
            "wacc": dynamic_wacc,
            "wacc_pct": wacc_pct,
            "cost_of_equity_pct": coe_pct,
            "beta": round(beta, 2),
            # Growth CAGRs
            "rev_cagr_3y": rev_cagr_3y,
            "rev_cagr_5y": rev_cagr_5y,
            "pat_cagr_3y": pat_cagr_3y,
            "pat_cagr_5y": pat_cagr_5y,
            # Working Capital
            "dio_days": dio_days,
            "dso_days": dso_days,
            "dpo_days": dpo_days,
            "ccc_days": ccc_days,
            # Cash Flow & Earnings Quality
            "cfo_5y_cr": total_cfo_5y_cr,
            "pat_5y_cr": total_pat_5y_cr,
            "cfo_to_pat_5y_pct": cfo_to_pat_5y_pct,
            "earnings_quality_verdict": earnings_quality_verdict,
            "latest_fcf_cr": latest_fcf_cr,
            "fcf_yield_pct": fcf_yield_pct,
            # Solvency
            "total_debt_cr": total_debt_cr,
            "cash_cr": cash_cr,
            "net_debt_cr": net_debt_cr,
            "equity_cr": equity_cr,
            "total_assets_cr": total_assets_cr,
            "net_debt_to_ebitda": net_debt_to_ebitda,
            "interest_coverage": interest_coverage,
            "debt_to_equity": debt_to_equity,
            "net_debt_to_equity": net_debt_to_equity,
            "promoter_pledge_pct": promoter_pledge_pct,
            "promoter_holding_pct": promoter_holding_pct,
            "institutional_holding_pct": institutional_holding_pct,
            # Returns & Margins
            "roce_pct": roce_pct,
            "roic_pct": roic_pct,
            "roe_pct": roe_pct,
            "roa_pct": roa_pct,
            "gross_margin_pct": gross_margin_pct,
            "ebitda_margin_pct": ebitda_margin_pct,
            "pat_margin_pct": pat_margin_pct,
            # Banking
            "is_bfsi": is_bfsi,
            "nim_pct": nim_pct,
            "casa_pct": casa_pct,
            "gnpa_pct": gnpa_pct,
            "nnpa_pct": nnpa_pct,
            "pcr_pct": pcr_pct,
            "crar_pct": crar_pct,
            "tier1_cet1_pct": tier1_cet1_pct,
            "credit_cost_pct": credit_cost_pct,
            "cost_to_income_pct": cost_to_income_pct
        }

    @staticmethod
    def format_verified_financials_block(metrics: Dict[str, Any], is_bfsi: bool = False) -> str:
        """
        Formats calculated metrics into an XML block wrapped in <verified_financials> tags
        for strict context locking in LLM prompts.
        Enforces Section 65: Absolute LLM prompt rule forbidding ratio recalculation or number invention.
        """
        def _fmt_val(val: Any, suffix: str = "", prefix: str = "", decimals: int = 2) -> str:
            if val is None or str(val).strip() in ["", "None", "N/A"]:
                return "Not Disclosed in Available Statements"
            try:
                f = float(val)
                return f"{prefix}{f:,.{decimals}f}{suffix}"
            except (ValueError, TypeError):
                return str(val)

        cmp_str = _fmt_val(metrics.get("current_price"), prefix="₹")
        mcap_str = _fmt_val(metrics.get("market_cap_cr"), suffix=" Cr", prefix="₹")
        pe_str = _fmt_val(metrics.get("pe_ratio"), suffix="x", decimals=1)
        ev_ebitda_str = _fmt_val(metrics.get("ev_to_ebitda"), suffix="x", decimals=1)
        pb_str = _fmt_val(metrics.get("pb_ratio"), suffix="x")

        r3_str = _fmt_val(metrics.get("rev_cagr_3y"), suffix="%")
        r5_str = _fmt_val(metrics.get("rev_cagr_5y"), suffix="%")
        p3_str = _fmt_val(metrics.get("pat_cagr_3y"), suffix="%")
        p5_str = _fmt_val(metrics.get("pat_cagr_5y"), suffix="%")

        cfo_5y_str = _fmt_val(metrics.get("cfo_5y_cr"), suffix=" Cr", prefix="₹")
        pat_5y_str = _fmt_val(metrics.get("pat_5y_cr"), suffix=" Cr", prefix="₹")
        cfo_pat_str = _fmt_val(metrics.get("cfo_to_pat_5y_pct"), suffix="%")
        eq_verdict = metrics.get("earnings_quality_verdict", "INSUFFICIENT DATA")

        tot_debt_str = _fmt_val(metrics.get("total_debt_cr"), suffix=" Cr", prefix="₹")
        cash_str = _fmt_val(metrics.get("cash_cr"), suffix=" Cr", prefix="₹")
        net_debt = metrics.get("net_debt_cr")
        if net_debt is not None:
            net_debt_desc = f"-₹{abs(net_debt):,.2f} Cr (Net Cash Positive)" if net_debt < 0 else f"₹{net_debt:,.2f} Cr"
        else:
            net_debt_desc = "Not Disclosed"

        nd_ebitda_str = _fmt_val(metrics.get("net_debt_to_ebitda"), suffix="x")
        icr_str = _fmt_val(metrics.get("interest_coverage"), suffix="x", decimals=1)
        de_str = _fmt_val(metrics.get("debt_to_equity"), suffix="x")
        pledge_str = _fmt_val(metrics.get("promoter_pledge_pct"), suffix="%")
        promoter_str = _fmt_val(metrics.get("promoter_holding_pct"), suffix="%")
        institutions_str = _fmt_val(metrics.get("institutional_holding_pct"), suffix="%")

        roce_str = _fmt_val(metrics.get("roce_pct"), suffix="%")
        roic_str = _fmt_val(metrics.get("roic_pct"), suffix="%")
        roe_str = _fmt_val(metrics.get("roe_pct"), suffix="%")
        roa_str = _fmt_val(metrics.get("roa_pct"), suffix="%")
        gm_str = _fmt_val(metrics.get("gross_margin_pct"), suffix="%")
        ebitda_m_str = _fmt_val(metrics.get("ebitda_margin_pct"), suffix="%")

        wacc_p_str = _fmt_val(metrics.get("wacc_pct"), suffix="%")
        coe_p_str = _fmt_val(metrics.get("cost_of_equity_pct"), suffix="%")
        beta_str = _fmt_val(metrics.get("beta"))

        lines = [
            "<verified_financials>",
            "<!-- SYSTEM DIRECTIVE (NON-NEGOTIABLE):",
            "You are receiving verified and programmatically calculated financial metrics. Treat numerical values as authoritative inputs. Do not recalculate, alter, approximate, interpolate, or invent numerical values. Do not introduce financial numbers that are not present in the supplied structured data or cited source evidence. If a required number is unavailable, state that it is unavailable.",
            "-->",
            "[CORE_VALUATION_METRICS]",
            f"Current Market Price (CMP): {cmp_str}",
            f"Market Capitalization: {mcap_str}",
            f"Trailing P/E Ratio: {pe_str}",
            f"Price to Book (P/BV): {pb_str}",
            f"EV/EBITDA: {ev_ebitda_str}" if not is_bfsi else "EV/EBITDA: N/A (Financial Institution)",
            f"Beta: {beta_str}",
            f"Cost of Equity (CAPM: Rf 7.0% + Beta x ERP 5.5%): {coe_p_str}",
            f"Dynamic WACC Hurdle Rate: {wacc_p_str}",
            "",
            "[HISTORICAL_GROWTH_CAGR]",
            f"3-Year Consolidated Revenue CAGR: {r3_str}",
            f"5-Year Consolidated Revenue CAGR: {r5_str}",
            f"3-Year Consolidated PAT CAGR: {p3_str}",
            f"5-Year Consolidated PAT CAGR: {p5_str}",
            ""
        ]

        if not is_bfsi:
            dio_str = _fmt_val(metrics.get("dio_days"), suffix=" Days", decimals=1)
            dso_str = _fmt_val(metrics.get("dso_days"), suffix=" Days", decimals=1)
            dpo_str = _fmt_val(metrics.get("dpo_days"), suffix=" Days", decimals=1)
            ccc_str = _fmt_val(metrics.get("ccc_days"), suffix=" Days", decimals=1)
            lines.extend([
                "[WORKING_CAPITAL_AND_CASH_CONVERSION_CYCLE]",
                f"Days Inventory Outstanding (DIO): {dio_str}",
                f"Days Sales Outstanding (DSO): {dso_str}",
                f"Days Payable Outstanding (DPO): {dpo_str}",
                f"Cash Conversion Cycle (CCC = DIO + DSO - DPO): {ccc_str}",
                ""
            ])
        else:
            lines.extend([
                "[WORKING_CAPITAL_AND_CASH_CONVERSION_CYCLE]",
                "Working Capital Days & CCC: Strictly N/A (Lending Institution)",
                ""
            ])

        lines.extend([
            "[EARNINGS_QUALITY_AND_CASH_FLOW]",
            f"5-Year Cumulative Operating Cash Flow (CFO): {cfo_5y_str}",
            f"5-Year Cumulative Net Profit (PAT): {pat_5y_str}",
            f"5-Year CFO to PAT Cash Conversion Ratio: {cfo_pat_str}",
            f"Earnings Quality Assessment: {eq_verdict}",
            "",
            "[SOLVENCY_AND_BALANCE_SHEET_DURABILITY]",
            f"Total Debt: {tot_debt_str}",
            f"Cash & Liquid Equivalents: {cash_str}",
            f"Net Debt: {net_debt_desc}",
            f"Net Debt to EBITDA: {nd_ebitda_str}" if not is_bfsi else "Net Debt to EBITDA: N/A (Bank/NBFC)",
            f"Interest Coverage Ratio (EBIT / Interest): {icr_str}",
            f"Debt to Equity Ratio: {de_str}",
            f"Promoter Pledge Percentage: {pledge_str}",
            f"Promoter Shareholding: {promoter_str}",
            f"Institutional Shareholding (FII + DII): {institutions_str}",
            "",
            "[CAPITAL_EFFICIENCY_AND_RETURNS]",
            f"Return on Capital Employed (ROCE): {roce_str}",
            f"Return on Invested Capital (ROIC): {roic_str}",
            f"Return on Equity (ROE): {roe_str}",
            f"Return on Assets (ROA): {roa_str}",
            f"Operating Gross Margin: {gm_str}" if not is_bfsi else "Operating Gross Margin: N/A (BFSI)",
            f"Operating EBITDA Margin: {ebitda_m_str}" if not is_bfsi else "Operating EBITDA Margin: N/A (BFSI)",
            ""
        ])

        if is_bfsi:
            nim_str = _fmt_val(metrics.get("nim_pct"), suffix="%")
            casa_str = _fmt_val(metrics.get("casa_pct"), suffix="%")
            gnpa_str = _fmt_val(metrics.get("gnpa_pct"), suffix="%")
            nnpa_str = _fmt_val(metrics.get("nnpa_pct"), suffix="%")
            pcr_str = _fmt_val(metrics.get("pcr_pct"), suffix="%")
            crar_str = _fmt_val(metrics.get("crar_pct"), suffix="%")
            tier1_str = _fmt_val(metrics.get("tier1_cet1_pct"), suffix="%")
            cc_str = _fmt_val(metrics.get("credit_cost_pct"), suffix="%")
            c2i_str = _fmt_val(metrics.get("cost_to_income_pct"), suffix="%")
            lines.extend([
                "[BANKING_AND_NBFC_PRUDENTIAL_METRICS]",
                f"Net Interest Margin (NIM): {nim_str}",
                f"CASA Deposit Ratio: {casa_str}",
                f"Gross NPA Ratio: {gnpa_str}",
                f"Net NPA Ratio: {nnpa_str}",
                f"Provision Coverage Ratio (PCR): {pcr_str}",
                f"Total Capital Adequacy Ratio (CRAR): {crar_str}",
                f"Common Equity Tier-1 (CET-1) Headroom: {tier1_str}",
                f"Normalized Credit Costs: {cc_str}",
                f"Cost-to-Income Ratio: {c2i_str}",
                ""
            ])

        lines.append("</verified_financials>")
        return "\n".join(lines)
