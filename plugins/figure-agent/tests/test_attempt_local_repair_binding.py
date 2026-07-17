from __future__ import annotations

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

    recovered = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=state_path,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["created"] is False
    after = _tree(workspace)
    assert after == _tree(workspace)


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
    original_create = packet_boundary.repair_transaction.atomic_create_text
    changed = False

    def mutate_after_first_create(path: Path, content: str) -> None:
        nonlocal changed
        original_create(path, content)
        if not changed:
            changed = True
            source_path.write_text("changed after validation\n", encoding="utf-8")

    monkeypatch.setattr(
        packet_boundary.repair_transaction,
        "atomic_create_text",
        mutate_after_first_create,
    )
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


def test_existing_v1_packet_schema_remains_unchanged() -> None:
    assert authoring_repair_packet.SCHEMA == "figure-agent.repair-execution-packet.v4"
    assert authoring_repair_packet.LEGACY_SCHEMA == "figure-agent.repair-execution-packet.v3"
