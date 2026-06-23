from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import candidate_contracts
import composition_post_apply_verify
import fixture_identity
import runtime_paths

SCHEMA: Final = "figure-agent.visual-clash-triage.v1"


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


def _kind_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        kind = str(candidate.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def _crop_paths(fixture: Path, clash_id: str) -> list[str]:
    crop_dir = fixture / "build" / "audit_crops" / "visual_clash"
    return [
        _relative(fixture, path)
        for path in sorted(crop_dir.glob(f"{clash_id}_*.png"))
        if path.is_file()
    ]


def _review_items(fixture: Path, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for candidate in candidates:
        clash_id = str(candidate.get("id") or "")
        items.append(
            {
                "id": clash_id,
                "kind": candidate.get("kind"),
                "text": candidate.get("text"),
                "bbox_px": candidate.get("bbox_px"),
                "metric": candidate.get("metric"),
                "crop_paths": _crop_paths(fixture, clash_id),
                "suggested_decision_values": [
                    "true_positive",
                    "false_positive",
                    "accepted_tradeoff",
                ],
                "action": "human_review_required",
            }
        )
    return items


def write_visual_clash_triage(
    name: str,
    *,
    receipt_path: str,
    output_path: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    fixture = paths.workspace_root / "examples" / name
    receipt_file = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        receipt_path,
    )
    output = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        output_path,
    )
    receipt = _load_json(receipt_file)
    if (
        receipt.get("schema") != composition_post_apply_verify.SCHEMA
        or receipt.get("fixture") != name
    ):
        raise ValueError("post-apply receipt identity mismatch")

    report_path = fixture / "build" / "visual_clash.json"
    report = _load_json(report_path)
    raw_candidates = report.get("candidates")
    if not isinstance(raw_candidates, list):
        raise ValueError("visual_clash candidates must be a list")
    candidates = [item for item in raw_candidates if isinstance(item, dict)]
    strict_compile = receipt.get("strict_compile")
    strict_blocked = (
        isinstance(strict_compile, dict)
        and strict_compile.get("status") == "blocked_by_visual_clash"
    )
    total = len(candidates)
    payload = {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": receipt.get("candidate_id"),
        "status": "review_required" if total else "no_visual_clash_candidates",
        "closeout_blocked": bool(strict_blocked and total),
        "total_candidates": total,
        "visual_clash_report": _artifact(fixture, report_path),
        "post_apply_receipt": _artifact(fixture, receipt_file),
        "kind_counts": _kind_counts(candidates),
        "review_items": _review_items(fixture, candidates),
        "required_next_actions": (
            [
                "adjudicate visual_clash review_items",
                "refresh critique after visual clash adjudication",
            ]
            if total
            else ["refresh critique after source apply"]
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
