"""Golden Target 001 fixture contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "examples" / "golden_trap_depth_picture"

pytestmark = pytest.mark.skipif(
    not FIXTURE.is_dir(),
    reason="optional golden_trap_depth_picture real fixture is not present in this plugin tree",
)

REQUIRED_SOURCE_TOKENS = [
    "Experiment",
    "Mathematical interpretation",
    "Molecular origin",
    "I(t)",
    "slope",
    "Discharge",
    "Debye",
    "tau_d",
    "n",
    "g(E_t)",
    "shallow",
    "deep",
    "localized traps",
    "S-rich segments",
    "chemical origin",
    "physical origin",
    "converged trap-depth picture",
    "Energy",
    "CB",
    "VB",
    "E_t",
]


def test_golden_target_fixture_files_exist() -> None:
    required = [
        FIXTURE / "spec.yaml",
        FIXTURE / "briefing.md",
        FIXTURE / "reference" / "golden_target_001.png",
    ]

    missing = [path for path in required if not path.exists()]

    assert missing == []


def test_golden_target_tex_contains_required_source_tokens() -> None:
    """Source smoke only; rendered-label acceptance is checked after compile."""
    tex_path = FIXTURE / "golden_trap_depth_picture.tex"
    text = tex_path.read_text(encoding="utf-8")

    missing = [label for label in REQUIRED_SOURCE_TOKENS if label not in text]

    assert missing == []
    assert r"font=\textsf{" not in text


def test_golden_target_exports_exist_when_fixture_is_accepted() -> None:
    exports = FIXTURE / "exports"
    expected = [
        exports / "golden_trap_depth_picture.pdf",
        exports / "golden_trap_depth_picture.svg",
        exports / "golden_trap_depth_picture.tif",
        exports / "golden_trap_depth_picture.png",
    ]

    missing = [path for path in expected if not path.exists()]

    assert missing == []
