"""Tests for golden fixture artifact quality gates."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_golden_artifacts import (  # noqa: E402
    audit_is_fresh,
    check_example,
    checker_warning_counts,
    count_svg_visible_elements,
    fixture_is_accepted,
    missing_pdf_labels,
    png_has_white_opaque_corners,
    source_inventory_counts,
    unresolved_visual_clash_count,
)


def test_missing_pdf_labels_uses_rendered_text_tokens() -> None:
    text = """
    Experiment
    Mathematical interpretation
    Molecular origin
    I(t) alpha t-n
    slope = -n
    Discharge Debye reference
    Debye exp -t tau
    tau d
    n
    g E t
    shallow deep localized traps S-rich segments chemical origin physical origin
    converged trap-depth picture Energy CB VB E t
    """

    assert missing_pdf_labels(text) == []


def test_missing_pdf_labels_accepts_pdftotext_joined_subscripts() -> None:
    text = "g(Et ) Et"

    missing = missing_pdf_labels(
        text,
        required={
            "g(E_t)": (("g", "e", "t"), ("g", "et")),
            "E_t": (("e", "t"), ("et",)),
        },
    )

    assert missing == []


def test_missing_pdf_labels_reports_absent_rendered_label() -> None:
    text = "Experiment Energy CB VB"

    missing = missing_pdf_labels(text)

    assert "converged trap-depth picture" in missing
    assert "localized traps" in missing


def test_count_svg_visible_elements_counts_namespaced_shapes(tmp_path: Path) -> None:
    svg = tmp_path / "figure.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
          <g><path d="M0 0 L1 1"/><text>Energy</text><rect width="1" height="1"/></g>
          <metadata><path d="ignored"/></metadata>
        </svg>""",
        encoding="utf-8",
    )

    assert count_svg_visible_elements(svg) == 3


def test_png_has_white_opaque_corners_accepts_white_rgb(tmp_path: Path) -> None:
    png = tmp_path / "white.png"
    Image.new("RGB", (20, 12), "white").save(png)

    assert png_has_white_opaque_corners(png)


def test_png_has_white_opaque_corners_rejects_transparent_or_black(tmp_path: Path) -> None:
    transparent = tmp_path / "transparent.png"
    black = tmp_path / "black.png"
    Image.new("RGBA", (20, 12), (255, 255, 255, 0)).save(transparent)
    Image.new("RGB", (20, 12), "black").save(black)

    assert not png_has_white_opaque_corners(transparent)
    assert not png_has_white_opaque_corners(black)


def test_fixture_is_accepted_requires_explicit_true(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    false_spec = tmp_path / "false.yaml"
    true_spec = tmp_path / "true.yaml"
    false_spec.write_text("accepted: false\n", encoding="utf-8")
    true_spec.write_text("accepted: true\n", encoding="utf-8")

    assert not fixture_is_accepted(missing)
    assert not fixture_is_accepted(false_spec)
    assert fixture_is_accepted(true_spec)


def test_source_inventory_counts_repeated_golden_primitives() -> None:
    tex = r"""
    \draw[sep] (0,0) -- (1,0);
    \draw[sep] (0,1) -- (1,1);
    \BandBox{0}{0}{CB}
    \BandBox{0}{1}{VB}
    \SmallLobe{0}{0}{cAmber}{shallow}
    \SmallLobe{1}{0}{cBlue}{deep}
    \TrapLevel{0}{0}{trapShallow}
    \TrapLevel{1}{0}{trapDeep}
    \TrapLevel{2}{0}{trapDeep}
    \foreach \x/\y in {1/1,2/2,3/3,4/4} {
      \node[text=cAmber] at (\x,\y) {S};
    }
    """

    counts = source_inventory_counts(tex)

    assert counts["separator_lines"] == 2
    assert counts["band_boxes"] == 2
    assert counts["distribution_lobes"] == 2
    assert counts["trap_levels"] == 3
    assert counts["sulfur_markers"] == 4


def test_checker_warning_counts_reads_quality_audit() -> None:
    audit = """
    Observed:
    6 collision(s) in golden_trap_depth_picture.pdf
    52 visual clash candidate(s)
    """

    assert checker_warning_counts(audit) == (6, 52)


def test_checker_warning_counts_reads_zero_collision_success() -> None:
    audit = """
    Observed:
    OK: no collisions found in golden_trap_depth_picture.pdf (115 words)
    30 visual clash candidate(s)
    """

    assert checker_warning_counts(audit) == (0, 30)


def test_unresolved_visual_clash_count_reads_triage_total() -> None:
    audit = """
    30 visual clash candidate(s)
    9 unresolved visual clash(es)
    """

    assert unresolved_visual_clash_count(audit) == 9


def test_audit_is_fresh_requires_audit_newer_than_sources(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    audit = fixture / "QUALITY_AUDIT.md"
    source = fixture / "fixture.tex"
    source.write_text("source", encoding="utf-8")
    audit.write_text("audit", encoding="utf-8")
    old = 100.0
    new = 200.0
    source.touch()
    audit.touch()
    import os

    os.utime(audit, (old, old))
    os.utime(source, (new, new))

    assert not audit_is_fresh(fixture, (source,))

    os.utime(audit, (new + 1, new + 1))
    assert audit_is_fresh(fixture, (source,))


def test_require_accepted_mode_rejects_unaccepted_current_fixture() -> None:
    fixture = Path(__file__).resolve().parents[1] / "examples" / "golden_trap_depth_picture"

    failures = check_example(
        fixture,
        min_svg_elements=80,
        min_png_width=1600,
        require_accepted=True,
        max_collisions=0,
        max_visual_clashes=0,
    )

    assert "fixture is not marked accepted: true" in failures
    assert not any(failure.startswith("collision budget exceeded") for failure in failures)
    assert "unresolved visual clash budget exceeded: 13 > 0" in failures
