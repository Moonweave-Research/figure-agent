from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig3_resistance_mechanism"
REVIEW = FIXTURE / "review" / "failure-first"
PACKET = REVIEW / "input_packet.yaml"
BOUNDARY = REVIEW / "semantic_object_relation_boundary.yaml"
RENDER_RECEIPT = REVIEW / "render_receipt.yaml"
RAW_RUN = REVIEW / "raw.yaml"
RAW_PROMPT = REVIEW / "raw_authoring_prompt.md"
RAW_SOURCE = REVIEW / "raw_generated.tex"
RAW_MODEL_CONTRACT = REVIEW / "model_contract.yaml"
RAW_BUDGET_CONTRACT = REVIEW / "budget_contract.yaml"
RAW_AUTHORITY_PACKET = REVIEW / "raw_authority_packet.yaml"
RAW_RENDER_RECEIPT = REVIEW / "raw_render_receipt.yaml"
RAW_SELECTOR_REGISTRY = REVIEW / "raw_selector_registry.yaml"
STYLE_CONTROL_RUN = REVIEW / "style_control.yaml"
STYLE_CONTROL_SOURCE = REVIEW / "style_control_generated.tex"
STYLE_CONTROL_RENDER_RECEIPT = REVIEW / "style_control_render_receipt.yaml"
VERIFIED_RUN = REVIEW / "verified.yaml"
VERIFIED_SOURCE = REVIEW / "verified_generated.tex"
VERIFIED_RENDER_RECEIPT = REVIEW / "verified_render_receipt.yaml"
VERIFIED_SELECTOR_REGISTRY = REVIEW / "verified_selector_registry.yaml"
VERIFIED_ATTEMPT1_SOURCE = REVIEW / "verified_attempt1_style_path_failed.tex"
VERIFIED_ATTEMPT1_RECORD = REVIEW / "verified_attempt1_style_path_failed.yaml"
REPAIRED_ATTEMPT = REVIEW / "repaired_layout_lane_attempt.yaml"
REPAIRED_AUTHORITY_PACKET = REVIEW / "repaired_authority_packet.yaml"
REPAIRED_PROMPT = REVIEW / "repaired_authoring_prompt.md"
REPAIRED_SOURCE = REVIEW / "repaired_generated.tex"
REPAIRED_RENDER_RECEIPT = REVIEW / "repaired_render_receipt.yaml"
REPAIRED_REGION_CONTRACT = REVIEW / "repaired_posthoc_region_contract.yaml"
REPAIRED_REGION_REPORT = REVIEW / "repaired_posthoc_region_report.json"
REPAIRED_REGION_EVALUATION = REVIEW / "repaired_posthoc_region_evaluation.yaml"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_pending_paths(repo_root: Path) -> set[str]:
    commands = (
        ("diff", "--name-only", "--cached"),
        ("diff", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    )
    pending: set[str] = set()
    for command in commands:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *command],
            check=True,
            capture_output=True,
            text=True,
        )
        pending.update(path for path in result.stdout.splitlines() if path)
    return pending


def _scope_violations(pending_paths: set[str], allowed_paths: set[str]) -> set[str]:
    return pending_paths - allowed_paths


def _tool_version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return next(line for line in (result.stdout + result.stderr).splitlines() if line)


def _compile_receipt_outputs() -> dict[str, object]:
    receipt = yaml.safe_load(RENDER_RECEIPT.read_text(encoding="utf-8"))
    subprocess.run(
        receipt["compile_command"], cwd=PLUGIN_ROOT, check=True, capture_output=True, text=True
    )
    return receipt


def _pdf_content_signature(path: Path) -> dict[str, object]:
    text_result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True
    )
    normalized_text = "\n".join(line.rstrip() for line in text_result.stdout.splitlines()).strip() + "\n"
    info_result = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True
    )
    page_count = int(next(line.split(":", 1)[1] for line in info_result.stdout.splitlines() if line.startswith("Pages:")).strip())
    return {
        "schema": "figure-agent.pdf-content-signature.v1",
        "extraction": "pdftotext-layout-trim-right-lines-v1",
        "normalized_text_sha256": "sha256:" + hashlib.sha256(normalized_text.encode()).hexdigest(),
        "page_count": page_count,
    }


