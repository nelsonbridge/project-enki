"""Authoritative product-identity resolution for Project-Enki.

Historical labels are preserved as provenance. Current product/system identity is
resolved explicitly so aliases, shorthand, frequency, or recency cannot silently
override governed naming.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


CANONICAL_PROJECT_NAME = "Project-Enki"
CANONICAL_REPOSITORY = "nelsonbridge/project-enki"


class IdentityUsage(StrEnum):
    CURRENT = "current"
    HISTORICAL = "historical"
    REPOSITORY = "repository"


class IdentityResolutionError(ValueError):
    """Raised when a current identity cannot be resolved without guessing."""


@dataclass(frozen=True)
class ProductIdentityResolution:
    supplied_name: str
    usage: IdentityUsage
    resolved_name: str
    canonical: bool
    historical_source_preserved: bool


_HISTORICAL_OR_NONCANONICAL_ALIASES = {
    "Enki",
    "Enki Knowledge System",
    "Project Enki",
}
_REPOSITORY_ALIASES = {
    "project-enki",
    CANONICAL_REPOSITORY,
}


def resolve_project_enki_identity(
    supplied_name: str,
    *,
    usage: IdentityUsage = IdentityUsage.CURRENT,
) -> ProductIdentityResolution:
    """Resolve Project-Enki identity without rewriting historical truth.

    CURRENT usage always renders the governed display identity. HISTORICAL usage
    preserves the source label. REPOSITORY usage accepts only repository forms.
    Unknown labels fail closed instead of being guessed from similarity.
    """

    name = supplied_name.strip()
    if not name:
        raise IdentityResolutionError("identity name cannot be empty")

    if usage == IdentityUsage.REPOSITORY:
        if name not in _REPOSITORY_ALIASES:
            raise IdentityResolutionError("unrecognized Project-Enki repository identity")
        return ProductIdentityResolution(
            supplied_name=name,
            usage=usage,
            resolved_name=CANONICAL_REPOSITORY,
            canonical=name == CANONICAL_REPOSITORY,
            historical_source_preserved=False,
        )

    recognized = name == CANONICAL_PROJECT_NAME or name in _HISTORICAL_OR_NONCANONICAL_ALIASES
    if not recognized:
        raise IdentityResolutionError("unrecognized Project-Enki identity; refusing to guess")

    if usage == IdentityUsage.HISTORICAL:
        return ProductIdentityResolution(
            supplied_name=name,
            usage=usage,
            resolved_name=name,
            canonical=name == CANONICAL_PROJECT_NAME,
            historical_source_preserved=True,
        )

    return ProductIdentityResolution(
        supplied_name=name,
        usage=usage,
        resolved_name=CANONICAL_PROJECT_NAME,
        canonical=name == CANONICAL_PROJECT_NAME,
        historical_source_preserved=False,
    )
