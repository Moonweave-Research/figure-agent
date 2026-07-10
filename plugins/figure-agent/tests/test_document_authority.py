"""Guard the two-document product authority contract."""

from __future__ import annotations

import zipfile
from pathlib import Path

from package_cowork_plugin import build_zip

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]

PRODUCT_MARKER = "<!-- FIGURE_AGENT:PRODUCT_AUTHORITY -->"
EXECUTION_MARKER = "<!-- FIGURE_AGENT:EXECUTION_AUTHORITY -->"
PRODUCT_DOC = "docs/product-spec.md"
EXECUTION_DOC = "docs/execution-plan.md"
HISTORICAL_STATUS = "**Status:** Historical evidence — non-authoritative."

AGENT_ENTRYPOINTS = (
    REPO_ROOT / "README.md",
    PLUGIN_ROOT / "README.md",
    PLUGIN_ROOT / "AGENTS.md",
    PLUGIN_ROOT / "skills" / "figure-agent" / "SKILL.md",
    PLUGIN_ROOT / "docs" / "architecture-overview.md",
)

SUPERSEDED_PRODUCT_DOCS = (
    "docs/quality-kernel-goal.md",
    "docs/architecture-v0.3-snippet-library.md",
    "docs/superpowers/specs/2026-06-21-iteration-first-figure-agent-spec.md",
    "docs/superpowers/specs/2026-06-21-figure-agent-v2-svg-illustrator-design.md",
    "docs/superpowers/specs/2026-06-25-ceiling-loop-design.md",
)

SUPERSEDED_EXECUTION_DOCS = (
    "docs/roadmap-2026-06-manuscript-figures.md",
    "docs/roadmap-2026-07-figure-quality-system.md",
    "docs/architecture-v0.12-quality-search-execution-plan.md",
    "docs/superpowers/plans/2026-07-01-next-agent-execution-waves.md",
    "docs/milestones/2026-07-03-forward-execution-plan-and-status.md",
    "docs/milestones-archive/2026-05-17-quality-state-hardening.md",
    "docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_exactly_two_canonical_product_authority_markers_exist() -> None:
    markdown_files = [REPO_ROOT / "README.md", *PLUGIN_ROOT.rglob("*.md")]
    product_hosts = [path for path in markdown_files if PRODUCT_MARKER in _read(path)]
    execution_hosts = [path for path in markdown_files if EXECUTION_MARKER in _read(path)]

    assert product_hosts == [PLUGIN_ROOT / PRODUCT_DOC]
    assert execution_hosts == [PLUGIN_ROOT / EXECUTION_DOC]


def test_agent_entrypoints_link_both_canonical_documents() -> None:
    for path in AGENT_ENTRYPOINTS:
        text = _read(path)
        assert PRODUCT_DOC in text, path
        assert EXECUTION_DOC in text, path


def test_superseded_product_and_plan_docs_are_explicitly_non_authoritative() -> None:
    for relative_path in (*SUPERSEDED_PRODUCT_DOCS, *SUPERSEDED_EXECUTION_DOCS):
        text = _read(PLUGIN_ROOT / relative_path)
        assert HISTORICAL_STATUS in text, relative_path
        assert PRODUCT_DOC in text, relative_path
        assert EXECUTION_DOC in text, relative_path


def test_canonical_authority_docs_ship_in_cowork_package(tmp_path: Path) -> None:
    zip_path = build_zip(tmp_path)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert PRODUCT_DOC in names
    assert EXECUTION_DOC in names