def test_fig3_resistance_failure_first_packet_hash_binds_current_authority() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))

    assert packet["schema"] == "figure-agent.failure-first-input-packet.v1"
    assert packet["fixture"] == "fig3_resistance_mechanism"
    assert packet["generation_status"] == "not_run"
    assert packet["panels"] == ["A", "B"]
    assert packet["publication_acceptance"] == "not_claimed"
    assert packet["forbidden_import_patterns"] == [
        "examples/fig1_",
        "experiments/python_svg_semantic_fig1",
        "fig1_hybrid_complex_panel_pilot",
    ]
    _compile_receipt_outputs()

    roles = [item["role"] for item in packet["authoritative_inputs"]]
    assert roles == [
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
        "editable_source",
        "rendered_png",
        "rendered_pdf",
        "critique",
        "critique_adjudication",
        "semantic_boundary",
        "scope_protection",
        "render_receipt",
    ]
    assert len(roles) == len(set(roles))
    for item in packet["authoritative_inputs"]:
        relative_path = Path(item["path"])
        assert not relative_path.is_absolute()
        assert ".." not in relative_path.parts
        assert relative_path.as_posix() == item["path"]
        path = (FIXTURE / relative_path).resolve()
        assert path.is_relative_to(FIXTURE.resolve())
        assert path.relative_to(FIXTURE.resolve()).as_posix() == item["path"]
        assert path.is_file()
        if item["role"] == "rendered_pdf":
            assert "sha256" not in item
            assert item["content_signature"]["schema"] == "figure-agent.pdf-content-signature.v1"
        else:
            assert item["sha256"] == _sha256(path)

    source_roles = {
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
        "editable_source",
        "semantic_boundary",
    }
    for item in packet["authoritative_inputs"]:
        if item["role"] in source_roles:
            contents = (FIXTURE / item["path"]).read_text(encoding="utf-8")
            for forbidden in packet["forbidden_import_patterns"]:
                assert forbidden not in contents


def test_fig3_resistance_declares_two_panel_semantic_object_relation_boundary() -> None:
    boundary = yaml.safe_load(BOUNDARY.read_text(encoding="utf-8"))

    assert boundary["schema"] == "figure-agent.semantic-object-relation-boundary.v1"
    assert boundary["fixture"] == "fig3_resistance_mechanism"
    assert boundary["declared_scope"] == "schematic_half_of_composite_fig3"
    assert set(boundary["panels"]) == {"A", "B"}
    assert boundary["panels"]["A"]["required_objects"] == [
        "applied_bias_cell",
        "sign_agnostic_carrier_walk",
        "repeated_trap_release",
        "current_decay_relation",
    ]
    assert boundary["panels"]["A"]["required_relations"] == [
        "applied_bias_cell_encloses_disordered_sulfur_polymer_film",
        "carrier_walk_contains_repeated_capture_and_release",
        "repeated_trapping_causes_transient_current_decay",
        "current_decay_implies_resistance_increase_under_applied_voltage",
    ]
    assert boundary["panels"]["B"]["required_objects"] == [
        "discrete_s60_distribution",
        "continuous_broad_s80_distribution",
        "n_breadth_span",
        "rho60s_magnitude_span",
    ]
    assert boundary["panels"]["B"]["required_relations"] == [
        "sulfur_increase_evolves_discrete_to_continuous_broad_distribution",
        "n_breadth_span_measures_distribution_width",
        "rho60s_magnitude_span_is_orthogonal_to_n_breadth",
        "distribution_breadth_is_not_trap_density",
    ]
    assert boundary["cross_panel_relations"] == [
        "repeated_trapping_causes_transient_current_decay",
        "n_encodes_distribution_breadth_not_density",
        "rho60s_is_orthogonal_magnitude_cue",
        "sulfur_increase_evolves_discrete_to_continuous_broad_distribution",
    ]
    assert boundary["out_of_scope_claims"] == [
        "carrier_polarity",
        "trap_chemistry",
        "quantitative_measured_data",
        "spatial_trap_network",
    ]


