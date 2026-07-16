"""Publish one outbound-only initial visual-review request from an authored render.

The module owns the narrow ``authored_rendered -> initial_review_requested``
transition.  It never invokes a host, reads a critique, adjudicates a finding,
or enters the repair path.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import critique_zoom_crops
import repair_transaction

SCHEMA = "figure-agent.initial-visual-review-request.v1"
ACTION = "initial_visual_review_request"
STOP_BOUNDARY = "host_llm"


class ClosedLoopInitialReviewError(ValueError):
    """Raised when an initial visual-review handoff is not current and bound."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _workspace_file(
    root: Path, fixture: str, value: Path | str, *, label: str
) -> Path:
    try:
        return closed_loop_attempt_state._workspace_artifact(  # noqa: SLF001
            root, fixture, value, label=label
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopInitialReviewError(str(exc)) from exc


def _load_published_state(
    *, workspace_root: Path, fixture: str, state_path: Path
) -> tuple[dict[str, Any], Path]:
    actual_path = _workspace_file(
        workspace_root, fixture, state_path, label="closed_loop_state"
    )
    try:
        payload = json.loads(actual_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialReviewError("closed_loop_state_json_invalid") from exc
    try:
        state = closed_loop_attempt_state.validate_state(
            payload, workspace_root=workspace_root
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopInitialReviewError(f"closed_loop_state_invalid:{exc}") from exc
    if state["fixture"] != fixture:
        raise ClosedLoopInitialReviewError("closed_loop_state_fixture_mismatch")
    if actual_path != closed_loop_attempt_state.state_path(
        state, workspace_root=workspace_root
    ):
        raise ClosedLoopInitialReviewError("closed_loop_state_path_mismatch")
    return state, actual_path


def _state_evidence(state: dict[str, Any], role: str) -> dict[str, str]:
    records = {record["role"]: record for record in state["evidence"]}
    record = records.get(role)
    if not isinstance(record, dict):
        raise ClosedLoopInitialReviewError(f"initial_review_evidence_missing:{role}")
    return record


def _bound_root_artifacts(
    state: dict[str, Any], *, workspace_root: Path
) -> tuple[Path, dict[str, str], Path, dict[str, str]]:
    source_record = _state_evidence(state, "authored_source")
    render_record = _state_evidence(state, "render")
    source = _workspace_file(
        workspace_root,
        state["fixture"],
        source_record["path"],
        label="authored_source",
    )
    render = _workspace_file(
        workspace_root,
        state["fixture"],
        render_record["path"],
        label="render",
    )
    if _sha256(source) != source_record["sha256"]:
        raise ClosedLoopInitialReviewError("authored_source_hash_stale")
    if _sha256(render) != render_record["sha256"]:
        raise ClosedLoopInitialReviewError("render_hash_stale")
    return source, source_record, render, render_record


def _assert_current(
    state: dict[str, Any], state_path: Path, *, workspace_root: Path
) -> None:
    current = closed_loop_current_state.resolve_current_attempt(
        workspace_root, state["fixture"]
    )
    if current.get("resolution") != "current":
        raise ClosedLoopInitialReviewError(
            f"initial_review_current_resolution:{current.get('resolution')}"
        )
    if (
        current.get("path") != state_path.relative_to(workspace_root).as_posix()
        or current.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopInitialReviewError("initial_review_current_state_mismatch")


def _snapshot_render(
    render: Path, expected_sha256: str
) -> tuple[bytes, tuple[int, int, int, int, int]]:
    before = render.stat()
    data = render.read_bytes()
    after = render.stat()
    fingerprint = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        != fingerprint
        or "sha256:" + hashlib.sha256(data).hexdigest() != expected_sha256
    ):
        raise ClosedLoopInitialReviewError("initial_review_render_changed_during_snapshot")
    return data, fingerprint


def _assert_render_unchanged(
    render: Path, *, expected_sha256: str, expected_fingerprint: tuple[int, int, int, int, int]
) -> None:
    _, fingerprint = _snapshot_render(render, expected_sha256)
    if fingerprint != expected_fingerprint:
        raise ClosedLoopInitialReviewError("initial_review_render_drift_detected")


def _validate_crop_manifest(
    manifest_path: Path,
    *,
    fixture_root: Path,
    render: Path,
    render_sha256: str,
) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialReviewError("initial_review_crop_manifest_invalid") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != critique_zoom_crops.CROP_MANIFEST_SCHEMA
        or manifest.get("render_path") != render.relative_to(fixture_root).as_posix()
        or manifest.get("render_sha256") != render_sha256
    ):
        raise ClosedLoopInitialReviewError("initial_review_crop_manifest_render_drift")
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        raise ClosedLoopInitialReviewError("initial_review_crop_manifest_crops_invalid")
    expected_ids = {"full_q1", "full_q2", "full_q3", "full_q4", "print_178mm", "print_thumbnail"}
    seen_ids: set[str] = set()
    for crop in crops:
        if not isinstance(crop, dict):
            raise ClosedLoopInitialReviewError("initial_review_crop_record_invalid")
        crop_id = crop.get("id")
        path_value = crop.get("path")
        expected_hash = crop.get("sha256")
        if (
            not isinstance(crop_id, str)
            or not isinstance(path_value, str)
            or not isinstance(expected_hash, str)
            or crop_id in seen_ids
        ):
            raise ClosedLoopInitialReviewError("initial_review_crop_record_invalid")
        seen_ids.add(crop_id)
        relative = Path(path_value)
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise ClosedLoopInitialReviewError("initial_review_crop_path_unsafe")
        crop_path = fixture_root
        for part in relative.parts:
            crop_path = crop_path / part
            if crop_path.is_symlink():
                raise ClosedLoopInitialReviewError("initial_review_crop_path_unsafe")
        if not crop_path.is_file() or _sha256(crop_path) != expected_hash:
            raise ClosedLoopInitialReviewError("initial_review_crop_hash_stale")
    if not expected_ids.issubset(seen_ids):
        raise ClosedLoopInitialReviewError("initial_review_required_crops_missing")
    return manifest


def _crop_roles(manifest: dict[str, Any]) -> dict[str, list[str]]:
    crop_ids = {str(crop.get("id")) for crop in manifest["crops"] if isinstance(crop, dict)}
    roles = {
        "panel_scale": ["full_q1", "full_q2", "full_q3", "full_q4"],
        "print_scale": ["print_178mm", "print_thumbnail"],
    }
    if not set(roles["panel_scale"] + roles["print_scale"]).issubset(crop_ids):
        raise ClosedLoopInitialReviewError("initial_review_required_crops_missing")
    return roles


def _build_request(
    *,
    state: dict[str, Any],
    state_path: Path,
    source_record: dict[str, str],
    render_record: dict[str, str],
    crop_manifest_path: Path,
    crop_manifest: dict[str, Any],
    workspace_root: Path,
) -> dict[str, Any]:
    unsigned = {
        "schema": SCHEMA,
        "fixture": state["fixture"],
        "attempt": {
            "state_path": state_path.relative_to(workspace_root).as_posix(),
            "state_sha256": state["state_sha256"],
            "state_file_sha256": _sha256(state_path),
        },
        "authored_source": {"path": source_record["path"], "sha256": source_record["sha256"]},
        "render": {"path": render_record["path"], "sha256": render_record["sha256"]},
        "crop_manifest": {
            "path": crop_manifest_path.relative_to(workspace_root).as_posix(),
            "sha256": _sha256(crop_manifest_path),
        },
        "crop_roles": {
            "full_render": "render",
            **_crop_roles(crop_manifest),
        },
        "publication_acceptance": "not_claimed",
    }
    return {**unsigned, "request_sha256": _canonical_sha256(unsigned)}


def _validate_existing_request(
    *,
    state: dict[str, Any],
    state_path: Path,
    workspace_root: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    request_record = _state_evidence(state, "initial_visual_review_request")
    request_path = _workspace_file(
        workspace_root,
        state["fixture"],
        request_record["path"],
        label="initial_visual_review_request",
    )
    if _sha256(request_path) != request_record["sha256"]:
        raise ClosedLoopInitialReviewError("initial_review_request_hash_stale")
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialReviewError("initial_review_request_invalid") from exc
    if not isinstance(request, dict) or request.get("schema") != SCHEMA:
        raise ClosedLoopInitialReviewError("initial_review_request_invalid")
    unsigned = dict(request)
    request_hash = unsigned.pop("request_sha256", None)
    if request_hash != _canonical_sha256(unsigned):
        raise ClosedLoopInitialReviewError("initial_review_request_hash_invalid")
    source, source_record, render, render_record = _bound_root_artifacts_from_lineage(
        state, workspace_root=workspace_root
    )
    crop_manifest_record = request.get("crop_manifest")
    if not isinstance(crop_manifest_record, dict):
        raise ClosedLoopInitialReviewError("initial_review_crop_manifest_missing")
    crop_manifest_path = _workspace_file(
        workspace_root,
        state["fixture"],
        str(crop_manifest_record.get("path") or ""),
        label="initial_review_crop_manifest",
    )
    if crop_manifest_record.get("sha256") != _sha256(crop_manifest_path):
        raise ClosedLoopInitialReviewError("initial_review_crop_manifest_hash_stale")
    manifest = _validate_crop_manifest(
        crop_manifest_path,
        fixture_root=workspace_root / "examples" / state["fixture"],
        render=render,
        render_sha256=render_record["sha256"],
    )
    expected = _build_request(
        state=_initial_parent_state(state, workspace_root=workspace_root),
        state_path=_initial_parent_path(state, workspace_root=workspace_root),
        source_record=source_record,
        render_record=render_record,
        crop_manifest_path=crop_manifest_path,
        crop_manifest=manifest,
        workspace_root=workspace_root,
    )
    if request != expected:
        raise ClosedLoopInitialReviewError("initial_review_existing_request_mismatch")
    return request_path, crop_manifest_path, request


def _initial_parent_state(state: dict[str, Any], *, workspace_root: Path) -> dict[str, Any]:
    if state["state"] == "authored_rendered":
        return state
    previous = state.get("previous_state_path")
    if not isinstance(previous, str):
        raise ClosedLoopInitialReviewError("initial_review_parent_state_missing")
    parent, _ = _load_published_state(
        workspace_root=workspace_root, fixture=state["fixture"], state_path=Path(previous)
    )
    if parent["state"] != "authored_rendered":
        raise ClosedLoopInitialReviewError("initial_review_parent_state_invalid")
    return parent


def _initial_parent_path(state: dict[str, Any], *, workspace_root: Path) -> Path:
    if state["state"] == "authored_rendered":
        return closed_loop_attempt_state.state_path(state, workspace_root=workspace_root)
    previous = state.get("previous_state_path")
    if not isinstance(previous, str):
        raise ClosedLoopInitialReviewError("initial_review_parent_state_missing")
    return _workspace_file(
        workspace_root,
        state["fixture"],
        previous,
        label="initial_review_parent_state",
    )


def _bound_root_artifacts_from_lineage(
    state: dict[str, Any], *, workspace_root: Path
) -> tuple[Path, dict[str, str], Path, dict[str, str]]:
    return _bound_root_artifacts(
        _initial_parent_state(state, workspace_root=workspace_root),
        workspace_root=workspace_root,
    )


def _publish_crop_pack(
    *,
    fixture_root: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    attempt_root: Path,
    review_root: Path,
) -> Path:
    staging = attempt_root / ".initial-review-staging"
    if staging.exists() or staging.is_symlink():
        raise ClosedLoopInitialReviewError("initial_review_staging_conflict")
    staging.mkdir()
    try:
        snapshot = staging / "verified-render-snapshot.png"
        snapshot.write_bytes(render_bytes)
        crops_root = staging / "crops"
        manifest_path = crops_root / "manifest.json"
        critique_zoom_crops.build_zoom_crop_pack(
            fixture_root,
            snapshot,
            panel_crop_paths=(),
            output_dir=crops_root,
            manifest_path=manifest_path,
            include_detector_crops=False,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ClosedLoopInitialReviewError("initial_review_crop_manifest_invalid")
        staging_prefix = crops_root.relative_to(fixture_root).as_posix() + "/"
        final_prefix = (review_root / "crops").relative_to(fixture_root).as_posix() + "/"
        for crop in manifest.get("crops", []):
            if not isinstance(crop, dict) or not isinstance(crop.get("path"), str):
                raise ClosedLoopInitialReviewError("initial_review_crop_manifest_invalid")
            if not crop["path"].startswith(staging_prefix):
                raise ClosedLoopInitialReviewError("initial_review_crop_path_unsafe")
            crop["path"] = final_prefix + crop["path"].removeprefix(staging_prefix)
            crop["source_path"] = render.relative_to(fixture_root).as_posix()
        manifest["render_path"] = render.relative_to(fixture_root).as_posix()
        manifest["render_sha256"] = render_sha256
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        snapshot.unlink()
        if review_root.exists() or review_root.is_symlink():
            raise ClosedLoopInitialReviewError("initial_review_output_conflict")
        os.replace(staging, review_root)
    except Exception:
        if staging.is_dir() and not staging.is_symlink():
            shutil.rmtree(staging)
        raise
    return review_root / "crops" / "manifest.json"


def run_outbound_handoff(
    fixture: str,
    *,
    state_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate or publish one initial host-review request without invoking it."""
    root = Path(os.path.abspath(workspace_root))
    state, published_state_path = _load_published_state(
        workspace_root=root, fixture=fixture, state_path=state_path
    )
    if expected_state_sha256 is not None and state["state_sha256"] != expected_state_sha256:
        raise ClosedLoopInitialReviewError("closed_loop_projected_state_hash_mismatch")
    _assert_current(state, published_state_path, workspace_root=root)
    if state["state"] == "initial_review_requested":
        request_path, crop_manifest_path, request = _validate_existing_request(
            state=state, state_path=published_state_path, workspace_root=root
        )
        return {
            "action": ACTION, "stop_boundary": STOP_BOUNDARY, "stop_reason": "host_boundary",
            "required_actor": "host_llm", "created": False, "input_state": state,
            "input_state_path": published_state_path, "next_state": state["state"],
            "next_state_path": published_state_path, "request_path": request_path,
            "crop_manifest_path": crop_manifest_path, "request": request, "published_state": state,
        }
    if state["state"] != "authored_rendered":
        raise ClosedLoopInitialReviewError("closed_loop_state_not_authored_rendered")
    source, source_record, render, render_record = _bound_root_artifacts(
        state, workspace_root=root
    )
    del source
    attempt_root = published_state_path.parent
    review_root = attempt_root / "initial-review"
    request_path = review_root / "request.json"
    crop_manifest_path = review_root / "crops" / "manifest.json"
    next_state_path = attempt_root / (
        f"state-{state['sequence'] + 1:03d}-initial_review_requested.json"
    )
    if not execute:
        return {
            "action": ACTION, "stop_boundary": STOP_BOUNDARY, "stop_reason": "plan_only",
            "required_actor": "workflow_agent", "created": False, "input_state": state,
            "input_state_path": published_state_path, "next_state": "initial_review_requested",
            "next_state_path": next_state_path, "request_path": request_path,
            "crop_manifest_path": crop_manifest_path, "request": None, "published_state": None,
        }
    try:
        with closed_loop_attempt_state.attempt_transition_lock(attempt_root):
            state, published_state_path = _load_published_state(
                workspace_root=root, fixture=fixture, state_path=state_path
            )
            _assert_current(state, published_state_path, workspace_root=root)
            if state["state"] == "initial_review_requested":
                return run_outbound_handoff(
                    fixture, state_path=published_state_path, execute=True, workspace_root=root
                )
            if state["state"] != "authored_rendered":
                raise ClosedLoopInitialReviewError("closed_loop_state_not_authored_rendered")
            source, source_record, render, render_record = _bound_root_artifacts(
                state, workspace_root=root
            )
            del source
            render_bytes, fingerprint = _snapshot_render(render, render_record["sha256"])
            attempt_root = published_state_path.parent
            review_root = attempt_root / "initial-review"
            request_path = review_root / "request.json"
            crop_manifest_path = review_root / "crops" / "manifest.json"
            next_state_path = attempt_root / (
                f"state-{state['sequence'] + 1:03d}-initial_review_requested.json"
            )
            if review_root.is_symlink():
                raise ClosedLoopInitialReviewError("initial_review_output_conflict")
            if review_root.exists():
                if request_path.is_symlink() or crop_manifest_path.is_symlink():
                    raise ClosedLoopInitialReviewError("initial_review_output_conflict")
                if not request_path.is_file() or not crop_manifest_path.is_file():
                    raise ClosedLoopInitialReviewError("initial_review_output_conflict")
            else:
                crop_manifest_path = _publish_crop_pack(
                    fixture_root=root / "examples" / fixture,
                    render=render,
                    render_bytes=render_bytes,
                    render_sha256=render_record["sha256"],
                    attempt_root=attempt_root,
                    review_root=review_root,
                )
            _assert_render_unchanged(
                render,
                expected_sha256=render_record["sha256"],
                expected_fingerprint=fingerprint,
            )
            manifest = _validate_crop_manifest(
                crop_manifest_path,
                fixture_root=root / "examples" / fixture,
                render=render,
                render_sha256=render_record["sha256"],
            )
            request = _build_request(
                state=state,
                state_path=published_state_path,
                source_record=source_record,
                render_record=render_record,
                crop_manifest_path=crop_manifest_path,
                crop_manifest=manifest,
                workspace_root=root,
            )
            if request_path.is_file():
                try:
                    existing_request = json.loads(request_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ClosedLoopInitialReviewError(
                        "initial_review_existing_request_invalid"
                    ) from exc
                if existing_request != request:
                    raise ClosedLoopInitialReviewError(
                        "initial_review_existing_request_mismatch"
                    )
            else:
                repair_transaction.atomic_create_json(request_path, request)
            next_state = closed_loop_attempt_state.transition_state(
                state,
                next_state="initial_review_requested",
                actor="fig_run",
                actor_role="workflow_agent",
                evidence={"initial_visual_review_request": request_path},
                workspace_root=root,
                previous_state_path=published_state_path,
            )
            _assert_render_unchanged(
                render,
                expected_sha256=render_record["sha256"],
                expected_fingerprint=fingerprint,
            )
            published_next_state = closed_loop_attempt_state.publish_state(
                next_state, workspace_root=root
            )
    except (
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopInitialReviewError(f"initial_review_publication_failed:{exc}") from exc
    if published_next_state != next_state_path:
        raise ClosedLoopInitialReviewError("initial_review_state_path_mismatch")
    return {
        "action": ACTION, "stop_boundary": STOP_BOUNDARY, "stop_reason": "host_boundary",
        "required_actor": "host_llm", "created": True, "input_state": state,
        "input_state_path": published_state_path, "next_state": next_state["state"],
        "next_state_path": published_next_state, "request_path": request_path,
        "crop_manifest_path": crop_manifest_path, "request": request,
        "published_state": next_state,
    }
