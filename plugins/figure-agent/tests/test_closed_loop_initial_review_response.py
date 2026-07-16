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
import closed_loop_initial_review  # noqa: E402
import closed_loop_initial_review_response as inbound  # noqa: E402
import fig_run  # noqa: E402
import post_repair_visual_review  # noqa: E402

FIXTURE = "fig3_resistance_mechanism"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest(path: Path, payload: dict[str, object]) -> Path:
    unsigned = dict(payload)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    _json(path, {**unsigned, "manifest_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest()})
    return path


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
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
            "source": {"path": f"examples/{FIXTURE}/{FIXTURE}.tex", "sha256": _sha256(source)},
            "render": {
                "path": f"examples/{FIXTURE}/build/{FIXTURE}.png",
                "sha256": _sha256(render),
            },
            "task": {"id": "task-1"},
            "model": {"identity": "model-1"},
            "budget": {"id": "budget-1"},
            "publication_acceptance": "not_claimed",
        },
    )
    admitted = closed_loop_attempt_admission.admit_root_attempt(
        FIXTURE, manifest_path=manifest, execute=True, workspace_root=workspace
    )
    initial = closed_loop_initial_review.run_outbound_handoff(
        FIXTURE, state_path=admitted["next_state_path"], execute=True, workspace_root=workspace
    )
    return workspace, fixture, initial["next_state_path"]


def _response_pack(workspace: Path, fixture: Path, state_path: Path) -> Path:
    request = json.loads((state_path.parent / "initial-review" / "request.json").read_text())
    manifest = json.loads(
        (state_path.parent / "initial-review" / "crops" / "manifest.json").read_text()
    )
    pack = state_path.parent / inbound.RESPONSE_PACK
    pack.mkdir()
    critique = pack / inbound.CRITIQUE_FILE
    source = Path(__file__).resolve().parents[1] / "examples" / FIXTURE / "critique.md"
    shutil.copyfile(source, critique)
    render = request["render"]
    artifacts = [{"role": "full_render", **render}]
    by_id = {crop["id"]: crop for crop in manifest["crops"]}
    artifacts.extend(
        {
            "role": crop_id,
            "path": f"examples/{FIXTURE}/{by_id[crop_id]['path']}",
            "sha256": by_id[crop_id]["sha256"],
        }
        for crop_id in inbound.EXPECTED_CROP_IDS
    )
    transcript = pack / inbound.TRANSCRIPT_FILE
    transcript.write_text("external host review transcript\n", encoding="utf-8")
    receipt = {
        "schema": post_repair_visual_review.EXECUTION_RECEIPT_SCHEMA,
        "request_sha256": request["request_sha256"],
        "actor": {
            "kind": "model",
            "identity": "external-reviewer",
            "model_or_tool": "vision-model",
        },
        "transcript": {
            "path": transcript.relative_to(workspace).as_posix(),
            "sha256": _sha256(transcript),
        },
        "inspected_artifacts": artifacts,
    }
    receipt["receipt_sha256"] = inbound._canonical_hash(receipt, omitted="receipt_sha256")  # noqa: SLF001
    receipt_path = pack / inbound.HOST_RECEIPT_FILE
    _json(receipt_path, receipt)
    response = {
        "schema": inbound.SCHEMA,
        "fixture": FIXTURE,
        "request_sha256": request["request_sha256"],
        "critique": {
            "path": critique.relative_to(workspace).as_posix(),
            "sha256": _sha256(critique),
        },
        "host_review_execution_receipt": {
            "path": receipt_path.relative_to(workspace).as_posix(),
            "sha256": _sha256(receipt_path),
        },
        "publication_acceptance": "not_claimed",
    }
    response["response_sha256"] = inbound._canonical_hash(response, omitted="response_sha256")  # noqa: SLF001
    response_path = pack / inbound.RESPONSE_FILE
    _json(response_path, response)
    return response_path


def test_plan_only_validates_supplied_pack_without_writing_state(tmp_path: Path) -> None:
    workspace, _, state_path = _setup(tmp_path)
    response_path = _response_pack(workspace, workspace / "examples" / FIXTURE, state_path)

    result = inbound.run_inbound_response(
        FIXTURE,
        state_path=state_path,
        response_path=response_path,
        execute=False,
        workspace_root=workspace,
    )

    assert result["next_state"] == "critique_unadjudicated"
    assert result["created"] is False
    assert not result["next_state_path"].exists()