def test_fig3_resistance_scope_allows_one_bounded_source_repair_and_protects_history() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    scope = yaml.safe_load((REVIEW / "scope_protection.yaml").read_text(encoding="utf-8"))

    assert scope["schema"] == "figure-agent.failure-first-scope-protection.v1"
    assert scope["fixture"] == "fig3_resistance_mechanism"
    assert scope["authorized_change_mode"] == "bounded_source_repair_and_review_artifacts"
    assert scope["allowed_review_paths"] == [
        "fig3_resistance_mechanism.tex",
        "spec.yaml",
        "review/failure-first/input_packet.yaml",
        "review/failure-first/semantic_object_relation_boundary.yaml",
        "review/failure-first/scope_protection.yaml",
        "review/failure-first/render_receipt.yaml",
        "review/failure-first/model_contract.yaml",
        "review/failure-first/budget_contract.yaml",
        "review/failure-first/raw_authoring_prompt.md",
        "review/failure-first/raw_authority_packet.yaml",
        "review/failure-first/raw_generated.tex",
        "review/failure-first/raw_generated.pdf",
        "review/failure-first/raw_generated.png",
        "review/failure-first/raw_render_receipt.yaml",
        "review/failure-first/raw_selector_registry.yaml",
        "review/failure-first/raw.yaml",
        "review/failure-first/raw.transcript.json",
        "review/failure-first/style_control_generated.tex",
        "review/failure-first/style_control_generated.pdf",
        "review/failure-first/style_control_generated.png",
        "review/failure-first/style_control_render_receipt.yaml",
        "review/failure-first/style_control.yaml",
        "review/failure-first/verified_generated.tex",
        "review/failure-first/verified_generated.pdf",
        "review/failure-first/verified_generated.png",
        "review/failure-first/verified_render_receipt.yaml",
        "review/failure-first/verified.yaml",
        "review/failure-first/verified.transcript.json",
        "review/failure-first/verified_selector_registry.yaml",
        "review/failure-first/verified_attempt1_style_path_failed.tex",
        "review/failure-first/verified_attempt1_style_path_failed.yaml",
        "review/failure-first/layout_lane_contract.yaml",
        "review/failure-first/raw_layout_lane_report.json",
        "review/failure-first/verified_layout_lane_report.json",
        "review/failure-first/repaired_authoring_prompt.md",
        "review/failure-first/repaired_authority_packet.yaml",
        "review/failure-first/repaired_generated.tex",
        "review/failure-first/repaired_generated.pdf",
        "review/failure-first/repaired_generated.png",
        "review/failure-first/repaired_layout_lane_report.json",
        "review/failure-first/repaired_visual_clash.json",
        "review/failure-first/repaired_undeclared_geometry.json",
        "review/failure-first/repaired_label_hyphenation.json",
        "review/failure-first/repaired_render_receipt.yaml",
        "review/failure-first/repaired_layout_lane_attempt.yaml",
        "review/failure-first/repaired_posthoc_region_contract.yaml",
        "review/failure-first/repaired_posthoc_region_report.json",
        "review/failure-first/repaired_posthoc_region_evaluation.yaml",
    ]
    assert scope["allowed_repository_paths"] == [
        "plugins/figure-agent/bin/fig-agent",
        "plugins/figure-agent/docs/execution-plan.md",
        "plugins/figure-agent/scripts/authoring_context_pack.py",
        "plugins/figure-agent/scripts/checks/check_layout_drift.py",
        "plugins/figure-agent/scripts/visual_finding_artifacts.py",
        "plugins/figure-agent/tests/test_authoring_context_pack.py",
        "plugins/figure-agent/tests/test_check_layout_drift.py",
        "plugins/figure-agent/tests/test_fig3_resistance_failure_first.py",
        "plugins/figure-agent/tests/test_visual_finding_artifacts.py",
    ]
    assert scope["protected_paths"] == [
        "briefing.md",
        "authoring_contract.md",
        "panel_goals.md",
        "critique.md",
        "critique_adjudication.yaml",
        "../fig3_trap_schematic_slice3_semantic/**",
        "../fig1_*/**",
        "../fig1_direct_svg_cleanroom_baseline/**",
        "../../experiments/python_svg_semantic_fig1/**",
    ]

    scope_item = next(
        item for item in packet["authoritative_inputs"] if item["role"] == "scope_protection"
    )
    assert scope_item["path"] == "review/failure-first/scope_protection.yaml"
    assert scope_item["sha256"] == _sha256(REVIEW / "scope_protection.yaml")
    receipt_item = next(
        item for item in packet["authoritative_inputs"] if item["role"] == "render_receipt"
    )
    assert receipt_item["path"] == "review/failure-first/render_receipt.yaml"
    assert receipt_item["sha256"] == _sha256(RENDER_RECEIPT)


