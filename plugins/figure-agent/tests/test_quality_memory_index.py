from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_memory_index  # noqa: E402


def _event(
    event_type: str,
    family: str,
    outcome: str,
    candidate_id: str,
    target: dict | None = None,
    quality_movement: str | None = None,
) -> dict:
    return {
        "schema": "figure-agent.quality-memory-event.v1",
        "fixture": "candidate_demo",
        "event_id": f"sha256:{candidate_id.lower():0<64}"[:71],
        "event_type": event_type,
        "created_at": "2026-06-08T00:00:00Z",
        "source_artifact": f"build/candidates/{candidate_id}/apply_result.json",
        "candidate_id": candidate_id,
        "edit_family": family,
        "target": target if target is not None else {"panel": "C", "subregion": "energy"},
        "pre_state": {},
        "post_state": {},
        "outcome": {
            "state": outcome,
            "pipeline_ok": None,
            "quality_movement": quality_movement,
            "reason": "",
            "evidence_paths": [],
        },
        "metrics": {"candidate_rank_score": 0.5},
    }


def test_fewer_than_three_eligible_events_yields_no_prior() -> None:
    index = quality_memory_index.build_memory_index(
        [
            _event(
                "candidate_applied",
                "label_offset",
                "improved",
                "CAND001",
                quality_movement="improved",
            )
        ]
    )

    assert index["schema"] == "figure-agent.quality-memory-index.v1"
    assert index["event_count"] == 1
    assert index["eligible_prior_count"] == 0
    assert index["families"]["label_offset"]["attempts"] == 1
    assert index["families"]["label_offset"]["recommended_prior"] == 0.0
    assert index["reward_sparsity"] == {
        "state": "sparse",
        "eligible_attempt_count": 1,
        "prior_floor": 3,
        "counterfactual_unchosen_count": 0,
        "mitigations": [
            "counterfactual_unchosen_rows",
            "cross_fixture_transfer",
        ],
    }


def test_sparse_reward_state_surfaces_counterfactual_mitigation() -> None:
    index = quality_memory_index.build_memory_index(
        [
            _event(
                "candidate_applied",
                "label_offset",
                "neutral",
                "CAND001",
                quality_movement="neutral",
            ),
            _event(
                "candidate_rejected",
                "label_offset",
                "regressed",
                "CAND002",
                quality_movement="regressed",
            ),
            _event(
                "candidate_unchosen",
                "label_offset",
                "unchosen",
                "CAND003",
                quality_movement=None,
            ),
        ]
    )

    assert index["eligible_prior_count"] == 0
    assert index["families"]["label_offset"]["attempts"] == 2
    assert index["families"]["label_offset"]["recommended_prior"] == 0.0
    assert index["reward_sparsity"] == {
        "state": "sparse",
        "eligible_attempt_count": 2,
        "prior_floor": 3,
        "counterfactual_unchosen_count": 1,
        "mitigations": [
            "counterfactual_unchosen_rows",
            "cross_fixture_transfer",
        ],
    }


def _experience_record(
    candidate_id: str,
    *,
    quality_movement: str | None,
    apply_status: str = "applied",
) -> dict:
    return {
        "schema": "figure-agent.experience-record.v1",
        "record_id": f"sha256:{candidate_id.lower():0<64}"[:71],
        "fixture": "candidate_demo",
        "created_at": "2026-06-08T00:00:00Z",
        "state": {
            "base_tex_hash": "sha256:" + "0" * 64,
            "target": {"panel": "C", "subregion_key": "sha256:" + "a" * 64},
            "pre_apply_defects": [],
            "critique_finding_id": None,
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": "label_offset",
            "params": {"operations": []},
            "candidate_hash": "sha256:" + "1" * 64,
            "rank_score": 0.7,
            "rank": 1,
            "n_candidates": 1,
        },
        "outcome": {
            "pipeline_ok": quality_movement is not None,
            "apply_status": apply_status,
            "quality_movement": quality_movement,
            "verifiers": {},
            "detector_recheck": {},
            "pixel_delta": {"changed_pixel_ratio": 0.01},
            "human_label": None,
            "human_decision_kind": None,
        },
    }


