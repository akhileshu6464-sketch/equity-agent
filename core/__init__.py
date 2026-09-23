"""
Core Domain Framework for Company Identity and Research Isolation.
"""

from .company_identity import CompanyIdentity, resolve_canonical_identity, resolve_company_identity
from .research_context import (
    ResearchRunContext,
    create_research_context,
    DataContaminationError,
    EntityRole,
    assert_company_boundary,
    validate_everything_belongs_to
)

__all__ = [
    "CompanyIdentity",
    "resolve_canonical_identity",
    "resolve_company_identity",
    "ResearchRunContext",
    "create_research_context",
    "DataContaminationError",
    "EntityRole",
    "assert_company_boundary",
    "validate_everything_belongs_to"
]
