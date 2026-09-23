"""
Calculation Validation & Reconciliation Cross-Check Module
Enforces mathematical validity, detects sign changes, reconciles reported vs calculated figures,
and validates company, period, and statement scope integrity.
"""

from typing import Optional, Dict, Any, Tuple
import math
from .models import CalculationResult, CalculationAuditRecord


def validate_calculation(result: CalculationResult) -> Tuple[bool, str]:
    """
    Validates mathematical sanity of a CalculationResult.
    Checks for NaN, Infinite, and extreme mathematical bounds.
    Distinguishes mathematically invalid from economically unusual.
    """
    if result.value is None:
        return True, "None value (legitimate data absence or not applicable)"

    if math.isnan(result.value):
        return False, "Mathematically invalid: NaN encountered"

    if math.isinf(result.value):
        return False, "Mathematically invalid: Infinite value encountered"

    # Economic range checks (non-blocking warning, flags unusual economic conditions)
    if result.metric in ["EBITDA_MARGIN", "EBIT_MARGIN", "PAT_MARGIN", "GROSS_MARGIN"]:
        if result.value > 100.0:
            return True, f"Economically unusual: Margin {result.value:.1f}% exceeds 100%"
        if result.value < -100.0:
            return True, f"Economically unusual: Margin {result.value:.1f}% is deeply negative"

    if result.metric == "PE_RATIO" and result.value < 0:
        return False, "Mathematically invalid: Negative P/E generated"

    return True, "VALID"


def reconcile_reported_vs_calculated(
    reported: Optional[float],
    calculated: Optional[float],
    tolerance_pct: float = 2.0,
    metric_name: str = "METRIC"
) -> Dict[str, Any]:
    """
    Section 62: Cross-check engine between reported and calculated metrics.
    Compares reported value against calculated value and flags discrepancies exceeding tolerance.
    """
    if reported is None and calculated is None:
        return {
            "status": "UNAVAILABLE",
            "difference_pct": None,
            "reconciliation_required": False,
            "message": "Both reported and calculated values are unavailable"
        }

    if reported is None:
        return {
            "status": "CALCULATED_ONLY",
            "reported": None,
            "calculated": calculated,
            "difference_pct": None,
            "reconciliation_required": False,
            "message": f"Only calculated {metric_name} is available"
        }

    if calculated is None:
        return {
            "status": "REPORTED_ONLY",
            "reported": reported,
            "calculated": None,
            "difference_pct": None,
            "reconciliation_required": False,
            "message": f"Only reported {metric_name} is available"
        }

    if reported == 0:
        diff_pct = abs(calculated) * 100.0 if calculated != 0 else 0.0
    else:
        diff_pct = (abs(reported - calculated) / abs(reported)) * 100.0

    needs_reconciliation = diff_pct > tolerance_pct
    message = (
        f"CALCULATION RECONCILIATION REQUIRED: {metric_name} reported ({reported:,.2f}) "
        f"differs from calculated ({calculated:,.2f}) by {diff_pct:.2f}% (tolerance {tolerance_pct}%)"
        if needs_reconciliation
        else f"Reconciled: Difference {diff_pct:.2f}% is within acceptable tolerance"
    )

    return {
        "status": "RECONCILIATION_REQUIRED" if needs_reconciliation else "RECONCILED",
        "metric": metric_name,
        "reported": reported,
        "calculated": calculated,
        "difference_pct": round(diff_pct, 2),
        "reconciliation_required": needs_reconciliation,
        "message": message
    }


def detect_sign_change(
    current: Optional[float],
    previous: Optional[float],
    metric_name: str = "Metric"
) -> Dict[str, Any]:
    """
    Section 55: Sign-Change Rule.
    Identifies if a financial metric shifted from negative to positive or vice versa.
    Prevents presenting misleading percentage growth on sign changes.
    """
    if current is None or previous is None:
        return {
            "has_sign_change": False,
            "direction": "UNKNOWN",
            "description": "Insufficient data to determine trajectory"
        }

    if previous < 0 and current >= 0:
        return {
            "has_sign_change": True,
            "direction": "TURNAROUND_POSITIVE",
            "description": f"{metric_name} turnaround: improved from negative ({previous:,.1f}) to positive (+{current:,.1f})"
        }
    elif previous >= 0 and current < 0:
        return {
            "has_sign_change": True,
            "direction": "DETERIORATION_NEGATIVE",
            "description": f"{metric_name} deterioration: swung from positive (+{previous:,.1f}) to negative ({current:,.1f})"
        }
    else:
        return {
            "has_sign_change": False,
            "direction": "SAME_SIGN",
            "description": "Metric maintained consistent sign convention across periods"
        }
