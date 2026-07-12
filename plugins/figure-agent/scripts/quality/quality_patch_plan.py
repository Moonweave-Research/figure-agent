"""Build deterministic patch plans from quality defect ledgers."""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import bounded_coordinate_offset
import fixture_identity
import yaml

SCHEMA = "figure-agent.quality-patch-plan.v1"
FORBIDDEN_TARGET_NAMES = {"critique.md", "QUALITY_AUDIT.md"}
FORBIDDEN_TARGET_PARTS = {"build", "exports"}


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def _is_allowed_target(path_text: str, fixture: str) -> bool:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        return False
    if len(path.parts) < 3 or path.parts[0] != "examples" or path.parts[1] != fixture:
        return False
    if path.name in FORBIDDEN_TARGET_NAMES:
        return False
    if any(part in FORBIDDEN_TARGET_PARTS for part in path.parts):
        return False
    if path.name.startswith("accepted") or path.name.startswith("publication"):
        return False
    return path == Path("examples") / fixture / f"{fixture}.tex"


def _resolve_line(selector: dict[str, Any], lines: list[str]) -> int | None:
    kind = selector.get("kind")
    value = selector.get("value")
    if kind == "line_range" and isinstance(value, str) and ":" in value:
        start = value.split(":", 1)[0].strip()
        if start.isdigit() and int(start) >= 1:
            return int(start)
        return None
    if kind == "node_name" and isinstance(value, str) and value:
        needle = f"({value})"
        for index, line in enumerate(lines):
            if needle in line and bounded_coordinate_offset.offset_first_coordinate(line):
                return index + 1
    return None


def _selector_line(selector: dict[str, Any]) -> int | None:
    return _resolve_line(selector, [])


def _patch_from_selector(
    workspace_root: Path,
    source_file: str,
    selector: dict[str, Any],
) -> str:
    source_path = workspace_root / source_file
    try:
        text = source_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    lines = text.splitlines()
    line_number = _resolve_line(selector, lines)
    if line_number is None or line_number > len(lines):
        return ""
    old = lines[line_number - 1]
    new = bounded_coordinate_offset.offset_first_coordinate(old)
    if new is None:
        return ""
    header = f"@@ -{line_number} +{line_number} @@"
    return f"--- {source_file}\n+++ {source_file}\n{header}\n-{old}\n+{new}\n"


def _alignment_requires_manual_patch(defect: dict[str, Any]) -> bool:
    if defect.get("source_detector") != "semantic_assertions":
        return False
    evidence = defect.get("evidence")
    if not isinstance(evidence, list):
        return False
    alignment_kinds = {
        "baseline_aligned",
        "top_aligned",
        "left_aligned",
        "right_aligned",
        "center_aligned_x",
        "center_aligned_y",
    }
    for item in evidence:
        if not isinstance(item, dict):
            continue
        if item.get("kind") in alignment_kinds:
            return not (
                isinstance(item.get("patch_axis"), str)
                and not isinstance(item.get("patch_delta_cm"), bool)
                and isinstance(item.get("patch_delta_cm"), (int, float))
            )
    return False


