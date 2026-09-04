"""
DCF & Reverse DCF Calculator for Equity Valuation
Implements institutional reverse discounted cash flow modeling and sensitivity matrix generation.
"""

from typing import Dict, List, Any, Optional
import numpy as np


def dcf_enterprise_value(
    base_fcf: float,
    growth_rate: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int = 10,
    fade_years: int = 5
) -> float:
    """
    Computes enterprise value given an explicit forecast growth rate and terminal growth.
    Uses a 2-stage or 3-stage fade DCF model.
    """
    if wacc <= terminal_growth:
        # Avoid division by zero or negative denominator
        wacc = terminal_growth + 0.005

    pv_cash_flows = 0.0
    fcf = base_fcf

    # Explicit stage (forecast_years)
    for year in range(1, forecast_years + 1):
        fcf *= (1.0 + growth_rate)
        discount_factor = (1.0 + wacc) ** year
        pv_cash_flows += fcf / discount_factor

    # Terminal value
    terminal_fcf = fcf * (1.0 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1.0 + wacc) ** forecast_years)

    return pv_cash_flows + pv_terminal_value


def dcf_share_price(
    enterprise_value: float,
    net_debt: float,
    shares_outstanding: float
) -> float:
    """
    Calculates equity value per share = (Enterprise Value - Net Debt) / Shares.
    Net Debt = Total Debt - Cash & Liquid Equivalents.
    """
    if shares_outstanding <= 0:
        return 0.0
    equity_value = enterprise_value - net_debt
    return max(0.0, equity_value / shares_outstanding)


def solve_implied_growth(
    target_market_cap: float,
    base_fcf: float,
    net_debt: float,
    wacc: float = 0.12,
    terminal_growth: float = 0.05,
    forecast_years: int = 10
) -> float:
    """
    Solves for the implied FCF growth rate embedded in current market cap via binary search.
    Enterprise Value = target_market_cap + net_debt.
    """
    target_ev = target_market_cap + net_debt
    if base_fcf <= 0:
        # If company has negative current FCF, implied growth on negative base is undefined
        return 0.0

    # Binary search bounds: -50% to +100% CAGR
    low = -0.50
    high = 1.00
    best_g = 0.0
    tolerance = 1000.0  # ₹1000 target EV tolerance

    for _ in range(100):
        mid = (low + high) / 2.0
        ev_estimate = dcf_enterprise_value(base_fcf, mid, wacc, terminal_growth, forecast_years)
        
        diff = ev_estimate - target_ev
        if abs(diff) < tolerance:
            return round(mid * 100, 2)

        if ev_estimate < target_ev:
            low = mid
        else:
            high = mid
        best_g = mid

    return round(best_g * 100, 2)


def generate_dcf_sensitivity_matrix(
    base_fcf: float,
    net_debt: float,
    shares_outstanding: float,
    assumed_growth: float = 0.12,
    wacc_range: Optional[List[float]] = None,
    terminal_growth_range: Optional[List[float]] = None,
    forecast_years: int = 10
) -> Dict[str, Any]:
    """
    Generates a 2D sensitivity table of fair values per share across varying WACC and Terminal Growth.
    """
    if wacc_range is None:
        wacc_range = [0.10, 0.11, 0.12, 0.13, 0.14]
    if terminal_growth_range is None:
        terminal_growth_range = [0.040, 0.045, 0.050, 0.055, 0.060]

    matrix: List[List[float]] = []
    
    for tg in terminal_growth_range:
        row: List[float] = []
        for w in wacc_range:
            if w <= tg:
                row.append(0.0)
                continue
            ev = dcf_enterprise_value(base_fcf, assumed_growth, w, tg, forecast_years)
            price = dcf_share_price(ev, net_debt, shares_outstanding)
            row.append(round(price, 2))
        matrix.append(row)

    return {
        "wacc_labels": [f"{round(w * 100, 1)}%" for w in wacc_range],
        "terminal_growth_labels": [f"{round(tg * 100, 1)}%" for tg in terminal_growth_range],
        "matrix": matrix,
        "assumed_growth_pct": round(assumed_growth * 100, 1)
    }


def calculate_reverse_dcf(
    current_price: float,
    shares_outstanding: float,
    base_fcf: float,
    net_debt: float,
    wacc: float = 0.12,
    terminal_growth: float = 0.05,
    conservative_growth: float = 0.08,
    base_growth: float = 0.12,
    bull_growth: float = 0.16,
    forecast_years: int = 10
) -> Dict[str, Any]:
    """
    Full Reverse DCF and valuation scenario suite.
    """
    market_cap = current_price * shares_outstanding
    
    # Check normalized base FCF
    is_fcf_normalized = False
    if base_fcf <= 0:
        # Fallback estimation: 4% of market cap as normalized proxy FCF if TTM FCF is depressed/negative
        base_fcf = max(100.0, market_cap * 0.03)
        is_fcf_normalized = True

    implied_growth_pct = solve_implied_growth(
        target_market_cap=market_cap,
        base_fcf=base_fcf,
        net_debt=net_debt,
        wacc=wacc,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years
    )

    # Scenarios fair value
    ev_conservative = dcf_enterprise_value(base_fcf, conservative_growth, wacc, terminal_growth, forecast_years)
    price_conservative = dcf_share_price(ev_conservative, net_debt, shares_outstanding)

    ev_base = dcf_enterprise_value(base_fcf, base_growth, wacc, terminal_growth, forecast_years)
    price_base = dcf_share_price(ev_base, net_debt, shares_outstanding)

    ev_bull = dcf_enterprise_value(base_fcf, bull_growth, wacc, terminal_growth, forecast_years)
    price_bull = dcf_share_price(ev_bull, net_debt, shares_outstanding)

    # Margin of Safety relative to Base Case Fair Value
    if price_base > 0:
        margin_of_safety_pct = round(((price_base - current_price) / price_base) * 100, 1)
    else:
        margin_of_safety_pct = 0.0

    # Sensitivity Matrix around base growth
    sensitivity = generate_dcf_sensitivity_matrix(
        base_fcf=base_fcf,
        net_debt=net_debt,
        shares_outstanding=shares_outstanding,
        assumed_growth=base_growth,
        forecast_years=forecast_years
    )

    return {
        "current_price": round(current_price, 2),
        "market_cap_cr": round(market_cap / 1e7, 2),  # in Crores
        "base_fcf_cr": round(base_fcf / 1e7, 2),
        "net_debt_cr": round(net_debt / 1e7, 2),
        "is_fcf_normalized": is_fcf_normalized,
        "implied_growth_cagr_pct": implied_growth_pct,
        "wacc_used_pct": round(wacc * 100, 1),
        "terminal_growth_used_pct": round(terminal_growth * 100, 1),
        "fair_values": {
            "conservative": {
                "growth_rate_pct": round(conservative_growth * 100, 1),
                "fair_price": round(price_conservative, 2),
                "upside_pct": round(((price_conservative - current_price) / current_price) * 100, 1) if current_price else 0
            },
            "base": {
                "growth_rate_pct": round(base_growth * 100, 1),
                "fair_price": round(price_base, 2),
                "upside_pct": round(((price_base - current_price) / current_price) * 100, 1) if current_price else 0
            },
            "bull": {
                "growth_rate_pct": round(bull_growth * 100, 1),
                "fair_price": round(price_bull, 2),
                "upside_pct": round(((price_bull - current_price) / current_price) * 100, 1) if current_price else 0
            }
        },
        "margin_of_safety_pct": margin_of_safety_pct,
        "sensitivity_matrix": sensitivity
    }