def test_build_fixture_index_reads_experience_log_not_build_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("source\n", encoding="utf-8")
    log_path = plugin_root / "docs" / "experience-log" / "candidate_demo.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            json.dumps(_experience_record(f"CAND{index:03d}", quality_movement="improved"))
            for index in range(1, 4)
        )
        + "\n",
        encoding="utf-8",
    )

    index = quality_memory_index.build_fixture_index(
        "candidate_demo",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    assert index["scope"] == {"kind": "fixture", "fixture": "candidate_demo"}
    assert index["event_count"] == 3
    assert index["eligible_prior_count"] == 3
    assert index["families"]["label_offset"]["recommended_prior"] == 0.25
    assert index["families"]["label_offset"]["prior_provenance"] == {
        "locality": "fixture_local",
        "scope": {"kind": "fixture", "fixture": "candidate_demo"},
        "source_fixtures": ["candidate_demo"],
    }


def test_recommendation_experience_records_are_candidate_recommended_attempts() -> None:
    record = _experience_record(
        "CAND001",
        quality_movement="neutral",
        apply_status="blocked",
    )
    record["outcome"]["human_decision_kind"] = "auto_accept_recommended"

    event = quality_memory_index._event_from_experience_record(record)  # type: ignore[attr-defined]
    assert event["event_type"] == "candidate_recommended"

    index = quality_memory_index.build_memory_index([event])

    assert index["event_count"] == 1
    assert index["candidate_event_count"] == 1
    assert index["families"]["label_offset"]["attempts"] == 1
    assert index["families"]["label_offset"]["neutral"] == 1
    assert index["panel_patterns"]["C:sha256:" + "a" * 64 + ":label_offset"][
        "attempts"
    ] == 1


def test_duplicate_recommendation_experience_rows_do_not_inflate_attempts() -> None:
    first = _experience_record(
        "CAND001",
        quality_movement="neutral",
        apply_status="blocked",
    )
    first["outcome"]["human_decision_kind"] = "auto_accept_recommended"
    duplicate = json.loads(json.dumps(first))
    duplicate["record_id"] = "sha256:" + "d" * 64
    duplicate["created_at"] = "2026-06-08T00:01:00Z"
    duplicate["source_artifacts"] = ["different-run-artifact.json"]
    unchosen = _experience_record(
        "CAND002",
        quality_movement=None,
        apply_status="unchosen",
    )
    unchosen["action"]["candidate_hash"] = "sha256:" + "2" * 64
    unchosen["outcome"]["human_decision_kind"] = "counterfactual_unchosen"
    duplicate_unchosen = json.loads(json.dumps(unchosen))
    duplicate_unchosen["record_id"] = "sha256:" + "e" * 64
    duplicate_unchosen["created_at"] = "2026-06-08T00:01:00Z"
    duplicate_unchosen["source_artifacts"] = ["different-run-artifact.json"]

    events = [
        quality_memory_index._event_from_experience_record(record)  # type: ignore[attr-defined]
        for record in (first, duplicate, unchosen, duplicate_unchosen)
    ]
    index = quality_memory_index.build_memory_index(events)

    assert index["event_count"] == 4
    assert index["candidate_event_count"] == 4
    assert index["families"]["label_offset"]["event_count"] == 4
    assert index["families"]["label_offset"]["attempts"] == 1
    assert index["families"]["label_offset"]["neutral"] == 1
    assert index["reward_sparsity"]["counterfactual_unchosen_count"] == 1


def test_legacy_outcome_state_is_not_reward_without_quality_movement() -> None:
    events = [
        _event("candidate_applied", "label_offset", "improved", "CAND001"),
        _event("candidate_applied", "label_offset", "improved", "CAND002"),
        _event("candidate_applied", "label_offset", "improved", "CAND003"),
    ]

    index = quality_memory_index.build_memory_index(events)

    family = index["families"]["label_offset"]
    assert index["eligible_prior_count"] == 0
    assert family["attempts"] == 0
    assert family["improved"] == 0
    assert family["unknown"] == 3
    assert family["recommended_prior"] == 0.0


def test_free_text_and_rank_score_cannot_create_reward() -> None:
    events = [
        {
            **_event("candidate_applied", "label_offset", "unknown", "CAND001"),
            "outcome": {
                "state": "unknown",
                "pipeline_ok": True,
                "quality_movement": None,
                "reason": "human_note says this is improved",
                "rationale": "prose should not be a reward signal",
                "human_note": "accept because evidence looks good",
                "evidence_paths": [],
            },
            "metrics": {"candidate_rank_score": 1.0},
        },
        {
            **_event("candidate_applied", "label_offset", "unknown", "CAND002"),
            "outcome": {
                "state": "unknown",
                "pipeline_ok": True,
                "quality_movement": None,
                "reason": "human_note says this is improved",
                "rationale": "prose should not be a reward signal",
                "human_note": "accept because evidence looks good",
                "evidence_paths": [],
            },
            "metrics": {"candidate_rank_score": 1.0},
        },
        {
            **_event("candidate_applied", "label_offset", "unknown", "CAND003"),
            "outcome": {
                "state": "unknown",
                "pipeline_ok": True,
                "quality_movement": None,
                "reason": "human_note says this is improved",
                "rationale": "prose should not be a reward signal",
                "human_note": "accept because evidence looks good",
                "evidence_paths": [],
            },
            "metrics": {"candidate_rank_score": 1.0},
        },
    ]

    index = quality_memory_index.build_memory_index(events)

    family = index["families"]["label_offset"]
    assert index["eligible_prior_count"] == 0
    assert family["attempts"] == 0
    assert family["improved"] == 0
    assert family["recommended_prior"] == 0.0
    assert family["median_rank_delta"] == 1.0


def test_quality_movement_overrides_legacy_outcome_state_for_reward() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND001",
            quality_movement="neutral",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND002",
            quality_movement="neutral",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND003",
            quality_movement="regressed",
        ),
    ]

    index = quality_memory_index.build_memory_index(events)

    family = index["families"]["label_offset"]
    assert index["eligible_prior_count"] == 3
    assert family["attempts"] == 3
    assert family["improved"] == 0
    assert family["neutral"] == 2
    assert family["regressed"] == 1
    assert family["recommended_prior"] == 0.0


