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


def _valid_v2_pack(fixture: str = "demo", *, lever_count: int = 1) -> str:
    levers = []
    for index in range(lever_count):
        suffix = "" if index == 0 else f"_{index}"
        levers.append(
            f"""
  - id: maturity_restraint{suffix}
    dimension: maturity
    intent: Make the figure read as controlled editorial science illustration.
    priority: required
    positive_signals:
      - restrained label scale
    anti_patterns:
      - poster-like saturation
    allowed_adjustments:
      - reduce non-essential label prominence
    forbidden_adjustments:
      - change mechanism meaning
    default_route: tikz_patch
""".rstrip()
        )
    return f"""
schema: figure-agent.aesthetic-intent.v2
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
aesthetic_levers:
{chr(10).join(levers)}
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


def test_load_aesthetic_intent_accepts_valid_v2_pack(tmp_path: Path) -> None:
    path = _write_pack(tmp_path, _valid_v2_pack())

    pack = aesthetic_intent.load_aesthetic_intent(path)

    assert pack["schema"] == "figure-agent.aesthetic-intent.v2"
    assert pack["aesthetic_levers"][0]["id"] == "maturity_restraint"
    assert pack["aesthetic_levers"][0]["dimension"] == "maturity"
    assert pack["aesthetic_levers"][0]["priority"] == "required"
    assert pack["aesthetic_levers"][0]["default_route"] == "tikz_patch"


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


def test_load_aesthetic_intent_rejects_invalid_v2_dimension(tmp_path: Path) -> None:
    path = _write_pack(
        tmp_path,
        _valid_v2_pack().replace("dimension: maturity", "dimension: cuteness", 1),
    )

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="dimension"):
        aesthetic_intent.load_aesthetic_intent(path)


def test_load_aesthetic_intent_rejects_invalid_v2_route(tmp_path: Path) -> None:
    path = _write_pack(
        tmp_path,
        _valid_v2_pack().replace("default_route: tikz_patch", "default_route: magic", 1),
    )

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="default_route"):
        aesthetic_intent.load_aesthetic_intent(path)


def test_load_aesthetic_intent_rejects_duplicate_v2_lever_ids(tmp_path: Path) -> None:
    path = _write_pack(
        tmp_path,
        _valid_v2_pack(lever_count=2).replace("maturity_restraint_1", "maturity_restraint"),
    )

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="duplicated"):
        aesthetic_intent.load_aesthetic_intent(path)


def test_load_aesthetic_intent_rejects_more_than_ten_v2_levers(tmp_path: Path) -> None:
    path = _write_pack(tmp_path, _valid_v2_pack(lever_count=11))

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="at most 10"):
        aesthetic_intent.load_aesthetic_intent(path)


def test_load_optional_aesthetic_intent_rejects_fixture_mismatch(tmp_path: Path) -> None:
    path = _write_pack(tmp_path, _valid_pack(fixture="wrong"), fixture="demo")

    with pytest.raises(aesthetic_intent.AestheticIntentError, match="fixture"):
        aesthetic_intent.load_optional_aesthetic_intent(path.parent)


def test_load_optional_aesthetic_intent_returns_none_when_missing(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)

    assert aesthetic_intent.load_optional_aesthetic_intent(example_dir) is None
