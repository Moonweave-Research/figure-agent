from __future__ import annotations

import re
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HANDOFF = PLUGIN_ROOT / "docs/current-sulfur-paper-figure-state.md"
PLAN_MAP = PLUGIN_ROOT / "docs/paper_figure_map.yaml"


def _plan_map() -> dict[str, object]:
    payload = yaml.safe_load(PLAN_MAP.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_handoff_describes_every_machine_resolved_main_figure() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    figures = _plan_map()["figures"]
    assert isinstance(figures, dict)

    for figure, entry in figures.items():
        assert isinstance(entry, dict)
        assert figure.casefold() in text.casefold()
        if entry["status"] == "active_candidate":
            fixture = entry["fixture"]
            assert isinstance(fixture, str)
            assert fixture in text
        else:
            assert entry["status"] == "planned_missing"
            assert "planned" in text


def test_handoff_contains_durable_experiment_contracts() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    for required in (
        "gridless, two-terminal high-voltage",
        "moved manually",
        "grounded conductive substrate",
        "induction-type electrostatic surface voltmeter",
        "not a Kelvin probe or KPFM schematic",
        "Actuation charge",
        "OFF / float",
        "Reversed drive",
        "Maxwell attraction",
        "q_tr E",
    ):
        assert required in text


def test_handoff_does_not_freeze_transient_repository_state() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    forbidden_patterns = (
        r"/Users/",
        r"\.worktrees/",
        r"\bbranch:\s",
        r"\bhead:\s",
        r"source_sha256",
        r"sha256:[0-9a-f]+",
        r"checked=\d+",
        r"blocking_total=\d+",
        r"render=FRESH",
        r"Updated:",
        r"next session",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, text, flags=re.IGNORECASE) is None


def test_historical_cantilever_fixtures_are_non_main_in_machine_map() -> None:
    plan_map = _plan_map()
    non_main = plan_map["non_main"]
    assert isinstance(non_main, dict)
    classified = {
        fixture: classification
        for classification, fixtures in non_main.items()
        for fixture in fixtures
    }

    assert classified["fig5_actuation_mechanism"] == "regression"
    assert classified["fig5_cantilever_mechanism_v1"] == "superseded"
    assert classified["fig3_floating_clip_protocol"] == "si"