def test_three_improved_family_outcomes_produce_bounded_positive_prior() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND001",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND002",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND003",
            quality_movement="improved",
        ),
    ]

    index = quality_memory_index.build_memory_index(events)

    family = index["families"]["label_offset"]
    assert index["eligible_prior_count"] == 3
    assert family["attempts"] == 3
    assert family["improved"] == 3
    assert family["recommended_prior"] == 0.25


def test_unknown_family_panel_and_outcome_are_measured_and_excluded_from_priors() -> None:
    events = [
        _event(
            "candidate_applied",
            "unknown",
            "improved",
            "CAND001",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND002",
            target={"panel": "unknown", "subregion": "energy"},
            quality_movement="improved",
        ),
        _event("candidate_applied", "label_offset", "unknown", "CAND003"),
    ]

    index = quality_memory_index.build_memory_index(events)

    assert index["candidate_event_count"] == 3
    assert index["unknown_event_count"] == 3
    assert index["unknown_event_rate"] == 1.0
    assert "unknown" not in index["families"]
    assert all(not key.startswith("unknown:") for key in index["panel_patterns"])
    assert all(":unknown:" not in key for key in index["panel_patterns"])
    assert index["eligible_prior_count"] == 0
    assert index["families"]["label_offset"]["attempts"] == 0
    assert index["families"]["label_offset"]["recommended_prior"] == 0.0