def test_fig3_raw_clean_room_baseline_is_hash_bound_but_not_publication_accepted() -> None:
    run = yaml.safe_load(RAW_RUN.read_text(encoding="utf-8"))
    receipt = run["generation_receipt"]

    assert run["schema"] == "figure-agent.failure-ablation-run.v1"
    assert run["variant"] == "raw"
    assert run["figure_family"] == "fig3_resistance_mechanism"
    assert run["model_contract_hash"] == _sha256(RAW_MODEL_CONTRACT)
    assert run["input_packet_hash"] == _sha256(RAW_AUTHORITY_PACKET)
    assert run["budget_contract_hash"] == _sha256(RAW_BUDGET_CONTRACT)
    assert run["clean_reproduction"] is False
    assert run["reproduction"]["project_compile"]["result"] == "blocked_by_style_lock"
    assert run["selector_registry_hash"] == _sha256(RAW_SELECTOR_REGISTRY)
    assert run["render_receipt_hash"] == _sha256(RAW_RENDER_RECEIPT)
    assert run["human_verdict"] == {"state": "pending"}
    assert run["publication_acceptance"] == "not_claimed"
    assert run["findings"] == [
        {
            "id": "RAW_STYLE_CONTRACT_MISSING",
            "failure_class": "style",
            "observation_scale": "whole",
            "review_outcome": "confirmed_defect",
            "attribution_state": "exact",
            "selector_id": "document.preamble_and_palette",
        },
        {
            "id": "RAW_SINGLE_DEEP_STATE_OMITTED",
            "failure_class": "semantic",
            "observation_scale": "panel",
            "review_outcome": "confirmed_defect",
            "attribution_state": "exact",
            "selector_id": "panel_b.s60_single_deep_state",
        },
        {
            "id": "RAW_TEXT_AND_LABEL_OVERFLOW",
            "failure_class": "geometry",
            "observation_scale": "whole",
            "review_outcome": "confirmed_defect",
            "attribution_state": "exact",
            "selector_id": "whole.layout_text_extents",
        },
    ]
    assert receipt["starting_artifact_path"] == RAW_PROMPT.name
    assert receipt["generated_artifact_path"] == RAW_SOURCE.name
    for kind, path in (("starting", RAW_PROMPT), ("generated", RAW_SOURCE)):
        assert receipt[f"{kind}_artifact_sha256"] == _sha256(path)
    transcript = RAW_RUN.with_suffix(".transcript.json")
    assert receipt["transcript_path"] == transcript.name
    assert receipt["transcript_sha256"] == _sha256(transcript)
    model_contract = yaml.safe_load(RAW_MODEL_CONTRACT.read_text(encoding="utf-8"))
    authority_packet = yaml.safe_load(RAW_AUTHORITY_PACKET.read_text(encoding="utf-8"))
    raw_source = RAW_SOURCE.read_text(encoding="utf-8")
    assert authority_packet["schema"] == "figure-agent.raw-authority-packet.v1"
    assert [item["role"] for item in authority_packet["authoritative_inputs"]] == [
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
    ]
    for item in authority_packet["authoritative_inputs"]:
        path = FIXTURE / item["path"]
        assert item["sha256"] == _sha256(path)
        for forbidden in model_contract["forbidden_import_patterns"]:
            assert forbidden not in item["path"]
            assert forbidden not in path.read_text(encoding="utf-8")
    for forbidden in model_contract["forbidden_import_patterns"]:
        assert forbidden not in raw_source

    selectors = yaml.safe_load(RAW_SELECTOR_REGISTRY.read_text(encoding="utf-8"))
    assert selectors["source_sha256"] == _sha256(RAW_SOURCE)
    selector_ids = {item["id"] for item in selectors["selectors"]}
    assert selector_ids == {item["selector_id"] for item in run["findings"]}

    render = yaml.safe_load(RAW_RENDER_RECEIPT.read_text(encoding="utf-8"))
    assert render["input_authority_packet_sha256"] == _sha256(RAW_AUTHORITY_PACKET)
    assert render["source_sha256"] == _sha256(RAW_SOURCE)
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    assert render["publication_acceptance"] == "not_claimed"


