"""Tests for scripts/status.py — infer_stage contract."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_stage_0_missing_directory(tmp_path: Path) -> None:
    result = infer_stage(tmp_path / "nonexistent")
    assert result["stage"] == 0


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


def test_stage_4_stale_export_when_coordinate_hints_newer(tmp_path: Path) -> None:
    """coordinate_hints.yaml newer than exports must trigger stale_export."""
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
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
    for path in (tex, fig_dir / "briefing.md", fig_dir / "spec.yaml"):
        os.utime(path, (old_time, old_time))
    for fname in ("myfig.pdf", "myfig.svg", "myfig.tif", "myfig.png"):
        os.utime(exports_dir / fname, (old_time, old_time))
    hints = fig_dir / "coordinate_hints.yaml"
    hints.write_text("metadata:\n  extraction_version: '0.3'\n", encoding="utf-8")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert "stale_export" in result["notes"]


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

    # Stage 6 figure
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
