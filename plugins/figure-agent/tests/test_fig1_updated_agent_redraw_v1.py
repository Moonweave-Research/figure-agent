from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(relative: str) -> dict:
    return yaml.safe_load((FIXTURE / relative).read_text(encoding="utf-8"))


def _historical_bytes(commit: str, source_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{source_path}"],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def test_redraw_pins_unchanged_visual_and_physics_authorities() -> None:
    authority = _yaml("authority.yaml")
    assert authority["schema"] == "figure-agent.reference-authority.v1"
    assert authority["candidate_kind"] == "additive_full_figure_redraw"
    assert authority["historical_inputs_unchanged"] is True
    assert authority["publication_acceptance"] == "not_claimed"

    roles = {item["role"] for item in authority["sources"]}
    assert roles == {
        "visual_and_narrative_baseline",
        "narrative_and_aesthetic_intent",
        "physics_correction_authority",
    }
    for source in authority["sources"]:
        tree = subprocess.run(
            ["git", "rev-parse", f"{source['source_commit']}^{{tree}}"],
            cwd=PLUGIN_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert tree == source["source_tree"]
        historical = _historical_bytes(source["source_commit"], source["source_path"])
        assert hashlib.sha256(historical).hexdigest() == source["sha256"]


def test_redraw_is_independent_and_keeps_floating_panel_f_topology() -> None:
    source = (FIXTURE / "fig1_updated_agent_redraw_v1.tex").read_text(encoding="utf-8")
    assert "fig1_overview_v5f_art_direction_001_vault" not in source
    assert "\\input{" not in source
    assert "\\include{" not in source
    assert "floating cantilever" in source
    assert "grounded\\\\source return" in source
    assert "sample and cantilever remain floating" in source

    result = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert result["summary"]["object_role_count"] == 9
    assert result["summary"]["visible_connector_count"] == 4
    assert result["summary"]["floating_object_count"] == 1
    assert result["summary"]["visual_review_required"] is True
    assert result["publication_acceptance"] == "not_claimed"
