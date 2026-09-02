from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_visual_clash_budget as budget  # noqa: E402


def _write_fixture(tmp_path: Path, *, cap: int | None, total: int) -> Path:
    fixture = tmp_path / "examples" / "demo"
    _write_fixture_at(fixture, cap=cap, total=total)
    return fixture


def _write_fixture_at(fixture: Path, *, cap: int | None, total: int) -> Path:
    (fixture / "build").mkdir(parents=True)
    spec = f"name: {fixture.name}\n"
    if cap is not None:
        spec += f"visual_clash_cap: {cap}\n"
    (fixture / "spec.yaml").write_text(spec, encoding="utf-8")
    (fixture / f"{fixture.name}.tex").write_text("% compiled source\n", encoding="utf-8")
    (fixture / "build" / "visual_clash.json").write_text(
        json.dumps(
            {
                "fixture": fixture.name,
                "render_pdf": f"build/{fixture.name}.pdf",
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
            "raw_total": 3,
            "total": 3,
            "cap": 5,
            "over_by": 0,
            "status": "within_budget",
            "source": "canonical",
            "accepted_simplification_count": 0,
            "accepted_false_positive_count": 0,
        },
    }


def test_visual_clash_budget_summary_reports_over_budget(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=2, total=5)

    result = budget.summarize_fixture(fixture)

    assert result["state"] == "needs_action"
    assert result["visual_clash"] == {
        "present": True,
        "raw_total": 5,
        "total": 5,
        "cap": 2,
        "over_by": 3,
        "status": "over_budget",
        "source": "canonical",
        "accepted_simplification_count": 0,
        "accepted_false_positive_count": 0,
    }


def test_visual_clash_budget_summary_reports_missing_report(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: demo\nvisual_clash_cap: 0\n", encoding="utf-8")

    result = budget.summarize_fixture(fixture)

    assert result["state"] == "missing_input"
    assert result["visual_clash"] == {
        "present": False,
        "raw_total": None,
        "total": None,
        "cap": 0,
        "over_by": None,
        "status": "missing_report",
        "source": "canonical",
        "accepted_simplification_count": None,
        "accepted_false_positive_count": None,
    }


def test_visual_clash_budget_excludes_all_explicitly_reviewed_nondefects(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(tmp_path, cap=0, total=5)

    result = budget.summarize_fixture(
        fixture,
        accepted_false_positive_count=1,
        accepted_simplification_count=5,
    )

    assert result["state"] == "pass"
    assert result["visual_clash"]["raw_total"] == 5
    assert result["visual_clash"]["total"] == 0
    assert result["visual_clash"]["accepted_simplification_count"] == 5
    assert result["visual_clash"]["accepted_false_positive_count"] == 1


def test_visual_clash_budget_defaults_missing_cap_to_zero(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=None, total=1)

    try:
        budget.check_fixture(fixture)
    except budget.VisualClashBudgetError as exc:
        assert str(exc) == "demo: visual clash budget exceeded: 1 > 0"
    else:
        raise AssertionError("expected VisualClashBudgetError")


def test_visual_clash_budget_uses_declared_current_candidate_report(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, cap=0, total=9)
    candidate_root = fixture / "review" / "candidate"
    (candidate_root / "build").mkdir(parents=True)
    source = candidate_root / "candidate.tex"
    source.write_text("% candidate", encoding="utf-8")
    (candidate_root / "build" / "candidate.pdf").write_bytes(b"%PDF")
    (candidate_root / "build" / "visual_clash.json").write_text(
        json.dumps({"total": 2}), encoding="utf-8"
    )
    import hashlib

    (fixture / "review" / "current-candidate.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.current-candidate-pointer.v1",
                "fixture": "demo",
                "candidate_root": "review/candidate",
                "source_path": "candidate.tex",
                "source_sha256": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
                "evidence": {
                    "render_pdf": "build/candidate.pdf",
                    "visual_clash": "build/visual_clash.json",
                },
            }
        ),
        encoding="utf-8",
    )

    result = budget.summarize_fixture(fixture)

    assert result["visual_clash"]["source"] == "current_candidate"
    assert result["visual_clash"]["raw_total"] == 2


def test_visual_clash_budget_fails_when_report_is_missing(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: demo\nvisual_clash_cap: 0\n", encoding="utf-8")
    (fixture / "demo.tex").write_text("% compiled source\n", encoding="utf-8")

    try:
        budget.check_fixture(fixture)
    except budget.VisualClashBudgetError as exc:
        assert "missing build/visual_clash.json" in str(exc)
    else:
        raise AssertionError("expected VisualClashBudgetError")


def test_visual_clash_budget_skips_review_only_fixture_without_tex_source(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(tmp_path, cap=2, total=1)
    review_only = examples / "composition_review"
    review_only.mkdir()
    (review_only / "spec.yaml").write_text(
        "name: composition_review\nvisual_clash_cap: 0\n", encoding="utf-8"
    )
    (review_only / "briefing.md").write_text("review-only\n", encoding="utf-8")

    results = budget.check_targets([examples])

    assert results == [
        {"fixture": "composition_review", "total": None, "cap": None, "status": "no_tex_source"},
        {"fixture": "demo", "total": 1, "cap": 2, "status": "ok"},
    ]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_visual_clash_budget.py", "examples"])
    assert budget.main() == 0
    out = capsys.readouterr().out
    assert "SKIP composition_review: no composition_review.tex source" in out
    assert "OK demo: visual_clash total 1 <= cap 2" in out


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
    _write_fixture(tmp_path, cap=0, total=2)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_visual_clash_budget.py", "demo"])

    assert budget.main() == 1
    captured = capsys.readouterr()
    assert "visual clash budget exceeded: 2 > 0" in captured.err


def test_visual_clash_budget_cli_accepts_examples_and_absolute_fixture_under_examples(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fixture = _write_fixture(tmp_path, cap=1, total=0)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(sys, "argv", ["check_visual_clash_budget.py", "examples"])
    assert budget.main() == 0
    assert "OK demo: visual_clash total 0 <= cap 1" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["check_visual_clash_budget.py", str(fixture.resolve())])
    assert budget.main() == 0
    assert "OK demo: visual_clash total 0 <= cap 1" in capsys.readouterr().out


def test_visual_clash_budget_cli_rejects_traversal_or_outside_relative_target(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    outside = _write_fixture_at(tmp_path / "outside", cap=1, total=0)
    _write_fixture_at(tmp_path / "examples" / "demo", cap=1, total=0)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        sys,
        "argv",
        ["check_visual_clash_budget.py", "examples/../outside"],
    )
    assert budget.main() == 1
    assert "invalid target path" in capsys.readouterr().err

    monkeypatch.setattr(sys, "argv", ["check_visual_clash_budget.py", outside.name])
    assert budget.main() == 1
    assert "relative fixture names must resolve under examples/" in capsys.readouterr().err
    assert not (outside / "visual_clash_budget.json").exists()
