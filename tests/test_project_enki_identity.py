from pathlib import Path

import pytest

from nks.enki.product_identity import (
    CANONICAL_PROJECT_NAME,
    CANONICAL_REPOSITORY,
    IdentityResolutionError,
    IdentityUsage,
    resolve_project_enki_identity,
)


def test_current_identity_always_resolves_to_project_enki() -> None:
    for supplied in (
        "Project-Enki",
        "Enki",
        "Enki Knowledge System",
        "Project Enki",
    ):
        resolved = resolve_project_enki_identity(supplied, usage=IdentityUsage.CURRENT)
        assert resolved.resolved_name == "Project-Enki"


def test_historical_identity_is_preserved_without_becoming_current_authority() -> None:
    resolved = resolve_project_enki_identity(
        "Enki Knowledge System",
        usage=IdentityUsage.HISTORICAL,
    )
    assert resolved.resolved_name == "Enki Knowledge System"
    assert resolved.historical_source_preserved is True
    assert resolved.canonical is False


def test_repository_identity_is_separate_from_display_identity() -> None:
    assert CANONICAL_PROJECT_NAME == "Project-Enki"
    assert CANONICAL_REPOSITORY == "nelsonbridge/project-enki"
    assert (
        resolve_project_enki_identity("project-enki", usage=IdentityUsage.REPOSITORY).resolved_name
        == CANONICAL_REPOSITORY
    )


def test_unknown_identity_fails_closed() -> None:
    with pytest.raises(IdentityResolutionError, match="refusing to guess"):
        resolve_project_enki_identity("Project Enki Knowledge Platform")


def test_current_authority_surfaces_use_canonical_name() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    architecture = Path(
        "architecture/enki/enki-canonical-nine-layer-architecture.md"
    ).read_text(encoding="utf-8")

    assert readme.startswith("# Project-Enki\n")
    assert architecture.startswith("# Project-Enki — Canonical Nine-Layer Architecture\n")
