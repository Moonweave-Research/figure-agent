"""Guard the single-document Figure Agent authority contract."""

from __future__ import annotations

import zipfile
from pathlib import Path

from package_cowork_plugin import build_zip

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]

AUTHORITY_MARKER = "<!-- FIGURE_AGENT:AUTHORITY -->"
LEGACY_MARKER = "<!-- FIGURE_AGENT:LEGACY_EVIDENCE -->"
AUTHORITY_DOC = "docs/figure-agent.md"
LEGACY_DOCS = ("docs/product-spec.md", "docs/execution-plan.md")
HISTORICAL_STATUS = "**Status:** Historical evidence — non-authoritative."

AGENT_ENTRYPOINTS = (
    REPO_ROOT / "README.md",
    PLUGIN_ROOT / "README.md",
    PLUGIN_ROOT / "AGENTS.md",
    PLUGIN_ROOT / "skills" / "figure-agent" / "SKILL.md",
    PLUGIN_ROOT / "docs" / "architecture-overview.md",
)

SUPERSEDED_DOCS = (
    "docs/quality-kernel-goal.md",
    "docs/architecture-v0.3-snippet-library.md",
    "docs/superpowers/specs/2026-06-21-iteration-first-figure-agent-spec.md",
    "docs/superpowers/specs/2026-06-21-figure-agent-v2-svg-illustrator-design.md",
    "docs/superpowers/specs/2026-06-25-ceiling-loop-design.md",
    "docs/roadmap-2026-06-manuscript-figures.md",
    "docs/roadmap-2026-07-figure-quality-system.md",
    "docs/architecture-v0.12-quality-search-execution-plan.md",
    "docs/superpowers/plans/2026-07-01-next-agent-execution-waves.md",
    "docs/milestones/2026-07-03-forward-execution-plan-and-status.md",
    "docs/milestones-archive/2026-05-17-quality-state-hardening.md",
    "docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md",
)

