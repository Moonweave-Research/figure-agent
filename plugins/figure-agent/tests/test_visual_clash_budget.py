from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_visual_clash_budget as budget  # noqa: E402


def _write_fixture(tmp_path: Path, *, cap: int | None, total: int) -> Path:
    fixture = tmp_path / "examples" / "demo"
    (fixture / "build").mkdir(parents=True)
    spec = "name: demo\n"
    if cap is not None:
        spec += f"visual_clash_cap: {cap}\n"
    (fixture / "spec.yaml").write_text(spec, encoding="utf-8")
    (fixture / "build" / "visual_clash.json").write_text(
        json.dumps(
            {
                "fixture": "demo",
                "render_pdf": "build/demo.pdf",
                "candidates": [],
                "total": total,
            }
        ),
        encoding="utf-8",
    )
    return fixture


def test_visual_clash_budget_passes_when_total_is_within_declared_cap(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=5, total=5)

    result = budget.check_fixture(fixture)

    assert result == {"fixture": "demo", "total": 5, "cap": 5, "status": "ok"}


def test_visual_clash_budget_summary_reports_pass_state(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=5, total=3)

    result = budget.summarize_fixture(fixture)

    assert result == {
        "schema": "figure-agent.warning-budget.v1",
        "fixture": "demo",
        "state": "pass",
        "reason": "visual clash warnings are within budget",
        "visual_clash": {
            "present": True,
            "total": 3,
            "cap": 5,
            "over_by": 0,
            "status": "within_budget",
        },
    }


def test_visual_clash_budget_summary_reports_over_budget(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=2, total=5)

    result = budget.summarize_fixture(fixture)

    assert result["state"] == "needs_action"
    assert result["visual_clash"] == {
        "present": True,
        "total": 5,
        "cap": 2,
        "over_by": 3,
        "status": "over_budget",
    }


def test_visual_clash_budget_summary_reports_missing_report(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: demo\nvisual_clash_cap: 0\n", encoding="utf-8")

    result = budget.summarize_fixture(fixture)

    assert result["state"] == "missing_input"
    assert result["visual_clash"] == {
        "present": False,
        "total": None,
        "cap": 0,
        "over_by": None,
        "status": "missing_report",
    }


def test_visual_clash_budget_defaults_missing_cap_to_zero(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=None, total=1)

    try:
        budget.check_fixture(fixture)
    except budget.VisualClashBudgetError as exc:
        assert str(exc) == "demo: visual clash budget exceeded: 1 > 0"
    else:
        raise AssertionError("expected VisualClashBudgetError")


def test_visual_clash_budget_fails_when_report_is_missing(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: demo\nvisual_clash_cap: 0\n", encoding="utf-8")

    try:
        budget.check_fixture(fixture)
    except budget.VisualClashBudgetError as exc:
        assert "missing build/visual_clash.json" in str(exc)
    else:
        raise AssertionError("expected VisualClashBudgetError")


def test_visual_clash_budget_checks_all_fixture_dirs_under_examples(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(tmp_path, cap=2, total=1)
    skipped = examples / "_scratch"
    skipped.mkdir()

    results = budget.check_targets([examples])

    assert results == [{"fixture": "demo", "total": 1, "cap": 2, "status": "ok"}]


def test_visual_clash_budget_main_returns_one_on_budget_failure(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fixture = _write_fixture(tmp_path, cap=0, total=2)
    monkeypatch.setattr(sys, "argv", ["check_visual_clash_budget.py", str(fixture)])

    assert budget.main() == 1
    captured = capsys.readouterr()
    assert "visual clash budget exceeded: 2 > 0" in captured.err
