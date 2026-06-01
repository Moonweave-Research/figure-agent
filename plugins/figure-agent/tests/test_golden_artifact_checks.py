"""Tests for golden fixture artifact quality gates."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_golden_artifacts as golden_checks  # noqa: E402
from check_golden_artifacts import (  # noqa: E402
    audit_is_fresh,
    check_example,
    checker_warning_counts,
    count_svg_visible_elements,
    fixture_is_accepted,
    load_golden_contract,
    missing_pdf_labels,
    png_has_white_opaque_corners,
    source_inventory_counts,
    unresolved_visual_clash_count,
)
from quality_manifest import file_sha256  # noqa: E402
from svg_polish_manifest import (  # noqa: E402
    final_artifact_source_set_hash,
    write_svg_polish_manifest,
)
from svg_semantic_diff import build_svg_semantic_diff_report  # noqa: E402

_BASELINE_REQUIRED_LABELS = [
    "Experiment",
    "Mathematical interpretation",
    "Molecular origin",
    "I t",
    "slope",
    "Discharge",
    "Debye",
    "tau d",
    "n",
    ["g e t", "g et"],
    "shallow",
    "deep",
    "localized traps",
    "S rich segments",
    "chemical origin",
    "physical origin",
    "converged trap depth picture",
    "Energy",
    "CB",
    "VB",
    ["e t", "et"],
]


def test_missing_pdf_labels_returns_empty_when_text_satisfies_contract() -> None:
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

    assert missing_pdf_labels(text, _BASELINE_REQUIRED_LABELS) == []


def test_missing_pdf_labels_alternative_list_passes_if_any_matches() -> None:
    text = "g(Et ) Et"

    missing = missing_pdf_labels(
        text,
        required=[["g e t", "g et"], ["e t", "et"]],
    )

    assert missing == []


def test_missing_pdf_labels_alternative_list_fails_if_none_matches() -> None:
    text = "Experiment Energy"

    missing = missing_pdf_labels(text, required=[["g e t", "g et"]])

    # Canonical name reported is the first alternative.
    assert missing == ["g e t"]


def test_missing_pdf_labels_reports_absent_rendered_label() -> None:
    text = "Experiment Energy CB VB"

    missing = missing_pdf_labels(text, _BASELINE_REQUIRED_LABELS)

    assert "converged trap depth picture" in missing
    assert "localized traps" in missing


def test_missing_pdf_labels_none_or_empty_returns_empty() -> None:
    assert missing_pdf_labels("anything", None) == []
    assert missing_pdf_labels("anything", []) == []


def test_missing_pdf_labels_invalid_entry_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        missing_pdf_labels("text", required=[123])  # type: ignore[list-item]
    with pytest.raises(ValueError):
        missing_pdf_labels("text", required=[[]])  # empty alternative list


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


def test_fixture_is_accepted_returns_false_for_invalid_utf8(tmp_path: Path) -> None:
    spec = tmp_path / "bad-encoding.yaml"
    spec.write_bytes(b"accepted: true\n\xff\n")

    assert not fixture_is_accepted(spec)


def test_source_inventory_counts_with_spec_patterns() -> None:
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
    """
    patterns = {
        "separator_lines": {"pattern": r"\\draw\[sep\]", "min": 1},
        "band_boxes": {"pattern": r"\\BandBox\b", "min": 1},
        "distribution_lobes": {"pattern": r"\\SmallLobe\b", "min": 1},
        "trap_levels": {"pattern": r"\\TrapLevel\b", "min": 1},
    }

    counts = source_inventory_counts(tex, patterns)

    assert counts["separator_lines"] == 2
    assert counts["band_boxes"] == 2
    assert counts["distribution_lobes"] == 2
    assert counts["trap_levels"] == 3


def test_source_inventory_counts_returns_empty_when_patterns_missing() -> None:
    assert source_inventory_counts("any tex", None) == {}
    assert source_inventory_counts("any tex", {}) == {}


