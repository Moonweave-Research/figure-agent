from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import attempt_local_repair_binding as packet_boundary  # noqa: E402
import authoring_repair_packet  # noqa: E402
import closed_loop_initial_attribution_binding as attribution  # noqa: E402
from test_closed_loop_initial_attribution_binding import (  # noqa: E402
    FIXTURE,
    _approved_attempt,
    _binding,
    _tree,
)


def _repair_bound_attempt(tmp_path: Path) -> tuple[Path, Path]:
    workspace, adjudicated_path = _approved_attempt(tmp_path)
    binding_path = _binding(workspace, adjudicated_path)
    created = attribution.run_initial_attribution_binding(
        FIXTURE,
        state_path=adjudicated_path,
        binding_path=binding_path,
        execute=True,
        workspace_root=workspace,
    )
    return workspace, created["next_state_path"]


def test_plan_is_write_free_then_creates_attempt_local_packet_once(tmp_path: Path) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    before = _tree(workspace)
    state_before = state_path.read_bytes()
    planned = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=False,
        workspace_root=workspace,
    )
    assert planned["created"] is False
    assert planned["next_state"] == "repair_bound"
    assert _tree(workspace) == before

    created = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    paths = created["artifacts"]
    binding = json.loads(paths["binding"].read_text(encoding="utf-8"))
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    assert binding["schema"] == authoring_repair_packet.ATTEMPT_LOCAL_BINDING_SCHEMA
    assert packet["schema"] == authoring_repair_packet.ATTEMPT_LOCAL_PACKET_SCHEMA
    assert packet["packet_sha256"] == authoring_repair_packet.canonical_packet_sha256(packet)
    assert paths["prompt"].read_text(encoding="utf-8") == packet["prompt"]["utf8"]
    assert paths["sandbox"].read_bytes() == (workspace / packet["source"]["path"]).read_bytes()
    assert created["created"] is True
    assert state_path.read_bytes() == state_before

    before_recovery = _tree(workspace)
    recovered = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["created"] is False
    assert _tree(workspace) == before_recovery


def test_legacy_global_bridge_is_not_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("legacy global bridge read")

    monkeypatch.setattr(
        authoring_repair_packet.critique_repair_bridge,
        "validate_adjudicated_repair_binding_snapshot",
        forbidden,
    )
    packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )


def test_conflicting_or_symlinked_packet_artifact_fails_closed(tmp_path: Path) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    repair_root = state_path.parent / packet_boundary.REPAIR_PACKET_DIRECTORY
    repair_root.mkdir()
    packet_path = repair_root / packet_boundary.PACKET_FILE
    packet_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(packet_boundary.AttemptLocalRepairBindingError, match="packet_conflict"):
        packet_boundary.run_attempt_local_repair_packet(
            FIXTURE,
            state_path=state_path,
            model_id="test-model",
            execute=True,
            workspace_root=workspace,
        )

    packet_path.unlink()
    packet_path.symlink_to("missing.json")
    with pytest.raises(packet_boundary.AttemptLocalRepairBindingError, match="packet_symlink"):
        packet_boundary.run_attempt_local_repair_packet(
            FIXTURE,
            state_path=state_path,
            model_id="test-model",
            execute=False,
            workspace_root=workspace,
        )


def test_source_or_binding_drift_is_rejected_before_create(tmp_path: Path) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    root_state = json.loads((state_path.parent / "state-000-authored_rendered.json").read_text())
    source = next(
        record for record in root_state["evidence"] if record["role"] == "authored_source"
    )
    source_path = workspace / source["path"]
    source_path.write_text("drift\n", encoding="utf-8")
    with pytest.raises(packet_boundary.AttemptLocalRepairBindingError, match="evidence_hash_stale"):
        packet_boundary.run_attempt_local_repair_packet(
            FIXTURE,
            state_path=state_path,
            model_id="test-model",
            execute=False,
            workspace_root=workspace,
        )


def test_execute_rechecks_source_after_create_only_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    root_state = json.loads((state_path.parent / "state-000-authored_rendered.json").read_text())
    source = next(
        record for record in root_state["evidence"] if record["role"] == "authored_source"
    )
    source_path = workspace / source["path"]
    original_write = packet_boundary._write_all  # noqa: SLF001
    changed = False

    def mutate_after_first_write(fd: int, content: bytes) -> None:
        nonlocal changed
        original_write(fd, content)
        if not changed:
            changed = True
            source_path.write_text("changed after validation\n", encoding="utf-8")

    monkeypatch.setattr(packet_boundary, "_write_all", mutate_after_first_write)
    with pytest.raises(
        packet_boundary.AttemptLocalRepairBindingError,
        match="inputs_drifted_during_execution",
    ):
        packet_boundary.run_attempt_local_repair_packet(
            FIXTURE,
            state_path=state_path,
            model_id="test-model",
            execute=True,
            workspace_root=workspace,
        )


