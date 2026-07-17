from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closed_loop_initial_adjudication as adjudication  # noqa: E402
import closed_loop_initial_attribution_binding as binding  # noqa: E402
import closed_loop_repair_candidate  # noqa: E402
import fig_run  # noqa: E402
from test_closed_loop_initial_adjudication import FIXTURE, _decision, _setup  # noqa: E402


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _record(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _sha(path)}


def _state_record(record: dict[str, str]) -> dict[str, str]:
    return {"path": record["path"], "sha256": record["sha256"]}


def _approved_attempt(tmp_path: Path) -> tuple[Path, Path]:
    workspace, critique_state_path = _setup(tmp_path)
    decision = _decision(workspace, critique_state_path)
    approved = adjudication.run_initial_adjudication(
        FIXTURE,
        state_path=critique_state_path,
        decision_path=decision,
        execute=True,
        workspace_root=workspace,
    )
    return workspace, approved["next_state_path"]


def _binding(workspace: Path, state_path: Path) -> Path:
    fixture = workspace / "examples" / FIXTURE
    state = json.loads(state_path.read_text(encoding="utf-8"))
    records = {record["role"]: record for record in state["evidence"]}
    root_state = json.loads((state_path.parent / "state-000-authored_rendered.json").read_text())
    root_records = {record["role"]: record for record in root_state["evidence"]}
    source = workspace / root_records["authored_source"]["path"]
    semantic = _write(
        fixture / "semantic-contract.json",
        {
            "schema": "figure-agent.failure-first-semantic-contract.v1",
            "required_objects": ["panel_a.label", "panel_a.axis"],
            "protected_relations": ["label_remains_clear_of_axis"],
            "publication_acceptance": "not_claimed",
        },
    )
    registry = _write(
        fixture / "source-selectors.json",
        {
            "schema": "figure-agent.source-selector-registry.v1",
            "source_path": source.relative_to(workspace).as_posix(),
            "source_sha256": _sha(source),
            "semantic_contract": _record(semantic, workspace),
            "selectors": [
                {
                    "selector_id": "panel-a-label",
                    "anchor_start": "\\documentclass",
                    "anchor_end": "standalone}",
                    "repair_role": "movable",
                    "repair_family": "label_reflow",
                    "protected_invariants": ["axis stays visible"],
                    "semantic_object_refs": ["panel_a.label", "panel_a.axis"],
                    "semantic_relation_refs": ["label_remains_clear_of_axis"],
                }
            ],
        },
    )
    directory = state_path.parent / binding.BINDING_DIRECTORY
    directory.mkdir()
    payload: dict[str, object] = {
        "schema": binding.SCHEMA,
        "fixture": FIXTURE,
        "attempt_id": state["attempt_id"],
        "current_state": {
            "path": state_path.relative_to(workspace).as_posix(),
            "sha256": state["state_sha256"],
        },
        "attribution_handoff": _state_record(records["attribution_handoff"]),
        "adjudication": _state_record(records["adjudication"]),
        "initial_visual_review_response": _state_record(records["initial_visual_review_response"]),
        "critique": {**_state_record(records["critique"]), "finding_id": "C001"},
        "human_attributor": {"kind": "human", "identity": "attributor-1"},
        "authored_source": _state_record(root_records["authored_source"]),
        "selector_registry": _record(registry, workspace),
        "semantic_contract": _record(semantic, workspace),
        "selector_id": "panel-a-label",
        "repair_family": "label_reflow",
        "publication_acceptance": "not_claimed",
    }
    payload["binding_sha256"] = binding.canonical_binding_sha256(payload)
    return _write(directory / binding.BINDING_FILE, payload)


