from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_loop as fig_loop_mod  # noqa: E402
from fig_loop import FigLoopError, ensure_safe_command, run_loop  # noqa: E402
from fig_loop_escalation import escalation_summary  # noqa: E402
from fig_loop_markdown import decision_markdown  # noqa: E402
from fig_loop_records import json_stdout_summary, write_json  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402
from reference_aesthetic_metrics import (  # noqa: E402
    build_reference_aesthetic_metrics,
    reference_aesthetic_metrics_summary,
)


def _make_fixture(repo: Path, name: str = "loop_demo") -> Path:
    fixture = repo / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"name: {name}\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    return fixture


def _write_reference_learning_metric_fixture(fixture: Path) -> None:
    build_dir = fixture / "build"
    ref_dir = fixture / "reference"
    build_dir.mkdir(exist_ok=True)
    ref_dir.mkdir(exist_ok=True)
    build = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(build).rectangle((0, 0, 79, 59), fill=(255, 0, 0))
    build.save(build_dir / f"{fixture.name}.png")
    reference = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(reference).rectangle((35, 25, 45, 35), fill=(40, 40, 40))
    reference.save(ref_dir / "style.png")
    (fixture / "critique_reference_pack.yaml").write_text(
        f"""
schema: figure-agent.critique-reference-pack.v1
fixture: {fixture.name}
target_journal: Nature Communications
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: reference/style.png
    role: journal_register
must_match_traits:
  - id: T001
    trait: compact editorial tone
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: poster-like palette
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Does this read as journal-grade?
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/style.png
      roles:
        - style_anchor
        - density_reference
      allowed_transfer:
        - restrained palette
      forbidden_transfer:
        - copy component topology
      rationale: Use as style class only.
""".lstrip(),
        encoding="utf-8",
    )
    build_reference_aesthetic_metrics(fixture)


def _write_previous_basin_iteration(
    runs_root: Path,
    name: str,
    suffix: str,
    *,
    status: dict,
    reference_metrics: dict,
) -> Path:
    run_dir = runs_root / f"20260101-0000{suffix}-{name}"
    run_dir.mkdir(parents=True)
    write_json(
        run_dir / "iteration_001.json",
        {
            "status": status,
            "stop_reason": "human_gate_required",
            "active_patch_target": None,
            "reference_aesthetic_metrics_summary": reference_metrics,
            "recommended_next_action": "human review required",
        },
    )
    write_json(
        run_dir / "run_manifest.json",
        {
            "schema": "figure-agent.fig-loop-run.v1",
            "fixture": name,
            "mode": "verify-only",
            "final_stop_reason": "human_gate_required",
            "iterations": ["iteration_001.json"],
        },
    )
    return run_dir


def _fixture_files(fixture: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(fixture)): path.read_bytes()
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


def _write_external_vision_review(fixture: Path, *, conflict: bool = True) -> None:
    spec_path = fixture / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8") + "external_vision_review: true\n",
        encoding="utf-8",
    )
    build_dir = fixture / "build"
    build_dir.mkdir(exist_ok=True)
    artifact = build_dir / f"{fixture.name}.png"
    artifact.write_bytes(b"png")
    conflicts = (
        """
conflicts:
  - external_finding_id: EV001
    host_finding_id: C001
    summary: external reviewer sees a defect that host critique dismissed
""".rstrip()
        if conflict
        else "conflicts: []"
    )
    (fixture / "external_vision_review.yaml").write_text(
        f"""
schema: figure-agent.external-vision-review.v1
fixture: {fixture.name}
reviewer: Gemini manual second pass
reviewed_at: "2026-05-28T12:00:00Z"
confidence: medium
reviewed_artifact:
  path: build/{fixture.name}.png
  hash: {file_sha256(artifact)}
reviewed_crops: []
findings:
  - id: EV001
    severity: MAJOR
    observation: possible label-target mismatch in high-zoom review
    evidence_ref: build/{fixture.name}.png
    suggested_action: human_review
{conflicts}
""".lstrip(),
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
    schema: str = "figure-agent.critique.v1.2",
    axis_overrides: dict[str, dict] | None = None,
    journal_assessment: dict | None = None,
    critique_input_hash: str | None = None,
    top_tier_audit: dict | None = None,
    editorial_art_direction: dict | None = None,
    micro_defects: list[dict] | None = None,
    crop_audit_log: list[dict] | None = None,
    aesthetic_lever_audit: list[dict] | None = None,
    journal_art_direction_playbook_audit: dict | None = None,
) -> Path:
    axis_overrides = axis_overrides or {}
    quality_axes = {
        axis_name: axis_overrides.get(axis_name, _quality_axis(axis_name))
        for axis_name in QUALITY_AXIS_NAMES
    }
    critique = fixture / "critique.md"
    frontmatter = {
        "schema": schema,
        "fixture": fixture.name,
        "quality_axes": quality_axes,
    }
    if critique_input_hash:
        frontmatter["critique_input_hash"] = critique_input_hash
    if journal_assessment:
        frontmatter["journal_grade_assessment"] = journal_assessment
    if top_tier_audit:
        frontmatter["top_tier_audit"] = top_tier_audit
    if editorial_art_direction:
        frontmatter["editorial_art_direction"] = editorial_art_direction
    if micro_defects is not None:
        frontmatter["micro_defects"] = micro_defects
    if crop_audit_log is not None:
        frontmatter["crop_audit_log"] = crop_audit_log
    if aesthetic_lever_audit is not None:
        frontmatter["aesthetic_lever_audit"] = aesthetic_lever_audit
    if journal_art_direction_playbook_audit is not None:
        frontmatter["journal_art_direction_playbook_audit"] = (
            journal_art_direction_playbook_audit
        )
    critique.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False)
        + "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def _top_tier_audit(
    *,
    overrides: dict[str, dict] | None = None,
) -> dict:
    overrides = overrides or {}
    keys = (
        "first_glance_message",
        "target_journal_fit",
        "novelty_claim_support",
        "figure_caption_coupling",
        "visual_economy",
        "cross_panel_semantic_grammar",
        "reader_misinterpretation_risk",
        "reduction_print_readability",
        "accessibility_color_robustness",
        "aesthetic_coherence",
    )
    return {
        key: overrides.get(
            key,
            {
                "verdict": "pass",
                "finding": f"{key} passes",
                "concrete_fix": "accept_simplification",
                "blocks_high_impact": False,
            },
        )
        for key in keys
    }


