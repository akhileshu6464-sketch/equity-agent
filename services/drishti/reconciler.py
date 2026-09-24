"""
Financial Reconciliation & Conflict Detection Gate (services/drishti/reconciler.py)
Enforces Research Beast's Critical Financial Data Rule:
DRISHTI_RAW -> NORMALIZED -> VALIDATED -> VERIFIED
1. Cross-checks Drishti earnings numbers against primary exchange filings (Screener.in / BSE).
2. If Drishti == Primary Filing -> VERIFIED.
3. If Drishti != Primary Filing -> CONFLICT (Flags for investigation. Never chooses automatically).
4. Never blindly overwrites Research Beast's verified financial database.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from services.screener_fetcher import _parse_numeric

logger = logging.getLogger("ResearchBeast.Drishti.Reconciler")


class FinancialReconciler:
    """
    Deterministically cross-checks financial numbers from Drishti against primary sources.
    """

    @classmethod
    def reconcile_metrics(
        cls,
        drishti_values: Dict[str, Any],
        primary_values: Dict[str, Any],
        tolerance_pct: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compares reported values (Revenue, EBITDA, PAT) between Drishti and primary filing.
        Returns:
        {
            "overall_status": "VERIFIED" | "CONFLICT" | "VALIDATED",
            "matches": [...],
            "conflicts": [...],
            "unverified_metrics": [...]
        }
        """
        matches = []
        conflicts = []
        unverified = []

        # Standard metric aliases
        metric_mappings = [
            ("revenue", ["revenue", "sales", "total_revenue", "income_from_operations"]),
            ("ebitda", ["ebitda", "operating_profit", "operating_earnings"]),
            ("pat", ["pat", "net_profit", "profit_after_tax"]),
        ]

        def find_val(data_dict: Dict[str, Any], aliases: List[str]) -> Optional[float]:
            for k, v in data_dict.items():
                clean_k = k.lower().replace(" ", "_").replace("-", "_")
                for alias in aliases:
                    if alias in clean_k:
                        num = _parse_numeric(str(v))
                        if num is not None:
                            return num
            return None

        for standard_key, aliases in metric_mappings:
            d_val = find_val(drishti_values, aliases)
            p_val = find_val(primary_values, aliases)

            if d_val is not None and p_val is not None:
                # Calculate relative difference
                base = max(abs(p_val), 1.0)
                diff_pct = (abs(d_val - p_val) / base) * 100.0

                if diff_pct <= tolerance_pct:
                    matches.append({
                        "metric": standard_key.upper(),
                        "drishti_value": d_val,
                        "primary_value": p_val,
                        "difference_pct": round(diff_pct, 2),
                        "status": "VERIFIED"
                    })
                else:
                    conflict_item = {
                        "metric": standard_key.upper(),
                        "drishti_value": d_val,
                        "primary_value": p_val,
                        "difference_pct": round(diff_pct, 2),
                        "status": "CONFLICT",
                        "audit_note": (
                            f"Numerical divergence of {diff_pct:.2f}% detected between Drishti ({d_val:,.1f}) "
                            f"and Primary regulatory filing ({p_val:,.1f}). System flagged for investigation."
                        )
                    }
                    conflicts.append(conflict_item)
                    logger.warning(f"Financial reconciliation CONFLICT: {conflict_item['audit_note']}")
            elif d_val is not None:
                unverified.append({
                    "metric": standard_key.upper(),
                    "drishti_value": d_val,
                    "status": "VALIDATED",
                    "audit_note": "Present in Drishti; awaiting secondary primary source confirmation."
                })

        # Determine overall verification status
        if conflicts:
            overall_status = "CONFLICT"
        elif matches:
            overall_status = "VERIFIED"
        else:
            overall_status = "VALIDATED"

        return {
            "overall_status": overall_status,
            "matches": matches,
            "conflicts": conflicts,
            "unverified_metrics": unverified,
            "requires_investigation": bool(conflicts),
        }
