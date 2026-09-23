"""
Deterministic Growth Calculations
Covers YoY, QoQ, Multi-Year CAGR, and line-item growth rates.
Handles negative denominators and sign changes safely without arbitrary defaults.
"""

from typing import Optional, Dict, Any
import math
from .models import CalculationResult


def revenue_growth(
    current_revenue: Optional[float],
    previous_revenue: Optional[float]
) -> CalculationResult:
    """
    Computes percentage Revenue Growth YoY or QoQ.
    Formula: ((current_revenue - previous_revenue) / abs(previous_revenue)) * 100
    """
    inputs = {"current_revenue": current_revenue, "previous_revenue": previous_revenue}
    formula = "((current_revenue - previous_revenue) / abs(previous_revenue)) * 100"

    if current_revenue is None or previous_revenue is None or previous_revenue == 0:
        return CalculationResult(
            metric="REVENUE_GROWTH",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if previous_revenue == 0 else "INSUFFICIENT_DATA",
            notes="Zero denominator" if previous_revenue == 0 else "Missing input values"
        )

    val = ((current_revenue - previous_revenue) / abs(previous_revenue)) * 100.0
    return CalculationResult(
        metric="REVENUE_GROWTH",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID"
    )


def yoy_change(
    current: Optional[float],
    previous: Optional[float],
    metric_name: str = "YOY_CHANGE"
) -> CalculationResult:
    """
    General year-over-year percentage change.
    Formula: ((current - previous) / abs(previous)) * 100
    """
    inputs = {"current": current, "previous": previous}
    formula = "((current - previous) / abs(previous)) * 100"

    if current is None or previous is None or previous == 0:
        return CalculationResult(
            metric=metric_name,
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if previous == 0 else "INSUFFICIENT_DATA",
            notes="Zero or missing previous value"
        )

    val = ((current - previous) / abs(previous)) * 100.0
    return CalculationResult(
        metric=metric_name,
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID"
    )


def qoq_change(
    current: Optional[float],
    previous: Optional[float],
    metric_name: str = "QOQ_CHANGE"
) -> CalculationResult:
    """
    Quarter-over-quarter percentage change across comparable quarters.
    Formula: ((current - previous) / abs(previous)) * 100
    """
    return yoy_change(current, previous, metric_name=metric_name)


def cagr(
    beginning_value: Optional[float],
    ending_value: Optional[float],
    years: float = 1.0,
    metric_name: str = "CAGR"
) -> CalculationResult:
    """
    Computes Compounded Annual Growth Rate (CAGR).
    Formula: ((ending_value / beginning_value) ** (1 / years) - 1) * 100
    Rule: Never force CAGR on negative or zero base values; returns NOT_APPLICABLE.
    """
    inputs = {"beginning_value": beginning_value, "ending_value": ending_value, "years": years}
    formula = "((ending_value / beginning_value) ** (1 / years) - 1) * 100"

    if beginning_value is None or ending_value is None or years is None:
        return CalculationResult(
            metric=metric_name,
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if beginning_value <= 0 or ending_value < 0 or years <= 0:
        return CalculationResult(
            metric=metric_name,
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="CAGR is not mathematically meaningful for negative or zero starting values"
        )

    try:
        val = ((ending_value / beginning_value) ** (1.0 / float(years)) - 1.0) * 100.0
        return CalculationResult(
            metric=metric_name,
            value=val,
            formula=formula,
            inputs=inputs,
            status="VALID"
        )
    except (ValueError, ZeroDivisionError, OverflowError):
        return CalculationResult(
            metric=metric_name,
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE"
        )



def inventory_growth(
    current_inventory: Optional[float],
    previous_inventory: Optional[float]
) -> CalculationResult:
    """Computes YoY growth in inventory."""
    return yoy_change(current_inventory, previous_inventory, metric_name="INVENTORY_GROWTH")


def receivable_growth(
    current_receivables: Optional[float],
    previous_receivables: Optional[float]
) -> CalculationResult:
    """Computes YoY growth in trade receivables."""
    return yoy_change(current_receivables, previous_receivables, metric_name="RECEIVABLE_GROWTH")


def cfo_growth(
    current_cfo: Optional[float],
    previous_cfo: Optional[float]
) -> CalculationResult:
    """
    Computes Operating Cash Flow growth, explicitly detecting and handling sign changes.
    (Section 38 & 55: Never present misleading 200% growth on negative to positive transition).
    """
    inputs = {"current_cfo": current_cfo, "previous_cfo": previous_cfo}
    formula = "((current_cfo - previous_cfo) / abs(previous_cfo)) * 100"

    if current_cfo is None or previous_cfo is None:
        return CalculationResult(
            metric="CFO_GROWTH",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if previous_cfo == 0:
        return CalculationResult(
            metric="CFO_GROWTH",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="Previous CFO was zero"
        )

    # Detect sign change
    if previous_cfo < 0 and current_cfo >= 0:
        notes = f"Turnaround to positive cash generation (from {previous_cfo:,.0f} to +{current_cfo:,.0f})"
        val = ((current_cfo - previous_cfo) / abs(previous_cfo)) * 100.0
        return CalculationResult(
            metric="CFO_GROWTH",
            value=val,
            formula=formula,
            inputs=inputs,
            status="VALID",
            notes=notes
        )
    elif previous_cfo > 0 and current_cfo < 0:
        notes = f"Deterioration to negative cash generation (from +{previous_cfo:,.0f} to {current_cfo:,.0f})"
        val = ((current_cfo - previous_cfo) / abs(previous_cfo)) * 100.0
        return CalculationResult(
            metric="CFO_GROWTH",
            value=val,
            formula=formula,
            inputs=inputs,
            status="VALID",
            notes=notes
        )

    val = ((current_cfo - previous_cfo) / abs(previous_cfo)) * 100.0
    return CalculationResult(
        metric="CFO_GROWTH",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID"
    )
