"""Build fixture-local quality memory events from existing artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import candidate_contracts
import evidence_index
import fixture_identity
import runtime_paths

EVENT_SCHEMA = "figure-agent.quality-memory-event.v1"
LOG_SCHEMA = "figure-agent.quality-memory-log.v1"


class QualityMemoryEventError(ValueError):
    """Raised when memory extraction would read outside fixture boundaries."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_time(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise QualityMemoryEventError(f"sandbox_symlink_forbidden: {label}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise QualityMemoryEventError(f"{label}_missing") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualityMemoryEventError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise QualityMemoryEventError(f"{label}_invalid")
    return payload


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise QualityMemoryEventError("path_escape") from exc


def _candidate_sandboxes(example_dir: Path) -> list[Path]:
    build_dir = example_dir / "build"
    candidates_root = build_dir / "candidates"
    if build_dir.is_symlink():
        raise QualityMemoryEventError("sandbox_symlink_forbidden: build")
    if candidates_root.is_symlink():
        raise QualityMemoryEventError("sandbox_symlink_forbidden: candidates")
    if not candidates_root.is_dir():
        return []
    sandboxes: list[Path] = []
    for sandbox in sorted(candidates_root.iterdir(), key=lambda path: path.name):
        if not sandbox.is_dir() and not sandbox.is_symlink():
            continue
        fixture_identity.validate_fixture_name(sandbox.name)
        if sandbox.is_symlink():
            raise QualityMemoryEventError(f"sandbox_symlink_forbidden: {sandbox.name}")
        try:
            sandbox.resolve().relative_to(candidates_root.resolve())
        except ValueError as exc:
            raise QualityMemoryEventError("candidate path_escape") from exc
        sandboxes.append(sandbox)
    return sandboxes


def _stage_status(payload: dict[str, Any], stage: str) -> str | None:
    stages = payload.get("stages")
    if not isinstance(stages, dict):
        return None
    value = stages.get(stage)
    if isinstance(value, dict):
        status = value.get("status")
        return str(status) if status is not None else None
    return str(value) if value is not None else None


def _candidate_metadata(
    example_dir: Path,
    manifest: dict[str, Any],
    candidate_id: str,
) -> dict[str, Any]:
    candidate_set_path = manifest.get("candidate_set_path")
    if not isinstance(candidate_set_path, str) or not candidate_set_path:
        return {}
    try:
        candidate_set_file = candidate_contracts.fixture_relative_path(
            example_dir,
            candidate_set_path,
        )
    except candidate_contracts.CandidateContractError as exc:
        raise QualityMemoryEventError("candidate_set_path_escape") from exc
    if candidate_set_file.is_symlink():
        raise QualityMemoryEventError("sandbox_symlink_forbidden: candidate_set")
    if not candidate_set_file.is_file():
        return {}
    candidate_set = _load_json(candidate_set_file, "candidate_set")
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        return {}
    for item in candidates:
        if isinstance(item, dict) and item.get("id") == candidate_id:
            return item
    return {}


def _candidate_family(manifest: dict[str, Any], candidate: dict[str, Any]) -> str:
    value = (
        manifest.get("edit_family")
        or manifest.get("edit_class")
        or candidate.get("edit_family")
        or candidate.get("edit_class")
        or manifest.get("family")
        or candidate.get("family")
    )
    return str(value) if value else "unknown"


