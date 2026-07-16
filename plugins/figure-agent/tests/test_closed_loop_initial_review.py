from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closed_loop_attempt_admission  # noqa: E402
import closed_loop_attempt_state  # noqa: E402
import closed_loop_initial_review  # noqa: E402
import closed_loop_post_review  # noqa: E402
import fig_run  # noqa: E402


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(path: Path, payload: dict[str, object]) -> Path:
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    unsigned["manifest_sha256"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    path.write_text(json.dumps(unsigned), encoding="utf-8")
    return path


def _setup(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "demo"
    fixture.mkdir(parents=True)
    source = fixture / "demo.tex"
    source.write_text("\\documentclass{standalone}\n", encoding="utf-8")
    render = fixture / "build" / "demo.png"
    render.parent.mkdir()
    Image.new("RGB", (800, 600), color=(44, 88, 155)).save(render)
    manifest = _manifest(
        fixture / "attempt-manifest.json",
        {
            "schema": "figure-agent.root-attempt-manifest.v1",
            "fixture": "demo",
            "author": {"identity": "author-1", "role": "authoring_agent"},
            "source": {"path": "examples/demo/demo.tex", "sha256": _sha256(source)},
            "render": {"path": "examples/demo/build/demo.png", "sha256": _sha256(render)},
            "task": {"id": "task-1"},
            "model": {"identity": "model-1"},
            "budget": {"id": "budget-1"},
            "publication_acceptance": "not_claimed",
        },
    )
    admitted = closed_loop_attempt_admission.admit_root_attempt(
        "demo", manifest_path=manifest, execute=True, workspace_root=workspace
    )
    return workspace, fixture, source, render, admitted["next_state_path"]


def _rewrite_initial_pack_and_state(
    created: dict[str, object], *, mutate_manifest: callable
) -> None:
    """Keep request/state hashes valid so pack-boundary checks are exercised."""
    manifest_path = created["crop_manifest_path"]
    request_path = created["request_path"]
    state_path = created["next_state_path"]
    assert isinstance(manifest_path, Path)
    assert isinstance(request_path, Path)
    assert isinstance(state_path, Path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mutate_manifest(manifest)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["crop_manifest"]["sha256"] = _sha256(manifest_path)
    unsigned_request = dict(request)
    unsigned_request.pop("request_sha256", None)
    request["request_sha256"] = closed_loop_initial_review._canonical_sha256(  # noqa: SLF001
        unsigned_request
    )
    request_path.write_text(json.dumps(request, sort_keys=True), encoding="utf-8")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["evidence"][0]["sha256"] = _sha256(request_path)
    state["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(state)
    state_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")


def test_plan_only_verifies_root_without_writing_request_or_crops(tmp_path: Path) -> None:
    workspace, fixture, _, _, state_path = _setup(tmp_path)

    result = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=False, workspace_root=workspace
    )

    assert result["created"] is False
    assert result["next_state"] == "initial_review_requested"
    assert result["stop_reason"] == "plan_only"
    assert not (state_path.parent / "initial-review").exists()
    assert not result["next_state_path"].exists()
    assert not (fixture / "critique.md").exists()


def test_fig_run_root_admission_publishes_only_initial_outbound_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, fixture, source, render, _ = _setup(tmp_path)
    # Start a distinct fixture so the root integration itself owns admission.
    second = workspace / "examples" / "second"
    second.mkdir(parents=True)
    second_source = second / "second.tex"
    second_source.write_text("source", encoding="utf-8")
    second_render = second / "build" / "second.png"
    second_render.parent.mkdir()
    Image.new("RGB", (640, 480), color=(80, 120, 180)).save(second_render)
    manifest = _manifest(
        second / "attempt-manifest.json",
        {
            "schema": "figure-agent.root-attempt-manifest.v1",
            "fixture": "second",
            "author": {"identity": "author-2", "role": "authoring_agent"},
            "source": {"path": "examples/second/second.tex", "sha256": _sha256(second_source)},
            "render": {
                "path": "examples/second/build/second.png",
                "sha256": _sha256(second_render),
            },
            "task": {"id": "task-2"},
            "model": {"identity": "model-2"},
            "budget": {"id": "budget-2"},
            "publication_acceptance": "not_claimed",
        },
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda *_args, **_kwargs: pytest.fail("root admission must not invoke a host command"),
    )

    payload = fig_run.run_workflow(
        "second",
        mode="authoring",
        goal="author",
        execute=True,
        closed_loop_attempt_manifest=manifest,
        repo_root=workspace,
    )

    assert payload["final_action"] == "initial_visual_review_request"
    assert payload["final_stop_boundary"] == "host_llm"
    assert payload["closed_loop"]["next_state"] == "initial_review_requested"
    assert payload["closed_loop"]["publication_acceptance"] == "not_claimed"
    request_path = workspace / payload["closed_loop"]["request_path"]
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["schema"] == "figure-agent.initial-visual-review-request.v1"
    assert request["render"]["sha256"] == _sha256(second_render)
    assert request["crop_roles"]["panel_scale"] == [
        "full_q1", "full_q2", "full_q3", "full_q4"
    ]
    assert request["crop_roles"]["print_scale"] == ["print_178mm", "print_thumbnail"]
    assert not (second / "critique.md").exists()
    assert not (second / "critique_adjudication.yaml").exists()
    assert source.is_file() and render.is_file()


def test_execute_writes_hash_bound_request_state_and_is_idempotent(tmp_path: Path) -> None:
    workspace, fixture, source, render, state_path = _setup(tmp_path)

    created = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )
    recovered = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=created["next_state_path"], execute=True, workspace_root=workspace
    )

    assert created["created"] is True
    assert recovered["created"] is False
    request_path = created["request_path"]
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["authored_source"] == {
        "path": "examples/demo/demo.tex", "sha256": _sha256(source)
    }
    assert request["render"] == {
        "path": "examples/demo/build/demo.png", "sha256": _sha256(render)
    }
    assert request["publication_acceptance"] == "not_claimed"
    state = json.loads(created["next_state_path"].read_text(encoding="utf-8"))
    assert state["state"] == "initial_review_requested"
    assert state["evidence"][0]["role"] == "initial_visual_review_request"
    manifest_path = state_path.parent / "initial-review" / "crops" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert {crop["id"] for crop in manifest["crops"]} >= {
        "full_q1", "full_q2", "full_q3", "full_q4", "print_178mm", "print_thumbnail"
    }


def test_initial_request_is_the_canonical_predecessor_of_unadjudicated_critique(
    tmp_path: Path,
) -> None:
    workspace, fixture, _, _, state_path = _setup(tmp_path)
    initial = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )
    critique = fixture / "critique.md"
    receipt = fixture / "host-review-receipt.json"
    critique.write_text("unadjudicated host finding\n", encoding="utf-8")
    receipt.write_text("{}\n", encoding="utf-8")

    next_state = closed_loop_attempt_state.transition_state(
        initial["published_state"],
        next_state="critique_unadjudicated",
        actor="host-reviewer",
        actor_role="host_llm",
        evidence={"critique": critique, "host_review_execution_receipt": receipt},
        workspace_root=workspace,
        previous_state_path=initial["next_state_path"],
    )

    assert next_state["required_actor"] == "human_adjudicator"