def _editorial_art_direction(
    *,
    trigger_path: str = "ready_for_svg_polish",
    overrides: dict[str, dict] | None = None,
) -> dict:
    overrides = overrides or {}
    keys = (
        "hero_focus",
        "narrative_choreography",
        "illustration_readiness",
        "abstraction_consistency",
        "reference_class_fit",
        "visual_identity",
        "claim_payload_fit",
        "aesthetic_risk",
        "tikz_vs_svg_polish_trigger",
        "human_art_direction_gate",
    )
    slots = {
        key: overrides.get(
            key,
            {
                "verdict": "pass",
                "evidence": f"{key} evidence",
                "rationale": f"{key} rationale",
                "concrete_fix": "none",
                "blocks_high_impact": False,
            },
        )
        for key in keys
    }
    slots["tikz_vs_svg_polish_trigger"]["recommended_path"] = trigger_path
    return slots


def _journal_assessment(
    assessed_hash: str,
    *,
    level: str = "solid_manuscript",
    gateable: bool = True,
    with_scores: bool = False,
    overall_score: int = 72,
) -> dict:
    assessment = {
        "schema": "figure-agent.journal-grade-assessment.v1",
        "scoring_mode": "fresh_reaudit",
        "assessed_artifact_hash": assessed_hash,
        "benchmark_level": level,
        "confidence": "high",
        "blockers": [],
        "regression_detected": False,
        "regressions": [],
        "score_is_gateable": gateable,
        "next_quality_bottleneck": "polish",
        "rationale": "current artifact quality level",
    }
    if with_scores:
        assessment.update(
            {
                "overall_score": overall_score,
                "sub_scores": {
                    "storyline": 78,
                    "composition": 70,
                    "component_fidelity": 55,
                    "scientific_plausibility": 82,
                    "label_semantics": 76,
                    "polish": 64,
                    "reference_fidelity": 80,
                    "export_scale_readability": 68,
                },
                "score_rationale": "current artifact only",
            }
        )
    return assessment


def _journal_art_direction_playbook_audit(
    *,
    typography_verdict: str = "weak",
    typography_route: str = "continue_tikz",
    active_human_trigger: bool = False,
) -> dict:
    return {
        "schema": "figure-agent.journal-art-direction-playbook-audit.v1",
        "playbook_id": "nc-main-text",
        "venue_context": "main_text",
        "design_center": [
            {
                "id": "editorial_restraint",
                "verdict": "pass",
                "evidence": "editorial_restraint is visible in current artifact",
                "positive_signal_refs": ["restrained_hero"],
                "anti_pattern_refs": [],
                "route": "none",
                "linked_evidence": ["top_tier_audit.aesthetic_coherence"],
                "rationale": "restrained labels remain subordinate",
            },
            {
                "id": "typography_authority",
                "verdict": typography_verdict,
                "evidence": "typography_authority still has print-scale refinement risk",
                "positive_signal_refs": [],
                "anti_pattern_refs": ["toy_schematic"],
                "route": typography_route,
                "linked_evidence": ["C001"],
                "rationale": "typography_authority needs bounded source polish",
            },
            {
                "id": "whitespace_breathing",
                "verdict": "pass",
                "evidence": "whitespace_breathing is adequate around dense labels",
                "positive_signal_refs": ["print_scale_calm"],
                "anti_pattern_refs": [],
                "route": "none",
                "linked_evidence": ["top_tier_audit.visual_economy"],
                "rationale": "dense region remains readable",
            },
        ],
        "route_rule_applied": {
            "id": "tikz_until_semantics_close",
            "recommended_path": "continue_tikz",
            "rationale": "source-level polish still dominates",
        },
        "human_review_triggers": [
            {
                "id": "taste_direction_conflict",
                "active": active_human_trigger,
                "rationale": "no conflict" if not active_human_trigger else "author choice needed",
            }
        ],
    }


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


