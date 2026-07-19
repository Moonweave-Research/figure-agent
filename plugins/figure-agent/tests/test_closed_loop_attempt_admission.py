from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closed_loop_attempt_admission  # noqa: E402
import closed_loop_attempt_state  # noqa: E402
import fig_run  # noqa: E402
import repair_transaction  # noqa: E402


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(path: Path, payload: dict[str, object]) -> Path:
    bound = dict(payload)
    bound.pop("manifest_sha256", None)
    encoded = json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()
    bound["manifest_sha256"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    path.write_text(json.dumps(bound), encoding="utf-8")
    return path


def _setup(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "demo"
    fixture.mkdir(parents=True)
    source = fixture / "demo.tex"
    render = fixture / "build" / "demo.png"
    source.write_text("source", encoding="utf-8")
    render.parent.mkdir()
    Image.new("RGB", (640, 480), color=(44, 88, 155)).save(render)
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
    return workspace, fixture, source, manifest


def test_fig_run_admits_one_fresh_root_attempt_and_stops(tmp_path: Path) -> None:
    workspace, fixture, source, manifest = _setup(tmp_path)

    payload = fig_run.run_workflow(
        "demo",
        mode="authoring",
        goal="author figure",
        execute=True,
        closed_loop_attempt_manifest=manifest,
        repo_root=workspace,
    )

    assert payload["final_action"] == "initial_visual_review_request"
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["executed_count"] == 2
    assert payload["closed_loop"]["next_state"] == "initial_review_requested"
    assert payload["closed_loop"]["publication_acceptance"] == "not_claimed"
    assert "development_accepted" not in json.dumps(payload["closed_loop"])
    assert "golden" not in json.dumps(payload["closed_loop"])
    state_path = workspace / payload["closed_loop"]["next_state_path"]
    assert state_path.is_file()
    assert (workspace / payload["closed_loop"]["request_path"]).is_file()


def test_admission_can_restart_from_explicit_repair_required_parent(tmp_path: Path) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    parent = closed_loop_attempt_admission._validated_state(
        "demo", manifest, workspace_root=workspace
    )
    parent_path = closed_loop_attempt_state.publish_state(parent, workspace_root=workspace)
    for next_state, roles in (
        (
            "critique_unadjudicated",
            (
                "critique",
                "host_review_execution_receipt",
                "initial_visual_review_response",
                "host_review_transcript",
            ),
        ),
        ("repair_bound", ("adjudicated_repair_binding",)),
        (
            "repair_candidate_ready",
            ("repair_execution_packet", "repair_response", "materialization_preview"),
        ),
        ("repair_authorized", ("human_authorization",)),
        ("repair_required", ("repair_failure_record",)),
    ):
        evidence = {}
        for role in roles:
            artifact = fixture / f"{next_state}-{role}.json"
            artifact.write_text("{}\n", encoding="utf-8")
            evidence[role] = artifact
        parent = closed_loop_attempt_state.transition_state(
            parent,
            next_state=next_state,
            actor="workflow-agent",
            actor_role=parent["required_actor"],
            evidence=evidence,
            workspace_root=workspace,
            previous_state_path=parent_path,
        )
        parent_path = closed_loop_attempt_state.publish_state(
            parent, workspace_root=workspace
        )

    child = closed_loop_attempt_admission.admit_root_attempt(
        "demo",
        manifest_path=manifest,
        parent_state_path=parent_path,
        execute=True,
        workspace_root=workspace,
    )

    assert child["created"] is True
    assert child["state"]["parent_state_path"] == parent_path.relative_to(workspace).as_posix()
    assert child["state"]["parent_state_sha256"] == parent["state_sha256"]
    assert child["state"]["attempt_id"] != parent["attempt_id"]


def test_plan_only_validates_and_never_acquires_or_writes_admission_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    monkeypatch.setattr(
        closed_loop_attempt_state,
        "fixture_admission_lock",
        lambda *_args, **_kwargs: pytest.fail("plan-only must not acquire admission lease"),
    )

    payload = fig_run.run_workflow(
        "demo", mode="authoring", goal="author", closed_loop_attempt_manifest=manifest,
        repo_root=workspace,
    )

    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["created"] is False
    assert not (fixture / "review").exists()
    assert not (fixture / ".closed-loop-admission.lock").exists()


def test_legacy_lease_prevents_root_admission_until_release(tmp_path: Path) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)

    with closed_loop_attempt_state.fixture_admission_lock(workspace, fixture.name):
        with pytest.raises(
            closed_loop_attempt_admission.ClosedLoopAttemptAdmissionError,
            match="canonical_admission_legacy_coordination_busy",
        ):
            closed_loop_attempt_admission.admit_root_attempt(
                fixture.name,
                manifest_path=manifest,
                execute=True,
                workspace_root=workspace,
            )
        assert not (fixture / "review").exists()

    admitted = closed_loop_attempt_admission.admit_root_attempt(
        fixture.name,
        manifest_path=manifest,
        execute=True,
        workspace_root=workspace,
    )
    assert admitted["created"] is True


def test_inner_attempt_transition_lock_keeps_existing_busy_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)

    @contextmanager
    def busy_transition_lock(*_args: object, **_kwargs: object) -> object:
        raise repair_transaction.RepairTransactionError("transaction lock exists")
        yield

    monkeypatch.setattr(
        closed_loop_attempt_state,
        "attempt_transition_lock",
        busy_transition_lock,
    )

    with pytest.raises(
        closed_loop_attempt_admission.ClosedLoopAttemptAdmissionError,
        match="attempt_transition_lock_busy",
    ):
        closed_loop_attempt_admission.admit_root_attempt(
            fixture.name,
            manifest_path=manifest,
            execute=True,
            workspace_root=workspace,
        )
    assert not (fixture / "review").exists()


