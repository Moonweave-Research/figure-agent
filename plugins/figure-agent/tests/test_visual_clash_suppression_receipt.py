"""The durable clash report must record known-false-positive suppression."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "checks"))

import check_visual_clash  # noqa: E402


def _payload(suppressed: int) -> dict:
    return check_visual_clash.visual_clash_payload(
        Path("build/demo.pdf"),
        [],
        fixture="demo",
        suppressed_total=suppressed,
    )


def test_suppression_is_recorded_in_the_report() -> None:
    """Suppression happens before the report is written, so a filtered run and
    a genuinely clean one used to be identical to every downstream gate."""
    assert _payload(6)["suppressed_total"] == 6


def test_an_unsuppressed_report_keeps_its_legacy_shape() -> None:
    """Report-mode snapshots are pinned byte-for-byte, so the field appears
    only when something was actually suppressed."""
    payload = _payload(0)

    assert "suppressed_total" not in payload
    assert payload["total"] == 0


def _issue(text: str) -> check_visual_clash.VisualIssue:
    return check_visual_clash.VisualIssue(
        kind="glyph_overlap",
        text=text,
        detail="overlap 1.0px",
        bbox=(0, 0, 10, 10),
    )


def test_clash_candidate_binds_to_the_node_line_that_made_it() -> None:
    """tex_lines gated critique_adjudication's auto-apply route while nothing
    ever filled it, so only a reviewer typing line numbers by hand could open
    that path."""
    tex = "\\node at (0,0) {occupancy};\n\\node at (1,0) {recovery};\n"

    payload = check_visual_clash.visual_clash_payload(
        Path("build/demo.pdf"),
        [_issue("recovery")],
        fixture="demo",
        source_tex=tex,
    )

    assert payload["candidates"][0]["tex_lines"] == [2, 2]


def test_an_ambiguous_or_absent_label_stays_unbound() -> None:
    tex = "\\node at (0,0) {field-on charging};\n\\node at (1,0) {field-on hold};\n"

    ambiguous = check_visual_clash.visual_clash_payload(
        Path("build/demo.pdf"), [_issue("field-on")], fixture="demo", source_tex=tex
    )
    without_source = check_visual_clash.visual_clash_payload(
        Path("build/demo.pdf"), [_issue("field-on charging")], fixture="demo"
    )

    assert ambiguous["candidates"][0]["tex_lines"] is None
    assert without_source["candidates"][0]["tex_lines"] is None


def test_report_records_whether_a_source_was_bound_at_all() -> None:
    """A null tex_lines meant either "no source offered" or "source offered and
    unreadable", and no reader could tell those apart."""
    assert _payload(0)["tex_binding"] == "not_requested"

    bound = check_visual_clash.visual_clash_payload(
        Path("build/demo.pdf"),
        [],
        fixture="demo",
        source_tex="\\node at (0,0) {occupancy};\n",
        tex_binding="bound",
    )
    unreadable = check_visual_clash.visual_clash_payload(
        Path("build/demo.pdf"), [], fixture="demo", tex_binding="source_missing"
    )

    assert bound["tex_binding"] == "bound"
    assert unreadable["tex_binding"] == "source_missing"


def test_an_unrecognised_binding_state_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown tex_binding state"):
        check_visual_clash.visual_clash_payload(
            Path("build/demo.pdf"), [], fixture="demo", tex_binding="probably_fine"
        )


def test_an_unreadable_explicit_source_exits_instead_of_reporting(tmp_path: Path) -> None:
    """compile.sh passes --source unconditionally, so a copy that cannot be read
    used to produce a clean-looking report with every binding silently absent."""
    pdf = tmp_path / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
    unreadable = tmp_path / "missing.tex"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "checks" / "check_visual_clash.py"),
            str(pdf),
            "--source",
            str(unreadable),
            "--json-output",
            str(tmp_path / "visual_clash.json"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--source is unreadable" in result.stderr
    assert not (tmp_path / "visual_clash.json").exists()
