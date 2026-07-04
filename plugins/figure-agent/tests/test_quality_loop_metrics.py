from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_loop_metrics  # noqa: E402


def _record(
    fixture: str,
    candidate_id: str,
    *,
    human_decision_kind: str | None = None,
    human_label: str | None = None,
    apply_status: str = "applied",
    quality_movement: str | None = "neutral",
    candidate_hash: str | None = None,
    changed_pixel_ratio: float | None = 0.01,
) -> dict:
    return {
        "schema": "figure-agent.experience-record.v1",
        "fixture": fixture,
        "created_at": "2026-06-08T00:00:00Z",
        "state": {
            "target": {"panel": "F", "subregion_key": "sha256:" + "1" * 64},
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": "apparatus_strengthen",
            "candidate_hash": candidate_hash or f"sha256:{candidate_id.lower()}",
        },
        "outcome": {
            "apply_status": apply_status,
            "quality_movement": quality_movement,
            "human_label": human_label,
            "human_decision_kind": human_decision_kind,
            "pixel_delta": {"changed_pixel_ratio": changed_pixel_ratio},
        },
    }


def _write_log(plugin_root: Path, fixture: str, rows: list[dict]) -> None:
    path = plugin_root / "docs" / "experience-log" / f"{fixture}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_loop_metrics_measures_auto_accept_precision_from_later_reverts(
    tmp_path: Path,
) -> None:
    plugin_root = tmp_path / "plugin"
    _write_log(
        plugin_root,
        "fig_demo",
        [
            _record(
                "fig_demo",
                "CAND001",
                human_decision_kind="auto_accept",
                human_label="accept",
            ),
            _record(
                "fig_demo",
                "CAND001",
                human_label="reject",
                quality_movement="regressed",
            ),
            _record(
                "fig_demo",
                "CAND002",
                human_decision_kind="auto_accept",
                human_label="accept",
            ),
        ],
    )

    payload = quality_loop_metrics.build_loop_metrics(plugin_root=plugin_root)

    assert payload["schema"] == "figure-agent.loop-metrics.v1"
    precision = payload["metrics"]["auto_accept_precision"]
    assert precision["auto_accepted_count"] == 2
    assert precision["reverted_count"] == 1
    assert precision["precision"] == 0.5
    assert precision["state"] == "measured"
    assert precision["reverted_candidates"] == ["fig_demo:CAND001"]


