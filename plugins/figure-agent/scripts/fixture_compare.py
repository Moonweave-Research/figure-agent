"""Read-only comparison packets for complete fixture lanes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths
import status
from quality.quality_manifest import file_sha256

SCHEMA = "figure-agent.fixture-compare.v1"
RECOMMENDATION_PRIORITY = {
    "blocked_stale_evidence": 0,
    "needs_human_critique": 1,
    "candidate_tie": 2,
}


class FixtureCompareError(ValueError):
    """Raised when a fixture comparison packet cannot be built safely."""


def _validate_fixture_name(name: str) -> str:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise FixtureCompareError(str(exc)) from exc
    return name


def _example_dir(workspace_root: Path, name: str) -> Path:
    fixture = workspace_root / "examples" / _validate_fixture_name(name)
    examples = workspace_root / "examples"
    if fixture.is_symlink():
        raise FixtureCompareError(f"fixture_symlink_forbidden: {name}")
    try:
        fixture.resolve().relative_to(examples.resolve())
    except ValueError as exc:
        raise FixtureCompareError("fixture path_escape") from exc
    return fixture


def _relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


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


def _artifact_set(example_dir: Path, name: str) -> dict[str, list[dict[str, Any]]]:
    source_files = [
        (example_dir / "spec.yaml", "spec"),
        (example_dir / "briefing.md", "briefing"),
        (example_dir / f"{name}.tex", "tex"),
        (example_dir / "aesthetic_intent.yaml", "aesthetic_intent"),
        (example_dir / "critique.md", "critique"),
    ]
    build_files = [
        (example_dir / "build" / f"{name}.pdf", "build_pdf"),
        (example_dir / "build" / f"{name}.png", "build_png"),
    ]
    export_files = [
        (example_dir / "exports" / f"{name}.pdf", "export_pdf"),
        (example_dir / "exports" / f"{name}.svg", "export_svg"),
        (example_dir / "exports" / f"{name}.png", "export_png"),
        (example_dir / "exports" / f"{name}.tif", "export_tif"),
        (example_dir / "exports" / f"{name}.tiff", "export_tiff"),
    ]
    return {
        "source": [
            _artifact(path, example_dir, kind=kind)
            for path, kind in source_files
            if path.is_file()
        ],
        "build": [_artifact(path, example_dir, kind=kind) for path, kind in build_files],
        "exports": [_artifact(path, example_dir, kind=kind) for path, kind in export_files],
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    if path.is_symlink():
        raise FixtureCompareError(f"json_symlink_forbidden: {_relative(path.parent, path)}")
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureCompareError(f"json_unreadable: {path.name}") from exc
    return payload if isinstance(payload, dict) else None


def _candidate_count(payload: dict[str, Any] | None) -> int | None:
    if payload is None:
        return None
    total = payload.get("total")
    if isinstance(total, int):
        return total
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        return len(candidates)
    return None


def _audit_counts(example_dir: Path) -> dict[str, Any]:
    build = example_dir / "build"
    paths = {
        "visual_clash": build / "visual_clash.json",
        "text_boundary": build / "text_boundary_clash.json",
        "label_path": build / "label_path_proximity.json",
        "undeclared_geometry": build / "undeclared_geometry.json",
    }
    counts: dict[str, Any] = {}
    for key, path in paths.items():
        payload = _load_json(path)
        counts[key] = {
            "present": payload is not None,
            "candidate_count": _candidate_count(payload),
        }
    return counts


def _visual_metrics(example_dir: Path) -> dict[str, Any]:
    payload = _load_json(example_dir / "build" / "visual_quality_metrics.json")
    if payload is not None:
        return {
            "state": payload.get("state", "unknown"),
            "schema": payload.get("schema"),
            "image": payload.get("image", {}),
            "scaffold_load": payload.get("scaffold_load", {}),
            "crop_audit": payload.get("crop_audit", {}),
            "print_scale": payload.get("print_scale", {}),
        }
    payload = _load_json(example_dir / "build" / "reference_aesthetic_metrics.json")
    if payload is None:
        return {"state": "missing"}
    return {
        "state": payload.get("state", "unknown"),
        "build_features": payload.get("build_features", {}),
        "comparison_count": len(payload.get("comparisons", []))
        if isinstance(payload.get("comparisons"), list)
        else 0,
    }


def _fixture_summary(workspace_root: Path, name: str, *, role: str) -> dict[str, Any]:
    example_dir = _example_dir(workspace_root, name)
    status_payload = status.infer_stage(example_dir)
    notes = status_payload.get("notes")
    return {
        "name": name,
        "role": role,
        "exists": example_dir.is_dir(),
        "status": {
            "stage": status_payload.get("stage"),
            "render_state": status_payload.get("render_state"),
            "export_state": status_payload.get("export_state"),
            "exports_substate": status_payload.get("exports_substate"),
            "critique_state": status_payload.get("critique_state"),
            "acceptance_state": status_payload.get("acceptance_state"),
            "accepted": status_payload.get("accepted"),
            "final_ready": status_payload.get("final_ready"),
            "release_ready": status_payload.get("release_ready"),
            "next": status_payload.get("next"),
            "notes": notes if isinstance(notes, list) else [],
        },
        "artifacts": _artifact_set(example_dir, name),
        "audit_counts": _audit_counts(example_dir),
        "visual_metrics": _visual_metrics(example_dir),
    }


def _is_stale_or_incomplete(summary: dict[str, Any]) -> bool:
    state = summary["status"]
    if state.get("stage") not in {3, 4}:
        return True
    if state.get("render_state") != "FRESH":
        return True
    if state.get("stage") == 4 and state.get("exports_substate") != "FRESH":
        return True
    return False


def _needs_human_critique(summary: dict[str, Any]) -> bool:
    return summary["status"].get("critique_state") in {
        "MISSING",
        "STALE",
        "INVALID",
        "LINT_FAILED",
    }


def _recommendation(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    stale = [item["name"] for item in candidates if _is_stale_or_incomplete(item)]
    if stale:
        return {
            "bucket": "blocked_stale_evidence",
            "reason": "At least one candidate lacks fresh render/export evidence.",
            "fixtures": stale,
            "next_agent_action": "refresh_compile_export_status",
        }
    missing_critique = [item["name"] for item in candidates if _needs_human_critique(item)]
    if missing_critique:
        return {
            "bucket": "needs_human_critique",
            "reason": (
                "Fresh human/host critique is required before visual preference "
                "is actionable."
            ),
            "fixtures": missing_critique,
            "next_agent_action": "run_fig_critique",
        }
    return {
        "bucket": "candidate_tie",
        "reason": "No deterministic winner is declared by the available evidence.",
        "fixtures": [item["name"] for item in candidates],
        "next_agent_action": "record_human_visual_choice_or_prepare_bounded_candidate",
    }


def build_fixture_compare_packet(
    fixture_names: list[str],
    *,
    baseline: str | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    if len(fixture_names) < 2:
        raise FixtureCompareError("compare-fixtures requires at least two fixtures")
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    fixtures = [
        _fixture_summary(paths.workspace_root, name, role="candidate")
        for name in fixture_names
    ]
    baseline_summary = (
        _fixture_summary(paths.workspace_root, baseline, role="baseline")
        if baseline is not None
        else None
    )
    packet: dict[str, Any] = {
        "schema": SCHEMA,
        "workspace_root": str(paths.workspace_root),
        "baseline": baseline_summary,
        "fixtures": fixtures,
        "recommendation": _recommendation(fixtures),
        "mutation_boundary": "read_only_no_source_or_state_mutation",
    }
    return packet


def main(
    argv: list[str] | None = None,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compare-fixtures")
    parser.add_argument("fixtures", nargs="+")
    parser.add_argument("--baseline")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_fixture_compare_packet(
            args.fixtures,
            baseline=args.baseline,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
        )
    except FixtureCompareError as exc:
        print(f"fig-agent compare-fixtures: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
