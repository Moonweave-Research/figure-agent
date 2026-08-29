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
