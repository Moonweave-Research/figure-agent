"""Build a read-only fixture intent model for candidate search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.intent-model.v1"


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


def build_intent_model(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    spec_path = example_dir / "spec.yaml"
    spec = _load_spec(spec_path)
    panels_raw = spec.get("panels")
    panels = panels_raw if isinstance(panels_raw, list) else []

    panel_reference_state = "missing_optional"
    panel_reference_reasons: list[str] = []
    output_panels: list[dict[str, Any]] = []
    for index, raw_panel in enumerate(panels):
        panel = raw_panel if isinstance(raw_panel, dict) else {}
        reference_path, reference_reasons = _fixture_relative_path(
            example_dir,
            panel.get("reference_image"),
        )
        if reference_reasons:
            panel_reference_reasons.extend(reference_reasons)
            if "path_escape" in reference_reasons:
                panel_reference_state = "blocked"
        else:
            panel_reference_state = "present"
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
            "panel_references": {
                "state": panel_reference_state,
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
    print(json.dumps(build_intent_model(args.name), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
