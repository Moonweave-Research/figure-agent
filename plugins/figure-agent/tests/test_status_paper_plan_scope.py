from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import status as status_mod  # noqa: E402

MAP = """\
schema: figure-agent.paper-figure-map.v2
paper_id: paper-demo
figures:
  fig5:
    figure_id: fig5
    role_id: actuation
    status: active_candidate
    fixture: live_fixture
non_main:
  superseded:
    - stale_fixture
"""


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    for name in ("live_fixture", "stale_fixture"):
        fixture = workspace / "examples" / name
        fixture.mkdir(parents=True)
        (fixture / "spec.yaml").write_text("schema: figure-agent.spec.v1\n", encoding="utf-8")
    docs = workspace / "docs"
    docs.mkdir()
    (docs / "paper_figure_map.yaml").write_text(MAP, encoding="utf-8")
    return workspace


def _report_with_stale_binding(examples_dir, map_path):
    return {
        "findings": [
            {
                "code": "non_main_fixture_declares_slot_binding",
                "severity": "blocking",
                "fixture": "stale_fixture",
                "slot": "fig4",
            }
        ],
        "examples_dir": str(examples_dir),
        "map_path": str(map_path),
    }


def test_another_fixtures_stale_binding_does_not_invalidate_this_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(tmp_path)
    monkeypatch.setattr(
        status_mod.check_plan_consistency, "build_report", _report_with_stale_binding
    )

    summary = status_mod._paper_plan_summary(
        workspace / "examples" / "live_fixture", "live_fixture"
    )

    assert summary["state"] == "VALID"
    assert summary["figure_id"] == "fig5"


def test_the_fixture_carrying_the_stale_binding_is_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(tmp_path)
    monkeypatch.setattr(
        status_mod.check_plan_consistency, "build_report", _report_with_stale_binding
    )

    summary = status_mod._paper_plan_summary(
        workspace / "examples" / "stale_fixture", "stale_fixture"
    )

    assert summary["state"] == "INVALID"
    assert summary["reason"] == "non_main_fixture_declares_slot_binding"
    assert [item["fixture"] for item in summary["blocking_findings"]] == ["stale_fixture"]


def test_a_map_level_blocking_finding_still_invalidates_every_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(tmp_path)
    monkeypatch.setattr(
        status_mod.check_plan_consistency,
        "build_report",
        lambda examples_dir, map_path: {
            "findings": [{"code": "map_schema_invalid", "severity": "blocking"}],
            "examples_dir": str(examples_dir),
            "map_path": str(map_path),
        },
    )

    summary = status_mod._paper_plan_summary(
        workspace / "examples" / "live_fixture", "live_fixture"
    )

    assert summary["state"] == "INVALID"
    assert summary["reason"] == "map_schema_invalid"