def test_unknown_metadata_does_not_activate_family_prior() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND001",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND002",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND003",
            target={"panel": "unknown", "subregion": "energy"},
            quality_movement="improved",
        ),
    ]

    index = quality_memory_index.build_memory_index(events)

    assert index["eligible_prior_count"] == 0
    assert index["families"]["label_offset"]["attempts"] == 2
    assert index["families"]["label_offset"]["recommended_prior"] == 0.0


def test_synthetic_smoke_memory_unknown_event_rate_stays_below_gate() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            f"CAND{index:03d}",
            quality_movement="improved",
        )
        for index in range(1, 10)
    ]
    events.append(_event("candidate_applied", "label_offset", "unknown", "CAND010"))

    index = quality_memory_index.build_memory_index(events)

    assert index["unknown_event_count"] == 1
    assert index["unknown_event_rate"] == 0.1
    assert index["unknown_event_rate"] <= 0.10


def test_regressed_event_reduces_prior() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND001",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND002",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "regressed",
            "CAND003",
            quality_movement="regressed",
        ),
    ]

    index = quality_memory_index.build_memory_index(events)

    family = index["families"]["label_offset"]
    assert index["eligible_prior_count"] == 3
    assert family["improved"] == 2
    assert family["regressed"] == 1
    assert family["recommended_prior"] == 0.0833


def test_mostly_regressed_events_can_make_prior_negative() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND001",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "regressed",
            "CAND002",
            quality_movement="regressed",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "regressed",
            "CAND003",
            quality_movement="regressed",
        ),
    ]

    index = quality_memory_index.build_memory_index(events)

    assert index["families"]["label_offset"]["recommended_prior"] < 0.0


def test_unknown_outcomes_do_not_affect_prior() -> None:
    events = [
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND001",
            quality_movement="improved",
        ),
        _event(
            "candidate_applied",
            "label_offset",
            "improved",
            "CAND002",
            quality_movement="improved",
        ),
        _event("candidate_applied", "label_offset", "unknown", "CAND003"),
    ]

    index = quality_memory_index.build_memory_index(events)

    assert index["eligible_prior_count"] == 0
    assert index["families"]["label_offset"]["unknown"] == 1
    assert index["families"]["label_offset"]["attempts"] == 2
    assert index["families"]["label_offset"]["recommended_prior"] == 0.0


def test_generated_and_closeout_events_do_not_count_as_family_attempts() -> None:
    events = [
        _event("candidate_generated", "label_offset", "unknown", "CAND001"),
        {
            **_event("closeout_ready", "unknown", "improved", "CAND002"),
            "candidate_id": None,
        },
    ]

    index = quality_memory_index.build_memory_index(events)

    assert index["event_count"] == 2
    assert index["families"]["label_offset"]["event_count"] == 1
    assert index["families"]["label_offset"]["attempts"] == 0
    assert "unknown" not in index["families"]


