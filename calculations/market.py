"""
Deterministic Market Performance & Price Calculations
Covers Stock Return, Relative Performance, Drawdown, and Dividend Yield.
"""

from typing import Optional
from .models import CalculationResult


def market_return(
    current_price: Optional[float],
    previous_price: Optional[float]
) -> CalculationResult:
    """
    Computes Stock Return %.
    Formula: ((current_price - previous_price) / previous_price) * 100
    """
    inputs = {"current_price": current_price, "previous_price": previous_price}
    formula = "((current_price - previous_price) / previous_price) * 100"

    if current_price is None or previous_price is None or previous_price <= 0:
        return CalculationResult(
            metric="MARKET_RETURN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = ((current_price - previous_price) / previous_price) * 100.0
    return CalculationResult(
        metric="MARKET_RETURN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def relative_performance(
    company_return: Optional[float],
    benchmark_return: Optional[float]
) -> CalculationResult:
    """
    Computes Relative Return over Benchmark index.
    Formula: company_return - benchmark_return
    """
    inputs = {"company_return": company_return, "benchmark_return": benchmark_return}
    formula = "company_return - benchmark_return"

    if company_return is None or benchmark_return is None:
        return CalculationResult(
            metric="RELATIVE_PERFORMANCE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = company_return - benchmark_return
    return CalculationResult(
        metric="RELATIVE_PERFORMANCE",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def drawdown(
    current_price: Optional[float],
    previous_peak: Optional[float]
) -> CalculationResult:
    """
    Computes Drawdown from 52-week or historical peak.
    Formula: ((current_price - previous_peak) / previous_peak) * 100
    """
    inputs = {"current_price": current_price, "previous_peak": previous_peak}
    formula = "((current_price - previous_peak) / previous_peak) * 100"

    if current_price is None or previous_peak is None or previous_peak <= 0:
        return CalculationResult(
            metric="DRAWDOWN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = ((current_price - previous_peak) / previous_peak) * 100.0
    return CalculationResult(
        metric="DRAWDOWN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def dividend_yield(
    dividend_per_share: Optional[float],
    current_price: Optional[float]
) -> CalculationResult:
    """
    Computes Dividend Yield %.
    Formula: (dividend_per_share / current_price) * 100
    """
    inputs = {"dividend_per_share": dividend_per_share, "current_price": current_price}
    formula = "(dividend_per_share / current_price) * 100"

    if dividend_per_share is None or current_price is None or current_price <= 0:
        return CalculationResult(
            metric="DIVIDEND_YIELD",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if current_price is not None and current_price <= 0 else "INSUFFICIENT_DATA"
        )

    val = (dividend_per_share / current_price) * 100.0
    return CalculationResult(
        metric="DIVIDEND_YIELD",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )
