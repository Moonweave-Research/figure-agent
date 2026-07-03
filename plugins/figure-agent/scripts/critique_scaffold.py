"""Build a fillable critique scaffold without making visual judgments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths
import status
from inputs import parse_spec
from quality.quality_manifest import compute_critique_input_hash, file_sha256

SCHEMA = "figure-agent.critique-scaffold.v1"
OUTPUT_RELATIVE_PATH = Path("build/critique_scaffold.md")


class CritiqueScaffoldError(ValueError):
    """Raised when a critique scaffold cannot be built safely."""


def _validate_fixture_name(name: str) -> str:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise CritiqueScaffoldError(str(exc)) from exc
    return name


def _example_dir(workspace_root: Path, name: str) -> Path:
    fixture = workspace_root / "examples" / _validate_fixture_name(name)
    examples = workspace_root / "examples"
    if fixture.is_symlink():
        raise CritiqueScaffoldError(f"fixture_symlink_forbidden: {name}")
    try:
        fixture.resolve().relative_to(examples.resolve())
    except ValueError as exc:
        raise CritiqueScaffoldError("fixture path_escape") from exc
    return fixture


def _relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path, *, label: str) -> dict[str, Any] | None:
    if path.is_symlink():
        raise CritiqueScaffoldError(f"{label}_symlink_forbidden")
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CritiqueScaffoldError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise CritiqueScaffoldError(f"{label}_invalid")
    return payload


def _artifact(path: Path, example_dir: Path, *, kind: str) -> dict[str, Any]:
    exists = path.is_file()
    payload: dict[str, Any] = {
        "kind": kind,
        "path": _relative(example_dir, path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }
    if exists:
        payload["sha256"] = file_sha256(path)
    return payload


def _required_crop_ids(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return []
    raw_ids = manifest.get("required_crop_ids")
    if not isinstance(raw_ids, list):
        return []
    return [item for item in raw_ids if isinstance(item, str) and item.strip()]


def _crop_path_by_id(manifest: dict[str, Any] | None) -> dict[str, str]:
    if manifest is None:
        return {}
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return {}
    paths: dict[str, str] = {}
    for crop in crops:
        if not isinstance(crop, dict):
            continue
        crop_id = crop.get("id")
        path = crop.get("path")
        if isinstance(crop_id, str) and isinstance(path, str):
            paths[crop_id] = path
    return paths


def _scaffold_markdown(payload: dict[str, Any]) -> str:
    crop_ids = payload["crop_audit"]["required_crop_ids"]
    crop_paths = payload["crop_audit"]["crop_paths"]
    lines = [
        "# Critique Scaffold",
        "",
        f"Fixture: `{payload['fixture']}`",
        f"Critique input hash: `{payload['critique_input_hash']}`",
        "",
        "This scaffold is evidence only. It does not assert that the figure has no defects.",
        "",
        "## Required Human Decisions",
        "",
        "- Overall verdict: TODO",
        "- Actionable findings: TODO",
        "- Crop audit verdicts: TODO",
        "",
        "## Crop Audit Log Template",
        "",
    ]
    if not crop_ids:
        lines.append("(No audit-crop manifest was found.)")
    for crop_id in crop_ids:
        lines.extend(
            [
                f"- crop_id: {crop_id}",
                f"  path: {crop_paths.get(crop_id, 'TODO')}",
                "  verdict: TODO",
                "  linked_micro_defect_id: TODO",
            ]
        )
    lines.extend(
        [
            "",
            "## Micro Defects Template",
            "",
            "- id: TODO",
            "  kind: TODO",
            "  severity: TODO",
            "  evidence: TODO",
            "",
        ]
    )
    return "\n".join(lines)


def build_critique_scaffold(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = _example_dir(paths.workspace_root, name)
    if not example_dir.is_dir():
        raise CritiqueScaffoldError(f"fixture_missing: {name}")

    status_payload = status.infer_stage(example_dir)
    if status_payload.get("render_state") != "FRESH":
        raise CritiqueScaffoldError("fresh_render_required")

    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        raise CritiqueScaffoldError("spec_missing")
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise CritiqueScaffoldError("spec_invalid") from exc

    build_dir = example_dir / "build"
    png_path = build_dir / f"{name}.png"
    pdf_path = build_dir / f"{name}.pdf"
    if not png_path.is_file():
        raise CritiqueScaffoldError("build_png_missing")

    crop_manifest_path = build_dir / "audit_crops" / "manifest.json"
    crop_manifest = _load_json(crop_manifest_path, label="audit_crop_manifest")
    required_crop_ids = _required_crop_ids(crop_manifest)
    critique_input_hash = compute_critique_input_hash(
        example_dir,
        name,
        spec,
        style_lock_path=status.STYLE_LOCK_PATH,
    )
    artifacts = [
        _artifact(spec_path, example_dir, kind="spec"),
        _artifact(example_dir / "briefing.md", example_dir, kind="briefing"),
        _artifact(example_dir / f"{name}.tex", example_dir, kind="tex"),
        _artifact(png_path, example_dir, kind="build_png"),
        _artifact(pdf_path, example_dir, kind="build_pdf"),
        _artifact(crop_manifest_path, example_dir, kind="audit_crop_manifest"),
    ]
    output_path = example_dir / OUTPUT_RELATIVE_PATH
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "fixture": name,
        "state": "ready",
        "critique_input_hash": critique_input_hash,
        "status": {
            "stage": status_payload.get("stage"),
            "render_state": status_payload.get("render_state"),
            "critique_state": status_payload.get("critique_state"),
            "exports_substate": status_payload.get("exports_substate"),
        },
        "artifacts": artifacts,
        "crop_audit": {
            "manifest_present": crop_manifest is not None,
            "required_count": len(required_crop_ids),
            "required_crop_ids": required_crop_ids,
            "crop_paths": _crop_path_by_id(crop_manifest),
            "verdict_policy": "human_required",
        },
        "output_path": _relative(example_dir, output_path),
        "mutation_boundary": "writes_build_scaffold_only_no_critique_or_acceptance_state",
        "forbidden_outputs": ["critique.md", "human_attestation.json", "accepted/golden state"],
    }
    if write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_scaffold_markdown(payload), encoding="utf-8")
    return payload


def main(
    argv: list[str] | None = None,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent critique-scaffold")
    parser.add_argument("fixture")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_critique_scaffold(
            args.fixture,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
            write=not args.no_write,
        )
    except CritiqueScaffoldError as exc:
        print(f"fig-agent critique-scaffold: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