def test_loop_surfaces_fresh_reaudit_journal_grade_assessment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique(
        fixture,
        critique_input_hash=critique_hash,
        journal_assessment=_journal_assessment(critique_hash, level="solid_manuscript"),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect journal-grade assessment",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assessment = iteration["journal_grade_assessment"]
    assert assessment["benchmark_level"] == "solid_manuscript"
    assert assessment["scoring_mode"] == "fresh_reaudit"
    assert assessment["score_is_gateable"] is True
    assert assessment["evaluation_state"] == "passed"


def test_loop_surfaces_v1_3_quality_axes_and_journal_grade_assessment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.3",
        critique_input_hash=critique_hash,
        axis_overrides={
            "publication_readiness": _quality_axis(
                "publication_readiness",
                verdict="needs_patch",
                blocking_items=["C001 - polish ceiling"],
            ),
        },
        journal_assessment=_journal_assessment(critique_hash, level="solid_manuscript"),
        top_tier_audit=_top_tier_audit(),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect v1.3 critique ingestion",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    publication = iteration["axis_verdicts"]["publication_safety"]
    assessment = iteration["journal_grade_assessment"]
    assert publication["source"] == "critique.quality_axes"
    assert publication["evidence_path"] == str(critique)
    assert publication["state"] == "needs_patch"
    assert assessment["benchmark_level"] == "solid_manuscript"
    assert assessment["evaluation_state"] == "passed"


def test_loop_surfaces_v1_4_quality_axes_journal_grade_and_top_tier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.4",
        critique_input_hash=critique_hash,
        axis_overrides={
            "publication_readiness": _quality_axis(
                "publication_readiness",
                verdict="needs_patch",
                blocking_items=["C001 - polish ceiling"],
            ),
        },
        journal_assessment=_journal_assessment(critique_hash, level="solid_manuscript"),
        top_tier_audit=_top_tier_audit(),
        micro_defects=[],
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect v1.4 critique ingestion",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    publication = iteration["axis_verdicts"]["publication_safety"]
    assert publication["source"] == "critique.quality_axes"
    assert publication["evidence_path"] == str(critique)
    assert publication["state"] == "needs_patch"
    assert iteration["journal_grade_assessment"]["evaluation_state"] == "passed"
    assert iteration["top_tier_audit_summary"]["source"] == "critique.top_tier_audit"


def test_loop_surfaces_v1_3_top_tier_audit_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.3",
        top_tier_audit=_top_tier_audit(
            overrides={
                "target_journal_fit": {
                    "verdict": "weak",
                    "finding": "not a high-impact hero figure",
                    "concrete_fix": "increase visual ambition",
                    "blocks_high_impact": True,
                },
                "cross_panel_semantic_grammar": {
                    "verdict": "fail",
                    "finding": "same color means two concepts",
                    "concrete_fix": "normalize palette",
                    "blocks_high_impact": True,
                },
                "reduction_print_readability": {
                    "verdict": "needs_human",
                    "finding": "print scale was not verified",
                    "concrete_fix": "review one-column export",
                    "blocks_high_impact": False,
                },
            }
        ),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect top-tier audit",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = iteration["top_tier_audit_summary"]
    assert summary["source"] == "critique.top_tier_audit"
    assert summary["evidence_path"] == str(critique)
    assert summary["slot_count"] == 10
    assert summary["verdict_counts"] == {
        "pass": 7,
        "weak": 1,
        "fail": 1,
        "needs_human": 1,
    }
    assert summary["blocking_high_impact_count"] == 2
    assert summary["blocking_high_impact_slots"] == [
        "target_journal_fit",
        "cross_panel_semantic_grammar",
    ]
    assert summary["weak_or_failed_slots"] == [
        "target_journal_fit",
        "cross_panel_semantic_grammar",
        "reduction_print_readability",
    ]
    assert summary["worst_verdict"] == "fail"
    stdout_summary = json_stdout_summary(run_dir)
    assert stdout_summary["top_tier_audit_summary"] == summary


def test_loop_surfaces_v1_5_editorial_art_direction_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.5",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(
            trigger_path="semantic_backport_required",
            overrides={
                "claim_payload_fit": {
                    "verdict": "fail",
                    "evidence": "novel mechanism is visually secondary",
                    "rationale": "central claim must carry the figure",
                    "concrete_fix": "semantic backport the source before SVG polish",
                    "blocks_high_impact": True,
                }
            },
        ),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect editorial art direction",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = iteration["editorial_art_direction_summary"]
    assert summary["source"] == "critique.editorial_art_direction"
    assert summary["evidence_path"] == str(critique)
    assert summary["worst_verdict"] == "fail"
    assert summary["blocking_high_impact_slots"] == ["claim_payload_fit"]
    assert summary["polish_recommended_path"] == "semantic_backport_required"
    assert summary["polish_trigger_verdict"] == "pass"
    stdout_summary = json_stdout_summary(run_dir)
    assert stdout_summary["editorial_art_direction_summary"] == summary


def test_loop_surfaces_svg_polish_readiness_from_editorial_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.5",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(
            trigger_path="continue_tikz",
            overrides={
                "tikz_vs_svg_polish_trigger": {
                    "verdict": "weak",
                    "evidence": "source-level polish remains",
                    "rationale": "TikZ geometry still needs source repair",
                    "concrete_fix": "continue TikZ iteration first",
                    "blocks_high_impact": False,
                    "recommended_path": "continue_tikz",
                }
            },
        ),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect svg polish readiness",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    readiness = iteration["svg_polish_readiness"]
    assert readiness["schema"] == "figure-agent.svg-polish-readiness.v1"
    assert readiness["can_start_svg_polish"] is False
    assert readiness["recommended_path"] == "continue_tikz"
    assert readiness["next_action"] == "run_fig_loop"
    assert readiness["blocking_items"][0]["id"] == "tikz_vs_svg_polish_trigger"
    stdout_summary = json_stdout_summary(run_dir)
    assert stdout_summary["svg_polish_readiness"] == readiness


