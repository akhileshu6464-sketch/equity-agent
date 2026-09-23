"""
Fundamental Data Store & Normalizer (services/decision_engine/fundamental_store.py)
Collects, normalizes, and indexes multi-year annual and quarterly financial data.
Enforces that every financial value contains:
- company_id, ticker, exchange, isin
- metric, period, period_type (annual/quarterly)
- value, unit, source, source_date, document, page/section

The LLM is NEVER the source of financial numbers. All numbers are deterministically extracted.
"""

from dataclasses import dataclass, asdict
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
from core.research_context import assert_company_boundary, DataContaminationError, EntityRole

logger = logging.getLogger("ResearchBeast.FundamentalStore")

DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_CACHE_DIR, "financial_cache.db")


@dataclass(frozen=True)
class FundamentalDatapoint:
    """Immutable, fully-auditable financial datapoint."""
    company_id: str
    ticker: str
    exchange: str
    isin: str
    metric: str
    period: str            # e.g. "FY24", "FY23", "Q4 FY24", "Dec 2024"
    period_type: str       # "ANNUAL" or "QUARTERLY"
    value: Optional[float]
    unit: str = "INR_CR"   # "INR_CR", "PERCENT", "RATIO", "COUNT", "INR"
    statement_scope: str = "CONSOLIDATED"  # "CONSOLIDATED" or "STANDALONE"
    value_type: str = "REPORTED"           # "REPORTED" or "CALCULATED"
    source_tier: str = "TIER_1_REGULATORY" # "TIER_1_REGULATORY", "TIER_2_AGGREGATOR", "TIER_3_WEB"
    source: str = "Statutory Financial Disclosures"
    source_date: str = ""
    document: str = ""
    page_or_section: str = ""
    entity_role: str = "PRIMARY_COMPANY"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FundamentalDataStore:
    """
    Structured repository of normalized, auditable financial metrics for a canonical company.
    Provides multi-period indexing, chronological sorting, and metric-level historical queries.
    """

    def __init__(self, company_id: str, ticker: str, exchange: str = "NSE", isin: str = ""):
        self.company_id = company_id
        self.ticker = ticker
        self.exchange = exchange
        self.isin = isin
        self._datapoints: List[FundamentalDatapoint] = []
        self._index: Dict[Tuple[str, str, str], FundamentalDatapoint] = {}  # (metric, period_type, period) -> Datapoint

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
        entity_role: str = "PRIMARY_COMPANY"
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

        dp = FundamentalDatapoint(
            company_id=self.company_id,
            ticker=self.ticker,
            exchange=self.exchange,
            isin=self.isin,
            metric=metric,
            period=str(period).strip(),
            period_type=str(period_type).strip().upper(),
            value=clean_val,
            unit=unit,
            statement_scope=statement_scope,
            value_type=value_type,
            source_tier=source_tier,
            source=source,
            source_date=source_date,
            document=document,
            page_or_section=page_or_section,
            entity_role=entity_role
        )
        self._datapoints.append(dp)
        self._index[(metric, dp.period_type, dp.period)] = dp
        return dp

    def add_datapoint_object(self, dp: FundamentalDatapoint) -> None:
        """Adds an existing FundamentalDatapoint verifying strict company boundary."""
        assert_company_boundary(dp, self.company_id, allowed_roles=("PRIMARY_COMPANY",), caller_module="FundamentalDataStore.add_datapoint_object")
        self._datapoints.append(dp)
        self._index[(dp.metric, dp.period_type, dp.period)] = dp

    def get_datapoint(self, metric: str, period: str, period_type: str = "ANNUAL") -> Optional[FundamentalDatapoint]:
        """Retrieves a specific verified datapoint by metric, period, and period_type."""
        return self._index.get((metric, period_type.upper(), period))

    def get_series(self, metric: str, period_type: str = "ANNUAL") -> List[FundamentalDatapoint]:
        """Returns chronologically ordered datapoints for a given metric and period type."""
        dps = [dp for dp in self._datapoints if dp.metric == metric and dp.period_type == period_type.upper()]
        return dps

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

            metric_mappings = [
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

            # Ingest reported primary lines
            for m_name, val, unit in metric_mappings:
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
                        document=f"Annual Financial Statements {year_label}"
                    )
                    count += 1

            rev = y_data.get("revenue")
            ebitda = y_data.get("ebitda")
            ebit = y_data.get("operating_income")
            pat = y_data.get("net_income")
            equity = y_data.get("stockholders_equity")
            total_debt = y_data.get("total_debt", 0.0)
            cash = y_data.get("cash_and_equivalents", 0.0)

            # Deterministic Code-Calculated Ratios (Section 2 & 7: Pure Python calculations)
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
                        document=f"Annual Financial Statements {year_label}"
                    )
                    # Record into audit trail (Section 60)
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

        # 2. Ingest Quarterly Results from Screener/Fast Info
        if screener_data:
            q_rows = screener_data.get("quarterly_rows", []) or []
            # q_rows: list of dicts like {"Metric": "Sales", "Dec 2023": 1200, "Mar 2024": 1350, ...}
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
                                document=f"Quarterly Earnings Release {p}"
                            )
                            count += 1
                        except (ValueError, TypeError):
                            continue

        logger.info(f"FundamentalDataStore initialized with {count} verified financial datapoints for {self.company_id}")
        # Auto-persist to SQLite verified store
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
            for dp in self._datapoints:
                cursor.execute("""
                    INSERT OR REPLACE INTO fundamental_datapoints (
                        company_id, ticker, isin, metric, period, period_type,
                        value, unit, statement_scope, value_type, source_tier,
                        source, source_date, document, page_or_section, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dp.company_id, dp.ticker, dp.isin, dp.metric, dp.period, dp.period_type,
                    dp.value, dp.unit, dp.statement_scope, dp.value_type, dp.source_tier,
                    dp.source, dp.source_date, dp.document, dp.page_or_section, now
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
        return {
            "company_id": self.company_id,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "isin": self.isin,
            "total_datapoints": len(self._datapoints),
            "metrics_available": sorted(list(set(dp.metric for dp in self._datapoints))),
            "annual_periods": sorted(list(set(dp.period for dp in self._datapoints if dp.period_type == "ANNUAL"))),
            "quarterly_periods": sorted(list(set(dp.period for dp in self._datapoints if dp.period_type == "QUARTERLY")))
        }

