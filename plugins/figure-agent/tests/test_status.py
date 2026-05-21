"""Tests for scripts/status.py — infer_stage contract."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import status as status_mod  # noqa: E402
from quality_manifest import CRITIQUE_RUBRIC_VERSION, file_sha256, input_manifest_hash  # noqa: E402
from status import CRITIQUE_REFERENCE_MISSING, compute_critique_state, infer_stage  # noqa: E402
from svg_polish_manifest import (  # noqa: E402
    final_artifact_source_set_hash,
    write_svg_polish_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def stable_style_lock_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep status tests independent from checkout mtimes."""
    style_lock = tmp_path / "polymer-paper-preamble.sty"
    style_lock.write_text("% stable style lock\n", encoding="utf-8")
    old_time = time.time() - 1000
    os.utime(style_lock, (old_time, old_time))
    monkeypatch.setattr(status_mod, "STYLE_LOCK_PATH", style_lock)


def _make_spec(
    directory: Path,
    reference_image: str | None = None,
    accepted: bool | str | None = None,
) -> None:
    reference_line = f"reference_image: {reference_image}\n" if reference_image else ""
    if accepted is None:
        accepted_line = ""
    elif isinstance(accepted, bool):
        accepted_line = f"accepted: {'true' if accepted else 'false'}\n"
    else:
        accepted_line = f"accepted: {accepted}\n"
    content = (
        f"name: {directory.name}\npanels: []\nstyle_profile: polymer-default\n"
        f"{reference_line}"
        f"{accepted_line}"
    )
    (directory / "spec.yaml").write_text(content, encoding="utf-8")
    (directory / "briefing.md").write_text("briefing", encoding="utf-8")


def _critique_input_hash(fig_dir: Path, name: str) -> str:
    spec = status_mod.parse_spec((fig_dir / "spec.yaml").read_text(encoding="utf-8"))
    return input_manifest_hash(
        status_mod._critique_source_paths(fig_dir, name, spec),
        base_dir=REPO_ROOT,
    )


def _write_hashed_critique(
    fig_dir: Path,
    name: str,
    *,
    critique_input_hash: str | None = None,
    generator_version: str | None = None,
    rubric_version: str = CRITIQUE_RUBRIC_VERSION,
    schema: str = "figure-agent.critique.v1.2",
) -> None:
    generator_version = generator_version or file_sha256(
        REPO_ROOT / "scripts" / "critique_brief.py"
    )
    critique_input_hash = critique_input_hash or _critique_input_hash(fig_dir, name)
    (fig_dir / "critique.md").write_text(
        "---\n"
        f"schema: {schema}\n"
        f"fixture: {name}\n"
        "generated_at: 2026-05-17T00:00:00Z\n"
        "generator: critique_brief.py\n"
        f"generator_version: {generator_version}\n"
        f"rubric_version: {rubric_version}\n"
        f"critique_input_hash: {critique_input_hash}\n"
        "verdict: ready\n"
        "audit_enumeration:\n"
        "  structural_completeness:\n"
        "    components:\n"
        "      - component: demo\n"
        "        mount_support: yes\n"
        "        rationale: supported\n"
        "        connections: no connections\n"
        "    missing_from_reference:\n"
        "      - element: none\n"
        "        status: intentional_omission\n"
        "        rationale: not needed\n"
        "  label_target_matching:\n"
        "    - label: demo\n"
        "      nearest_object: demo\n"
        "      intended_target: demo\n"
        "      matches: true\n"
        "      proposed_fix: \"\"\n"
        "  physical_plausibility:\n"
        "    - check: floating_components\n"
        "      finding: no floating components\n"
        "      verdict: convention_acceptable\n"
        "  conceptual_completeness:\n"
        "    - element: none\n"
        "      reference: briefing\n"
        "      severity: NIT\n"
        "      proposed_action: accept_simplification\n"
        "quality_axes:\n"
        "  message_storyline:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: story is clear\n"
        "    evidence: briefing and render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  panel_role_coherence:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: panel role is clear\n"
        "    evidence: panel A\n"
        "    panel_roles:\n"
        "      - panel_id: A\n"
        "        role: setup\n"
        "        role_quality: clear\n"
        "        rationale: panel introduces the setup\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  subregion_integration:\n"
        "    verdict: not_applicable\n"
        "    confidence: low\n"
        "    rationale: \"\"\n"
        "    evidence: \"\"\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  component_fidelity:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: components are recognizable\n"
        "    evidence: structural audit\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  scientific_plausibility:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: no visible scientific conflict\n"
        "    evidence: briefing invariant\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  composition_layout:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: layout is readable\n"
        "    evidence: render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  label_annotation_semantics:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: labels match targets\n"
        "    evidence: label audit\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  journal_polish:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: polish is adequate\n"
        "    evidence: render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  reference_fidelity:\n"
        "    verdict: not_applicable\n"
        "    confidence: low\n"
        "    rationale: \"\"\n"
        "    evidence: \"\"\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  publication_readiness:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: all applicable quality axes pass\n"
        "    evidence: quality axis summary\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "panels: []\n"
        "findings: []\n"
        "---\n"
        "# Vision Critique\n",
        encoding="utf-8",
    )


def test_stage_0_missing_directory(tmp_path: Path) -> None:
    result = infer_stage(tmp_path / "nonexistent")
    assert result["stage"] == 0


