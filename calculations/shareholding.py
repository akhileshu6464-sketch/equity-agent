"""
Deterministic Shareholding & Governance Calculations
Covers Promoter Holding shifts (absolute bps/pp vs relative %) and Promoter Pledge.
"""

from typing import Optional, Dict, Any
from .models import CalculationResult


def promoter_holding_change(
    current_pct: Optional[float],
    previous_pct: Optional[float]
) -> CalculationResult:
    """
    Computes absolute percentage-point change and relative change in promoter holding.
    (Section 50: Clearly distinguishes -1 percentage point from relative change).
    """
    inputs = {"current_promoter_pct": current_pct, "previous_promoter_pct": previous_pct}
    formula = "current_pct - previous_pct"

    if current_pct is None or previous_pct is None:
        return CalculationResult(
            metric="PROMOTER_HOLDING_CHANGE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    abs_change_pp = current_pct - previous_pct
    rel_change_pct = ((current_pct - previous_pct) / previous_pct) * 100.0 if previous_pct > 0 else 0.0

    notes = f"Absolute change: {abs_change_pp:+.2f} percentage points ({abs_change_pp * 100:+.0f} bps); Relative change: {rel_change_pct:+.2f}%"

    return CalculationResult(
        metric="PROMOTER_HOLDING_CHANGE",
        value=abs_change_pp,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENTAGE_POINTS",
        notes=notes
    )


def promoter_pledge_percentage(
    pledged_shares: Optional[float],
    total_promoter_shares: Optional[float]
) -> CalculationResult:
    """
    Computes Promoter Pledge %.
    Formula: (pledged_shares / total_promoter_shares) * 100
    """
    inputs = {"pledged_shares": pledged_shares, "total_promoter_shares": total_promoter_shares}
    formula = "(pledged_shares / total_promoter_shares) * 100"

    if pledged_shares is None or total_promoter_shares is None:
        return CalculationResult(
            metric="PROMOTER_PLEDGE_PERCENTAGE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if total_promoter_shares <= 0:
        return CalculationResult(
            metric="PROMOTER_PLEDGE_PERCENTAGE",
            value=0.0,
            formula=formula,
            inputs=inputs,
            status="VALID",
            unit="PERCENT",
            notes="Total promoter shares is zero"
        )

    val = (pledged_shares / total_promoter_shares) * 100.0
    return CalculationResult(
        metric="PROMOTER_PLEDGE_PERCENTAGE",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )
