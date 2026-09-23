"""
Calculation Audit Registry
Stores and indexes reproducible CalculationAuditRecord instances for every calculated metric.
Enables click-to-verify UI displays (formula, inputs, source documents, result)
and ensures full compliance with Section 60 & Section 66.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .models import CalculationAuditRecord, CalculationResult


class CalculationAuditRegistry:
    """In-memory and persistent registry for reproducible calculation audit records."""

    def __init__(self):
        self._records: List[CalculationAuditRecord] = []
        # Key: (company_id, metric, period, statement_scope)
        self._index: Dict[tuple, CalculationAuditRecord] = {}

    def record_calculation(
        self,
        company_id: str,
        metric: str,
        period: str,
        calc_result: CalculationResult,
        formatted_result: str,
        source_ids: Optional[List[str]] = None,
        statement_scope: str = "CONSOLIDATED",
        engine_version: str = "2.0"
    ) -> CalculationAuditRecord:
        """Records a single deterministic calculation into the audit ledger."""
        record = CalculationAuditRecord(
            company_id=company_id,
            metric=metric,
            period=period,
            formula=calc_result.formula,
            inputs=calc_result.inputs,
            result=calc_result.value,
            formatted_result=formatted_result,
            source_ids=source_ids or [],
            calculated_at=datetime.utcnow().isoformat(),
            engine_version=engine_version,
            statement_scope=statement_scope,
            status=calc_result.status,
            notes=calc_result.notes
        )

        self._records.append(record)
        key = (company_id, metric, str(period).strip().upper(), statement_scope.upper())
        self._index[key] = record
        return record

    def get_record(
        self,
        company_id: str,
        metric: str,
        period: str,
        statement_scope: str = "CONSOLIDATED"
    ) -> Optional[CalculationAuditRecord]:
        """Retrieves an audit record by canonical key."""
        key = (company_id, metric, str(period).strip().upper(), statement_scope.upper())
        return self._index.get(key)

    def get_company_audit_trail(
        self,
        company_id: str,
        period: Optional[str] = None
    ) -> List[CalculationAuditRecord]:
        """Retrieves all calculation audit records for a given company."""
        res = [r for r in self._records if r.company_id == company_id]
        if period:
            res = [r for r in res if r.period == period]
        return res

    def to_json_list(self, company_id: str) -> List[Dict[str, Any]]:
        """Returns JSON-serializable list of audit records for the frontend or LLM prompt."""
        return [r.to_dict() for r in self.get_company_audit_trail(company_id)]

    def save_to_sqlite(self, db_path: Optional[str] = None, company_id: Optional[str] = None) -> int:
        """Persists calculation audit records to SQLite calculation_audit_records table."""
        import os
        import sqlite3
        import json

        default_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        target_db = db_path or os.path.join(default_dir, "financial_cache.db")

        records_to_save = self._records
        if company_id:
            records_to_save = [r for r in self._records if r.company_id == company_id]

        if not records_to_save:
            return 0

        conn = None
        saved = 0
        try:
            os.makedirs(os.path.dirname(target_db), exist_ok=True)
            conn = sqlite3.connect(target_db)
            cursor = conn.cursor()
            for r in records_to_save:
                cursor.execute("""
                    INSERT OR REPLACE INTO calculation_audit_records (
                        company_id, metric, period, statement_scope, formula,
                        inputs_json, result, formatted_result, status, source_ids_json,
                        calculated_at, engine_version, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.company_id, r.metric, r.period, r.statement_scope, r.formula,
                    json.dumps(r.inputs, default=str), r.result, r.formatted_result,
                    r.status, json.dumps(r.source_ids), r.calculated_at,
                    r.engine_version, r.notes
                ))
                saved += 1
            conn.commit()
        except Exception:
            pass
        finally:
            if conn:
                conn.close()
        return saved

    def load_from_sqlite(self, company_id: str, db_path: Optional[str] = None) -> int:
        """Loads calculation audit records from SQLite strictly scoped to company_id."""
        if not company_id:
            raise ValueError("company_id is required to load calculation audit records. Unscoped queries are strictly forbidden.")

        import os
        import sqlite3
        import json

        default_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        target_db = db_path or os.path.join(default_dir, "financial_cache.db")

        if not os.path.exists(target_db):
            return 0

        conn = None
        loaded = 0
        try:
            conn = sqlite3.connect(target_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT company_id, metric, period, statement_scope, formula,
                       inputs_json, result, formatted_result, status, source_ids_json,
                       calculated_at, engine_version, notes
                FROM calculation_audit_records
                WHERE company_id = ?
            """, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                cid, m, p, scope, formula, inp_json, res, f_res, status, src_json, calc_at, eng_ver, notes = row
                try:
                    inputs = json.loads(inp_json)
                except Exception:
                    inputs = {}
                try:
                    src_ids = json.loads(src_json)
                except Exception:
                    src_ids = []

                record = CalculationAuditRecord(
                    company_id=cid,
                    metric=m,
                    period=p,
                    formula=formula,
                    inputs=inputs,
                    result=res,
                    formatted_result=f_res,
                    source_ids=src_ids,
                    calculated_at=calc_at,
                    engine_version=eng_ver,
                    statement_scope=scope,
                    status=status,
                    notes=notes or ""
                )
                self._records.append(record)
                key = (cid, m, str(p).strip().upper(), scope.upper())
                self._index[key] = record
                loaded += 1
        except Exception:
            pass
        finally:
            if conn:
                conn.close()
        return loaded


# Singleton instance
global_audit_registry = CalculationAuditRegistry()

