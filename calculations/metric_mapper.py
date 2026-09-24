"""
Financial Metric Normalization & Explicit Mapping Layer (calculations/metric_mapper.py)
Normalizes raw line-item names from heterogeneous sources (Screener.in, Drishti, yfinance,
BSE/NSE statutory filings, FMP) into canonical financial schema metrics.

Rules:
1. Different sources may use different names (e.g., 'Revenue from Operations', 'Net Sales', 'Sales').
2. They must ONLY map to the same metric when the accounting definition is actually equivalent.
3. Explicit metric mapping layer: never blindly map similar names.
4. Retains original source field/tag and statement type on every normalized datapoint.
5. Rejects ambiguous or non-equivalent line items to prevent accounting pollution.
"""

from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger("ResearchBeast.MetricMapper")


@dataclass(frozen=True)
class CanonicalMetricDef:
    """Canonical definition of an accounting line item."""
    canonical_key: str          # e.g. "revenue", "ebitda", "pat"
    display_name: str           # e.g. "Revenue from Operations", "EBITDA", "Profit After Tax"
    statement_type: str         # "PL" (Profit & Loss), "BS" (Balance Sheet), "CF" (Cash Flow), "RATIO"
    unit_default: str           # "INR_CR", "PERCENT", "INR", "RATIO", "DAYS"
    description: str
    is_flow_metric: bool        # True for P&L and CF (period flow), False for BS (point-in-time stock)