def test_retry_recovers_a_complete_request_left_before_state_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, _, _, state_path = _setup(tmp_path)
    original_publish = closed_loop_attempt_state.publish_state
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> Path:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "simulated_publish_failure"
            )
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(closed_loop_attempt_state, "publish_state", fail_once)
    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_publication_failed",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo", state_path=state_path, execute=True, workspace_root=workspace
        )

    recovered = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )

    assert recovered["created"] is True
    assert recovered["next_state"] == "initial_review_requested"


@pytest.mark.parametrize("failure", ["tamper", "missing", "symlink"])
def test_initial_review_fails_closed_for_invalid_bound_render(
    tmp_path: Path, failure: str
) -> None:
    workspace, fixture, _, render, state_path = _setup(tmp_path)
    if failure == "tamper":
        render.write_bytes(b"tampered")
    elif failure == "missing":
        render.unlink()
    else:
        external = tmp_path / "render.png"
        external.write_bytes(render.read_bytes())
        render.unlink()
        render.symlink_to(external)

    with pytest.raises(closed_loop_initial_review.ClosedLoopInitialReviewError):
        closed_loop_initial_review.run_outbound_handoff(
            "demo", state_path=state_path, execute=True, workspace_root=workspace
        )
    assert not list((fixture / "review" / "closed-loop").rglob("initial-review"))


def test_initial_review_fails_closed_for_ambiguous_current_attempt(tmp_path: Path) -> None:
    workspace, fixture, source, render, state_path = _setup(tmp_path)
    alternate_manifest = fixture / "alternate-manifest.json"
    alternate_manifest.write_text("{}\n", encoding="utf-8")
    alternate = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-2",
        actor_role="authoring_agent",
        evidence={
            "attempt_manifest": alternate_manifest,
            "authored_source": source,
            "render": render,
        },
    )
    closed_loop_attempt_state.publish_state(alternate, workspace_root=workspace)

    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_current_resolution:ambiguous",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo", state_path=state_path, execute=True, workspace_root=workspace
        )


