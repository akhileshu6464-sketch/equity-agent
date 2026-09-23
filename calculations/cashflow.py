"""
Deterministic Cash Flow & Quality of Earnings Calculations
Covers CFO/PAT conversion, Free Cash Flow, FCF Yield, and Capex decomposition.
"""

from typing import Optional, List
from .models import CalculationResult


def cfo_to_pat(
    cfo: Optional[float],
    pat: Optional[float]
) -> CalculationResult:
    """
    Computes Cash Flow from Operations to PAT ratio (Cash Conversion).
    Formula: cfo / pat (displayed as e.g. 0.95x).
    """
    inputs = {"cfo": cfo, "pat": pat}
    formula = "cfo / pat"

    if cfo is None or pat is None:
        return CalculationResult(
            metric="CFO_TO_PAT",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    if pat <= 0:
        return CalculationResult(
            metric="CFO_TO_PAT",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE",
            notes="PAT is zero or negative; ratio is economically non-standard"
        )

    val = cfo / pat
    return CalculationResult(
        metric="CFO_TO_PAT",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="MULTIPLE"
    )


def free_cash_flow(
    cfo: Optional[float],
    capex: Optional[float]
) -> CalculationResult:
    """
    Computes Free Cash Flow (FCF).
    Formula: cfo - abs(capex)
    Normalizes Capex sign convention: Capex is treated as an outflow.
    """
    inputs = {"cfo": cfo, "capex": capex}
    formula = "cfo - abs(capex)"

    if cfo is None:
        return CalculationResult(
            metric="FREE_CASH_FLOW",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    effective_capex = abs(capex) if capex is not None else 0.0
    val = cfo - effective_capex

    return CalculationResult(
        metric="FREE_CASH_FLOW",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def fcf_yield(
    fcf: Optional[float],
    market_cap: Optional[float]
) -> CalculationResult:
    """
    Computes Free Cash Flow Yield %.
    Formula: (fcf / market_cap) * 100
    """
    inputs = {"fcf": fcf, "market_cap": market_cap}
    formula = "(fcf / market_cap) * 100"

    if fcf is None or market_cap is None or market_cap <= 0:
        return CalculationResult(
            metric="FCF_YIELD",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if market_cap is not None and market_cap <= 0 else "INSUFFICIENT_DATA"
        )

    val = (fcf / market_cap) * 100.0
    return CalculationResult(
        metric="FCF_YIELD",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def cash_flow_reconciliation(
    cfo_list: List[float],
    pat_list: List[float]
) -> CalculationResult:
    """
    Computes cumulative multi-year Cash Flow from Operations to PAT realization ratio.
    Formula: (sum(cfo_list) / sum(pat_list)) * 100
    """
    inputs = {"total_cfo": sum(cfo_list) if cfo_list else None, "total_pat": sum(pat_list) if pat_list else None}
    formula = "(sum(cfo_list) / sum(pat_list)) * 100"

    if not cfo_list or not pat_list:
        return CalculationResult(
            metric="CUMULATIVE_CASH_CONVERSION",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    tot_cfo = sum(cfo_list)
    tot_pat = sum(pat_list)

    if tot_pat <= 0:
        return CalculationResult(
            metric="CUMULATIVE_CASH_CONVERSION",
            value=None,
            formula=formula,
            inputs={"total_cfo": tot_cfo, "total_pat": tot_pat},
            status="NOT_APPLICABLE",
            notes="Cumulative PAT is zero or negative"
        )

    val = (tot_cfo / tot_pat) * 100.0
    return CalculationResult(
        metric="CUMULATIVE_CASH_CONVERSION",
        value=val,
        formula=formula,
        inputs={"total_cfo": tot_cfo, "total_pat": tot_pat},
        status="VALID",
        unit="PERCENT"
    )
