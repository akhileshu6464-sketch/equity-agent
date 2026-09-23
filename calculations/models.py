"""
Canonical Financial Data Models & Calculation Audit Record
Enforces strict company isolation, period isolation, statement scope,
and calculation reproducibility across the entire financial engine.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class PeriodScope(str, Enum):
    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"
    TTM = "TTM"
    POINT_IN_TIME = "POINT_IN_TIME"


class StatementScope(str, Enum):
    CONSOLIDATED = "CONSOLIDATED"
    STANDALONE = "STANDALONE"


class ValueType(str, Enum):
    REPORTED = "REPORTED"
    CALCULATED = "CALCULATED"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"


class SourceTier(str, Enum):
    TIER_1_REGULATORY = "TIER_1_REGULATORY"  # BSE, NSE, Annual Report PDF, MCA
    TIER_2_AGGREGATOR = "TIER_2_AGGREGATOR"  # Screener.in, yfinance, Trendlyne
    TIER_3_WEB = "TIER_3_WEB"                # Web articles, news, conference notes


@dataclass(frozen=True)
class FinancialDataPoint:
    """
    Immutable canonical financial datapoint.
    Every financial value in the system must be tied to an explicit company, period,
    scope, and verified source provenance.
    """
    company_id: str
    company_name: str
    metric: str
    value: Optional[float]
    unit: str = "INR"                         # "INR", "PERCENT", "RATIO", "COUNT", "DAYS"
    currency: str = "INR"
    period_start: str = ""                    # e.g. "2023-04-01"
    period_end: str = ""                      # e.g. "2024-03-31"
    period_type: str = "ANNUAL"               # "ANNUAL", "QUARTERLY", "TTM"
    fiscal_year: str = ""                     # e.g. "FY2024"
    fiscal_quarter: Optional[str] = None      # e.g. "Q1", "Q2", "Q3", "Q4"
    statement_type: str = "PL"                # "PL", "BS", "CF", "RATIOS", "MARKET"
    statement_scope: str = "CONSOLIDATED"     # "CONSOLIDATED", "STANDALONE"
    value_type: str = "REPORTED"              # "REPORTED", "CALCULATED", "DERIVED"
    source_id: str = ""                       # e.g. "bse_filing_20240522"
    source_type: str = "TIER_1_REGULATORY"
    source_date: str = ""
    filing_date: str = ""
    confidence: float = 1.0
    restated: bool = False
    original_value: Optional[float] = None
    document: str = ""
    page_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CalculationResult:
    """Standard return object for deterministic calculation functions."""
    metric: str
    value: Optional[float]
    formula: str
    inputs: Dict[str, Any]
    status: str = "VALID"                     # "VALID", "NOT_APPLICABLE", "INSUFFICIENT_DATA"
    unit: str = "PERCENT"
    notes: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == "VALID" and self.value is not None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CalculationAuditRecord:
    """
    Complete audit trail for every calculated metric.
    Guarantees 100% mathematical reproducibility from stored source inputs.
    """
    company_id: str
    metric: str
    period: str
    formula: str
    inputs: Dict[str, Any]
    result: Optional[float]
    formatted_result: str
    source_ids: List[str] = field(default_factory=list)
    calculated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    engine_version: str = "2.0"
    statement_scope: str = "CONSOLIDATED"
    status: str = "VALID"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
