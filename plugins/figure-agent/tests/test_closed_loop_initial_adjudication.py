from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closed_loop_attempt_admission  # noqa: E402
import closed_loop_attempt_state  # noqa: E402
import closed_loop_current_state  # noqa: E402
import closed_loop_initial_adjudication as adjudication  # noqa: E402
import closed_loop_initial_review  # noqa: E402
import closed_loop_initial_review_response as response_adapter  # noqa: E402
import fig_run  # noqa: E402
import post_repair_visual_review  # noqa: E402

FIXTURE = "fig3_resistance_mechanism"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest(path: Path, payload: dict[str, object]) -> Path:
    payload = dict(payload)
    payload["manifest_sha256"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    _write_json(path, payload)
    return path


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / FIXTURE
    fixture.mkdir(parents=True)
    source = fixture / f"{FIXTURE}.tex"
    source.write_text("\\documentclass{standalone}\n", encoding="utf-8")
    render = fixture / "build" / f"{FIXTURE}.png"
    render.parent.mkdir()
    Image.new("RGB", (800, 600), color=(44, 88, 155)).save(render)
    manifest = _manifest(
        fixture / "attempt-manifest.json",
        {
            "schema": "figure-agent.root-attempt-manifest.v1",
            "fixture": FIXTURE,
            "author": {"identity": "author-1", "role": "authoring_agent"},
            "source": {"path": f"examples/{FIXTURE}/{FIXTURE}.tex", "sha256": _sha(source)},
            "render": {"path": f"examples/{FIXTURE}/build/{FIXTURE}.png", "sha256": _sha(render)},
            "task": {"id": "task-1"},
            "model": {"identity": "model-1"},
            "budget": {"id": "budget-1"},
            "publication_acceptance": "not_claimed",
        },
    )
    admitted = closed_loop_attempt_admission.admit_root_attempt(
        FIXTURE, manifest_path=manifest, execute=True, workspace_root=workspace
    )
    outbound = closed_loop_initial_review.run_outbound_handoff(
        FIXTURE, state_path=admitted["next_state_path"], execute=True, workspace_root=workspace
    )
    response = _response_pack(workspace, fixture, outbound["next_state_path"])
    inbound = response_adapter.run_inbound_response(
        FIXTURE,
        state_path=outbound["next_state_path"],
        response_path=response,
        execute=True,
        workspace_root=workspace,
    )
    return workspace, inbound["next_state_path"]


def _response_pack(workspace: Path, fixture: Path, state_path: Path) -> Path:
    request = json.loads((state_path.parent / "initial-review" / "request.json").read_text())
    crop_manifest = json.loads(
        (state_path.parent / "initial-review" / "crops" / "manifest.json").read_text()
    )
    pack = state_path.parent / response_adapter.RESPONSE_PACK
    pack.mkdir()
    critique = pack / response_adapter.CRITIQUE_FILE
    source = Path(__file__).resolve().parents[1] / "examples" / FIXTURE / "critique.md"
    shutil.copyfile(source, critique)
    transcript = pack / response_adapter.TRANSCRIPT_FILE
    transcript.write_text("review transcript\n", encoding="utf-8")
    crop_by_id = {item["id"]: item for item in crop_manifest["crops"]}
    inspected = [{"role": "full_render", **request["render"]}]
    inspected.extend(
        {
            "role": crop_id,
            "path": f"examples/{FIXTURE}/{crop_by_id[crop_id]['path']}",
            "sha256": crop_by_id[crop_id]["sha256"],
        }
        for crop_id in response_adapter.EXPECTED_CROP_IDS
    )
    receipt = {
        "schema": post_repair_visual_review.EXECUTION_RECEIPT_SCHEMA,
        "request_sha256": request["request_sha256"],
        "actor": {"kind": "model", "identity": "vision", "model_or_tool": "vision"},
        "transcript": {
            "path": transcript.relative_to(workspace).as_posix(),
            "sha256": _sha(transcript),
        },
        "inspected_artifacts": inspected,
    }
    receipt["receipt_sha256"] = response_adapter._canonical_hash(receipt, omitted="receipt_sha256")  # noqa: SLF001
    receipt_path = pack / response_adapter.HOST_RECEIPT_FILE
    _write_json(receipt_path, receipt)
    response = {
        "schema": response_adapter.SCHEMA,
        "fixture": FIXTURE,
        "request_sha256": request["request_sha256"],
        "critique": {"path": critique.relative_to(workspace).as_posix(), "sha256": _sha(critique)},
        "host_review_execution_receipt": {
            "path": receipt_path.relative_to(workspace).as_posix(),
            "sha256": _sha(receipt_path),
        },
        "publication_acceptance": "not_claimed",
    }
    response["response_sha256"] = response_adapter._canonical_hash(
        response, omitted="response_sha256"
    )  # noqa: SLF001
    result = pack / response_adapter.RESPONSE_FILE
    _write_json(result, response)
    return result


def _decision(
    workspace: Path, state_path: Path, *, action: str = "approve_for_attribution"
) -> Path:
    state = json.loads(state_path.read_text())
    evidence = {item["role"]: item for item in state["evidence"]}
    directory = state_path.parent / adjudication.DECISION_DIRECTORY
    directory.mkdir()
    attribution: object = None
    if action == "approve_for_attribution":
        # The copied fixture critique has a stable top-level C001 finding.
        finding_id = "C001"
        attribution = {
            "selected_finding_ids": [finding_id],
            "human_attributor": {"kind": "human", "identity": "attributor-1"},
            "permitted_scope": ["classify selected critique findings"],
            "forbidden_scope": ["mutate source", "bind repair", "claim publication acceptance"],
            "source_mutation": "forbidden",
        }
    decision: dict[str, object] = {
        "schema": adjudication.SCHEMA,
        "fixture": FIXTURE,
        "attempt_id": state["attempt_id"],
        "current_state": {
            "path": state_path.relative_to(workspace).as_posix(),
            "sha256": state["state_sha256"],
        },
        "response": {
            "path": evidence["initial_visual_review_response"]["path"],
            "sha256": evidence["initial_visual_review_response"]["sha256"],
        },
        "critique": {
            "path": evidence["critique"]["path"],
            "sha256": evidence["critique"]["sha256"],
        },
        "host_review_execution_receipt": {
            "path": evidence["host_review_execution_receipt"]["path"],
            "sha256": evidence["host_review_execution_receipt"]["sha256"],
        },
        "host_review_transcript": {
            "path": evidence["host_review_transcript"]["path"],
            "sha256": evidence["host_review_transcript"]["sha256"],
        },
        "reviewer": {"kind": "human", "identity": "reviewer-1"},
        "rationale": "Reviewed the visual critique and selected the safe next boundary.",
        "decision": action,
        "attribution": attribution,
        "publication_acceptance": "not_claimed",
    }
    decision["decision_sha256"] = adjudication.canonical_decision_sha256(decision)
    path = directory / adjudication.DECISION_FILE
    _write_json(path, decision)
    return path


def test_approve_creates_unbound_handoff_and_is_idempotent(tmp_path: Path) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    created = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=state_path,
        decision_path=decision,
        execute=True,
        workspace_root=workspace,
    )
    rerun = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=created["next_state_path"],
        decision_path=decision,
        execute=True,
        workspace_root=workspace,
    )
    assert created["next_state"] == "adjudicated_unbound"
    assert created["attribution_handoff_path"].is_file()
    assert rerun["created"] is False
    assert created["published_state"]["required_actor"] == "human_attributor"
    assert {item["role"] for item in created["published_state"]["evidence"]} == {
        "adjudication",
        "attribution_handoff",
        "critique",
        "host_review_execution_receipt",
        "host_review_transcript",
        "initial_visual_review_response",
    }