def test_staged_publish_never_follows_mid_publish_destination_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    destination = state_path.parent / packet_boundary.REPAIR_PACKET_DIRECTORY
    original_write = packet_boundary._write_all  # noqa: SLF001
    injected = False

    def inject_destination_symlink(fd: int, content: bytes) -> None:
        nonlocal injected
        original_write(fd, content)
        if not injected:
            injected = True
            destination.symlink_to(external, target_is_directory=True)

    monkeypatch.setattr(packet_boundary, "_write_all", inject_destination_symlink)
    with pytest.raises(packet_boundary.AttemptLocalRepairBindingError):
        packet_boundary.run_attempt_local_repair_packet(
            FIXTURE,
            state_path=state_path,
            model_id="test-model",
            execute=True,
            workspace_root=workspace,
        )
    assert not destination.exists()
    assert list(external.iterdir()) == []
    assert not list(state_path.parent.glob(".repair-packet-staging-*"))


def test_existing_v1_packet_schema_remains_unchanged() -> None:
    assert authoring_repair_packet.SCHEMA == "figure-agent.repair-execution-packet.v4"
    assert authoring_repair_packet.LEGACY_SCHEMA == "figure-agent.repair-execution-packet.v3"


def test_public_v2_validator_rejects_noncurrent_or_non_repair_bound_state(
    tmp_path: Path,
) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    created = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    binding_path = created["artifacts"]["binding"]
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    authored = json.loads(
        (state_path.parent / "state-000-authored_rendered.json").read_text(encoding="utf-8")
    )
    authored_path = state_path.parent / "state-000-authored_rendered.json"
    binding["current_state"] = {
        "path": authored_path.relative_to(workspace).as_posix(),
        "sha256": authored["state_sha256"],
    }
    binding["binding_sha256"] = authoring_repair_packet.canonical_attempt_local_binding_sha256(
        binding
    )
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="current state is not repair_bound",
    ):
        authoring_repair_packet.validate_attempt_local_repair_binding_v2(
            binding,
            workspace_root=workspace,
        )


def test_public_v2_validator_reconstructs_exact_initial_review_crops(tmp_path: Path) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    created = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    binding = json.loads(created["artifacts"]["binding"].read_text(encoding="utf-8"))
    binding["crops"][0] = {
        "id": binding["crops"][0]["id"],
        **binding["authored_source"],
    }
    binding["binding_sha256"] = authoring_repair_packet.canonical_attempt_local_binding_sha256(
        binding
    )
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="crops do not match initial request",
    ):
        authoring_repair_packet.validate_attempt_local_repair_binding_v2(
            binding,
            workspace_root=workspace,
        )


def test_public_v2_validator_rejects_forged_recomputed_attribution_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    created = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    binding = json.loads(created["artifacts"]["binding"].read_text(encoding="utf-8"))
    original_record = binding["initial_attribution_binding"]
    original_snapshot = workspace / original_record["path"]
    forged = json.loads(original_snapshot.read_text(encoding="utf-8"))
    forged["human_attributor"] = {"kind": "human", "identity": "forged-human"}
    forged["binding_sha256"] = attribution.canonical_binding_sha256(forged)
    forged_path = original_snapshot.with_name("forged.binding.snapshot.json")
    forged_path.write_text(
        json.dumps(forged, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    forged_record = {
        "path": forged_path.relative_to(workspace).as_posix(),
        "sha256": "sha256:" + hashlib.sha256(forged_path.read_bytes()).hexdigest(),
    }
    binding["initial_attribution_binding"] = forged_record
    binding["binding_sha256"] = authoring_repair_packet.canonical_attempt_local_binding_sha256(
        binding
    )
    original_evidence = authoring_repair_packet._attempt_local_evidence  # noqa: SLF001

    def forged_evidence(state: dict[str, object], role: str) -> dict[str, str]:
        if state.get("state") == "repair_bound" and role == "adjudicated_repair_binding":
            return forged_record
        return original_evidence(state, role)

    monkeypatch.setattr(authoring_repair_packet, "_attempt_local_evidence", forged_evidence)
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="attribution handoff mismatch",
    ):
        authoring_repair_packet.validate_attempt_local_repair_binding_v2(
            binding,
            workspace_root=workspace,
        )


@pytest.mark.parametrize(
    ("binding_path", "sandbox_path", "error"),
    [
        (
            "examples/fig3_resistance_mechanism/repair-packet/attempt-local-repair-binding.json",
            "examples/fig3_resistance_mechanism/repair-packet/repaired.tex",
            "binding path must be canonical",
        ),
        (
            "examples/fig3_resistance_mechanism/review/closed-loop/attempt-placeholder/repair-packet/attempt-local-repair-binding.json",
            "examples/fig3_resistance_mechanism/repair-packet/repaired.tex",
            "binding path must be canonical",
        ),
    ],
)
def test_public_compiler_rejects_caller_controlled_artifact_paths(
    tmp_path: Path,
    binding_path: str,
    sandbox_path: str,
    error: str,
) -> None:
    workspace, state_path = _repair_bound_attempt(tmp_path)
    planned = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=False,
        workspace_root=workspace,
    )
    binding, _source = packet_boundary._binding_payload(  # noqa: SLF001
        root=workspace,
        fixture=FIXTURE,
        repair_state=planned["input_state"],
        repair_path=state_path,
    )
    with pytest.raises(authoring_repair_packet.RepairExecutionPacketError, match=error):
        authoring_repair_packet.compile_attempt_local_repair_packet_v2(
            binding,
            binding_path=binding_path,
            sandbox_path=sandbox_path,
            model_id="test-model",
            workspace_root=workspace,
        )
