"""Build a read-only panel model for candidate search."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import candidate_tex_index
import figure_intent_model
import fixture_identity

SCHEMA = "figure-agent.candidate-panel-model.v1"
PANEL_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class CandidatePanelModelError(ValueError):
    """Raised when panel analysis cannot safely resolve inputs."""


def _validate_panel_id(panel_id: str) -> str:
    if not PANEL_ID_RE.match(panel_id):
        raise CandidatePanelModelError("invalid_panel_id")
    return panel_id


def _declared_panel(intent: dict[str, Any], panel_id: str) -> dict[str, Any] | None:
    panels = intent.get("panels")
    if not isinstance(panels, list):
        return None
    for panel in panels:
        if isinstance(panel, dict) and panel.get("id") == panel_id:
            return panel
    return None


def _panel_payload(panel: dict[str, Any] | None, panel_id: str) -> dict[str, Any]:
    if panel is None:
        return {
            "id": panel_id,
            "role": "unknown",
            "bbox_pdf_cm": [],
            "reference_image": "",
            "apply_authority_floor": "review_only",
        }
    payload = {
        "id": panel_id,
        "role": str(panel.get("role") or "unknown"),
        "bbox_pdf_cm": (
            panel.get("bbox_pdf_cm")
            if isinstance(panel.get("bbox_pdf_cm"), list)
            else []
        ),
        "reference_image": str(panel.get("reference_image") or ""),
        "apply_authority_floor": str(panel.get("apply_authority_floor") or "review_only"),
    }
    if payload["bbox_pdf_cm"]:
        payload["coordinate_system"] = "pdf_cm_bottom_left"
    return payload


def build_panel_model(
    name: str,
    panel_id: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    panel_id = _validate_panel_id(panel_id)
    intent = figure_intent_model.build_intent_model(
        name,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    tex_index = candidate_tex_index.build_tex_index(
        name,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    panel = _declared_panel(intent, panel_id)
    selectors = [
        item
        for item in tex_index.get("selectors", [])
        if isinstance(item, dict) and item.get("panel") == panel_id
    ]
    refusals = []
    if panel is None:
        refusals.append({"code": "panel_not_declared"})
    refusals.extend(item for item in tex_index.get("refusals", []) if isinstance(item, dict))
    return {
        "schema": SCHEMA,
        "fixture": name,
        "panel": _panel_payload(panel, panel_id),
        "selector_count": len(selectors),
        "selectors": selectors,
        "visual_review": {
            "status": "missing_render",
            "reason": "panel crop/render helper has not run",
        },
        "inputs": {
            "intent_model_schema": intent.get("schema"),
            "tex_index_schema": tex_index.get("schema"),
            "fixture_dirty": bool(tex_index.get("fixture_dirty")),
            "affected_files_dirty": bool(tex_index.get("affected_files_dirty")),
        },
        "refusals": refusals,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("panel_id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_panel_model(args.name, args.panel_id)
    except (CandidatePanelModelError, ValueError) as exc:
        print(f"candidate_panel_model: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
