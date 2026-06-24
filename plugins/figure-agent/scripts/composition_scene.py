from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Final

import fixture_identity
import runtime_paths
import yaml

SEMANTIC_SCENE_MODEL_SCHEMA: Final = "figure-agent.semantic-scene-model.v1"
START_RE: Final = re.compile(r"^\s*%\s*fig-agent:start\s+(?P<meta>.+)$")
END_RE: Final = re.compile(r"^\s*%\s*fig-agent:end\s+object=(?P<object>[A-Za-z0-9_-]+)\s*$")
OBJECT_ID_RE: Final = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class CompositionSceneError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SemanticBlock:
    object_id: str
    panel: str | None
    kind: str | None
    truth_bearing: bool | None
    start_line: int
    end_line: int
    start_marker: str
    end_marker: str
    text: str


def _diagnostic(code: str, message: str) -> dict[str, str]:
    return {"code": code, "stage": "scene_model", "message": message}


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _metadata(raw: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in raw.split():
        key, separator, value = token.partition("=")
        if separator and key and value:
            values[key] = value
    return values


def _truth_value(value: str | None) -> bool | None:
    if value == "true":
        return True
    if value == "false":
        return False
    return None


def _selector(block: SemanticBlock) -> dict[str, str | int]:
    return {
        "kind": "semantic_block",
        "object_id": block.object_id,
        "start_marker": block.start_marker,
        "end_marker": block.end_marker,
        "original_hash": _sha256_text(block.text),
        "start_line": block.start_line,
        "end_line": block.end_line,
    }


def _parse_semantic_blocks(source_text: str) -> tuple[list[SemanticBlock], list[dict[str, str]]]:
    blocks: list[SemanticBlock] = []
    diagnostics: list[dict[str, str]] = []
    active: tuple[dict[str, str], int, str] | None = None
    body: list[str] = []
    seen: set[str] = set()
    for line_number, line in enumerate(source_text.splitlines(), start=1):
        start_match = START_RE.match(line)
        end_match = END_RE.match(line)
        if start_match is not None:
            metadata = _metadata(start_match.group("meta"))
            object_id = metadata.get("object", "")
            if active is not None:
                return [], [_diagnostic("semantic_block_nested", "semantic blocks cannot nest")]
            if not OBJECT_ID_RE.fullmatch(object_id):
                return [], [
                    _diagnostic("semantic_block_invalid_object", "invalid semantic object id")
                ]
            if object_id in seen:
                return [], [_diagnostic("semantic_block_duplicate", "duplicate semantic object id")]
            active = (metadata, line_number, line)
            body = []
            continue
        if end_match is not None:
            if active is None:
                return [], [_diagnostic("semantic_block_unmatched_end", "unmatched end marker")]
            metadata, start_line, start_marker = active
            object_id = metadata["object"]
            if end_match.group("object") != object_id:
                return [], [_diagnostic("semantic_block_mismatched_end", "mismatched end marker")]
            seen.add(object_id)
            blocks.append(
                SemanticBlock(
                    object_id=object_id,
                    panel=metadata.get("panel"),
                    kind=metadata.get("kind"),
                    truth_bearing=_truth_value(metadata.get("truth_bearing")),
                    start_line=start_line,
                    end_line=line_number,
                    start_marker=start_marker,
                    end_marker=line,
                    text="\n".join(body) + ("\n" if body else ""),
                )
            )
            active = None
            body = []
            continue
        if active is not None:
            body.append(line)
    if active is not None:
        diagnostics.append(_diagnostic("semantic_block_unclosed", "unclosed semantic block"))
    return blocks, diagnostics


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _load_spec(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _mapping(payload)


def _composition_annotations(spec: dict[str, object]) -> dict[str, dict[str, object]]:
    annotations: dict[str, dict[str, object]] = {}
    composition_model = _mapping(spec.get("composition_model"))
    panels = _mapping(composition_model.get("panels"))
    for panel_id, panel_payload in panels.items():
        objects = _mapping(_mapping(panel_payload).get("objects"))
        for object_id, object_payload in objects.items():
            annotation = _mapping(object_payload)
            annotation["panel"] = panel_id
            annotations[object_id] = annotation
    return annotations


def _panels(
    spec: dict[str, object],
    objects: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    raw_panels = spec.get("panels")
    panel_ids: list[str] = []
    if isinstance(raw_panels, list):
        for item in raw_panels:
            panel_id = _mapping(item).get("id")
            if isinstance(panel_id, str):
                panel_ids.append(panel_id)
    if not panel_ids:
        panel_ids = sorted({str(obj.get("panel")) for obj in objects.values() if obj.get("panel")})
    return [
        {
            "id": panel_id,
            "objects": sorted(
                object_id
                for object_id, obj in objects.items()
                if obj.get("panel") == panel_id
            ),
        }
        for panel_id in panel_ids
    ]


def _object_record(block: SemanticBlock, annotation: dict[str, object]) -> dict[str, object]:
    return {
        "id": block.object_id,
        "panel": annotation.get("panel", block.panel),
        "kind": annotation.get("kind", block.kind or "semantic_object"),
        "truth_bearing": annotation.get("truth_bearing", block.truth_bearing or False),
        "role": annotation.get("role"),
        "anchor_target": annotation.get("anchor_target"),
        "allowed_creative_ops": annotation.get("allowed_creative_ops", []),
        "semantic_claim": annotation.get("semantic_claim"),
        "invariant": annotation.get("invariant"),
    }


def _coverage(record: dict[str, object]) -> dict[str, object]:
    if record.get("truth_bearing") is False:
        return {"status": "not_truth_bearing"}
    if isinstance(record.get("invariant"), str):
        return {"status": "covered", "invariant": record["invariant"]}
    return {"status": "missing_explicit_invariant"}


def build_semantic_scene_model(
    name: str,
    *,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    fixture = paths.examples_dir / name
    spec = _load_spec(fixture / "spec.yaml")
    source_text = (fixture / f"{name}.tex").read_text(encoding="utf-8")
    blocks, diagnostics = _parse_semantic_blocks(source_text)
    if diagnostics:
        return {
            "schema": SEMANTIC_SCENE_MODEL_SCHEMA,
            "fixture": name,
            "status": "blocked",
            "diagnostics": diagnostics,
        }
    annotations = _composition_annotations(spec)
    objects = {
        block.object_id: _object_record(block, annotations.get(block.object_id, {}))
        for block in blocks
    }
    return {
        "schema": SEMANTIC_SCENE_MODEL_SCHEMA,
        "fixture": name,
        "status": "ready",
        "panels": _panels(spec, objects),
        "objects": objects,
        "source_selectors": {block.object_id: _selector(block) for block in blocks},
        "invariant_coverage": {
            object_id: _coverage(record) for object_id, record in objects.items()
        },
        "diagnostics": [],
    }


def semantic_block_selector_from_text(source_text: str, object_id: str) -> dict[str, str | int]:
    blocks, diagnostics = _parse_semantic_blocks(source_text)
    if diagnostics:
        raise CompositionSceneError(diagnostics[0]["code"])
    for block in blocks:
        if block.object_id == object_id:
            return _selector(block)
    raise CompositionSceneError("semantic_block_missing")