def test_latest_inner_lock_contention_is_not_misreported_as_fixture_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    fixture_lock_calls = 0

    @contextmanager
    def mixed_fixture_lease(*_args: object, **_kwargs: object) -> object:
        nonlocal fixture_lock_calls
        fixture_lock_calls += 1
        if fixture_lock_calls == 1:
            raise closed_loop_attempt_state.FixtureAdmissionLeaseBusy(
                "fixture_admission_lease_busy"
            )
        yield

    @contextmanager
    def busy_transition_lock(*_args: object, **_kwargs: object) -> object:
        raise repair_transaction.RepairTransactionError("transaction lock exists")
        yield

    monkeypatch.setattr(
        closed_loop_attempt_state,
        "fixture_admission_lock",
        mixed_fixture_lease,
    )
    monkeypatch.setattr(
        closed_loop_attempt_state,
        "attempt_transition_lock",
        busy_transition_lock,
    )

    with pytest.raises(
        closed_loop_attempt_admission.ClosedLoopAttemptAdmissionError,
        match="attempt_transition_lock_busy",
    ):
        closed_loop_attempt_admission.admit_root_attempt(
            fixture.name,
            manifest_path=manifest,
            execute=True,
            workspace_root=workspace,
        )


def test_plan_only_accepts_workspace_relative_attempt_manifest(tmp_path: Path) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)

    payload = fig_run.run_workflow(
        "demo",
        mode="authoring",
        goal="author",
        closed_loop_attempt_manifest=manifest.relative_to(workspace),
        repo_root=workspace,
    )

    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["manifest_path"] == "examples/demo/attempt-manifest.json"
    assert not (fixture / "review").exists()


def test_execute_accepts_workspace_relative_attempt_manifest_and_recovers(
    tmp_path: Path,
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    relative_manifest = manifest.relative_to(workspace)

    created = fig_run.run_workflow(
        "demo",
        mode="authoring",
        goal="author",
        execute=True,
        closed_loop_attempt_manifest=relative_manifest,
        repo_root=workspace,
    )
    recovered = fig_run.run_workflow(
        "demo",
        mode="authoring",
        goal="author",
        execute=True,
        closed_loop_attempt_manifest=relative_manifest,
        repo_root=workspace,
    )

    assert created["final_stop_reason"] == "host_boundary"
    assert created["closed_loop"]["created"] is True
    assert recovered["closed_loop"]["created"] is False
    assert created["closed_loop"]["manifest_path"] == "examples/demo/attempt-manifest.json"
    assert len(list((fixture / "review" / "closed-loop").rglob("state-*.json"))) == 2


@pytest.mark.parametrize("field", ["source", "render"])
def test_admission_rejects_stale_bound_artifact_hashes(tmp_path: Path, field: str) -> None:
    workspace, fixture, source, manifest = _setup(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload[field]["sha256"] = "sha256:" + "0" * 64
    manifest = _manifest(manifest, payload | {"manifest_sha256": "ignored"})

    with pytest.raises(ValueError, match=f"attempt_manifest_{field}_hash_stale"):
        fig_run.run_workflow(
            "demo", mode="authoring", goal="author", execute=True,
            closed_loop_attempt_manifest=manifest, repo_root=workspace,
        )
    assert not (fixture / "review").exists()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data.__setitem__("fixture", "other"), "attempt_manifest_fixture_mismatch"),
        (
            lambda data: data["author"].__setitem__("role", "reviewer"),
            "attempt_manifest_author_invalid",
        ),
        (
            lambda data: data["source"].__setitem__("path", "examples/other/x.tex"),
            "source_cross_fixture",
        ),
    ],
)
def test_admission_rejects_mismatched_author_or_cross_fixture_paths(
    tmp_path: Path, mutate: object, message: str
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    mutate(data)  # type: ignore[operator]
    manifest = _manifest(manifest, data | {"manifest_sha256": "ignored"})

    with pytest.raises(ValueError, match=message):
        fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                             closed_loop_attempt_manifest=manifest, repo_root=workspace)
    assert not (fixture / "review").exists()


