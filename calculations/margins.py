"""
Deterministic Margin Calculations & Basis-Point Shifts
Covers Gross Margin, EBITDA Margin, EBIT Margin, PAT Margin, and bps shifts.
"""

from typing import Optional
from .models import CalculationResult


def ebitda_margin(
    ebitda: Optional[float],
    revenue: Optional[float]
) -> CalculationResult:
    """
    Computes EBITDA Margin %.
    Formula: (ebitda / revenue) * 100
    """
    inputs = {"ebitda": ebitda, "revenue": revenue}
    formula = "(ebitda / revenue) * 100"

    if ebitda is None or revenue is None or revenue <= 0:
        return CalculationResult(
            metric="EBITDA_MARGIN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if revenue == 0 else "INSUFFICIENT_DATA",
            notes="Revenue is zero or negative" if (revenue is not None and revenue <= 0) else "Missing inputs"
        )

    val = (ebitda / revenue) * 100.0
    return CalculationResult(
        metric="EBITDA_MARGIN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def ebit_margin(
    ebit: Optional[float],
    revenue: Optional[float]
) -> CalculationResult:
    """
    Computes EBIT (Operating) Margin %.
    Formula: (ebit / revenue) * 100
    """
    inputs = {"ebit": ebit, "revenue": revenue}
    formula = "(ebit / revenue) * 100"

    if ebit is None or revenue is None or revenue <= 0:
        return CalculationResult(
            metric="EBIT_MARGIN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if revenue == 0 else "INSUFFICIENT_DATA"
        )

    val = (ebit / revenue) * 100.0
    return CalculationResult(
        metric="EBIT_MARGIN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def pat_margin(
    pat: Optional[float],
    revenue: Optional[float]
) -> CalculationResult:
    """
    Computes Net Profit (PAT) Margin %.
    Formula: (pat / revenue) * 100
    """
    inputs = {"pat": pat, "revenue": revenue}
    formula = "(pat / revenue) * 100"

    if pat is None or revenue is None or revenue <= 0:
        return CalculationResult(
            metric="PAT_MARGIN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if revenue == 0 else "INSUFFICIENT_DATA"
        )

    val = (pat / revenue) * 100.0
    return CalculationResult(
        metric="PAT_MARGIN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def gross_margin(
    revenue: Optional[float],
    cogs: Optional[float] = None,
    gross_profit: Optional[float] = None
) -> CalculationResult:
    """
    Computes Gross Margin %.
    Formula: (gross_profit / revenue) * 100 or ((revenue - cogs) / revenue) * 100
    """
    if gross_profit is None and revenue is not None and cogs is not None:
        gross_profit = revenue - cogs

    inputs = {"revenue": revenue, "cogs": cogs, "gross_profit": gross_profit}
    formula = "(gross_profit / revenue) * 100"

    if gross_profit is None or revenue is None or revenue <= 0:
        return CalculationResult(
            metric="GROSS_MARGIN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if revenue == 0 else "INSUFFICIENT_DATA"
        )

    val = (gross_profit / revenue) * 100.0
    return CalculationResult(
        metric="GROSS_MARGIN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def margin_change_bps(
    current_margin_pct: Optional[float],
    previous_margin_pct: Optional[float],
    metric_name: str = "MARGIN_CHANGE_BPS"
) -> CalculationResult:
    """
    Computes change in margin in basis points (1% = 100 bps).
    Formula: (current_margin_pct - previous_margin_pct) * 100
    Example: 22.5% -> 19.8% = -2.7% = -270 bps
    """
    inputs = {"current_margin_pct": current_margin_pct, "previous_margin_pct": previous_margin_pct}
    formula = "(current_margin_pct - previous_margin_pct) * 100"

    if current_margin_pct is None or previous_margin_pct is None:
        return CalculationResult(
            metric=metric_name,
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = (current_margin_pct - previous_margin_pct) * 100.0
    return CalculationResult(
        metric=metric_name,
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="BPS"
    )
