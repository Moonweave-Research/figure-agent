"""Tests for golden fixture artifact quality gates."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_golden_artifacts as golden_checks  # noqa: E402
import human_attestation  # noqa: E402
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


def test_extract_pdf_text_tolerates_non_utf8_pdftotext_stdout(tmp_path: Path, monkeypatch) -> None:
    """pdftotext can emit non-UTF8 bytes (symbol/Latin-1/Greek glyphs) on
    `-layout -`; extract_pdf_text must decode-replace instead of crashing,
    so the --require-accepted release gate returns a verdict rather than a
    UnicodeDecodeError traceback. ASCII label tokens survive the U+FFFD
    substitution."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    fake_pdftotext = bin_dir / "pdftotext"
    fake_pdftotext.write_text(
        f'#!{sys.executable}\nimport sys\nsys.stdout.buffer.write(b"Foo\\xffBar\\n")\n',
        encoding="utf-8",
    )
    fake_pdftotext.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])

    text = golden_checks.extract_pdf_text(tmp_path / "any.pdf")

    assert isinstance(text, str)
    assert "Foo" in text
    assert "Bar" in text


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
def _make_passing_accepted_fixture(fixture: Path, monkeypatch) -> None:
    _write_minimal_accepted_fixture(fixture)
    monkeypatch.setenv("HOME", str(fixture.parent / "home"))
    human_attestation.write_attestation(fixture)
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
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "checks"
        / "check_golden_artifacts.py"
    )

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


def test_require_accepted_mode_requires_human_attestation(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "attestationRequired"
    _write_minimal_accepted_fixture(fixture)
    _write_passing_theory_guard(fixture)
    _mark_quality_audit_fresh(fixture)
    monkeypatch.setattr(golden_checks, "extract_pdf_text", lambda _path: "Foo")

    failures = check_example(fixture, require_accepted=True)

    assert "human attestation invalid: missing_human_attestation" in failures


def test_require_accepted_mode_requires_theory_guard(tmp_path: Path, monkeypatch) -> None:
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


def test_require_accepted_mode_requires_publication_compliance(tmp_path: Path, monkeypatch) -> None:
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


def test_require_accepted_mode_requires_disclosure_for_non_generated_final_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fixture = tmp_path / "polishedFinal"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    spec = fixture / "spec.yaml"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "final_artifact:\n"
        + "  kind: polished_svg\n"
        + "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )
    human_attestation.write_attestation(fixture)

    failures = check_example(fixture, require_accepted=True)

    assert "QUALITY_AUDIT.md does not declare disclosure-needed" in failures


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


def test_require_accepted_gate_rejects_hash_stamped_audit_after_source_change(
    tmp_path: Path, monkeypatch
) -> None:
    """Through the real release gate: a hash-stamped audit whose source content
    changed is stale even when every mtime is preserved (the git-clone case),
    and the prepended front-matter block does not disturb the other readers."""
    fixture = tmp_path / "hashStampedGate"
    _make_passing_accepted_fixture(fixture, monkeypatch)
    golden_checks.stamp_audit_input_hash(fixture, golden_checks.audit_source_paths(fixture))

    # Sanity: stamped + unchanged passes the freshness gate.
    failures = check_example(fixture, require_accepted=True)
    assert "QUALITY_AUDIT.md is stale or missing" not in failures

    # Mutate a source after stamping, then make every artifact mtime-fresh so the
    # legacy mtime check alone would still pass.
    (fixture / "hashStampedGate.tex").write_text("Foo changed", encoding="utf-8")
    audit_mtime = (fixture / "QUALITY_AUDIT.md").stat().st_mtime
    for path in golden_checks.audit_source_paths(fixture):
        os.utime(path, (audit_mtime - 5, audit_mtime - 5))

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


def test_require_accepted_mode_validates_reference_pack(tmp_path: Path, monkeypatch) -> None:
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


def test_check_example_basic_mode_skips_semantic_spec_error(tmp_path: Path, monkeypatch) -> None:
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


def _write_hash_freshness_fixture(fixture: Path) -> tuple[Path, ...]:
    """Minimal source set plus an audit, returning the hashed source paths."""
    fixture.mkdir()
    spec = fixture / "spec.yaml"
    briefing = fixture / "briefing.md"
    tex = fixture / "fixture.tex"
    exports = fixture / "exports"
    exports.mkdir()
    pdf = exports / "fixture.pdf"
    svg = exports / "fixture.svg"
    tif = exports / "fixture.tif"
    png = exports / "fixture.png"
    spec.write_text("name: fixture\n", encoding="utf-8")
    briefing.write_text("brief", encoding="utf-8")
    tex.write_text("source", encoding="utf-8")
    for artifact in (pdf, svg, tif, png):
        artifact.write_text("content", encoding="utf-8")
    return (spec, briefing, tex, pdf, svg, tif, png)


def test_audit_is_fresh_with_hash_is_stale_when_source_changes_despite_mtime(
    tmp_path: Path,
) -> None:
    """The hole: a hash-bearing audit must catch content drift even when every
    source mtime is preserved at/below the audit mtime (the git-clone case)."""
    fixture = tmp_path / "fixture"
    sources = _write_hash_freshness_fixture(fixture)
    golden_checks.stamp_audit_input_hash(fixture, sources)

    # Mutate a source after stamping, then make every mtime mtime-fresh.
    sources[2].write_text("source-changed", encoding="utf-8")
    audit_mtime = (fixture / "QUALITY_AUDIT.md").stat().st_mtime
    for path in sources:
        os.utime(path, (audit_mtime - 5, audit_mtime - 5))

    assert not audit_is_fresh(fixture, sources)


def test_audit_is_fresh_with_hash_survives_relocation(tmp_path: Path) -> None:
    """Content-based freshness must be invariant to where the fixture lives, so
    a timestamp-preserving copy (git clone / cp -p) stays fresh."""
    fixture = tmp_path / "fixture"
    sources = _write_hash_freshness_fixture(fixture)
    golden_checks.stamp_audit_input_hash(fixture, sources)
    assert audit_is_fresh(fixture, sources)

    relocated = tmp_path / "relocated"
    shutil.copytree(fixture, relocated)
    relocated_sources = tuple(relocated / path.relative_to(fixture) for path in sources)
    assert audit_is_fresh(relocated, relocated_sources)


def test_audit_is_fresh_without_hash_falls_back_to_mtime(tmp_path: Path) -> None:
    """Legacy audits (golden fixture) carry no hash and must keep the mtime gate."""
    fixture = tmp_path / "fixture"
    sources = _write_hash_freshness_fixture(fixture)
    audit = fixture / "QUALITY_AUDIT.md"
    audit.write_text("# Quality Audit\n\nno front matter here\n", encoding="utf-8")
    audit_mtime = 200.0
    os.utime(audit, (audit_mtime, audit_mtime))
    for path in sources:
        os.utime(path, (audit_mtime - 5, audit_mtime - 5))
    assert audit_is_fresh(fixture, sources)

    os.utime(sources[0], (audit_mtime + 5, audit_mtime + 5))
    assert not audit_is_fresh(fixture, sources)


def test_stamp_audit_input_hash_roundtrip_is_fresh(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    sources = _write_hash_freshness_fixture(fixture)
    (fixture / "QUALITY_AUDIT.md").write_text("# Quality Audit\n\nbody text\n", encoding="utf-8")
    golden_checks.stamp_audit_input_hash(fixture, sources)
    assert audit_is_fresh(fixture, sources)
    # Stamping preserves the original body so regex readers stay intact.
    assert "body text" in (fixture / "QUALITY_AUDIT.md").read_text(encoding="utf-8")


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
