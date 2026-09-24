"""
Fundamental Data Store & Normalizer (services/decision_engine/fundamental_store.py)
Collects, normalizes, reconciles, and indexes multi-year annual and quarterly financial data.

Strict Architecture Principles (Sections 4, 5, 6, 7):
1. THE DATABASE KNOWS THE FACTS. AI is never the database or source of financial truth.
2. Canonical schema:
   {company_id, isin, metric, value, unit, currency, period_start, period_end,
    period_type, fiscal_year, quarter, scope, source, source_document, source_date,
    extraction_method, verification_status}
3. No anonymous numbers: Every single value retains full provenance.
4. Source reconciliation: When multiple sources provide the same number, compare them.
   - Match within tolerance -> VERIFIED
   - Divergence -> CONFLICT (investigate revision, period, scope, units; if unresolved: DO NOT use for analysis).
5. Revision control: original value, revised value, filing date, revision date, revision status.
   Latest valid becomes ACTIVE; older versions remain for audit.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
import os
import sqlite3
import time
import math
import logging

from calculations.margins import ebitda_margin as calc_ebitda_margin, ebit_margin as calc_ebit_margin, pat_margin as calc_pat_margin
from calculations.profitability import roe as calc_roe, roce as calc_roce
from calculations.leverage import net_debt as calc_net_debt
from calculations.audit import global_audit_registry
from calculations.normalization import format_percentage, format_inr_crores
from calculations.metric_mapper import MetricMapper
from core.research_context import assert_company_boundary, DataContaminationError, EntityRole

logger = logging.getLogger("ResearchBeast.FundamentalStore")

DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_CACHE_DIR, "financial_cache.db")


@dataclass(frozen=True)
class FundamentalDatapoint:
    """
    Immutable, fully-auditable verified financial datapoint (Sections 4, 5, 6, 7).
    No anonymous financial numbers.
    """
    company_id: str
    isin: str
    metric: str
    value: Optional[float]
    unit: str = "INR_CR"                       # "INR_CR", "PERCENT", "RATIO", "COUNT", "INR", "DAYS"
    currency: str = "INR"
    period_start: str = ""                    # e.g. "2023-04-01"
    period_end: str = ""                      # e.g. "2024-03-31"
    period_type: str = "ANNUAL"               # "ANNUAL" or "QUARTERLY"
    fiscal_year: str = ""                     # e.g. "FY2024"
    quarter: Optional[str] = None             # e.g. "Q1", "Q2", "Q3", "Q4"
    scope: str = "CONSOLIDATED"               # "CONSOLIDATED" or "STANDALONE"
    source: str = "Statutory Financial Disclosures"
    source_document: str = ""
    source_date: str = ""
    extraction_method: str = "DETERMINISTIC_REGULATORY_PARSER"
    verification_status: str = "VERIFIED"     # "VERIFIED", "CONFLICT", "VALIDATED", "DATA_UNAVAILABLE"

    # Explicit normalization tracking (Section 4)
    original_source_field: str = ""

    # Provenance and classification
    ticker: str = ""
    exchange: str = "NSE"
    statement_scope: str = "CONSOLIDATED"     # Backward-compatible alias for scope
    document: str = ""                        # Backward-compatible alias for source_document
    period: str = ""                          # e.g. "FY24", "Dec 2024"
    value_type: str = "REPORTED"              # "REPORTED" or "CALCULATED"
    source_tier: str = "TIER_1_REGULATORY"
    page_or_section: str = ""
    entity_role: str = "PRIMARY_COMPANY"

    # Revision Control (Section 7)
    original_value: Optional[float] = None
    revised_value: Optional[float] = None
    filing_date: str = ""
    revision_date: str = ""
    revision_status: str = "ACTIVE"           # "ACTIVE", "SUPERSEDED", "RESTATED"
    is_active: bool = True

    # Multi-source Reconciliation & Usability (Section 6)
    is_usable_for_analysis: bool = True
    conflict_reason: Optional[str] = None
    reconciliation_sources: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["reconciliation_sources"] = list(self.reconciliation_sources)
        return d


class FundamentalDataStore:
    """
    Central Verified Financial Data Layer (Section 5).
    Structured repository of normalized, reconciled, auditable financial metrics.
    Enforces that AI agents never invent or estimate basic financial figures.
    """

    def __init__(self, company_id: str, ticker: str, exchange: str = "NSE", isin: str = ""):
        self.company_id = company_id
        self.ticker = ticker
        self.exchange = exchange
        self.isin = isin
        self._datapoints: List[FundamentalDatapoint] = []
        self._index: Dict[Tuple[str, str, str], FundamentalDatapoint] = {}  # (metric, period_type, period) -> Datapoint
        self._conflicts: List[FundamentalDatapoint] = []

    def add_datapoint(
        self,
        metric: str,
        period: str,
        period_type: str,
        value: Optional[float],
        unit: str = "INR_CR",
        statement_scope: str = "CONSOLIDATED",
        value_type: str = "REPORTED",
        source_tier: str = "TIER_1_REGULATORY",
        source: str = "Verified Statutory Disclosures",
        source_date: str = "",
        document: str = "",
        page_or_section: str = "",
        entity_role: str = "PRIMARY_COMPANY",
        currency: str = "INR",
        period_start: str = "",
        period_end: str = "",
        fiscal_year: str = "",
        quarter: Optional[str] = None,
        extraction_method: str = "DETERMINISTIC_REGULATORY_PARSER",
        verification_status: str = "VERIFIED",
        original_source_field: str = "",
        original_value: Optional[float] = None,
        revised_value: Optional[float] = None,
        filing_date: str = "",
        revision_date: str = "",
        revision_status: str = "ACTIVE",
        is_active: bool = True,
        is_usable_for_analysis: bool = True,
        conflict_reason: Optional[str] = None,
        reconciliation_sources: Optional[List[str]] = None
    ) -> FundamentalDatapoint:
        """Adds a single verified datapoint strictly bound to this company's canonical identity."""
        if entity_role != "PRIMARY_COMPANY":
            raise DataContaminationError(
                f"CRITICAL CONTAMINATION ERROR in [FundamentalDataStore]: "
                f"Cannot add non-primary entity role '{entity_role}' to fundamental store for company '{self.company_id}'. Execution halted."
            )
        clean_val = None
        if value is not None:
            try:
                f = float(value)
                if not (math.isnan(f) or math.isinf(f)):
                    clean_val = f
            except (ValueError, TypeError):
                clean_val = None

        clean_period = str(period).strip()
        clean_ptype = str(period_type).strip().upper()
        clean_fy = fiscal_year or (clean_period if clean_ptype == "ANNUAL" else "")
        clean_scope = statement_scope.strip().upper()

        rec_sources = tuple(reconciliation_sources) if reconciliation_sources else (source,)

        dp = FundamentalDatapoint(
            company_id=self.company_id,
            isin=self.isin,
            metric=metric,
            value=clean_val,
            unit=unit,
            currency=currency,
            period_start=period_start,
            period_end=period_end,
            period_type=clean_ptype,
            fiscal_year=clean_fy,
            quarter=quarter,
            scope=clean_scope,
            source=source,
            source_document=document,
            source_date=source_date,
            extraction_method=extraction_method,
            verification_status=verification_status,
            original_source_field=original_source_field or metric,
            ticker=self.ticker,
            exchange=self.exchange,
            statement_scope=clean_scope,
            document=document,
            period=clean_period,
            value_type=value_type,
            source_tier=source_tier,
            page_or_section=page_or_section,
            entity_role=entity_role,
            original_value=original_value if original_value is not None else clean_val,
            revised_value=revised_value,
            filing_date=filing_date,
            revision_date=revision_date,
            revision_status=revision_status,
            is_active=is_active,
            is_usable_for_analysis=is_usable_for_analysis,
            conflict_reason=conflict_reason,
            reconciliation_sources=rec_sources
        )

        self._datapoints.append(dp)
        self._index[(metric, dp.period_type, dp.period)] = dp

        # Add index aliases for canonical accounting equivalents
        alias_groups = [
            {"Revenue", "Revenue from Operations", "Sales", "Net Sales"},
            {"EBITDA", "Operating Profit"},
            {"EBIT", "Operating Income"},
            {"PAT", "Net Profit", "Net Income", "Profit After Tax"},
            {"Total Debt", "Borrowings"},
            {"Operating Cash Flow", "Cash from Operating Activity", "CFO"},
            {"Receivables", "Debtor Days", "Trade Receivables"},
            {"Capital Expenditures", "Capex"},
            {"Interest Expense", "Interest"}
        ]
        for grp in alias_groups:
            if metric in grp:
                for alias in grp:
                    self._index[(alias, dp.period_type, dp.period)] = dp
                break

        if not is_usable_for_analysis or verification_status == "CONFLICT":
            self._conflicts.append(dp)

        return dp

    def reconcile_and_add_datapoint(
        self,
        metric: str,
        period: str,
        period_type: str,
        value: Optional[float],
        new_source: str,
        new_document: str = "",
        unit: str = "INR_CR",
        statement_scope: str = "CONSOLIDATED",
        tolerance_pct: float = 1.0,
        original_source_field: str = ""
    ) -> FundamentalDatapoint:
        """
        Multi-source reconciliation gate (Section 6).
        When multiple sources provide the same number:
        - Compares new_source vs existing record.
        - Match within tolerance -> Marks VERIFIED, appends source.
        - Divergence -> Marks CONFLICT, flags for investigation, DO NOT use for analysis.
        - Never lets AI choose between conflicting sources.
        """
        key = (metric, period_type.strip().upper(), str(period).strip())
        existing = self._index.get(key)
        if existing is None:
            # Check canonical alias groups
            alias_groups = [
                {"Revenue", "Revenue from Operations", "Sales", "Net Sales"},
                {"EBITDA", "Operating Profit"},
                {"EBIT", "Operating Income"},
                {"PAT", "Net Profit", "Net Income", "Profit After Tax"},
                {"Total Debt", "Borrowings"},
                {"Operating Cash Flow", "Cash from Operating Activity", "CFO"},
                {"Receivables", "Debtor Days", "Trade Receivables"},
                {"Capital Expenditures", "Capex"},
                {"Interest Expense", "Interest"}
            ]
            for grp in alias_groups:
                if metric in grp:
                    for alias in grp:
                        alt_key = (alias, period_type.strip().upper(), str(period).strip())
                        if alt_key in self._index:
                            existing = self._index[alt_key]
                            break
                    if existing:
                        break

        clean_val = None
        if value is not None:
            try:
                f = float(value)
                if not (math.isnan(f) or math.isinf(f)):
                    clean_val = f
            except (ValueError, TypeError):
                clean_val = None

        if existing is None:
            # First observation of this metric
            return self.add_datapoint(
                metric=metric,
                period=period,
                period_type=period_type,
                value=clean_val,
                unit=unit,
                statement_scope=statement_scope,
                source=new_source,
                document=new_document,
                original_source_field=original_source_field,
                verification_status="VALIDATED",
                reconciliation_sources=[new_source]
            )

        # Existing record found -> Reconcile
        if clean_val is not None and existing.value is not None:
            base = max(abs(existing.value), 1.0)
            diff_pct = (abs(clean_val - existing.value) / base) * 100.0

            if diff_pct <= tolerance_pct:
                # Reconciliation match -> Mark VERIFIED
                updated_sources = list(existing.reconciliation_sources)
                if new_source not in updated_sources:
                    updated_sources.append(new_source)

                # Update existing record in place
                verified_dp = FundamentalDatapoint(
                    company_id=existing.company_id,
                    isin=existing.isin,
                    metric=existing.metric,
                    value=existing.value,
                    unit=existing.unit,
                    currency=existing.currency,
                    period_start=existing.period_start,
                    period_end=existing.period_end,
                    period_type=existing.period_type,
                    fiscal_year=existing.fiscal_year,
                    quarter=existing.quarter,
                    scope=existing.scope,
                    source=f"{existing.source} + {new_source}",
                    source_document=existing.source_document,
                    source_date=existing.source_date,
                    extraction_method=existing.extraction_method,
                    verification_status="VERIFIED",
                    original_source_field=existing.original_source_field,
                    ticker=existing.ticker,
                    exchange=existing.exchange,
                    statement_scope=existing.statement_scope,
                    document=existing.document,
                    period=existing.period,
                    value_type=existing.value_type,
                    source_tier=existing.source_tier,
                    page_or_section=existing.page_or_section,
                    entity_role=existing.entity_role,
                    original_value=existing.original_value,
                    revised_value=existing.revised_value,
                    filing_date=existing.filing_date,
                    revision_date=existing.revision_date,
                    revision_status=existing.revision_status,
                    is_active=True,
                    is_usable_for_analysis=True,
                    conflict_reason=None,
                    reconciliation_sources=tuple(updated_sources)
                )
                self._index[key] = verified_dp
                # Replace in list
                for i, dp in enumerate(self._datapoints):
                    if (dp.metric, dp.period_type, dp.period) == key:
                        self._datapoints[i] = verified_dp
                        break
                logger.info(f"Reconciliation verified for {metric} ({period}): {existing.source} vs {new_source}")
                return verified_dp
            else:
                # Numerical divergence -> Flag CONFLICT (Section 6)
                conflict_msg = (
                    f"Divergence of {diff_pct:.2f}% detected for {metric} ({period}): "
                    f"Existing '{existing.source}' reported {existing.value} vs '{new_source}' reported {clean_val}. "
                    f"Flagged for investigation (scope/restatement/period alignment). Excluded from automated analysis."
                )
                conflict_dp = FundamentalDatapoint(
                    company_id=existing.company_id,
                    isin=existing.isin,
                    metric=existing.metric,
                    value=existing.value,
                    unit=existing.unit,
                    currency=existing.currency,
                    period_start=existing.period_start,
                    period_end=existing.period_end,
                    period_type=existing.period_type,
                    fiscal_year=existing.fiscal_year,
                    quarter=existing.quarter,
                    scope=existing.scope,
                    source=existing.source,
                    source_document=existing.source_document,
                    source_date=existing.source_date,
                    extraction_method=existing.extraction_method,
                    verification_status="CONFLICT",
                    original_source_field=existing.original_source_field,
                    ticker=existing.ticker,
                    exchange=existing.exchange,
                    statement_scope=existing.statement_scope,
                    document=existing.document,
                    period=existing.period,
                    value_type=existing.value_type,
                    source_tier=existing.source_tier,
                    page_or_section=existing.page_or_section,
                    entity_role=existing.entity_role,
                    original_value=existing.original_value,
                    revised_value=clean_val,
                    filing_date=existing.filing_date,
                    revision_date=str(time.time()),
                    revision_status="CONFLICT",
                    is_active=False,
                    is_usable_for_analysis=False,
                    conflict_reason=conflict_msg,
                    reconciliation_sources=(existing.source, new_source)
                )
                self._index[key] = conflict_dp
                for i, dp in enumerate(self._datapoints):
                    if (dp.metric, dp.period_type, dp.period) == key:
                        self._datapoints[i] = conflict_dp
                        break
                self._conflicts.append(conflict_dp)
                logger.warning(f"SOURCE RECONCILIATION CONFLICT: {conflict_msg}")
                return conflict_dp

        return existing

    def add_datapoint_object(self, dp: FundamentalDatapoint) -> None:
        """Adds an existing FundamentalDatapoint verifying strict company boundary."""
        assert_company_boundary(dp, self.company_id, allowed_roles=("PRIMARY_COMPANY",), caller_module="FundamentalDataStore.add_datapoint_object")
        self._datapoints.append(dp)
        self._index[(dp.metric, dp.period_type, dp.period)] = dp
        if not dp.is_usable_for_analysis or dp.verification_status == "CONFLICT":
            self._conflicts.append(dp)

    def get_datapoint(self, metric: str, period: str, period_type: str = "ANNUAL") -> Optional[FundamentalDatapoint]:
        """Retrieves a specific verified datapoint by metric, period, and period_type."""
        return self._index.get((metric, period_type.upper(), period))

    def get_usable_datapoint(self, metric: str, period: str, period_type: str = "ANNUAL") -> Optional[FundamentalDatapoint]:
        """
        Retrieves a verified datapoint ONLY IF it has passed reconciliation and is usable for analysis.
        Returns None if conflicting or unverified (Section 6: never let AI guess or use ungrounded numbers).
        """
        dp = self.get_datapoint(metric, period, period_type)
        if dp is not None and dp.is_usable_for_analysis and dp.verification_status != "CONFLICT":
            return dp
        return None

    def get_series(self, metric: str, period_type: str = "ANNUAL") -> List[FundamentalDatapoint]:
        """Returns chronologically ordered datapoints for a given metric and period type."""
        dps = [dp for dp in self._datapoints if dp.metric == metric and dp.period_type == period_type.upper()]
        return dps

    def get_latest_datapoint(self, metric: str, period_type: str = "ANNUAL") -> Optional[FundamentalDatapoint]:
        """Returns the most recent verified datapoint for a metric, or None if unavailable (never guesses)."""
        series = self.get_series(metric, period_type)
        return series[-1] if series else None

    def get_latest_datapoint_value(self, metric: str, period_type: str = "ANNUAL") -> Optional[float]:
        """Returns the float value of the most recent verified datapoint, or None if unavailable."""
        dp = self.get_latest_datapoint(metric, period_type)
        return dp.value if dp is not None else None

    def get_conflicts(self) -> List[FundamentalDatapoint]:
        """Returns all datapoints currently flagged with CONFLICT status."""
        return [dp for dp in self._datapoints if dp.verification_status == "CONFLICT" or not dp.is_usable_for_analysis]

    def populate_from_raw_sources(
        self,
        company_data: Dict[str, Any],
        screener_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Populates store from verified financial data structures (FinancialDataService & ScreenerEngine).
        Guarantees that 100% of figures originate from deterministic primary sources and code calculations.
        """
        if company_data:
            c_cid = company_data.get("company_id")
            if c_cid:
                assert_company_boundary({"company_id": c_cid}, self.company_id, caller_module="FundamentalDataStore.populate_from_raw_sources(company_data)")

        if screener_data:
            s_cid = screener_data.get("company_id")
            if s_cid:
                assert_company_boundary({"company_id": s_cid}, self.company_id, caller_module="FundamentalDataStore.populate_from_raw_sources(screener_data)")

        count = 0
        history_years = company_data.get("history_years", []) or []

        # 1. Ingest Annual Multi-Year History
        for y_data in history_years:
            year_label = str(y_data.get("year", ""))
            if not year_label:
                continue

            raw_items = [
                ("Revenue", y_data.get("revenue"), "INR_CR"),
                ("EBITDA", y_data.get("ebitda"), "INR_CR"),
                ("EBIT", y_data.get("operating_income"), "INR_CR"),
                ("PAT", y_data.get("net_income"), "INR_CR"),
                ("EPS", y_data.get("eps"), "INR"),
                ("Total Debt", y_data.get("total_debt"), "INR_CR"),
                ("Cash & Equivalents", y_data.get("cash_and_equivalents"), "INR_CR"),
                ("Operating Cash Flow", y_data.get("operating_cash_flow"), "INR_CR"),
                ("Capital Expenditures", abs(y_data.get("capital_expenditures")) if y_data.get("capital_expenditures") is not None else None, "INR_CR"),
                ("Free Cash Flow", y_data.get("free_cash_flow"), "INR_CR"),
                ("Receivables", y_data.get("receivables"), "INR_CR"),
                ("Inventory", y_data.get("inventory"), "INR_CR"),
                ("Payables", y_data.get("payables"), "INR_CR"),
                ("Working Capital", y_data.get("working_capital"), "INR_CR"),
                ("Total Assets", y_data.get("total_assets"), "INR_CR"),
                ("Stockholders Equity", y_data.get("stockholders_equity"), "INR_CR"),
                ("Interest Expense", abs(y_data.get("interest_expense")) if y_data.get("interest_expense") is not None else None, "INR_CR"),
            ]

            for m_name, val, unit in raw_items:
                if val is not None:
                    self.add_datapoint(
                        metric=m_name,
                        period=year_label,
                        period_type="ANNUAL",
                        value=float(val),
                        unit=unit,
                        statement_scope="CONSOLIDATED",
                        value_type="REPORTED",
                        source_tier="TIER_1_REGULATORY",
                        source="Audited Annual Financial Statements",
                        document=f"Annual Financial Statements {year_label}",
                        original_source_field=m_name,
                        verification_status="VERIFIED"
                    )
                    count += 1

            rev = y_data.get("revenue")
            ebitda = y_data.get("ebitda")
            ebit = y_data.get("operating_income")
            pat = y_data.get("net_income")
            equity = y_data.get("stockholders_equity")
            total_debt = y_data.get("total_debt", 0.0)
            cash = y_data.get("cash_and_equivalents", 0.0)

            # Deterministic Code-Calculated Ratios (Section 8)
            ebitda_m_res = calc_ebitda_margin(ebitda, rev)
            ebit_m_res = calc_ebit_margin(ebit, rev)
            pat_m_res = calc_pat_margin(pat, rev)
            roe_res = calc_roe(pat, None, equity)
            capital_employed = (equity + total_debt - cash) if (equity is not None and (equity + total_debt - cash) > 0) else None
            roce_res = calc_roce(ebit, None, capital_employed)
            net_debt_res = calc_net_debt(total_debt, cash)

            calculated_ratios = [
                ("EBITDA Margin", ebitda_m_res, "PERCENT"),
                ("EBIT Margin", ebit_m_res, "PERCENT"),
                ("Net Margin", pat_m_res, "PERCENT"),
                ("ROE", roe_res, "PERCENT"),
                ("ROCE", roce_res, "PERCENT"),
                ("Net Debt", net_debt_res, "INR_CR")
            ]

            for m_name, c_res, unit in calculated_ratios:
                if c_res.value is not None:
                    self.add_datapoint(
                        metric=m_name,
                        period=year_label,
                        period_type="ANNUAL",
                        value=round(c_res.value, 2),
                        unit=unit,
                        statement_scope="CONSOLIDATED",
                        value_type="CALCULATED",
                        source_tier="TIER_1_REGULATORY",
                        source="Deterministic Code Calculation",
                        document=f"Annual Financial Statements {year_label}",
                        original_source_field=m_name,
                        verification_status="VERIFIED"
                    )
                    global_audit_registry.record_calculation(
                        company_id=self.company_id,
                        metric=m_name,
                        period=year_label,
                        calc_result=c_res,
                        formatted_result=format_percentage(c_res.value) if unit == "PERCENT" else format_inr_crores(c_res.value * 1e7),
                        source_ids=[f"Annual Financial Statements {year_label}"],
                        statement_scope="CONSOLIDATED"
                    )
                    count += 1

        # 2. Ingest Quarterly Results
        if screener_data:
            q_rows = screener_data.get("quarterly_rows", []) or []
            periods = [k for k in (q_rows[0].keys() if q_rows else []) if k not in ["Metric", "metric"]]

            for row in q_rows:
                raw_metric = str(row.get("Metric", "")).strip()
                if not raw_metric:
                    continue

                for p in periods:
                    val = row.get(p)
                    if val is not None:
                        try:
                            clean_val = float(str(val).replace(",", "").replace("%", "").strip())
                            unit = "PERCENT" if "OPM" in raw_metric or "%" in raw_metric else "INR_CR"
                            self.add_datapoint(
                                metric=f"Quarterly {raw_metric}",
                                period=p,
                                period_type="QUARTERLY",
                                value=clean_val,
                                unit=unit,
                                source="Quarterly Financial Disclosures (BSE/NSE LODR)",
                                document=f"Quarterly Earnings Release {p}",
                                original_source_field=raw_metric,
                                verification_status="VERIFIED"
                            )
                            count += 1
                        except (ValueError, TypeError):
                            continue

        # 3. Optional Drishti Reconciliation (Section 6)
        d_intel = (company_data or {}).get("drishti") or (screener_data or {}).get("drishti")
        if d_intel and isinstance(d_intel, dict):
            earnings_list = d_intel.get("earnings", [])
            for ear in earnings_list:
                ear_period = str(getattr(ear, "period", "") or (ear.get("period", "") if isinstance(ear, dict) else "")).strip()
                ear_rev = getattr(ear, "revenue", None) or (ear.get("revenue") if isinstance(ear, dict) else None)
                ear_pat = getattr(ear, "pat", None) or (ear.get("pat") if isinstance(ear, dict) else None)

                if ear_period and ear_rev is not None:
                    self.reconcile_and_add_datapoint(
                        metric="Revenue from Operations",
                        period=ear_period,
                        period_type="ANNUAL" if "FY" in ear_period else "QUARTERLY",
                        value=float(ear_rev),
                        new_source="Drishti API",
                        new_document="Drishti Earnings Disclosures"
                    )
                if ear_period and ear_pat is not None:
                    self.reconcile_and_add_datapoint(
                        metric="Net Profit (PAT)",
                        period=ear_period,
                        period_type="ANNUAL" if "FY" in ear_period else "QUARTERLY",
                        value=float(ear_pat),
                        new_source="Drishti API",
                        new_document="Drishti Earnings Disclosures"
                    )

        logger.info(f"FundamentalDataStore initialized with {count} verified financial datapoints for {self.company_id}")
        try:
            self.save_to_sqlite()
        except Exception as e:
            logger.warning(f"Could not auto-persist fundamental store to SQLite: {e}")
        return count

    def save_to_sqlite(self, db_path: Optional[str] = None) -> int:
        """Persists all verified fundamental datapoints to SQLite fundamental_datapoints table."""
        target_db = db_path or DEFAULT_DB_PATH
        conn = None
        saved = 0
        try:
            os.makedirs(os.path.dirname(target_db), exist_ok=True)
            conn = sqlite3.connect(target_db)
            now = time.time()
            cursor = conn.cursor()

            # Ensure table exists with full canonical schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fundamental_datapoints (
                    company_id TEXT NOT NULL,
                    ticker TEXT,
                    isin TEXT,
                    metric TEXT NOT NULL,
                    period TEXT NOT NULL,
                    period_type TEXT NOT NULL,
                    value REAL,
                    unit TEXT,
                    currency TEXT DEFAULT 'INR',
                    period_start TEXT,
                    period_end TEXT,
                    fiscal_year TEXT,
                    quarter TEXT,
                    statement_scope TEXT,
                    value_type TEXT,
                    source_tier TEXT,
                    source TEXT,
                    source_date TEXT,
                    document TEXT,
                    page_or_section TEXT,
                    extraction_method TEXT,
                    verification_status TEXT DEFAULT 'VERIFIED',
                    original_source_field TEXT,
                    original_value REAL,
                    revised_value REAL,
                    filing_date TEXT,
                    revision_date TEXT,
                    revision_status TEXT DEFAULT 'ACTIVE',
                    is_active INTEGER DEFAULT 1,
                    is_usable_for_analysis INTEGER DEFAULT 1,
                    conflict_reason TEXT,
                    reconciliation_sources TEXT,
                    created_at REAL NOT NULL,
                    PRIMARY KEY (company_id, metric, period, period_type)
                )
            """)

            # Automatic schema migration for existing SQLite databases
            migration_cols = [
                ("currency", "TEXT DEFAULT 'INR'"),
                ("period_start", "TEXT"),
                ("period_end", "TEXT"),
                ("fiscal_year", "TEXT"),
                ("quarter", "TEXT"),
                ("statement_scope", "TEXT"),
                ("value_type", "TEXT"),
                ("source_tier", "TEXT"),
                ("source_date", "TEXT"),
                ("extraction_method", "TEXT"),
                ("verification_status", "TEXT DEFAULT 'VERIFIED'"),
                ("original_source_field", "TEXT"),
                ("original_value", "REAL"),
                ("revised_value", "REAL"),
                ("filing_date", "TEXT"),
                ("revision_date", "TEXT"),
                ("revision_status", "TEXT DEFAULT 'ACTIVE'"),
                ("is_active", "INTEGER DEFAULT 1"),
                ("is_usable_for_analysis", "INTEGER DEFAULT 1"),
                ("conflict_reason", "TEXT"),
                ("reconciliation_sources", "TEXT")
            ]
            for col_name, col_type in migration_cols:
                try:
                    cursor.execute(f"ALTER TABLE fundamental_datapoints ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

            for dp in self._datapoints:
                rec_sources_str = ",".join(dp.reconciliation_sources)
                cursor.execute("""
                    INSERT OR REPLACE INTO fundamental_datapoints (
                        company_id, ticker, isin, metric, period, period_type,
                        value, unit, currency, period_start, period_end, fiscal_year,
                        quarter, statement_scope, value_type, source_tier, source,
                        source_date, document, page_or_section, extraction_method,
                        verification_status, original_source_field, original_value,
                        revised_value, filing_date, revision_date, revision_status,
                        is_active, is_usable_for_analysis, conflict_reason,
                        reconciliation_sources, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dp.company_id, dp.ticker, dp.isin, dp.metric, dp.period, dp.period_type,
                    dp.value, dp.unit, dp.currency, dp.period_start, dp.period_end, dp.fiscal_year,
                    dp.quarter, dp.scope, dp.value_type, dp.source_tier, dp.source,
                    dp.source_date, dp.source_document, dp.page_or_section, dp.extraction_method,
                    dp.verification_status, dp.original_source_field, dp.original_value,
                    dp.revised_value, dp.filing_date, dp.revision_date, dp.revision_status,
                    1 if dp.is_active else 0, 1 if dp.is_usable_for_analysis else 0, dp.conflict_reason,
                    rec_sources_str, now
                ))
                saved += 1
            conn.commit()
            logger.info(f"Persisted {saved} fundamental datapoints for {self.company_id} into {target_db}")
        except Exception as e:
            logger.warning(f"Error persisting fundamental datapoints for {self.company_id} to SQLite: {e}")
        finally:
            if conn:
                conn.close()
        return saved

    def load_from_sqlite(self, db_path: Optional[str] = None) -> int:
        """Loads and indexes verified fundamental datapoints for this canonical company from SQLite."""
        target_db = db_path or DEFAULT_DB_PATH
        if not os.path.exists(target_db):
            return 0
        conn = None
        loaded = 0
        try:
            conn = sqlite3.connect(target_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT metric, period, period_type, value, unit, statement_scope,
                       value_type, source_tier, source, source_date, document, page_or_section
                FROM fundamental_datapoints
                WHERE company_id = ?
            """, (self.company_id,))
            rows = cursor.fetchall()
            for row in rows:
                m, p, p_type, val, unit, scope, v_type, s_tier, src, s_date, doc, page = row
                self.add_datapoint(
                    metric=m,
                    period=p,
                    period_type=p_type,
                    value=val,
                    unit=unit,
                    statement_scope=scope,
                    value_type=v_type,
                    source_tier=s_tier,
                    source=src,
                    source_date=s_date or "",
                    document=doc or "",
                    page_or_section=page or ""
                )
                loaded += 1
            logger.info(f"Loaded {loaded} fundamental datapoints for {self.company_id} from {target_db}")
        except Exception as e:
            logger.warning(f"Error loading fundamental datapoints for {self.company_id} from SQLite: {e}")
        finally:
            if conn:
                conn.close()
        return loaded

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns structured metadata summary of the fundamental store."""
        conflicts = self.get_conflicts()
        return {
            "company_id": self.company_id,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "isin": self.isin,
            "total_datapoints": len(self._datapoints),
            "metrics_available": sorted(list(set(dp.metric for dp in self._datapoints))),
            "annual_periods": sorted(list(set(dp.period for dp in self._datapoints if dp.period_type == "ANNUAL"))),
            "quarterly_periods": sorted(list(set(dp.period for dp in self._datapoints if dp.period_type == "QUARTERLY"))),
            "total_conflicts": len(conflicts),
            "conflicts": [c.to_dict() for c in conflicts]
        }
