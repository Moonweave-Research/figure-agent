from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import composition_contracts  # noqa: E402

SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path, name: str = "fig3_resistance_mechanism") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        "name: fig3_resistance_mechanism\npanels:\n  - id: A\n",
        encoding="utf-8",
    )
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, fixture, source


def _proposal(fixture: Path, source_hash: str) -> Path:
    path = fixture / "proposal.json"
    path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": "fig3_resistance_mechanism",
                "authority": "creative_review_only",
                "base": {"tex_hash": source_hash},
                "candidates": [
                    {
                        "id": "CCAND001",
                        "family": "freeform_structural",
                        "target": {"panel": "A", "object": "carrier_walk"},
                        "proposal_source": "host",
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_capture_returns_freshness_vector_for_host_proposal(tmp_path: Path) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    source_hash = _sha256_text(source.read_text(encoding="utf-8"))
    proposal_path = _proposal(fixture, source_hash)

    result = composition_contracts.capture_composition_candidates(
        "fig3_resistance_mechanism",
        proposal_json_path=proposal_path,
        workspace_root=workspace,
    )

    assert result["schema"] == "figure-agent.composition-candidate-set.v1"
    assert result["fixture"] == "fig3_resistance_mechanism"
    assert result["status"] == "proposed_unranked"
    assert result["capture_policy"] == {
        "mode": "host_authored",
        "model_calls_allowed": False,
        "executable_payload_allowed": False,
    }
    assert result["base"] == {"tex_hash": source_hash}
    freshness = result["freshness_vector"]
    assert freshness["schema"] == "figure-agent.freshness-vector.v1"
    assert freshness["captured"]["tex_hash"] == source_hash
    assert freshness["current"]["tex_hash"] == source_hash
    assert freshness["status"]["source"] == "fresh"
    assert freshness["status"]["render"] == "unknown"
    assert freshness["stale_fields"] == []
    assert freshness["blocking_for"] == []
    assert result["diagnostics"] == []


def test_capture_allows_stale_source_but_rank_and_apply_block_vector(tmp_path: Path) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    captured_hash = _sha256_text(source.read_text(encoding="utf-8"))
    proposal_path = _proposal(fixture, captured_hash)
    source.write_text(SOURCE_TEXT.replace("old walk", "changed walk"), encoding="utf-8")

    result = composition_contracts.capture_composition_candidates(
        "fig3_resistance_mechanism",
        proposal_json_path=proposal_path,
        workspace_root=workspace,
    )

    freshness = result["freshness_vector"]
    assert result["status"] == "proposed_unranked"
    assert freshness["status"]["source"] == "stale"
    assert freshness["stale_fields"] == ["source"]
    assert freshness["blocking_for"] == ["rank", "apply"]

    ranked = composition_contracts.rank_composition_candidates(
        "fig3_resistance_mechanism",
        candidate_set=result,
        freshness_vector=freshness,
        workspace_root=workspace,
    )
    applied = composition_contracts.apply_composition_candidate(
        "fig3_resistance_mechanism",
        candidate_set=result,
        freshness_vector=freshness,
        workspace_root=workspace,
    )

    assert ranked["status"] == "proposed_unranked"
    assert ranked["diagnostics"][0]["code"] == "stale_evidence_proposed_unranked"
    assert applied["status"] == "blocked"
    assert applied["diagnostics"][0]["code"] == "refresh_required"


def test_capture_preserves_no_model_call_contract(tmp_path: Path) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    proposal_path = _proposal(fixture, _sha256_text(source.read_text(encoding="utf-8")))

    result = composition_contracts.capture_composition_candidates(
        "fig3_resistance_mechanism",
        proposal_json_path=proposal_path,
        workspace_root=workspace,
    )

    assert result["capture_policy"]["model_calls_allowed"] is False
    assert result["capture_policy"]["executable_payload_allowed"] is False
    assert "model_payload" not in result["candidates"][0]
    assert "executable_payload" not in result["candidates"][0]
