"""
Unit and Currency Normalization Module
Standardizes financial numbers from various reported units (Crores, Millions, Lakhs, Billions)
into canonical absolute figures for calculation, and provides clean presentation formatting.
Enforces full mathematical precision internally without intermediate rounding.
"""

from typing import Union, Optional
import math


CRORE_MULTIPLIER = 10_000_000.0
LAKH_MULTIPLIER = 100_000.0
MILLION_MULTIPLIER = 1_000_000.0
BILLION_MULTIPLIER = 1_000_000_000.0


def normalize_to_inr(
    val: Union[int, float, str, None],
    source_unit: str = "CRORE"
) -> Optional[float]:
    """
    Normalizes a numerical value from a declared source unit into absolute INR.
    Supported source_unit: 'CRORE', 'CR', 'LAKH', 'MILLION', 'MN', 'BILLION', 'BN', 'ABSOLUTE', 'INR'.
    Returns None if input is invalid or missing.
    """
    if val is None:
        return None

    if isinstance(val, str):
        clean_str = val.replace(",", "").replace("₹", "").replace("$", "").strip()
        if not clean_str or clean_str.upper() in ["N/A", "NA", "-", "--", "NONE", "NULL"]:
            return None
        try:
            val = float(clean_str)
        except ValueError:
            return None

    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return None
    except (TypeError, ValueError):
        return None

    unit_norm = str(source_unit).strip().upper()
    if unit_norm in ["CRORE", "CR", "INR_CR"]:
        return f_val * CRORE_MULTIPLIER
    elif unit_norm in ["LAKH", "LACS", "LAC"]:
        return f_val * LAKH_MULTIPLIER
    elif unit_norm in ["MILLION", "MN"]:
        return f_val * MILLION_MULTIPLIER
    elif unit_norm in ["BILLION", "BN"]:
        return f_val * BILLION_MULTIPLIER
    elif unit_norm in ["ABSOLUTE", "INR", "RAW"]:
        return f_val
    else:
        return f_val


def format_inr_crores(
    val_inr: Optional[float],
    decimals: int = 2,
    include_symbol: bool = True
) -> str:
    """Formats canonical absolute INR into human-readable ₹ Crores for presentation only."""
    if val_inr is None or math.isnan(val_inr) or math.isinf(val_inr):
        return "N/A"
    val_cr = val_inr / CRORE_MULTIPLIER
    prefix = "₹ " if include_symbol else ""
    return f"{prefix}{val_cr:,.{decimals}f} Cr"


def format_percentage(
    pct: Optional[float],
    decimals: int = 2,
    include_sign: bool = False
) -> str:
    """Formats a percentage value for presentation."""
    if pct is None or math.isnan(pct) or math.isinf(pct):
        return "N/A"
    sign = "+" if include_sign and pct > 0 else ""
    return f"{sign}{pct:.{decimals}f}%"


def format_multiple(
    mult: Optional[float],
    decimals: int = 2
) -> str:
    """Formats a valuation or conversion multiple (e.g. 0.90x, 18.5x)."""
    if mult is None or math.isnan(mult) or math.isinf(mult):
        return "N/A"
    return f"{mult:.{decimals}f}x"


def format_days(
    days: Optional[float],
    decimals: int = 1
) -> str:
    """Formats working capital turnover days."""
    if days is None or math.isnan(days) or math.isinf(days):
        return "N/A"
    return f"{days:.{decimals}f} days"
