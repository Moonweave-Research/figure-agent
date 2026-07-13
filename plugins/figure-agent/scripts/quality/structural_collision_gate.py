#!/usr/bin/env python3
"""Aggregate collision reports without mistaking one clean lane for success."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

BLOCKING_VISUAL_KINDS = frozenset({"clipping", "text_on_fill", "text_on_path"})
BLOCKING_GEOMETRY_KINDS = frozenset({"label_crosses_semantic_path"})


def summarize_reports(
    *,
    collisions: dict[str, Any],
    visual_clash: dict[str, Any],
    undeclared_geometry: dict[str, Any],
    declared_coverage: dict[str, bool],
) -> dict[str, Any]:
    """Return one fail-closed structural status across independent detectors."""
    text_text = len(collisions.get("collisions") or [])
    visual_candidates = visual_clash.get("candidates") or []
    text_on_path_or_fill = sum(
        1
        for item in visual_candidates
        if isinstance(item, dict) and item.get("kind") in BLOCKING_VISUAL_KINDS
    )
    geometry_candidates = undeclared_geometry.get("candidates") or []
    semantic_path_crossing = sum(
        1
        for item in geometry_candidates
        if isinstance(item, dict) and item.get("kind") in BLOCKING_GEOMETRY_KINDS
    )
    blocking_counts = {
        "text_text": text_text,
        "text_on_path_or_fill": text_on_path_or_fill,
        "semantic_path_crossing": semantic_path_crossing,
    }
    failed = any(blocking_counts.values())
    review_counts = {
        "visual_near_miss": sum(
            1
            for item in visual_candidates
            if isinstance(item, dict) and item.get("kind") == "near_miss"
        )
    }
    coverage_gaps = sorted(key for key, covered in declared_coverage.items() if not covered)
    if failed:
        state = "failed"
    elif coverage_gaps or any(review_counts.values()):
        state = "review_required"
    else:
        state = "eligible_for_human_review"
    return {
        "schema": "figure-agent.structural-collision-gate.v1",
        "state": state,
        "structural_pass": state == "eligible_for_human_review",
        "blocking_counts": blocking_counts,
        "review_counts": review_counts,
        "declared_coverage": declared_coverage,
        "coverage_gaps": coverage_gaps,
        "publication_acceptance": "not_claimed",
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _artifact(path: Path) -> dict[str, str]:
    return {
        "path": path.as_posix(),
        "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _declared_coverage(spec_path: Path | None) -> dict[str, bool]:
    if spec_path is None or not spec_path.is_file():
        return {"label_path": False, "panel_boundary": False}
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{spec_path}: expected a YAML mapping")
    return {
        "label_path": bool(payload.get("label_path_proximity_checks")),
        "panel_boundary": bool(payload.get("text_boundary_checks")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collisions", type=Path, required=True)
    parser.add_argument("--visual-clash", type=Path, required=True)
    parser.add_argument("--undeclared-geometry", type=Path, required=True)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = summarize_reports(
            collisions=_load_json(args.collisions),
            visual_clash=_load_json(args.visual_clash),
            undeclared_geometry=_load_json(args.undeclared_geometry),
            declared_coverage=_declared_coverage(args.spec),
        )
        summary["source_reports"] = {
            "collisions": _artifact(args.collisions),
            "visual_clash": _artifact(args.visual_clash),
            "undeclared_geometry": _artifact(args.undeclared_geometry),
        }
    except (OSError, json.JSONDecodeError, yaml.YAMLError, ValueError) as exc:
        print(f"structural_collision_gate.py: {exc}", file=sys.stderr)
        return 2
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"{summary['state']}: text_text={summary['blocking_counts']['text_text']} "
        "text_on_path_or_fill="
        f"{summary['blocking_counts']['text_on_path_or_fill']} "
        "semantic_path_crossing="
        f"{summary['blocking_counts']['semantic_path_crossing']}"
    )
    return 1 if summary["state"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
