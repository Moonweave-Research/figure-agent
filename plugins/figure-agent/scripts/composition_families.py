from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import composition_scene
import fixture_identity
import runtime_paths
from composition_family_templates import FAMILY_DATA

SCHEMA: Final = "figure-agent.composition-candidate-set.v1"
OPERATION_SCHEMA: Final = "figure-agent.composition-candidate-operation.v1"


class CompositionFamilyError(ValueError):
    pass


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return _sha256_text(data)


def _source_path(name: str, workspace: Path) -> Path:
    return workspace / "examples" / name / f"{name}.tex"


def _block_text(source_text: str, selector: dict[str, Any]) -> str:
    start = selector.get("start_marker")
    end = selector.get("end_marker")
    if not isinstance(start, str) or not isinstance(end, str):
        raise CompositionFamilyError("selector_marker_missing")
    start_index = source_text.find(start)
    end_index = source_text.find(end, start_index + len(start)) if start_index >= 0 else -1
    if start_index < 0 or end_index < 0:
        raise CompositionFamilyError("selector_not_found")
    body_start = start_index + len(start)
    if body_start < len(source_text) and source_text[body_start] == "\n":
        body_start += 1
    return source_text[body_start:end_index]


def _replacement(selector: dict[str, Any], body: str) -> str:
    start = str(selector["start_marker"])
    end = str(selector["end_marker"])
    clean_body = body.rstrip("\n")
    return f"{start}\n{clean_body}\n{end}"


def _candidate(
    name: str,
    source: Path,
    source_text: str,
    selectors: dict[str, Any],
    variant_data: tuple[Any, ...],
    index: int,
    workspace: Path,
) -> dict[str, Any]:
    (
        family,
        target_object,
        variant,
        improvements,
        invariants,
        regressions,
        check_metric,
        summary,
        body,
    ) = variant_data
    selector = selectors.get(target_object)
    if not isinstance(selector, dict):
        raise CompositionFamilyError(f"selector_missing:{target_object}")
    original_text = _block_text(source_text, selector)
    replacement_text = _replacement(selector, "\n".join(body))
    operation = {
        "schema": OPERATION_SCHEMA,
        "kind": "replace_semantic_block",
        "path": source.relative_to(workspace).as_posix(),
        "base_source_hash": _sha256_text(source_text),
        "selector": selector,
        "original_text_hash": _sha256_text(original_text),
        "replacement_text": replacement_text,
        "replacement_text_hash": _sha256_text(replacement_text),
        "replacement_summary": summary,
        "rollback": {"kind": "restore_original_text", "original_text": original_text},
    }
    operation["operation_hash"] = _sha256_json(operation)
    return {
        "id": f"CFAM{index:03d}",
        "family": family,
        "variant": variant,
        "target": {"fixture": name, "object": target_object},
        "proposal_source": "host_deterministic_template",
        "edit_class": "structural",
        "expected_improvements": list(improvements),
        "protected_invariants": list(invariants),
        "possible_regressions": list(regressions),
        "composition_lint_delta": {
            "deterministic": [
                {
                    "check": check_metric[0],
                    "metric": check_metric[1],
                    "threshold": {"review": 1},
                    "evidence_object": {"object_id": target_object},
                    "delta": "improved",
                }
            ],
            "human_commentary": [],
        },
        "operations": [operation],
        "apply_authority": "human_required",
    }


def generate_structural_family_candidates(
    name: str,
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    scene = composition_scene.build_semantic_scene_model(name, workspace_root=paths.workspace_root)
    if scene.get("status") != "ready":
        return {
            "schema": SCHEMA,
            "fixture": name,
            "status": "blocked",
            "candidates": [],
            "diagnostics": scene.get("diagnostics", []),
        }
    source = _source_path(name, paths.workspace_root)
    source_text = source.read_text(encoding="utf-8")
    selectors = scene.get("source_selectors")
    if not isinstance(selectors, dict):
        raise CompositionFamilyError("source_selectors_missing")
    candidates = [
        _candidate(name, source, source_text, selectors, variant, index, paths.workspace_root)
        for index, variant in enumerate(FAMILY_DATA, start=1)
    ]
    return {
        "schema": SCHEMA,
        "fixture": name,
        "status": "proposed_unranked",
        "authority": "creative_review_only",
        "generation_policy": {
            "mode": "host_deterministic_family_templates",
            "model_calls_allowed": False,
            "tex_execution_allowed": False,
            "source_mutation_allowed": False,
        },
        "base": {"tex_hash": _sha256_text(source_text)},
        "candidates": candidates,
        "diagnostics": [],
    }
