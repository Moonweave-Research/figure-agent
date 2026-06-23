from __future__ import annotations

import importlib
import json
import sys
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)
REPLACEMENT_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "smoothed walk\n"
    "% fig-agent:end object=carrier_walk\n"
)


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _future_api(module_name: str, attribute: str):
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _fixture(tmp_path: Path, name: str = "fig3_resistance_mechanism") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    sandbox.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        "name: fig3_resistance_mechanism\npanels:\n  - id: A\n",
        encoding="utf-8",
    )
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, fixture, source


def test_host_authored_proposal_capture_has_no_executable_or_model_payload(tmp_path: Path) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    proposal_path = fixture / "proposal.json"
    proposal_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": "fig3_resistance_mechanism",
                "authority": "creative_review_only",
                "goal": "make the carrier walk read more naturally",
                "candidates": [
                    {
                        "id": "CCAND001",
                        "family": "freeform_structural",
                        "target": {"panel": "A", "object": "carrier_walk"},
                        "proposal_source": "host",
                        "model_payload": None,
                        "executable_payload": None,
                        "operations": [
                            {
                                "schema": "figure-agent.composition-candidate-operation.v1",
                                "kind": "replace_semantic_block",
                                "path": source.relative_to(workspace).as_posix(),
                                "base_source_hash": _sha256_text(
                                    source.read_text(encoding="utf-8")
                                ),
                                "selector": {
                                    "kind": "semantic_block",
                                    "object_id": "carrier_walk",
                                    "start_marker": "% fig-agent:start object=carrier_walk",
                                    "end_marker": "% fig-agent:end object=carrier_walk",
                                    "original_hash": _sha256_text("old walk\n"),
                                },
                                "original_text_hash": _sha256_text("old walk\n"),
                                "replacement_text": REPLACEMENT_TEXT,
                                "replacement_text_hash": _sha256_text(REPLACEMENT_TEXT),
                                "rollback": {
                                    "kind": "restore_original_text",
                                    "original_text": "old walk\n",
                                },
                            }
                        ],
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    capture = _future_api("composition_contracts", "capture_composition_candidates")
    result = capture(
        "fig3_resistance_mechanism",
        proposal_json_path=proposal_path,
        workspace_root=workspace,
    )

    assert result["status"] == "proposed_unranked"
    assert result["authority"] == "creative_review_only"
    assert "model_payload" not in result["candidates"][0]
    assert "executable_payload" not in result["candidates"][0]
    assert result["diagnostics"] == []


def test_plugin_side_goal_or_model_generation_is_rejected(tmp_path: Path) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    proposal_path = fixture / "proposal.json"
    proposal_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": "fig3_resistance_mechanism",
                "authority": "creative_review_only",
                "goal": "let the plugin invent a smoother figure",
                "model_prompt": "generate a composition candidate",
                "candidates": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    capture = _future_api("composition_contracts", "capture_composition_candidates")
    result = capture(
        "fig3_resistance_mechanism",
        proposal_json_path=proposal_path,
        workspace_root=workspace,
    )

    assert result["status"] == "rejected"
    assert result["diagnostics"][0]["code"] == "goal_generation_forbidden"
    assert result["diagnostics"][0]["field"] in {"goal", "model_prompt"}


def test_stale_evidence_can_only_be_proposed_unranked(tmp_path: Path) -> None:
    workspace, fixture, source = _fixture(tmp_path)
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
    freshness_vector = {
        "schema": "figure-agent.freshness-vector.v1",
        "captured": {"tex_hash": candidate_set["base"]["tex_hash"]},
        "current": {"tex_hash": _sha256_text("changed\n")},
        "status": {"source": "stale", "detectors": "stale", "references": "fresh"},
    }

    rank = _future_api("composition_contracts", "rank_composition_candidates")
    ranked = rank(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        freshness_vector=freshness_vector,
        workspace_root=workspace,
    )

    assert ranked["status"] == "proposed_unranked"
    assert ranked["diagnostics"][0]["code"] == "stale_evidence_proposed_unranked"

    apply_candidate = _future_api("composition_contracts", "apply_composition_candidate")
    applied = apply_candidate(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        freshness_vector=freshness_vector,
        workspace_root=workspace,
    )

    assert applied["status"] == "blocked"
    assert applied["diagnostics"][0]["code"] == "refresh_required"


def test_candidate_operation_requires_exact_text_hash_selector_and_rollback(
    tmp_path: Path,
) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    operation = {
        "schema": "figure-agent.composition-candidate-operation.v1",
        "kind": "replace_semantic_block",
        "path": source.relative_to(workspace).as_posix(),
        "base_source_hash": _sha256_text(source.read_text(encoding="utf-8")),
        "selector": {
            "kind": "semantic_block",
            "object_id": "carrier_walk",
            "start_marker": "% fig-agent:start object=carrier_walk",
            "end_marker": "% fig-agent:end object=carrier_walk",
            "original_hash": _sha256_text("old walk\n"),
        },
        "original_text_hash": _sha256_text("old walk\n"),
        "replacement_text": REPLACEMENT_TEXT,
        "replacement_text_hash": _sha256_text(REPLACEMENT_TEXT),
        "rollback": {"kind": "restore_original_text", "original_text": "old walk\n"},
    }

    validate_operation = _future_api("composition_contracts", "validate_candidate_operation")
    result = validate_operation(operation, workspace_root=workspace)

    assert result["status"] == "valid"
    assert result["operation"]["replacement_text"] == operation["replacement_text"]
    assert result["operation"]["base_source_hash"] == operation["base_source_hash"]
    assert result["operation"]["selector"]["kind"] == "semantic_block"
    assert result["operation"]["rollback"]["kind"] == "restore_original_text"


def test_candidate_operation_rejects_raw_line_range_selector_for_composition(
    tmp_path: Path,
) -> None:
    workspace, _example_dir, source = _fixture(tmp_path)
    operation = {
        "schema": "figure-agent.composition-candidate-operation.v1",
        "kind": "replace_semantic_block",
        "path": source.relative_to(workspace).as_posix(),
        "base_source_hash": _sha256_text(source.read_text(encoding="utf-8")),
        "selector": {"kind": "line_range", "start": 1, "end": 3},
        "replacement_text": REPLACEMENT_TEXT,
    }

    validate_operation = _future_api("composition_contracts", "validate_candidate_operation")
    result = validate_operation(operation, workspace_root=workspace)

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "line_range_selector_read_only"