def _operation_from_defect(
    defect: dict[str, Any],
    fixture: str,
    *,
    workspace_root: Path,
) -> dict[str, Any] | None:
    affected = defect.get("affected_files")
    if not isinstance(affected, list) or not affected or not isinstance(affected[0], str):
        return None
    source_file = affected[0]
    if not _is_allowed_target(source_file, fixture):
        return None
    suggested = defect.get("suggested_change")
    if not isinstance(suggested, dict):
        suggested = {}
    selector = defect.get("selector_hint")
    if not isinstance(selector, dict) or selector.get("kind") != "semantic_anchor":
        return None
    required_selector_fields = (
        "selector_id",
        "anchor_start",
        "anchor_end",
        "source_hash",
    )
    protected_invariants = defect.get("protected_invariants")
    if (
        any(not selector.get(field) for field in required_selector_fields)
        or not isinstance(protected_invariants, list)
        or not protected_invariants
    ):
        return None
    patch = suggested.get("patch") or ""
    manual_reason: str | None = None
    if not patch:
        if _alignment_requires_manual_patch(defect):
            manual_reason = "axis/direction evidence is required for semantic alignment patches"
            patch = ""
    if patch:
        proposed_change = {
            "summary": suggested.get("summary") or f"Address {defect['id']}",
            "patch": patch,
        }
    else:
        proposed_change = {
            "summary": (
                manual_reason
                or suggested.get("summary")
                or f"Manual edit required at {location} to address {defect['id']}"
            ),
            "patch": "",
            "manual_only": True,
        }
    return {
        "id": "OP001",
        "defect_id": defect["id"],
        "file": source_file,
        "operation_type": suggested.get("operation_type") or "tikz_coordinate_adjust",
        "repair_family": defect.get("repair_family"),
        "selector": {field: selector[field] for field in ("kind", *required_selector_fields)},
        "proposed_change": proposed_change,
        "bounds": {"max_translate_px": 10, "allowed_style_names": []},
        "protected_invariants": list(protected_invariants),
        "change_budget": {
            "max_source_blocks": 1,
            "max_changed_lines": 6,
            "max_rendered_pixel_ratio": 0.03,
        },
        "semantic_guard": {
            "allowed": False,
            "state": "pending_post_render_verification",
        },
    }


def build_quality_patch_plan(
    name: str,
    ledger: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    defects = ledger.get("defects")
    if not isinstance(defects, list):
        defects = []
    operations: list[dict[str, Any]] = []
    refusals: list[dict[str, str]] = []

    for defect in defects:
        if not isinstance(defect, dict):
            continue
        selector = defect.get("selector_hint")
        if not isinstance(selector, dict) or selector.get("kind") != "semantic_anchor":
            refusals.append(
                {
                    "defect_id": str(defect.get("id")),
                    "code": "exact_selector_required",
                }
            )
            continue
        if (defect.get("patchability") or {}).get("state") != "safe_candidate":
            refusals.append({"defect_id": str(defect.get("id")), "code": "unsupported_defect"})
            continue
        operation = _operation_from_defect(defect, name, workspace_root=workspace_root)
        if operation is None:
            refusals.append({"defect_id": str(defect.get("id")), "code": "plan_target_forbidden"})
            continue
        operations.append(operation)
        break

    created_from = {
        "defect_ledger_hash": ledger.get("ledger_hash") or _canonical_hash(ledger),
        "audit_evidence_graph_hash": _first_graph_hash(defects),
        "source_hashes": _source_hashes(defects),
    }
    verification = {
        "required_commands": [
            f"fig-agent compile {name} --strict",
            f"fig-agent status {name} --json",
        ],
        "success_metrics": [{"resolved_defect_ids": [op["defect_id"] for op in operations]}],
    }
    base = {
        "schema": SCHEMA,
        "fixture": name,
        "created_from": created_from,
        "operations": operations,
        "verification": verification,
        "rollback": {"strategy": "reverse_patch"},
        "refusals": refusals,
    }
    base["plan_id"] = _canonical_hash(
        {
            "fixture": name,
            "operations": operations,
            "source_hashes": created_from["source_hashes"],
            "policy_version": "figure-agent.quality-patch-policy.v1",
            "verification": verification,
        }
    )
    return base


def _first_graph_hash(defects: list[Any]) -> str:
    for defect in defects:
        if isinstance(defect, dict):
            value = (defect.get("freshness") or {}).get("audit_evidence_graph_hash")
            if isinstance(value, str):
                return value
    return "sha256:" + "0" * 64


def _source_hashes(defects: list[Any]) -> dict[str, str]:
    for defect in defects:
        if isinstance(defect, dict):
            value = (defect.get("freshness") or {}).get("source_hashes")
            if isinstance(value, dict):
                return {str(key): str(item) for key, item in sorted(value.items())}
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default=None)
    args = parser.parse_args(argv)
    data = yaml.safe_load(args.ledger.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        parser.error("ledger must be a mapping")
    plan = build_quality_patch_plan(args.name, data, workspace_root=args.workspace_root)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