# Registry of Canonical Metrics in Research Beast
CANONICAL_METRICS: Dict[str, CanonicalMetricDef] = {
    # ------------------ PROFIT & LOSS (PL) ------------------
    "revenue": CanonicalMetricDef(
        canonical_key="revenue",
        display_name="Revenue from Operations",
        statement_type="PL",
        unit_default="INR_CR",
        description="Core statutory revenue from operations / net sales excluding other non-operating income.",
        is_flow_metric=True
    ),
    "other_income": CanonicalMetricDef(
        canonical_key="other_income",
        display_name="Other Income",
        statement_type="PL",
        unit_default="INR_CR",
        description="Non-operating income including interest, dividend, and treasury gains.",
        is_flow_metric=True
    ),
    "total_revenue": CanonicalMetricDef(
        canonical_key="total_revenue",
        display_name="Total Revenue",
        statement_type="PL",
        unit_default="INR_CR",
        description="Sum of revenue from operations and other income.",
        is_flow_metric=True
    ),
    "operating_expenses": CanonicalMetricDef(
        canonical_key="operating_expenses",
        display_name="Operating Expenses",
        statement_type="PL",
        unit_default="INR_CR",
        description="Total operating expenses excluding finance costs and depreciation.",
        is_flow_metric=True
    ),
    "ebitda": CanonicalMetricDef(
        canonical_key="ebitda",
        display_name="Operating Profit (EBITDA)",
        statement_type="PL",
        unit_default="INR_CR",
        description="Earnings before interest, taxes, depreciation, and amortization.",
        is_flow_metric=True
    ),
    "depreciation": CanonicalMetricDef(
        canonical_key="depreciation",
        display_name="Depreciation & Amortization",
        statement_type="PL",
        unit_default="INR_CR",
        description="Depreciation on tangible assets and amortization of intangible assets.",
        is_flow_metric=True
    ),
    "ebit": CanonicalMetricDef(
        canonical_key="ebit",
        display_name="Operating Income (EBIT)",
        statement_type="PL",
        unit_default="INR_CR",
        description="Earnings before interest and taxes.",
        is_flow_metric=True
    ),
    "interest_expense": CanonicalMetricDef(
        canonical_key="interest_expense",
        display_name="Finance Costs",
        statement_type="PL",
        unit_default="INR_CR",
        description="Interest on debt obligations and financial liabilities.",
        is_flow_metric=True
    ),
    "pbt": CanonicalMetricDef(
        canonical_key="pbt",
        display_name="Profit Before Tax (PBT)",
        statement_type="PL",
        unit_default="INR_CR",
        description="Earnings before corporate income tax and exceptional items.",
        is_flow_metric=True
    ),
    "tax_expense": CanonicalMetricDef(
        canonical_key="tax_expense",
        display_name="Tax Expense",
        statement_type="PL",
        unit_default="INR_CR",
        description="Current and deferred corporate tax provisions.",
        is_flow_metric=True
    ),
    "pat": CanonicalMetricDef(
        canonical_key="pat",
        display_name="Net Profit (PAT)",
        statement_type="PL",
        unit_default="INR_CR",
        description="Consolidated Profit After Tax attributable to owners of the company.",
        is_flow_metric=True
    ),
    "eps": CanonicalMetricDef(
        canonical_key="eps",
        display_name="Earnings Per Share (EPS)",
        statement_type="PL",
        unit_default="INR",
        description="Basic/Diluted earnings per equity share in INR.",
        is_flow_metric=True
    ),

    # ------------------ BALANCE SHEET (BS) ------------------
    "equity_share_capital": CanonicalMetricDef(
        canonical_key="equity_share_capital",
        display_name="Equity Share Capital",
        statement_type="BS",
        unit_default="INR_CR",
        description="Paid-up equity share capital.",
        is_flow_metric=False
    ),
    "reserves_and_surplus": CanonicalMetricDef(
        canonical_key="reserves_and_surplus",
        display_name="Reserves & Surplus",
        statement_type="BS",
        unit_default="INR_CR",
        description="Accumulated retained earnings and statutory reserves.",
        is_flow_metric=False
    ),
    "net_worth": CanonicalMetricDef(
        canonical_key="net_worth",
        display_name="Net Worth / Shareholders Equity",
        statement_type="BS",
        unit_default="INR_CR",
        description="Total equity attributable to equity shareholders (Capital + Reserves).",
        is_flow_metric=False
    ),
    "borrowings": CanonicalMetricDef(
        canonical_key="borrowings",
        display_name="Total Borrowings (Debt)",
        statement_type="BS",
        unit_default="INR_CR",
        description="Total long-term and short-term debt borrowings.",
        is_flow_metric=False
    ),
    "cash_and_equivalents": CanonicalMetricDef(
        canonical_key="cash_and_equivalents",
        display_name="Cash & Bank Balances",
        statement_type="BS",
        unit_default="INR_CR",
        description="Cash, bank balances, liquid mutual funds, and treasury deposits.",
        is_flow_metric=False
    ),
    "fixed_assets": CanonicalMetricDef(
        canonical_key="fixed_assets",
        display_name="Fixed Assets (Net Block)",
        statement_type="BS",
        unit_default="INR_CR",
        description="Property, plant, equipment, and right-of-use assets net of depreciation.",
        is_flow_metric=False
    ),
    "cwip": CanonicalMetricDef(
        canonical_key="cwip",
        display_name="Capital Work in Progress",
        statement_type="BS",
        unit_default="INR_CR",
        description="Work-in-progress capital expenditures under execution.",
        is_flow_metric=False
    ),
    "investments": CanonicalMetricDef(
        canonical_key="investments",
        display_name="Investments",
        statement_type="BS",
        unit_default="INR_CR",
        description="Non-current and current financial investments.",
        is_flow_metric=False
    ),
    "receivables": CanonicalMetricDef(
        canonical_key="receivables",
        display_name="Trade Receivables",
        statement_type="BS",
        unit_default="INR_CR",
        description="Amounts owed to the company by commercial customers for goods/services delivered.",
        is_flow_metric=False
    ),
    "inventory": CanonicalMetricDef(
        canonical_key="inventory",
        display_name="Inventories",
        statement_type="BS",
        unit_default="INR_CR",
        description="Raw materials, work-in-progress, and finished goods inventory.",
        is_flow_metric=False
    ),
    "payables": CanonicalMetricDef(
        canonical_key="payables",
        display_name="Trade Payables",
        statement_type="BS",
        unit_default="INR_CR",
        description="Amounts owed by the company to commercial vendors and suppliers.",
        is_flow_metric=False
    ),
    "working_capital": CanonicalMetricDef(
        canonical_key="working_capital",
        display_name="Working Capital",
        statement_type="BS",
        unit_default="INR_CR",
        description="Current assets minus current liabilities.",
        is_flow_metric=False
    ),
    "total_assets": CanonicalMetricDef(
        canonical_key="total_assets",
        display_name="Total Assets",
        statement_type="BS",
        unit_default="INR_CR",
        description="Total consolidated balance sheet assets.",
        is_flow_metric=False
    ),

    # ------------------ CASH FLOW (CF) ------------------
    "operating_cash_flow": CanonicalMetricDef(
        canonical_key="operating_cash_flow",
        display_name="Cash from Operating Activities (CFO)",
        statement_type="CF",
        unit_default="INR_CR",
        description="Net cash generated from operating business activities.",
        is_flow_metric=True
    ),
    "investing_cash_flow": CanonicalMetricDef(
        canonical_key="investing_cash_flow",
        display_name="Cash from Investing Activities (CFI)",
        statement_type="CF",
        unit_default="INR_CR",
        description="Net cash used in capital expenditures, acquisitions, and asset purchases.",
        is_flow_metric=True
    ),
    "financing_cash_flow": CanonicalMetricDef(
        canonical_key="financing_cash_flow",
        display_name="Cash from Financing Activities (CFF)",
        statement_type="CF",
        unit_default="INR_CR",
        description="Net cash flows from debt issues/repayments, equity issuance, and dividends paid.",
        is_flow_metric=True
    ),
    "capex": CanonicalMetricDef(
        canonical_key="capex",
        display_name="Capital Expenditures",
        statement_type="CF",
        unit_default="INR_CR",
        description="Cash outflows for acquisition of property, plant, equipment, and intangibles.",
        is_flow_metric=True
    ),
    "free_cash_flow": CanonicalMetricDef(
        canonical_key="free_cash_flow",
        display_name="Free Cash Flow (FCF)",
        statement_type="CF",
        unit_default="INR_CR",
        description="Operating cash flow minus capital expenditures (CFO - Capex).",
        is_flow_metric=True
    ),

    # ------------------ RATIOS / MARKET ------------------
    "ebitda_margin": CanonicalMetricDef(
        canonical_key="ebitda_margin",
        display_name="Operating Profit Margin (OPM %)",
        statement_type="RATIO",
        unit_default="PERCENT",
        description="EBITDA as a percentage of revenue from operations.",
        is_flow_metric=True
    ),
    "pat_margin": CanonicalMetricDef(
        canonical_key="pat_margin",
        display_name="Net Profit Margin (NPM %)",
        statement_type="RATIO",
        unit_default="PERCENT",
        description="PAT as a percentage of revenue from operations.",
        is_flow_metric=True
    ),
    "roe": CanonicalMetricDef(
        canonical_key="roe",
        display_name="Return on Equity (ROE %)",
        statement_type="RATIO",
        unit_default="PERCENT",
        description="PAT as a percentage of average net worth.",
        is_flow_metric=True
    ),
    "roce": CanonicalMetricDef(
        canonical_key="roce",
        display_name="Return on Capital Employed (ROCE %)",
        statement_type="RATIO",
        unit_default="PERCENT",
        description="EBIT as a percentage of capital employed (Net Worth + Debt - Cash).",
        is_flow_metric=True
    ),
    "debt_to_equity": CanonicalMetricDef(
        canonical_key="debt_to_equity",
        display_name="Debt to Equity Ratio",
        statement_type="RATIO",
        unit_default="RATIO",
        description="Total borrowings divided by net worth.",
        is_flow_metric=False
    ),
}


