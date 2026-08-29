"""The durable clash report must record known-false-positive suppression."""

from __future__ import annotations

import sys
from pathlib import Path

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
