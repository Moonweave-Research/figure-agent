from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import aesthetic_intent  # noqa: E402


def _write_pack(tmp_path: Path, text: str, *, fixture: str = "demo") -> Path:
    example_dir = tmp_path / "examples" / fixture
    example_dir.mkdir(parents=True)
    path = example_dir / "aesthetic_intent.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _valid_pack(fixture: str = "demo") -> str:
    return f"""
schema: figure-agent.aesthetic-intent.v1
fixture: {fixture}
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantically correct TikZ lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
""".lstrip()


def test_load_aesthetic_intent_accepts_valid_pack(tmp_path: Path) -> None:
    path = _write_pack(tmp_path, _valid_pack())

    pack = aesthetic_intent.load_aesthetic_intent(path)

    assert pack["schema"] == "figure-agent.aesthetic-intent.v1"
    assert pack["fixture"] == "demo"
    assert pack["visual_maturity"] == "editorial"
    assert pack["design_principles"][0]["id"] == "mature_restraint"
    assert pack["must_avoid"][0]["severity"] == "MAJOR"
    assert pack["polish_triggers"][0]["recommended_path"] == "ready_for_svg_polish"


def test_load_aesthetic_intent_rejects_invalid_enum(tmp_path: Path) -> None:
    path = _write_pack(
        tmp_path,
        _valid_pack().replace("visual_maturity: editorial", "visual_maturity: cute"),
    )

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="visual_maturity"):
        aesthetic_intent.load_aesthetic_intent(path)


def test_load_aesthetic_intent_rejects_duplicate_item_ids(tmp_path: Path) -> None:
    path = _write_pack(
        tmp_path,
        _valid_pack().replace(
            "must_avoid:\n  - id: toy_diagram",
            (
                "must_avoid:\n"
                "  - id: toy_diagram\n"
                "    pattern: rounded generic blocks\n"
                "    severity: MINOR\n"
                "  - id: toy_diagram"
            ),
        ),
    )

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="duplicated"):
        aesthetic_intent.load_aesthetic_intent(path)


def test_load_optional_aesthetic_intent_rejects_fixture_mismatch(tmp_path: Path) -> None:
    path = _write_pack(tmp_path, _valid_pack(fixture="wrong"), fixture="demo")

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="fixture"):
        aesthetic_intent.load_optional_aesthetic_intent(path.parent)


def test_load_optional_aesthetic_intent_returns_none_when_missing(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)

    assert aesthetic_intent.load_optional_aesthetic_intent(example_dir) is None