# Explicit source field mappings to canonical metrics
# Format: {source: {raw_field_normalized_pattern: canonical_key}}
SOURCE_FIELD_MAPPINGS: Dict[str, List[Tuple[str, str]]] = {
    # Screener.in line-item mappings
    "SCREENER": [
        (r"^sales\b", "revenue"),
        (r"^revenue\s+from\s+operations\b", "revenue"),
        (r"^net\s+sales\b", "revenue"),
        (r"^expenses\b", "operating_expenses"),
        (r"^operating\s+profit\b", "ebitda"),
        (r"^opm\s*%", "ebitda_margin"),
        (r"^other\s+income\b", "other_income"),
        (r"^interest\b", "interest_expense"),
        (r"^depreciation\b", "depreciation"),
        (r"^profit\s+before\s+tax\b", "pbt"),
        (r"^tax\s*%", "tax_expense"),
        (r"^net\s+profit\b", "pat"),
        (r"^eps\s+in\s+rs\b", "eps"),
        (r"^dividend\s+payout\s*%", "dividend_payout"),
        (r"^equity\s+capital\b", "equity_share_capital"),
        (r"^reserves\b", "reserves_and_surplus"),
        (r"^borrowings\b", "borrowings"),
        (r"^other\s+liabilities\b", "other_liabilities"),
        (r"^total\s+liabilities\b", "total_assets"),
        (r"^fixed\s+assets\b", "fixed_assets"),
        (r"^cwip\b", "cwip"),
        (r"^investments\b", "investments"),
        (r"^other\s+assets\b", "other_assets"),
        (r"^total\s+assets\b", "total_assets"),
        (r"^cash\s+from\s+operating\s+activity\b", "operating_cash_flow"),
        (r"^cash\s+from\s+investing\s+activity\b", "investing_cash_flow"),
        (r"^cash\s+from\s+financing\s+activity\b", "financing_cash_flow"),
        (r"^net\s+cash\s+flow\b", "net_cash_flow"),
        (r"^debtor\s+days\b", "receivable_days"),
        (r"^inventory\s+days\b", "inventory_days"),
        (r"^days\s+payable\b", "payable_days"),
        (r"^cash\s+conversion\s+cycle\b", "cash_conversion_cycle"),
        (r"^working\s+capital\s+days\b", "working_capital_days"),
        (r"^roce\s*%", "roce"),
        (r"^roe\s*%", "roe"),
    ],
    # Drishti API line-item mappings
    "DRISHTI": [
        (r"^revenue\b", "revenue"),
        (r"^sales\b", "revenue"),
        (r"^net_sales\b", "revenue"),
        (r"^total_revenue\b", "total_revenue"),
        (r"^operating_income\b", "ebit"),
        (r"^operating_profit\b", "ebitda"),
        (r"^ebitda\b", "ebitda"),
        (r"^ebit\b", "ebit"),
        (r"^pat\b", "pat"),
        (r"^net_profit\b", "pat"),
        (r"^profit_after_tax\b", "pat"),
        (r"^eps\b", "eps"),
        (r"^total_debt\b", "borrowings"),
        (r"^cash_and_equivalents\b", "cash_and_equivalents"),
        (r"^net_debt\b", "net_debt"),
        (r"^operating_cash_flow\b", "operating_cash_flow"),
        (r"^free_cash_flow\b", "free_cash_flow"),
        (r"^total_assets\b", "total_assets"),
        (r"^net_worth\b", "net_worth"),
    ],
    # yfinance line-item mappings
    "YFINANCE": [
        (r"^total\s+revenue\b", "total_revenue"),
        (r"^operating\s+revenue\b", "revenue"),
        (r"^ebitda\b", "ebitda"),
        (r"^operating\s+income\b", "ebit"),
        (r"^net\s+income\b", "pat"),
        (r"^basic\s+eps\b", "eps"),
        (r"^total\s+debt\b", "borrowings"),
        (r"^cash\s+and\s+cash\s+equivalents\b", "cash_and_equivalents"),
        (r"^operating\s+cash\s+flow\b", "operating_cash_flow"),
        (r"^capital\s+expenditure\b", "capex"),
        (r"^free\s+cash\s+flow\b", "free_cash_flow"),
        (r"^receivables\b", "receivables"),
        (r"^inventory\b", "inventory"),
        (r"^payables\b", "payables"),
        (r"^working\s+capital\b", "working_capital"),
        (r"^total\s+assets\b", "total_assets"),
        (r"^stockholders\s+equity\b", "net_worth"),
        (r"^interest\s+expense\b", "interest_expense"),
    ],
    # BSE/NSE Statutory Filing mappings
    "BSE_NSE_FILINGS": [
        (r"^revenue\s+from\s+operations\b", "revenue"),
        (r"^other\s+income\b", "other_income"),
        (r"^total\s+income\b", "total_revenue"),
        (r"^cost\s+of\s+materials\s+consumed\b", "raw_material_cost"),
        (r"^employee\s+benefits\s+expense\b", "employee_cost"),
        (r"^finance\s+costs\b", "interest_expense"),
        (r"^depreciation\s+and\s+amortisation\b", "depreciation"),
        (r"^profit\s+before\s+tax\b", "pbt"),
        (r"^profit\s+for\s+the\s+period\b", "pat"),
        (r"^profit\s+after\s+tax\b", "pat"),
        (r"^earnings\s+per\s+equity\s+share\b", "eps"),
        (r"^paid[- ]up\s+equity\s+share\s+capital\b", "equity_share_capital"),
        (r"^other\s+equity\b", "reserves_and_surplus"),
        (r"^total\s+equity\b", "net_worth"),
        (r"^non[- ]current\s+borrowings\b", "long_term_borrowings"),
        (r"^current\s+borrowings\b", "short_term_borrowings"),
        (r"^trade\s+receivables\b", "receivables"),
        (r"^inventories\b", "inventory"),
        (r"^trade\s+payables\b", "payables"),
        (r"^cash\s+and\s+cash\s+equivalents\b", "cash_and_equivalents"),
    ]
}


