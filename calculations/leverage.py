"""
Deterministic Leverage and Solvency Calculations
Covers Debt-to-Equity, Net Debt, Net Debt to EBITDA, and Interest Coverage.
Strictly returns None for invalid or negative denominators (never arbitrary constants).
"""

from typing import Optional
from .models import CalculationResult


def debt_to_equity(
    total_debt: Optional[float],
    shareholders_equity: Optional[float]
) -> CalculationResult:
    """
    Computes Debt-to-Equity ratio.
    Formula: total_debt / shareholders_equity
    """
    inputs = {"total_debt": total_debt, "shareholders_equity": shareholders_equity}
    formula = "total_debt / shareholders_equity"

    if total_debt is None or shareholders_equity is None:
        return CalculationResult(
            metric="DEBT_TO_EQUITY",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if shareholders_equity <= 0:
        return CalculationResult(
            metric="DEBT_TO_EQUITY",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="Shareholders' equity is zero or negative"
        )

    val = total_debt / shareholders_equity
    return CalculationResult(
        metric="DEBT_TO_EQUITY",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="RATIO"
    )


def net_debt(
    total_debt: Optional[float],
    cash_and_equivalents: Optional[float]
) -> CalculationResult:
    """
    Computes Net Debt.
    Formula: total_debt - cash_and_equivalents
    """
    inputs = {"total_debt": total_debt, "cash_and_equivalents": cash_and_equivalents}
    formula = "total_debt - cash_and_equivalents"

    if total_debt is None or cash_and_equivalents is None:
        return CalculationResult(
            metric="NET_DEBT",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = total_debt - cash_and_equivalents
    return CalculationResult(
        metric="NET_DEBT",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def net_debt_to_ebitda(
    net_debt_val: Optional[float],
    ebitda: Optional[float]
) -> CalculationResult:
    """
    Computes Net Debt to EBITDA ratio.
    Formula: net_debt / ebitda
    Rule: If EBITDA <= 0, returns None (never arbitrary fallback like 5.0).
    """
    inputs = {"net_debt": net_debt_val, "ebitda": ebitda}
    formula = "net_debt / ebitda"

    if net_debt_val is None or ebitda is None:
        return CalculationResult(
            metric="NET_DEBT_TO_EBITDA",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if ebitda <= 0:
        return CalculationResult(
            metric="NET_DEBT_TO_EBITDA",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="EBITDA is zero or negative; ratio is non-standard"
        )

    val = net_debt_val / ebitda
    return CalculationResult(
        metric="NET_DEBT_TO_EBITDA",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="RATIO"
    )


def interest_coverage(
    ebit: Optional[float],
    interest_expense: Optional[float]
) -> CalculationResult:
    """
    Computes Interest Coverage Ratio.
    Formula: ebit / interest_expense
    Rule: If interest_expense <= 0, returns None / NOT_APPLICABLE (never arbitrary fallback like 50.0).
    """
    inputs = {"ebit": ebit, "interest_expense": interest_expense}
    formula = "ebit / interest_expense"

    if ebit is None or interest_expense is None:
        return CalculationResult(
            metric="INTEREST_COVERAGE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if interest_expense <= 0:
        return CalculationResult(
            metric="INTEREST_COVERAGE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="Company has zero or negative interest expense (debt-free or net interest earner)"
        )

    val = ebit / interest_expense
    return CalculationResult(
        metric="INTEREST_COVERAGE",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="RATIO"
    )