def test_idempotent_recheck_rejects_a_symlinked_crop(tmp_path: Path) -> None:
    workspace, fixture, _, _, state_path = _setup(tmp_path)
    created = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )
    manifest = json.loads(created["crop_manifest_path"].read_text(encoding="utf-8"))
    crop = fixture / manifest["crops"][0]["path"]
    external = tmp_path / "copied-crop.png"
    external.write_bytes(crop.read_bytes())
    crop.unlink()
    crop.symlink_to(external)

    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_crop_path_unsafe",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo",
            state_path=created["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )


def test_idempotent_recheck_rejects_forged_build_render_crop_mapping(tmp_path: Path) -> None:
    workspace, fixture, _, render, state_path = _setup(tmp_path)
    created = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )

    def forge(manifest: dict[str, object]) -> None:
        crops = manifest["crops"]
        assert isinstance(crops, list)
        first = next(crop for crop in crops if crop["id"] == "full_q1")
        first["path"] = "build/demo.png"
        first["sha256"] = _sha256(render)

    _rewrite_initial_pack_and_state(created, mutate_manifest=forge)

    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_crop_path_outside_attempt",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo",
            state_path=created["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )


def test_idempotent_recheck_rejects_semantically_forged_crop_metadata(tmp_path: Path) -> None:
    workspace, _, _, _, state_path = _setup(tmp_path)
    created = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )

    def forge(manifest: dict[str, object]) -> None:
        crops = manifest["crops"]
        assert isinstance(crops, list)
        first = next(crop for crop in crops if crop["id"] == "full_q1")
        first["bbox_px"] = [1, 1, 2, 2]

    _rewrite_initial_pack_and_state(created, mutate_manifest=forge)

    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_crop_semantics_invalid",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo",
            state_path=created["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )


def test_idempotent_recheck_rejects_pixel_forged_crop_with_valid_hash(tmp_path: Path) -> None:
    workspace, fixture, _, _, state_path = _setup(tmp_path)
    created = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )
    manifest_path = created["crop_manifest_path"]
    assert isinstance(manifest_path, Path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first = next(crop for crop in manifest["crops"] if crop["id"] == "full_q1")
    crop_path = fixture / first["path"]
    with Image.open(crop_path) as crop_image:
        crop_size = crop_image.size
    Image.new("RGB", crop_size, color=(1, 2, 3)).save(crop_path)

    def forge(updated_manifest: dict[str, object]) -> None:
        crops = updated_manifest["crops"]
        assert isinstance(crops, list)
        next(crop for crop in crops if crop["id"] == "full_q1")["sha256"] = _sha256(
            crop_path
        )

    _rewrite_initial_pack_and_state(created, mutate_manifest=forge)

    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_crop_pixels_invalid",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo",
            state_path=created["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )


def test_root_retry_recovers_only_a_complete_verified_crop_pack(tmp_path: Path) -> None:
    workspace, fixture, _, render, state_path = _setup(tmp_path)
    state, published_state_path = closed_loop_initial_review._load_published_state(  # noqa: SLF001
        workspace_root=workspace,
        fixture="demo",
        state_path=state_path,
    )
    _, source_record, _, render_record = closed_loop_initial_review._bound_root_artifacts(  # noqa: SLF001
        state, workspace_root=workspace
    )
    request_path, _, _ = closed_loop_initial_review._publish_review_pack(  # noqa: SLF001
        fixture_root=fixture,
        render=render,
        render_bytes=render.read_bytes(),
        render_sha256=render_record["sha256"],
        attempt_root=published_state_path.parent,
        review_root=published_state_path.parent / "initial-review",
        state=state,
        state_path=published_state_path,
        source_record=source_record,
        render_record=render_record,
        workspace_root=workspace,
    )
    request_path.unlink()

    recovered = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )

    assert recovered["created"] is True
    assert request_path.is_file()


def test_atomic_crop_request_publish_leaves_no_partial_final_pack_on_request_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, _, _, state_path = _setup(tmp_path)
    original_create = closed_loop_initial_review.repair_transaction.atomic_create_json

    def fail_staged_request(path: Path, payload: dict[str, object]) -> None:
        if path.name == "request.json" and ".initial-review-staging" in path.parts:
            raise closed_loop_initial_review.repair_transaction.RepairTransactionError(
                "simulated_request_failure"
            )
        original_create(path, payload)

    monkeypatch.setattr(
        closed_loop_initial_review.repair_transaction,
        "atomic_create_json",
        fail_staged_request,
    )
    with pytest.raises(
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        match="initial_review_publication_failed",
    ):
        closed_loop_initial_review.run_outbound_handoff(
            "demo", state_path=state_path, execute=True, workspace_root=workspace
        )

    review_root = state_path.parent / "initial-review"
    assert not review_root.exists()
    assert not (state_path.parent / ".initial-review-staging").exists()


def test_post_repair_adapter_rejects_initial_review_state(tmp_path: Path) -> None:
    workspace, _, _, _, state_path = _setup(tmp_path)
    initial = closed_loop_initial_review.run_outbound_handoff(
        "demo", state_path=state_path, execute=True, workspace_root=workspace
    )

    with pytest.raises(
        closed_loop_post_review.ClosedLoopPostReviewError,
        match="closed_loop_state_not_machine_repaired",
    ):
        closed_loop_post_review.run_outbound_handoff(
            "demo",
            state_path=initial["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )
