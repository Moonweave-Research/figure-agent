"""Tests for scripts/status.py — infer_stage contract."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_spec(
    directory: Path,
    selected_preview: str | None = None,
    reference_image: str | None = None,
    accepted: bool | str | None = None,
) -> None:
    preview_val = selected_preview if selected_preview else "null"
    reference_line = f"reference_image: {reference_image}\n" if reference_image else ""
    if accepted is None:
        accepted_line = ""
    elif isinstance(accepted, bool):
        accepted_line = f"accepted: {'true' if accepted else 'false'}\n"
    else:
        accepted_line = f"accepted: {accepted}\n"
    content = (
        f"name: {directory.name}\npanels: []\nstyle_profile: polymer-default\n"
        f"selected_preview: {preview_val}\n"
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


def test_stage_2_previews_has_image_selected_preview_null(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview=None)
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / ".gitkeep").touch()
    (previews / "candidate_01.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 2


def test_stage_3_selected_preview_set_no_tex(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="chosen.png")
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / ".gitkeep").touch()
    result = infer_stage(fig_dir)
    assert result["stage"] == 3


def test_stage_4_tex_stale_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="chosen.png")
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
    assert result["stage"] == 4


def test_stage_4_tex_no_build_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4


def test_stage_5_fresh_pdf_no_exports(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    # Make pdf newer than tex
    old_time = time.time() - 100
    os.utime(tex, (old_time, old_time))
    os.utime(fig_dir / "briefing.md", (old_time, old_time))
    new_time = time.time() - 10
    os.utime(pdf, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 5


def test_stage_6_partial_export_svg_only(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    result = infer_stage(fig_dir)
    assert result["stage"] == 6
    assert "partial_export" in result["notes"]


def test_stage_6_partial_export_next_redirects_to_re_export(tmp_path: Path) -> None:
    """A partial export must steer the user back to /fig_export, not present
    "done" so they think the figure is finished."""
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    result = infer_stage(fig_dir)
    assert result["stage"] == 6
    assert "partial_export" in result["notes"]
    assert "/fig_export" in result["next"]
    assert "done" not in result["next"]


def test_stage_6_stale_takes_priority_over_partial(tmp_path: Path) -> None:
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
    assert result["stage"] == 6
    assert "partial_export" in result["notes"]
    assert "stale_export" in result["notes"]
    assert "/fig_compile" in result["next"]


def test_stage_6_all_four_exports_no_note(tmp_path: Path) -> None:
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
    assert result["stage"] == 6
    assert "partial_export" not in result["notes"]


def test_stage_4_briefing_newer_than_pdf(tmp_path: Path) -> None:
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
    assert result["stage"] == 4
    assert ("build_pdf", "stale") in result["checks"]


def test_stage_6_stale_export_when_source_newer(tmp_path: Path) -> None:
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
    assert result["stage"] == 6
    assert "stale_export" in result["notes"]
    assert "partial_export" not in result["notes"]
    assert "/fig_compile" in result["next"]
    assert "done" not in result["next"]


def test_stage_6_preserves_selected_preview_missing_note(tmp_path: Path) -> None:
    fig = tmp_path / "preview_missing_exported"
    fig.mkdir()
    _make_spec(fig, selected_preview="missing.png")
    (fig / "briefing.md").write_text("briefing", encoding="utf-8")
    (fig / "previews").mkdir()
    exports = fig / "exports"
    exports.mkdir()
    (exports / "preview_missing_exported.pdf").write_bytes(b"%PDF")

    result = infer_stage(fig)

    assert result["stage"] == 6
    assert "selected_preview_missing" in result["notes"]


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


def test_stage_3_selected_preview_missing_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="ghost.png")
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / ".gitkeep").touch()
    result = infer_stage(fig_dir)
    assert result["stage"] == 3
    assert "selected_preview_missing" in result["notes"]


def test_stage_3_selected_preview_present_no_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="real.png")
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / "real.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 3
    assert "selected_preview_missing" not in result["notes"]


def test_reference_image_existing_is_not_treated_as_selected_preview(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview=None, reference_image="reference/golden_target_001.png")
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
    _make_spec(fig_dir, selected_preview=None, reference_image="reference/golden.png")
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
    _make_spec(fig_dir, selected_preview=None, reference_image="reference/golden.png")
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


def test_coordinate_hints_stale_when_reference_newer(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview=None, reference_image="reference/golden.png")
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
    _make_spec(fig_dir, selected_preview=None, reference_image="reference/golden.png")
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
    _make_spec(fig_dir, selected_preview=None)
    (fig_dir / "previews").mkdir()

    result = infer_stage(fig_dir)

    assert not any(n.startswith("coordinate_hints_") for n in result["notes"])


def test_reference_image_missing_surfaces_separate_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "goldenfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview=None, reference_image="reference/golden_target_001.png")
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
    assert result["stage"] == 6
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
    assert result["stage"] == 6
    assert result["accepted"] is True


def test_accepted_false_resolves_in_result(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, accepted=False)
    exports = fig_dir / "exports"
    exports.mkdir()
    (exports / "myfig.pdf").write_bytes(b"%PDF")
    (exports / "myfig.svg").write_bytes(b"<svg/>")
    (exports / "myfig.tif").write_bytes(b"TIFF")
    (exports / "myfig.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 6
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


def test_stage_6_stale_takes_priority_over_not_accepted(tmp_path: Path) -> None:
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
    assert result["stage"] == 6
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
    assert "goldenfig — stage 6/6 (not accepted)" in captured.out


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
    assert "goldenfig — stage 6/6 (accepted)" in captured.out


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
    assert "goldenfig  stage 6/6 (not accepted)" in captured.out


def test_real_golden_fixture_is_not_accepted() -> None:
    fixture = REPO_ROOT / "examples" / "golden_trap_depth_picture"
    if not fixture.exists():
        return
    result = infer_stage(fixture)
    assert result["stage"] == 6
    assert result["accepted"] is False
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
    assert "stage 6" in captured.out
    assert "notes:" not in captured.out
    lines = [ln for ln in captured.out.splitlines() if ln.strip()]
    names = [ln.split()[0] for ln in lines]
    assert names == sorted(names)


def test_no_arg_all_figures_surfaces_notes(tmp_path: Path, capsys, monkeypatch) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    fig = examples_dir / "stale_fig"
    fig.mkdir()
    _make_spec(fig, selected_preview="missing.png")
    (fig / "briefing.md").write_text("briefing", encoding="utf-8")
    exports = fig / "exports"
    exports.mkdir()
    (exports / "stale_fig.pdf").write_bytes(b"%PDF")

    monkeypatch.chdir(tmp_path)

    import status as status_mod

    old_argv = sys.argv
    sys.argv = ["status.py"]
    try:
        status_mod.main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert "stale_fig  stage 6/6" in captured.out
    assert "notes: selected_preview_missing" in captured.out