def test_loop_metrics_reports_unmeasured_without_auto_accepts(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    _write_log(
        plugin_root,
        "fig_demo",
        [_record("fig_demo", "CAND001", human_label="accept")],
    )

    payload = quality_loop_metrics.build_loop_metrics(plugin_root=plugin_root)

    precision = payload["metrics"]["auto_accept_precision"]
    assert precision["state"] == "unmeasured"
    assert precision["precision"] is None
    assert precision["auto_accepted_count"] == 0


def test_loop_metrics_measures_wasted_iteration_rate_from_repeats_and_noops(
    tmp_path: Path,
) -> None:
    plugin_root = tmp_path / "plugin"
    repeated_hash = "sha256:" + "a" * 64
    _write_log(
        plugin_root,
        "fig_demo",
        [
            _record("fig_demo", "CAND001", candidate_hash=repeated_hash),
            _record("fig_demo", "CAND002", candidate_hash=repeated_hash),
            _record("fig_demo", "CAND003", changed_pixel_ratio=0.0),
            _record("fig_demo", "CAND004", changed_pixel_ratio=0.02),
        ],
    )

    payload = quality_loop_metrics.build_loop_metrics(plugin_root=plugin_root)

    wasted = payload["metrics"]["wasted_iteration_rate"]
    assert wasted["iteration_count"] == 4
    assert wasted["wasted_count"] == 2
    assert wasted["rate"] == 0.5
    assert wasted["wasted_candidates"] == ["fig_demo:CAND002", "fig_demo:CAND003"]


def _write_loop_run(
    workspace: Path,
    run_id: str,
    *,
    created_at: str,
    completed_at: str | None = None,
    fixture: str = "fig_demo",
    stop_causes: list[str],
    auto_remedy_status: str | None,
) -> None:
    run_dir = workspace / ".scratch" / "fig-loop-runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.loop-run.v1",
                "created_at": created_at,
                "started_at": created_at,
                "completed_at": completed_at or created_at,
                "fixture": fixture,
                "run_id": run_id,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    auto_remedy = (
        {"status": auto_remedy_status, "cause": "critique_missing"}
        if auto_remedy_status is not None
        else None
    )
    (run_dir / "iteration_001.json").write_text(
        json.dumps(
            {
                "stop_routes": [
                    {
                        "subregion_id": f"sel:{index}",
                        "stop_cause": cause,
                    }
                    for index, cause in enumerate(stop_causes, start=1)
                ],
                "auto_remedy": auto_remedy,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_loop_metrics_reports_stop_cause_histogram_and_auto_remedy_fraction(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_loop_run(
        workspace,
        "RUN001",
        created_at="2026-07-04T00:00:00Z",
        stop_causes=["lever_exhausted", "decision_weak"],
        auto_remedy_status="remedied",
    )
    _write_loop_run(
        workspace,
        "RUN002",
        created_at="2026-07-05T00:00:00Z",
        stop_causes=["decision_weak"],
        auto_remedy_status="remedy_ineffective",
    )

    payload = quality_loop_metrics.build_loop_metrics(
        plugin_root=tmp_path / "plugin",
        workspace_root=workspace,
    )

    stop_metrics = payload["metrics"]["stop_cause_histogram"]
    assert stop_metrics["run_count"] == 2
    assert stop_metrics["route_count"] == 3
    assert stop_metrics["total_histogram"] == {
        "decision_weak": 2,
        "lever_exhausted": 1,
    }
    assert stop_metrics["auto_remedied_count"] == 1
    assert stop_metrics["auto_remedied_fraction"] == 0.5
    assert stop_metrics["histogram_by_week"]["2026-W27"] == {
        "decision_weak": 2,
        "lever_exhausted": 1,
    }


def test_loop_metrics_reports_experience_log_growth_per_run(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    _write_loop_run(
        workspace,
        "RUN001",
        created_at="2026-07-04T00:00:00Z",
        completed_at="2026-07-04T00:10:00Z",
        stop_causes=[],
        auto_remedy_status=None,
    )
    _write_loop_run(
        workspace,
        "RUN002",
        created_at="2026-07-04T00:20:00Z",
        completed_at="2026-07-04T00:30:00Z",
        stop_causes=[],
        auto_remedy_status=None,
    )
    rows = [
        {**_record("fig_demo", "CAND001"), "created_at": "2026-07-04T00:01:00Z"},
        {**_record("fig_demo", "CAND002"), "created_at": "2026-07-04T00:02:00Z"},
    ]
    _write_log(plugin_root, "fig_demo", rows)

    payload = quality_loop_metrics.build_loop_metrics(
        plugin_root=plugin_root,
        workspace_root=workspace,
    )

    growth = payload["metrics"]["experience_log_growth"]
    assert growth["run_count"] == 2
    assert growth["total_records_attributed"] == 2
    assert growth["unassigned_record_count"] == 0
    assert growth["runs_without_growth"] == ["RUN002"]
    assert growth["records_by_run"] == [
        {
            "run_id": "RUN001",
            "fixture": "fig_demo",
            "started_at": "2026-07-04T00:00:00Z",
            "completed_at": "2026-07-04T00:10:00Z",
            "record_count": 2,
        },
        {
            "run_id": "RUN002",
            "fixture": "fig_demo",
            "started_at": "2026-07-04T00:20:00Z",
            "completed_at": "2026-07-04T00:30:00Z",
            "record_count": 0,
        },
    ]
