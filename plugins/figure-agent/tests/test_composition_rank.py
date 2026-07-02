from __future__ import annotations

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
REPLACEMENT_TEXT = SOURCE_TEXT.replace("old walk", "smoothed walk")


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path, name: str = "candidate_demo") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels:\n  - id: A\n", encoding="utf-8")
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, fixture, source


def _finding(check: str, delta: str) -> dict[str, str]:
    return {
        "check": check,
        "mode": "deterministic",
        "delta": delta,
        "metric": f"{check}_count",
        "evidence_object": "carrier_walk",
        "threshold": "<=0",
    }


def _candidate(candidate_id: str, source: Path, workspace: Path, *, delta: str) -> dict:
    return {
        "id": candidate_id,
        "family": "freeform_structural",
        "operations": [
            {
                "schema": "figure-agent.composition-candidate-operation.v1",
                "kind": "replace_semantic_block",
                "path": source.relative_to(workspace).as_posix(),
                "base_source_hash": _sha256_text(source.read_text(encoding="utf-8")),
                "selector": {
                    "kind": "semantic_block",
                    "object_id": "carrier_walk",
                    "start_marker": "% fig-agent:start object=carrier_walk",
                    "end_marker": "% fig-agent:end object=carrier_walk",
                },
                "replacement_text": REPLACEMENT_TEXT,
            }
        ],
        "composition_lint_delta": {
            "deterministic": [_finding("orphan_plot", delta)],
            "human_commentary": [
                {
                    "check": "path_mechanicalness",
                    "mode": "human_commentary",
                    "rank_eligible": True,
                    "blocking_allowed": True,
                }
            ],
        },
    }


def _candidate_set(workspace: Path, source: Path) -> dict:
    return {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": "candidate_demo",
        "status": "proposed_unranked",
        "candidates": [
            _candidate("CCAND_BAD", source, workspace, delta="regressed"),
            _candidate("CCAND_GOOD", source, workspace, delta="improved"),
        ],
    }


def _single_candidate_set(workspace: Path, source: Path) -> dict:
    return {
        **_candidate_set(workspace, source),
        "candidates": [_candidate("CCAND_GOOD", source, workspace, delta="improved")],
    }


def _write_prepare_manifest(fixture: Path, candidate_id: str) -> None:
    sandbox = fixture / "build" / "candidates" / candidate_id
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True)
    source_copy.write_text(REPLACEMENT_TEXT, encoding="utf-8")
    (sandbox / "composition_render_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-render-manifest.v1",
                "fixture": fixture.name,
                "candidate_id": candidate_id,
                "sandbox_path": f"build/candidates/{candidate_id}",
                "artifacts": {
                    "source_copy": f"build/candidates/{candidate_id}/source/candidate.tex"
                },
                "stages": {
                    "prepare": {"status": "success"},
                    "compile": {"status": "not_run"},
                    "export": {"status": "not_run"},
                    "crop": {"status": "not_run"},
                    "evaluate": {"status": "not_run"},
                },
                "human_review_required": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _render_manifest_path(fixture: Path, candidate_id: str) -> Path:
    return fixture / "build" / "candidates" / candidate_id / "composition_render_manifest.json"


def test_rank_uses_only_deterministic_lint_delta_and_hard_gates(tmp_path: Path) -> None:
    import composition_rank

    workspace, fixture, source = _fixture(tmp_path)
    for candidate_id in ("CCAND_BAD", "CCAND_GOOD"):
        _write_prepare_manifest(fixture, candidate_id)

    payload = composition_rank.rank_composition_candidates(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        workspace_root=workspace,
    )

    assert payload["schema"] == "figure-agent.composition-rank-result.v1"
    assert payload["status"] == "ranked"
    assert payload["rank_policy"]["basis"] == ["hard_gates", "deterministic_composition_lint_delta"]
    assert payload["rank_policy"]["aesthetic_scoring_allowed"] is False
    assert [item["candidate_id"] for item in payload["ranked_candidates"]] == [
        "CCAND_GOOD",
        "CCAND_BAD",
    ]
    encoded = json.dumps(payload, sort_keys=True)
    assert "aesthetic_score" not in encoded
    assert "taste_score" not in encoded


def test_rank_ignores_human_commentary_for_ordering_and_blocking(tmp_path: Path) -> None:
    import composition_rank

    workspace, fixture, source = _fixture(tmp_path)
    for candidate_id in ("CCAND_BAD", "CCAND_GOOD"):
        _write_prepare_manifest(fixture, candidate_id)

    payload = composition_rank.rank_composition_candidates(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        workspace_root=workspace,
    )

    bad = payload["ranked_candidates"][1]
    commentary = bad["composition_lint_delta"]["human_commentary"][0]
    assert bad["candidate_id"] == "CCAND_BAD"
    assert commentary["rank_eligible"] is False
    assert commentary["blocking_allowed"] is False
    assert bad["hard_gate_state"] == "reviewable"


def test_freeform_structural_is_review_only_and_never_auto_apply(tmp_path: Path) -> None:
    import composition_rank

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, "CCAND_GOOD")
    candidate_set = _single_candidate_set(workspace, source)

    payload = composition_rank.rank_composition_candidates(
        "candidate_demo",
        candidate_set=candidate_set,
        workspace_root=workspace,
    )

    ranked = payload["ranked_candidates"][0]
    assert ranked["family"] == "freeform_structural"
    assert ranked["effective_apply_authority"] == "review_only"
    assert ranked["auto_apply_allowed"] is False


