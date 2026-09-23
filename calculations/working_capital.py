"""
Deterministic Working Capital and Cash Conversion Cycle Calculations
Covers Net Working Capital, Receivable Days (DSO), Inventory Days (DIO),
Payable Days (DPO), and Cash Conversion Cycle (CCC).
Strictly separates COGS/Purchases from Revenue without silent substitutions.
"""

from typing import Optional
from .models import CalculationResult


def net_working_capital(
    current_assets: Optional[float],
    current_liabilities: Optional[float]
) -> CalculationResult:
    """
    Computes Net Working Capital (NWC).
    Formula: current_assets - current_liabilities
    """
    inputs = {"current_assets": current_assets, "current_liabilities": current_liabilities}
    formula = "current_assets - current_liabilities"

    if current_assets is None or current_liabilities is None:
        return CalculationResult(
            metric="NET_WORKING_CAPITAL",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA"
        )

    val = current_assets - current_liabilities
    return CalculationResult(
        metric="NET_WORKING_CAPITAL",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="INR"
    )


def receivable_days(
    receivables: Optional[float],
    revenue: Optional[float],
    days: float = 365.0
) -> CalculationResult:
    """
    Computes Days Sales Outstanding (DSO) / Receivable Days.
    Formula: (receivables / revenue) * days
    """
    inputs = {"receivables": receivables, "revenue": revenue, "days": days}
    formula = "(receivables / revenue) * days"

    if receivables is None or revenue is None or revenue <= 0:
        return CalculationResult(
            metric="RECEIVABLE_DAYS",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if revenue is not None and revenue <= 0 else "INSUFFICIENT_DATA"
        )

    val = (receivables / revenue) * days
    return CalculationResult(
        metric="RECEIVABLE_DAYS",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="DAYS"
    )


def inventory_days(
    inventory: Optional[float],
    cogs: Optional[float],
    days: float = 365.0
) -> CalculationResult:
    """
    Computes Days Inventory Outstanding (DIO) based on Cost of Goods Sold (COGS).
    Formula: (inventory / cogs) * days
    Rule: Never divide inventory by revenue. If COGS is missing, return INSUFFICIENT_DATA.
    """
    inputs = {"inventory": inventory, "cogs": cogs, "days": days}
    formula = "(inventory / cogs) * days"

    if inventory is None or cogs is None or cogs <= 0:
        return CalculationResult(
            metric="INVENTORY_DAYS",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if cogs is not None and cogs <= 0 else "INSUFFICIENT_DATA",
            notes="COGS is zero, negative, or not disclosed" if cogs is not None and cogs <= 0 else "Missing inputs"
        )

    val = (inventory / cogs) * days
    return CalculationResult(
        metric="INVENTORY_DAYS",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="DAYS"
    )


def payable_days(
    payables: Optional[float],
    purchases: Optional[float],
    days: float = 365.0
) -> CalculationResult:
    """
    Computes Days Payable Outstanding (DPO).
    Formula: (payables / purchases) * days
    Rule: If purchases are unavailable, never silently substitute revenue. Return INSUFFICIENT_DATA.
    """
    inputs = {"payables": payables, "purchases": purchases, "days": days}
    formula = "(payables / purchases) * days"

    if payables is None or purchases is None or purchases <= 0:
        return CalculationResult(
            metric="PAYABLE_DAYS",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA",
            notes="Raw material purchases/operating expenses not disclosed"
        )

    val = (payables / purchases) * days
    return CalculationResult(
        metric="PAYABLE_DAYS",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="DAYS"
    )


def cash_conversion_cycle(
    dso: Optional[float],
    dio: Optional[float],
    dpo: Optional[float]
) -> CalculationResult:
    """
    Computes Cash Conversion Cycle (CCC).
    Formula: dso + dio - dpo
    """
    inputs = {"dso": dso, "dio": dio, "dpo": dpo}
    formula = "dso + dio - dpo"

    if dso is None or dio is None or dpo is None:
        return CalculationResult(
            metric="CASH_CONVERSION_CYCLE",
            value=None,
            formula=formula,
            inputs=inputs,
            status="INSUFFICIENT_DATA",
            notes="Requires verified DSO, DIO, and DPO"
        )

    val = dso + dio - dpo
    return CalculationResult(
        metric="CASH_CONVERSION_CYCLE",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="DAYS"
    )