def test_source_inventory_counts_ignores_commented_macros() -> None:
    """A commented-out macro call must not satisfy the inventory floor;
    otherwise an author could write `% \\BandBox{...}` lines to pass the
    accepted-mode gate without actually drawing the primitive."""
    tex = r"""
    \BandBox{0}{0}{CB}
    % \BandBox{0}{1}{VB}
    """
    patterns = {"band_boxes": {"pattern": r"\\BandBox\b", "min": 1}}

    counts = source_inventory_counts(tex, patterns)

    assert counts["band_boxes"] == 1


def test_source_inventory_counts_respects_escaped_percent() -> None:
    """A literal `\\%` is not a comment marker; counts past it must include
    macros on the same line."""
    tex = r"\BandBox{a}{b}{c} \% inline literal percent \BandBox{d}{e}{f}"
    patterns = {"band_boxes": {"pattern": r"\\BandBox\b", "min": 1}}

    counts = source_inventory_counts(tex, patterns)

    assert counts["band_boxes"] == 2


def test_load_golden_contract_returns_none_when_block_absent(tmp_path: Path) -> None:
    spec = tmp_path / "spec.yaml"
    spec.write_text("name: foo\naccepted: false\n", encoding="utf-8")

    assert load_golden_contract(spec) is None


def test_load_golden_contract_returns_validated_block(tmp_path: Path) -> None:
    spec = tmp_path / "spec.yaml"
    spec.write_text(
        "golden_contract:\n"
        "  required_labels:\n"
        '    - "Foo"\n'
        '    - ["a b", "a-b"]\n'
        "  source_inventory:\n"
        "    walls:\n"
        "      pattern: '\\\\Wall\\b'\n"
        "      min: 4\n",
        encoding="utf-8",
    )

    contract = load_golden_contract(spec)

    assert contract is not None
    assert contract["required_labels"] == ["Foo", ["a b", "a-b"]]
    assert contract["source_inventory"]["walls"]["min"] == 4


