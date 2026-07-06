from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA: Final = "figure-agent.post-apply-visual-receipt.v1"
EXPORT_EXTENSIONS: Final = ("pdf", "png", "svg", "tif")
DETECTOR_REPORTS: Final = (
    "visual_clash",
    "text_boundary_clash",
    "label_path_proximity",
)


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _relative(fixture: Path, path: Path) -> str:
    return path.relative_to(fixture).as_posix()


def _artifact(fixture: Path, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": _relative(fixture, path), "exists": False}
    return {
        "path": _relative(fixture, path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": _hash_file(path),
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("expected JSON object")
    return payload


def _changed_source_path(fixture: Path, name: str, apply_result: dict[str, Any]) -> Path:
    changed_files = apply_result.get("changed_files")
    if isinstance(changed_files, list) and changed_files:
        first = changed_files[0]
        if isinstance(first, dict) and isinstance(first.get("path"), str):
            return candidate_contracts.fixture_relative_path(fixture, first["path"])
    return fixture / f"{name}.tex"


def _artifact_group_status(artifacts: list[dict[str, Any]]) -> str:
    if all(artifact.get("exists") for artifact in artifacts):
        return "present"
    if any(artifact.get("exists") for artifact in artifacts):
        return "partial"
    return "missing"


def _render_summary(fixture: Path, name: str) -> dict[str, Any]:
    artifacts = [
        _artifact(fixture, fixture / "build" / f"{name}.pdf"),
        _artifact(fixture, fixture / "build" / f"{name}.png"),
    ]
    return {"status": _artifact_group_status(artifacts), "artifacts": artifacts}


def _export_summary(fixture: Path, name: str) -> dict[str, Any]:
    artifacts = [
        _artifact(fixture, fixture / "exports" / f"{name}.{extension}")
        for extension in EXPORT_EXTENSIONS
    ]
    return {"status": _artifact_group_status(artifacts), "artifacts": artifacts}


def _detector_summary(fixture: Path, report_name: str) -> dict[str, Any]:
    path = fixture / "build" / f"{report_name}.json"
    artifact = _artifact(fixture, path)
    if not path.exists():
        return {"status": "missing", "total": None, "artifact": artifact}
    payload = _load_json(path)
    candidates = payload.get("candidates")
    return {
        "status": "present",
        "total": payload.get("total", 0),
        "candidate_count": len(candidates) if isinstance(candidates, list) else None,
        "artifact": artifact,
    }


def _strict_compile_summary(
    render: dict[str, Any],
    detector_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    # A detector report that could not be read leaves the strict blocker
    # unevaluated: fail closed rather than treat an absent report as "no clash".
    missing_reports = sorted(
        report_name
        for report_name, summary in detector_reports.items()
        if summary.get("status") != "present"
    )
    if missing_reports:
        return {
            "status": "blocked_missing_detector_report",
            "missing_detector_reports": missing_reports,
        }
    visual_total = detector_reports["visual_clash"].get("total")
    if isinstance(visual_total, int) and visual_total > 0:
        return {
            "status": "blocked_by_visual_clash",
            "visual_clash_total": visual_total,
        }
    if render.get("status") != "present":
        return {"status": "render_artifacts_missing"}
    return {"status": "no_known_strict_blocker"}


def _receipt_status(
    render: dict[str, Any],
    export: dict[str, Any],
    strict_compile: dict[str, Any],
) -> str:
    strict_status = strict_compile.get("status")
    if strict_status == "blocked_missing_detector_report":
        return "blocked_missing_detector_report"
    if (
        render.get("status") == "present"
        and export.get("status") == "present"
        and strict_status == "blocked_by_visual_clash"
    ):
        return "rendered_exported_with_strict_visual_warnings"
    if render.get("status") == "present" and export.get("status") == "present":
        return "rendered_exported"
    return "post_apply_artifacts_missing"


def write_post_apply_visual_receipt(
    name: str,
    *,
    candidate_id: str,
    apply_result_path: str,
    output_path: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    current_id = candidate_id.strip()
    if not current_id:
        raise ValueError("candidate id is required")

    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    fixture = paths.workspace_root / "examples" / name
    apply_path = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        apply_result_path,
    )
    output = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        output_path,
    )
    apply_result = _load_json(apply_path)
    if apply_result.get("candidate_id") != current_id or apply_result.get("fixture") != name:
        raise ValueError("apply result identity mismatch")
    if apply_result.get("status") != "applied_unverified":
        raise ValueError("apply result is not applied_unverified")

    source = _changed_source_path(fixture, name, apply_result)
    candidate_source_copy = (
        fixture / "build" / "candidates" / current_id / "source" / "candidate.tex"
    )
    source_artifact = _artifact(fixture, source)
    copy_artifact = _artifact(fixture, candidate_source_copy)
    source_matches_candidate_copy = (
        source_artifact.get("exists") is True
        and copy_artifact.get("exists") is True
        and source_artifact.get("sha256") == copy_artifact.get("sha256")
    )

    render = _render_summary(fixture, name)
    export = _export_summary(fixture, name)
    detector_reports = {
        report_name: _detector_summary(fixture, report_name) for report_name in DETECTOR_REPORTS
    }
    strict_compile = _strict_compile_summary(render, detector_reports)
    required_next_actions = []
    if strict_compile.get("status") == "blocked_by_visual_clash":
        required_next_actions.append("review visual_clash candidates before closeout")
    required_next_actions.append("refresh critique after source apply")

    payload = {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": current_id,
        "status": _receipt_status(render, export, strict_compile),
        "source_matches_candidate_copy": source_matches_candidate_copy,
        "apply_result": _artifact(fixture, apply_path),
        "applied_source": source_artifact,
        "candidate_source_copy": copy_artifact,
        "rollback_patch": _artifact(
            fixture,
            fixture / str(apply_result.get("rollback_patch") or ""),
        ),
        "render": render,
        "export": export,
        "strict_compile": strict_compile,
        "detector_reports": detector_reports,
        "required_next_actions": required_next_actions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
