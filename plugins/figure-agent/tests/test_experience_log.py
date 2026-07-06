from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import experience_log  # noqa: E402
from test_evidence_index import _fixture  # noqa: E402


def test_append_apply_experience_record_joins_existing_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    fixture = _fixture(workspace)
    candidate_set_path = fixture / "build" / "candidates" / "candidate_set.json"
    candidate_set = json.loads(candidate_set_path.read_text(encoding="utf-8"))
    candidate_set["candidates"][0].update(
        {
            "edit_family": "label_offset",
            "target": {"panel": "C", "subregion": "trap-label"},
            "selector": {"selector_text_hash": "sha256:" + "a" * 64},
            "operations": [{"kind": "replace_text", "path": "candidate_demo.tex"}],
            "rank_score": 0.72,
            "rank": 1,
        }
    )
    candidate_set["candidates"].append(
        {
            "id": "CAND002",
            "candidate_hash": "sha256:" + "2" * 64,
            "edit_family": "apparatus_strengthen",
            "target": {"panel": "F", "subregion": "air-gap"},
            "selector": {"selector_text_hash": "sha256:" + "b" * 64},
            "operations": [{"kind": "replace_text", "path": "candidate_demo.tex"}],
            "rank_score": 0.61,
            "rank": 2,
        }
    )
    candidate_set_path.write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = experience_log.append_apply_record(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    output = experience_log.experience_log_dir(plugin_root) / "candidate_demo.jsonl"
    assert result["writes"] == ["docs/experience-log/candidate_demo.jsonl"]
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    row = rows[0]
    assert row["schema"] == "figure-agent.experience-record.v1"
    assert row["fixture"] == "candidate_demo"
    assert row["state"]["base_tex_hash"] == "sha256:" + "0" * 64
    assert row["state"]["target"] == {
        "panel": "C",
        "subregion_key": "sha256:" + "a" * 64,
    }
    assert row["action"]["candidate_id"] == "CAND001"
    assert row["action"]["edit_family"] == "label_offset"
    assert row["action"]["candidate_hash"] == "sha256:" + "1" * 64
    assert row["action"]["rank_score"] == 0.72
    assert row["action"]["rank"] == 1
    assert row["action"]["n_candidates"] == 2
    assert row["outcome"]["pipeline_ok"] is True
    assert row["outcome"]["apply_status"] == "applied"
    assert row["outcome"]["quality_movement"] == "neutral"
    assert row["outcome"]["human_label"] is None
    unchosen = rows[1]
    assert unchosen["action"]["candidate_id"] == "CAND002"
    assert unchosen["action"]["rank_score"] == 0.61
    assert unchosen["action"]["rank"] == 2
    assert unchosen["state"]["target"] == {
        "panel": "F",
        "subregion_key": "sha256:" + "b" * 64,
    }
    assert unchosen["outcome"]["apply_status"] == "unchosen"
    assert unchosen["outcome"]["pipeline_ok"] is None
    assert unchosen["outcome"]["quality_movement"] is None


def test_append_apply_record_refuses_symlinked_experience_log(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    _fixture(workspace)
    log_dir = experience_log.experience_log_dir(plugin_root)
    log_dir.mkdir(parents=True)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("", encoding="utf-8")
    (log_dir / "candidate_demo.jsonl").symlink_to(outside)

    with pytest.raises(experience_log.ExperienceLogError, match="experience_log_symlink"):
        experience_log.append_apply_record(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
            plugin_root=plugin_root,
        )


def test_append_recommendation_record_writes_auto_accept_recommendation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = workspace
    _fixture(workspace)
    run_dir = plugin_root / ".scratch" / "quality-search-runs" / "run-001"
    run_dir.mkdir(parents=True)
    for filename in (
        "candidate_set_000.json",
        "candidate_rankings_000.json",
        "selected_semantic_precheck_000.json",
        "selected_review_packet_000.json",
        "selected_acceptance_recommendation_000.json",
    ):
        (run_dir / filename).write_text("{}\n", encoding="utf-8")
    candidate_set = {
        "candidates": [
            {
                "id": "QS001",
                "candidate_hash": "sha256:" + "1" * 64,
                "edit_family": "panel_f_qtr_apparatus_lane",
                "target": {"panel": "F", "subregion": "qtr_apparatus"},
                "operations": [{"kind": "replace_text", "path": "candidate_demo.tex"}],
            },
            {
                "id": "QS002",
                "candidate_hash": "sha256:" + "2" * 64,
                "edit_family": "panel_f_qtr_label_lane",
                "target": {"panel": "F", "subregion": "qtr_label"},
                "operations": [{"kind": "replace_text", "path": "candidate_demo.tex"}],
            },
        ]
    }

    result = experience_log.append_recommendation_record(
        "candidate_demo",
        "QS001",
        candidate_set=candidate_set,
        candidate_rankings=[
            {"candidate_id": "QS001", "rank_score": 0.81},
            {"candidate_id": "QS002", "rank_score": 0.52},
        ],
        decision={"source_context": {"source_hash": "sha256:" + "0" * 64}},
        recommendation={
            "status": "auto_accept_recommended",
            "evidence": {
                "semantic_precheck_status": "pass",
                "review_packet_status": "ready",
                "apply_readiness_status": "ready_for_local_acceptance",
                "full_changed_pixel_ratio": 0.005,
            },
        },
        run_dir=run_dir,
        workspace_root=workspace,
        plugin_root=plugin_root,
        selected_attempt={
            "attempt_id": "run-001:QS001",
            "journal_guide_hash": "sha256:" + "1" * 64,
            "journal_constraints": {"passed": True},
            "semantic_score": {"complete": True},
            "aesthetic_score": {"overall": 0.8073},
            "outputs": {
                "editable": "candidate_demo.tex",
                "pdf": "render/candidate.pdf",
                "png": "render/candidate.png",
                "svg": "render/candidate.svg",
            },
        },
        convergence_decision={
            "decision": "accept",
            "attempt_id": "run-001:QS001",
            "selected_attempt_id": "run-001:QS001",
            "current_aesthetic_score": 0.8073,
            "selected_aesthetic_score": 0.8073,
        },
    )

    output = experience_log.experience_log_dir(plugin_root) / "candidate_demo.jsonl"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert result["writes"] == ["docs/experience-log/candidate_demo.jsonl"]
    assert len(rows) == 2
    row = rows[0]
    assert row["schema"] == "figure-agent.experience-record.v1"
    assert row["action"]["candidate_id"] == "QS001"
    assert row["action"]["edit_family"] == "panel_f_qtr_apparatus_lane"
    assert row["action"]["rank_score"] == 0.81
    assert row["action"]["rank"] == 1
    assert row["outcome"]["apply_status"] == "blocked"
    assert row["outcome"]["quality_movement"] == "neutral"
    assert row["outcome"]["human_label"] is None
    assert row["outcome"]["human_decision_kind"] == "auto_accept_recommended"
    assert row["outcome"]["automation_boundary"] == "recommendation_only"
    assert row["outcome"]["convergence"] == {
        "attempt_id": "run-001:QS001",
        "decision": "accept",
        "journal_constraints_passed": True,
        "semantic_complete": True,
        "aesthetic_overall": 0.8073,
        "journal_guide_hash": "sha256:" + "1" * 64,
        "selected_aesthetic_score": 0.8073,
        "output_formats": ["editable", "pdf", "png", "svg"],
        "outputs": {
            "editable": "candidate_demo.tex",
            "pdf": "render/candidate.pdf",
            "png": "render/candidate.png",
            "svg": "render/candidate.svg",
        },
    }
    assert row["outcome"]["verifiers"] == {
        "acceptance_recommendation": "pass",
        "apply_readiness": "pass",
        "convergence_decision": "pass",
        "journal_constraints": "pass",
        "review_packet": "pass",
        "semantic_precheck": "pass",
    }
    assert row["outcome"]["pixel_delta"]["changed_pixel_ratio"] == 0.005
    assert row["source_artifacts"][-2:] == [
        ".scratch/quality-search-runs/run-001/selected_attempt_000.json",
        ".scratch/quality-search-runs/run-001/convergence_decision_000.json",
    ]
    unchosen = rows[1]
    assert unchosen["action"]["candidate_id"] == "QS002"
    assert unchosen["action"]["edit_family"] == "panel_f_qtr_label_lane"
    assert unchosen["action"]["rank_score"] == 0.52
    assert unchosen["action"]["rank"] == 2
    assert unchosen["outcome"]["apply_status"] == "unchosen"
    assert unchosen["outcome"]["quality_movement"] is None
    assert unchosen["outcome"]["human_decision_kind"] == "counterfactual_unchosen"


def test_append_recommendation_record_writes_convergence_deferred_recommendation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = workspace
    _fixture(workspace)
    run_dir = plugin_root / ".scratch" / "quality-search-runs" / "run-002"
    run_dir.mkdir(parents=True)
    for filename in (
        "candidate_set_000.json",
        "candidate_rankings_000.json",
        "selected_semantic_precheck_000.json",
        "selected_review_packet_000.json",
        "selected_acceptance_recommendation_000.json",
        "selected_attempt_000.json",
        "convergence_decision_000.json",
    ):
        (run_dir / filename).write_text("{}\n", encoding="utf-8")
    candidate_set = {
        "candidates": [
            {
                "id": "QS001",
                "candidate_hash": "sha256:" + "1" * 64,
                "edit_family": "panel_f_qtr_apparatus_lane",
                "target": {"panel": "F", "subregion": "qtr_apparatus"},
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": "candidate_demo.tex",
                        "template_id": "panel_f_qtr_apparatus_lane_v1",
                    }
                ],
            }
        ]
    }

    result = experience_log.append_recommendation_record(
        "candidate_demo",
        "QS001",
        candidate_set=candidate_set,
        candidate_rankings=[{"candidate_id": "QS001", "rank_score": 0.81}],
        decision={"source_context": {"source_hash": "sha256:" + "0" * 64}},
        recommendation={
            "status": "blocked",
            "recommendation": "defer",
            "rationale": "convergence controller did not accept the selected attempt",
            "evidence": {
                "semantic_precheck_status": "pass",
                "review_packet_status": "ready",
                "apply_readiness_status": "ready_for_local_acceptance",
                "full_changed_pixel_ratio": 0.005,
            },
        },
        run_dir=run_dir,
        workspace_root=workspace,
        plugin_root=plugin_root,
        selected_attempt={
            "attempt_id": "run-002:QS001",
            "journal_guide_hash": "sha256:" + "1" * 64,
            "journal_constraints": {"passed": True},
            "semantic_score": {"complete": True},
            "aesthetic_score": {"overall": 0.8073},
            "outputs": {"editable": "candidate_demo.tex", "svg": "render/candidate.svg"},
        },
        convergence_decision={
            "decision": "stop",
            "attempt_id": "run-002:QS001",
            "selected_attempt_id": "run-002:QS001",
            "current_aesthetic_score": 0.8073,
            "selected_aesthetic_score": 0.8073,
        },
    )

    rows = [
        json.loads(line)
        for line in (experience_log.experience_log_dir(plugin_root) / "candidate_demo.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert result["record"]["outcome"]["human_decision_kind"] == "convergence_deferred"
    assert len(rows) == 1
    row = rows[0]
    assert row["outcome"]["apply_status"] == "blocked"
    assert row["outcome"]["quality_movement"] == "neutral"
    assert row["outcome"]["human_decision_kind"] == "convergence_deferred"
    assert row["outcome"]["convergence"]["decision"] == "stop"
    assert row["outcome"]["verifiers"]["convergence_decision"] == "defer"
    assert row["source_artifacts"][-2:] == [
        ".scratch/quality-search-runs/run-002/selected_attempt_000.json",
        ".scratch/quality-search-runs/run-002/convergence_decision_000.json",
    ]


def test_experience_log_is_append_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    _fixture(workspace)

    first = experience_log.append_apply_record(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )
    second = experience_log.append_apply_record(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    output = experience_log.experience_log_dir(plugin_root) / "candidate_demo.jsonl"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert rows[0] == first["record"]
    assert rows[1] == second["record"]


def test_convergence_attempt_history_reconstructs_valid_prior_attempts(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    plugin_root = workspace
    _fixture(workspace)
    log_dir = experience_log.experience_log_dir(plugin_root)
    log_dir.mkdir(parents=True)
    record = {
        "schema": "figure-agent.experience-record.v1",
        "fixture": "candidate_demo",
        "created_at": "2026-07-06T00:00:00Z",
        "state": {"base_tex_hash": "sha256:" + "0" * 64},
        "action": {"candidate_id": "QS001"},
        "outcome": {
            "human_decision_kind": "auto_accept_recommended",
            "convergence": {
                "attempt_id": "run-001:QS001",
                "decision": "accept",
                "journal_guide_hash": "sha256:" + "1" * 64,
                "journal_constraints_passed": True,
                "semantic_complete": True,
                "aesthetic_overall": 0.8073,
                "outputs": {
                    "editable": "candidate_demo.tex",
                    "pdf": "render/candidate.pdf",
                    "png": "render/candidate.png",
                    "svg": "render/candidate.svg",
                },
            },
        },
    }
    (log_dir / "candidate_demo.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")

    history = experience_log.convergence_attempt_history(
        "candidate_demo",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    assert len(history) == 1
    attempt = history[0]
    assert attempt["schema"] == "figure-agent.figure-attempt.v1"
    assert attempt["attempt_id"] == "run-001:QS001"
    assert attempt["aesthetic_score"]["overall"] == 0.8073
    assert attempt["journal_constraints"]["passed"] is True
    assert attempt["semantic_score"]["complete"] is True
    assert attempt["outputs"]["svg"] == "render/candidate.svg"


def test_subregion_key_without_selector_hash_is_marked_unstable(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set_path = fixture / "build" / "candidates" / "candidate_set.json"
    candidate_set = json.loads(candidate_set_path.read_text(encoding="utf-8"))
    candidate_set["candidates"][0]["target"] = {"panel": "C", "subregion": "trap-label"}
    candidate_set_path.write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    row = experience_log.build_apply_record(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
        plugin_root=tmp_path / "plugin",
    )

    assert row["state"]["target"] == {
        "panel": "C",
        "subregion_key": "unstable:trap-label",
    }


def _anchor_candidate_set(anchor_text: str) -> dict[str, Any]:
    return {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [
            {
                "id": "CAND001",
                "candidate_hash": "sha256:" + "1" * 64,
                "visual_review": {"status": "missing_render"},
                "target": {"panel": "F", "subregion": "panel"},
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": "candidate_demo.tex",
                        "original": anchor_text,
                    }
                ],
            }
        ],
    }


def test_subregion_key_is_stable_for_anchored_operation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    anchor_text = "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);\n\\draw (0,0) -- (1,1);\n"
    candidate_set_path = fixture / "build" / "candidates" / "candidate_set.json"
    candidate_set_path.write_text(
        json.dumps(_anchor_candidate_set(anchor_text), sort_keys=True) + "\n",
        encoding="utf-8",
    )

    row = experience_log.build_apply_record(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
        plugin_root=tmp_path / "plugin",
    )

    subregion_key = row["state"]["target"]["subregion_key"]
    assert not subregion_key.startswith("unstable:")
    assert subregion_key.startswith("sha256:")


def test_subregion_key_is_deterministic_across_runs(tmp_path: Path) -> None:
    # Same logical operation applied in two fresh workspaces must yield the same
    # subregion_key: the hash input must exclude timestamps, tmp paths, run ids.
    anchor_text = "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);\n"

    def _key(root: Path) -> str:
        workspace = root / "workspace"
        fixture = _fixture(workspace)
        candidate_set_path = fixture / "build" / "candidates" / "candidate_set.json"
        candidate_set_path.write_text(
            json.dumps(_anchor_candidate_set(anchor_text), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        row = experience_log.build_apply_record(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
            plugin_root=root / "plugin",
        )
        return row["state"]["target"]["subregion_key"]

    first = _key(tmp_path / "run_a")
    second = _key(tmp_path / "run_b")
    assert first == second


def test_subregion_key_is_stable_across_cosmetic_reflow(tmp_path: Path) -> None:
    # Trailing whitespace and surrounding blank lines must not change the key.
    base = "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);\n\\draw (0,0) -- (1,1);\n"
    reflowed = (
        "\n\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);   \n\\draw (0,0) -- (1,1);\n\n"
    )

    def _key(root: Path, anchor_text: str) -> str:
        workspace = root / "workspace"
        fixture = _fixture(workspace)
        candidate_set_path = fixture / "build" / "candidates" / "candidate_set.json"
        candidate_set_path.write_text(
            json.dumps(_anchor_candidate_set(anchor_text), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        row = experience_log.build_apply_record(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
            plugin_root=root / "plugin",
        )
        return row["state"]["target"]["subregion_key"]

    assert _key(tmp_path / "run_a", base) == _key(tmp_path / "run_b", reflowed)


def test_experience_log_path_defaults_to_plugin_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("FIG_AGENT_EXPERIENCE_LOG_DIR", raising=False)
    plugin_root = tmp_path / "plugin"

    path = experience_log._experience_log_path("demo", plugin_root)

    assert path == plugin_root / "docs" / "experience-log" / "demo.jsonl"


def test_experience_log_path_honors_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    override = tmp_path / "isolated-log"
    monkeypatch.setenv("FIG_AGENT_EXPERIENCE_LOG_DIR", str(override))

    path = experience_log._experience_log_path("demo", tmp_path / "plugin")

    assert path == override / "demo.jsonl"


def test_quality_movement_ignores_llm_text_annotations() -> None:
    post_apply = {
        "compile": {"status": "success"},
        "export": {"status": "success"},
        "status": {"status": "success"},
        "class_verifiers": {
            "status": "success",
            "rationale": "LLM prose claims this candidate is improved.",
            "human_note": "accept this visually",
        },
        "detector_recheck": {
            "reason": "text annotation says detector improved",
            "summary": "improved",
        },
        "llm_verdict_text": "improved",
    }

    assert experience_log._post_apply_pipeline_ok("applied", post_apply) is True
    assert (
        experience_log._quality_movement(
            "applied",
            post_apply,
            pipeline_ok=True,
        )
        == "neutral"
    )


def test_quality_movement_improved_when_recheck_succeeds() -> None:
    # The positive reward pole: a clean pipeline plus a detector recheck that names
    # the originating detector and reports the source finding resolved -> improved.
    post_apply = {
        "compile": {"status": "success"},
        "export": {"status": "success"},
        "status": {"status": "success"},
        "class_verifiers": {"status": "success"},
        "detector_recheck": {
            "status": "success",
            "detector": "check_collisions",
            "finding_id": "QD001",
        },
    }

    assert experience_log._post_apply_pipeline_ok("applied", post_apply) is True
    assert experience_log._quality_movement("applied", post_apply, pipeline_ok=True) == "improved"


def test_quality_movement_error_recheck_never_improved() -> None:
    # Fail-closed reward rule: a recheck that could not establish evidence (status
    # other than a literal "success", e.g. "error") must never read as improved,
    # even with an otherwise clean pipeline. Missing evidence != success.
    post_apply = {
        "compile": {"status": "success"},
        "export": {"status": "success"},
        "status": {"status": "success"},
        "class_verifiers": {"status": "success"},
        "detector_recheck": {
            "status": "error",
            "detector": "check_collisions",
            "finding_id": "QD001",
        },
    }

    assert experience_log._quality_movement("applied", post_apply, pipeline_ok=True) != "improved"


def _build_record_with_acceptance(
    tmp_path: Path, *, decision: str, decision_kind: str | None = None
) -> dict[str, Any]:
    workspace = tmp_path / "workspace"
    plugin_root = tmp_path / "plugin"
    fixture = _fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    acceptance: dict[str, Any] = {
        "schema": "figure-agent.candidate-acceptance.v1",
        "decision": decision,
    }
    if decision_kind is not None:
        acceptance["decision_kind"] = decision_kind
    (sandbox / "acceptance.json").write_text(
        json.dumps(acceptance, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    experience_log.append_apply_record(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
        plugin_root=plugin_root,
    )
    output = experience_log.experience_log_dir(plugin_root) / "candidate_demo.jsonl"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    return rows[0]


def test_reject_decision_flows_to_human_label(tmp_path: Path) -> None:
    record = _build_record_with_acceptance(tmp_path, decision="reject")
    assert record["outcome"]["human_label"] == "reject"


def test_accept_decision_still_flows_to_human_label(tmp_path: Path) -> None:
    record = _build_record_with_acceptance(tmp_path, decision="accept")
    assert record["outcome"]["human_label"] == "accept"


def test_unknown_decision_does_not_masquerade_as_human_label(tmp_path: Path) -> None:
    record = _build_record_with_acceptance(tmp_path, decision="defer")
    assert record["outcome"]["human_label"] is None


def test_decision_kind_threads_from_acceptance_payload(tmp_path: Path) -> None:
    record = _build_record_with_acceptance(
        tmp_path, decision="reject", decision_kind="human_visual_reject"
    )
    assert record["outcome"]["human_label"] == "reject"
    assert record["outcome"]["human_decision_kind"] == "human_visual_reject"


def test_experience_log_write_path_refuses_symlinked_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("FIG_AGENT_EXPERIENCE_LOG_DIR", raising=False)
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    real_docs = tmp_path / "real-docs"
    real_docs.mkdir()
    (plugin_root / "docs").symlink_to(real_docs, target_is_directory=True)
    with pytest.raises(experience_log.ExperienceLogError, match="docs_symlink"):
        experience_log._experience_log_path("candidate_demo", plugin_root)
