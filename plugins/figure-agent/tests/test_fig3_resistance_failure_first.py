from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig3_resistance_mechanism"
REVIEW = FIXTURE / "review" / "failure-first"
PACKET = REVIEW / "input_packet.yaml"
BOUNDARY = REVIEW / "semantic_object_relation_boundary.yaml"
RENDER_RECEIPT = REVIEW / "render_receipt.yaml"


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


def test_fig3_resistance_failure_first_scope_is_additive_and_historically_protected() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    scope = yaml.safe_load((REVIEW / "scope_protection.yaml").read_text(encoding="utf-8"))

    assert scope["schema"] == "figure-agent.failure-first-scope-protection.v1"
    assert scope["fixture"] == "fig3_resistance_mechanism"
    assert scope["authorized_change_mode"] == "additive_review_artifacts_only"
    assert scope["allowed_review_paths"] == [
        "review/failure-first/input_packet.yaml",
        "review/failure-first/semantic_object_relation_boundary.yaml",
        "review/failure-first/scope_protection.yaml",
        "review/failure-first/render_receipt.yaml",
    ]
    assert all(path.startswith("review/failure-first/") for path in scope["allowed_review_paths"])
    assert scope["protected_paths"] == [
        "fig3_resistance_mechanism.tex",
        "briefing.md",
        "spec.yaml",
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


def test_fig3_resistance_scope_guard_checks_actual_pending_git_surface() -> None:
    scope = yaml.safe_load((REVIEW / "scope_protection.yaml").read_text(encoding="utf-8"))
    repo_root = PLUGIN_ROOT.parents[1]
    fixture_prefix = "plugins/figure-agent/examples/fig3_resistance_mechanism/"
    allowed_paths = {
        "plugins/figure-agent/tests/test_fig3_resistance_failure_first.py",
        *(fixture_prefix + path for path in scope["allowed_review_paths"]),
    }

    assert _scope_violations(
        {fixture_prefix + "fig3_resistance_mechanism.tex"}, allowed_paths
    ) == {fixture_prefix + "fig3_resistance_mechanism.tex"}
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