def test_reject_is_terminal_and_plan_only_writes_nothing(tmp_path: Path) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path, action="reject_initial_review")
    planned = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=state_path,
        decision_path=decision,
        execute=False,
        workspace_root=workspace,
    )
    assert planned["next_state"] == "rejected"
    assert not planned["next_state_path"].exists()
    assert planned["attribution_handoff_path"] is None
    created = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=state_path,
        decision_path=decision,
        execute=True,
        workspace_root=workspace,
    )
    assert created["published_state"]["terminal"] is True


@pytest.mark.parametrize("mutation", ("state_hash", "finding", "path", "symlink", "publication"))
def test_decision_fails_closed_on_bad_binding_or_selection(tmp_path: Path, mutation: str) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    payload = json.loads(decision.read_text())
    if mutation == "state_hash":
        payload["current_state"]["sha256"] = "sha256:" + "0" * 64
    elif mutation == "finding":
        payload["attribution"]["selected_finding_ids"] = ["missing"]
    elif mutation == "path":
        payload["critique"]["path"] = "examples/outside/critique.md"
    elif mutation == "publication":
        payload["publication_acceptance"] = "claimed"
    else:
        external = tmp_path / "external.json"
        external.write_text(decision.read_text(), encoding="utf-8")
        decision.unlink()
        decision.symlink_to(external)
        with pytest.raises(adjudication.ClosedLoopInitialAdjudicationError):
            adjudication.run_initial_adjudication(
                FIXTURE,
                state_path=state_path,
                decision_path=decision,
                execute=True,
                workspace_root=workspace,
            )
        return
    payload["decision_sha256"] = adjudication.canonical_decision_sha256(payload)
    _write_json(decision, payload)
    with pytest.raises(adjudication.ClosedLoopInitialAdjudicationError):
        adjudication.run_initial_adjudication(
            FIXTURE,
            state_path=state_path,
            decision_path=decision,
            execute=True,
            workspace_root=workspace,
        )


