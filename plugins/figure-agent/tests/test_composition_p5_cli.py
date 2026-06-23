from __future__ import annotations

import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels:\n  - id: C\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(SOURCE_TEXT, encoding="utf-8")
    return fixture


def _candidate_set(fixture: Path, source_hash: str) -> Path:
    path = fixture / "build" / "candidates" / "composition_candidate_set.json"
    path.parent.mkdir(parents=True)
    payload = {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": fixture.name,
        "status": "proposed_unranked",
        "candidates": [
            {
                "id": "CCAND001",
                "family": "freeform_structural",
                "operations": [
                    {
                        "schema": "figure-agent.composition-candidate-operation.v1",
                        "kind": "replace_semantic_block",
                        "path": f"examples/{fixture.name}/{fixture.name}.tex",
                        "base_source_hash": source_hash,
                        "selector": {
                            "kind": "semantic_block",
                            "start_marker": "% fig-agent:start object=carrier_walk",
                            "end_marker": "% fig-agent:end object=carrier_walk",
                        },
                        "replacement_text": SOURCE_TEXT.replace("old walk", "smoothed walk"),
                    }
                ],
                "composition_lint_delta": {
                    "deterministic": [
                        {
                            "check": "orphan_plot",
                            "mode": "deterministic",
                            "delta": "improved",
                            "metric": "orphan_plot_count",
                            "evidence_object": "carrier_walk",
                            "threshold": "<=0",
                        }
                    ],
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
        ],
    }
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def _prepare_candidate(workspace: Path, fixture: Path) -> Path:
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _candidate_set(fixture, _sha256_text(source.read_text(encoding="utf-8")))
    result = _run(
        workspace,
        "compose-render",
        "candidate_demo",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )
    assert result.returncode == 0, result.stderr
    return candidate_set_path


def test_fig_agent_compose_rank_outputs_json_without_aesthetic_scoring(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set_path = _prepare_candidate(workspace, fixture)

    result = _run(
        workspace,
        "compose-rank",
        "candidate_demo",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--json",
    )

    payload = json.loads(result.stdout)
    encoded = json.dumps(payload, sort_keys=True)
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-rank-result.v1"
    assert payload["rank_policy"]["aesthetic_scoring_allowed"] is False
    assert payload["ranked_candidates"][0]["effective_apply_authority"] == "review_only"
    assert payload["ranked_candidates"][0]["auto_apply_allowed"] is False
    assert "aesthetic_score" not in encoded
    assert "taste_score" not in encoded
    assert not (fixture / "build" / "candidates" / "CCAND001" / "render").exists()


def test_fig_agent_compose_rank_keeps_stale_candidate_set_unranked(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _candidate_set(fixture, _sha256_text(source.read_text(encoding="utf-8")))
    payload = json.loads(candidate_set_path.read_text(encoding="utf-8"))
    payload["freshness_vector"] = {"status": {"source": "stale", "composition_lint": "fresh"}}
    candidate_set_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    result = _run(
        workspace,
        "compose-rank",
        "candidate_demo",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--json",
    )

    ranked = json.loads(result.stdout)
    assert result.returncode == 1
    assert ranked["status"] == "proposed_unranked"
    assert ranked["diagnostics"][0]["code"] == "stale_evidence_proposed_unranked"
    assert "stale_evidence_proposed_unranked" in result.stderr


def test_fig_agent_compose_review_outputs_source_before_after_packet_without_tex_execution(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _prepare_candidate(workspace, fixture)

    result = _run(
        workspace,
        "compose-review",
        "candidate_demo",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-review-packet.v1"
    assert payload["render_status"] == "prepared_needs_human_review"
    assert payload["before_artifacts"][0]["path"] == "candidate_demo.tex"
    assert payload["after_artifacts"][0]["path"] == (
        "build/candidates/CCAND001/source/candidate.tex"
    )
    assert payload["composition_lint_delta"]["deterministic"][0]["metric"] == "orphan_plot_count"
    assert payload["composition_lint_delta"]["human_commentary"][0]["rank_eligible"] is False
    assert payload["visual_evidence"]["visual_metrics"]["path"] == (
        "build/candidates/CCAND001/visual_metrics.json"
    )
    visual_metrics_path = fixture / "build" / "candidates" / "CCAND001" / "visual_metrics.json"
    assert json.loads(visual_metrics_path.read_text(encoding="utf-8"))["artifact_paths"] == []
    assert payload["apply_boundary"]["source_mutation_allowed"] is False
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert not (fixture / "exports").exists()
    assert not (fixture / "build" / "candidates" / "CCAND001" / "render").exists()


def test_fig_agent_compose_review_synthesis_writes_findings_first_markdown(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set_path = _prepare_candidate(workspace, fixture)
    review = _run(
        workspace,
        "compose-review",
        "candidate_demo",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--output",
        "build/candidates/CCAND001/composition_review_packet.json",
        "--json",
    )
    assert review.returncode == 0, review.stderr

    result = _run(
        workspace,
        "compose-review-synthesis",
        "candidate_demo",
        "--review-packet",
        "build/candidates/CCAND001/composition_review_packet.json",
        "--output",
        "build/candidates/review_synthesis.md",
        "--json",
    )

    payload = json.loads(result.stdout)
    synthesis_path = fixture / "build" / "candidates" / "review_synthesis.md"
    text = synthesis_path.read_text(encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-review-synthesis.v1"
    assert payload["status"] == "review_synthesis_ready"
    assert payload["path"] == "build/candidates/review_synthesis.md"
    assert payload["hard_refutations"] == []
    assert text.startswith("# Composition Review Synthesis\n\n## Confirmed\n")
    assert "- Candidate `CCAND001` is review-ready with source mutation disabled." in text
    assert "## Refuted\n\n- None." in text
    assert "## Unverified\n\n- Human visual preference remains unverified until acceptance." in text
    assert "## Acceptance Recommendation\n\nHuman review required before apply." in text
