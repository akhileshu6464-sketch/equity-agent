"""
Deterministic Financial Calculations Package (services.calculations)
Pure Python numerical accounting, valuation, banking, and financial analysis functions.

Guarantees:
1. Zero LLM calculations.
2. Zero synthetic defaults or invented numbers.
3. Explicit formula and input tracking for auditability.
4. Safe handling of zero/negative denominators returning None.
5. Strict isolation by company, period, and statement scope.
"""

from .models import (
    FinancialDataPoint,
    CalculationAuditRecord,
    PeriodScope,
    StatementScope,
    ValueType,
    SourceTier,
    CalculationResult,
)
from .base import (
    CanonicalFinancialContext,
    DataStatus,
)
from .audit import (
    CalculationAuditRegistry,
    global_audit_registry,
)
from .normalization import (
    normalize_to_inr,
    format_inr_crores,
    format_percentage,
    format_multiple,
    format_days,
)
from .growth import (
    revenue_growth,
    yoy_change,
    qoq_change,
    cagr,
    inventory_growth,
    receivable_growth,
    cfo_growth,
)
from .margins import (
    ebitda_margin,
    ebit_margin,
    pat_margin,
    gross_margin,
    margin_change_bps,
)
from .profitability import (
    roe,
    roce,
    roic,
    asset_turnover,
)
from .cashflow import (
    cfo_to_pat,
    free_cash_flow,
    fcf_yield,
    cash_flow_reconciliation,
)
from .leverage import (
    debt_to_equity,
    net_debt,
    net_debt_to_ebitda,
    interest_coverage,
)
from .working_capital import (
    net_working_capital,
    receivable_days,
    inventory_days,
    payable_days,
    cash_conversion_cycle,
)
from .valuation import (
    pe_ratio,
    pb_ratio,
    market_capitalization,
    enterprise_value,
    ev_to_ebitda,
    ev_to_sales,
)
from .per_share import (
    eps,
    book_value_per_share,
    dividend_payout,
    share_dilution,
)
from .market import (
    market_return,
    relative_performance,
    drawdown,
    dividend_yield,
)
from .shareholding import (
    promoter_holding_change,
    promoter_pledge_percentage,
)
from .banking import (
    net_interest_margin,
    cost_to_income_ratio,
    gross_npa_ratio,
    net_npa_ratio,
    provision_coverage_ratio,
    crar,
    tier1_ratio,
    casa_ratio,
    credit_cost_ratio,
)
from .validation import (
    validate_calculation,
    reconcile_reported_vs_calculated,
    detect_sign_change,
)

__all__ = [
    "FinancialDataPoint",
    "CalculationAuditRecord",
    "CalculationAuditRegistry",
    "global_audit_registry",
    "PeriodScope",
    "StatementScope",
    "ValueType",
    "SourceTier",
    "CalculationResult",
    "CanonicalFinancialContext",
    "DataStatus",
    "normalize_to_inr",
    "format_inr_crores",
    "format_percentage",
    "format_multiple",
    "format_days",
    "revenue_growth",
    "yoy_change",
    "qoq_change",
    "cagr",
    "inventory_growth",
    "receivable_growth",
    "cfo_growth",
    "ebitda_margin",
    "ebit_margin",
    "pat_margin",
    "gross_margin",
    "margin_change_bps",
    "roe",
    "roce",
    "roic",
    "asset_turnover",
    "cfo_to_pat",
    "free_cash_flow",
    "fcf_yield",
    "cash_flow_reconciliation",
    "debt_to_equity",
    "net_debt",
    "net_debt_to_ebitda",
    "interest_coverage",
    "net_working_capital",
    "receivable_days",
    "inventory_days",
    "payable_days",
    "cash_conversion_cycle",
    "pe_ratio",
    "pb_ratio",
    "market_capitalization",
    "enterprise_value",
    "ev_to_ebitda",
    "ev_to_sales",
    "eps",
    "book_value_per_share",
    "dividend_payout",
    "share_dilution",
    "market_return",
    "relative_performance",
    "drawdown",
    "dividend_yield",
    "promoter_holding_change",
    "promoter_pledge_percentage",
    "net_interest_margin",
    "cost_to_income_ratio",
    "gross_npa_ratio",
    "net_npa_ratio",
    "provision_coverage_ratio",
    "crar",
    "tier1_ratio",
    "casa_ratio",
    "credit_cost_ratio",
    "validate_calculation",
    "reconcile_reported_vs_calculated",
    "detect_sign_change",
]
