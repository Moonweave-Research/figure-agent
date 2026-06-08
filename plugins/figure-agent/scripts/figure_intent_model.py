"""Build a read-only fixture intent model for candidate search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths
import yaml

SCHEMA = "figure-agent.intent-model.v1"


class IntentModelError(ValueError):
    """Raised when the intent model cannot safely resolve fixture inputs."""


def _state(path: Path, *, required: bool) -> dict[str, Any]:
    if path.is_file():
        return {"state": "present", "path": str(path)}
    return {
        "state": "missing_required" if required else "missing_optional",
        "path": str(path),
    }


def _fixture_relative_path(example_dir: Path, value: Any) -> tuple[str, list[str]]:
    if not isinstance(value, str) or not value.strip():
        return "", ["missing"]
    candidate = (example_dir / value).resolve()
    try:
        candidate.relative_to(example_dir.resolve())
    except ValueError:
        return str(candidate), ["path_escape"]
    if not candidate.is_file():
        return str(candidate), ["missing"]
    return str(candidate), []


def _load_spec(spec_path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _reference_state(reasons: list[str], *, has_present: bool) -> str:
    if "path_escape" in reasons:
        return "blocked"
    if has_present:
        return "present"
    if reasons:
        return "missing_optional"
    return "missing_optional"


def _resolve_paths(
    *,
    plugin_root: Path | None,
    workspace_root: Path | None,
) -> runtime_paths.RuntimePaths:
    plugin = (
        plugin_root
        if plugin_root is not None
        else runtime_paths.default_plugin_root()
    ).expanduser().resolve()
    if workspace_root is not None:
        return runtime_paths.resolve_runtime_paths(
            plugin_root=plugin,
            workspace_root=workspace_root,
        )
    workspace, _source = runtime_paths.workspace_root_with_source(plugin)
    if workspace is None:
        raise IntentModelError(
            "workspace_missing: set FIGURE_AGENT_WORKSPACE or run from a project "
            "root containing examples/"
        )
    return runtime_paths.resolve_runtime_paths(
        plugin_root=plugin,
        workspace_root=workspace,
    )


def build_intent_model(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = _resolve_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    spec_path = example_dir / "spec.yaml"
    spec = _load_spec(spec_path)
    panels_raw = spec.get("panels")
    panels = panels_raw if isinstance(panels_raw, list) else []

    figure_reference_path, figure_reference_reasons = _fixture_relative_path(
        example_dir,
        spec.get("reference_image"),
    )
    panel_reference_reasons: list[str] = []
    panel_reference_present = False
    output_panels: list[dict[str, Any]] = []
    for index, raw_panel in enumerate(panels):
        panel = raw_panel if isinstance(raw_panel, dict) else {}
        panel_reference_value = panel.get("reference_image") or spec.get("reference_image")
        reference_path, reference_reasons = _fixture_relative_path(
            example_dir,
            panel_reference_value,
        )
        if reference_reasons:
            panel_reference_reasons.extend(reference_reasons)
        else:
            panel_reference_present = True
        role = str(panel.get("caption") or panel.get("role") or "unknown")
        output_panels.append(
            {
                "id": str(panel.get("id") or f"panel_{index + 1}"),
                "role": role,
                "bbox_pdf_cm": panel.get("bbox_pdf_cm")
                if isinstance(panel.get("bbox_pdf_cm"), list)
                else [],
                "reference_image": reference_path,
                "semantic_claims": [],
                "visual_priorities": [],
                "locked_invariants": [],
                "allowed_edit_classes": [
                    "label_offset",
                    "whitespace",
                    "style_normalization",
                ],
                "apply_authority_floor": "review_only"
                if reference_reasons
                else "apply_eligible",
            }
        )

    return {
        "schema": SCHEMA,
        "fixture": name,
        "workspace_root": str(paths.workspace_root),
        "inputs": {
            "spec": _state(spec_path, required=True),
            "briefing": _state(example_dir / "briefing.md", required=True),
            "source": _state(example_dir / f"{name}.tex", required=True),
            "caption": _state(example_dir / "caption.md", required=False),
            "figure_reference": {
                "state": _reference_state(
                    figure_reference_reasons,
                    has_present=not figure_reference_reasons,
                ),
                "path": figure_reference_path,
                "reasons": sorted(set(figure_reference_reasons)),
            },
            "panel_references": {
                "state": _reference_state(
                    panel_reference_reasons,
                    has_present=panel_reference_present,
                ),
                "reasons": sorted(set(panel_reference_reasons)),
            },
            "coordinate_hints": _state(
                example_dir / "coordinate_hints.yaml",
                required=False,
            ),
            "perception_pack": {
                "state": "present"
                if (example_dir / "build" / "perception").is_dir()
                else "missing_optional",
            },
            "semantic_invariants": _state(
                example_dir / "semantic_invariants.yaml",
                required=False,
            ),
        },
        "panels": output_panels,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_intent_model(args.name)
    except (IntentModelError, ValueError) as exc:
        print(f"figure_intent_model: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