def test_prepare_only_render_manifest_is_reviewable_without_tex_execution(tmp_path: Path) -> None:
    import composition_rank

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, "CCAND_GOOD")
    candidate_set = _single_candidate_set(workspace, source)

    payload = composition_rank.rank_composition_candidates(
        "candidate_demo",
        candidate_set=candidate_set,
        workspace_root=workspace,
    )

    ranked = payload["ranked_candidates"][0]
    assert ranked["render_status"] == "prepared_needs_human_review"
    assert ranked["hard_gates"] == {
        "prepare": "success",
        "compile": "not_run",
        "export": "not_run",
        "crop": "not_run",
        "evaluate": "not_run",
    }
    assert not (fixture / "build" / "candidates" / "CCAND_GOOD" / "render").exists()


def test_rank_blocks_non_prepare_only_manifest_from_reviewable_state(
    tmp_path: Path,
) -> None:
    import composition_rank

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, "CCAND_GOOD")
    manifest_path = _render_manifest_path(fixture, "CCAND_GOOD")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["stages"]["compile"] = {"status": "success"}
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    candidate_set = _single_candidate_set(workspace, source)

    payload = composition_rank.rank_composition_candidates(
        "candidate_demo",
        candidate_set=candidate_set,
        workspace_root=workspace,
    )

    ranked = payload["ranked_candidates"][0]
    assert ranked["render_status"] == "not_prepared"
    assert ranked["hard_gate_state"] == "blocked"
    assert ranked["rank_evidence"]["deterministic_delta_score"] == -100


def test_rank_rejects_render_manifest_identity_mismatch(tmp_path: Path) -> None:
    import composition_rank
    import pytest

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, "CCAND_GOOD")
    manifest_path = _render_manifest_path(fixture, "CCAND_GOOD")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_id"] = "CCAND_OTHER"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    candidate_set = _single_candidate_set(workspace, source)

    with pytest.raises(composition_rank.CompositionRankError, match="identity_mismatch"):
        composition_rank.rank_composition_candidates(
            "candidate_demo",
            candidate_set=candidate_set,
            workspace_root=workspace,
        )


def test_rank_rejects_render_manifest_path_escape_through_sandbox_symlink(
    tmp_path: Path,
) -> None:
    import composition_rank
    import pytest

    workspace, fixture, source = _fixture(tmp_path)
    outside = tmp_path / "outside-candidate"
    outside.mkdir()
    (fixture / "build" / "candidates").mkdir(parents=True)
    (fixture / "build" / "candidates" / "CCAND_GOOD").symlink_to(outside)
    candidate_set = _single_candidate_set(workspace, source)

    with pytest.raises(composition_rank.CompositionRankError, match="sandbox_symlink_forbidden"):
        composition_rank.rank_composition_candidates(
            "candidate_demo",
            candidate_set=candidate_set,
            workspace_root=workspace,
        )


def test_stale_freshness_remains_proposed_unranked(tmp_path: Path) -> None:
    import composition_rank

    workspace, _fixture_dir, source = _fixture(tmp_path)
    payload = composition_rank.rank_composition_candidates(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        freshness_vector={"status": {"source": "stale", "composition_lint": "fresh"}},
        workspace_root=workspace,
    )

    assert payload["schema"] == "figure-agent.composition-rank-result.v1"
    assert payload["status"] == "proposed_unranked"
    assert payload["diagnostics"][0]["code"] == "stale_evidence_proposed_unranked"