def test_loop_svg_polish_readiness_honors_top_tier_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.5",
        top_tier_audit=_top_tier_audit(
            overrides={
                "aesthetic_coherence": {
                    "verdict": "weak",
                    "finding": "visual identity is not high-impact ready",
                    "concrete_fix": "human art-direction review",
                    "blocks_high_impact": True,
                }
            }
        ),
        editorial_art_direction=_editorial_art_direction(
            trigger_path="ready_for_svg_polish"
        ),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect svg polish readiness",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    readiness = iteration["svg_polish_readiness"]
    assert readiness["can_start_svg_polish"] is False
    assert readiness["recommended_path"] == "ready_for_svg_polish"
    assert readiness["next_action"] == "human_art_direction_review"
    assert readiness["blocking_items"][0]["source"] == "top_tier_audit_summary"
    assert readiness["blocking_items"][0]["id"] == "aesthetic_coherence"


def test_loop_surfaces_v1_8_crop_audit_uncertain_verdicts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.8",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(),
        micro_defects=[],
        crop_audit_log=[
            {
                "crop_id": "full_q1",
                "path": "build/audit_crops/full_q1.png",
                "source": "full_render",
                "inspected": True,
                "verdict": "no_defect",
                "linked_micro_defect_id": "",
                "rationale": "full crop inspected",
            },
            {
                "crop_id": "VC001_A",
                "path": "build/audit_crops/visual_clash/VC001_A.png",
                "source": "visual_clash:VC001",
                "inspected": True,
                "verdict": "uncertain",
                "linked_micro_defect_id": "",
                "rationale": "needs another local read",
            },
        ],
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect crop accountability",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = iteration["crop_audit_summary"]
    assert summary["source"] == "critique.crop_audit_log"
    assert summary["evidence_path"] == str(critique)
    assert summary["evaluation_state"] == "needs_action"
    assert summary["uncertain_crop_ids"] == ["VC001_A"]
    stdout_summary = json_stdout_summary(run_dir)
    assert stdout_summary["crop_audit_summary"] == summary


def test_loop_surfaces_v1_11_aesthetic_lever_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.11",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(),
        micro_defects=[],
        crop_audit_log=[],
        aesthetic_lever_audit=[
            {
                "lever_id": "maturity_restraint",
                "dimension": "maturity",
                "verdict": "pass",
                "route": "none",
                "linked_evidence": ["top_tier_audit.aesthetic_coherence"],
            },
            {
                "lever_id": "hero_balance",
                "dimension": "hero_hierarchy",
                "verdict": "weak",
                "route": "tikz_patch",
                "linked_evidence": ["C001"],
            },
        ],
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect aesthetic levers",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = iteration["aesthetic_lever_summary"]
    assert summary["source"] == "critique.aesthetic_lever_audit"
    assert summary["evidence_path"] == str(critique)
    assert summary["evaluation_state"] == "needs_patch"
    assert summary["worst_verdict"] == "weak"
    assert summary["next_aesthetic_bottleneck"] == {
        "lever_id": "hero_balance",
        "dimension": "hero_hierarchy",
        "route": "tikz_patch",
        "linked_evidence": ["C001"],
    }
    stdout_summary = json_stdout_summary(run_dir)
    assert stdout_summary["aesthetic_lever_summary"] == summary


def test_loop_surfaces_v1_12_journal_art_direction_playbook_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.12",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(trigger_path="continue_tikz"),
        micro_defects=[],
        crop_audit_log=[],
        journal_art_direction_playbook_audit=_journal_art_direction_playbook_audit(),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect journal art-direction playbook",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = iteration["journal_art_direction_playbook_summary"]
    assert summary["source"] == "critique.journal_art_direction_playbook_audit"
    assert summary["evidence_path"] == str(critique)
    assert summary["playbook_id"] == "nc-main-text"
    assert summary["venue_context"] == "main_text"
    assert summary["design_center_count"] == 3
    assert summary["verdict_counts"] == {
        "pass": 2,
        "not_applicable": 0,
        "weak": 1,
        "fail": 0,
        "needs_human": 0,
    }
    assert summary["worst_verdict"] == "weak"
    assert summary["evaluation_state"] == "needs_patch"
    assert summary["weak_or_failed_design_center_ids"] == ["typography_authority"]
    assert summary["recommended_path"] == "continue_tikz"
    assert summary["route_rule_applied"] == {
        "id": "tikz_until_semantics_close",
        "recommended_path": "continue_tikz",
    }
    assert summary["active_human_review_triggers"] == []
    stdout_summary = json_stdout_summary(run_dir)
    assert stdout_summary["journal_art_direction_playbook_summary"] == summary


def test_loop_does_not_create_new_stop_boundary_for_journal_playbook_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.12",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(trigger_path="continue_tikz"),
        micro_defects=[],
        crop_audit_log=[],
        journal_art_direction_playbook_audit=_journal_art_direction_playbook_audit(
            typography_verdict="needs_human",
            typography_route="needs_human_art_direction",
            active_human_trigger=True,
        ),
    )
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect journal art-direction playbook",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = iteration["journal_art_direction_playbook_summary"]
    assert summary["evaluation_state"] == "needs_human"
    assert summary["active_human_review_triggers"] == ["taste_direction_conflict"]
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["human_gate_status"] == "not_requested"
    assert iteration["active_patch_target"] is None