def _candidate_target(manifest: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    target = manifest.get("target")
    if isinstance(target, dict):
        return dict(target)
    target = candidate.get("target")
    if isinstance(target, dict):
        return dict(target)
    return {"panel": "unknown", "subregion": "unknown"}


def _event(
    *,
    fixture: str,
    event_type: str,
    source_artifact: str,
    source_payload: dict[str, Any],
    source_path: Path,
    candidate_id: str | None = None,
    edit_family: str = "unknown",
    target: dict[str, Any] | None = None,
    pre_state: dict[str, Any] | None = None,
    post_state: dict[str, Any] | None = None,
    outcome_state: str = "unknown",
    pipeline_ok: bool | None = None,
    quality_movement: str | None = None,
    reason: str = "",
    evidence_paths: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "fixture": fixture,
        "event_type": event_type,
        "source_artifact": source_artifact,
        "candidate_id": candidate_id,
        "edit_family": edit_family,
        "target": target or {"panel": "unknown", "subregion": "unknown"},
        "outcome": {
            "state": outcome_state,
            "pipeline_ok": pipeline_ok,
            "quality_movement": quality_movement,
            "reason": reason,
            "evidence_paths": evidence_paths or [source_artifact],
        },
    }
    return {
        "schema": EVENT_SCHEMA,
        "fixture": fixture,
        "event_id": candidate_contracts.canonical_hash(payload),
        "event_type": event_type,
        "created_at": _artifact_time(source_path),
        "source_artifact": source_artifact,
        "candidate_id": candidate_id,
        "edit_family": edit_family,
        "target": target or {"panel": "unknown", "subregion": "unknown"},
        "pre_state": pre_state or {},
        "post_state": post_state or {},
        "outcome": {
            "state": outcome_state,
            "pipeline_ok": pipeline_ok,
            "quality_movement": quality_movement,
            "reason": reason,
            "evidence_paths": evidence_paths or [source_artifact],
        },
        "metrics": metrics or {},
    }


def _post_apply_pipeline_ok(apply_status: str | None, post_state: dict[str, str]) -> bool:
    return apply_status == "applied" and all(
        post_state.get(stage) == "success" for stage in ("compile", "export", "status")
    )


def _quality_movement_from_apply(
    apply_status: str | None,
    post_apply: dict[str, Any],
    *,
    pipeline_ok: bool,
) -> str | None:
    class_verifiers = post_apply.get("class_verifiers")
    if apply_status == "rolled_back":
        return "regressed"
    if isinstance(class_verifiers, dict) and (
        class_verifiers.get("rolled_back") is True or class_verifiers.get("status") == "failed"
    ):
        return "regressed"
    detector_recheck = post_apply.get("detector_recheck")
    if isinstance(detector_recheck, dict) and detector_recheck.get("status") == "failed":
        return "regressed"
    if not pipeline_ok:
        return None
    if isinstance(detector_recheck, dict) and detector_recheck.get("status") == "success":
        return "improved"
    return "neutral"


def _candidate_events(name: str, example_dir: Path, sandbox: Path) -> list[dict[str, Any]]:
    candidate_id = sandbox.name
    manifest_path = sandbox / "candidate_manifest.json"
    if not manifest_path.is_file():
        return []
    manifest = _load_json(manifest_path, "candidate_manifest")
    if str(manifest.get("candidate_id") or candidate_id) != candidate_id:
        raise QualityMemoryEventError("candidate_id_mismatch")
    if manifest.get("fixture") is not None and manifest.get("fixture") != name:
        raise QualityMemoryEventError("fixture_mismatch")
    candidate = _candidate_metadata(example_dir, manifest, candidate_id)
    manifest_rel = _fixture_relative(example_dir, manifest_path)
    family = _candidate_family(manifest, candidate)
    target = _candidate_target(manifest, candidate)
    events = [
        _event(
            fixture=name,
            event_type="candidate_generated",
            source_artifact=manifest_rel,
            source_payload=manifest,
            source_path=manifest_path,
            candidate_id=candidate_id,
            edit_family=family,
            target=target,
        )
    ]

    render_path = sandbox / "render_manifest.json"
    if render_path.is_file():
        render = _load_json(render_path, "render_manifest")
        if render.get("figure_name") is not None and render.get("figure_name") != name:
            raise QualityMemoryEventError("fixture_mismatch")
        if render.get("fixture") is not None and render.get("fixture") != name:
            raise QualityMemoryEventError("fixture_mismatch")
        if render.get("candidate_id") is not None and render.get("candidate_id") != candidate_id:
            raise QualityMemoryEventError("candidate_id_mismatch")
        render_rel = _fixture_relative(example_dir, render_path)
        post_state = {
            stage: _stage_status(render, stage)
            for stage in ("compile", "export", "crop", "evaluate")
            if _stage_status(render, stage) is not None
        }
        events.append(
            _event(
                fixture=name,
                event_type="candidate_rendered",
                source_artifact=render_rel,
                source_payload=render,
                source_path=render_path,
                candidate_id=candidate_id,
                edit_family=family,
                target=target,
                post_state=post_state,
                outcome_state="reviewed_not_applied",
                reason=str(_stage_status(render, "evaluate") or "rendered"),
                evidence_paths=[manifest_rel, render_rel],
                metrics=render.get("visual_deltas")
                if isinstance(render.get("visual_deltas"), dict)
                else {},
            )
        )

    apply_path = sandbox / "apply_result.json"
    if apply_path.is_file():
        apply_result = _load_json(apply_path, "apply_result")
        if apply_result.get("figure_name") is not None and apply_result.get("figure_name") != name:
            raise QualityMemoryEventError("fixture_mismatch")
        if apply_result.get("fixture") is not None and apply_result.get("fixture") != name:
            raise QualityMemoryEventError("fixture_mismatch")
        if (
            apply_result.get("candidate_id") is not None
            and apply_result.get("candidate_id") != candidate_id
        ):
            raise QualityMemoryEventError("candidate_id_mismatch")
        diagnostics: list[str] = []
        apply_status = evidence_index._apply_status(  # type: ignore[attr-defined]
            example_dir=example_dir,
            apply_result=apply_result,
            diagnostics=diagnostics,
        )
        post_state = evidence_index._post_apply_summary(apply_result)  # type: ignore[attr-defined]
        pipeline_ok = _post_apply_pipeline_ok(apply_status, post_state)
        post_apply = apply_result.get("post_apply")
        quality_movement = _quality_movement_from_apply(
            apply_status,
            post_apply if isinstance(post_apply, dict) else {},
            pipeline_ok=pipeline_ok,
        )
        outcome_state = quality_movement or "blocked_by_hard_gate"
        reason = (
            "post_apply_success"
            if pipeline_ok
            else ",".join(diagnostics) or str(apply_status)
        )
        events.append(
            _event(
                fixture=name,
                event_type="candidate_applied",
                source_artifact=_fixture_relative(example_dir, apply_path),
                source_payload=apply_result,
                source_path=apply_path,
                candidate_id=candidate_id,
                edit_family=family,
                target=target,
                post_state=post_state,
                outcome_state=outcome_state,
                pipeline_ok=pipeline_ok,
                quality_movement=quality_movement,
                reason=reason,
                evidence_paths=[manifest_rel, _fixture_relative(example_dir, apply_path)],
            )
        )
    return events


def _closeout_events(name: str, example_dir: Path) -> list[dict[str, Any]]:
    closeout_dir = example_dir / "build" / "closeout"
    if closeout_dir.is_symlink():
        raise QualityMemoryEventError("sandbox_symlink_forbidden: closeout")
    acceptance_path = closeout_dir / "golden_acceptance.json"
    if not acceptance_path.is_file():
        return []
    payload = _load_json(acceptance_path, "golden_acceptance")
    accepted = payload.get("decision") == "accept" or payload.get("accept_golden") is True
    return [
        _event(
            fixture=name,
            event_type="closeout_ready",
            source_artifact=_fixture_relative(example_dir, acceptance_path),
            source_payload=payload,
            source_path=acceptance_path,
            outcome_state="improved" if accepted else "blocked_by_human_gate",
            reason="golden_acceptance" if accepted else "golden_not_accepted",
        )
    ]


def build_memory_log(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        raise QualityMemoryEventError(f"examples/{name}/ not found")
    events: list[dict[str, Any]] = []
    for sandbox in _candidate_sandboxes(example_dir):
        events.extend(_candidate_events(name, example_dir, sandbox))
    events.extend(_closeout_events(name, example_dir))
    events.sort(key=lambda event: (str(event["created_at"]), str(event["event_id"])))
    return {
        "schema": LOG_SCHEMA,
        "fixture": name,
        "generated_at": _utc_now(),
        "event_count": len(events),
        "events": events,
    }


def main(
    argv: list[str] | None = None,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="quality_memory_events.py")
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = build_memory_log(
        args.name,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