COMPETING_AUTHORITY_PHRASES = (
    "active product direction",
    "active direction",
    "canonical direction",
    "active working plan",
    "active roadmap",
    "active handoff plan",
    "active issue record and implementation direction",
    "single active product specification",
    "only active forward execution authority",
    "only product and execution authorities",
    "single product and forward-execution authorities",
    "this is the only active forward plan",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_exactly_one_active_authority_marker_exists() -> None:
    markdown_files = [REPO_ROOT / "README.md", *PLUGIN_ROOT.rglob("*.md")]
    authority_hosts = [
        path for path in markdown_files if AUTHORITY_MARKER in _read(path)
    ]

    assert authority_hosts == [PLUGIN_ROOT / AUTHORITY_DOC]


def test_previous_authorities_are_legacy_evidence_in_place() -> None:
    for relative_path in LEGACY_DOCS:
        text = _read(PLUGIN_ROOT / relative_path)
        assert text.startswith(LEGACY_MARKER), relative_path
        assert HISTORICAL_STATUS in text, relative_path
        assert "`docs/figure-agent.md`" in text, relative_path
        assert "Everything below this boundary is quoted historical" in text
        assert "MUST NOT be executed or treated" in text
        assert AUTHORITY_MARKER not in text, relative_path


def test_competing_authority_claims_require_an_earlier_legacy_boundary() -> None:
    authority_path = PLUGIN_ROOT / AUTHORITY_DOC
    for path in PLUGIN_ROOT.rglob("*.md"):
        if path == authority_path:
            continue
        text = _read(path)
        normalized = text.lower()
        claim_offsets = [
            normalized.index(phrase)
            for phrase in COMPETING_AUTHORITY_PHRASES
            if phrase in normalized
        ]
        if not claim_offsets:
            continue

        boundary_offsets = [
            text.index(marker)
            for marker in (LEGACY_MARKER, HISTORICAL_STATUS)
            if marker in text
        ]
        assert boundary_offsets, path
        assert min(boundary_offsets) < min(claim_offsets), path


def test_authoring_execution_binding_documents_are_historical_evidence() -> None:
    for relative_path in (
        "docs/superpowers/plans/2026-07-13-authoring-execution-binding.md",
        "docs/superpowers/specs/2026-07-13-authoring-execution-binding-design.md",
    ):
        text = _read(PLUGIN_ROOT / relative_path)
        assert text.startswith(LEGACY_MARKER), relative_path
        assert HISTORICAL_STATUS in text, relative_path
        assert "`docs/figure-agent.md`" in text, relative_path
        assert "MUST NOT be executed" in text, relative_path


def test_agent_entrypoints_link_the_single_authority() -> None:
    for path in AGENT_ENTRYPOINTS:
        text = _read(path)
        assert AUTHORITY_DOC in text, path


def test_prior_superseded_documents_remain_explicitly_historical() -> None:
    for relative_path in SUPERSEDED_DOCS:
        text = _read(PLUGIN_ROOT / relative_path)
        assert HISTORICAL_STATUS in text, relative_path


def test_authority_defines_product_identity_and_renderer_boundaries() -> None:
    authority = _read(PLUGIN_ROOT / AUTHORITY_DOC)
    normalized = " ".join(authority.replace("**", "").split())

    for required in (
        "Let the LLM propose freely",
        "Figure production is not Figure Agent product development.",
        "TikZ/TeX",
        "SVG is a derived export",
        "Python is the control plane",
        "Direct-SVG generation is not an active backend-development target",
        "not LLM prompt plumbing",
        "automatic physics detection",
        "publication_acceptance: not_claimed",
    ):
        assert required in normalized


def test_authority_binds_the_committed_baseline_and_closed_loop() -> None:
    authority = _read(PLUGIN_ROOT / AUTHORITY_DOC)
    normalized = " ".join(authority.split())

    for required in (
        "c6a28e40",
        "235 targeted baseline tests",
        "context and authoring packet",
        "free LLM authoring",
        "deterministic compile and render",
        "fresh host vision critique",
        "adjudicated actionable finding",
        "exact semantic and source attribution",
        "human-authorized bounded repair packet",
        "fresh post-repair visual and regression review",
        "named human development-baseline verdict",
    ):
        assert required in normalized


def test_authority_defines_comparable_lineage_and_claim_ladder() -> None:
    authority = _read(PLUGIN_ROOT / AUTHORITY_DOC)

    for required in (
        "A** is raw LLM authoring",
        "B** is the same LLM and task plus Figure Agent",
        "C** is the hash-bound child of B",
        "Machine-valid",
        "Visually re-reviewed",
        "Human development accepted",
        "Publication accepted",
        "No lower state implies a higher one.",
        "two materially different figure families",
        "prospectively recorded correction time",
    ):
        assert required in authority


def test_authority_contains_one_ordered_executable_roadmap() -> None:
    authority = _read(PLUGIN_ROOT / AUTHORITY_DOC)

    assert len(authority.splitlines()) < 320
    roadmap_positions = [authority.index(f"### R{index} ") for index in range(6)]
    assert roadmap_positions == sorted(roadmap_positions)
    for required in (
        "Specify the closed-loop attempt state",
        "Connect critique to bounded repair",
        "Require fresh post-repair vision and regression evidence",
        "Make the lifecycle the canonical run path",
        "Cross-family proof and capability promotion",
        "smallest failing test first",
    ):
        assert required in authority


def test_authority_defines_fail_closed_stop_conditions() -> None:
    authority = _read(PLUGIN_ROOT / AUTHORITY_DOC)
    normalized = " ".join(authority.split())

    for required in (
        "attribution is ambiguous, unbound",
        "protected scientific invariants",
        "neighboring-region",
        "introduces a new one",
        "scientific interpretation",
        "accepted/golden promotion",
        "publication judgment",
        "weakening a gate",
        "third generation as repair",
        "retrospective correction time",
    ):
        assert required in normalized.replace("a third generation", "third generation")


def test_single_authority_ships_in_cowork_package(tmp_path: Path) -> None:
    zip_path = build_zip(tmp_path)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert AUTHORITY_DOC in names
    for relative_path in LEGACY_DOCS:
        assert relative_path in names
