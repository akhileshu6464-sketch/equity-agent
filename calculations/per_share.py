"""
Deterministic Per-Share Metrics
Covers EPS, Book Value Per Share (BVPS), Dividend Payout, and Share Dilution.
"""

from typing import Optional
from .models import CalculationResult


def eps(
    pat_attributable: Optional[float],
    weighted_shares: Optional[float]
) -> CalculationResult:
    """
    Computes Basic Earnings Per Share (EPS).
    Formula: pat_attributable / weighted_shares
    """
    inputs = {"pat_attributable": pat_attributable, "weighted_shares": weighted_shares}
    formula = "pat_attributable / weighted_shares"

    if pat_attributable is None or weighted_shares is None or weighted_shares <= 0:
        return CalculationResult(
            metric="EPS",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = pat_attributable / weighted_shares
    return CalculationResult(
        metric="EPS",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def book_value_per_share(
    equity_attributable: Optional[float],
    shares_outstanding: Optional[float]
) -> CalculationResult:
    """
    Computes Book Value Per Share (BVPS).
    Formula: equity_attributable / shares_outstanding
    """
    inputs = {"equity_attributable": equity_attributable, "shares_outstanding": shares_outstanding}
    formula = "equity_attributable / shares_outstanding"

    if equity_attributable is None or shares_outstanding is None or shares_outstanding <= 0:
        return CalculationResult(
            metric="BOOK_VALUE_PER_SHARE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = equity_attributable / shares_outstanding
    return CalculationResult(
        metric="BOOK_VALUE_PER_SHARE",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def dividend_payout(
    dps: Optional[float] = None,
    eps_val: Optional[float] = None,
    total_dividends: Optional[float] = None,
    pat: Optional[float] = None
) -> CalculationResult:
    """
    Computes Dividend Payout %.
    Formula: (dps / eps) * 100 or (total_dividends / pat) * 100
    """
    if dps is not None and eps_val is not None and eps_val > 0:
        val = (dps / eps_val) * 100.0
        return CalculationResult(
            metric="DIVIDEND_PAYOUT",
            value=val,
            formula="(dps / eps) * 100",
            inputs={"dps": dps, "eps": eps_val},
            status="VALID",
            unit="PERCENT"
        )
    elif total_dividends is not None and pat is not None and pat > 0:
        val = (total_dividends / pat) * 100.0
        return CalculationResult(
            metric="DIVIDEND_PAYOUT",
            value=val,
            formula="(total_dividends / pat) * 100",
            inputs={"total_dividends": total_dividends, "pat": pat},
            status="VALID",
            unit="PERCENT"
        )
    else:
        return CalculationResult(
            metric="DIVIDEND_PAYOUT",
            value=None,
            formula="(dps / eps) * 100",
            inputs={"dps": dps, "eps": eps_val, "total_dividends": total_dividends, "pat": pat},
            status="NOT_APPLICABLE" if (eps_val is not None and eps_val <= 0) else "INSUFFICIENT_DATA",
            notes="EPS/PAT is negative or inputs missing"
        )


def share_dilution(
    current_shares: Optional[float],
    previous_shares: Optional[float]
) -> CalculationResult:
    """
    Computes percentage share dilution.
    Formula: ((current_shares - previous_shares) / previous_shares) * 100
    """
    inputs = {"current_shares": current_shares, "previous_shares": previous_shares}
    formula = "((current_shares - previous_shares) / previous_shares) * 100"

    if current_shares is None or previous_shares is None or previous_shares <= 0:
        return CalculationResult(
            metric="SHARE_DILUTION",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = ((current_shares - previous_shares) / previous_shares) * 100.0
    return CalculationResult(
        metric="SHARE_DILUTION",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )
