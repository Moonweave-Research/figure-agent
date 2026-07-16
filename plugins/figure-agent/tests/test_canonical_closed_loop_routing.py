from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closed_loop_attempt_state  # noqa: E402
import fig_driver  # noqa: E402
import fig_run  # noqa: E402
import status as status_mod  # noqa: E402


def _projection(
    *,
    resolution: str = "current",
    lifecycle_state: str = "post_review_requested",
    required_actor: str = "host_llm",
    terminal: bool = False,
) -> dict[str, Any]:
    return {
        "schema": "figure-agent.closed-loop-current-state.v1",
        "resolution": resolution,
        "attempt_id": "attempt-0123456789abcdef01234567",
        "state": lifecycle_state,
        "sequence": 8,
        "path": (
            "examples/demo/review/closed-loop/"
            "attempt-0123456789abcdef01234567/"
            f"state-008-{lifecycle_state}.json"
        ),
        "state_sha256": "sha256:" + "a" * 64,
        "disposition": "human_review_required",
        "required_actor": required_actor,
        "terminal": terminal,
        "publication_acceptance": "not_claimed",
    }


def _legacy_status(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": 3,
        "name": "demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "MISSING",
        "adjudication_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "MISSING",
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
        "closed_loop_attempt": projection,
    }


def test_status_projects_closed_loop_before_legacy_next_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    projection = _projection()
    monkeypatch.setattr(
        status_mod.closed_loop_current_state,
        "resolve_current_attempt",
        lambda **_kwargs: projection,
    )

    payload = status_mod.infer_stage(tmp_path / "demo")

    assert payload["closed_loop_attempt"] == projection
    assert payload["next_action_summary"]["action"] == "closed_loop_handoff_stop"
    assert payload["next_action_summary"]["required_actor"] == "host_llm"
    assert payload["next_action_summary"]["safe_command"] is None
    assert payload["next_action_summary"]["publication_acceptance"] == "not_claimed"
    assert projection["path"] in payload["next_action_summary"]["evidence_refs"]


def test_default_status_driver_run_discovers_real_published_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    source = fixture / "demo.tex"
    source.write_text("\\documentclass{standalone}\n", encoding="utf-8")
    render = build / "demo.png"
    render.write_bytes(b"render-v1")
    manifest = fixture / "attempt-manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence={
            "attempt_manifest": manifest,
            "authored_source": source,
            "render": render,
        },
    )
    state_path = closed_loop_attempt_state.publish_state(
        state,
        workspace_root=workspace,
    )

    status = status_mod.infer_stage(fixture)
    driver = fig_driver.build_driver_summary(
        "demo",
        mode="review",
        goal="resume",
        repo_root=workspace,
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda *_args, **_kwargs: pytest.fail("current attempt must preempt legacy execution"),
    )
    run = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="resume",
        execute=True,
        repo_root=workspace,
    )

    relative_state = state_path.relative_to(workspace).as_posix()
    assert status["closed_loop_attempt"]["path"] == relative_state
    assert status["next_action_summary"]["required_actor"] == "workflow_agent"
    assert driver["action"] == fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP
    assert driver["closed_loop_attempt"]["state_sha256"] == state["state_sha256"]
    assert run["executed_count"] == 0
    assert run["boundary_handoff"]["evidence_refs"][0] == relative_state
    assert run["boundary_handoff"]["publication_acceptance"] == "not_claimed"


@pytest.mark.parametrize(
    ("lifecycle_state", "required_actor", "operator_state"),
    [
        ("critique_unadjudicated", "human_adjudicator", "human_boundary"),
        ("adjudicated_unbound", "human_attributor", "human_boundary"),
        ("repair_candidate_ready", "human_repair_authorizer", "human_boundary"),
        ("post_review_requested", "host_llm", "host_boundary"),
        ("visually_re_reviewed", "human_reviewer", "human_boundary"),
        ("machine_repaired", "workflow_agent", "blocked"),
    ],
)
def test_driver_closed_loop_boundary_preempts_legacy_export_or_loop(
    lifecycle_state: str,
    required_actor: str,
    operator_state: str,
) -> None:
    projection = _projection(
        lifecycle_state=lifecycle_state,
        required_actor=required_actor,
    )

    summary = fig_driver._select_action(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        status=_legacy_status(projection),
        example_dir=Path("examples/demo"),
    )

    assert summary["action"] == fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "closed_loop_actor_required"
    assert summary["closed_loop_attempt"] == projection
    assert summary["next_action_summary"]["required_actor"] == required_actor
    assert summary["operator_guidance"]["required_actor"] == required_actor
    assert summary["operator_guidance"]["state"] == operator_state
    assert projection["path"] in summary["next_action_summary"]["evidence_refs"]


@pytest.mark.parametrize("resolution", ["invalid", "ambiguous"])
def test_driver_invalid_or_ambiguous_closed_loop_fails_closed(resolution: str) -> None:
    projection = {
        "schema": "figure-agent.closed-loop-current-state.v1",
        "resolution": resolution,
        "reason": f"closed_loop_{resolution}",
        "required_actor": "workflow_agent",
        "publication_acceptance": "not_claimed",
        "evidence_refs": ["examples/demo/review/closed-loop/"],
    }

    summary = fig_driver._select_action(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        status=_legacy_status(projection),
        example_dir=Path("examples/demo"),
    )

    assert summary["action"] == fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == f"closed_loop_{resolution}"
    assert summary["operator_guidance"]["required_actor"] == "workflow_agent"


def test_final_readiness_keeps_named_human_actor_as_human_required() -> None:
    projection = _projection(
        lifecycle_state="visually_re_reviewed",
        required_actor="human_reviewer",
    )

    summary = fig_driver._select_action(
        "demo",
        mode="final",
        goal="final readiness",
        status=_legacy_status(projection),
        example_dir=Path("examples/demo"),
    )

    assert summary["operator_guidance"]["required_actor"] == "human_reviewer"
    assert summary["final_readiness_profile"]["overall_state"] == "human_required"


def test_development_acceptance_does_not_claim_release_or_publication() -> None:
    projection = _projection(
        resolution="current",
        lifecycle_state="development_accepted",
        required_actor="none",
        terminal=True,
    )
    status = _legacy_status(projection)
    status["export_state"] = "TRACKED_GOLDEN"

    summary = fig_driver._select_action(
        "demo",
        mode="release",
        goal="release",
        status=status,
        example_dir=Path("examples/demo"),
    )

    assert summary["action"] == fig_driver.ACTION_RELEASE_BLOCKED
    assert summary["closed_loop_attempt"]["publication_acceptance"] == "not_claimed"
    assert summary["status"]["release_ready"] is False


def test_development_acceptance_closes_review_without_reopening_legacy_loop() -> None:
    projection = _projection(
        resolution="current",
        lifecycle_state="development_accepted",
        required_actor="none",
        terminal=True,
    )

    summary = fig_driver._select_action(
        "demo",
        mode="review",
        goal="review",
        status=_legacy_status(projection),
        example_dir=Path("examples/demo"),
    )

    assert summary["action"] == fig_driver.ACTION_COMPLETE
    assert summary["safe_command"] is None
    assert summary["closed_loop_attempt"]["publication_acceptance"] == "not_claimed"
    assert "does not claim accepted, golden, release, or publication" in summary["reason"]


def test_run_execute_never_runs_a_command_at_closed_loop_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection = _projection(lifecycle_state="repair_authorized", required_actor="workflow_agent")
    driver_summary = fig_driver._select_action(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        status=_legacy_status(projection),
        example_dir=Path("examples/demo"),
    )
    monkeypatch.setattr(fig_run, "_driver_summary", lambda *_args, **_kwargs: driver_summary)
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda *_args, **_kwargs: pytest.fail("closed-loop boundary must execute zero commands"),
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        execute=True,
        repo_root=Path("."),
    )

    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert projection["path"] in payload["boundary_handoff"]["evidence_refs"]
    assert payload["boundary_handoff"]["publication_acceptance"] == "not_claimed"


def test_absent_closed_loop_keeps_legacy_driver_result() -> None:
    status = _legacy_status(
        {
            "schema": "figure-agent.closed-loop-current-state.v1",
            "resolution": "absent",
            "publication_acceptance": "not_claimed",
        }
    )

    summary = fig_driver._select_action(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        status=status,
        example_dir=Path("examples/demo"),
    )
    legacy_status = dict(status)
    legacy_status.pop("closed_loop_attempt")
    legacy = fig_driver._select_action(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        status=legacy_status,
        example_dir=Path("examples/demo"),
    )

    assert summary["action"] == legacy["action"]
    assert summary["safe_command"] == legacy["safe_command"]
    assert summary["stop_boundary"] == legacy["stop_boundary"]