def test_load_golden_contract_rejects_malformed_inventory(tmp_path: Path) -> None:
    import pytest

    spec = tmp_path / "spec.yaml"
    spec.write_text(
        "golden_contract:\n"
        "  source_inventory:\n"
        "    walls:\n"
        "      pattern: '\\\\Wall\\b'\n"
        "      min: 'not-an-int'\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_golden_contract(spec)


def test_load_golden_contract_invalid_utf8_is_normalized(tmp_path: Path) -> None:
    import pytest

    spec = tmp_path / "spec.yaml"
    spec.write_bytes(b"golden_contract:\n\xff\n")

    with pytest.raises(ValueError, match="invalid spec.yaml:"):
        load_golden_contract(spec)


_DUMMY_SVG_50_RECTS = (
    "<svg xmlns='http://www.w3.org/2000/svg'>"
    + "".join("<rect width='1' height='1'/>" for _ in range(50))
    + "</svg>"
)


def _write_minimal_export_set(exports: Path, name: str, *, tiff_extension: str = ".tif") -> None:
    """Write the four required export artifacts in minimal but plausible form."""
    exports.mkdir(exist_ok=True)
    (exports / f"{name}.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    Image.new("RGB", (1200, 800), "white").save(exports / f"{name}.png")
    (exports / f"{name}.svg").write_text(_DUMMY_SVG_50_RECTS, encoding="utf-8")
    Image.new("RGB", (1200, 800), "white").save(
        exports / f"{name}{tiff_extension}",
        dpi=(600, 600),
    )


def _write_minimal_accepted_fixture(fixture: Path) -> None:
    name = fixture.name
    fixture.mkdir()
    (fixture / "spec.yaml").write_text(
        "name: fixture\n"
        "accepted: true\n"
        "golden_contract:\n"
        "  required_labels:\n"
        '    - "Foo"\n'
        "  source_inventory: {}\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text("Foo", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", name)
    (fixture / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "**submission-safe:** true\n\n"
        "OK: no collisions found\n"
        "0 visual clash candidate(s)\n"
        "0 unresolved visual clash(es)\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true\n",
        encoding="utf-8",
    )


def _write_passing_theory_guard(fixture: Path) -> None:
    (fixture / "theory_guard.md").write_text(
        "| ID | Severity | Claim | Check Method | Pass/Fail Evidence |\n"
        "|---|---|---|---|---|\n"
        "| TG-1 | BLOCKER | invariant | source review | Pass: invariant verified. |\n",
        encoding="utf-8",
    )


def _mark_quality_audit_fresh(fixture: Path) -> None:
    fresh = time.time() + 10
    os.utime(fixture / "QUALITY_AUDIT.md", (fresh, fresh))


def _add_quality_audit_disclosure(fixture: Path) -> None:
    audit = fixture / "QUALITY_AUDIT.md"
    audit.write_text(
        audit.read_text(encoding="utf-8") + "disclosure-needed: no\n",
        encoding="utf-8",
    )


def _append_polished_svg_opt_in(fixture: Path) -> None:
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "final_artifact:\n"
        + "  kind: polished_svg\n"
        + "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )


def _append_generated_export_final_artifact(fixture: Path) -> None:
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "final_artifact:\n"
        + "  kind: generated_export\n"
        + "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )


def _append_manifest_only_final_artifact_block(fixture: Path) -> None:
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "final_artifact:\n"
        + "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )


def _append_custom_manifest_polished_svg_opt_in(fixture: Path) -> None:
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "final_artifact:\n"
        + "  kind: polished_svg\n"
        + "  manifest: polish/custom_manifest.yaml\n",
        encoding="utf-8",
    )


def _write_valid_polish_manifest(
    fixture: Path,
    *,
    semantic_change_declared: bool = False,
    backport_required: bool = False,
    reviewer: str = "author",
) -> None:
    name = fixture.name
    polish = fixture / "polish"
    polish.mkdir(exist_ok=True)
    (fixture / "critique.md").write_text("# critique\n", encoding="utf-8")
    (polish / f"{name}.polished.svg").write_text(
        (fixture / "exports" / f"{name}.svg").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (polish / "svg_polish_audit.md").write_text(
        "# SVG Polish Audit\n\nsemantic_change_declared: false\n",
        encoding="utf-8",
    )
    manifest = {
        "schema": "figure-agent.svg-polish-manifest.v1",
        "fixture": name,
        "base": {
            "source_set_hash": final_artifact_source_set_hash(fixture, name),
            "source_tex_hash": file_sha256(fixture / f"{name}.tex"),
            "briefing_hash": file_sha256(fixture / "briefing.md"),
            "spec_hash": file_sha256(fixture / "spec.yaml"),
            "generated_svg_hash": file_sha256(fixture / "exports" / f"{name}.svg"),
            "export_pdf_hash": file_sha256(fixture / "exports" / f"{name}.pdf"),
            "critique_hash": file_sha256(fixture / "critique.md"),
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
            "reviewer": reviewer,
            "reviewed_at": "2026-05-19T00:00:00Z",
            "notes": "visual-only polish",
        },
    }
    write_svg_polish_manifest(polish / "svg_polish_manifest.yaml", manifest)
    if not semantic_change_declared and not backport_required:
        build_svg_semantic_diff_report(fixture)


def _make_passing_accepted_fixture(fixture: Path, monkeypatch) -> None:
    _write_minimal_accepted_fixture(fixture)
    _write_passing_theory_guard(fixture)
    _mark_quality_audit_fresh(fixture)
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")


def test_check_example_basic_mode_skips_label_and_inventory_checks(tmp_path: Path) -> None:
    """Without --require-accepted (and without spec.accepted), only
    artifact-shape gates run."""
    fixture = tmp_path / "tinyfig"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: tinyfig\n", encoding="utf-8")
    (fixture / "tinyfig.tex").write_text("% empty", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "tinyfig")

    failures = check_example(
        fixture, min_svg_elements=40, min_png_width=1000, require_accepted=False
    )

    assert failures == []


def test_check_example_basic_mode_requires_tiff(tmp_path: Path) -> None:
    """The four-export contract (PDF/SVG/TIFF/PNG) must close in basic mode;
    a missing TIFF surfaces as a missing-artifact failure."""
    fixture = tmp_path / "noTiff"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: noTiff\n", encoding="utf-8")
    (fixture / "noTiff.tex").write_text("% empty", encoding="utf-8")
    exports = fixture / "exports"
    exports.mkdir()
    (exports / "noTiff.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    Image.new("RGB", (1200, 800), "white").save(exports / "noTiff.png")
    (exports / "noTiff.svg").write_text(_DUMMY_SVG_50_RECTS, encoding="utf-8")
    # TIFF intentionally absent.

    failures = check_example(fixture, require_accepted=False)

    assert any("missing artifact" in f and "tif" in f for f in failures)


def test_check_example_accepts_tiff_extension(tmp_path: Path) -> None:
    """Either .tif or .tiff satisfies the TIFF requirement."""
    fixture = tmp_path / "longTiff"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: longTiff\n", encoding="utf-8")
    (fixture / "longTiff.tex").write_text("% empty", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "longTiff", tiff_extension=".tiff")

    failures = check_example(fixture, require_accepted=False)

    assert failures == []


def test_check_example_rejects_corrupt_tiff(tmp_path: Path) -> None:
    fixture = tmp_path / "badTiff"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: badTiff\n", encoding="utf-8")
    (fixture / "badTiff.tex").write_text("% empty", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "badTiff")
    (fixture / "exports" / "badTiff.tif").write_bytes(b"II*\x00")

    failures = check_example(fixture, require_accepted=False)

    assert any("invalid TIFF artifact" in failure for failure in failures)


def test_check_example_rejects_low_resolution_tiff(tmp_path: Path) -> None:
    fixture = tmp_path / "lowDpiTiff"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: lowDpiTiff\n", encoding="utf-8")
    (fixture / "lowDpiTiff.tex").write_text("% empty", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "lowDpiTiff")
    Image.new("RGB", (1200, 800), "white").save(
        fixture / "exports" / "lowDpiTiff.tif",
        dpi=(72, 72),
    )

    failures = check_example(fixture, require_accepted=False)

    assert any("TIFF resolution below 600 dpi" in failure for failure in failures)


def test_check_example_auto_escalates_when_spec_has_accepted_key(tmp_path: Path) -> None:
    """A fixture whose spec.yaml declares the `accepted` key automatically
    runs in accepted mode without requiring an explicit --require-accepted
    flag, so a forgotten CLI flag cannot bypass the golden contract."""
    fixture = tmp_path / "autoGolden"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: autoGolden\naccepted: false\n", encoding="utf-8")
    (fixture / "autoGolden.tex").write_text("% empty", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "autoGolden")

    # Note: no require_accepted argument; default None triggers auto-escalate.
    failures = check_example(fixture)

    assert any("golden_contract block missing" in f for f in failures)


def test_check_example_no_require_accepted_overrides_auto_escalate(tmp_path: Path) -> None:
    """An explicit require_accepted=False forces basic mode even when the
    spec declares the `accepted` key — escape hatch for ad-hoc inspection."""
    fixture = tmp_path / "explicitBasic"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: explicitBasic\naccepted: false\n", encoding="utf-8")
    (fixture / "explicitBasic.tex").write_text("% empty", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "explicitBasic")

    failures = check_example(fixture, require_accepted=False)

    assert failures == []


@pytest.mark.parametrize("unsafe_arg", ["examples/../outside", "outside"])
def test_cli_rejects_traversal_or_outside_relative_fixture_path(
    tmp_path: Path,
    unsafe_arg: str,
) -> None:
    (tmp_path / "examples").mkdir()
    fixture = tmp_path / "outside"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: outside\n", encoding="utf-8")
    (fixture / "outside.tex").write_text("% empty\n", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "outside")
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_golden_artifacts.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            unsafe_arg,
            "--no-require-accepted",
        ],
        check=False,
        capture_output=True,
        cwd=tmp_path,
        text=True,
    )

    assert result.returncode == 1
    assert "invalid fixture path" in result.stderr


def test_check_example_require_accepted_fails_without_contract(tmp_path: Path) -> None:
    fixture = tmp_path / "noContract"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: noContract\n", encoding="utf-8")
    (fixture / "noContract.tex").write_text("% empty", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", "noContract")

    failures = check_example(
        fixture,
        min_svg_elements=40,
        min_png_width=1000,
        require_accepted=True,
    )

    assert any("golden_contract block missing" in failure for failure in failures)


def test_require_accepted_mode_requires_theory_guard(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "needsTheory"
    _write_minimal_accepted_fixture(fixture)
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")

    failures = check_example(fixture, require_accepted=True)

    assert "missing theory guard: theory_guard.md" in failures


def test_require_accepted_mode_rejects_failed_blocker_theory_guard(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "failedTheory"
    _write_minimal_accepted_fixture(fixture)
    (fixture / "theory_guard.md").write_text(
        "| ID | Severity | Claim | Check Method | Pass/Fail Evidence |\n"
        "|---|---|---|---|---|\n"
        "| TG-1 | BLOCKER | invariant | source review | FAIL: unresolved topology. |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")

    failures = check_example(fixture, require_accepted=True)

    assert any("theory BLOCKER not passing: TG-1" in failure for failure in failures)


def test_require_accepted_mode_requires_publication_compliance(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "needsPublication"
    _write_minimal_accepted_fixture(fixture)
    _write_passing_theory_guard(fixture)
    (fixture / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "OK: no collisions found\n"
        "0 visual clash candidate(s)\n"
        "0 unresolved visual clash(es)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")

    failures = check_example(fixture, require_accepted=True)

    assert "missing Provenance and Publication Compliance section in QUALITY_AUDIT.md" in failures
    assert "QUALITY_AUDIT.md does not declare submission-safe: true" in failures
    assert "QUALITY_AUDIT.md does not declare disclosure-needed" not in failures


def test_publication_compliance_failures_preserve_legacy_messages(tmp_path: Path) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text("# Quality Audit\n\nsubmission-safe: false\n", encoding="utf-8")

    failures = golden_checks.publication_compliance_failures(
        audit,
        require_disclosure=True,
    )

    assert failures == [
        "missing Provenance and Publication Compliance section in QUALITY_AUDIT.md",
        "QUALITY_AUDIT.md does not declare submission-safe: true",
        "QUALITY_AUDIT.md does not declare disclosure-needed",
    ]


def test_require_accepted_mode_includes_tiff_in_audit_freshness(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "staleTiffAudit"
    _write_minimal_accepted_fixture(fixture)
    _write_passing_theory_guard(fixture)
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")
    old_time = 100.0
    fresh_time = 200.0
    for path in (
        fixture / "spec.yaml",
        fixture / "briefing.md",
        fixture / "staleTiffAudit.tex",
        fixture / "exports" / "staleTiffAudit.pdf",
        fixture / "exports" / "staleTiffAudit.svg",
        fixture / "exports" / "staleTiffAudit.png",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(fixture / "QUALITY_AUDIT.md", (old_time + 1, old_time + 1))
    os.utime(fixture / "exports" / "staleTiffAudit.tif", (fresh_time, fresh_time))

    failures = check_example(fixture, require_accepted=True)

    assert "QUALITY_AUDIT.md is stale or missing" in failures


def test_require_accepted_mode_requires_reference_pack_for_reference_image(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "needsReferencePack"
    _write_minimal_accepted_fixture(fixture)
    _write_passing_theory_guard(fixture)
    (fixture / "spec.yaml").write_text(
        "name: fixture\n"
        "accepted: true\n"
        "reference_image: reference/ref.png\n"
        "golden_contract:\n"
        "  required_labels:\n"
        '    - "Foo"\n'
        "  source_inventory: {}\n",
        encoding="utf-8",
    )
    (fixture / "reference").mkdir()
    (fixture / "reference" / "ref.png").write_bytes(b"png")
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")

    failures = check_example(fixture, require_accepted=True)

    assert any("missing reference pack" in failure for failure in failures)


def test_require_accepted_mode_validates_reference_pack(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "badReferencePack"
    _write_minimal_accepted_fixture(fixture)
    _write_passing_theory_guard(fixture)
    ref_dir = fixture / "reference"
    ref_dir.mkdir()
    (ref_dir / "reference_pack.md").write_text(
        "| File | Role | Use | Do Not Transfer |\n"
        "|---|---|---|---|\n"
        "| `reference/ref.png` |  | style only |  |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")

    failures = check_example(fixture, require_accepted=True)

    assert "reference row missing role: reference/ref.png" in failures
    assert "reference row missing Do Not Transfer boundary: reference/ref.png" in failures


def test_require_accepted_mode_ignores_draft_polish_without_opt_in(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "draftPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    polish = fixture / "polish"
    polish.mkdir()
    (polish / "svg_polish_manifest.yaml").write_text("schema: [unterminated\n", encoding="utf-8")

    failures = check_example(fixture, require_accepted=True)

    assert not any("final artifact" in failure for failure in failures)


def test_require_accepted_mode_ignores_draft_polish_for_generated_export_kind(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "generatedExportFinal"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_generated_export_final_artifact(fixture)
    _mark_quality_audit_fresh(fixture)
    polish = fixture / "polish"
    polish.mkdir()
    (polish / "svg_polish_manifest.yaml").write_text("schema: [unterminated\n", encoding="utf-8")

    failures = check_example(fixture, require_accepted=True)

    assert not any("final artifact" in failure for failure in failures)


def test_require_accepted_mode_ignores_final_artifact_block_without_polished_kind(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "manifestOnlyFinal"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_manifest_only_final_artifact_block(fixture)
    _mark_quality_audit_fresh(fixture)
    polish = fixture / "polish"
    polish.mkdir()
    (polish / "svg_polish_manifest.yaml").write_text("schema: [unterminated\n", encoding="utf-8")

    failures = check_example(fixture, require_accepted=True)

    assert not any("final artifact" in failure for failure in failures)


def test_require_accepted_mode_fails_polished_svg_missing_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "missingFinalPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _mark_quality_audit_fresh(fixture)

    failures = check_example(fixture, require_accepted=True)

    assert "final artifact missing: polish/svg_polish_manifest.yaml" in failures


def test_require_accepted_mode_fails_polished_svg_custom_manifest_path(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "customManifestFinal"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_custom_manifest_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    _mark_quality_audit_fresh(fixture)
    (fixture / "polish" / "svg_polish_manifest.yaml").rename(
        fixture / "polish" / "custom_manifest.yaml"
    )

    failures = check_example(fixture, require_accepted=True)

    assert (
        "final artifact invalid: final_artifact.manifest must be "
        "polish/svg_polish_manifest.yaml"
    ) in failures


def test_require_accepted_mode_malformed_spec_fails_cleanly(tmp_path: Path) -> None:
    fixture = tmp_path / "badSpecFinalArtifact"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fixture / f"{fixture.name}.tex").write_text("% source\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", fixture.name)

    failures = check_example(fixture, require_accepted=True)

    assert any("invalid spec.yaml" in failure for failure in failures)


def test_check_example_default_mode_malformed_spec_fails_cleanly(tmp_path: Path) -> None:
    fixture = tmp_path / "badSpecDefault"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fixture / f"{fixture.name}.tex").write_text("% source\n", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", fixture.name)

    failures = check_example(fixture)

    assert any(failure.startswith("invalid spec.yaml:") for failure in failures)
    assert not any("invalid spec.yaml: invalid spec.yaml:" in failure for failure in failures)


def test_check_example_basic_mode_malformed_spec_fails_cleanly(tmp_path: Path) -> None:
    fixture = tmp_path / "badSpecBasic"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fixture / f"{fixture.name}.tex").write_text("% source\n", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", fixture.name)

    failures = check_example(fixture, require_accepted=False)

    assert any(failure.startswith("invalid spec.yaml:") for failure in failures)


def test_check_example_invalid_utf8_spec_fails_cleanly(tmp_path: Path) -> None:
    fixture = tmp_path / "badSpecEncoding"
    fixture.mkdir()
    (fixture / "spec.yaml").write_bytes(b"accepted: true\n\xff\n")
    (fixture / f"{fixture.name}.tex").write_text("% source\n", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", fixture.name)

    failures = check_example(fixture, require_accepted=True)

    assert failures
    assert all(failure.startswith("invalid spec.yaml:") for failure in failures)


def test_check_example_accepted_mode_malformed_spec_is_not_golden_contract_failure(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "badSpecAccepted"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("final_artifact: [unterminated\n", encoding="utf-8")
    (fixture / f"{fixture.name}.tex").write_text("% source\n", encoding="utf-8")
    _write_minimal_export_set(fixture / "exports", fixture.name)

    failures = check_example(fixture, require_accepted=True)

    assert any(failure.startswith("invalid spec.yaml:") for failure in failures)
    assert not any("invalid golden_contract" in failure for failure in failures)


def test_check_example_accepted_mode_semantic_spec_error_fails_cleanly(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "badStyleAccepted"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8") + "style_profile: future-profile\n",
        encoding="utf-8",
    )
    _mark_quality_audit_fresh(fixture)

    failures = check_example(fixture, require_accepted=True)

    assert any(failure.startswith("invalid spec.yaml:") for failure in failures)
    assert not any("final artifact" in failure for failure in failures)


def test_check_example_basic_mode_skips_semantic_spec_error(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "badStyleBasic"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8") + "style_profile: future-profile\n",
        encoding="utf-8",
    )
    _mark_quality_audit_fresh(fixture)

    failures = check_example(fixture, require_accepted=False)

    assert not any(failure.startswith("invalid spec.yaml:") for failure in failures)


def test_require_accepted_mode_fails_polished_svg_stale_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "staleFinalPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    _add_quality_audit_disclosure(fixture)
    _mark_quality_audit_fresh(fixture)
    (fixture / "polish" / "svg_polish_audit.md").write_text("# changed audit\n", encoding="utf-8")

    failures = check_example(fixture, require_accepted=True)

    assert "final artifact stale: refresh polish/svg_polish_manifest.yaml" in failures


def test_require_accepted_mode_fails_polished_svg_missing_polished_file(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "missingPolishedSvg"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    _add_quality_audit_disclosure(fixture)
    _mark_quality_audit_fresh(fixture)
    (fixture / "polish" / "missingPolishedSvg.polished.svg").unlink()

    failures = check_example(fixture, require_accepted=True)

    assert any("final artifact missing:" in failure for failure in failures)
    assert any("missingPolishedSvg.polished.svg" in failure for failure in failures)


@pytest.mark.parametrize(
    ("semantic_change_declared", "backport_required"),
    ((True, False), (False, True)),
)
def test_require_accepted_mode_fails_polished_svg_semantic_backport_required(
    tmp_path: Path,
    monkeypatch,
    semantic_change_declared: bool,
    backport_required: bool,
) -> None:
    fixture = tmp_path / "blockedFinalPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(
        fixture,
        semantic_change_declared=semantic_change_declared,
        backport_required=backport_required,
    )
    _mark_quality_audit_fresh(fixture)

    failures = check_example(fixture, require_accepted=True)

    assert (
        "final artifact blocked: semantic backport required before acceptance"
        in failures
    )
    assert not any("final artifact invalid:" in failure for failure in failures)


@pytest.mark.parametrize("provenance_field", ("reviewer", "reviewed_at"))
def test_require_accepted_mode_fails_polished_svg_without_required_provenance(
    tmp_path: Path,
    monkeypatch,
    provenance_field: str,
) -> None:
    fixture = tmp_path / "invalidFinalPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    _mark_quality_audit_fresh(fixture)
    manifest = fixture / "polish" / "svg_polish_manifest.yaml"
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    del data["provenance"][provenance_field]
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    failures = check_example(fixture, require_accepted=True)

    assert any("final artifact invalid:" in failure for failure in failures)
    assert any(provenance_field in failure for failure in failures)


def test_require_accepted_mode_reports_malformed_manifest_as_invalid_when_path_says_missing(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "invalidMissingName"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _mark_quality_audit_fresh(fixture)
    polish = fixture / "polish"
    polish.mkdir()
    (polish / "svg_polish_manifest.yaml").write_text("schema: [unterminated\n", encoding="utf-8")

    failures = check_example(fixture, require_accepted=True)

    assert any("final artifact invalid:" in failure for failure in failures)
    assert not any(
        failure.startswith("final artifact missing: invalid YAML") for failure in failures
    )


def test_require_accepted_mode_accepts_fresh_polished_svg_final_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "freshFinalPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    _add_quality_audit_disclosure(fixture)
    _mark_quality_audit_fresh(fixture)

    failures = check_example(fixture, require_accepted=True)

    assert failures == []


def test_require_accepted_mode_polished_svg_still_requires_publication_compliance(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "polishedNeedsPublication"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    (fixture / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "OK: no collisions found\n"
        "0 visual clash candidate(s)\n"
        "0 unresolved visual clash(es)\n",
        encoding="utf-8",
    )
    _mark_quality_audit_fresh(fixture)

    failures = check_example(fixture, require_accepted=True)

    assert "missing Provenance and Publication Compliance section in QUALITY_AUDIT.md" in failures
    assert "QUALITY_AUDIT.md does not declare submission-safe: true" in failures
    assert "QUALITY_AUDIT.md does not declare disclosure-needed" in failures


def test_require_accepted_mode_does_not_mutate_spec_or_generated_exports(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "readOnlyFinalPolish"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    spec = fixture / "spec.yaml"
    spec.write_text(spec.read_text(encoding="utf-8").replace("accepted: true", "accepted: false"))
    _append_polished_svg_opt_in(fixture)
    _write_valid_polish_manifest(fixture)
    _mark_quality_audit_fresh(fixture)
    exports = fixture / "exports"
    before = {
        "spec": spec.read_text(encoding="utf-8"),
        "pdf": (exports / f"{fixture.name}.pdf").read_bytes(),
        "svg": (exports / f"{fixture.name}.svg").read_text(encoding="utf-8"),
        "tif": (exports / f"{fixture.name}.tif").read_bytes(),
        "png": (exports / f"{fixture.name}.png").read_bytes(),
        "manifest": (fixture / "polish" / "svg_polish_manifest.yaml").read_text(
            encoding="utf-8"
        ),
        "polished": (fixture / "polish" / f"{fixture.name}.polished.svg").read_text(
            encoding="utf-8"
        ),
        "polish_audit": (fixture / "polish" / "svg_polish_audit.md").read_text(
            encoding="utf-8"
        ),
    }

    failures = check_example(fixture, require_accepted=True)

    assert "fixture is not marked accepted: true" in failures
    assert spec.read_text(encoding="utf-8") == before["spec"]
    assert (exports / f"{fixture.name}.pdf").read_bytes() == before["pdf"]
    assert (exports / f"{fixture.name}.svg").read_text(encoding="utf-8") == before["svg"]
    assert (exports / f"{fixture.name}.tif").read_bytes() == before["tif"]
    assert (exports / f"{fixture.name}.png").read_bytes() == before["png"]
    assert (
        (fixture / "polish" / "svg_polish_manifest.yaml").read_text(encoding="utf-8")
        == before["manifest"]
    )
    assert (
        (fixture / "polish" / f"{fixture.name}.polished.svg").read_text(encoding="utf-8")
        == before["polished"]
    )
    assert (
        (fixture / "polish" / "svg_polish_audit.md").read_text(encoding="utf-8")
        == before["polish_audit"]
    )


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


def test_require_accepted_mode_rejects_unaccepted_fixture_with_checker_debt(
    tmp_path: Path, monkeypatch
) -> None:
    fixture = tmp_path / "unacceptedCheckerDebt"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    spec = fixture / "spec.yaml"
    spec.write_text(spec.read_text(encoding="utf-8").replace("accepted: true", "accepted: false"))
    (fixture / "QUALITY_AUDIT.md").write_text(
        "# Quality Audit\n\n"
        "**submission-safe:** true\n\n"
        "OK: no collisions found\n"
        "52 visual clash candidate(s)\n"
        "13 unresolved visual clash(es)\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true\n",
        encoding="utf-8",
    )
    _mark_quality_audit_fresh(fixture)

    failures = check_example(
        fixture,
        min_svg_elements=40,
        min_png_width=1000,
        require_accepted=True,
        max_collisions=0,
        max_visual_clashes=0,
    )

    assert "fixture is not marked accepted: true" in failures
    assert not any(failure.startswith("collision budget exceeded") for failure in failures)
    assert "unresolved visual clash budget exceeded: 13 > 0" in failures
