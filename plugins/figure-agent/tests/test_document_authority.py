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
COMPETING_AUTHORITY_PHRASES = (
    "active product direction",
    "active direction",
    "canonical direction",
    "active working plan",
    "active roadmap",
    "active handoff plan",
    "active issue record and implementation direction",
)

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


def test_no_other_document_can_claim_active_product_or_plan_authority() -> None:
    canonical_docs = {PLUGIN_ROOT / PRODUCT_DOC, PLUGIN_ROOT / EXECUTION_DOC}
    for path in PLUGIN_ROOT.rglob("*.md"):
        if path in canonical_docs:
            continue
        text = _read(path)
        lowered = text.lower()
        if any(phrase in lowered for phrase in COMPETING_AUTHORITY_PHRASES):
            assert HISTORICAL_STATUS in text, path.relative_to(PLUGIN_ROOT)


def test_canonical_docs_close_known_attribution_and_provenance_edge_cases() -> None:
    product = _read(PLUGIN_ROOT / PRODUCT_DOC)
    execution = _read(PLUGIN_ROOT / EXECUTION_DOC)

    for required in (
        "stable selector ID",
        "Line ranges are review snapshots",
        "render-geometry hash",
        "No fragment may depend on network access",
        "aggregate review-input hash",
        "Test A — reference reconstruction",
        "Test B — semantic synthesis",
        "separately hashed input packet",
        "two independent cold-reproduction tasks",
        "author either the semantic packet or clean-room SVG artifacts",
    ):
        assert required in product

    for required in (
        "tracked editable source",
        "tracked Fig1-family editable source",
        "source commit and tree hash",
        "selector_id:",
        "anchor_start:",
        "coordinate_space: pdf_cm",
        "page_index:",
        "render_geometry_hash:",
        "external URLs",
        "review_input_hash",
        "predeclared comparison protocol",
        "Task 15: Validate clean-room direct-SVG input packets",
        "target_crop_forbidden",
        "blocked_pending_independent_semantic_packet",
        "Run two cold reproductions only for a passing claim",
    ):
        assert required in execution

    assert "fig1_overview_v5f_hybrid_panel_f_pilot" not in execution
    assert "panel_f_fragment" not in execution


def test_canonical_docs_define_failure_first_llm_control() -> None:
    product = _read(PLUGIN_ROOT / PRODUCT_DOC)
    execution = _read(PLUGIN_ROOT / EXECUTION_DOC)

    for required in (
        "Let the LLM propose freely",
        "Failure ontology",
        "Bounded repair contract",
        "Figure production is not Figure Agent product development.",
        "A: raw LLM authoring",
        "B: the same LLM plus Figure Agent contracts and verification",
        "C: the same LLM plus contracts, verification, and bounded repair",
    ):
        assert required in product

    for required in (
        "Failure-First Implementation Plan",
        "failure_corpus.py",
        "failure_ablation.py",
        "quality_search.py or scripts/quality/panel_block_edits.yaml",
    ):
        assert required in execution

    assert "determine whether an LLM can directly author SVG" not in product


def test_canonical_authority_docs_ship_in_cowork_package(tmp_path: Path) -> None:
    zip_path = build_zip(tmp_path)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert PRODUCT_DOC in names
    assert EXECUTION_DOC in names