def test_fig3_style_control_injects_only_the_paper_style_contract() -> None:
    run = yaml.safe_load(STYLE_CONTROL_RUN.read_text(encoding="utf-8"))
    source = STYLE_CONTROL_SOURCE.read_text(encoding="utf-8")
    render = yaml.safe_load(STYLE_CONTROL_RENDER_RECEIPT.read_text(encoding="utf-8"))

    assert run["schema"] == "figure-agent.style-control-run.v1"
    assert run["control_kind"] == "deterministic_style_contract_injection"
    assert run["figure_family"] == "fig3_resistance_mechanism"
    assert run["source_derivation"] == {
        "from_path": RAW_SOURCE.name,
        "from_sha256": _sha256(RAW_SOURCE),
        "permitted_transformations": [
            "paper_preamble_and_palette",
            "paper_font_hierarchy",
        ],
    }
    assert run["clean_reproduction"] is True
    assert run["human_verdict"] == {"state": "pending"}
    assert run["publication_acceptance"] == "not_claimed"
    assert "\\usepackage{polymer-paper-preamble}" in source
    assert "\\definecolor" not in source
    assert "\\tiny" not in source
    assert "\\scriptsize" not in source
    for invariant in (
        "sign-agnostic carrier",
        "repeatedly trapped / released",
        "I(t)\\propto t^{-n}",
        "S60",
        "S80",
        "$n$ = breadth",
        "magnitude",
    ):
        assert invariant in source
    assert render["source_sha256"] == _sha256(STYLE_CONTROL_SOURCE)
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    assert render["publication_acceptance"] == "not_claimed"


