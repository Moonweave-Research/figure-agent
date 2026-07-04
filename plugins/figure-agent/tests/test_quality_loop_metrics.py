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
        },
        "outcome": {
            "apply_status": apply_status,
            "quality_movement": quality_movement,
            "human_label": human_label,
            "human_decision_kind": human_decision_kind,
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