def test_execute_binds_exact_request_critique_and_host_receipt_idempotently(tmp_path: Path) -> None:
    workspace, _, state_path = _setup(tmp_path)
    response_path = _response_pack(workspace, workspace / "examples" / FIXTURE, state_path)

    created = inbound.run_inbound_response(
        FIXTURE,
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    rerun = inbound.run_inbound_response(
        FIXTURE,
        state_path=created["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )

    assert created["next_state"] == "critique_unadjudicated"
    assert created["published_state"]["required_actor"] == "human_adjudicator"
    assert rerun["created"] is False
    assert created["published_state"]["publication_acceptance"] == "not_claimed"


@pytest.mark.parametrize(
    "mutation", ("response_hash", "receipt_order", "extra_file", "symlink", "transcript")
)
def test_response_pack_fails_closed_on_hash_layout_or_artifact_drift(
    tmp_path: Path, mutation: str
) -> None:
    workspace, _, state_path = _setup(tmp_path)
    response_path = _response_pack(workspace, workspace / "examples" / FIXTURE, state_path)
    pack = response_path.parent
    if mutation == "response_hash":
        response = json.loads(response_path.read_text())
        response["fixture"] = "forged"
        _json(response_path, response)
    elif mutation == "receipt_order":
        receipt_path = pack / inbound.HOST_RECEIPT_FILE
        receipt = json.loads(receipt_path.read_text())
        receipt["inspected_artifacts"] = list(reversed(receipt["inspected_artifacts"]))
        receipt["receipt_sha256"] = inbound._canonical_hash(receipt, omitted="receipt_sha256")  # noqa: SLF001
        _json(receipt_path, receipt)
        response = json.loads(response_path.read_text())
        response["host_review_execution_receipt"]["sha256"] = _sha256(receipt_path)
        response["response_sha256"] = inbound._canonical_hash(response, omitted="response_sha256")  # noqa: SLF001
        _json(response_path, response)
    elif mutation == "extra_file":
        (pack / "unexpected.json").write_text("{}", encoding="utf-8")
    elif mutation == "symlink":
        external = tmp_path / "external.md"
        external.write_text("x", encoding="utf-8")
        (pack / inbound.TRANSCRIPT_FILE).unlink()
        (pack / inbound.TRANSCRIPT_FILE).symlink_to(external)
    else:
        receipt_path = pack / inbound.HOST_RECEIPT_FILE
        receipt = json.loads(receipt_path.read_text())
        receipt["transcript"]["path"] = "examples/outside.md"
        receipt["receipt_sha256"] = inbound._canonical_hash(receipt, omitted="receipt_sha256")  # noqa: SLF001
        _json(receipt_path, receipt)
        response = json.loads(response_path.read_text())
        response["host_review_execution_receipt"]["sha256"] = _sha256(receipt_path)
        response["response_sha256"] = inbound._canonical_hash(response, omitted="response_sha256")  # noqa: SLF001
        _json(response_path, response)

    with pytest.raises(inbound.ClosedLoopInitialReviewResponseError):
        inbound.run_inbound_response(
            FIXTURE,
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
        )


def test_fig_run_has_distinct_initial_response_route_and_rejects_post_response_mix(
    tmp_path: Path,
) -> None:
    workspace, _, state_path = _setup(tmp_path)
    response_path = _response_pack(workspace, workspace / "examples" / FIXTURE, state_path)
    payload = fig_run.run_workflow(
        FIXTURE,
        mode="authoring",
        goal="review",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_initial_review_response=response_path,
        repo_root=workspace,
    )
    assert payload["final_action"] == inbound.ACTION
    assert payload["final_stop_boundary"] == "human_adjudicator"
    with pytest.raises(ValueError, match="mutually exclusive"):
        fig_run.run_workflow(
            FIXTURE,
            mode="authoring",
            goal="review",
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            closed_loop_initial_review_response=response_path,
            repo_root=workspace,
        )


def test_rerun_recovers_after_state_publication_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, state_path = _setup(tmp_path)
    response_path = _response_pack(workspace, workspace / "examples" / FIXTURE, state_path)
    original = closed_loop_attempt_state.publish_state
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> Path:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError("simulated_publish_failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(closed_loop_attempt_state, "publish_state", fail_once)
    with pytest.raises(inbound.ClosedLoopInitialReviewResponseError, match="publication_failed"):
        inbound.run_inbound_response(
            FIXTURE,
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
        )
    recovered = inbound.run_inbound_response(
        FIXTURE,
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["created"] is True


@pytest.mark.parametrize("artifact", (inbound.RESPONSE_FILE, inbound.TRANSCRIPT_FILE))
def test_published_initial_response_artifacts_are_durable_current_state_evidence(
    tmp_path: Path, artifact: str
) -> None:
    workspace, _, state_path = _setup(tmp_path)
    response_path = _response_pack(workspace, workspace / "examples" / FIXTURE, state_path)
    created = inbound.run_inbound_response(
        FIXTURE,
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    leaf_path = created["next_state_path"]
    leaf = json.loads(leaf_path.read_text(encoding="utf-8"))
    roles = {record["role"] for record in leaf["evidence"]}
    assert roles == {
        "critique",
        "host_review_execution_receipt",
        "initial_visual_review_response",
        "host_review_transcript",
    }
    target = response_path.parent / artifact
    if artifact == inbound.RESPONSE_FILE:
        target.unlink()
    else:
        target.write_text("tampered transcript\n", encoding="utf-8")

    with pytest.raises(closed_loop_attempt_state.ClosedLoopAttemptStateError):
        closed_loop_attempt_state.validate_state(leaf, workspace_root=workspace)
    projection = closed_loop_current_state.resolve_current_attempt(workspace, FIXTURE)
    assert projection["resolution"] == "invalid"
