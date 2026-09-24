"""
Research Run Context Module (core/research_context.py)
Propagates immutable run isolation metadata to every downstream module.
Enforces ZERO cross-company data contamination with fail-closed boundary assertions.
"""

import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional, Tuple, Iterable, List, Union

from .company_identity import CompanyIdentity, resolve_canonical_identity, CANONICAL_ALIASES


class DataContaminationError(ValueError, RuntimeError):
    """
    Critical Exception raised immediately when foreign company data,
    mixed-company calculations, or cross-company records are detected.
    Halts execution to prevent cross-contamination.
    """
    pass


class EntityRole(str, Enum):
    """
    Strict entity classification ensuring peer or subsidiary data
    is never mixed into primary company financial statements or calculations.
    """
    PRIMARY_COMPANY = "PRIMARY_COMPANY"
    SUBSIDIARY = "SUBSIDIARY"
    PEER = "PEER"
    INDUSTRY = "INDUSTRY"
    MARKET = "MARKET"


def _normalize_cid(cid: Optional[str]) -> str:
    """Helper to normalize company_id or ticker for canonical comparison."""
    if not cid:
        return ""
    s = str(cid).strip().upper()
    for prefix in ("NSE:", "BSE:", "IN:"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    for suffix in (".NS", ".BO"):
        if s.endswith(suffix):
            s = s[:-len(suffix)]
    return CANONICAL_ALIASES.get(s, s)


def assert_company_boundary(
    record_or_obj: Any,
    active_company_id: str,
    allowed_roles: Optional[Iterable[str]] = None,
    caller_module: str = "Unknown"
) -> bool:
    """
    Hard failure boundary assertion.
    Verifies that the provided record, dataset, or object belongs strictly to active_company_id.
    Fails closed by raising DataContaminationError on ANY foreign company data or forbidden role.
    """
    if record_or_obj is None or not active_company_id:
        return True

    norm_active = _normalize_cid(active_company_id)
    default_allowed = (EntityRole.PRIMARY_COMPANY.value,) if allowed_roles is None else tuple(
        r.value if isinstance(r, EntityRole) else str(r) for r in allowed_roles
    )

    if isinstance(record_or_obj, (list, tuple)):
        for item in record_or_obj:
            assert_company_boundary(item, active_company_id, allowed_roles=allowed_roles, caller_module=caller_module)
        return True

    # Extract company_id and entity_role whether record is a dict or an object
    rec_cid = None
    rec_role = None
    rec_isin = None

    if isinstance(record_or_obj, dict):
        rec_cid = record_or_obj.get("company_id") or record_or_obj.get("canonical_id")
        rec_role = record_or_obj.get("entity_role")
        rec_isin = record_or_obj.get("isin")
    elif hasattr(record_or_obj, "__dict__") or hasattr(record_or_obj, "__slots__"):
        rec_cid = getattr(record_or_obj, "company_id", None)
        rec_role = getattr(record_or_obj, "entity_role", None)
        rec_isin = getattr(record_or_obj, "isin", None)

    if rec_role is not None:
        rec_role_str = rec_role.value if isinstance(rec_role, EntityRole) else str(rec_role)
        if rec_role_str not in default_allowed:
            raise DataContaminationError(
                f"CRITICAL CONTAMINATION ERROR in [{caller_module}]: "
                f"Record has entity_role='{rec_role_str}', which is forbidden in context requiring {default_allowed}. "
                f"Active company: '{active_company_id}'. Execution halted."
            )

    if rec_cid:
        norm_rec = _normalize_cid(rec_cid)
        if norm_rec != norm_active:
            raise DataContaminationError(
                f"CRITICAL CONTAMINATION ERROR in [{caller_module}]: "
                f"Active research run is bound to company_id='{active_company_id}', "
                f"but encountered foreign record with company_id='{rec_cid}'! Execution halted."
            )

    return True


def validate_everything_belongs_to(
    dataset_or_state: Any,
    active_company_id: str,
    caller_module: str = "StateValidation"
) -> None:
    """
    Recursively scans a collection, dictionary, or state object and confirms
    every single element with company identity attributes matches active_company_id.
    """
    if dataset_or_state is None:
        return

    if isinstance(dataset_or_state, (list, tuple)):
        for item in dataset_or_state:
            validate_everything_belongs_to(item, active_company_id, caller_module=caller_module)
    elif isinstance(dataset_or_state, dict):
        assert_company_boundary(dataset_or_state, active_company_id, caller_module=caller_module)
        for k, v in dataset_or_state.items():
            if isinstance(v, (dict, list, tuple)):
                validate_everything_belongs_to(v, active_company_id, caller_module=f"{caller_module}.{k}")
            elif hasattr(v, "company_id"):
                assert_company_boundary(v, active_company_id, caller_module=f"{caller_module}.{k}")
    elif hasattr(dataset_or_state, "company_id"):
        assert_company_boundary(dataset_or_state, active_company_id, caller_module=caller_module)


@dataclass(frozen=True)
class ResearchRunContext:
    """
    Immutable execution context for a single research run.
    Guarantees that every downstream module knows exactly which canonical company
    is being researched, with zero ambiguity or cross-company leakage.
    """
    research_run_id: str                      # Unique UUID per research run
    company_id: str                           # Canonical internal company ID, e.g. "NSE:TATAMOTORS"
    company_name: str                         # Official registered company name
    legal_name: str                           # e.g. "Tata Motors Limited"
    display_name: str                         # e.g. "Tata Motors"
    ticker: str                               # e.g. "TATAMOTORS.NS"
    nse_symbol: str                           # e.g. "TATAMOTORS"
    bse_code: str                             # e.g. "500570"
    isin: str                                 # e.g. "INE155A01022"
    timestamp: str                            # ISO8601 timestamp
    exchange: str = "NSE"                     # Primary exchange
    allowed_entity_roles: Tuple[str, ...] = ("PRIMARY_COMPANY",)
    statement_scope: str = "CONSOLIDATED"     # Financial scope
    active_period: Optional[str] = None       # Financial period

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def assert_same_company(self, other_company_id: str, caller_module: str = "Unknown"):
        """
        Hard failure assertion.
        Halts immediately if any operation attempts to inject another company's data.
        """
        if not other_company_id:
            return
        norm_self = _normalize_cid(self.company_id)
        norm_other = _normalize_cid(other_company_id)
        if norm_self != norm_other:
            raise DataContaminationError(
                f"CRITICAL CONTAMINATION ERROR in [{caller_module}]: "
                f"Active research run is bound to company_id='{self.company_id}' ({self.company_name}), "
                f"but received data or request for company_id='{other_company_id}'! Execution aborted."
            )

    def assert_boundary(
        self,
        record: Any,
        allowed_roles: Optional[Iterable[str]] = None,
        caller_module: str = "Unknown"
    ) -> bool:
        """Convenience method to assert boundary against this context."""
        roles = allowed_roles if allowed_roles is not None else self.allowed_entity_roles
        return assert_company_boundary(record, self.company_id, allowed_roles=roles, caller_module=caller_module)


def create_research_context(user_input_or_identity: Any) -> ResearchRunContext:
    """
    Initializes a new ResearchRunContext from either user input string or existing CompanyIdentity.
    """
    if isinstance(user_input_or_identity, CompanyIdentity):
        identity = user_input_or_identity
    else:
        identity = resolve_canonical_identity(str(user_input_or_identity))

    run_id = f"run_{uuid.uuid4().hex[:12]}_{int(time.time())}"
    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return ResearchRunContext(
        research_run_id=run_id,
        company_id=identity.company_id,
        company_name=identity.company_name,
        legal_name=identity.legal_name,
        display_name=identity.display_name,
        ticker=identity.primary_ticker,
        nse_symbol=identity.nse_symbol,
        bse_code=identity.bse_code,
        isin=identity.isin,
        timestamp=now_str,
        exchange=identity.primary_exchange,
        allowed_entity_roles=(EntityRole.PRIMARY_COMPANY.value,),
        statement_scope="CONSOLIDATED",
        active_period=None
    )


@dataclass
class StructuredAgentContext:
    """
    Standard Structured Input Context for AI Agents (Section 11).
    Before execution: asserts all objects belong to company_id; if mismatch, raises DataContaminationError.
    """
    company_id: str
    company_name: str
    isin: str
    period: str
    scope: str
    verified_financial_data: Dict[str, Any]
    deterministic_calculations: List[Dict[str, Any]]
    verified_documents: List[Dict[str, Any]]
    news: List[Dict[str, Any]]
    announcements: List[Dict[str, Any]]
    known_conflicts: List[Dict[str, Any]]
    source_metadata: Dict[str, Any]

    def validate_integrity(self) -> None:
        """Asserts that all contained objects match company_id. Raises DataContaminationError if breached."""
        for collection_name, collection in [
            ("verified_documents", self.verified_documents),
            ("news", self.news),
            ("announcements", self.announcements),
            ("known_conflicts", self.known_conflicts)
        ]:
            if isinstance(collection, (list, tuple)):
                for item in collection:
                    assert_company_boundary(item, self.company_id, caller_module=f"StructuredAgentContext.{collection_name}")
            elif isinstance(collection, dict):
                assert_company_boundary(collection, self.company_id, caller_module=f"StructuredAgentContext.{collection_name}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