def test_write_fixture_index_writes_only_memory_index(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("source\n", encoding="utf-8")
    before = sorted(
        path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()
    )

    payload = quality_memory_index.write_fixture_index(
        "candidate_demo",
        [_event("candidate_applied", "label_offset", "improved", "CAND001")],
        workspace_root=workspace,
    )

    written = fixture / "build" / "memory" / "quality_memory_index.json"
    assert payload["writes"] == ["build/memory/quality_memory_index.json"]
    assert written.is_file()
    after_files = sorted(
        path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()
    )
    assert after_files == sorted(
        [*before, "examples/candidate_demo/build/memory/quality_memory_index.json"]
    )
    assert json.loads(written.read_text(encoding="utf-8"))["event_count"] == 1


def test_write_fixture_index_refuses_memory_dir_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    memory_dir = fixture / "build" / "memory"
    memory_dir.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    memory_dir.symlink_to(outside)

    with pytest.raises(quality_memory_index.QualityMemoryIndexError, match="sandbox_symlink"):
        quality_memory_index.write_fixture_index(
            "candidate_demo",
            [],
            workspace_root=workspace,
        )


def test_write_fixture_index_refuses_build_dir_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (fixture / "build").symlink_to(outside)

    with pytest.raises(quality_memory_index.QualityMemoryIndexError, match="sandbox_symlink"):
        quality_memory_index.write_fixture_index(
            "candidate_demo",
            [],
            workspace_root=workspace,
        )


def test_write_fixture_index_refuses_output_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    memory_dir = fixture / "build" / "memory"
    memory_dir.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    (memory_dir / "quality_memory_index.json").symlink_to(outside)

    with pytest.raises(quality_memory_index.QualityMemoryIndexError, match="sandbox_symlink"):
        quality_memory_index.write_fixture_index(
            "candidate_demo",
            [],
            workspace_root=workspace,
        )


def test_write_fixture_index_refuses_cloud_storage_workspace(tmp_path: Path) -> None:
    workspace = (
        tmp_path
        / "Library"
        / "CloudStorage"
        / "GoogleDrive-user@example.com"
        / "My Drive"
        / "Research"
    )
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("source\n", encoding="utf-8")

    with pytest.raises(
        quality_memory_index.QualityMemoryIndexError,
        match="cloud_storage_write_forbidden",
    ):
        quality_memory_index.write_fixture_index(
            "candidate_demo",
            [],
            workspace_root=workspace,
        )


def test_build_suite_index_skips_missing_fixtures_and_writes_scratch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    (plugin_root / "benchmarks").mkdir(parents=True)
    (plugin_root / "benchmarks" / "quality_suites.yaml").write_text(
        "\n".join(
            [
                "schema: figure-agent.quality-benchmark-suites.v1",
                "suites:",
                "  smoke:",
                "    description: Test suite.",
                "    fixtures:",
                "      - missing_demo",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    index = quality_memory_index.build_suite_index(
        "smoke",
        write=True,
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    assert index["scope"] == {"kind": "suite", "suite": "smoke"}
    assert index["suite_diagnostics"] == [
        {"fixture": "missing_demo", "status": "skipped", "reason": "missing_fixture"}
    ]
    assert index["writes"] == [
        ".scratch/figure-agent-memory/smoke/quality_memory_index.json"
    ]
    assert (
        workspace / ".scratch" / "figure-agent-memory" / "smoke" / "quality_memory_index.json"
    ).is_file()


def test_build_suite_index_aggregates_all_experience_logs_with_transfer_provenance(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    (plugin_root / "benchmarks").mkdir(parents=True)
    (plugin_root / "benchmarks" / "quality_suites.yaml").write_text(
        "\n".join(
            [
                "schema: figure-agent.quality-benchmark-suites.v1",
                "suites:",
                "  smoke:",
                "    description: Test suite.",
                "    fixtures:",
                "      - suite_demo",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "examples" / "suite_demo").mkdir(parents=True)
    log_path = plugin_root / "docs" / "experience-log" / "outside_demo.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        json.dumps(
            _experience_record(
                "OUTSIDE001",
                quality_movement="improved",
            )
            | {
                "fixture": "outside_demo",
                "record_id": "sha256:outside",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    index = quality_memory_index.build_suite_index(
        "smoke",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    assert index["scope"] == {"kind": "suite", "suite": "smoke"}
    assert index["event_count"] == 1
    assert index["families"]["label_offset"]["attempts"] == 1
    assert index["families"]["label_offset"]["prior_provenance"] == {
        "locality": "cross_fixture_transfer",
        "scope": {"kind": "suite", "suite": "smoke"},
        "source_fixtures": ["outside_demo"],
    }
    assert {
        "fixture": "outside_demo",
        "status": "included",
        "reason": "out_of_suite_experience_log",
    } in index["suite_diagnostics"]
