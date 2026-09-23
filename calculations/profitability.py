"""
Deterministic Profitability and Return Ratios
Covers ROE, ROCE, ROIC, and Asset Turnover with explicit average balance-sheet accounting.
"""

from typing import Optional
from .models import CalculationResult


def roe(
    pat: Optional[float],
    beginning_equity: Optional[float],
    ending_equity: Optional[float]
) -> CalculationResult:
    """
    Computes Return on Equity (ROE) using average shareholders' equity.
    Formula: (pat / ((beginning_equity + ending_equity) / 2)) * 100
    """
    inputs = {
        "pat": pat,
        "beginning_equity": beginning_equity,
        "ending_equity": ending_equity
    }
    formula = "(pat / ((beginning_equity + ending_equity) / 2)) * 100"

    if pat is None or ending_equity is None:
        return CalculationResult(
            metric="ROE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    # If beginning equity not available, fall back to ending equity with documentation
    if beginning_equity is None:
        avg_equity = ending_equity
        formula_used = "(pat / ending_equity) * 100"
        notes = "Calculated using ending equity (beginning equity unavailable)"
    else:
        avg_equity = (beginning_equity + ending_equity) / 2.0
        formula_used = formula
        notes = "Calculated using average equity"

    if avg_equity == 0:
        return CalculationResult(
            metric="ROE",
            value=None,
            formula=formula_used,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="Zero average equity"
        )

    val = (pat / avg_equity) * 100.0
    return CalculationResult(
        metric="ROE",
        value=val,
        formula=formula_used,
        inputs=inputs,
        status="VALID",
        unit="PERCENT",
        notes=notes
    )


def roce(
    ebit: Optional[float],
    beginning_capital_employed: Optional[float],
    ending_capital_employed: Optional[float]
) -> CalculationResult:
    """
    Computes Return on Capital Employed (ROCE) using average capital employed.
    Capital Employed Definition: Total Assets - Current Liabilities (or Net Worth + Total Debt - Cash).
    Formula: (ebit / ((beginning_ce + ending_ce) / 2)) * 100
    """
    inputs = {
        "ebit": ebit,
        "beginning_capital_employed": beginning_capital_employed,
        "ending_capital_employed": ending_capital_employed
    }
    formula = "(ebit / ((beginning_ce + ending_ce) / 2)) * 100"

    if ebit is None or ending_capital_employed is None:
        return CalculationResult(
            metric="ROCE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if beginning_capital_employed is None:
        avg_ce = ending_capital_employed
        formula_used = "(ebit / ending_ce) * 100"
        notes = "Calculated using ending capital employed"
    else:
        avg_ce = (beginning_capital_employed + ending_capital_employed) / 2.0
        formula_used = formula
        notes = "Calculated using average capital employed"

    if avg_ce <= 0:
        return CalculationResult(
            metric="ROCE",
            value=None,
            formula=formula_used,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="Capital employed is zero or negative"
        )

    val = (ebit / avg_ce) * 100.0
    return CalculationResult(
        metric="ROCE",
        value=val,
        formula=formula_used,
        inputs=inputs,
        status="VALID",
        unit="PERCENT",
        notes=notes
    )


def roic(
    nopat: Optional[float],
    invested_capital: Optional[float]
) -> CalculationResult:
    """
    Computes Return on Invested Capital (ROIC).
    Formula: (nopat / invested_capital) * 100
    """
    inputs = {"nopat": nopat, "invested_capital": invested_capital}
    formula = "(nopat / invested_capital) * 100"

    if nopat is None or invested_capital is None or invested_capital <= 0:
        return CalculationResult(
            metric="ROIC",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if invested_capital is not None and invested_capital <= 0 else "INSUFFICIENT_DATA"
        )

    val = (nopat / invested_capital) * 100.0
    return CalculationResult(
        metric="ROIC",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def asset_turnover(
    revenue: Optional[float],
    avg_total_assets: Optional[float]
) -> CalculationResult:
    """
    Computes Total Asset Turnover ratio.
    Formula: revenue / avg_total_assets
    """
    inputs = {"revenue": revenue, "avg_total_assets": avg_total_assets}
    formula = "revenue / avg_total_assets"

    if revenue is None or avg_total_assets is None or avg_total_assets <= 0:
        return CalculationResult(
            metric="ASSET_TURNOVER",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if avg_total_assets is not None and avg_total_assets <= 0 else "INSUFFICIENT_DATA"
        )

    val = revenue / avg_total_assets
    return CalculationResult(
        metric="ASSET_TURNOVER",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="RATIO"
    )
