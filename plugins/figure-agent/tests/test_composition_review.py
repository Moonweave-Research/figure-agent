from __future__ import annotations

import json
import struct
import sys
import zlib
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
SPARK_SOURCE_TEXT = (
    "% fig-agent:start object=current_sparkline\n"
    "old spark\n"
    "% fig-agent:end object=current_sparkline\n"
)
SPARK_REPLACEMENT_TEXT = SPARK_SOURCE_TEXT.replace("old spark", "anchored spark")


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _png_bytes(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = (
        len(ihdr).to_bytes(4, "big")
        + b"IHDR"
        + ihdr
        + zlib.crc32(b"IHDR" + ihdr).to_bytes(4, "big")
    )
    return signature + ihdr_chunk


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


def _sparkline_operation(workspace: Path, source: Path) -> dict:
    return {
        "schema": "figure-agent.composition-candidate-operation.v1",
        "kind": "replace_semantic_block",
        "path": source.relative_to(workspace).as_posix(),
        "base_source_hash": _sha256_text(source.read_text(encoding="utf-8")),
        "selector": {
            "kind": "semantic_block",
            "object_id": "current_sparkline",
            "start_marker": "% fig-agent:start object=current_sparkline",
            "end_marker": "% fig-agent:end object=current_sparkline",
        },
        "replacement_text": SPARK_REPLACEMENT_TEXT,
    }


def _write_prepare_manifest(
    fixture: Path,
    *,
    candidate_id: str = "CCAND001",
    source_copy_symlink: bool = False,
    source_copy_text: str = REPLACEMENT_TEXT,
    render_artifact: bool = False,
    valid_png: bool = False,
    manifest_visual_artifacts: bool = True,
) -> None:
    sandbox = fixture / "build" / "candidates" / candidate_id
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True)
    if source_copy_symlink:
        outside = fixture.parent / "outside.tex"
        outside.write_text(source_copy_text, encoding="utf-8")
        source_copy.symlink_to(outside)
    else:
        source_copy.write_text(source_copy_text, encoding="utf-8")
    artifacts = {
        "source_copy": f"build/candidates/{candidate_id}/source/candidate.tex"
    }
    if render_artifact:
        rendered = sandbox / "render" / "candidate.png"
        rendered.parent.mkdir(parents=True)
        rendered.write_bytes(
            _png_bytes(2, 3) if valid_png else b"\x89PNG\r\n\x1a\ncandidate-render"
        )
        board = fixture / "build" / "candidates" / "comparison_board.png"
        board.write_bytes(_png_bytes(5, 7) if valid_png else b"\x89PNG\r\n\x1a\ncomparison-board")
        if manifest_visual_artifacts:
            artifacts["rendered_candidate"] = (
                f"build/candidates/{candidate_id}/render/candidate.png"
            )
            artifacts["comparison_board"] = "build/candidates/comparison_board.png"
    (sandbox / "composition_render_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-render-manifest.v1",
                "fixture": fixture.name,
                "candidate_id": candidate_id,
                "sandbox_path": f"build/candidates/{candidate_id}",
                "artifacts": artifacts,
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


def test_review_packet_includes_visual_evidence_for_rendered_candidates(
    tmp_path: Path,
) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, render_artifact=True)

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
    )

    evidence = payload["visual_evidence"]
    assert evidence["render_manifest"]["path"] == (
        "build/candidates/CCAND001/composition_render_manifest.json"
    )
    assert evidence["candidate_render_artifacts"] == [
        {
            "kind": "rendered_candidate",
            "path": "build/candidates/CCAND001/render/candidate.png",
            "exists": True,
            "size_bytes": 24,
            "sha256": evidence["candidate_render_artifacts"][0]["sha256"],
        }
    ]
    assert evidence["comparison_boards"] == [
        {
            "kind": "comparison_board",
            "path": "build/candidates/comparison_board.png",
            "exists": True,
            "size_bytes": 24,
            "sha256": evidence["comparison_boards"][0]["sha256"],
        }
    ]


def test_review_packet_writes_visual_metrics_when_requested(tmp_path: Path) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(fixture, render_artifact=True, valid_png=True)

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
        write_visual_metrics=True,
    )

    metrics_path = fixture / "build" / "candidates" / "CCAND001" / "visual_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert payload["visual_evidence"]["visual_metrics"]["path"] == (
        "build/candidates/CCAND001/visual_metrics.json"
    )
    assert metrics["schema"] == "figure-agent.visual-metrics.v1"
    assert metrics["candidate_id"] == "CCAND001"
    assert metrics["artifact_paths"] == [
        "build/candidates/CCAND001/render/candidate.png",
        "build/candidates/comparison_board.png",
    ]
    assert metrics["nonblank_checks"] == [
        {
            "path": "build/candidates/CCAND001/render/candidate.png",
            "exists": True,
            "size_bytes": len(_png_bytes(2, 3)),
            "looks_nonblank": True,
        },
        {
            "path": "build/candidates/comparison_board.png",
            "exists": True,
            "size_bytes": len(_png_bytes(5, 7)),
            "looks_nonblank": True,
        },
    ]
    assert metrics["image_dimensions"] == [
        {
            "path": "build/candidates/CCAND001/render/candidate.png",
            "width": 2,
            "height": 3,
        },
        {
            "path": "build/candidates/comparison_board.png",
            "width": 5,
            "height": 7,
        },
    ]


def test_review_packet_discovers_conventional_visual_artifacts_when_manifest_omits_them(
    tmp_path: Path,
) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    _write_prepare_manifest(
        fixture,
        render_artifact=True,
        valid_png=True,
        manifest_visual_artifacts=False,
    )

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    evidence = payload["visual_evidence"]
    assert evidence["candidate_render_artifacts"][0]["path"] == (
        "build/candidates/CCAND001/render/candidate.png"
    )
    assert evidence["comparison_boards"][0]["path"] == "build/candidates/comparison_board.png"


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
        "status": "ready_for_local_acceptance",
        "source_mutation_allowed": False,
    }


def test_review_packet_accepts_multi_operation_composite_candidate(tmp_path: Path) -> None:
    import composition_review

    workspace, fixture, source = _fixture(tmp_path)
    source.write_text(SOURCE_TEXT + SPARK_SOURCE_TEXT, encoding="utf-8")
    candidate_set = _candidate_set(workspace, source)
    candidate = candidate_set["candidates"][0]
    candidate["id"] = "CCAND_COMBO"
    candidate["family"] = "composite_structural"
    candidate["operations"].append(_sparkline_operation(workspace, source))
    candidate["composition_lint_delta"]["deterministic"].append(
        {
            "check": "orphan_plot",
            "mode": "deterministic",
            "delta": "improved",
            "metric": "unanchored_plot_count",
            "evidence_object": "current_sparkline",
            "threshold": "<=0",
        }
    )
    _write_prepare_manifest(
        fixture,
        candidate_id="CCAND_COMBO",
        source_copy_text=REPLACEMENT_TEXT + SPARK_REPLACEMENT_TEXT,
    )

    payload = composition_review.build_composition_review_packet(
        "candidate_demo",
        candidate_set=candidate_set,
        candidate_id="CCAND_COMBO",
        workspace_root=workspace,
    )

    assert payload["candidate_id"] == "CCAND_COMBO"
    assert payload["candidate"]["family"] == "composite_structural"
    assert len(payload["composition_lint_delta"]["deterministic"]) == 2
    assert payload["apply_boundary"]["status"] == "ready_for_local_acceptance"


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