class NormalizedMetricResult(NamedTuple):
    """Result of normalizing a raw metric from an external source."""
    is_mapped: bool
    canonical_key: str
    display_name: str
    statement_type: str
    unit_default: str
    original_source_field: str
    source_name: str
    accounting_note: str


class MetricMapper:
    """
    Explicit, auditable metric mapper that guarantees:
    1. Zero blind mapping: lines map only when the accounting definition is identical.
    2. Retains original raw source field for full auditability.
    3. Prevents ambiguous line items from silently entering the verified database.
    """

    @classmethod
    def normalize_metric_name(
        cls,
        raw_name: str,
        source: str = "SCREENER"
    ) -> NormalizedMetricResult:
        """
        Normalizes a raw line-item field name to its canonical financial metric key.
        Returns a NormalizedMetricResult. If no valid equivalent mapping exists, is_mapped=False.
        """
        clean_raw = str(raw_name or "").strip()
        if not clean_raw:
            return NormalizedMetricResult(
                is_mapped=False,
                canonical_key="unknown",
                display_name=clean_raw,
                statement_type="UNKNOWN",
                unit_default="INR_CR",
                original_source_field=clean_raw,
                source_name=source,
                accounting_note="Empty line-item field name."
            )

        norm_src = source.upper()
        if norm_src not in SOURCE_FIELD_MAPPINGS:
            # Fallback to general patterns across all sources
            patterns = (
                SOURCE_FIELD_MAPPINGS.get("SCREENER", []) +
                SOURCE_FIELD_MAPPINGS.get("DRISHTI", []) +
                SOURCE_FIELD_MAPPINGS.get("BSE_NSE_FILINGS", [])
            )
        else:
            patterns = SOURCE_FIELD_MAPPINGS[norm_src]

        lower_raw = clean_raw.lower()
        lower_raw_clean = re.sub(r"[_\s]+", " ", lower_raw).strip()

        for pattern, canon_key in patterns:
            if re.search(pattern, lower_raw_clean, re.IGNORECASE):
                canon_def = CANONICAL_METRICS.get(canon_key)
                if canon_def:
                    return NormalizedMetricResult(
                        is_mapped=True,
                        canonical_key=canon_def.canonical_key,
                        display_name=canon_def.display_name,
                        statement_type=canon_def.statement_type,
                        unit_default=canon_def.unit_default,
                        original_source_field=clean_raw,
                        source_name=source,
                        accounting_note=f"Mapped '{clean_raw}' to '{canon_def.canonical_key}' via explicit regex rule '{pattern}'"
                    )

        # Direct canonical key check
        clean_key = lower_raw_clean.replace(" ", "_")
        if clean_key in CANONICAL_METRICS:
            canon_def = CANONICAL_METRICS[clean_key]
            return NormalizedMetricResult(
                is_mapped=True,
                canonical_key=canon_def.canonical_key,
                display_name=canon_def.display_name,
                statement_type=canon_def.statement_type,
                unit_default=canon_def.unit_default,
                original_source_field=clean_raw,
                source_name=source,
                accounting_note="Direct canonical key match."
            )

        # Unmapped: reject blind mapping
        return NormalizedMetricResult(
            is_mapped=False,
            canonical_key=clean_key,
            display_name=clean_raw,
            statement_type="UNKNOWN",
            unit_default="INR_CR",
            original_source_field=clean_raw,
            source_name=source,
            accounting_note="No verified accounting equivalence rule found. Preserved as unmapped raw metric."
        )

    @classmethod
    def get_canonical_definition(cls, canonical_key: str) -> Optional[CanonicalMetricDef]:
        """Retrieves official definition of a canonical metric."""
        return CANONICAL_METRICS.get(canonical_key.lower().strip())
