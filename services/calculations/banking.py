"""
Deterministic Banking & NBFC Calculations (services/calculations/banking.py)
Covers Net Interest Margin (NIM), Cost-to-Income, GNPA, NNPA, PCR, CRAR, CET-1, CASA, and Credit Cost.
Guarantees zero hardcoded constants (eliminating synthetic 46.5%, 3.85%, 1.78%, 0.42%, 76.4%, 0.48%, 43.8%).
Missing items return None with status="NOT_DISCLOSED" or "INSUFFICIENT_DATA".
"""

from typing import Optional
from .base import CalculationResult


def net_interest_margin(
    net_interest_income: Optional[float],
    avg_earning_assets: Optional[float]
) -> CalculationResult:
    """
    Computes Net Interest Margin (NIM) %.
    Formula: (net_interest_income / avg_earning_assets) * 100
    """
    inputs = {"net_interest_income": net_interest_income, "avg_earning_assets": avg_earning_assets}
    formula = "(net_interest_income / avg_earning_assets) * 100"

    if net_interest_income is None or avg_earning_assets is None or avg_earning_assets <= 0:
        return CalculationResult(
            metric="NET_INTEREST_MARGIN",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if (avg_earning_assets is not None and avg_earning_assets <= 0) else "NOT_DISCLOSED",
            unit="PERCENT",
            notes="Net interest income or earning assets not disclosed in primary statements"
        )

    val = (net_interest_income / avg_earning_assets) * 100.0
    return CalculationResult(
        metric="NET_INTEREST_MARGIN",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def cost_to_income_ratio(
    operating_expenses: Optional[float],
    net_total_income: Optional[float]
) -> CalculationResult:
    """
    Computes Cost-to-Income Ratio %.
    Formula: (operating_expenses / net_total_income) * 100
    """
    inputs = {"operating_expenses": operating_expenses, "net_total_income": net_total_income}
    formula = "(operating_expenses / net_total_income) * 100"

    if operating_expenses is None or net_total_income is None or net_total_income <= 0:
        return CalculationResult(
            metric="COST_TO_INCOME_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if (net_total_income is not None and net_total_income <= 0) else "NOT_DISCLOSED",
            unit="PERCENT",
            notes="Operating expenses or net total income not disclosed"
        )

    val = (operating_expenses / net_total_income) * 100.0
    return CalculationResult(
        metric="COST_TO_INCOME_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def gross_npa_ratio(
    gross_npas: Optional[float],
    gross_advances: Optional[float]
) -> CalculationResult:
    """
    Computes Gross Non-Performing Asset (GNPA) Ratio %.
    Formula: (gross_npas / gross_advances) * 100
    """
    inputs = {"gross_npas": gross_npas, "gross_advances": gross_advances}
    formula = "(gross_npas / gross_advances) * 100"

    if gross_npas is None or gross_advances is None or gross_advances <= 0:
        return CalculationResult(
            metric="GROSS_NPA_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if (gross_advances is not None and gross_advances <= 0) else "NOT_DISCLOSED",
            unit="PERCENT",
            notes="Gross NPA or gross loan advances not disclosed in statutory filing"
        )

    val = (gross_npas / gross_advances) * 100.0
    return CalculationResult(
        metric="GROSS_NPA_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def net_npa_ratio(
    net_npas: Optional[float],
    net_advances: Optional[float]
) -> CalculationResult:
    """
    Computes Net Non-Performing Asset (NNPA) Ratio %.
    Formula: (net_npas / net_advances) * 100
    """
    inputs = {"net_npas": net_npas, "net_advances": net_advances}
    formula = "(net_npas / net_advances) * 100"

    if net_npas is None or net_advances is None or net_advances <= 0:
        return CalculationResult(
            metric="NET_NPA_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if (net_advances is not None and net_advances <= 0) else "NOT_DISCLOSED",
            unit="PERCENT",
            notes="Net NPA or net loan advances not disclosed"
        )

    val = (net_npas / net_advances) * 100.0
    return CalculationResult(
        metric="NET_NPA_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def provision_coverage_ratio(
    total_provisions: Optional[float],
    gross_npas: Optional[float]
) -> CalculationResult:
    """
    Computes Provision Coverage Ratio (PCR) %.
    Formula: (total_provisions / gross_npas) * 100
    """
    inputs = {"total_provisions": total_provisions, "gross_npas": gross_npas}
    formula = "(total_provisions / gross_npas) * 100"

    if total_provisions is None or gross_npas is None or gross_npas <= 0:
        return CalculationResult(
            metric="PROVISION_COVERAGE_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_APPLICABLE" if (gross_npas is not None and gross_npas <= 0) else "NOT_DISCLOSED",
            unit="PERCENT",
            notes="Provisions or gross NPAs not disclosed"
        )

    val = (total_provisions / gross_npas) * 100.0
    return CalculationResult(
        metric="PROVISION_COVERAGE_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def crar(
    total_capital: Optional[float],
    risk_weighted_assets: Optional[float]
) -> CalculationResult:
    """
    Computes Capital to Risk-Weighted Assets Ratio (CRAR) %.
    Formula: (total_capital / risk_weighted_assets) * 100
    """
    inputs = {"total_capital": total_capital, "risk_weighted_assets": risk_weighted_assets}
    formula = "(total_capital / risk_weighted_assets) * 100"

    if total_capital is None or risk_weighted_assets is None or risk_weighted_assets <= 0:
        return CalculationResult(
            metric="CRAR",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_DISCLOSED",
            unit="PERCENT",
            notes="Capital adequacy / Basel III disclosures not available in statement"
        )

    val = (total_capital / risk_weighted_assets) * 100.0
    return CalculationResult(
        metric="CRAR",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def tier1_ratio(
    tier1_capital: Optional[float],
    risk_weighted_assets: Optional[float]
) -> CalculationResult:
    """
    Computes Tier-1 / CET-1 Capital Ratio %.
    Formula: (tier1_capital / risk_weighted_assets) * 100
    """
    inputs = {"tier1_capital": tier1_capital, "risk_weighted_assets": risk_weighted_assets}
    formula = "(tier1_capital / risk_weighted_assets) * 100"

    if tier1_capital is None or risk_weighted_assets is None or risk_weighted_assets <= 0:
        return CalculationResult(
            metric="TIER1_CET1_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_DISCLOSED",
            unit="PERCENT"
        )

    val = (tier1_capital / risk_weighted_assets) * 100.0
    return CalculationResult(
        metric="TIER1_CET1_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def casa_ratio(
    casa_deposits: Optional[float],
    total_deposits: Optional[float]
) -> CalculationResult:
    """
    Computes Current Account Savings Account (CASA) Deposit Ratio %.
    Formula: (casa_deposits / total_deposits) * 100
    """
    inputs = {"casa_deposits": casa_deposits, "total_deposits": total_deposits}
    formula = "(casa_deposits / total_deposits) * 100"

    if casa_deposits is None or total_deposits is None or total_deposits <= 0:
        return CalculationResult(
            metric="CASA_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_DISCLOSED",
            unit="PERCENT",
            notes="CASA or total deposits breakdown not disclosed"
        )

    val = (casa_deposits / total_deposits) * 100.0
    return CalculationResult(
        metric="CASA_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )


def credit_cost_ratio(
    provisions_for_loans: Optional[float],
    avg_loans: Optional[float]
) -> CalculationResult:
    """
    Computes Annualized Credit Cost %.
    Formula: (provisions_for_loans / avg_loans) * 100
    """
    inputs = {"provisions_for_loans": provisions_for_loans, "avg_loans": avg_loans}
    formula = "(provisions_for_loans / avg_loans) * 100"

    if provisions_for_loans is None or avg_loans is None or avg_loans <= 0:
        return CalculationResult(
            metric="CREDIT_COST_RATIO",
            value=None,
            formula=formula,
            inputs=inputs,
            status="NOT_DISCLOSED",
            unit="PERCENT"
        )

    val = (provisions_for_loans / avg_loans) * 100.0
    return CalculationResult(
        metric="CREDIT_COST_RATIO",
        value=val,
        formula=formula,
        inputs=inputs,
        status="VALID",
        unit="PERCENT"
    )