def test_loop_surfaces_external_vision_conflict_as_human_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_external_vision_review(fixture, conflict=True)
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect external vision conflict",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    stdout_summary = json_stdout_summary(run_dir)
    summary = iteration["external_vision_review_summary"]

    assert summary["evaluation_state"] == "needs_human"
    assert summary["active_conflicts"] == ["EV001 vs C001"]
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["human_gate_status"] == "required"
    assert iteration["escalation_level"] == "human_review_required"
    assert "external vision conflict" in iteration["recommended_next_action"]
    assert stdout_summary["external_vision_review_summary"] == summary


def test_loop_routes_reference_aesthetic_metric_severe_divergence_to_human_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_reference_learning_metric_fixture(fixture)
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect reference aesthetic divergence",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    stdout_summary = json_stdout_summary(run_dir)
    summary = iteration["reference_aesthetic_metrics_summary"]

    assert summary["evaluation_state"] == "severe_divergence"
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["escalation_level"] == "human_review_required"
    assert "reference aesthetic metric divergence" in iteration["recommended_next_action"]
    assert stdout_summary["reference_aesthetic_metrics_summary"] == summary


def test_loop_detects_repeated_reference_aesthetic_metric_basin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_reference_learning_metric_fixture(fixture)
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    current_metrics = reference_aesthetic_metrics_summary(fixture)
    assert current_metrics is not None
    assert current_metrics["evaluation_state"] == "severe_divergence"
    status = {
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
    }
    _write_previous_basin_iteration(
        runs_root,
        "loop_demo",
        "01",
        status=status,
        reference_metrics=current_metrics,
    )
    _write_previous_basin_iteration(
        runs_root,
        "loop_demo",
        "02",
        status=status,
        reference_metrics=current_metrics,
    )

    run_dir = run_loop(
        "loop_demo",
        "detect repeated aesthetic basin",
        repo_root=tmp_path,
        runs_root=runs_root,
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    stdout_summary = json_stdout_summary(run_dir)

    assert iteration["stop_reason"] == "basin_detected"
    assert iteration["escalation_level"] == "human_review_required"
    assert iteration["basin_summary"]["evaluation_state"] == "basin_detected"
    assert iteration["basin_summary"]["history_count"] == 3
    assert "step out" in iteration["recommended_next_action"]
    assert stdout_summary["basin_summary"] == iteration["basin_summary"]


def test_loop_does_not_detect_basin_without_repeated_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_reference_learning_metric_fixture(fixture)
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "single metric divergence",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))

    assert iteration["stop_reason"] == "human_gate_required"
    assert "basin_summary" not in iteration


def test_loop_ignores_stale_history_for_basin_detection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_reference_learning_metric_fixture(fixture)
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    current_metrics = reference_aesthetic_metrics_summary(fixture)
    assert current_metrics is not None
    stale_status = {
        "render_state": "STALE",
        "critique_state": "FRESH",
        "export_state": "FRESH",
    }
    _write_previous_basin_iteration(
        runs_root,
        "loop_demo",
        "01",
        status=stale_status,
        reference_metrics=current_metrics,
    )
    _write_previous_basin_iteration(
        runs_root,
        "loop_demo",
        "02",
        status=stale_status,
        reference_metrics=current_metrics,
    )

    run_dir = run_loop(
        "loop_demo",
        "ignore stale basin history",
        repo_root=tmp_path,
        runs_root=runs_root,
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))

    assert iteration["stop_reason"] == "human_gate_required"
    assert "basin_summary" not in iteration


def test_loop_does_not_count_warning_metrics_as_severe_basin_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_reference_learning_metric_fixture(fixture)
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(fixture, file_sha256(critique))
    _patch_fresh_status(monkeypatch)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    warning_metrics = {
        "evaluation_state": "warning",
        "blocking_items": [],
        "warning_metrics": [
            {
                "reference_path": "reference/style.png",
                "metric": "palette_histogram_distance",
            }
        ],
    }
    status = {
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
    }
    _write_previous_basin_iteration(
        runs_root,
        "loop_demo",
        "01",
        status=status,
        reference_metrics=warning_metrics,
    )
    _write_previous_basin_iteration(
        runs_root,
        "loop_demo",
        "02",
        status=status,
        reference_metrics=warning_metrics,
    )

    run_dir = run_loop(
        "loop_demo",
        "ignore warning basin history",
        repo_root=tmp_path,
        runs_root=runs_root,
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))

    assert iteration["stop_reason"] == "human_gate_required"
    assert "basin_summary" not in iteration


