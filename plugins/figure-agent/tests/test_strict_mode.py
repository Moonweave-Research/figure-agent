"""Exit-code tests for the --strict opt-in on collision/clash checkers.

Default behavior is report-only (exit 0). When --strict is passed the
checkers must exit non-zero on any finding, so compile.sh can be made to
fail under FIGURE_AGENT_STRICT=1 without changing default ergonomics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_collisions  # noqa: E402
import check_visual_clash  # noqa: E402

GOLDEN_PDF = (
    REPO_ROOT / "examples" / "golden_trap_depth_picture" / "build" / "golden_trap_depth_picture.pdf"
)


def _require_golden_pdf() -> None:
    if not GOLDEN_PDF.exists():
        pytest.skip(f"{GOLDEN_PDF} not present; run /fig_compile golden_trap_depth_picture")


def test_check_collisions_default_exits_zero(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_collisions.py", str(GOLDEN_PDF)])
    # Golden fixture currently has zero text bbox collisions.
    assert check_collisions.main() == 0


def test_check_collisions_strict_exits_zero_when_no_collisions(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_collisions.py", str(GOLDEN_PDF), "--strict"])
    assert check_collisions.main() == 0


def test_check_visual_clash_default_exits_zero(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_visual_clash.py", str(GOLDEN_PDF)])
    # Default mode reports findings but does not fail.
    assert check_visual_clash.main() == 0


def test_check_visual_clash_strict_fails_on_unsuppressed_clashes(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_visual_clash.py", str(GOLDEN_PDF), "--strict"])
    # Golden fixture currently carries 42 raw clash candidates; strict mode
    # must fail until they are resolved or moved into the false-positive
    # registry.
    assert check_visual_clash.main() == 1


def test_compile_strict_flag_is_documented_in_script() -> None:
    """compile.sh must propagate FIGURE_AGENT_STRICT to --strict so users can
    opt into a hard gate without editing the script."""
    compile_sh = (REPO_ROOT / "scripts" / "compile.sh").read_text(encoding="utf-8")
    assert "FIGURE_AGENT_STRICT" in compile_sh
    assert "--strict" in compile_sh