def test_fig3_verified_llm_retry_is_receipt_bound_to_the_same_clean_room_inputs() -> None:
    raw_run = yaml.safe_load(RAW_RUN.read_text(encoding="utf-8"))
    run = yaml.safe_load(VERIFIED_RUN.read_text(encoding="utf-8"))
    source = VERIFIED_SOURCE.read_text(encoding="utf-8")
    receipt = run["generation_receipt"]
    render = yaml.safe_load(VERIFIED_RENDER_RECEIPT.read_text(encoding="utf-8"))

    assert run["schema"] == "figure-agent.failure-ablation-run.v1"
    assert run["variant"] == "verified"
    for field in (
        "model_contract_hash",
        "input_packet_hash",
        "budget_contract_hash",
        "figure_family",
    ):
        assert run[field] == raw_run[field]
    assert run["comparison_eligibility"] == "feedback_guided_not_equal_input"
    assert run["selector_registry_hash"] == _sha256(VERIFIED_SELECTOR_REGISTRY)
    assert receipt["model_id"] == raw_run["generation_receipt"]["model_id"]
    assert receipt["source_commit"] == raw_run["generation_receipt"]["source_commit"]
    assert receipt["starting_artifact_path"] == RAW_PROMPT.name
    assert receipt["starting_artifact_sha256"] == _sha256(RAW_PROMPT)
    assert receipt["generated_artifact_path"] == VERIFIED_SOURCE.name
    assert receipt["generated_artifact_sha256"] == _sha256(VERIFIED_SOURCE)
    assert receipt["transcript_sha256"] == _sha256(VERIFIED_RUN.with_suffix(".transcript.json"))
    assert run["clean_reproduction"] is True
    assert run["human_verdict"] == {"state": "pending"}
    assert run["publication_acceptance"] == "not_claimed"
    assert "\\usepackage{polymer-paper-preamble}" in source
    assert "\\definecolor" not in source
    assert "\\tiny" not in source
    assert "\\scriptsize" not in source
    for invariant in (
        "carrier (sign-agnostic)",
        "repeated trap $\\leftrightarrow$ release",
        "I(t)\\propto t^{-n}",
        "S60",
        "single deep",
        "S80",
        "continuous broad",
        "$n$ = breadth",
        "magnitude",
    ):
        assert invariant in source
    assert render["source_sha256"] == _sha256(VERIFIED_SOURCE)
    assert render["visual_clash_candidates"] == 21
    assert render["undeclared_geometry_candidates"] == 37
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    assert render["publication_acceptance"] == "not_claimed"
    selectors = yaml.safe_load(VERIFIED_SELECTOR_REGISTRY.read_text(encoding="utf-8"))
    assert selectors["source_sha256"] == _sha256(VERIFIED_SOURCE)
    assert {item["id"] for item in selectors["selectors"]} == {
        item["selector_id"] for item in run["findings"]
    }


def test_fig3_first_verified_retry_preserves_the_style_path_failure() -> None:
    attempt = yaml.safe_load(VERIFIED_ATTEMPT1_RECORD.read_text(encoding="utf-8"))

    assert attempt == {
        "schema": "figure-agent.clean-room-attempt.v1",
        "attempt": "verified_attempt1",
        "source_path": VERIFIED_ATTEMPT1_SOURCE.name,
        "source_sha256": _sha256(VERIFIED_ATTEMPT1_SOURCE),
        "project_compile": {
            "result": "failed",
            "failure_class": "reproducibility",
            "failure": "styles/polymer-paper-preamble.sty not found from nested review path",
        },
        "publication_acceptance": "not_claimed",
    }


def test_fig3_constraint_guided_repaired_attempt_records_failure_without_ablation_claim() -> None:
    attempt = yaml.safe_load(REPAIRED_ATTEMPT.read_text(encoding="utf-8"))
    render = yaml.safe_load(REPAIRED_RENDER_RECEIPT.read_text(encoding="utf-8"))

    assert attempt["schema"] == "figure-agent.constraint-guided-attempt.v1"
    assert attempt["comparison_eligibility"] == "constraint_guided_iterative_not_ablation"
    assert attempt["input_authority_packet_sha256"] == _sha256(
        REPAIRED_AUTHORITY_PACKET
    )
    assert attempt["starting_prompt"]["sha256"] == _sha256(REPAIRED_PROMPT)
    assert attempt["generated_source"]["sha256"] == _sha256(REPAIRED_SOURCE)
    assert attempt["authoring_trace"]["feedback_rounds"] == 4
    assert attempt["machine_outcome"]["strict_compile"] == (
        "failed_detector_gate_after_render"
    )
    assert attempt["machine_outcome"]["declared_layout_lane"] == (
        "failed_0.013_lt_0.015"
    )
    assert attempt["publication_acceptance"] == "not_claimed"

    assert render["source_sha256"] == _sha256(REPAIRED_SOURCE)
    assert render["machine_findings"]["layout_lane"] == {
        "rule_id": "panel_a_narrative_clear_of_bias_marker",
        "measured_clearance": 0.013,
        "required_clearance": 0.015,
        "result": "failed",
    }
    assert render["strict_compile_result"] == "failed_detector_gate_after_render"
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    for evidence in render["evidence"]:
        assert evidence["sha256"] == _sha256(REVIEW / evidence["path"])
    assert render["publication_acceptance"] == "not_claimed"