def _tree(root: Path) -> dict[Path, bytes]:
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_plan_is_write_free_then_execute_snapshots_and_binds(tmp_path: Path) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    binding_path = _binding(workspace, state_path)
    before = _tree(workspace)
    planned = binding.run_initial_attribution_binding(
        FIXTURE,
        state_path=state_path,
        binding_path=binding_path,
        execute=False,
        workspace_root=workspace,
    )
    assert planned["next_state"] == "repair_bound"
    assert _tree(workspace) == before

    created = binding.run_initial_attribution_binding(
        FIXTURE,
        state_path=state_path,
        binding_path=binding_path,
        execute=True,
        workspace_root=workspace,
    )
    snapshot = binding_path.with_name(binding.BINDING_SNAPSHOT_FILE)
    assert created["created"] is True
    assert snapshot.read_bytes() == binding_path.read_bytes()
    assert created["published_state"]["actor_role"] == "human_attributor"
    assert created["published_state"]["evidence"] == [
        {"role": "adjudicated_repair_binding", **_record(snapshot, workspace)}
    ]
    rerun = binding.run_initial_attribution_binding(
        FIXTURE,
        state_path=created["next_state_path"],
        binding_path=binding_path,
        execute=True,
        workspace_root=workspace,
    )
    assert rerun["created"] is False


@pytest.mark.parametrize(
    ("mutator", "error"),
    [
        (
            lambda payload: payload["initial_visual_review_response"].update(
                {"sha256": "sha256:" + "0" * 64}
            ),
            "initial_attribution_initial_visual_review_response_mismatch",
        ),
        (
            lambda payload: payload["critique"].update({"finding_id": "C999"}),
            "initial_attribution_finding_not_selected",
        ),
        (
            lambda payload: payload["human_attributor"].update({"identity": "another-human"}),
            "initial_attribution_human_attributor_mismatch",
        ),
        (
            lambda payload: payload.update({"selector_id": "missing"}),
            "initial_attribution_selector_invalid",
        ),
        (
            lambda payload: payload.update({"repair_family": "unknown_family"}),
            "initial_attribution_repair_family_invalid",
        ),
        (
            lambda payload: payload.pop("repair_family"),
            "initial_attribution_binding_schema_invalid",
        ),
    ],
)
def test_binding_rejects_wrong_current_provenance_or_target(
    tmp_path: Path, mutator: object, error: str
) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    path = _binding(workspace, state_path)
    payload = json.loads(path.read_text())
    mutator(payload)  # type: ignore[operator]
    payload["binding_sha256"] = binding.canonical_binding_sha256(payload)
    _write(path, payload)
    with pytest.raises(binding.ClosedLoopInitialAttributionBindingError, match=error):
        binding.run_initial_attribution_binding(
            FIXTURE,
            state_path=state_path,
            binding_path=path,
            execute=False,
            workspace_root=workspace,
        )


@pytest.mark.parametrize("execute", [False, True])
def test_binding_rejects_overlapping_selector_anchors(tmp_path: Path, execute: bool) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    path = _binding(workspace, state_path)
    payload = json.loads(path.read_text())
    registry_path = workspace / payload["selector_registry"]["path"]
    registry = json.loads(registry_path.read_text())
    registry["selectors"][0]["anchor_end"] = "class{stand"
    _write(registry_path, registry)
    payload["selector_registry"] = _record(registry_path, workspace)
    payload["binding_sha256"] = binding.canonical_binding_sha256(payload)
    _write(path, payload)
    with pytest.raises(
        binding.ClosedLoopInitialAttributionBindingError,
        match="initial_attribution_selector_anchor_invalid",
    ):
        binding.run_initial_attribution_binding(
            FIXTURE,
            state_path=state_path,
            binding_path=path,
            execute=execute,
            workspace_root=workspace,
        )
    assert not path.with_name(binding.BINDING_SNAPSHOT_FILE).exists()


@pytest.mark.parametrize("execute", [False, True])
def test_dangling_snapshot_symlink_fails_closed_without_recursion(
    tmp_path: Path, execute: bool
) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    path = _binding(workspace, state_path)
    snapshot = path.with_name(binding.BINDING_SNAPSHOT_FILE)
    snapshot.symlink_to("missing-binding.snapshot.json")
    with pytest.raises(
        binding.ClosedLoopInitialAttributionBindingError,
        match="initial_attribution_binding_snapshot_symlink",
    ):
        binding.run_initial_attribution_binding(
            FIXTURE,
            state_path=state_path,
            binding_path=path,
            execute=execute,
            workspace_root=workspace,
        )