def test_hash_fresh_critique_becomes_stale_when_visual_clash_report_changes(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "ref_fig"
    fig_dir.mkdir()
    (fig_dir / "reference").mkdir()
    (fig_dir / "build").mkdir()
    _make_spec(fig_dir, reference_image="reference/ref.png")
    (fig_dir / "ref_fig.tex").write_text("% tikz", encoding="utf-8")
    (fig_dir / "reference" / "ref.png").write_bytes(b"\x89PNG")
    visual_clash = fig_dir / "build" / "visual_clash.json"
    visual_clash.write_text(
        '{"fixture":"ref_fig","render_pdf":"build/ref_fig.pdf","candidates":[],"total":0}\n',
        encoding="utf-8",
    )
    _write_hashed_critique(fig_dir, "ref_fig", schema="figure-agent.critique.v1.7")

    assert compute_critique_state(fig_dir, "ref_fig") == status_mod.CRITIQUE_FRESH

    visual_clash.write_text(
        (
            '{"fixture":"ref_fig","render_pdf":"build/ref_fig.pdf",'
            '"candidates":[{"id":"VC001"}],"total":1}\n'
        ),
        encoding="utf-8",
    )

    assert compute_critique_state(fig_dir, "ref_fig") == status_mod.CRITIQUE_STALE


def test_stage_1_spec_only_empty_previews(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    previews = fig_dir / "previews"
    previews.mkdir()
    result = infer_stage(fig_dir)
    assert result["stage"] == 1


def test_stage_2_tex_stale_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    # Make tex newer than pdf
    old_time = time.time() - 100
    os.utime(pdf, (old_time, old_time))
    new_time = time.time() - 10
    os.utime(tex, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 2


def test_stage_2_tex_no_build_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    result = infer_stage(fig_dir)
    assert result["stage"] == 2


def test_stage_2_missing_briefing_does_not_suggest_compile(tmp_path: Path) -> None:
    fig_dir = tmp_path / "legacy_authored"
    fig_dir.mkdir()
    (fig_dir / "legacy_authored.tex").write_text("% tikz", encoding="utf-8")

    result = infer_stage(fig_dir)

    assert result["stage"] == 2
    assert "missing_briefing" in result["notes"]
    assert "briefing.md" in result["next"]
    assert "/fig_compile" not in result["next"]


def test_stage_3_fresh_pdf_no_exports(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    # All sources must be older than the build pdf
    old_time = time.time() - 100
    os.utime(tex, (old_time, old_time))
    os.utime(fig_dir / "briefing.md", (old_time, old_time))
    os.utime(fig_dir / "spec.yaml", (old_time, old_time))
    new_time = time.time() - 10
    os.utime(pdf, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 3


def test_stage_3_missing_briefing_does_not_suggest_export(tmp_path: Path) -> None:
    fig_dir = tmp_path / "legacy_built"
    fig_dir.mkdir()
    tex = fig_dir / "legacy_built.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    build_pdf = build_dir / "legacy_built.pdf"
    build_pdf.write_bytes(b"%PDF")
    old_time = time.time() - 100
    fresh_time = time.time() - 10
    os.utime(tex, (old_time, old_time))
    os.utime(build_pdf, (fresh_time, fresh_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 3
    assert "missing_briefing" in result["notes"]
    assert "briefing.md" in result["next"]
    assert "/fig_export" not in result["next"]


def test_stage_3_panel_reference_missing_critique_redirects_to_fig_critique(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "panel_ref_fig"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "\n".join(
            [
                "name: panel_ref_fig",
                "style_profile: polymer-default",
                "panels:",
                "  - id: A",
                "    reference_image: reference/panel_a.png",
                "    bbox_pdf_cm: [0, 0, 1, 1]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (fig_dir / "briefing.md").write_text("briefing", encoding="utf-8")
    (fig_dir / "panel_ref_fig.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "panel_a.png").write_bytes(b"\x89PNG")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / "panel_ref_fig.pdf").write_bytes(b"%PDF")

    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / "panel_ref_fig.tex",
        reference / "panel_a.png",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(build_dir / "panel_ref_fig.pdf", (fresh_time, fresh_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 3
    assert "critique_missing" in result["notes"]
    assert "/fig_critique" in result["next"]
    assert "before /fig_export" in result["next"]


def test_stage_3_reference_stale_critique_redirects_to_fig_critique(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "stale_critique_fig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / "stale_critique_fig.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / "stale_critique_fig.pdf").write_bytes(b"%PDF")
    (fig_dir / "critique.md").write_text("old critique", encoding="utf-8")

    old_time = time.time() - 100
    middle_time = time.time() - 50
    fresh_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / "stale_critique_fig.tex",
        reference / "golden.png",
    ):
        os.utime(path, (middle_time, middle_time))
    os.utime(fig_dir / "critique.md", (old_time, old_time))
    os.utime(build_dir / "stale_critique_fig.pdf", (fresh_time, fresh_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 3
    assert "critique_stale" in result["notes"]
    assert "/fig_critique" in result["next"]
    assert "before /fig_export" in result["next"]


def test_hash_metadata_keeps_matching_critique_fresh_even_when_mtime_is_old(
    tmp_path: Path,
) -> None:
    name = "hash_fresh_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / f"{name}.pdf").write_bytes(b"%PDF")
    _write_hashed_critique(fig_dir, name)

    old_time = time.time() - 100
    source_time = time.time() - 10
    os.utime(fig_dir / "critique.md", (old_time, old_time))
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (source_time, source_time))
    os.utime(build_dir / f"{name}.pdf", (source_time, source_time))

    assert compute_critique_state(fig_dir, name) == "FRESH"


def test_hash_metadata_marks_current_v1_4_critique_fresh(
    tmp_path: Path,
) -> None:
    name = "hash_v14_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    _write_hashed_critique(fig_dir, name, schema="figure-agent.critique.v1.4")

    assert compute_critique_state(fig_dir, name) == "FRESH"


def test_hash_metadata_marks_critique_stale_when_input_content_changes(
    tmp_path: Path,
) -> None:
    name = "hash_changed_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / f"{name}.pdf").write_bytes(b"%PDF")
    old_hash = _critique_input_hash(fig_dir, name)
    _write_hashed_critique(fig_dir, name, critique_input_hash=old_hash)
    (fig_dir / "briefing.md").write_text("changed briefing", encoding="utf-8")

    source_time = time.time() - 100
    critique_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (source_time, source_time))
    os.utime(fig_dir / "critique.md", (critique_time, critique_time))
    os.utime(build_dir / f"{name}.pdf", (critique_time, critique_time))

    assert compute_critique_state(fig_dir, name) == "STALE"


def test_hash_metadata_marks_critique_stale_when_rubric_version_changes(
    tmp_path: Path,
) -> None:
    name = "hash_rubric_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    _write_hashed_critique(
        fig_dir,
        name,
        rubric_version="figure-agent.critique-rubric.v0",
    )

    assert compute_critique_state(fig_dir, name) == "STALE"


def test_hash_metadata_marks_critique_stale_when_generator_version_changes(
    tmp_path: Path,
) -> None:
    name = "hash_generator_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    _write_hashed_critique(
        fig_dir,
        name,
        generator_version="sha256:00000000000000000000000000000000",
    )

    assert compute_critique_state(fig_dir, name) == "STALE"


def test_malformed_critique_frontmatter_falls_back_to_mtime(
    tmp_path: Path,
) -> None:
    name = "malformed_frontmatter_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / "critique.md").write_text(
        "---\n"
        "generator_version: sha256:bad\n"
        "rubric_version: figure-agent.critique-rubric.v1\n"
        "critique_input_hash: [unterminated\n"
        "---\n"
        "# Vision Critique\n",
        encoding="utf-8",
    )

    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(fig_dir / "critique.md", (fresh_time, fresh_time))

    assert compute_critique_state(fig_dir, name) == "FRESH"


@pytest.mark.parametrize(
    "authoring_doc",
    (
        "authoring_contract.md",
        "reference/reference_pack.md",
        "authoring_plan.md",
        "theory_guard.md",
        "subregion_iteration_log.md",
    ),
)
def test_stage_3_authoring_doc_stale_critique_redirects_to_fig_critique(
    tmp_path: Path,
    authoring_doc: str,
) -> None:
    name = "stale_authoring_context_fig"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / f"{name}.pdf").write_bytes(b"%PDF")
    (fig_dir / "critique.md").write_text("critique from old authoring context", encoding="utf-8")

    authoring_path = fig_dir / authoring_doc
    authoring_path.parent.mkdir(parents=True, exist_ok=True)
    authoring_path.write_text("updated authoring context", encoding="utf-8")

    old_time = time.time() - 100
    critique_time = time.time() - 50
    fresh_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(fig_dir / "critique.md", (critique_time, critique_time))
    os.utime(authoring_path, (fresh_time, fresh_time))
    os.utime(build_dir / f"{name}.pdf", (fresh_time, fresh_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 3
    assert "critique_stale" in result["notes"]
    assert "/fig_critique" in result["next"]


def _make_fresh_exports(fig_dir: Path, name: str) -> None:
    """Create all-four exports + matching build PDF so compute_export_state → FRESH."""
    pdf_bytes = b"%PDF-1.4 stub"
    build_dir = fig_dir / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / f"{name}.pdf").write_bytes(pdf_bytes)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir(exist_ok=True)
    (exports_dir / f"{name}.pdf").write_bytes(pdf_bytes)
    (exports_dir / f"{name}.svg").write_bytes(b"<svg/>")
    (exports_dir / f"{name}.tif").write_bytes(b"TIFF")
    (exports_dir / f"{name}.png").write_bytes(b"\x89PNG")


def _make_status_ready_fixture(fig_dir: Path, *, accepted: bool | None = None) -> None:
    name = fig_dir.name
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=accepted)
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    (fig_dir / "critique.md").write_text("# critique\n", encoding="utf-8")
    _make_fresh_exports(fig_dir, name)


def _write_final_artifact_spec(
    fig_dir: Path,
    kind: str = "polished_svg",
    *,
    manifest: str = "polish/svg_polish_manifest.yaml",
) -> None:
    existing = (fig_dir / "spec.yaml").read_text(encoding="utf-8")
    (fig_dir / "spec.yaml").write_text(
        existing
        + "final_artifact:\n"
        f"  kind: {kind}\n"
        f"  manifest: {manifest}\n",
        encoding="utf-8",
    )


def _append_manifest_only_final_artifact_spec(fig_dir: Path) -> None:
    existing = (fig_dir / "spec.yaml").read_text(encoding="utf-8")
    (fig_dir / "spec.yaml").write_text(
        existing
        + "final_artifact:\n"
        "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )


def _write_polish_manifest(
    fig_dir: Path,
    *,
    semantic_change_declared: bool = False,
    backport_required: bool = False,
) -> None:
    name = fig_dir.name
    polish = fig_dir / "polish"
    polish.mkdir(exist_ok=True)
    (polish / f"{name}.polished.svg").write_text(
        "<svg><text>polished</text></svg>\n",
        encoding="utf-8",
    )
    (polish / "svg_polish_audit.md").write_text("# Audit\n", encoding="utf-8")
    manifest = {
        "schema": "figure-agent.svg-polish-manifest.v1",
        "fixture": name,
        "base": {
            "source_set_hash": final_artifact_source_set_hash(
                fig_dir,
                name,
                style_lock_path=status_mod.STYLE_LOCK_PATH,
            ),
            "source_tex_hash": file_sha256(fig_dir / f"{name}.tex"),
            "briefing_hash": file_sha256(fig_dir / "briefing.md"),
            "spec_hash": file_sha256(fig_dir / "spec.yaml"),
            "generated_svg_hash": file_sha256(fig_dir / "exports" / f"{name}.svg"),
            "export_pdf_hash": file_sha256(fig_dir / "exports" / f"{name}.pdf"),
            "critique_hash": file_sha256(fig_dir / "critique.md"),
        },
        "polished": {
            "path": f"polish/{name}.polished.svg",
            "polished_svg_hash": file_sha256(polish / f"{name}.polished.svg"),
            "audit_hash": file_sha256(polish / "svg_polish_audit.md"),
            "editor": "human",
            "toolchain": [{"name": "Inkscape", "version": "1.4"}],
            "edit_classes": ["label_micro_position"],
            "semantic_change_declared": semantic_change_declared,
            "backport_required": backport_required,
        },
        "provenance": {
            "reviewer": "author",
            "reviewed_at": "2026-05-19T00:00:00Z",
            "notes": "visual polish",
        },
    }
    write_svg_polish_manifest(polish / "svg_polish_manifest.yaml", manifest)


def _mark_sources_older_than_outputs(fig_dir: Path) -> None:
    name = fig_dir.name
    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(fig_dir / "build" / f"{name}.pdf", (fresh_time, fresh_time))
    for path in (fig_dir / "exports").iterdir():
        os.utime(path, (fresh_time, fresh_time))


def test_final_artifact_state_none_without_polish_opt_in(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "plain_final"
    _make_status_ready_fixture(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "NONE"
    assert result["final_artifact_kind"] == "generated_export"
    assert result["final_artifact_path"] == "exports/plain_final.svg"
    assert result["workflow_ready"] is True


def test_final_artifact_generated_export_kind_keeps_current_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "generated_final"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir, kind="generated_export")
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "NONE"
    assert result["final_artifact_kind"] == "generated_export"
    assert result["workflow_ready"] is True


def test_stray_polish_manifest_without_opt_in_does_not_change_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "stray_polish"
    _make_status_ready_fixture(fig_dir)
    _write_polish_manifest(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "NONE"
    assert "final_artifact" not in ",".join(result["notes"])
    assert result["workflow_ready"] is True


def test_final_artifact_block_without_kind_keeps_generated_export_behavior(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "manifest_only_final_status"
    _make_status_ready_fixture(fig_dir)
    _append_manifest_only_final_artifact_spec(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "NONE"
    assert result["final_artifact_kind"] == "generated_export"
    assert "final_artifact" not in ",".join(result["notes"])


@pytest.mark.parametrize(
    "final_artifact_yaml",
    (
        "final_artifact: []\n",
        "final_artifact:\n  kind: polished_svg\n",
        "final_artifact:\n  kind: polished_svg\n  manifest: ''\n",
    ),
)
def test_invalid_final_artifact_shapes_report_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    final_artifact_yaml: str,
) -> None:
    fig_dir = tmp_path / "invalid_final_shape"
    _make_status_ready_fixture(fig_dir)
    existing = (fig_dir / "spec.yaml").read_text(encoding="utf-8")
    (fig_dir / "spec.yaml").write_text(existing + final_artifact_yaml, encoding="utf-8")
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]


def test_declared_polished_svg_missing_manifest_reports_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "missing_polish"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "MISSING"
    assert "final_artifact_missing" in result["notes"]
    assert result["final_artifact_path"] == "polish/svg_polish_manifest.yaml"
    assert "final artifact is missing" in result["next"]
    assert result["workflow_ready"] is True


def test_declared_polished_svg_malformed_manifest_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "invalid_polish"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    polish = fig_dir / "polish"
    polish.mkdir()
    (polish / "svg_polish_manifest.yaml").write_text("schema: [unterminated\n", encoding="utf-8")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "final artifact is invalid" in result["next"]


def test_declared_polished_svg_malformed_manifest_reports_invalid_when_path_says_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "invalidMissingName"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    polish = fig_dir / "polish"
    polish.mkdir()
    (polish / "svg_polish_manifest.yaml").write_text("schema: [unterminated\n", encoding="utf-8")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "final_artifact_missing" not in result["notes"]
    assert "final artifact is invalid" in result["next"]


def test_declared_polished_svg_rejects_noncanonical_manifest_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "custom_manifest_polish"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir, manifest="polish/custom_manifest.yaml")
    _write_polish_manifest(fig_dir)
    custom_manifest = fig_dir / "polish" / "custom_manifest.yaml"
    (fig_dir / "polish" / "svg_polish_manifest.yaml").rename(custom_manifest)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "INVALID"
    assert result["final_artifact_path"] == "polish/custom_manifest.yaml"


def test_malformed_spec_reports_final_artifact_invalid_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_spec_final"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_unknown_style_profile_with_malformed_panels_does_not_crash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_style_panels"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "style_profile: unknown-profile\npanels:\n  - not-a-mapping\n",
        encoding="utf-8",
    )
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "style_profile_unknown" in result["notes"]
    assert result["stage"] == 4
    assert result["workflow_ready"] is False
    assert "style_profile" in result["next"]


def test_style_profile_unknown_takes_precedence_over_final_artifact_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_style_missing_final"
    _make_status_ready_fixture(fig_dir, accepted=True)
    spec = fig_dir / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "style_profile: future-profile\n"
        + "final_artifact:\n"
        + "  kind: polished_svg\n"
        + "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "style_profile_unknown" in result["notes"]
    assert "final_artifact_missing" in result["notes"]
    assert "style_profile" in result["next"]
    assert "final artifact is missing" not in result["next"]


def test_legacy_spec_parse_error_does_not_become_final_artifact_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_bbox_legacy"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "name: bad_bbox_legacy\n"
        "panels:\n"
        "  - id: A\n"
        "    bbox_pdf_cm: [1, 1, 0, 0]\n",
        encoding="utf-8",
    )
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "NONE"
    assert "final_artifact_invalid" not in result["notes"]
    assert "fix malformed" in result["next"]


def test_unrelated_semantic_spec_error_does_not_invalidate_valid_final_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_bbox_with_final"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "name: bad_bbox_with_final\n"
        "panels:\n"
        "  - id: A\n"
        "    bbox_pdf_cm: [1, 1, 0, 0]\n"
        "final_artifact:\n"
        "  kind: polished_svg\n"
        "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "MISSING"
    assert "final_artifact_missing" in result["notes"]
    assert "final_artifact_invalid" not in result["notes"]
    assert "fix malformed" in result["next"]


def test_legacy_malformed_yaml_does_not_become_final_artifact_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_legacy"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("accepted: [unterminated\n", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "NONE"
    assert "final_artifact_invalid" not in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_top_level_final_artifact_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_quoted_top_level_final_artifact_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_quoted_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text('"final_artifact": [unterminated\n', encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_single_quoted_top_level_final_artifact_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_single_quoted_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("'final_artifact': [unterminated\n", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_indented_top_level_final_artifact_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_indented_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("  final_artifact: [unterminated\n", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_flow_style_top_level_final_artifact_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_flow_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "{final_artifact: {kind: polished_svg, manifest: polish/svg_polish_manifest.yaml}, "
        "accepted: [unterminated\n",
        encoding="utf-8",
    )
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_flow_style_later_top_level_final_artifact_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_flow_later_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "{accepted: true, final_artifact: [unterminated\n",
        encoding="utf-8",
    )
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_yaml_with_nested_final_artifact_does_not_become_final_artifact_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_yaml_nested_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "metadata:\n  final_artifact: [unterminated\n",
        encoding="utf-8",
    )
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "NONE"
    assert "final_artifact_invalid" not in result["notes"]
    assert "fix malformed" in result["next"]


@pytest.mark.parametrize(
    "spec_text",
    (
        '{note: "mentions final_artifact only in value", accepted: [unterminated\n',
        "{metadata: {final_artifact: {kind: polished_svg}}, accepted: [unterminated\n",
        "{metadata:{x:1,final_artifact:{kind:polished_svg}},accepted:[unterminated\n",
    ),
)
def test_malformed_flow_yaml_with_non_root_final_artifact_does_not_become_final_artifact_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    spec_text: str,
) -> None:
    fig_dir = tmp_path / "bad_yaml_flow_nested_final_artifact"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(spec_text, encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "NONE"
    assert "final_artifact_invalid" not in result["notes"]
    assert "fix malformed" in result["next"]


def test_invalid_utf8_spec_reports_spec_parse_error_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_utf8_status"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_bytes(b"accepted: true\n\xff\n")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "NONE"
    assert "fix malformed" in result["next"]


@pytest.mark.parametrize(
    "spec_text",
    (
        "# note: final_artifact handled elsewhere\naccepted: [unterminated\n",
        "not_final_artifact_reason: keep\naccepted: [unterminated\n",
    ),
)
def test_malformed_yaml_with_final_artifact_substring_does_not_become_final_artifact_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    spec_text: str,
) -> None:
    fig_dir = tmp_path / "bad_yaml_substring_legacy"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(spec_text, encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    _make_fresh_exports(fig_dir, fig_dir.name)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert "spec_parse_error" in result["notes"]
    assert result["final_artifact_state"] == "NONE"
    assert "final_artifact_invalid" not in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_spec_without_tex_routes_to_spec_fix_first(tmp_path: Path) -> None:
    fig_dir = tmp_path / "bad_spec_unauthored"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")

    result = infer_stage(fig_dir)

    assert result["stage"] == 1
    assert "spec_parse_error" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_spec_with_tex_routes_to_spec_fix_first(tmp_path: Path) -> None:
    fig_dir = tmp_path / "bad_spec_authored"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")

    result = infer_stage(fig_dir)

    assert result["stage"] == 2
    assert "spec_parse_error" in result["notes"]
    assert "fix malformed" in result["next"]


def test_malformed_spec_with_fresh_build_routes_to_spec_fix_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "bad_spec_built"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fig_dir / "briefing.md").write_text("brief", encoding="utf-8")
    (fig_dir / f"{fig_dir.name}.tex").write_text("% source\n", encoding="utf-8")
    build = fig_dir / "build"
    build.mkdir()
    (build / f"{fig_dir.name}.pdf").write_bytes(b"%PDF")
    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (fig_dir / "spec.yaml", fig_dir / "briefing.md", fig_dir / f"{fig_dir.name}.tex"):
        os.utime(path, (old_time, old_time))
    os.utime(build / f"{fig_dir.name}.pdf", (fresh_time, fresh_time))
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "MISSING")

    result = infer_stage(fig_dir)

    assert result["stage"] == 3
    assert "spec_parse_error" in result["notes"]
    assert "fix malformed" in result["next"]


def test_invalid_final_artifact_kind_blocks_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "invalid_kind_polish"
    _make_status_ready_fixture(fig_dir, accepted=True)
    _write_final_artifact_spec(fig_dir, kind="raster_polish")
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "final artifact is invalid" in result["next"]
    assert result["workflow_ready"] is True
    assert result["golden_ready"] is True
    assert result["release_ready"] is False
    assert result["final_ready"] is False


def test_declared_polished_svg_stale_manifest_reports_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "stale_polish"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    (fig_dir / "briefing.md").write_text("changed briefing", encoding="utf-8")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "STALE"
    assert "final_artifact_stale" in result["notes"]
    assert "exports are stale" in result["next"]


def test_declared_polished_svg_with_backport_reports_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "blocked_polish"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir, backport_required=True)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "BLOCKED"
    assert "final_artifact_blocked" in result["notes"]
    assert "semantic backport" in result["next"]


@pytest.mark.parametrize(
    ("state_case", "expected_next_text"),
    (
        ("missing", "final artifact is missing"),
        ("invalid", "final artifact is invalid"),
        ("stale", "final artifact is stale"),
        ("blocked", "semantic backport"),
    ),
)
def test_declared_polished_svg_issue_takes_precedence_over_not_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state_case: str,
    expected_next_text: str,
) -> None:
    fig_dir = tmp_path / f"{state_case}_not_accepted"
    _make_status_ready_fixture(fig_dir, accepted=False)
    _write_final_artifact_spec(fig_dir)
    if state_case == "missing":
        pass
    elif state_case == "invalid":
        polish = fig_dir / "polish"
        polish.mkdir()
        (polish / "svg_polish_manifest.yaml").write_text(
            "schema: [unterminated\n",
            encoding="utf-8",
        )
    elif state_case == "stale":
        _write_polish_manifest(fig_dir)
        (fig_dir / "polish" / "svg_polish_audit.md").write_text(
            "# Audit changed\n",
            encoding="utf-8",
        )
    else:
        _write_polish_manifest(fig_dir, backport_required=True)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert expected_next_text in result["next"]
    assert "accepted: true" not in result["next"]


@pytest.mark.parametrize(
    "relative_path",
    ("polish/missing_polish_input.polished.svg", "polish/svg_polish_audit.md"),
)
def test_declared_polished_svg_missing_polish_inputs_report_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
) -> None:
    fig_dir = tmp_path / "missing_polish_input"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    (fig_dir / relative_path).unlink()
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "MISSING"
    assert "final_artifact_missing" in result["notes"]
    assert result["final_artifact_path"] == relative_path
    assert "final artifact is missing" in result["next"]


def test_declared_polished_svg_missing_provenance_reports_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "invalid_polish_provenance"
    _make_status_ready_fixture(fig_dir)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    del data["provenance"]["reviewed_at"]
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "INVALID"
    assert "final_artifact_invalid" in result["notes"]
    assert "final artifact is invalid" in result["next"]


def test_declared_polished_svg_matching_manifest_reports_fresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "fresh_polish"
    _make_status_ready_fixture(fig_dir, accepted=True)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "FRESH"
    assert result["final_artifact_kind"] == "polished_svg"
    assert result["final_artifact_path"] == "polish/fresh_polish.polished.svg"
    assert result["workflow_ready"] is True
    assert result["golden_ready"] is True
    assert result["release_ready"] is True
    assert result["final_ready"] is True


def test_declared_polished_svg_stale_blocks_release_not_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fig_dir = tmp_path / "release_polish"
    _make_status_ready_fixture(fig_dir, accepted=True)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    (fig_dir / "polish" / "svg_polish_audit.md").write_text("# Audit changed\n", encoding="utf-8")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_state"] == "STALE"
    assert "final artifact is stale" in result["next"]
    assert result["workflow_ready"] is True
    assert result["golden_ready"] is True
    assert result["release_ready"] is False
    assert result["final_ready"] is False


def test_stage_4_export_present_critique_stale_redirects_to_fig_critique(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "stale_critique_stage4"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    for ext in (".pdf", ".svg", ".tif", ".png"):
        (exports_dir / f"{name}{ext}").write_bytes(b"stub")
    (fig_dir / "critique.md").write_text("old critique", encoding="utf-8")
    monkeypatch.setattr(sys.modules["status"], "compute_export_state", lambda *_: "FRESH")

    old_time = time.time() - 100
    middle_time = time.time() - 50
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (middle_time, middle_time))
    os.utime(fig_dir / "critique.md", (old_time, old_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 4
    assert "critique_stale" in result["notes"]
    assert "/fig_critique" in result["next"]


def test_stage_4_critique_required_takes_priority_over_not_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "critique_vs_accepted"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png", accepted=False)
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    for ext in (".pdf", ".svg", ".tif", ".png"):
        (exports_dir / f"{name}{ext}").write_bytes(b"stub")
    monkeypatch.setattr(sys.modules["status"], "compute_export_state", lambda *_: "FRESH")

    old_time = time.time() - 100
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (old_time, old_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 4
    assert "critique_missing" in result["notes"]
    assert "/fig_critique" in result["next"]
    assert "not accepted" not in result["next"]


def test_panel_reference_image_missing_emits_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "missing_panel_ref"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "\n".join(
            [
                "name: missing_panel_ref",
                "style_profile: polymer-default",
                "panels:",
                "  - id: A",
                "    reference_image: reference/nonexistent.png",
                "    bbox_pdf_cm: [0, 0, 1, 1]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (fig_dir / "briefing.md").write_text("briefing", encoding="utf-8")

    result = infer_stage(fig_dir)

    assert "panel_reference_image_missing" in result["notes"]


def test_stage_4_partial_export_svg_only(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert "partial_export" in result["notes"]


def test_stage_4_partial_export_next_redirects_to_re_export(tmp_path: Path) -> None:
    """A partial export must steer the user back to /fig_export, not present
    "done" so they think the figure is finished."""
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert "partial_export" in result["notes"]
    assert "/fig_export" in result["next"]
    assert "done" not in result["next"]


def test_stage_4_stale_takes_priority_over_partial(tmp_path: Path) -> None:
    """When sources are newer than the (partial) export, the stale signal
    wins because regenerating exports is the unconditional next action."""
    import os
    import time

    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    briefing = fig_dir / "briefing.md"
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    svg = exports_dir / "myfig.svg"
    svg.write_bytes(b"<svg/>")
    old = time.time() - 100
    for path in (svg, briefing):
        os.utime(path, (old, old))
    new = time.time() - 5
    os.utime(tex, (new, new))
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert "partial_export" in result["notes"]
    assert "stale_export" in result["notes"]
    assert "/fig_compile" in result["next"]


def test_stage_4_all_four_exports_no_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.pdf").write_bytes(b"%PDF")
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    (exports_dir / "myfig.tif").write_bytes(b"TIFF")
    (exports_dir / "myfig.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert "partial_export" not in result["notes"]


def test_stage_4_missing_briefing_does_not_report_done(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "legacy_exported"
    fig_dir.mkdir()
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "legacy_exported.pdf").write_bytes(b"%PDF")
    (exports_dir / "legacy_exported.svg").write_bytes(b"<svg/>")
    (exports_dir / "legacy_exported.tif").write_bytes(b"TIFF")
    (exports_dir / "legacy_exported.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["stage"] == 4
    assert "missing_briefing" in result["notes"]
    assert "briefing.md" in result["next"]
    assert "done" not in result["next"]


def test_stage_2_briefing_newer_than_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    briefing = fig_dir / "briefing.md"
    briefing.write_text("# briefing", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    old_time = time.time() - 100
    os.utime(tex, (old_time, old_time))
    os.utime(pdf, (old_time + 10, old_time + 10))
    new_time = time.time() - 5
    os.utime(briefing, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 2
    assert ("build_pdf", "stale") in result["checks"]


def test_stage_4_stale_export_when_source_newer(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    briefing = fig_dir / "briefing.md"
    briefing.write_text("# briefing", encoding="utf-8")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    pdf = exports_dir / "myfig.pdf"
    svg = exports_dir / "myfig.svg"
    tif = exports_dir / "myfig.tif"
    png = exports_dir / "myfig.png"
    for path, content in (
        (pdf, b"%PDF"),
        (svg, b"<svg/>"),
        (tif, b"TIFF"),
        (png, b"\x89PNG"),
    ):
        path.write_bytes(content)
    old_time = time.time() - 100
    for path in (pdf, svg, tif, png, briefing):
        os.utime(path, (old_time, old_time))
    new_time = time.time() - 5
    os.utime(tex, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert "stale_export" in result["notes"]
    assert "partial_export" not in result["notes"]
    assert "/fig_compile" in result["next"]
    assert "done" not in result["next"]


def test_stage_4_stale_export_and_stale_critique_keeps_critique_in_next(
    tmp_path: Path,
) -> None:
    name = "stale_export_and_critique"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    (fig_dir / "critique.md").write_text("old critique", encoding="utf-8")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    for ext in (".pdf", ".svg", ".tif", ".png"):
        (exports_dir / f"{name}{ext}").write_bytes(b"stub")

    old_time = time.time() - 100
    middle_time = time.time() - 50
    fresh_time = time.time() - 5
    for path in exports_dir.iterdir():
        os.utime(path, (old_time, old_time))
    os.utime(fig_dir / "critique.md", (middle_time, middle_time))
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        reference / "golden.png",
    ):
        os.utime(path, (fresh_time, fresh_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 4
    assert "stale_export" in result["notes"]
    assert "critique_stale" in result["notes"]
    assert "/fig_compile" in result["next"]
    assert "/fig_critique" in result["next"]
    assert "/fig_export" in result["next"]


def test_stage_4_export_substate_stale_redirects_to_fig_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Content-stale exports must not present the figure as done when all
    mtimes are fresh. export_freshness already owns the PDF content hash;
    status.py must honor that substate in its user-facing Next hint.
    """
    import status as status_mod

    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / "myfig.pdf").write_bytes(b"%PDF build")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    for fname, content in (
        ("myfig.pdf", b"%PDF stale export"),
        ("myfig.svg", b"<svg/>"),
        ("myfig.tif", b"TIFF"),
        ("myfig.png", b"\x89PNG"),
    ):
        (exports_dir / fname).write_bytes(content)

    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (tex, fig_dir / "briefing.md", fig_dir / "spec.yaml"):
        os.utime(path, (old_time, old_time))
    for path in exports_dir.iterdir():
        os.utime(path, (fresh_time, fresh_time))

    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "STALE")

    result = status_mod.infer_stage(fig_dir)

    assert result["stage"] == 4
    assert result["exports_substate"] == "STALE"
    assert "stale_export" in result["notes"]
    assert "/fig_export" in result["next"]
    assert "/fig_compile" not in result["next"]
    assert "done" not in result["next"]


def test_stage_4_coordinate_hints_newer_stales_critique_not_exports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """coordinate_hints.yaml is critique/reference context, not a render source."""
    import status as status_mod

    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    (fig_dir / "critique.md").write_text("old critique", encoding="utf-8")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    for fname, content in (
        ("myfig.pdf", b"%PDF"),
        ("myfig.svg", b"<svg/>"),
        ("myfig.tif", b"TIFF"),
        ("myfig.png", b"\x89PNG"),
    ):
        (exports_dir / fname).write_bytes(content)
    old_time = time.time() - 100
    for path in (
        tex,
        fig_dir / "briefing.md",
        fig_dir / "spec.yaml",
        reference / "golden.png",
        fig_dir / "critique.md",
    ):
        os.utime(path, (old_time, old_time))
    for fname in ("myfig.pdf", "myfig.svg", "myfig.tif", "myfig.png"):
        os.utime(exports_dir / fname, (old_time, old_time))
    hints = fig_dir / "coordinate_hints.yaml"
    hints.write_text("metadata:\n  extraction_version: '0.3'\n", encoding="utf-8")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["stage"] == 4
    assert "critique_stale" in result["notes"]
    assert "stale_export" not in result["notes"]
    assert "/fig_critique" in result["next"]
    assert "/fig_compile" not in result["next"]


def test_missing_briefing_blocks_stage_advance(tmp_path: Path) -> None:
    fig = tmp_path / "missing_briefing"
    fig.mkdir()
    _make_spec(fig)
    (fig / "briefing.md").unlink()
    (fig / "missing_briefing.tex").write_text("tex", encoding="utf-8")
    build = fig / "build"
    build.mkdir()
    (build / "missing_briefing.pdf").write_bytes(b"%PDF")

    result = infer_stage(fig)

    assert result["stage"] == 1
    assert "missing_briefing" in result["notes"]
    assert "briefing.md" in result["next"]
    assert "/fig_review" not in result["next"]


def test_reference_image_existing_is_not_treated_as_selected_preview(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden_target_001.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden_target_001.png").write_bytes(b"\x89PNG")
    (fig_dir / "previews").mkdir()

    result = infer_stage(fig_dir)

    assert result["stage"] == 1
    assert ("reference_image", "reference/golden_target_001.png") in result["checks"]
    assert "selected_preview_missing" not in result["notes"]
    assert "reference_image_missing" not in result["notes"]


def test_coordinate_hints_missing_when_reference_present(tmp_path: Path) -> None:
    """If reference_image exists but coordinate_hints.yaml does not, surface
    a coordinate_hints_missing note pointing at /fig_extract."""
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / "previews").mkdir()

    result = infer_stage(fig_dir)

    assert "coordinate_hints_missing" in result["notes"]
    assert "coordinate_hints_stale" not in result["notes"]


def test_coordinate_hints_present_clears_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / "previews").mkdir()
    (fig_dir / "coordinate_hints.yaml").write_text(
        "metadata: {extraction_version: '0.1'}\ntext_labels: []\n", encoding="utf-8"
    )

    result = infer_stage(fig_dir)

    assert "coordinate_hints_missing" not in result["notes"]
    assert ("coordinate_hints", "present") in result["checks"]
    assert "coordinate_hints_outdated" in result["notes"]


def test_coordinate_hints_outdated_when_version_matches(tmp_path: Path) -> None:
    """extraction_version matching EXTRACTION_VERSION must NOT produce outdated note."""
    from reference_extract import EXTRACTION_VERSION

    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    (fig_dir / "reference").mkdir()
    (fig_dir / "reference" / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / "previews").mkdir()
    (fig_dir / "coordinate_hints.yaml").write_text(
        f"metadata:\n  extraction_version: '{EXTRACTION_VERSION}'\ntext_labels: []\n",
        encoding="utf-8",
    )

    result = infer_stage(fig_dir)

    assert ("coordinate_hints", "present") in result["checks"]
    assert "coordinate_hints_outdated" not in result["notes"]


def test_coordinate_hints_stale_when_reference_newer(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    ref_file = reference / "golden.png"
    ref_file.write_bytes(b"\x89PNG")
    (fig_dir / "previews").mkdir()
    hints = fig_dir / "coordinate_hints.yaml"
    hints.write_text("metadata: {extraction_version: '0.1'}\ntext_labels: []\n", encoding="utf-8")

    old = time.time() - 100
    new = time.time() - 5
    os.utime(hints, (old, old))
    os.utime(ref_file, (new, new))

    result = infer_stage(fig_dir)

    assert "coordinate_hints_stale" in result["notes"]


@pytest.mark.parametrize(
    ("hint_case", "expected_note"),
    [
        ("missing", "coordinate_hints_missing"),
        ("outdated", "coordinate_hints_outdated"),
        ("parse_error", "coordinate_hints_parse_error"),
        ("stale", "coordinate_hints_stale"),
    ],
)
def test_coordinate_hint_notes_do_not_block_workflow_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hint_case: str,
    expected_note: str,
) -> None:
    from reference_extract import EXTRACTION_VERSION

    name = f"hint_note_ready_{hint_case}"
    fig_dir = tmp_path / name
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png", accepted=False)
    (fig_dir / f"{name}.tex").write_text("% tikz", encoding="utf-8")
    reference = fig_dir / "reference"
    reference.mkdir()
    ref_file = reference / "golden.png"
    ref_file.write_bytes(b"\x89PNG")
    hints = fig_dir / "coordinate_hints.yaml"
    if hint_case == "outdated":
        hints.write_text(
            "metadata: {extraction_version: '0.1'}\ntext_labels: []\n",
            encoding="utf-8",
        )
    elif hint_case == "parse_error":
        hints.write_text("this: is: not: valid: yaml:\n  - because\n", encoding="utf-8")
    elif hint_case == "stale":
        hints.write_text(
            f"metadata:\n  extraction_version: '{EXTRACTION_VERSION}'\ntext_labels: []\n",
            encoding="utf-8",
        )
    _make_fresh_exports(fig_dir, name)
    _write_hashed_critique(fig_dir, name)

    old = time.time() - 100
    new = time.time() - 5
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / f"{name}.tex",
        *(path for path in (hints,) if path.exists()),
    ):
        os.utime(path, (old, old))
    for path in (
        ref_file,
        fig_dir / "build" / f"{name}.pdf",
        fig_dir / "exports" / f"{name}.pdf",
        fig_dir / "exports" / f"{name}.svg",
        fig_dir / "exports" / f"{name}.tif",
        fig_dir / "exports" / f"{name}.png",
        fig_dir / "critique.md",
    ):
        os.utime(path, (new, new))
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = status_mod.infer_stage(fig_dir)

    assert result["stage"] == 4
    assert result["render_state"] == "FRESH"
    assert result["critique_state"] == "FRESH"
    assert result["export_state"] == "FRESH"
    assert expected_note in result["notes"]
    assert result["workflow_ready"] is True
    assert result["golden_ready"] is False
    assert "accepted: true" in result["next"]


def test_coordinate_hints_parse_error_when_yaml_malformed(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden.png")
    reference = fig_dir / "reference"
    reference.mkdir()
    (reference / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / "previews").mkdir()
    (fig_dir / "coordinate_hints.yaml").write_text(
        "this: is: not: valid: yaml:\n  - because\n :::: malformed\n", encoding="utf-8"
    )

    result = infer_stage(fig_dir)

    assert "coordinate_hints_parse_error" in result["notes"]


def test_coordinate_hints_check_skips_when_reference_image_absent(tmp_path: Path) -> None:
    """Ordinary fixtures (no reference_image key) must not emit any
    coordinate_hints_* notes; Layer 2.5 only applies to golden-class fixtures."""
    fig_dir = tmp_path / "ordinaryfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    (fig_dir / "previews").mkdir()

    result = infer_stage(fig_dir)

    assert not any(n.startswith("coordinate_hints_") for n in result["notes"])


def test_style_profile_unknown_surfaces_note(tmp_path: Path) -> None:
    """Unknown style_profile value must produce style_profile_unknown note
    without crashing infer_stage."""
    fig_dir = tmp_path / "badfig"
    fig_dir.mkdir()
    (fig_dir / "spec.yaml").write_text(
        "name: badfig\npanels: []\nstyle_profile: future-profile\n", encoding="utf-8"
    )
    (fig_dir / "briefing.md").write_text("briefing", encoding="utf-8")

    result = infer_stage(fig_dir)

    assert "style_profile_unknown" in result["notes"]


def test_reference_image_missing_surfaces_separate_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden_target_001.png")
    (fig_dir / "previews").mkdir()

    result = infer_stage(fig_dir)

    assert result["stage"] == 1
    assert "reference_image_missing" in result["notes"]
    assert "selected_preview_missing" not in result["notes"]


def test_declared_missing_reference_keeps_critique_gate_closed(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden_target_001.png")

    assert compute_critique_state(fig_dir, "goldenfig") == CRITIQUE_REFERENCE_MISSING


def test_declared_missing_reference_next_hint_requires_fix_not_critique(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, reference_image="reference/golden_target_001.png")
    (fig_dir / "goldenfig.tex").write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    (build_dir / "goldenfig.pdf").write_bytes(b"%PDF")

    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (fig_dir / "spec.yaml", fig_dir / "briefing.md", fig_dir / "goldenfig.tex"):
        os.utime(path, (old_time, old_time))
    os.utime(build_dir / "goldenfig.pdf", (fresh_time, fresh_time))

    result = infer_stage(fig_dir)

    assert result["stage"] == 3
    assert "critique_reference_missing" in result["notes"]
    assert "fix declared reference inputs" in result["next"]
    assert "/fig_critique" not in result["next"]


def test_previews_as_file_not_directory_does_not_crash(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    (fig_dir / "previews").write_text("not a dir", encoding="utf-8")
    result = infer_stage(fig_dir)
    assert result["stage"] == 1
    assert "previews_not_directory" in result["notes"]


def test_smoke_fixture_smoke_trap_demo() -> None:
    fixture = REPO_ROOT / "examples" / "smoke_trap_demo"
    if not fixture.exists():
        return
    if not (fixture / "build" / "smoke_trap_demo.pdf").exists():
        pytest.skip("smoke_trap_demo build artifacts are gitignored")
    result = infer_stage(fixture)
    assert result["stage"] == 4
    assert "partial_export" not in result["notes"]
    assert result["accepted"] is None


def test_accepted_true_resolves_in_result(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=True)
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "myfig.pdf").write_bytes(b"%PDF")
    (exports / "myfig.svg").write_bytes(b"<svg/>")
    (exports / "myfig.tif").write_bytes(b"TIFF")
    (exports / "myfig.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert result["accepted"] is True


def test_accepted_false_resolves_in_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import status as status_mod

    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=False)
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "myfig.pdf").write_bytes(b"%PDF")
    (exports / "myfig.svg").write_bytes(b"<svg/>")
    (exports / "myfig.tif").write_bytes(b"TIFF")
    (exports / "myfig.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")
    result = status_mod.infer_stage(fig_dir)
    assert result["stage"] == 4
    assert result["accepted"] is False
    assert "QUALITY_AUDIT.md" in result["next"]
    assert "accepted: true" in result["next"]


def test_accepted_invalid_type_coerces_to_none(tmp_path: Path) -> None:
    # YAML 1.1 parses bare yes/no/on/off as booleans, so use a value that is
    # genuinely a non-bool after parse (string "maybe" stays a string).
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted="maybe")
    result = infer_stage(fig_dir)
    assert result["accepted"] is None


def test_stage_4_stale_takes_priority_over_not_accepted(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=False)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    briefing = fig_dir / "briefing.md"
    exports = fig_dir / "exports"
    exports.mkdir()
    pdf = exports / "myfig.pdf"
    svg = exports / "myfig.svg"
    tif = exports / "myfig.tif"
    png = exports / "myfig.png"
    for path, content in (
        (pdf, b"%PDF"),
        (svg, b"<svg/>"),
        (tif, b"TIFF"),
        (png, b"\x89PNG"),
    ):
        path.write_bytes(content)
    old_time = time.time() - 100
    for path in (pdf, svg, tif, png, briefing):
        os.utime(path, (old_time, old_time))
    new_time = time.time() - 5
    os.utime(tex, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert result["accepted"] is False
    assert "stale_export" in result["notes"]
    # stale takes priority over not-accepted in the next-hint
    assert "/fig_compile" in result["next"]
    assert "QUALITY_AUDIT" not in result["next"]


def test_print_single_shows_not_accepted_marker(tmp_path: Path, capsys) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=False)
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "goldenfig.pdf").write_bytes(b"%PDF")
    (exports / "goldenfig.svg").write_bytes(b"<svg/>")
    (exports / "goldenfig.tif").write_bytes(b"TIFF")
    (exports / "goldenfig.png").write_bytes(b"\x89PNG")

    import status as status_mod

    result = status_mod.infer_stage(fig_dir)
    status_mod._print_single(result)
    captured = capsys.readouterr()
    assert "goldenfig — stage 4/4 (not accepted)" in captured.out


def test_print_single_shows_accepted_marker(tmp_path: Path, capsys) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=True)
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "goldenfig.pdf").write_bytes(b"%PDF")
    (exports / "goldenfig.svg").write_bytes(b"<svg/>")
    (exports / "goldenfig.tif").write_bytes(b"TIFF")
    (exports / "goldenfig.png").write_bytes(b"\x89PNG")

    import status as status_mod

    result = status_mod.infer_stage(fig_dir)
    status_mod._print_single(result)
    captured = capsys.readouterr()
    assert "goldenfig — stage 4/4 (accepted)" in captured.out


def test_no_arg_summary_shows_not_accepted_marker(tmp_path: Path, capsys, monkeypatch) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    fig = examples_dir / "goldenfig"
    fig.mkdir()
    _make_spec(fig, accepted=False)
    exports = fig / "exports"
    exports.mkdir()
    (exports / "goldenfig.pdf").write_bytes(b"%PDF")
    (exports / "goldenfig.svg").write_bytes(b"<svg/>")
    (exports / "goldenfig.tif").write_bytes(b"TIFF")
    (exports / "goldenfig.png").write_bytes(b"\x89PNG")

    monkeypatch.chdir(tmp_path)

    import status as status_mod

    old_argv = sys.argv
    sys.argv = ["status.py"]
    try:
        status_mod.main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert "goldenfig  stage 4/4 (not accepted)" in captured.out


def test_no_arg_summary_shows_publication_gate_state(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    fig = examples_dir / "goldenfig"
    _make_status_ready_fixture(fig, accepted=True)
    (fig / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: false\n",
        encoding="utf-8",
    )
    _mark_sources_older_than_outputs(fig)
    monkeypatch.chdir(tmp_path)

    import status as status_mod

    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")
    old_argv = sys.argv
    sys.argv = ["status.py"]
    try:
        status_mod.main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert "goldenfig  stage 4/4 (accepted)" in captured.out
    assert "ready: true" in captured.out
    assert "publication: PROVENANCE_REQUIRED" in captured.out


def test_real_golden_fixture_is_not_accepted() -> None:
    fixture = REPO_ROOT / "examples" / "golden_trap_depth_picture"
    if not fixture.exists():
        return
    result = infer_stage(fixture)
    assert result["stage"] == 4
    assert result["accepted"] is False
    if "stale_export" in result["notes"]:
        # Golden fixture is TRACKED_GOLDEN → stale hint must mention --force-golden
        assert "--force-golden" in result["next"]
        assert "QUALITY_AUDIT" not in result["next"]
    else:
        assert "QUALITY_AUDIT.md" in result["next"]


def test_no_arg_all_figures(tmp_path: Path, capsys, monkeypatch) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    # Stage 1 figure
    fig1 = examples_dir / "alpha_fig"
    fig1.mkdir()
    _make_spec(fig1)
    (fig1 / "previews").mkdir()

    # Stage 4 figure
    fig2 = examples_dir / "zeta_fig"
    fig2.mkdir()
    _make_spec(fig2)
    exports = fig2 / "exports"
    exports.mkdir()
    (exports / "zeta_fig.pdf").write_bytes(b"%PDF")
    (exports / "zeta_fig.svg").write_bytes(b"<svg/>")
    (exports / "zeta_fig.tif").write_bytes(b"TIFF")
    (exports / "zeta_fig.png").write_bytes(b"\x89PNG")

    monkeypatch.chdir(tmp_path)

    import status as status_mod

    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    old_argv = sys.argv
    sys.argv = ["status.py"]
    try:
        status_mod.main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert "alpha_fig" in captured.out
    assert "stage 1" in captured.out
    assert "zeta_fig" in captured.out
    assert "stage 4" in captured.out
    assert "notes:" not in captured.out
    lines = [ln for ln in captured.out.splitlines() if ln.strip()]
    names = [ln.split()[0] for ln in lines]
    assert names == sorted(names)


def test_infer_stage_returns_exports_substate_field(tmp_path: Path) -> None:
    """infer_stage must include exports_substate in its return dict so
    /fig_status can surface MISSING / TRACKED_GOLDEN / STALE / FRESH.
    """
    fixture = tmp_path / "examples" / "no_files"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: no_files\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# stub\n", encoding="utf-8")
    result = infer_stage(fixture)
    assert "exports_substate" in result
    assert result["exports_substate"] == "MISSING"


def test_infer_stage_returns_status_vector_for_ready_final(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "ready_fig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    (fig_dir / "ready_fig.tex").write_text("% tikz", encoding="utf-8")
    build = fig_dir / "build"
    build.mkdir()
    (build / "ready_fig.pdf").write_bytes(b"%PDF")
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "ready_fig.pdf").write_bytes(b"%PDF")
    (exports / "ready_fig.svg").write_bytes(b"<svg/>")
    (exports / "ready_fig.tif").write_bytes(b"TIFF")
    (exports / "ready_fig.png").write_bytes(b"\x89PNG")

    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / "ready_fig.tex",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(build / "ready_fig.pdf", (fresh_time, fresh_time))
    for path in exports.iterdir():
        os.utime(path, (fresh_time, fresh_time))

    import status as status_mod

    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = status_mod.infer_stage(fig_dir)

    assert result["render_state"] == "FRESH"
    assert result["critique_state"] == "NOT_REQUIRED"
    assert result["export_state"] == "FRESH"
    assert result["acceptance_state"] == "NOT_DECLARED"
    assert result["workflow_ready"] is True
    assert result["golden_ready"] is False
    assert result["release_ready"] is False
    assert result["final_ready"] is False


def test_infer_stage_status_vector_not_ready_when_not_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=False)
    (fig_dir / "goldenfig.tex").write_text("% tikz", encoding="utf-8")
    build = fig_dir / "build"
    build.mkdir()
    (build / "goldenfig.pdf").write_bytes(b"%PDF")
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "goldenfig.pdf").write_bytes(b"%PDF")
    (exports / "goldenfig.svg").write_bytes(b"<svg/>")
    (exports / "goldenfig.tif").write_bytes(b"TIFF")
    (exports / "goldenfig.png").write_bytes(b"\x89PNG")

    import status as status_mod

    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = status_mod.infer_stage(fig_dir)

    assert result["acceptance_state"] == "NOT_ACCEPTED"
    assert result["workflow_ready"] is True
    assert result["golden_ready"] is False
    assert result["release_ready"] is False
    assert result["final_ready"] is False
    assert result["publication_gate_state"] == "HUMAN_ACCEPTANCE_REQUIRED"
    assert result["publication_gate_failures"][0]["code"] == "missing_quality_audit"


def test_infer_stage_publication_gate_not_applicable_without_acceptance_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "draftfig"
    _make_status_ready_fixture(fig_dir)
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["acceptance_state"] == "NOT_DECLARED"
    assert result["publication_gate_state"] == "NOT_APPLICABLE"
    assert result["publication_gate_failures"] == []


def test_infer_stage_surfaces_publication_provenance_gate_when_audit_is_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "goldenfig"
    _make_status_ready_fixture(fig_dir, accepted=True)
    (fig_dir / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "human-visual-acceptance: true\n"
        "submission-safe: false\n",
        encoding="utf-8",
    )
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["acceptance_state"] == "ACCEPTED"
    assert result["golden_ready"] is True
    assert result["release_ready"] is True
    assert result["publication_gate_state"] == "PROVENANCE_REQUIRED"
    assert result["publication_gate_failures"] == [
        {
            "code": "missing_submission_safe_true",
            "category": "publication_provenance",
            "actor": "human",
            "message": "QUALITY_AUDIT.md does not declare submission-safe: true",
            "required_action": (
                "Human reviewer must decide submission safety and write an explicit value."
            ),
        }
    ]


def test_infer_stage_requires_disclosure_for_polished_svg_publication_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "polishedfig"
    _make_status_ready_fixture(fig_dir, accepted=True)
    _write_final_artifact_spec(fig_dir)
    _write_polish_manifest(fig_dir)
    (fig_dir / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true\n",
        encoding="utf-8",
    )
    _mark_sources_older_than_outputs(fig_dir)
    monkeypatch.setattr(status_mod, "compute_export_state", lambda _example, _name: "FRESH")

    result = infer_stage(fig_dir)

    assert result["final_artifact_kind"] == "polished_svg"
    assert result["final_artifact_state"] == "FRESH"
    assert result["publication_gate_state"] == "PROVENANCE_REQUIRED"
    assert result["publication_gate_failures"] == [
        {
            "code": "missing_disclosure_needed",
            "category": "publication_provenance",
            "actor": "human",
            "message": "QUALITY_AUDIT.md does not declare disclosure-needed",
            "required_action": (
                "Human reviewer must declare whether publication disclosure is needed."
            ),
        }
    ]


def test_infer_stage_release_ready_requires_fresh_export_not_tracked_golden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=True)
    (fig_dir / "goldenfig.tex").write_text("% tikz", encoding="utf-8")
    build = fig_dir / "build"
    build.mkdir()
    (build / "goldenfig.pdf").write_bytes(b"%PDF")
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "goldenfig.pdf").write_bytes(b"%PDF")
    (exports / "goldenfig.svg").write_bytes(b"<svg/>")
    (exports / "goldenfig.tif").write_bytes(b"TIFF")
    (exports / "goldenfig.png").write_bytes(b"\x89PNG")

    import status as status_mod

    monkeypatch.setattr(
        status_mod,
        "compute_export_state",
        lambda _example, _name: "TRACKED_GOLDEN",
    )

    result = status_mod.infer_stage(fig_dir)

    assert result["workflow_ready"] is True
    assert result["golden_ready"] is True
    assert result["release_ready"] is False
    assert result["final_ready"] is False


def test_print_single_shows_exports_substate(tmp_path: Path, capsys) -> None:
    """_print_single must surface exports_substate so users see MISSING /
    TRACKED_GOLDEN / STALE / FRESH for each fixture.
    """
    fixture = tmp_path / "no_exports_fig"
    fixture.mkdir(parents=True)
    _make_spec(fixture)
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")

    import status as status_mod

    result = status_mod.infer_stage(fixture)
    status_mod._print_single(result)
    captured = capsys.readouterr()
    assert "Exports: MISSING" in captured.out


def test_print_single_shows_status_vector(tmp_path: Path, capsys) -> None:
    fixture = tmp_path / "no_exports_fig"
    fixture.mkdir(parents=True)
    _make_spec(fixture)

    import status as status_mod

    result = status_mod.infer_stage(fixture)
    status_mod._print_single(result)
    captured = capsys.readouterr()
    assert (
        "States: render=NOT_AUTHORED critique=NOT_REQUIRED "
        "export=MISSING acceptance=NOT_DECLARED "
        "workflow_ready=false golden_ready=false release_ready=false final_ready=false"
    ) in captured.out


def test_print_single_shows_publication_gate_state_and_first_blocker(
    tmp_path: Path, capsys
) -> None:
    fixture = tmp_path / "goldenfig"
    fixture.mkdir(parents=True)
    _make_spec(fixture, accepted=False)

    import status as status_mod

    result = status_mod.infer_stage(fixture)
    status_mod._print_single(result)
    captured = capsys.readouterr()

    assert "Publication gate: HUMAN_ACCEPTANCE_REQUIRED" in captured.out
    assert "missing_quality_audit" in captured.out
    assert "create QUALITY_AUDIT.md from the publication audit scaffold" in captured.out


def test_print_single_shows_final_artifact_state(tmp_path: Path, capsys) -> None:
    fixture = tmp_path / "no_exports_fig"
    fixture.mkdir(parents=True)
    _make_spec(fixture)

    import status as status_mod

    result = status_mod.infer_stage(fixture)
    status_mod._print_single(result)
    captured = capsys.readouterr()
    assert "Final artifact: generated_export NONE exports/no_exports_fig.svg" in captured.out


def test_main_resolves_single_name_under_examples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The documented /fig_status <name> form should resolve examples/<name>."""
    import status as status_mod

    examples_dir = tmp_path / "examples"
    fixture = examples_dir / "named_fig"
    fixture.mkdir(parents=True)
    _make_spec(fixture)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["status.py", "named_fig"])

    assert status_mod.main() == 0

    captured = capsys.readouterr()
    assert "named_fig — stage 1/4" in captured.out


def test_tracked_golden_stale_gives_force_golden_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When exports_substate is TRACKED_GOLDEN and sources are newer, the next
    hint must mention --force-golden rather than the generic /fig_compile advice.
    """
    import subprocess

    import export_freshness
    import status as status_mod

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)

    fig_dir = repo / "examples" / "golden_fig"
    (fig_dir / "exports").mkdir(parents=True)
    pdf = fig_dir / "exports" / "golden_fig.pdf"
    pdf.write_bytes(b"%PDF")
    subprocess.run(["git", "add", str(pdf.relative_to(repo))], cwd=repo, check=True)

    # Sources newer than the tracked PDF → stale
    (fig_dir / "spec.yaml").write_text(
        "name: golden_fig\npanels: []\nstyle_profile: polymer-default\n", encoding="utf-8"
    )
    (fig_dir / "briefing.md").write_text("briefing", encoding="utf-8")
    (fig_dir / "golden_fig.tex").write_text("% tex", encoding="utf-8")
    old_time = 1_000_000.0
    os.utime(pdf, (old_time, old_time))

    monkeypatch.setattr(export_freshness, "REPO_ROOT", repo)

    result = status_mod.infer_stage(fig_dir)
    assert result["exports_substate"] == "TRACKED_GOLDEN"
    assert "stale_export" in result["notes"]
    assert "--force-golden" in result["next"]
    assert "/fig_compile" not in result["next"]


def test_tracked_golden_stale_with_fresh_render_and_missing_critique_skips_compile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    import export_freshness
    import status as status_mod

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)

    fig_dir = repo / "examples" / "golden_fig"
    (fig_dir / "reference").mkdir(parents=True)
    (fig_dir / "build").mkdir()
    (fig_dir / "exports").mkdir()
    (fig_dir / "spec.yaml").write_text(
        "name: golden_fig\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/golden.png\n",
        encoding="utf-8",
    )
    (fig_dir / "briefing.md").write_text("briefing", encoding="utf-8")
    (fig_dir / "golden_fig.tex").write_text("% tex", encoding="utf-8")
    (fig_dir / "reference" / "golden.png").write_bytes(b"\x89PNG")
    (fig_dir / "build" / "golden_fig.pdf").write_bytes(b"%PDF")
    for suffix, content in {
        "pdf": b"%PDF",
        "svg": b"<svg/>",
        "tif": b"TIFF",
        "png": b"\x89PNG",
    }.items():
        (fig_dir / "exports" / f"golden_fig.{suffix}").write_bytes(content)
    subprocess.run(
        ["git", "add", str((fig_dir / "exports" / "golden_fig.pdf").relative_to(repo))],
        cwd=repo,
        check=True,
    )

    now = time.time()
    export_time = now - 200
    source_time = now - 100
    build_time = now - 10
    for path in (
        fig_dir / "spec.yaml",
        fig_dir / "briefing.md",
        fig_dir / "golden_fig.tex",
        fig_dir / "reference" / "golden.png",
    ):
        os.utime(path, (source_time, source_time))
    os.utime(fig_dir / "build" / "golden_fig.pdf", (build_time, build_time))
    for path in (fig_dir / "exports").iterdir():
        os.utime(path, (export_time, export_time))

    monkeypatch.setattr(export_freshness, "REPO_ROOT", repo)

    result = status_mod.infer_stage(fig_dir)

    assert result["render_state"] == "FRESH"
    assert result["critique_state"] == "MISSING"
    assert "stale_export" in result["notes"]
    assert "--force-golden" in result["next"]
    assert "/fig_critique" in result["next"]
    assert "/fig_compile" not in result["next"]


def test_tracked_golden_partial_export_gives_force_golden_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tracked golden with missing sibling exports cannot be fixed by plain
    /fig_export because run_export.py protects tracked artifacts unless
    --force-golden is explicit.
    """
    import subprocess

    import export_freshness
    import status as status_mod

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)

    fig_dir = repo / "examples" / "golden_partial"
    (fig_dir / "exports").mkdir(parents=True)
    (fig_dir / "spec.yaml").write_text(
        "name: golden_partial\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    (fig_dir / "briefing.md").write_text("briefing", encoding="utf-8")
    (fig_dir / "golden_partial.tex").write_text("% tex", encoding="utf-8")
    pdf = fig_dir / "exports" / "golden_partial.pdf"
    pdf.write_bytes(b"%PDF")
    subprocess.run(["git", "add", str(pdf.relative_to(repo))], cwd=repo, check=True)

    old_time = 1_000_000.0
    fresh_time = time.time() + 100.0
    for path in (fig_dir / "spec.yaml", fig_dir / "briefing.md", fig_dir / "golden_partial.tex"):
        os.utime(path, (old_time, old_time))
    os.utime(pdf, (fresh_time, fresh_time))

    monkeypatch.setattr(export_freshness, "REPO_ROOT", repo)

    result = status_mod.infer_stage(fig_dir)
    assert result["exports_substate"] == "TRACKED_GOLDEN"
    assert "partial_export" in result["notes"]
    assert "--force-golden" in result["next"]
    assert "re-run /fig_export <name> to generate" not in result["next"]