def test_fig3_repaired_render_exposes_panel_and_plot_region_failures() -> None:
    contract = yaml.safe_load(REPAIRED_REGION_CONTRACT.read_text(encoding="utf-8"))
    report = json.loads(REPAIRED_REGION_REPORT.read_text(encoding="utf-8"))
    evaluation = yaml.safe_load(
        REPAIRED_REGION_EVALUATION.read_text(encoding="utf-8")
    )

    assert contract["schema"] == "figure-agent.layout-lanes.v1"
    assert contract["evaluation_mode"] == "posthoc_not_generation_input"
    assert report["failure_count"] == 2
    assert {
        result["rule_id"]: result["status"] for result in report["results"]
    } == {
        "panel_a_title_contained": "violation",
        "panel_a_decay_note_clear_of_plot": "violation",
    }
    assert contract["publication_acceptance"] == "not_claimed"
    assert evaluation["schema"] == "figure-agent.posthoc-layout-evaluation.v1"
    assert evaluation["source_sha256"] == _sha256(REPAIRED_SOURCE)
    assert evaluation["contract_sha256"] == _sha256(REPAIRED_REGION_CONTRACT)
    assert evaluation["report_sha256"] == _sha256(REPAIRED_REGION_REPORT)
    assert evaluation["machine_outcome"] == "failed_two_declared_region_rules"
    assert evaluation["human_verdict"] == {"state": "pending"}
    assert evaluation["publication_acceptance"] == "not_claimed"


def test_fig3_resistance_scope_guard_checks_actual_pending_git_surface() -> None:
    scope = yaml.safe_load((REVIEW / "scope_protection.yaml").read_text(encoding="utf-8"))
    repo_root = PLUGIN_ROOT.parents[1]
    fixture_prefix = "plugins/figure-agent/examples/fig3_resistance_mechanism/"
    allowed_paths = {
        *(fixture_prefix + path for path in scope["allowed_review_paths"]),
        *scope["allowed_repository_paths"],
    }

    assert _scope_violations({fixture_prefix + "briefing.md"}, allowed_paths) == {
        fixture_prefix + "briefing.md"
    }
    assert _scope_violations(_git_pending_paths(repo_root), allowed_paths) == set()


def test_fig3_resistance_render_receipt_reproduces_current_source_outputs() -> None:
    receipt = _compile_receipt_outputs()
    command = ["bash", "scripts/compile.sh", "examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex"]

    assert receipt["schema"] == "figure-agent.compile-render-receipt.v1"
    assert receipt["fixture"] == "fig3_resistance_mechanism"
    assert receipt["compile_command"] == command
    assert receipt["working_directory"] == "plugins/figure-agent"
    assert receipt["source_path"] == "fig3_resistance_mechanism.tex"
    assert receipt["pdf_path"] == "build/fig3_resistance_mechanism.pdf"
    assert receipt["png_path"] == "build/fig3_resistance_mechanism.png"
    assert receipt["raw_pdf_sha256_status"] == "snapshot_only_nondeterministic"
    assert receipt["toolchain"]["latex_engine"] == "lualatex"
    assert receipt["toolchain"]["lualatex_version"]
    assert receipt["toolchain"]["pdftocairo_version"]
    assert _tool_version(["lualatex", "--version"])
    assert _tool_version(["pdftocairo", "-v"])

    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    packet_by_role = {item["role"]: item for item in packet["authoritative_inputs"]}
    assert packet_by_role["rendered_pdf"]["content_signature"] == receipt["pdf_content_signature"]
    assert packet_by_role["rendered_png"]["sha256"] == receipt["png_sha256"]
    assert receipt["source_sha256"] == _sha256(FIXTURE / receipt["source_path"])

    pdf_path = FIXTURE / receipt["pdf_path"]
    png_path = FIXTURE / receipt["png_path"]
    assert pdf_path.read_bytes().startswith(b"%PDF-")
    assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert _pdf_content_signature(pdf_path) == receipt["pdf_content_signature"]
    assert _sha256(png_path) == receipt["png_sha256"]