def test_conflicting_snapshot_fails_closed_while_exact_snapshot_recovers(tmp_path: Path) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    path = _binding(workspace, state_path)
    snapshot = path.with_name(binding.BINDING_SNAPSHOT_FILE)
    snapshot.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        binding.ClosedLoopInitialAttributionBindingError,
        match="initial_attribution_binding_snapshot_conflict",
    ):
        binding.run_initial_attribution_binding(
            FIXTURE,
            state_path=state_path,
            binding_path=path,
            execute=True,
            workspace_root=workspace,
        )
    snapshot.write_bytes(path.read_bytes())
    recovered = binding.run_initial_attribution_binding(
        FIXTURE,
        state_path=state_path,
        binding_path=path,
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["created"] is True


@pytest.mark.parametrize("artifact", ["authored_source", "selector_registry", "semantic_contract"])
def test_execute_revalidates_declared_repair_authority_before_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact: str
) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    path = _binding(workspace, state_path)
    payload = json.loads(path.read_text())
    artifact_path = workspace / payload[artifact]["path"]
    original = binding._validate_binding  # noqa: SLF001
    calls = 0

    def mutate_after_fresh_validation(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        validated = original(*args, **kwargs)
        if calls == 2:
            artifact_path.write_text("{}\n", encoding="utf-8")
        return validated

    monkeypatch.setattr(binding, "_validate_binding", mutate_after_fresh_validation)
    with pytest.raises(
        binding.ClosedLoopInitialAttributionBindingError,
        match=f"initial_attribution_{artifact}_drift",
    ):
        binding.run_initial_attribution_binding(
            FIXTURE,
            state_path=state_path,
            binding_path=path,
            execute=True,
            workspace_root=workspace,
        )
    assert not path.with_name(binding.BINDING_SNAPSHOT_FILE).exists()


def test_v2_repair_bound_blocks_legacy_candidate_until_r4_13(tmp_path: Path) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    binding_path = _binding(workspace, state_path)
    bound = binding.run_initial_attribution_binding(
        FIXTURE,
        state_path=state_path,
        binding_path=binding_path,
        execute=True,
        workspace_root=workspace,
    )
    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="initial_attribution_binding_v2_requires_r4_13",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            FIXTURE,
            state_path=bound["next_state_path"],
            packet_path=binding_path,
            response_path=binding_path,
            preview_path=binding_path,
            execute=False,
            workspace_root=workspace,
        )


def test_execute_rejects_binding_replacement_before_snapshot_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    binding_path = _binding(workspace, state_path)
    original = binding._validate_binding  # noqa: SLF001
    calls = 0

    def mutate_after_fresh_snapshot(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        snapshot = original(*args, **kwargs)
        if calls == 2:
            binding_path.write_text("{}\n", encoding="utf-8")
        return snapshot

    monkeypatch.setattr(binding, "_validate_binding", mutate_after_fresh_snapshot)
    with pytest.raises(
        binding.ClosedLoopInitialAttributionBindingError,
        match="initial_attribution_binding_drift",
    ):
        binding.run_initial_attribution_binding(
            FIXTURE,
            state_path=state_path,
            binding_path=binding_path,
            execute=True,
            workspace_root=workspace,
        )
    assert not binding_path.with_name(binding.BINDING_SNAPSHOT_FILE).exists()
    sequence = json.loads(state_path.read_text())["sequence"] + 1
    assert not (state_path.parent / f"state-{sequence:03d}-repair_bound.json").exists()


def test_fig_run_accepts_only_the_explicit_initial_attribution_binding_input(
    tmp_path: Path,
) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    binding_path = _binding(workspace, state_path)
    payload = fig_run.run_workflow(
        FIXTURE,
        mode="authoring",
        goal="bind one selected initial-review finding",
        closed_loop_state=state_path,
        closed_loop_initial_attribution_binding=binding_path,
        repo_root=workspace,
    )
    assert payload["closed_loop"]["next_state"] == "repair_bound"
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"


def test_fig_run_cli_exposes_the_exact_initial_attribution_binding_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace, state_path = _approved_attempt(tmp_path)
    binding_path = _binding(workspace, state_path)
    assert (
        fig_run.main(
            [
                FIXTURE,
                "--mode",
                "authoring",
                "--goal",
                "bind one selected initial-review finding",
                "--closed-loop-state",
                str(state_path),
                "--closed-loop-initial-attribution-binding",
                str(binding_path),
                "--json",
            ],
            repo_root=workspace,
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["closed_loop"]["next_state"] == "repair_bound"
