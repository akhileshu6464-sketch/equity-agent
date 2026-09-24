"""
Drishti Company Identity Firewall (services/drishti/identity_firewall.py)
Strictly enforces cross-company boundary isolation on all incoming Drishti records.
Guarantees:
1. Every Drishti response is verified against Research Beast canonical CompanyIdentity.
2. Evaluates: NSE symbol, BSE code, ISIN, and legal company name.
3. NEVER accepts matching on company name alone.
4. If identity cannot be confidently mapped -> REJECTS THE DATA. Zero guessing.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from core.company_identity import CompanyIdentity

logger = logging.getLogger("ResearchBeast.Drishti.IdentityFirewall")


class DrishtiIdentityMismatchError(Exception):
    """Raised when an incoming Drishti record does not match the target company's canonical identity."""
    pass


class DrishtiIdentityFirewall:
    """
    Company boundary gatekeeper for all Drishti external payloads.
    Validates identity before any data is normalized or stored.
    """

    @classmethod
    def clean_symbol(cls, sym: Optional[str]) -> str:
        """Strips exchange suffixes and spaces from symbol."""
        if not sym:
            return ""
        return re.sub(r"(?i)\.(NS|BO|NSE|BSE)$", "", str(sym)).strip().upper()

    @classmethod
    def clean_code(cls, code: Optional[str]) -> str:
        """Normalizes scrip code or ISIN."""
        if not code:
            return ""
        return str(code).strip().upper()

    @classmethod
    def verify_and_align_item(
        cls,
        item: Dict[str, Any],
        target_identity: CompanyIdentity,
        endpoint: str,
        strict_raise: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Verifies that a single Drishti item belongs to target_identity.
        Returns: Augmented dict with canonical identifiers, or None if rejected.
        """
        # Extract Drishti identifiers from item
        d_sym = cls.clean_symbol(item.get("symbol"))
        d_scrip = cls.clean_code(item.get("scrip_code"))
        d_isin = cls.clean_code(item.get("isin"))
        d_cname = str(item.get("company_name") or item.get("company") or "").strip()

        # Target canonical identifiers
        tgt_nse = cls.clean_symbol(target_identity.nse_symbol or target_identity.primary_symbol)
        tgt_bse = cls.clean_code(target_identity.bse_code)
        tgt_isin = cls.clean_code(target_identity.isin)
        tgt_legal = (target_identity.legal_name or target_identity.display_name or "").upper()

        # Strict Multi-Factor Matching Rule:
        # At least ONE authoritative regulatory identifier (NSE symbol, BSE scrip code, or ISIN) MUST match.
        symbol_matches = bool(d_sym and tgt_nse and d_sym == tgt_nse)
        scrip_matches = bool(d_scrip and tgt_bse and d_scrip == tgt_bse)
        isin_matches = bool(d_isin and tgt_isin and d_isin == tgt_isin)

        # Check for cross-company contamination in name (e.g. Reliance vs Tata)
        name_contradiction = False
        if d_cname and tgt_legal:
            d_name_upper = d_cname.upper()
            # If item name is completely different and no symbol matches, it's a contradiction
            # e.g. "TCS" vs "TATA MOTORS"
            words_item = set(re.findall(r"\w+", d_name_upper))
            words_tgt = set(re.findall(r"\w+", tgt_legal))
            # Remove common generic corporate tokens
            stopwords = {"LIMITED", "LTD", "INDIA", "CORP", "CORPORATION", "ENTERPRISES", "HOLDINGS", "THE"}
            clean_words_item = words_item - stopwords
            clean_words_tgt = words_tgt - stopwords
            if clean_words_item and clean_words_tgt and not (clean_words_item & clean_words_tgt):
                name_contradiction = True

        is_verified = (symbol_matches or scrip_matches or isin_matches) and not name_contradiction

        if not is_verified:
            msg = (
                f"REJECTED Drishti record from '{endpoint}': Identity mismatch for target '{target_identity.company_id}'. "
                f"Drishti values: [symbol='{d_sym}', scrip='{d_scrip}', isin='{d_isin}', company='{d_cname}']. "
                f"Target canonical: [nse='{tgt_nse}', bse='{tgt_bse}', isin='{tgt_isin}']."
            )
            logger.warning(msg)
            if strict_raise:
                raise DrishtiIdentityMismatchError(msg)
            return None

        # Record is validated: inject canonical company identity
        validated = dict(item)
        validated["company_id"] = target_identity.company_id
        validated["company_name"] = target_identity.legal_name or target_identity.display_name
        validated["isin"] = target_identity.isin
        validated["nse_symbol"] = tgt_nse
        validated["bse_code"] = tgt_bse
        validated["verification_status"] = "VALIDATED"
        validated["source"] = "DRISHTI"
        validated["source_endpoint"] = endpoint

        return validated

    @classmethod
    def filter_and_validate_batch(
        cls,
        items: List[Dict[str, Any]],
        target_identity: CompanyIdentity,
        endpoint: str
    ) -> List[Dict[str, Any]]:
        """
        Filters a batch of raw Drishti responses, dropping any items that fail canonical alignment.
        """
        validated_list: List[Dict[str, Any]] = []
        rejected_count = 0

        for item in items:
            if not isinstance(item, dict):
                continue
            aligned = cls.verify_and_align_item(item, target_identity, endpoint, strict_raise=False)
            if aligned:
                validated_list.append(aligned)
            else:
                rejected_count += 1

        if rejected_count > 0:
            logger.info(
                f"Identity Firewall filtered endpoint '{endpoint}': "
                f"{len(validated_list)} verified, {rejected_count} rejected for target '{target_identity.company_id}'."
            )

        return validated_list
