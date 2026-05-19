from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_loop as fig_loop_mod  # noqa: E402
from fig_loop import FigLoopError, _escalation_summary, ensure_safe_command, run_loop  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _make_fixture(repo: Path, name: str = "loop_demo") -> Path:
    fixture = repo / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"name: {name}\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    return fixture


def _fixture_files(fixture: Path) -> dict[str, str]:
    return {
        str(path.relative_to(fixture)): path.read_text(encoding="utf-8")
        for path in sorted(fixture.rglob("*"))
        if path.is_file()
    }


def _write_adjudication(
    fixture: Path,
    critique_hash: str,
    decisions: list[dict[str, str]] | None = None,
) -> None:
    (fixture / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.critique-adjudication.v1",
                "fixture": fixture.name,
                "source_critique_hash": critique_hash,
                "decisions": decisions
                or [
                    {
                        "finding_id": "C001",
                        "decision": "dismiss",
                        "reason": "false positive in current render",
                        "patch_target": "",
                        "evidence": "",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)


def _quality_axis(
    axis_name: str,
    *,
    verdict: str = "pass",
    recommended_action: str | None = None,
    blocking_items: list[str] | None = None,
) -> dict:
    if recommended_action is None:
        recommended_action = {
            "pass": "none",
            "not_applicable": "none",
            "needs_patch": "patch",
            "needs_human": "human_review",
            "block": "block_release",
        }[verdict]
    axis = {
        "verdict": verdict,
        "confidence": "high" if verdict != "not_applicable" else "low",
        "rationale": "" if verdict == "not_applicable" else f"{axis_name} rationale",
        "evidence": "" if verdict == "not_applicable" else f"{axis_name} evidence",
        "blocking_items": blocking_items or [],
        "recommended_action": recommended_action,
    }
    if axis_name == "panel_role_coherence":
        axis["panel_roles"] = [
            {
                "panel_id": "A",
                "role": "setup",
                "role_quality": "clear",
                "rationale": "panel A introduces the setup",
            }
        ]
    return axis


def _write_v1_2_critique(
    fixture: Path,
    *,
    axis_overrides: dict[str, dict] | None = None,
) -> Path:
    axis_overrides = axis_overrides or {}
    quality_axes = {
        axis_name: axis_overrides.get(axis_name, _quality_axis(axis_name))
        for axis_name in QUALITY_AXIS_NAMES
    }
    critique = fixture / "critique.md"
    critique.write_text(
        "---\n"
        + yaml.safe_dump(
            {
                "schema": "figure-agent.critique.v1.2",
                "fixture": fixture.name,
                "quality_axes": quality_axes,
            },
            sort_keys=False,
        )
        + "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def _patch_fresh_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        fig_loop_mod,
        "infer_stage",
        lambda _example_dir: {
            "stage": 4,
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "workflow_ready": False,
            "golden_ready": False,
            "release_ready": False,
            "final_ready": False,
            "notes": [],
            "next": "inspect figure state",
        },
    )


def _assert_agent_action_required(iteration: dict) -> None:
    assert iteration["escalation_level"] == "agent_action_required"
    assert iteration["requires_user_input"] is False
    assert iteration["requires_domain_review"] is False
    assert iteration["patch_handoff"] is None


def test_verify_only_loop_writes_manifest_iteration_and_decision(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    before_files = _fixture_files(fixture)

    run_dir = run_loop(
        "loop_demo",
        "inspect current loop state",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    assert (run_dir / "run_manifest.json").is_file()
    assert (run_dir / "iteration_001.json").is_file()
    assert (run_dir / "decision.md").is_file()
    assert _fixture_files(fixture) == before_files

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")

    assert manifest["fixture"] == "loop_demo"
    assert manifest["goal"] == "inspect current loop state"
    assert manifest["mode"] == "verify-only"
    assert manifest["final_stop_reason"] == "status_action_required"
    assert iteration["status"]["stage"] == 1
    assert set(iteration["axis_verdicts"]) == {
        "render",
        "static_visual",
        "critique",
        "adjudication",
        "theory",
        "reference_fidelity",
        "story_hierarchy",
        "export",
        "publication_safety",
    }
    assert iteration["adjudication"]["state"] == "missing"
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["patch_evidence"] is None
    assert "status_action_required" in decision


def test_loop_axis_verdicts_record_sources_and_evaluation_state(tmp_path: Path) -> None:
    _make_fixture(tmp_path)

    run_dir = run_loop(
        "loop_demo",
        "inspect axis evidence",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    for axis, record in iteration["axis_verdicts"].items():
        assert "source" in record, axis
        assert "evidence_path" in record, axis
        assert "evaluation_state" in record, axis

    assert iteration["axis_verdicts"]["render"]["source"] == "status.render_state"
    assert iteration["axis_verdicts"]["render"]["evaluation_state"] == "needs_action"
    assert iteration["axis_verdicts"]["static_visual"]["evaluation_state"] == "not_evaluated"
    assert iteration["axis_verdicts"]["static_visual"]["source"] == "verify-only runner"
    assert iteration["axis_verdicts"]["adjudication"]["evaluation_state"] == "not_configured"
    assert iteration["axis_verdicts"]["reference_fidelity"]["evaluation_state"] == "not_configured"
    assert iteration["axis_verdicts"]["theory"]["evaluation_state"] == "not_configured"
    assert iteration["axis_verdicts"]["story_hierarchy"]["evaluation_state"] == "not_configured"


def test_loop_axis_verdicts_mark_configured_unparsed_axes_not_evaluated(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "theory_guard.md").write_text("# theory\n", encoding="utf-8")
    (fixture / "authoring_plan.md").write_text("# plan\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "inspect configured axis evidence",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    theory = iteration["axis_verdicts"]["theory"]
    story = iteration["axis_verdicts"]["story_hierarchy"]
    assert theory["evaluation_state"] == "not_evaluated"
    assert theory["evidence_path"].endswith("examples/loop_demo/theory_guard.md")
    assert story["evaluation_state"] == "not_evaluated"
    assert story["evidence_path"].endswith("examples/loop_demo/authoring_plan.md")


def test_loop_maps_v1_2_quality_axes_to_story_hierarchy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        axis_overrides={
            "message_storyline": _quality_axis("message_storyline"),
            "panel_role_coherence": _quality_axis(
                "panel_role_coherence",
                verdict="needs_patch",
                blocking_items=["C001 - panel role is weak"],
            ),
            "composition_layout": _quality_axis(
                "composition_layout",
                verdict="needs_human",
                blocking_items=["layout judgment requires domain review"],
            ),
            "publication_readiness": _quality_axis(
                "publication_readiness",
                verdict="needs_human",
                recommended_action="human_review",
                blocking_items=["layout judgment requires domain review"],
            ),
        },
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect quality axes",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    story = iteration["axis_verdicts"]["story_hierarchy"]
    assert story["source"] == "critique.quality_axes"
    assert story["evidence_path"] == str(critique)
    assert story["state"] == "needs_human"
    assert story["verdict"] == "needs_human"
    assert story["evaluation_state"] == "blocked"
    assert story["quality_axes"] == [
        "message_storyline",
        "panel_role_coherence",
        "composition_layout",
    ]
    assert story["quality_axis_verdicts"] == {
        "message_storyline": "pass",
        "panel_role_coherence": "needs_patch",
        "composition_layout": "needs_human",
    }


def test_loop_maps_v1_2_reference_fidelity_quality_axis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        axis_overrides={
            "reference_fidelity": _quality_axis(
                "reference_fidelity",
                verdict="needs_patch",
                blocking_items=["C002 - reference topology is weak"],
            ),
            "publication_readiness": _quality_axis(
                "publication_readiness",
                verdict="needs_patch",
                blocking_items=["C002 - reference topology is weak"],
            ),
        },
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect reference quality axis",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    reference = iteration["axis_verdicts"]["reference_fidelity"]
    assert reference["source"] == "critique.quality_axes"
    assert reference["evidence_path"] == str(critique)
    assert reference["state"] == "needs_patch"
    assert reference["verdict"] == "needs_patch"
    assert reference["evaluation_state"] == "needs_action"
    assert reference["quality_axes"] == ["reference_fidelity"]


def test_loop_keeps_missing_reference_gate_ahead_of_quality_axes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_v1_2_critique(
        fixture,
        axis_overrides={
            "reference_fidelity": _quality_axis("reference_fidelity"),
        },
    )
    monkeypatch.setattr(
        fig_loop_mod,
        "infer_stage",
        lambda _example_dir: {
            "stage": 3,
            "render_state": "FRESH",
            "critique_state": "REFERENCE_MISSING",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "workflow_ready": False,
            "golden_ready": False,
            "release_ready": False,
            "final_ready": False,
            "notes": ["critique_reference_missing"],
            "next": "fix declared reference inputs before continuing",
        },
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect reference quality gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    reference = iteration["axis_verdicts"]["reference_fidelity"]
    assert iteration["stop_reason"] == "reference_input_missing"
    assert reference["source"] == "status.notes"
    assert reference["state"] == ["critique_reference_missing"]
    assert reference["verdict"] == "blocked"
    assert reference["evaluation_state"] == "blocked"


def test_loop_maps_v1_2_publication_readiness_to_publication_safety(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        axis_overrides={
            "publication_readiness": _quality_axis(
                "publication_readiness",
                verdict="block",
                recommended_action="block_release",
                blocking_items=["C003 - publication release is blocked"],
            ),
        },
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect publication readiness",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    publication = iteration["axis_verdicts"]["publication_safety"]
    assert publication["source"] == "critique.quality_axes"
    assert publication["evidence_path"] == str(critique)
    assert publication["state"] == "block"
    assert publication["verdict"] == "block"
    assert publication["evaluation_state"] == "blocked"
    assert publication["quality_axes"] == ["publication_readiness"]
    assert publication["quality_axis_recommended_actions"] == {
        "publication_readiness": "block_release"
    }


def test_loop_ignores_malformed_quality_axes_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.2\n"
        "quality_axes: [unterminated\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect malformed quality axes",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    story = iteration["axis_verdicts"]["story_hierarchy"]
    assert story["source"] == "not configured"
    assert story["evaluation_state"] == "not_configured"


def test_loop_records_fresh_adjudication(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(fixture, file_sha256(critique))

    run_dir = run_loop(
        "loop_demo",
        "check adjudication",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "fresh"
    assert iteration["adjudication"]["decision_count"] == 1
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["axis_verdicts"]["adjudication"]["verdict"] == "complete"


def test_loop_status_action_is_agent_action_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "inspect status action",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "agent_action_required"
    assert iteration["requires_user_input"] is False
    assert iteration["requires_domain_review"] is False
    assert "escalation_level: agent_action_required" in decision


def test_loop_human_gate_is_domain_review_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C002",
                "decision": "needs_human",
                "reason": "mechanism arrow semantics may change",
                "patch_target": "",
                "evidence": "",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect human gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["escalation_level"] == "human_review_required"
    assert iteration["requires_user_input"] is True
    assert iteration["requires_domain_review"] is True


def test_loop_force_golden_status_action_is_manual_approval_required(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")
    run_dir = run_loop(
        "loop_demo",
        "inspect tracked golden approval",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration_path = run_dir / "iteration_001.json"
    data = json.loads(iteration_path.read_text(encoding="utf-8"))
    data["stop_reason"] = "status_action_required"
    data["recommended_next_action"] = (
        "tracked golden artifact is intentionally stale; "
        "to roll forward run /fig_export loop_demo --force-golden."
    )

    escalation = _escalation_summary(data)
    assert escalation["escalation_level"] == "manual_approval_required"
    assert escalation["requires_user_input"] is True
    assert escalation["requires_domain_review"] is False


def test_loop_records_stale_adjudication(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique v1\n", encoding="utf-8")
    _write_adjudication(fixture, file_sha256(critique))
    critique.write_text("# critique v2\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "check adjudication",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "stale"
    assert iteration["recommended_next_action"] == "review or refresh critique_adjudication.yaml"
    assert iteration["stop_reason"] == "stale_adjudication"
    _assert_agent_action_required(iteration)


def test_loop_records_invalid_adjudication_without_traceback(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "critique_adjudication.yaml").write_text(
        "schema: [unterminated\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "check invalid adjudication",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "invalid"
    assert "error" in iteration["adjudication"]
    assert iteration["recommended_next_action"] == "fix critique_adjudication.yaml"
    assert iteration["stop_reason"] == "invalid_adjudication"


def test_loop_records_duplicate_adjudication_finding_ids_as_invalid(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "dismiss",
                "reason": "first decision",
                "patch_target": "",
                "evidence": "",
            },
            {
                "finding_id": "C001",
                "decision": "defer",
                "reason": "duplicate decision",
                "patch_target": "",
                "evidence": "",
            },
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "check duplicate adjudication ids",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "invalid"
    assert "duplicate finding_id" in iteration["adjudication"]["error"]
    assert iteration["recommended_next_action"] == "fix critique_adjudication.yaml"
    assert iteration["stop_reason"] == "invalid_adjudication"


def test_loop_identifies_apply_decision_patch_target(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps the arrow",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")

    assert manifest["final_stop_reason"] == "patch_target_recommended"
    assert iteration["stop_reason"] == "patch_target_recommended"
    assert iteration["active_patch_target"] == {
        "finding_id": "C001",
        "patch_target": "panel A label cluster",
        "reason": "label overlaps the arrow",
    }
    assert iteration["axis_verdicts"]["adjudication"]["verdict"] == "actionable"
    assert iteration["recommended_next_action"] == "patch C001: panel A label cluster"
    assert iteration["patch_handoff"] == {
        "target_type": "finding",
        "target_id": "C001",
        "patch_target": "panel A label cluster",
        "reason": "label overlaps the arrow",
        "allowed_edit_scope": [
            "examples/loop_demo/loop_demo.tex",
            "examples/loop_demo/authoring_plan.md",
            "examples/loop_demo/subregion_iteration_log.md",
        ],
        "forbidden_edit_scope": [
            "accepted",
            "golden_contract",
            "examples/loop_demo/exports/",
            "examples/loop_demo/build/",
            "examples/loop_demo/critique.md",
            "unrelated examples",
            "broad refactors",
            "multiple findings in one patch",
        ],
        "required_closeout_checks": [
            "/fig_compile loop_demo",
            "/fig_critique loop_demo when critique freshness requires it",
            "update or recreate examples/loop_demo/critique_adjudication.yaml",
            "preserve unresolved findings",
            "/fig_loop loop_demo --goal <same goal or next goal>",
        ],
        "unresolved_findings_requirement": (
            "Do not delete, rewrite, or hide unresolved critique findings; record only the"
            " selected target decision in critique_adjudication.yaml."
        ),
    }
    assert "active_patch_target: C001 -> panel A label cluster" in decision
    assert "patch_handoff_target: finding C001" in decision


def test_loop_marks_label_spacing_patch_as_auto_patch_candidate(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps arrow; adjust label offset and spacing",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )
    before_files = _fixture_files(fixture)

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert _fixture_files(fixture) == before_files
    assert iteration["stop_reason"] == "patch_target_recommended"
    assert iteration["auto_patch_eligibility"] == {
        "level": "auto_patch_candidate",
        "target_type": "finding",
        "target_id": "C001",
        "allowed_reasons": ["label offset", "text overlap"],
        "blocked_reasons": [],
        "required_evidence": [
            "before compile/export evidence",
            "after compile/export evidence",
            "rollback path",
        ],
        "may_edit": False,
    }


def test_loop_records_pre_patch_evidence_baseline_for_patch_handoff(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    tex_path = fixture / "loop_demo.tex"
    plan_path = fixture / "authoring_plan.md"
    tex_path.write_text("\\documentclass{standalone}\n", encoding="utf-8")
    plan_path.write_text("keep label clear of arrow\n", encoding="utf-8")
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps arrow; adjust label offset",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )
    before_files = _fixture_files(fixture)

    run_dir = run_loop(
        "loop_demo",
        "record pre-patch evidence",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert _fixture_files(fixture) == before_files
    assert iteration["patch_evidence"] == {
        "schema": "figure-agent.patch-evidence.v1",
        "phase": "pre_patch",
        "target_type": "finding",
        "target_id": "C001",
        "verdict": "not_evaluated",
        "may_edit": False,
        "pre_patch": {
            "allowed_edit_scope": [
                {
                    "path": "examples/loop_demo/loop_demo.tex",
                    "exists": True,
                    "sha256": file_sha256(tex_path),
                },
                {
                    "path": "examples/loop_demo/authoring_plan.md",
                    "exists": True,
                    "sha256": file_sha256(plan_path),
                },
                {
                    "path": "examples/loop_demo/subregion_iteration_log.md",
                    "exists": False,
                    "sha256": None,
                },
            ]
        },
        "post_patch_required_verdicts": ["resolved", "unresolved", "regressed", "ambiguous"],
        "rollback_reference": {
            "git_commit": None,
            "restore_strategy": (
                "restore allowed_edit_scope paths to the recorded pre_patch sha256 values"
            ),
        },
    }


def test_loop_records_resolved_post_patch_evidence_from_previous_baseline(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex_path = fixture / "loop_demo.tex"
    tex_path.write_text("\\documentclass{standalone}\n", encoding="utf-8")
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps arrow; adjust label offset",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    baseline_run = run_loop(
        "loop_demo",
        "record pre-patch evidence",
        repo_root=tmp_path,
        runs_root=runs_root,
    )
    baseline_iteration_path = baseline_run / "iteration_001.json"

    tex_path.write_text("\\documentclass{standalone}\n% label moved\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "resolved",
                "reason": "label no longer overlaps arrow",
                "patch_target": "panel A label cluster",
                "evidence": "post-patch critique",
            }
        ],
    )

    post_run = run_loop(
        "loop_demo",
        "verify post-patch evidence",
        repo_root=tmp_path,
        runs_root=runs_root,
    )

    iteration = json.loads((post_run / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["patch_handoff"] is None
    assert iteration["patch_evidence"] is None
    assert iteration["post_patch_evidence"] == {
        "schema": "figure-agent.post-patch-evidence.v1",
        "baseline_path": str(baseline_iteration_path),
        "target_type": "finding",
        "target_id": "C001",
        "verdict": "resolved",
        "allowed_edit_scope_changed": True,
        "changed_allowed_paths": ["examples/loop_demo/loop_demo.tex"],
        "current_decision": "resolved",
        "may_edit": False,
    }


def test_loop_records_unresolved_post_patch_evidence_when_target_still_apply(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex_path = fixture / "loop_demo.tex"
    tex_path.write_text("\\documentclass{standalone}\n", encoding="utf-8")
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps arrow; adjust label offset",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    baseline_run = run_loop(
        "loop_demo",
        "record pre-patch evidence",
        repo_root=tmp_path,
        runs_root=runs_root,
    )

    tex_path.write_text("\\documentclass{standalone}\n% attempted move\n", encoding="utf-8")

    post_run = run_loop(
        "loop_demo",
        "verify unresolved post-patch evidence",
        repo_root=tmp_path,
        runs_root=runs_root,
    )

    iteration = json.loads((post_run / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["patch_handoff"] is not None
    assert iteration["patch_evidence"] is None
    assert iteration["post_patch_evidence"] == {
        "schema": "figure-agent.post-patch-evidence.v1",
        "baseline_path": str(baseline_run / "iteration_001.json"),
        "target_type": "finding",
        "target_id": "C001",
        "verdict": "unresolved",
        "allowed_edit_scope_changed": True,
        "changed_allowed_paths": ["examples/loop_demo/loop_demo.tex"],
        "current_decision": "apply",
        "may_edit": False,
    }


def test_loop_marks_mechanism_patch_as_human_review_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C002",
                "decision": "apply",
                "reason": "causal arrow semantics change the physical mechanism",
                "patch_target": "panel B mechanism arrow",
                "evidence": "critique.md C002",
            }
        ],
    )
    before_files = _fixture_files(fixture)

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert _fixture_files(fixture) == before_files
    assert iteration["stop_reason"] == "patch_target_recommended"
    assert iteration["patch_handoff"] is not None
    assert iteration["auto_patch_eligibility"]["level"] == "human_review_required"
    assert iteration["auto_patch_eligibility"]["may_edit"] is False
    assert iteration["auto_patch_eligibility"]["blocked_reasons"] == [
        "physical mechanism",
        "causal arrow semantics",
    ]


def test_loop_marks_publication_safety_patch_as_human_review_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C003",
                "decision": "apply",
                "reason": "publication safety depends on accepted golden state",
                "patch_target": "accepted publication-safety metadata",
                "evidence": "critique.md C003",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["auto_patch_eligibility"]["level"] == "human_review_required"
    assert iteration["auto_patch_eligibility"]["may_edit"] is False
    assert iteration["auto_patch_eligibility"]["blocked_reasons"] == [
        "accepted/golden/export/build state",
        "publication safety",
    ]


def test_loop_does_not_auto_candidate_generic_label_changes(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C004",
                "decision": "apply",
                "reason": "label wording should be clearer for readers",
                "patch_target": "panel C label text",
                "evidence": "critique.md C004",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["auto_patch_eligibility"] == {
        "level": "patch_assisted_only",
        "target_type": "finding",
        "target_id": "C004",
        "allowed_reasons": [],
        "blocked_reasons": [],
        "required_evidence": [
            "before compile/export evidence",
            "after compile/export evidence",
            "rollback path",
        ],
        "may_edit": False,
    }


def test_loop_does_not_auto_candidate_non_label_offsets(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C005",
                "decision": "apply",
                "reason": "offset the process arrow so it points to the correct species",
                "patch_target": "panel B process arrow",
                "evidence": "critique.md C005",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["auto_patch_eligibility"]["level"] == "patch_assisted_only"
    assert iteration["auto_patch_eligibility"]["allowed_reasons"] == []


def test_loop_does_not_auto_candidate_story_style_changes(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C006",
                "decision": "apply",
                "reason": "story hierarchy style should emphasize the main conclusion more clearly",
                "patch_target": "panel C narrative emphasis",
                "evidence": "critique.md C006",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["auto_patch_eligibility"]["level"] == "patch_assisted_only"
    assert iteration["auto_patch_eligibility"]["allowed_reasons"] == []


def test_loop_stops_when_multiple_apply_decisions_make_patch_target_ambiguous(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "first overlap",
                "patch_target": "panel A",
                "evidence": "critique C001",
            },
            {
                "finding_id": "C002",
                "decision": "apply",
                "reason": "second overlap",
                "patch_target": "panel B",
                "evidence": "critique C002",
            },
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "ambiguous_patch_selection"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["escalation_level"] == "ambiguous_patch_selection"
    assert iteration["recommended_next_action"] == (
        "select exactly one apply decision in critique_adjudication.yaml"
    )


def test_loop_stops_on_human_gated_decision(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C002",
                "decision": "needs_human",
                "reason": "changes the mechanism arrow semantics",
                "patch_target": "",
                "evidence": "",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["human_gate_status"] == "required"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["axis_verdicts"]["publication_safety"]["verdict"] == "human_gate"
    assert iteration["recommended_next_action"] == "human review required for C002"


def test_loop_stops_on_missing_reference_input(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/missing.png\n"
        "panels: []\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect reference gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert manifest["final_stop_reason"] == "reference_input_missing"
    assert iteration["stop_reason"] == "reference_input_missing"
    assert iteration["axis_verdicts"]["reference_fidelity"]["verdict"] == "blocked"
    assert iteration["axis_verdicts"]["reference_fidelity"]["evaluation_state"] == "blocked"
    _assert_agent_action_required(iteration)
    assert iteration["recommended_next_action"] == (
        "fix declared reference inputs before continuing"
    )


def test_loop_uses_active_subregion_when_no_apply_decision(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-2 | current loop | label spacing |\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect active target",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "active_subregion_recommended"
    assert iteration["active_patch_target"] == {
        "finding_id": None,
        "patch_target": "D-2",
        "reason": "active sub-region target",
    }
    assert iteration["patch_handoff"]["target_type"] == "subregion"
    assert iteration["patch_handoff"]["target_id"] == "D-2"
    assert iteration["patch_handoff"]["patch_target"] == "D-2"
    assert iteration["escalation_level"] == "patch_allowed"
    assert iteration["requires_user_input"] is False
    assert iteration["requires_domain_review"] is False


def test_loop_not_accepted_ready_state_is_manual_approval_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)
    status_result = {
        "stage": 4,
        "name": "loop_demo",
        "checks": [],
        "next": (
            "golden fixture is not accepted yet — resolve examples/loop_demo/"
            "QUALITY_AUDIT.md defects, then set accepted: true in spec.yaml."
        ),
        "notes": [],
        "accepted": False,
        "exports_substate": "FRESH",
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "NOT_ACCEPTED",
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_loop_mod, "infer_stage", lambda _example_dir: status_result)

    run_dir = run_loop(
        "loop_demo",
        "inspect approval gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "manual_approval_required"
    assert iteration["requires_user_input"] is True
    assert iteration["requires_domain_review"] is False
    assert iteration["patch_handoff"] is None


@pytest.mark.parametrize(
    ("state", "next_action", "expected_level"),
    (
        (
            "MISSING",
            "final artifact is missing — create or restore the declared polished SVG.",
            "agent_action_required",
        ),
        (
            "INVALID",
            "final artifact is invalid — fix spec.yaml final_artifact.",
            "agent_action_required",
        ),
        (
            "BLOCKED",
            "final artifact requires semantic backport — patch TikZ/briefing/spec.",
            "agent_action_required",
        ),
        (
            "STALE",
            "final artifact is stale — refresh polish/svg_polish_manifest.yaml.",
            "agent_action_required",
        ),
    ),
)
def test_loop_final_artifact_not_ready_blocks_verify_only_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    next_action: str,
    expected_level: str,
) -> None:
    _make_fixture(tmp_path)
    status_result = {
        "stage": 4,
        "name": "loop_demo",
        "checks": [],
        "next": next_action,
        "notes": [f"final_artifact_{state.lower()}"],
        "accepted": True,
        "exports_substate": "FRESH",
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "ACCEPTED",
        "final_artifact_state": state,
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "polish/loop_demo.polished.svg",
        "workflow_ready": True,
        "golden_ready": True,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_loop_mod, "infer_stage", lambda _example_dir: status_result)

    run_dir = run_loop(
        "loop_demo",
        "inspect final artifact gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["recommended_next_action"] == next_action
    assert iteration["escalation_level"] == expected_level
    assert iteration["escalation_level"] != "none"
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert (
        f"- final_artifact_state: polished_svg {state} "
        "polish/loop_demo.polished.svg"
    ) in decision


def test_loop_requires_adjudication_before_active_subregion_for_fresh_critique(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    reference = fixture / "reference" / "target.png"
    reference.parent.mkdir()
    reference.write_bytes(b"png")
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/target.png\n"
        "panels: []\n",
        encoding="utf-8",
    )
    (fixture / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-2 | current loop | label spacing |\n",
        encoding="utf-8",
    )
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: loop_demo\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect active target",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["status"]["critique_state"] == "FRESH"
    assert iteration["stop_reason"] == "missing_adjudication"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["axis_verdicts"]["adjudication"]["evaluation_state"] == "needs_action"
    assert iteration["axis_verdicts"]["reference_fidelity"]["evaluation_state"] == "not_evaluated"
    _assert_agent_action_required(iteration)
    assert iteration["recommended_next_action"] == "create critique_adjudication.yaml"


@pytest.mark.parametrize("critique_state", ["MISSING", "STALE"])
def test_loop_missing_or_stale_critique_is_agent_action_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    critique_state: str,
) -> None:
    _make_fixture(tmp_path)
    status_result = {
        "stage": 4,
        "name": "loop_demo",
        "checks": [],
        "next": f"run /fig_critique loop_demo because critique is {critique_state.lower()}.",
        "notes": [f"critique_{critique_state.lower()}"],
        "accepted": None,
        "exports_substate": "FRESH",
        "render_state": "FRESH",
        "critique_state": critique_state,
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_loop_mod, "infer_stage", lambda _example_dir: status_result)

    run_dir = run_loop(
        "loop_demo",
        "inspect critique freshness",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    _assert_agent_action_required(iteration)


def test_loop_stale_critique_takes_precedence_over_human_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# stale critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "needs_human",
                "reason": "domain review belongs to stale critique",
                "patch_target": "",
                "evidence": "",
            }
        ],
    )
    status_result = {
        "stage": 4,
        "name": "loop_demo",
        "checks": [],
        "next": (
            "tracked golden artifact is stale and reference-grounded critique is stale; "
            "run /fig_critique loop_demo, then /fig_export loop_demo --force-golden."
        ),
        "notes": ["critique_stale"],
        "accepted": None,
        "exports_substate": "FRESH",
        "render_state": "FRESH",
        "critique_state": "STALE",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_loop_mod, "infer_stage", lambda _example_dir: status_result)

    run_dir = run_loop(
        "loop_demo",
        "inspect stale critique precedence",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "fresh"
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["human_gate_status"] == "not_requested"
    assert iteration["recommended_next_action"] == (
        "run /fig_critique loop_demo because critique is stale."
    )
    _assert_agent_action_required(iteration)


def test_loop_non_golden_stale_export_is_agent_action_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)
    status_result = {
        "stage": 4,
        "name": "loop_demo",
        "checks": [],
        "next": "exports are stale — re-run /fig_compile loop_demo then /fig_export loop_demo.",
        "notes": ["stale_export"],
        "accepted": None,
        "exports_substate": "STALE",
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "STALE",
        "acceptance_state": "NOT_DECLARED",
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_loop_mod, "infer_stage", lambda _example_dir: status_result)

    run_dir = run_loop(
        "loop_demo",
        "inspect stale export",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    _assert_agent_action_required(iteration)


def test_loop_marks_status_action_required_when_status_next_blocks_patch(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "inspect stale status",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["status"]["render_state"] == "MISSING"
    assert manifest["final_stop_reason"] == "status_action_required"
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["patch_handoff"] is None
    _assert_agent_action_required(iteration)
    assert iteration["recommended_next_action"] == (
        "run /fig_compile loop_demo to compile the TikZ source."
    )
    assert "stop_reason: status_action_required" in decision


def test_loop_status_action_required_when_resolved_adjudication_but_status_unready(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")
    critique_path = fixture / "critique.md"
    critique_path.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique_path),
        decisions=[
            {
                "finding_id": "C001",
                "decision": "resolved",
                "reason": "already patched",
                "patch_target": "panel label",
                "evidence": "compile passed",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect resolved adjudication with stale status",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["status"]["render_state"] == "MISSING"
    assert manifest["final_stop_reason"] == "status_action_required"
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["patch_handoff"] is None
    assert iteration["recommended_next_action"] == (
        "run /fig_compile loop_demo to compile the TikZ source."
    )
    assert "stop_reason: status_action_required" in decision


def test_loop_fails_for_missing_fixture(tmp_path: Path) -> None:
    with pytest.raises(FigLoopError, match="not found"):
        run_loop(
            "missing",
            "inspect",
            repo_root=tmp_path,
            runs_root=tmp_path / ".scratch" / "fig-loop-runs",
        )


def test_git_mutation_commands_are_rejected() -> None:
    with pytest.raises(FigLoopError, match="git mutation"):
        ensure_safe_command(("git", "commit"))

    with pytest.raises(FigLoopError, match="git mutation"):
        ensure_safe_command(("git", "-C", ".", "commit"))

    assert ensure_safe_command(("uv", "run", "pytest")) == ("uv", "run", "pytest")


def test_main_json_emits_machine_readable_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_dir = tmp_path / "runs" / "loop_demo"
    run_dir.mkdir(parents=True)
    _write_json = fig_loop_mod._write_json
    _write_json(
        run_dir / "run_manifest.json",
        {
            "run_dir": str(run_dir),
            "final_stop_reason": "status_action_required",
        },
    )
    _write_json(
        run_dir / "iteration_001.json",
        {
            "escalation_level": "agent_action_required",
            "patch_handoff": None,
            "auto_patch_eligibility": None,
            "patch_evidence": None,
            "post_patch_evidence": None,
            "status": {
                "final_artifact_state": "NONE",
                "final_artifact_kind": "generated_export",
                "final_artifact_path": "exports/loop_demo.svg",
            },
            "recommended_next_action": "inspect figure state",
        },
    )

    def fake_run_loop(name: str, goal: str, *, runs_root: Path | None = None) -> Path:
        assert name == "loop_demo"
        assert goal == "inspect json"
        assert runs_root == tmp_path / "runs"
        return run_dir

    monkeypatch.setattr(fig_loop_mod, "run_loop", fake_run_loop)

    exit_code = fig_loop_mod.main(
        [
            "loop_demo",
            "--goal",
            "inspect json",
            "--runs-root",
            str(tmp_path / "runs"),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload == {
        "run_dir": str(run_dir),
        "manifest_path": str(run_dir / "run_manifest.json"),
        "iteration_path": str(run_dir / "iteration_001.json"),
        "final_stop_reason": "status_action_required",
        "escalation_level": "agent_action_required",
        "patch_handoff_present": False,
        "auto_patch_eligibility": None,
        "patch_evidence_present": False,
        "post_patch_evidence_verdict": None,
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": "exports/loop_demo.svg",
        "recommended_next_action": "inspect figure state",
    }


def test_main_without_json_keeps_legacy_prose_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_dir = tmp_path / "runs" / "loop_demo"

    def fake_run_loop(name: str, goal: str, *, runs_root: Path | None = None) -> Path:
        assert name == "loop_demo"
        assert goal == "inspect prose"
        assert runs_root == tmp_path / "runs"
        return run_dir

    monkeypatch.setattr(fig_loop_mod, "run_loop", fake_run_loop)

    exit_code = fig_loop_mod.main(
        ["loop_demo", "--goal", "inspect prose", "--runs-root", str(tmp_path / "runs")]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == f"fig_loop.py: wrote verify-only run to {run_dir}\n"
    assert captured.err == ""


def test_main_json_missing_fixture_keeps_existing_error_contract(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_loop(name: str, goal: str, *, runs_root: Path | None = None) -> Path:
        raise FigLoopError(f"examples/{name}/ not found")

    monkeypatch.setattr(fig_loop_mod, "run_loop", fake_run_loop)

    exit_code = fig_loop_mod.main(["missing", "--goal", "inspect", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "fig_loop.py: examples/missing/ not found\n"


def test_main_json_exercises_real_run_loop_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = fig_loop_mod.REPO_ROOT / "examples" / "fig1_overview_v2"
    if not fixture.is_dir():
        pytest.skip("fig1_overview_v2 fixture not present")

    exit_code = fig_loop_mod.main(
        [
            "fig1_overview_v2",
            "--goal",
            "json integration smoke",
            "--runs-root",
            str(tmp_path / "runs"),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    run_dir = Path(payload["run_dir"])
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert payload == {
        "run_dir": str(run_dir),
        "manifest_path": str(manifest_path),
        "iteration_path": str(iteration_path),
        "final_stop_reason": manifest["final_stop_reason"],
        "escalation_level": iteration["escalation_level"],
        "patch_handoff_present": iteration["patch_handoff"] is not None,
        "auto_patch_eligibility": iteration["auto_patch_eligibility"],
        "patch_evidence_present": iteration["patch_evidence"] is not None,
        "post_patch_evidence_verdict": (
            (iteration["post_patch_evidence"] or {}).get("verdict")
        ),
        "final_artifact_state": iteration["status"]["final_artifact_state"],
        "final_artifact_kind": iteration["status"]["final_artifact_kind"],
        "final_artifact_path": iteration["status"]["final_artifact_path"],
        "recommended_next_action": iteration["recommended_next_action"],
    }
