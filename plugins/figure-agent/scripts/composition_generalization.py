from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import candidate_contracts
import composition_scene
import fixture_identity
import runtime_paths

SCHEMA: Final = "figure-agent.composition-generalization-report.v1"
FAMILY_TARGETS: Final = ("carrier_walk", "current_sparkline", "n_breadth")


def _composition_model_object_count(scene: dict[str, Any]) -> int:
    objects = scene.get("objects")
    if isinstance(objects, dict):
        return len(objects)
    return 0


def _missing_prerequisites(scene: dict[str, Any]) -> list[str]:
    objects = scene.get("objects")
    object_ids = set(objects) if isinstance(objects, dict) else set()
    missing = []
    if not object_ids:
        missing.extend(["semantic_blocks", "composition_model.objects"])
    for target in FAMILY_TARGETS:
        if target not in object_ids:
            missing.append(f"family_target:{target}")
    return missing


def _recommended_next_action(missing: list[str]) -> str:
    if not missing:
        return "run compose-generate-families"
    if "semantic_blocks" in missing or "composition_model.objects" in missing:
        return "add semantic composition annotations"
    return "map fixture objects to supported structural families"


def write_generalization_report(
    name: str,
    *,
    output_path: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    output = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        output_path,
    )
    scene = composition_scene.build_semantic_scene_model(
        name,
        workspace_root=paths.workspace_root,
    )
    missing = _missing_prerequisites(scene)
    payload = {
        "schema": SCHEMA,
        "fixture": name,
        "status": "ready_for_composition_search" if not missing else "missing_prerequisites",
        "can_generate_structural_families": not missing,
        "source_mutation_allowed": False,
        "tex_execution_allowed": False,
        "model_calls_allowed": False,
        "semantic_block_count": _composition_model_object_count(scene),
        "supported_family_targets": list(FAMILY_TARGETS),
        "missing_prerequisites": missing,
        "scene_model": {
            "status": scene.get("status"),
            "diagnostics": scene.get("diagnostics", []),
        },
        "recommended_next_action": _recommended_next_action(missing),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
