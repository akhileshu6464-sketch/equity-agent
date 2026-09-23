"""
Deterministic Valuation Multiples
Covers P/E, P/B, Market Cap, Enterprise Value (EV), EV/EBITDA, and EV/Sales.
Strictly returns None/NOT_APPLICABLE for negative or zero earnings/book value/EBITDA.
"""

from typing import Optional
from .models import CalculationResult


def pe_ratio(
    market_price: Optional[float],
    eps_val: Optional[float]
) -> CalculationResult:
    """
    Computes Price-to-Earnings (P/E) ratio.
    Formula: market_price / eps
    Rule: If EPS <= 0, returns None/NOT_APPLICABLE (never negative P/E).
    """
    inputs = {"market_price": market_price, "eps": eps_val}
    formula = "market_price / eps"

    if market_price is None or eps_val is None:
        return CalculationResult(
            metric="PE_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if eps_val <= 0:
        return CalculationResult(
            metric="PE_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="EPS is zero or negative; P/E ratio is not economically meaningful"
        )

    val = market_price / eps_val
    return CalculationResult(
        metric="PE_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="MULTIPLE"
    )


def pb_ratio(
    market_price: Optional[float],
    book_value_per_share_val: Optional[float]
) -> CalculationResult:
    """
    Computes Price-to-Book (P/B) ratio.
    Formula: market_price / book_value_per_share
    Rule: If BVPS <= 0, returns None/NOT_APPLICABLE.
    """
    inputs = {"market_price": market_price, "book_value_per_share": book_value_per_share_val}
    formula = "market_price / book_value_per_share"

    if market_price is None or book_value_per_share_val is None:
        return CalculationResult(
            metric="PB_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if book_value_per_share_val <= 0:
        return CalculationResult(
            metric="PB_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="Book value is zero or negative"
        )

    val = market_price / book_value_per_share_val
    return CalculationResult(
        metric="PB_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="MULTIPLE"
    )


def market_capitalization(
    share_price: Optional[float],
    shares_outstanding: Optional[float]
) -> CalculationResult:
    """
    Computes Market Capitalization.
    Formula: share_price * shares_outstanding
    """
    inputs = {"share_price": share_price, "shares_outstanding": shares_outstanding}
    formula = "share_price * shares_outstanding"

    if share_price is None or shares_outstanding is None or share_price <= 0 or shares_outstanding <= 0:
        return CalculationResult(
            metric="MARKET_CAP",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = share_price * shares_outstanding
    return CalculationResult(
        metric="MARKET_CAP",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def enterprise_value(
    market_cap: Optional[float],
    total_debt: Optional[float],
    cash_and_equivalents: Optional[float],
    preferred_equity: float = 0.0,
    minority_interest: float = 0.0
) -> CalculationResult:
    """
    Computes Enterprise Value (EV).
    Formula: market_cap + total_debt + preferred_equity + minority_interest - cash_and_equivalents
    """
    inputs = {
        "market_cap": market_cap,
        "total_debt": total_debt,
        "cash_and_equivalents": cash_and_equivalents,
        "preferred_equity": preferred_equity,
        "minority_interest": minority_interest
    }
    formula = "market_cap + total_debt + preferred_equity + minority_interest - cash_and_equivalents"

    if market_cap is None:
        return CalculationResult(
            metric="ENTERPRISE_VALUE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    tot_debt = total_debt if total_debt is not None else 0.0
    cash = cash_and_equivalents if cash_and_equivalents is not None else 0.0

    val = market_cap + tot_debt + preferred_equity + minority_interest - cash
    return CalculationResult(
        metric="ENTERPRISE_VALUE",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def ev_to_ebitda(
    ev: Optional[float],
    ebitda: Optional[float]
) -> CalculationResult:
    """
    Computes EV/EBITDA multiple.
    Formula: enterprise_value / ebitda
    Rule: If EBITDA <= 0, returns None/NOT_APPLICABLE.
    """
    inputs = {"enterprise_value": ev, "ebitda": ebitda}
    formula = "enterprise_value / ebitda"

    if ev is None or ebitda is None:
        return CalculationResult(
            metric="EV_TO_EBITDA",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if ebitda <= 0:
        return CalculationResult(
            metric="EV_TO_EBITDA",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="EBITDA is zero or negative"
        )

    val = ev / ebitda
    return CalculationResult(
        metric="EV_TO_EBITDA",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="MULTIPLE"
    )


def ev_to_sales(
    ev: Optional[float],
    revenue: Optional[float]
) -> CalculationResult:
    """
    Computes EV/Sales multiple.
    Formula: enterprise_value / revenue
    """
    inputs = {"enterprise_value": ev, "revenue": revenue}
    formula = "enterprise_value / revenue"

    if ev is None or revenue is None or revenue <= 0:
        return CalculationResult(
            metric="EV_TO_SALES",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if revenue is not None and revenue <= 0 else "INSUFFICIENT_DATA"
        )

    val = ev / revenue
    return CalculationResult(
        metric="EV_TO_SALES",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="MULTIPLE"
    )
