"""Compile immutable R4.13a attempt-local repair authority without state advance.

This adapter intentionally creates only a same-attempt repair packet bundle.  It
does not consult legacy global critique/adjudication bridges, invoke a model,
materialize a response, render, compile, or publish a new closed-loop state.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

import authoring_repair_packet
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_initial_attribution_binding
import closed_loop_initial_review
import closed_loop_initial_review_response
import repair_transaction

ACTION = "attempt_local_repair_packet"
REPAIR_PACKET_DIRECTORY = "repair-packet"
BINDING_FILE = "attempt-local-repair-binding.json"
PACKET_FILE = "attempt-local-repair-packet.json"
PROMPT_FILE = "repair-prompt.md"
SANDBOX_FILE = "repaired.tex"
_EXPECTED_CROP_IDS = (
    "full_q1",
    "full_q2",
    "full_q3",
    "full_q4",
    "print_178mm",
    "print_thumbnail",
)


class AttemptLocalRepairBindingError(ValueError):
    """Raised when R4.13a cannot derive an immutable same-attempt bundle."""


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _safe_regular(path: Path, *, root: Path, label: str) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise AttemptLocalRepairBindingError(f"{label}_outside_workspace") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AttemptLocalRepairBindingError(f"{label}_symlink")
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise AttemptLocalRepairBindingError(f"{label}_missing") from exc
    if not stat.S_ISREG(mode):
        raise AttemptLocalRepairBindingError(f"{label}_not_regular")
    return path


def _load_state(root: Path, fixture: str, path: Path) -> tuple[dict[str, Any], Path]:
    requested = Path(os.path.abspath(path if path.is_absolute() else root / path))
    _safe_regular(requested, root=root, label="state")
    try:
        payload = json.loads(requested.read_text(encoding="utf-8"))
        state = closed_loop_attempt_state.validate_state(payload, workspace_root=root)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
    ) as exc:
        raise AttemptLocalRepairBindingError(f"state_invalid:{exc}") from exc
    if state["fixture"] != fixture or requested != closed_loop_attempt_state.state_path(
        state, workspace_root=root
    ):
        raise AttemptLocalRepairBindingError("state_path_mismatch")
    return state, requested


def _previous(root: Path, fixture: str, state: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    value = state.get("previous_state_path")
    if not isinstance(value, str):
        raise AttemptLocalRepairBindingError("state_parent_missing")
    return _load_state(root, fixture, Path(value))


def _record(state: dict[str, Any], role: str) -> dict[str, str]:
    matches = [item for item in state["evidence"] if item["role"] == role]
    if len(matches) != 1:
        raise AttemptLocalRepairBindingError(f"state_evidence_{role}_missing")
    return {"path": matches[0]["path"], "sha256": matches[0]["sha256"]}


def _read_record(root: Path, record: dict[str, str], *, label: str) -> bytes:
    relative = Path(record["path"])
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise AttemptLocalRepairBindingError(f"{label}_path_unsafe")
    path = _safe_regular(root / relative, root=root, label=label)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise AttemptLocalRepairBindingError(f"{label}_missing") from exc
    if _sha256(content) != record["sha256"]:
        raise AttemptLocalRepairBindingError(f"{label}_hash_drift")
    return content


def _assert_current(root: Path, fixture: str, state: dict[str, Any], state_path: Path) -> None:
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        current.get("resolution") != "current"
        or current.get("state") != "repair_bound"
        or current.get("path") != state_path.relative_to(root).as_posix()
        or current.get("state_sha256") != state["state_sha256"]
        or current.get("publication_acceptance") != "not_claimed"
    ):
        raise AttemptLocalRepairBindingError("current_state_mismatch")


def _attempt_chain(
    root: Path, fixture: str, repair_state: dict[str, Any], repair_path: Path
) -> tuple[dict[str, Any], Path, dict[str, Any], Path, dict[str, Any], Path, dict[str, Any], Path]:
    adjudicated, adjudicated_path = _previous(root, fixture, repair_state)
    critique, critique_path = _previous(root, fixture, adjudicated)
    review, review_path = _previous(root, fixture, critique)
    authored, authored_path = _previous(root, fixture, review)
    if (
        repair_state["state"] != "repair_bound"
        or adjudicated["state"] != "adjudicated_unbound"
        or critique["state"] != "critique_unadjudicated"
        or review["state"] != "initial_review_requested"
        or authored["state"] != "authored_rendered"
        or authored["sequence"] != 0
    ):
        raise AttemptLocalRepairBindingError("attempt_chain_invalid")
    try:
        parent_state = None
        parent_state_path = None
        if authored.get("parent_state_path") is not None:
            parent_state, parent_state_path = _load_state(
                root, fixture, Path(authored["parent_state_path"])
            )
        closed_loop_attempt_state.validate_chain(
            [authored, review, critique, adjudicated, repair_state],
            workspace_root=root,
            parent_state=parent_state,
            parent_state_path=parent_state_path,
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise AttemptLocalRepairBindingError(f"attempt_chain_invalid:{exc}") from exc
    return (
        authored,
        authored_path,
        review,
        review_path,
        critique,
        critique_path,
        adjudicated,
        adjudicated_path,
    )


def _binding_payload(
    *,
    root: Path,
    fixture: str,
    repair_state: dict[str, Any],
    repair_path: Path,
) -> tuple[dict[str, object], bytes]:
    (
        authored,
        _authored_path,
        review,
        review_path,
        critique_state,
        _critique_path,
        adjudicated,
        adjudicated_path,
    ) = _attempt_chain(root, fixture, repair_state, repair_path)
    try:
        request_path, manifest_path, request = (
            closed_loop_initial_review.validate_outbound_request_pack(
                state=review, state_path=review_path, workspace_root=root
            )
        )
        response_path = root / _record(critique_state, "initial_visual_review_response")["path"]
        closed_loop_initial_review_response.inspect_inbound_response_pack(
            fixture=fixture,
            initial_review_state=review,
            initial_review_state_path=review_path,
            response_path=response_path,
            workspace_root=root,
        )
    except (
        closed_loop_initial_review.ClosedLoopInitialReviewError,
        closed_loop_initial_review_response.ClosedLoopInitialReviewResponseError,
    ) as exc:
        raise AttemptLocalRepairBindingError(f"initial_review_evidence_invalid:{exc}") from exc

    initial_binding_path = root / _record(repair_state, "adjudicated_repair_binding")["path"]
    original_binding_path = initial_binding_path.with_name(
        closed_loop_initial_attribution_binding.BINDING_FILE
    )
    try:
        restored = closed_loop_initial_attribution_binding.run_initial_attribution_binding(
            fixture,
            state_path=repair_path,
            binding_path=original_binding_path,
            execute=False,
            workspace_root=root,
        )
    except closed_loop_initial_attribution_binding.ClosedLoopInitialAttributionBindingError as exc:
        raise AttemptLocalRepairBindingError(f"initial_attribution_binding_invalid:{exc}") from exc
    if restored.get("binding_snapshot_path") != initial_binding_path:
        raise AttemptLocalRepairBindingError("initial_attribution_snapshot_mismatch")
    try:
        initial_binding = json.loads(
            _read_record(
                root,
                _record(repair_state, "adjudicated_repair_binding"),
                label="initial_attribution_binding",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AttemptLocalRepairBindingError("initial_attribution_binding_invalid") from exc
    if not isinstance(initial_binding, dict):
        raise AttemptLocalRepairBindingError("initial_attribution_binding_invalid")

    source = _record(authored, "authored_source")
    source_bytes = _read_record(root, source, label="source")
    render = _record(authored, "render")
    _read_record(root, render, label="render")
    try:
        manifest = json.loads(
            _read_record(
                root,
                {
                    "path": manifest_path.relative_to(root).as_posix(),
                    "sha256": _sha256(manifest_path.read_bytes()),
                },
                label="crop_manifest",
            ).decode("utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AttemptLocalRepairBindingError("crop_manifest_invalid") from exc
    crops = manifest.get("crops") if isinstance(manifest, dict) else None
    if not isinstance(crops, list):
        raise AttemptLocalRepairBindingError("crops_invalid")
    by_id = {crop.get("id"): crop for crop in crops if isinstance(crop, dict)}
    if set(by_id) != set(_EXPECTED_CROP_IDS):
        raise AttemptLocalRepairBindingError("crops_invalid")
    crop_records: list[dict[str, str]] = []
    for crop_id in _EXPECTED_CROP_IDS:
        crop = by_id[crop_id]
        path, sha = crop.get("path"), crop.get("sha256")
        if not isinstance(path, str) or not isinstance(sha, str):
            raise AttemptLocalRepairBindingError("crops_invalid")
        record = {"path": f"examples/{fixture}/{path}", "sha256": sha}
        _read_record(root, record, label=f"crop_{crop_id}")
        crop_records.append({"id": crop_id, **record})

    selector_registry = initial_binding.get("selector_registry")
    semantic = initial_binding.get("semantic_contract")
    selector_id = initial_binding.get("selector_id")
    if (
        not isinstance(selector_registry, dict)
        or not isinstance(semantic, dict)
        or not isinstance(selector_id, str)
    ):
        raise AttemptLocalRepairBindingError("initial_attribution_binding_invalid")
    registry_bytes = _read_record(root, selector_registry, label="selector_registry")
    _read_record(root, semantic, label="semantic_contract")
    try:
        registry = json.loads(registry_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AttemptLocalRepairBindingError("selector_registry_invalid") from exc
    selectors = registry.get("selectors") if isinstance(registry, dict) else None
    selected = [
        item
        for item in selectors or []
        if isinstance(item, dict) and item.get("selector_id") == selector_id
    ]
    if len(selected) != 1:
        raise AttemptLocalRepairBindingError("selector_registry_invalid")
    selector = selected[0]
    selected_finding = initial_binding.get("critique")
    if not isinstance(selected_finding, dict) or not isinstance(
        selected_finding.get("finding_id"), str
    ):
        raise AttemptLocalRepairBindingError("selected_finding_invalid")
    payload: dict[str, object] = {
        "schema": authoring_repair_packet.ATTEMPT_LOCAL_BINDING_SCHEMA,
        "fixture": fixture,
        "attempt_id": repair_state["attempt_id"],
        "current_state": {
            "path": repair_path.relative_to(root).as_posix(),
            "sha256": repair_state["state_sha256"],
        },
        "authored_source": source,
        "render": render,
        "initial_review_request": {
            "path": request_path.relative_to(root).as_posix(),
            "sha256": _sha256(request_path.read_bytes()),
        },
        "initial_visual_review_response": _record(critique_state, "initial_visual_review_response"),
        "critique": _record(critique_state, "critique"),
        "adjudication": _record(adjudicated, "adjudication"),
        "attribution_handoff": _record(adjudicated, "attribution_handoff"),
        "initial_attribution_binding": _record(repair_state, "adjudicated_repair_binding"),
        "crop_manifest": {
            "path": manifest_path.relative_to(root).as_posix(),
            "sha256": _sha256(manifest_path.read_bytes()),
        },
        "crops": crop_records,
        "selected_finding_id": selected_finding["finding_id"],
        "human_attributor": initial_binding["human_attributor"],
        "selector": selector,
        "repair_family": initial_binding["repair_family"],
        "semantic_contract": semantic,
        "publication_acceptance": "not_claimed",
    }
    payload["binding_sha256"] = authoring_repair_packet.canonical_attempt_local_binding_sha256(
        payload
    )
    try:
        authoring_repair_packet.validate_attempt_local_repair_binding_v2(
            payload, workspace_root=root
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise AttemptLocalRepairBindingError(str(exc)) from exc
    return payload, source_bytes


def _artifact_paths(state_path: Path) -> dict[str, Path]:
    directory = state_path.parent / REPAIR_PACKET_DIRECTORY
    return {
        "binding": directory / BINDING_FILE,
        "packet": directory / PACKET_FILE,
        "prompt": directory / PROMPT_FILE,
        "sandbox": directory / SANDBOX_FILE,
    }


def _write_all(fd: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write")
        view = view[written:]


def _publish_staged_bundle(
    attempt_root: Path,
    *,
    expected: dict[str, bytes],
) -> None:
    """Publish a complete bundle by rename; never follow final-directory symlinks."""
    flags = os.O_RDONLY | os.O_DIRECTORY
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    attempt_fd = os.open(attempt_root, flags | nofollow)
    stage_name = f".{REPAIR_PACKET_DIRECTORY}-staging-{secrets.token_hex(16)}"
    stage_fd: int | None = None
    published = False
    created_names: list[str] = []
    try:
        os.mkdir(stage_name, 0o700, dir_fd=attempt_fd)
        stage_fd = os.open(stage_name, flags | nofollow, dir_fd=attempt_fd)
        for name in ("binding", "sandbox", "packet", "prompt"):
            filename = {
                "binding": BINDING_FILE,
                "packet": PACKET_FILE,
                "prompt": PROMPT_FILE,
                "sandbox": SANDBOX_FILE,
            }[name]
            fd = os.open(
                filename,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
                0o600,
                dir_fd=stage_fd,
            )
            try:
                _write_all(fd, expected[name])
                os.fsync(fd)
            finally:
                os.close(fd)
            created_names.append(filename)
        os.fsync(stage_fd)
        os.rename(
            stage_name,
            REPAIR_PACKET_DIRECTORY,
            src_dir_fd=attempt_fd,
            dst_dir_fd=attempt_fd,
        )
        published = True
        os.fsync(attempt_fd)
    finally:
        if not published:
            if stage_fd is not None:
                for filename in reversed(created_names):
                    try:
                        os.unlink(filename, dir_fd=stage_fd)
                    except OSError:
                        pass
        if stage_fd is not None:
            os.close(stage_fd)
        if not published:
            try:
                if stat.S_ISLNK(
                    os.stat(
                        REPAIR_PACKET_DIRECTORY,
                        dir_fd=attempt_fd,
                        follow_symlinks=False,
                    ).st_mode
                ):
                    os.unlink(REPAIR_PACKET_DIRECTORY, dir_fd=attempt_fd)
            except FileNotFoundError:
                pass
            try:
                os.rmdir(stage_name, dir_fd=attempt_fd)
            except OSError:
                pass
        os.close(attempt_fd)


def _assert_destination(path: Path, expected: bytes, *, root: Path, label: str) -> bool:
    if path.is_symlink():
        raise AttemptLocalRepairBindingError(f"{label}_symlink")
    if not path.exists():
        return False
    _safe_regular(path, root=root, label=label)
    try:
        existing = path.read_bytes()
    except OSError as exc:
        raise AttemptLocalRepairBindingError(f"{label}_invalid") from exc
    if existing != expected:
        raise AttemptLocalRepairBindingError(f"{label}_conflict")
    return True


def _plan(
    fixture: str,
    *,
    state_path: Path,
    model_id: str,
    workspace_root: Path,
) -> dict[str, Any]:
    root = Path(os.path.abspath(workspace_root))
    state, published_path = _load_state(root, fixture, state_path)
    _assert_current(root, fixture, state, published_path)
    if state["state"] != "repair_bound":
        raise AttemptLocalRepairBindingError("state_not_repair_bound")
    binding, source_bytes = _binding_payload(
        root=root, fixture=fixture, repair_state=state, repair_path=published_path
    )
    paths = _artifact_paths(published_path)
    directory = paths["binding"].parent
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise AttemptLocalRepairBindingError("repair_packet_directory_invalid")
    binding_bytes = (
        json.dumps(binding, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    )
    try:
        packet, prompt = authoring_repair_packet.compile_attempt_local_repair_packet_v2(
            binding,
            binding_path=paths["binding"].relative_to(root).as_posix(),
            sandbox_path=paths["sandbox"].relative_to(root).as_posix(),
            model_id=model_id,
            workspace_root=root,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise AttemptLocalRepairBindingError(str(exc)) from exc
    packet_bytes = (
        json.dumps(packet, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    )
    expected = {
        "binding": binding_bytes,
        "packet": packet_bytes,
        "prompt": prompt.encode("utf-8"),
        "sandbox": source_bytes,
    }
    present = {
        name: _assert_destination(paths[name], content, root=root, label=name)
        for name, content in expected.items()
    }
    return {
        "root": root,
        "state": state,
        "state_path": published_path,
        "paths": paths,
        "expected": expected,
        "complete": all(present.values()),
    }


def run_attempt_local_repair_packet(
    fixture: str,
    *,
    state_path: Path,
    model_id: str,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Plan or create only the immutable R4.13a packet bundle for one attempt."""
    plan = _plan(
        fixture,
        state_path=state_path,
        model_id=model_id,
        workspace_root=workspace_root,
    )
    if expected_state_sha256 is not None and plan["state"]["state_sha256"] != expected_state_sha256:
        raise AttemptLocalRepairBindingError("projected_state_hash_mismatch")
    result = {
        "action": ACTION,
        "created": False,
        "input_state": plan["state"],
        "input_state_path": plan["state_path"],
        "next_state": "repair_bound",
        "next_state_path": plan["state_path"],
        "artifacts": plan["paths"],
        "stop_boundary": "workflow_agent",
        "stop_reason": "packet_compiled" if plan["complete"] else "plan_only",
        "publication_acceptance": "not_claimed",
    }
    if plan["complete"]:
        return result
    if not execute:
        return result
    try:
        with closed_loop_attempt_state.attempt_transition_lock(plan["state_path"].parent):
            with repair_transaction.recoverable_exclusive_lock(
                plan["state_path"].parent / ".attempt-local-repair-packet.lock",
                owner="figure_agent_attempt_local_repair_packet",
            ):
                fresh = _plan(
                    fixture,
                    state_path=state_path,
                    model_id=model_id,
                    workspace_root=workspace_root,
                )
                if (
                    expected_state_sha256 is not None
                    and fresh["state"]["state_sha256"] != expected_state_sha256
                ):
                    raise AttemptLocalRepairBindingError("projected_state_hash_mismatch")
                if fresh["expected"] != plan["expected"]:
                    raise AttemptLocalRepairBindingError("inputs_drifted_during_execution")
                if not fresh["complete"]:
                    _publish_staged_bundle(
                        fresh["state_path"].parent,
                        expected=fresh["expected"],
                    )
                try:
                    verified = _plan(
                        fixture,
                        state_path=state_path,
                        model_id=model_id,
                        workspace_root=workspace_root,
                    )
                except AttemptLocalRepairBindingError as exc:
                    raise AttemptLocalRepairBindingError("inputs_drifted_during_execution") from exc
                if not verified["complete"] or verified["expected"] != fresh["expected"]:
                    raise AttemptLocalRepairBindingError("inputs_drifted_during_execution")
    except (repair_transaction.RepairTransactionError, OSError, ValueError) as exc:
        if isinstance(exc, AttemptLocalRepairBindingError):
            raise
        raise AttemptLocalRepairBindingError(f"packet_publication_failed:{exc}") from exc
    result["created"] = True
    result["stop_reason"] = "packet_compiled"
    return result