def test_admission_rejects_existing_nonterminal_and_recovers_identical_publish(
    tmp_path: Path,
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    first = fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                                 closed_loop_attempt_manifest=manifest, repo_root=workspace)
    recovered = fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                                     closed_loop_attempt_manifest=manifest, repo_root=workspace)

    assert first["closed_loop"]["created"] is True
    assert recovered["closed_loop"]["created"] is False
    assert len(list((fixture / "review" / "closed-loop").rglob("state-*.json"))) == 2

    other = fixture / "second-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["author"] = {"identity": "author-2", "role": "authoring_agent"}
    other = _manifest(other, data | {"manifest_sha256": "ignored"})
    with pytest.raises(ValueError, match="existing_current_attempt:current"):
        fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                             closed_loop_attempt_manifest=other, repo_root=workspace)


def test_admission_rejects_terminal_existing_attempt(tmp_path: Path) -> None:
    workspace, fixture, source, manifest = _setup(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-0",
        actor_role="authoring_agent",
        evidence={
            "attempt_manifest": manifest,
            "authored_source": source,
            "render": fixture / "build" / "demo.png",
        },
    )
    state_path = closed_loop_attempt_state.publish_state(state, workspace_root=workspace)
    abort = fixture / "abort.json"
    abort.write_text("{}", encoding="utf-8")
    terminal = closed_loop_attempt_state.transition_state(
        state, next_state="aborted", actor="workflow-1", actor_role="workflow_agent",
        evidence={"abort_record": abort}, workspace_root=workspace, previous_state_path=state_path,
    )
    closed_loop_attempt_state.publish_state(terminal, workspace_root=workspace)

    with pytest.raises(ValueError, match="existing_current_attempt:current"):
        fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                             closed_loop_attempt_manifest=manifest, repo_root=workspace)


def test_admission_rejects_ambiguous_existing_attempts(tmp_path: Path) -> None:
    workspace, fixture, source, manifest = _setup(tmp_path)
    render = fixture / "build" / "demo.png"
    second_manifest = fixture / "second-attempt-manifest.json"
    second_manifest.write_text("second", encoding="utf-8")
    for actor, evidence_manifest in (
        ("author-a", manifest),
        ("author-b", second_manifest),
    ):
        state = closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor=actor,
            actor_role="authoring_agent",
            evidence={
                "attempt_manifest": evidence_manifest,
                "authored_source": source,
                "render": render,
            },
        )
        closed_loop_attempt_state.publish_state(state, workspace_root=workspace)

    with pytest.raises(ValueError, match="existing_current_attempt:ambiguous"):
        fig_run.run_workflow(
            "demo",
            mode="authoring",
            goal="author",
            execute=True,
            closed_loop_attempt_manifest=manifest,
            repo_root=workspace,
        )


@pytest.mark.parametrize(
    ("setup", "resolution"),
    [
        (
            lambda fixture: (fixture / "review" / "closed-loop" / "attempt-bad").mkdir(
                parents=True
            ),
            "invalid",
        ),
        (
            lambda fixture: (fixture / "review").symlink_to(fixture / "outside"),
            "invalid",
        ),
    ],
)
def test_admission_rejects_invalid_or_symlinked_current_attempts(
    tmp_path: Path, setup: object, resolution: str
) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    setup(fixture)  # type: ignore[operator]

    with pytest.raises(ValueError, match=f"existing_current_attempt:{resolution}"):
        fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                             closed_loop_attempt_manifest=manifest, repo_root=workspace)


def test_admission_rejects_symlinked_manifest_path(tmp_path: Path) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)
    linked = fixture / "linked-manifest.json"
    linked.symlink_to(manifest)

    with pytest.raises(ValueError, match="attempt_manifest_symlink"):
        fig_run.run_workflow("demo", mode="authoring", goal="author", execute=True,
                             closed_loop_attempt_manifest=linked, repo_root=workspace)


def test_identical_concurrent_admission_recovers_one_publication(tmp_path: Path) -> None:
    workspace, fixture, _, manifest = _setup(tmp_path)

    def admit() -> dict[str, object]:
        return fig_run.run_workflow(
            "demo",
            mode="authoring",
            goal="author",
            execute=True,
            closed_loop_attempt_manifest=manifest,
            repo_root=workspace,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: admit(), range(2)))

    assert sorted(result["closed_loop"]["created"] for result in results) == [False, True]
    assert len(list((fixture / "review" / "closed-loop").rglob("state-*.json"))) == 2
