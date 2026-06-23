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
AFTER_TEXT = SOURCE_TEXT.replace("old walk", "smoothed walk")


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def _fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text(SOURCE_TEXT, encoding="utf-8")
    return fixture


def _candidate_set(fixture: Path, source_hash: str) -> Path:
    path = fixture / "build" / "candidates" / "composition_candidate_set.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": fixture.name,
                "candidates": [
                    {
                        "id": "CCAND001",
                        "family": "freeform_structural",
                        "operations": [
                            {
                                "kind": "replace_semantic_block",
                                "path": f"examples/{fixture.name}/{fixture.name}.tex",
                                "base_source_hash": source_hash,
                                "selector": {
                                    "kind": "semantic_block",
                                    "start_marker": "% fig-agent:start object=carrier_walk",
                                    "end_marker": "% fig-agent:end object=carrier_walk",
                                },
                                "replacement_text": AFTER_TEXT,
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
    return path


def _render_artifacts(fixture: Path) -> None:
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True)
    source_copy.write_text(AFTER_TEXT, encoding="utf-8")
    (sandbox / "composition_render_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-render-manifest.v1",
                "fixture": fixture.name,
                "candidate_id": "CCAND001",
                "artifacts": {"source_copy": "build/candidates/CCAND001/source/candidate.tex"},
                "hash_evidence": {"source_copy": _sha256_text(AFTER_TEXT)},
                "stages": {
                    "prepare": {"status": "success"},
                    "compile": {"status": "not_run"},
                    "export": {"status": "not_run"},
                    "crop": {"status": "not_run"},
                    "evaluate": {"status": "not_run"},
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _post_apply_artifacts(fixture: Path) -> None:
    build = fixture / "build"
    exports = fixture / "exports"
    build.mkdir(parents=True, exist_ok=True)
    exports.mkdir(parents=True, exist_ok=True)
    for path in (
        build / "candidate_demo.pdf",
        build / "candidate_demo.png",
        exports / "candidate_demo.pdf",
        exports / "candidate_demo.png",
        exports / "candidate_demo.svg",
        exports / "candidate_demo.tif",
    ):
        path.write_bytes(b"artifact")
    (build / "visual_clash.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.visual-clash.v1",
                "fixture": fixture.name,
                "render_pdf": "build/candidate_demo.pdf",
                "total": 2,
                "candidates": [
                    {
                        "id": "VC001",
                        "kind": "text_on_path",
                        "bbox_px": [10, 20, 30, 40],
                        "metric": {"dark": 0.08},
                        "text": "sulfur",
                    },
                    {
                        "id": "VC002",
                        "kind": "near_miss",
                        "bbox_px": [50, 60, 70, 80],
                        "metric": {"edge": 0.01},
                        "text": "S80",
                    },
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    crop_dir = build / "audit_crops" / "visual_clash"
    crop_dir.mkdir(parents=True)
    (crop_dir / "VC001_sulfur.png").write_bytes(b"crop")
    (crop_dir / "VC002_S80.png").write_bytes(b"crop")
    for report in ("text_boundary_clash.json", "label_path_proximity.json"):
        (build / report).write_text(
            json.dumps(
                {
                    "schema": f"figure-agent.{report.removesuffix('.json')}.v1",
                    "fixture": fixture.name,
                    "total": 0,
                    "candidates": [],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def test_fig_agent_compose_apply_mutates_after_explicit_acceptance(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _candidate_set(fixture, _sha256_text(SOURCE_TEXT))
    _render_artifacts(fixture)

    accept = _run(
        workspace,
        "compose-accept",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--reviewer",
        "local-user",
        "--rationale",
        "Reviewed before apply.",
        "--permission",
        "apply_to_fixture_source",
        "--permission",
        "accept_freeform_structural",
        "--json",
    )
    assert accept.returncode == 0, accept.stderr

    result = _run(
        workspace,
        "compose-apply",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-apply-result.v1"
    assert payload["status"] == "applied_unverified"
    assert source.read_text(encoding="utf-8") == AFTER_TEXT
    assert (fixture / "build" / "candidates" / "CCAND001" / "rollback.patch").is_file()


def test_fig_agent_compose_post_apply_verify_summarizes_render_export_and_detectors(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _candidate_set(fixture, _sha256_text(SOURCE_TEXT))
    _render_artifacts(fixture)

    accept = _run(
        workspace,
        "compose-accept",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--reviewer",
        "local-user",
        "--rationale",
        "Reviewed before apply.",
        "--permission",
        "apply_to_fixture_source",
        "--permission",
        "accept_freeform_structural",
        "--json",
    )
    assert accept.returncode == 0, accept.stderr
    apply_result = _run(
        workspace,
        "compose-apply",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )
    assert apply_result.returncode == 0, apply_result.stderr
    _post_apply_artifacts(fixture)

    result = _run(
        workspace,
        "compose-post-apply-verify",
        fixture.name,
        "--candidate-id",
        "CCAND001",
        "--apply-result",
        "build/candidates/CCAND001/composition_apply_result.json",
        "--output",
        "build/candidates/post_apply_visual_receipt.json",
        "--json",
    )

    payload = json.loads(result.stdout)
    receipt_path = fixture / "build" / "candidates" / "post_apply_visual_receipt.json"
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.post-apply-visual-receipt.v1"
    assert payload["status"] == "rendered_exported_with_strict_visual_warnings"
    assert payload["source_matches_candidate_copy"] is True
    assert payload["render"]["status"] == "present"
    assert payload["export"]["status"] == "present"
    assert payload["strict_compile"]["status"] == "blocked_by_visual_clash"
    assert payload["detector_reports"]["visual_clash"]["total"] == 2
    assert payload["detector_reports"]["text_boundary_clash"]["total"] == 0
    assert payload["required_next_actions"] == [
        "review visual_clash candidates before closeout",
        "refresh critique after source apply",
    ]
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == payload
    assert source.read_text(encoding="utf-8") == AFTER_TEXT


def test_fig_agent_compose_visual_clash_triage_builds_review_items(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set_path = _candidate_set(fixture, _sha256_text(SOURCE_TEXT))
    _render_artifacts(fixture)

    accept = _run(
        workspace,
        "compose-accept",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--reviewer",
        "local-user",
        "--rationale",
        "Reviewed before apply.",
        "--permission",
        "apply_to_fixture_source",
        "--permission",
        "accept_freeform_structural",
        "--json",
    )
    assert accept.returncode == 0, accept.stderr
    apply_result = _run(
        workspace,
        "compose-apply",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )
    assert apply_result.returncode == 0, apply_result.stderr
    _post_apply_artifacts(fixture)
    receipt = _run(
        workspace,
        "compose-post-apply-verify",
        fixture.name,
        "--candidate-id",
        "CCAND001",
        "--apply-result",
        "build/candidates/CCAND001/composition_apply_result.json",
        "--output",
        "build/candidates/post_apply_visual_receipt.json",
        "--json",
    )
    assert receipt.returncode == 0, receipt.stderr

    result = _run(
        workspace,
        "compose-visual-clash-triage",
        fixture.name,
        "--receipt",
        "build/candidates/post_apply_visual_receipt.json",
        "--output",
        "build/candidates/visual_clash_triage.json",
        "--json",
    )

    payload = json.loads(result.stdout)
    triage_path = fixture / "build" / "candidates" / "visual_clash_triage.json"
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.visual-clash-triage.v1"
    assert payload["status"] == "review_required"
    assert payload["candidate_id"] == "CCAND001"
    assert payload["closeout_blocked"] is True
    assert payload["total_candidates"] == 2
    assert payload["kind_counts"] == {"near_miss": 1, "text_on_path": 1}
    assert payload["review_items"][0]["id"] == "VC001"
    assert payload["review_items"][0]["crop_paths"] == [
        "build/audit_crops/visual_clash/VC001_sulfur.png"
    ]
    assert payload["review_items"][0]["suggested_decision_values"] == [
        "true_positive",
        "false_positive",
        "accepted_tradeoff",
    ]
    assert payload["required_next_actions"] == [
        "adjudicate visual_clash review_items",
        "refresh critique after visual clash adjudication",
    ]
    assert json.loads(triage_path.read_text(encoding="utf-8")) == payload
