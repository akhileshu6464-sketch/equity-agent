"""
Base Context & Interface for Deterministic Calculations
Enforces that every calculation receives:
- company_id, isin, ticker
- period, period_type (ANNUAL, QUARTERLY, TTM), fiscal_year
- statement_scope (CONSOLIDATED, STANDALONE)
- currency (INR, USD, etc.)
- source_id, source_tier (TIER_1_REGULATORY, TIER_2_AGGREGATOR, TIER_3_WEB)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum
import math
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


class DataStatus(str, Enum):
    VALID = "VALID"
    NOT_DISCLOSED = "NOT_DISCLOSED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class CanonicalFinancialContext:
    """Immutable context binding calculations to a specific company, period, and scope."""
    company_id: str
    isin: str
    ticker: str
    period: str                         # e.g. "FY2024", "Q3 FY2025"
    period_type: str = "ANNUAL"         # "ANNUAL", "QUARTERLY", "TTM"
    fiscal_year: str = ""               # e.g. "FY2024"
    fiscal_quarter: Optional[str] = None # e.g. "Q1", "Q2"
    statement_scope: str = "CONSOLIDATED" # "CONSOLIDATED" or "STANDALONE"
    currency: str = "INR"
    source_tier: str = "TIER_1_REGULATORY"
    source_id: str = ""

    def validate_compatibility(self, other: "CanonicalFinancialContext") -> bool:
        """Verifies that two contexts can be legitimately combined in a calculation."""
        if self.company_id != other.company_id:
            return False
        if self.statement_scope != other.statement_scope:
            return False
        if self.currency != other.currency:
            return False
        return True


@dataclass
class CalculationResult:
    """Standard return object for all deterministic calculations."""
    metric: str
    value: Optional[float]
    formula: str
    inputs: Dict[str, Any]
    status: str = "VALID"               # "VALID", "NOT_DISCLOSED", "NOT_APPLICABLE", "INSUFFICIENT_DATA"
    unit: str = "PERCENT"               # "PERCENT", "INR", "RATIO", "DAYS", "MULTIPLE", "BPS"
    notes: str = ""
    statement_scope: str = "CONSOLIDATED"

    @property
    def is_valid(self) -> bool:
        return self.status == "VALID" and self.value is not None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CalculationAuditRecord:
    """Full reproducibility audit record for every calculated number (Section 60)."""
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
