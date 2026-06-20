from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_memory_events  # noqa: E402
from test_evidence_index import _fixture  # noqa: E402


def test_memory_log_missing_optional_artifacts_is_empty(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "plain_demo"
    fixture.mkdir(parents=True)
    (fixture / "plain_demo.tex").write_text("source\n", encoding="utf-8")

    payload = quality_memory_events.build_memory_log("plain_demo", workspace_root=workspace)

    assert payload["schema"] == "figure-agent.quality-memory-log.v1"
    assert payload["fixture"] == "plain_demo"
    assert payload["event_count"] == 0
    assert payload["events"] == []


def test_applied_candidate_produces_candidate_events(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)

    event_types = {event["event_type"] for event in payload["events"]}
    assert {
        "candidate_generated",
        "candidate_rendered",
        "candidate_applied",
    }.issubset(event_types)
    applied = next(
        event for event in payload["events"] if event["event_type"] == "candidate_applied"
    )
    assert applied["candidate_id"] == "CAND001"
    assert applied["outcome"]["state"] == "improved"
    assert applied["post_state"] == {
        "compile": "success",
        "export": "success",
        "status": "success",
    }


def test_memory_log_uses_candidate_set_family_and_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set_path = fixture / "build" / "candidates" / "candidate_set.json"
    candidate_set = json.loads(candidate_set_path.read_text(encoding="utf-8"))
    candidate_set["candidates"][0]["edit_class"] = "label_offset"
    candidate_set["candidates"][0]["target"] = {
        "panel": "C",
        "subregion": "energy-trap-labels",
    }
    candidate_set_path.write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)

    generated = next(
        event for event in payload["events"] if event["event_type"] == "candidate_generated"
    )
    assert generated["edit_family"] == "label_offset"
    assert generated["target"] == {"panel": "C", "subregion": "energy-trap-labels"}


def test_stale_apply_result_is_blocked_by_hard_gate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    payload = quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)

    applied = next(
        event for event in payload["events"] if event["event_type"] == "candidate_applied"
    )
    assert applied["outcome"]["state"] == "blocked_by_hard_gate"
    assert "candidate_apply_stale:candidate_demo.tex" in applied["outcome"]["reason"]


def test_memory_log_rejects_manifest_fixture_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixture"] = "other_demo"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(quality_memory_events.QualityMemoryEventError, match="fixture_mismatch"):
        quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)


def test_memory_log_rejects_render_fixture_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    render_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    render = json.loads(render_path.read_text(encoding="utf-8"))
    render["figure_name"] = "other_demo"
    render_path.write_text(json.dumps(render, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(quality_memory_events.QualityMemoryEventError, match="fixture_mismatch"):
        quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)


def test_memory_log_rejects_apply_fixture_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    apply_path = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result = json.loads(apply_path.read_text(encoding="utf-8"))
    apply_result["figure_name"] = "other_demo"
    apply_path.write_text(json.dumps(apply_result, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(quality_memory_events.QualityMemoryEventError, match="fixture_mismatch"):
        quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)


def test_closeout_ready_artifact_produces_closeout_event(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "closeout_demo"
    closeout_dir = fixture / "build" / "closeout"
    closeout_dir.mkdir(parents=True)
    (fixture / "closeout_demo.tex").write_text("source\n", encoding="utf-8")
    (closeout_dir / "golden_acceptance.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.golden-acceptance.v1",
                "decision": "accept",
                "accept_golden": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = quality_memory_events.build_memory_log("closeout_demo", workspace_root=workspace)

    assert payload["events"][0]["event_type"] == "closeout_ready"
    assert payload["events"][0]["outcome"]["state"] == "improved"


def test_memory_log_rejects_symlinked_candidate_sandbox(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    for path in sorted(sandbox.rglob("*"), reverse=True):
        path.unlink()
    sandbox.rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sandbox.symlink_to(outside)

    with pytest.raises(quality_memory_events.QualityMemoryEventError, match="sandbox_symlink"):
        quality_memory_events.build_memory_log("candidate_demo", workspace_root=workspace)
