from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

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


def _candidate_set(workspace: Path, source: Path) -> dict:
    return {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": "candidate_demo",
        "status": "proposed_unranked",
        "candidates": [
            {
                "id": "CCAND001",
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


def _write_prepare_manifest(
    fixture: Path,
    *,
    candidate_id: str = "CCAND001",
    source_copy_symlink: bool = False,
) -> None:
    sandbox = fixture / "build" / "candidates" / candidate_id
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True)
    if source_copy_symlink:
        outside = fixture.parent / "outside.tex"
        outside.write_text(REPLACEMENT_TEXT, encoding="utf-8")
        source_copy.symlink_to(outside)
    else:
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


def test_review_packet_reports_before_after_source_artifacts_without_tex_execution(
    tmp_path: Path,
) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture)

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
    )

    assert payload["schema"] == "figure-agent.composition-review-packet.v1"
    assert payload["render_status"] == "prepared_needs_human_review"
    assert payload["hard_gates"] == {
        "prepare": "success",
        "compile": "not_run",
        "export": "not_run",
        "crop": "not_run",
        "evaluate": "not_run",
    }
    assert payload["before_artifacts"][0]["path"] == "candidate_demo.tex"
    assert payload["after_artifacts"][0]["path"] == "build/candidates/CCAND001/source/candidate.tex"
    assert payload["before_artifacts"][0]["sha256"] == _sha256_text(SOURCE_TEXT)
    assert payload["after_artifacts"][0]["sha256"] == _sha256_text(REPLACEMENT_TEXT)
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert not (fixture / "exports").exists()
    assert not (fixture / "build" / "candidates" / "CCAND001" / "render").exists()


def test_review_packet_includes_metric_backed_deterministic_lint_delta(
    tmp_path: Path,
) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture)

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    finding = payload["composition_lint_delta"]["deterministic"][0]
    assert finding["metric"] == "orphan_plot_count"
    assert finding["evidence_object"] == "carrier_walk"
    assert finding["threshold"] == "<=0"


def test_review_packet_keeps_human_commentary_non_ranking(tmp_path: Path) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture)

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    commentary = payload["composition_lint_delta"]["human_commentary"][0]
    assert commentary["mode"] == "human_commentary"
    assert commentary["rank_eligible"] is False
    assert commentary["blocking_allowed"] is False


def test_review_packet_marks_freeform_structural_review_only(tmp_path: Path) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture)

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    assert payload["candidate"]["family"] == "freeform_structural"
    assert payload["candidate"]["effective_apply_authority"] == "review_only"
    assert payload["candidate"]["auto_apply_allowed"] is False
    assert payload["apply_boundary"] == {
        "status": "p6_not_implemented",
        "source_mutation_allowed": False,
    }


def test_review_packet_rejects_sandbox_path_escape_or_symlink(tmp_path: Path) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, source_copy_symlink=True)

    with pytest.raises(
        composition_review.CompositionReviewError,
        match="sandbox_symlink_forbidden",
    ):
        composition_review.build_composition_review_packet(
            "candidate_demo",
            candidate_set=_candidate_set(workspace, source),
            candidate_id="CCAND001",
            workspace_root=workspace,
        )


def test_review_packet_rejects_requested_second_candidate_symlink(
    tmp_path: Path,
) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture)
    _write_prepare_manifest(
        fixture,
        candidate_id="CCAND002",
        source_copy_symlink=True,
    )
    candidate_set = _candidate_set(workspace, source)
    candidate_set["candidates"].append(
        {**candidate_set["candidates"][0], "id": "CCAND002"}
    )

    with pytest.raises(
        composition_review.CompositionReviewError,
        match="sandbox_symlink_forbidden",
    ):
        composition_review.build_composition_review_packet(
            "candidate_demo",
            candidate_set=candidate_set,
            candidate_id="CCAND002",
            workspace_root=workspace,
        )


def test_review_packet_rejects_absolute_source_path_escape(tmp_path: Path) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    outside = tmp_path / "outside.tex"
    outside.write_text(SOURCE_TEXT, encoding="utf-8")
    _write_prepare_manifest(fixture)
    candidate_set = _candidate_set(workspace, source)
    candidate_set["candidates"][0]["operations"][0]["path"] = outside.as_posix()

    with pytest.raises(composition_review.CompositionReviewError, match="path_escape"):
        composition_review.build_composition_review_packet(
            "candidate_demo",
            candidate_set=candidate_set,
            candidate_id="CCAND001",
            workspace_root=workspace,
        )