@pytest.mark.parametrize(
    "artifact", ("initial_visual_review_response", "critique", "host_review_transcript")
)
def test_published_adjudication_retains_live_initial_review_provenance(
    tmp_path: Path, artifact: str
) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    created = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=state_path,
        decision_path=decision,
        execute=True,
        workspace_root=workspace,
    )
    evidence = {item["role"]: item for item in created["published_state"]["evidence"]}
    target = workspace / evidence[artifact]["path"]
    target.unlink()
    assert (
        closed_loop_current_state.resolve_current_attempt(workspace, FIXTURE)["resolution"]
        == "invalid"
    )


def test_fig_run_has_distinct_adjudication_route_and_exclusions(tmp_path: Path) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    payload = fig_run.run_workflow(
        FIXTURE,
        mode="authoring",
        goal="adjudicate",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_initial_adjudication=decision,
        repo_root=workspace,
    )
    assert payload["final_action"] == adjudication.ACTION
    with pytest.raises(ValueError, match="mutually exclusive"):
        fig_run.run_workflow(
            FIXTURE,
            mode="authoring",
            goal="adjudicate",
            closed_loop_state=state_path,
            closed_loop_initial_adjudication=decision,
            closed_loop_response=decision,
            repo_root=workspace,
        )


def test_fig_run_can_project_the_current_adjudication_state_automatically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    state = json.loads(state_path.read_text())
    projection = {
        "schema": "figure-agent.closed-loop-current-state.v1",
        "resolution": "current",
        "state": "critique_unadjudicated",
        "disposition": "human_review_required",
        "required_actor": "human_adjudicator",
        "terminal": False,
        "publication_acceptance": "not_claimed",
        "path": state_path.relative_to(workspace).as_posix(),
        "state_sha256": state["state_sha256"],
    }
    monkeypatch.setattr(
        fig_run,
        "_driver_summary",
        lambda *_args, **_kwargs: {
            "action": fig_run.fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP,
            "stop_boundary": fig_run.fig_driver.STOP_CLOSED_LOOP_ACTOR,
            "closed_loop_attempt": projection,
        },
    )

    payload = fig_run.run_workflow(
        FIXTURE,
        mode="authoring",
        goal="adjudicate",
        execute=True,
        closed_loop_initial_adjudication=decision,
        repo_root=workspace,
    )

    assert payload["final_action"] == adjudication.ACTION
    assert payload["closed_loop"]["next_state"] == "adjudicated_unbound"


def test_publish_failure_recovers_without_source_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, state_path = _setup(tmp_path)
    source = workspace / "examples" / FIXTURE / f"{FIXTURE}.tex"
    original_source = source.read_bytes()
    decision = _decision(workspace, state_path)
    original_publish = closed_loop_attempt_state.publish_state
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> Path:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError("simulated_publish_failure")
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(closed_loop_attempt_state, "publish_state", fail_once)
    with pytest.raises(adjudication.ClosedLoopInitialAdjudicationError, match="publication_failed"):
        adjudication.run_initial_adjudication(
            FIXTURE,
            state_path=state_path,
            decision_path=decision,
            execute=True,
            workspace_root=workspace,
        )
    recovered = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=state_path,
        decision_path=decision,
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["created"] is True
    assert source.read_bytes() == original_source


def test_current_response_drift_fails_closed_before_adjudication(tmp_path: Path) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    state = json.loads(state_path.read_text())
    response = workspace / next(
        item["path"]
        for item in state["evidence"]
        if item["role"] == "initial_visual_review_response"
    )
    response.write_text("{}\n", encoding="utf-8")

    with pytest.raises(adjudication.ClosedLoopInitialAdjudicationError, match="state_invalid"):
        adjudication.run_initial_adjudication(
            FIXTURE,
            state_path=state_path,
            decision_path=decision,
            execute=True,
            workspace_root=workspace,
        )


def test_decision_replacement_before_publication_fails_without_handoff_or_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, state_path = _setup(tmp_path)
    decision = _decision(workspace, state_path)
    original_assert = adjudication._assert_snapshot_still_current  # noqa: SLF001

    def replace_then_assert(snapshot: object, *, root: Path) -> None:
        original_bytes = decision.read_bytes()
        decision.unlink()
        decision.write_bytes(original_bytes)
        original_assert(snapshot, root=root)

    monkeypatch.setattr(adjudication, "_assert_snapshot_still_current", replace_then_assert)

    with pytest.raises(adjudication.ClosedLoopInitialAdjudicationError, match="decision_drift"):
        adjudication.run_initial_adjudication(
            FIXTURE,
            state_path=state_path,
            decision_path=decision,
            execute=True,
            workspace_root=workspace,
        )

    assert not (decision.parent / adjudication.DECISION_SNAPSHOT_FILE).exists()
    assert not (decision.parent / adjudication.HANDOFF_FILE).exists()
    assert not (state_path.parent / f"state-{3:03d}-adjudicated_unbound.json").exists()
