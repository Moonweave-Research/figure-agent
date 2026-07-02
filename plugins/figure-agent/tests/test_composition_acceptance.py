from __future__ import annotations

import importlib
import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

pytestmark = pytest.mark.quarantine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _future_api(module_name: str, attribute: str):
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _fixture(tmp_path: Path, name: str = "fig3_resistance_mechanism") -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    sandbox.mkdir(parents=True)
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, source


def test_acceptance_binds_candidate_source_render_evaluation_hashes_and_permissions(
    tmp_path: Path,
) -> None:
    workspace, source = _fixture(tmp_path)
    fixture = workspace / "examples" / "fig3_resistance_mechanism"
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    candidate_manifest = sandbox / "candidate_manifest.json"
    render_manifest = sandbox / "render_manifest.json"
    evaluation_manifest = sandbox / "evaluation.json"
    candidate_manifest.write_text(
        json.dumps({"candidate": "manifest"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    render_manifest.write_text(
        json.dumps({"render": "manifest"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    evaluation_manifest.write_text(
        json.dumps({"evaluation": "manifest"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    acceptance = {
        "schema": "figure-agent.composition-acceptance.v1",
        "fixture": "fig3_resistance_mechanism",
        "candidate_id": "CCAND001",
        "decision": "accept",
        "accepted_hashes": {
            "candidate_manifest": _sha256_text(candidate_manifest.read_text(encoding="utf-8")),
            "candidate_source": _sha256_text(source.read_text(encoding="utf-8")),
            "base_source": _sha256_text(source.read_text(encoding="utf-8")),
            "operation_set": _sha256_text("operation-set\n"),
            "scene_model": _sha256_text("scene\n"),
            "invariant_set": _sha256_text("invariants\n"),
            "lint_config": _sha256_text("lint\n"),
            "render": _sha256_text(render_manifest.read_text(encoding="utf-8")),
            "evaluation": _sha256_text(evaluation_manifest.read_text(encoding="utf-8")),
        },
        "permissions_granted": ["apply_to_fixture_source", "accept_freeform_structural"],
        "rollback_patch": "build/candidates/CCAND001/rollback.patch",
    }

    validate_acceptance = _future_api("composition_contracts", "validate_composition_acceptance")
    result = validate_acceptance(acceptance, workspace_root=workspace)

    assert result["status"] == "accepted"
    assert (
        result["accepted_hashes"]["candidate_source"]
        == acceptance["accepted_hashes"]["candidate_source"]
    )
    assert result["accepted_hashes"]["render"] == acceptance["accepted_hashes"]["render"]
    assert result["permissions_granted"] == [
        "apply_to_fixture_source",
        "accept_freeform_structural",
    ]


def test_human_commentary_cannot_rank_or_block(tmp_path: Path) -> None:
    workspace, source = _fixture(tmp_path)
    candidate_set = {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": "fig3_resistance_mechanism",
        "authority": "creative_review_only",
        "base": {
            "tex_hash": _sha256_text(source.read_text(encoding="utf-8")),
            "render_hash": _sha256_text("render\n"),
            "scene_model_hash": _sha256_text("scene\n"),
            "composition_lint_hash": _sha256_text("lint\n"),
            "freshness_vector_hash": _sha256_text("freshness\n"),
        },
        "candidates": [{"id": "CCAND001", "status": "proposed_unranked"}],
    }
    lint_packet = {
        "schema": "figure-agent.composition-lint.v1",
        "findings": [
            {
                "check_id": "CL999",
                "status": "human_commentary",
                "message": "the figure feels a little awkward",
            }
        ],
    }

    rank = _future_api("composition_contracts", "rank_composition_candidates")
    ranked = rank(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        lint_packet=lint_packet,
        workspace_root=workspace,
    )

    assert ranked["status"] == "ranked"
    assert ranked["blockers"] == []
    assert ranked["diagnostics"] == []