def test_loop_stale_external_vision_does_not_demote_existing_human_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_external_vision_review(fixture, conflict=False)
    (fixture / "build" / f"{fixture.name}.png").write_bytes(b"changed")
    critique = _write_v1_2_critique(fixture)
    _write_adjudication(
        fixture,
        file_sha256(critique),
        decisions=[
            {
                "finding_id": "C001",
                "decision": "needs_human",
                "reason": "domain decision remains unresolved",
                "patch_target": "",
                "evidence": "human note",
            }
        ],
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect stale external vision with human gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["external_vision_review_summary"]["evaluation_state"] == "stale"
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["escalation_level"] == "human_review_required"


def test_loop_human_gates_v1_11_human_art_direction_lever(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.11",
        top_tier_audit=_top_tier_audit(),
        editorial_art_direction=_editorial_art_direction(),
        micro_defects=[],
        crop_audit_log=[],
        aesthetic_lever_audit=[
            {
                "lever_id": "target_journal_taste",
                "dimension": "maturity",
                "verdict": "needs_human",
                "route": "human_art_direction",
                "linked_evidence": ["editorial_art_direction.human_art_direction_gate"],
            }
        ],
    )
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
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect aesthetic levers",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["aesthetic_lever_summary"]["evaluation_state"] == "needs_human"
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["human_gate_status"] == "required"
    assert iteration["escalation_level"] == "human_review_required"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["auto_patch_eligibility"] is None


def test_loop_marks_hash_mismatched_journal_assessment_not_gateable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_v1_2_critique(
        fixture,
        critique_input_hash="sha256:" + "a" * 64,
        journal_assessment=_journal_assessment("sha256:" + "b" * 64),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect stale journal-grade assessment",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assessment = iteration["journal_grade_assessment"]
    assert assessment["score_is_gateable"] is False
    assert assessment["evaluation_state"] == "stale"


def test_loop_surfaces_advisory_score_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique(
        fixture,
        critique_input_hash=critique_hash,
        journal_assessment=_journal_assessment(
            critique_hash,
            with_scores=True,
            overall_score=72,
        ),
    )
    _write_adjudication(fixture, file_sha256(fixture / "critique.md"))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect score",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assessment = iteration["journal_grade_assessment"]
    assert assessment["overall_score"] == 72
    assert assessment["sub_scores"]["component_fidelity"] == 55
    assert assessment["score_rationale"] == "current artifact only"
    assert assessment["score_policy"] == "advisory_fresh_reaudit_not_gate"
    assert iteration["stop_reason"] == "status_action_required"


def test_loop_surfaces_reference_calibrated_score_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    assessment = _journal_assessment(
        critique_hash,
        with_scores=True,
        overall_score=84,
    )
    assessment["reference_calibration"] = {
        "reference_pack_hash": "sha256:" + "b" * 64,
        "reference_class": "mechanism_schematic",
        "visual_ambition": "high_impact_candidate",
        "score_basis": "current_artifact_vs_pack",
        "limiting_reference_traits": ["T003"],
        "rationale": "T003 limits high-impact promotion",
    }
    print_scale_axis_overrides = {
        "journal_polish": _quality_axis(
            "journal_polish",
            verdict="pass",
        )
        | {"evidence": "print-scale audit: print_178mm.png passes"},
        "publication_readiness": _quality_axis(
            "publication_readiness",
            verdict="pass",
        )
        | {"evidence": "print-scale audit: print_thumbnail.png passes"},
    }
    _write_v1_2_critique(
        fixture,
        schema="figure-agent.critique.v1.9",
        axis_overrides=print_scale_axis_overrides,
        critique_input_hash=critique_hash,
        journal_assessment=assessment,
        top_tier_audit=_top_tier_audit(),
        micro_defects=[],
        editorial_art_direction=_editorial_art_direction(),
        crop_audit_log=[],
    )
    _write_adjudication(fixture, file_sha256(fixture / "critique.md"))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect reference calibrated score",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    summary = json_stdout_summary(run_dir)
    expected = {
        "reference_pack_hash": "sha256:" + "b" * 64,
        "reference_class": "mechanism_schematic",
        "visual_ambition": "high_impact_candidate",
        "score_basis": "current_artifact_vs_pack",
        "limiting_reference_trait_count": 1,
    }
    assert iteration["journal_grade_assessment"]["reference_calibration_summary"] == expected
    assert summary["journal_grade_assessment"]["reference_calibration_summary"] == expected
    assert iteration["stop_reason"] == "status_action_required"


def test_loop_does_not_mark_malformed_score_block_as_advisory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    assessment = _journal_assessment(
        critique_hash,
        with_scores=True,
        overall_score=101,
    )
    _write_v1_2_critique(
        fixture,
        critique_input_hash=critique_hash,
        journal_assessment=assessment,
    )
    _write_adjudication(fixture, file_sha256(fixture / "critique.md"))
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect malformed score",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assessment_record = iteration["journal_grade_assessment"]
    assert assessment_record["overall_score"] == 101
    assert "score_policy" not in assessment_record


def test_loop_marks_high_score_stale_when_assessment_hash_mismatches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    _write_v1_2_critique(
        fixture,
        critique_input_hash="sha256:" + "a" * 64,
        journal_assessment=_journal_assessment(
            "sha256:" + "b" * 64,
            with_scores=True,
            overall_score=99,
        ),
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect stale score",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assessment = iteration["journal_grade_assessment"]
    assert assessment["overall_score"] == 99
    assert assessment["score_is_gateable"] is False
    assert assessment["evaluation_state"] == "stale"
    assert "score_policy" not in assessment


def test_loop_high_score_does_not_override_human_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique(
        fixture,
        critique_input_hash=critique_hash,
        journal_assessment=_journal_assessment(
            critique_hash,
            with_scores=True,
            overall_score=96,
        ),
    )
    _write_adjudication(
        fixture,
        file_sha256(fixture / "critique.md"),
        decisions=[
            {
                "finding_id": "C001",
                "decision": "needs_human",
                "reason": "domain decision",
                "patch_target": "",
                "evidence": "human note",
            }
        ],
    )
    _patch_fresh_status(monkeypatch)

    run_dir = run_loop(
        "loop_demo",
        "inspect human gate score",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["journal_grade_assessment"]["overall_score"] == 96
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["escalation_level"] == "human_review_required"


def test_loop_ignores_malformed_quality_axes_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1.2\nquality_axes: [unterminated\n---\n# critique\n",
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

    escalation = escalation_summary(data)
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
        f"- final_artifact_state: polished_svg {state} polish/loop_demo.polished.svg"
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
        "---\nschema: figure-agent.critique.v1\nfixture: loop_demo\n---\n# critique\n",
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
    write_json(
        run_dir / "run_manifest.json",
        {
            "run_dir": str(run_dir),
            "final_stop_reason": "status_action_required",
        },
    )
    write_json(
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
            "top_tier_audit_summary": None,
            "crop_audit_summary": None,
            "journal_art_direction_playbook_summary": None,
            "audit_evidence": {
                "evaluation_state": "missing_input",
                "blocking_items": ["build/visual_clash.json"],
                "next_action": "/fig_compile loop_demo",
                "reason": "missing build/visual_clash.json",
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
            "top_tier_audit_summary": None,
            "editorial_art_direction_summary": None,
            "crop_audit_summary": None,
            "aesthetic_lever_summary": None,
            "journal_art_direction_playbook_summary": None,
            "external_vision_review_summary": None,
            "audit_evidence": {
                "evaluation_state": "missing_input",
                "blocking_items": ["build/visual_clash.json"],
                "next_action": "/fig_compile loop_demo",
                "reason": "missing build/visual_clash.json",
            },
            "journal_grade_assessment": None,
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


def test_decision_markdown_surfaces_actionable_audit_evidence() -> None:
    decision = decision_markdown(
        name="loop_demo",
        goal="inspect audit evidence",
        status_result={
            "stage": 3,
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "MISSING",
            "final_artifact_kind": "generated_export",
            "final_artifact_state": "NONE",
            "final_artifact_path": "exports/loop_demo.svg",
            "notes": [],
            "audit_evidence": {
                "evaluation_state": "needs_action",
                "blocking_items": ["VC050", "full_q1"],
                "next_action": "/fig_critique loop_demo",
                "reason": "visual-clash candidates are not fully accounted",
            },
        },
        adjudication={"state": "fresh"},
        loop_decision={
            "stop_reason": "status_action_required",
            "active_patch_target": None,
            "recommended_next_action": "/fig_critique loop_demo",
        },
        escalation={"escalation_level": "agent_action_required"},
        patch_handoff=None,
    )

    assert "- audit_evidence_state: needs_action" in decision
    assert "- audit_evidence_blocking: VC050, full_q1" in decision
    assert "- audit_evidence_next: /fig_critique loop_demo" in decision


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
        "post_patch_evidence_verdict": ((iteration["post_patch_evidence"] or {}).get("verdict")),
        "final_artifact_state": iteration["status"]["final_artifact_state"],
        "final_artifact_kind": iteration["status"]["final_artifact_kind"],
        "final_artifact_path": iteration["status"]["final_artifact_path"],
        "top_tier_audit_summary": iteration["top_tier_audit_summary"],
        "editorial_art_direction_summary": iteration["editorial_art_direction_summary"],
        "crop_audit_summary": iteration["crop_audit_summary"],
        "aesthetic_lever_summary": iteration["aesthetic_lever_summary"],
        "journal_art_direction_playbook_summary": iteration[
            "journal_art_direction_playbook_summary"
        ],
        "external_vision_review_summary": iteration["external_vision_review_summary"],
        "audit_evidence": iteration["audit_evidence"],
        "journal_grade_assessment": iteration["journal_grade_assessment"],
        "next_action_summary": iteration["next_action_summary"],
        "recommended_next_action": iteration["recommended_next_action"],
    }


# --- Issue 7E: final-artifact loop surfacing ---------------------------------


def _patch_status_with_final_artifact(
    monkeypatch: pytest.MonkeyPatch,
    *,
    final_artifact_state: str,
    final_artifact_kind: str = "polished_svg",
    final_artifact_path: str | None = "polish/loop_demo.polished.svg",
    workflow_ready: bool = True,
    final_ready: bool = False,
    acceptance_state: str = "ACCEPTED",
    critique_state: str = "NOT_REQUIRED",
    notes: list[str] | None = None,
    next_hint: str | None = None,
) -> None:
    """Inject a synthetic /fig_status vector targeting a final-artifact state.

    Defaults keep the per-fixture render/critique/export gates closed so that
    _loop_decision reaches the final-artifact branch via workflow_ready=true
    + final_ready=false. When ``next_hint`` is omitted, the helper resolves to
    the canonical status_next_policy.py per-state next-action template,
    mirroring what ``infer_stage()`` would emit for a real fixture in the given
    final-artifact state.
    """
    if next_hint is None:
        next_hint = _next_hint_for_final_artifact(final_artifact_state, final_artifact_kind)
    monkeypatch.setattr(
        fig_loop_mod,
        "infer_stage",
        lambda _example_dir: {
            "stage": 4,
            "render_state": "FRESH",
            "critique_state": critique_state,
            "export_state": "FRESH",
            "acceptance_state": acceptance_state,
            "final_artifact_state": final_artifact_state,
            "final_artifact_kind": final_artifact_kind,
            "final_artifact_path": final_artifact_path,
            "workflow_ready": workflow_ready,
            "golden_ready": workflow_ready,
            "release_ready": final_ready,
            "final_ready": final_ready,
            "notes": notes or [],
            "next": next_hint,
        },
    )


def _next_hint_for_final_artifact(final_artifact_state: str, final_artifact_kind: str) -> str:
    """Mirror status_next_policy.py's final-artifact hints for synthetic statuses."""
    from export_freshness import EXPORT_FRESH  # noqa: PLC0415
    from status_next_policy import select_next_hint  # noqa: PLC0415

    if final_artifact_kind != "polished_svg":
        return "inspect figure state"
    if final_artifact_state not in {"MISSING", "INVALID", "STALE", "BLOCKED"}:
        return "inspect figure state"
    return select_next_hint(
        stage=4,
        name="loop_demo",
        notes=[],
        critique_state="NOT_REQUIRED",
        exports_substate=EXPORT_FRESH,
        final_artifact={"state": final_artifact_state},
        accepted=True,
    )


def test_loop_no_polish_opt_in_keeps_existing_behavior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """generated_export kind must not trip the new final-artifact branch."""
    _make_fixture(tmp_path)
    _patch_status_with_final_artifact(
        monkeypatch,
        final_artifact_state="NONE",
        final_artifact_kind="generated_export",
        final_artifact_path="exports/loop_demo.svg",
        final_ready=True,
    )

    run_dir = run_loop(
        "loop_demo",
        "no-polish backward compat",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "verify_only_complete"
    assert iteration["status"]["final_artifact_kind"] == "generated_export"


def test_loop_blocks_verify_only_complete_when_final_artifact_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_fixture(tmp_path)
    _patch_status_with_final_artifact(monkeypatch, final_artifact_state="MISSING")

    run_dir = run_loop(
        "loop_demo",
        "polish missing",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["stop_reason"] != "verify_only_complete"
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "agent_action_required"
    action = iteration["recommended_next_action"]
    assert "polish" in action.lower()
    assert "polish/loop_demo.polished.svg" in action or "polish/svg_polish_manifest.yaml" in action
    assert "MISSING" in decision
    assert "polished_svg" in decision


def test_loop_blocks_verify_only_complete_when_final_artifact_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_fixture(tmp_path)
    _patch_status_with_final_artifact(monkeypatch, final_artifact_state="INVALID")

    run_dir = run_loop(
        "loop_demo",
        "polish invalid",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "agent_action_required"
    action = iteration["recommended_next_action"]
    assert "invalid" in action.lower()
    assert "manifest" in action.lower() or "spec" in action.lower()


def test_loop_blocks_verify_only_complete_when_final_artifact_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_fixture(tmp_path)
    _patch_status_with_final_artifact(monkeypatch, final_artifact_state="STALE")

    run_dir = run_loop(
        "loop_demo",
        "polish stale",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "agent_action_required"
    action = iteration["recommended_next_action"]
    assert "stale" in action.lower() or "refresh" in action.lower()
    assert "manifest" in action.lower()


def test_loop_routes_to_semantic_backport_when_final_artifact_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BLOCKED routes to semantic backport, not generic manifest repair."""
    _make_fixture(tmp_path)
    _patch_status_with_final_artifact(monkeypatch, final_artifact_state="BLOCKED")

    run_dir = run_loop(
        "loop_demo",
        "polish blocked",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "agent_action_required"
    action = iteration["recommended_next_action"].lower()
    assert "semantic backport" in action
    # Backport target must include source families, not just manifest.
    assert "tikz" in action and "briefing" in action and "spec" in action
    # Decision.md must mention BLOCKED so a reviewer sees the state.
    assert "BLOCKED" in decision


def test_loop_surfaces_final_artifact_fresh_in_decision_and_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FRESH polished SVG must not block verify_only_complete by itself."""
    _make_fixture(tmp_path)
    _patch_status_with_final_artifact(
        monkeypatch,
        final_artifact_state="FRESH",
        final_ready=True,
    )

    run_dir = run_loop(
        "loop_demo",
        "polish fresh",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["stop_reason"] == "verify_only_complete"
    assert iteration["status"]["final_artifact_state"] == "FRESH"
    assert iteration["status"]["final_artifact_kind"] == "polished_svg"
    assert "polished_svg" in decision
    assert "FRESH" in decision


def test_loop_remains_non_mutating_for_final_artifact_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Driving the new branches must not mutate the fixture."""
    fixture = _make_fixture(tmp_path)
    before = _fixture_files(fixture)

    for state in ("MISSING", "INVALID", "STALE", "BLOCKED", "FRESH"):
        _patch_status_with_final_artifact(
            monkeypatch,
            final_artifact_state=state,
            final_ready=(state == "FRESH"),
        )
        run_loop(
            "loop_demo",
            f"non-mutation/{state}",
            repo_root=tmp_path,
            runs_root=tmp_path / ".scratch" / "fig-loop-runs",
        )

    assert _fixture_files(fixture) == before
