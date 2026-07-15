from __future__ import annotations

import hashlib
import json
from pathlib import Path

import authoring_repair_finalize
import authoring_repair_packet
import critique_adjudication
import critique_repair_bridge
import critique_zoom_crops
import post_repair_visual_review
import pytest
import yaml
from PIL import Image
from quality_manifest import (
    compute_critique_input_hash,
    critique_generator_version,
    expected_critique_rubric_version,
)
from test_critique_schema_validator import (
    CRITIQUE_SCHEMA_V1_17,
    _valid_frontmatter,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    example = workspace / "examples" / "demo"
    source_dir = example / "review" / "failure-first" / "execution-binding-v1"
    attempt = example / "review" / "failure-first" / "execution-repair-v1"
    source_dir.mkdir(parents=True)
    attempt.mkdir(parents=True)
    reference = example / "reference" / "golden.png"
    reference.parent.mkdir()
    reference.write_bytes(b"reference")
    (example / "spec.yaml").write_text(
        "name: demo\n"
        "reference_image: reference/golden.png\n"
        "panels: []\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    current_render = example / "build" / "demo.png"
    current_render.parent.mkdir()
    Image.new("RGB", (800, 600), "white").save(current_render)
    current_pdf = example / "build" / "demo.pdf"
    current_pdf.write_bytes(b"%PDF-current\n")
    critique_zoom_crops.build_zoom_crop_pack(
        example,
        current_render,
        panel_crop_paths=(),
    )
    source = source_dir / "treatment_generated.tex"
    source.write_text(
        "\\documentclass{standalone}\n"
        "% label:start\n"
        "\\node {carrier label};\n"
        "% label:end\n"
        "\\node {S60};\n",
        encoding="utf-8",
    )
    semantic_contract = attempt / "semantic_contract.yaml"
    semantic_contract.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.failure-first-semantic-contract.v1",
                "required_objects": ["panel_a.carrier_label", "panel_a.axis"],
                "protected_relations": ["carrier_label_remains_clear_of_axis"],
                "semantic_legibility": {
                    "object_roles": [
                        {
                            "object_id": "panel_a.carrier_label",
                            "declared_role": "annotation_label",
                            "forbidden_readings": [],
                        },
                        {
                            "object_id": "panel_a.axis",
                            "declared_role": "plot_axis",
                            "forbidden_readings": [],
                        },
                    ],
                    "visible_connectors": [],
                    "forbidden_connectors": [],
                    "label_ownership": [],
                },
                "publication_acceptance": "not_claimed",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report = attempt / "collisions.json"
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-collisions.v1",
                "fixture": "demo",
                "render_pdf": "build/demo.pdf",
                "render_pdf_sha256": _sha256(current_pdf),
                "render_path": "build/demo.png",
                "render_sha256": _sha256(current_render),
                "collisions": [
                    {"id": "TC001", "texts": ["carrier", "axis"]}
                ],
            }
        ),
        encoding="utf-8",
    )
    registry = attempt / "source_selectors.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "figure-agent.source-selector-registry.v1",
                "source_path": source.relative_to(workspace).as_posix(),
                "source_sha256": _sha256(source),
                "semantic_contract": {
                    "path": semantic_contract.relative_to(workspace).as_posix(),
                    "sha256": _sha256(semantic_contract),
                },
                "selectors": [
                    {
                        "selector_id": "panel-a-carrier-label",
                        "anchor_start": "% label:start",
                        "anchor_end": "% label:end",
                        "rendered_aliases": ["carrier"],
                        "repair_role": "movable",
                        "repair_family": "local_reposition",
                        "protected_invariants": ["S60"],
                        "semantic_object_refs": [
                            "panel_a.axis",
                            "panel_a.carrier_label",
                        ],
                        "semantic_relation_refs": [
                            "carrier_label_remains_clear_of_axis"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    frontmatter = _valid_frontmatter(CRITIQUE_SCHEMA_V1_17)
    frontmatter["fixture"] = "demo"
    frontmatter["findings"][0].update(
        {
            "severity": "NIT",
            "category": "label_placement",
            "observation": "carrier label overlaps the axis",
            "suggested_fix": "move the carrier label",
        }
    )
    for axis in ("journal_polish", "publication_readiness"):
        frontmatter["quality_axes"][axis]["evidence"] = (
            "print-scale audit evidence confirms readable spacing"
        )
    spec = yaml.safe_load((example / "spec.yaml").read_text(encoding="utf-8"))
    frontmatter.update(
        {
            "generator": "critique_brief.py",
            "generator_version": critique_generator_version(
                PLUGIN_ROOT / "scripts" / "critique_brief.py"
            ),
            "rubric_version": expected_critique_rubric_version(example),
            "critique_input_hash": compute_critique_input_hash(
                example,
                "demo",
                spec,
                style_lock_path=(
                    PLUGIN_ROOT / "styles" / "polymer-paper-preamble.sty"
                ),
                base_dir=PLUGIN_ROOT,
            ),
        }
    )
    critique = example / "critique.md"
    critique.write_text(
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n",
        encoding="utf-8",
    )
    adjudication = {
        "schema": "figure-agent.critique-adjudication.v1",
        "fixture": "demo",
        "source_critique_hash": _sha256(critique),
        "decisions": [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "bounded label repair",
                "patch_target": "panel A carrier label",
                "evidence": "critique C001 and collision TC001",
                "repair_evidence": {
                    "report_path": report.relative_to(workspace).as_posix(),
                    "finding_id": "TC001",
                    "selector_registry_path": registry.relative_to(workspace).as_posix(),
                },
            }
        ],
    }
    (example / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(adjudication, sort_keys=False), encoding="utf-8"
    )
    return workspace, attempt


def test_builds_exact_additive_bridge_artifacts(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)

    result = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert result["schema"] == "figure-agent.adjudicated-repair-binding.v1"
    assert result["attribution_state"] == "exact"
    assert result["publication_acceptance"] == "not_claimed"
    assert result["spec"]["path"] == "examples/demo/spec.yaml"
    assert result["current_render"]["path"] == "examples/demo/build/demo.png"
    assert result["current_pdf"]["path"] == "examples/demo/build/demo.pdf"
    assert result["crop_manifest"]["path"] == (
        "examples/demo/build/audit_crops/manifest.json"
    )
    target = json.loads((attempt / "repair_targets.json").read_text())
    assert target["targets"][0]["selector"]["selector_id"] == (
        "panel-a-carrier-label"
    )
    semantic = json.loads((attempt / "semantic_attribution.json").read_text())
    assert json.loads((attempt / "source_attribution.json").read_text())["summary"][
        "exact"
    ] == 1
    assert semantic["schema"] == "figure-agent.semantic-finding-attribution.v1"
    assert semantic["semantic_object_refs"] == [
        "panel_a.axis",
        "panel_a.carrier_label",
    ]
    assert semantic["semantic_relation_refs"] == [
        "carrier_label_remains_clear_of_axis"
    ]
    assert result["semantic_attribution"]["path"].endswith(
        "/semantic_attribution.json"
    )
    assert json.loads((attempt / "critique_repair_binding.json").read_text()) == result


def test_validates_full_live_adjudicated_repair_binding(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    expected = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    binding, paths = critique_repair_bridge.validate_adjudicated_repair_binding(
        attempt.relative_to(workspace) / "critique_repair_binding.json",
        fixture="demo",
        workspace_root=workspace,
    )

    assert binding == expected
    assert paths["source"] == (
        workspace / "examples/demo/review/failure-first/execution-binding-v1/"
        "treatment_generated.tex"
    )
    assert paths["target_contract"] == attempt / "repair_targets.json"
    assert paths["semantic_attribution"] == attempt / "semantic_attribution.json"


def test_binding_rejects_crop_manifest_render_redirection(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    manifest_path = workspace / "examples/demo/build/audit_crops/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["render_path"] = "build/redirected.png"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    binding_path = attempt / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["crop_manifest"]["sha256"] = _sha256(manifest_path)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="binding crop manifest render lineage invalid",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_semantic_binding_rejects_legacy_minimal_crop_manifest(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    manifest_path = workspace / "examples/demo/build/audit_crops/manifest.json"
    manifest_path.write_text(
        json.dumps({"schema": "figure-agent.audit-crop-manifest.v1"}),
        encoding="utf-8",
    )
    binding_path = attempt / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["crop_manifest"]["sha256"] = _sha256(manifest_path)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="binding crop manifest render lineage invalid",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_rejects_rehashed_spec_stale_to_critique(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    spec_path = workspace / "examples/demo/spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8") + "panels:\n  - id: changed\n",
        encoding="utf-8",
    )
    binding_path = attempt / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["spec"]["sha256"] = _sha256(spec_path)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="critique_input_hash mismatch",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_new_binding_hash_binds_semantic_attribution_and_rejects_drift(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    semantic_path = attempt / "semantic_attribution.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    semantic["semantic_object_refs"].append("panel_a.unknown")
    semantic_path.write_text(json.dumps(semantic), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic attribution hash drift",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            attempt.relative_to(workspace) / "critique_repair_binding.json",
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_rejects_mixed_target_and_semantic_selectors(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    source_path = (
        workspace / "examples/demo/review/failure-first/execution-binding-v1/"
        "treatment_generated.tex"
    )
    source_path.write_text(
        source_path.read_text(encoding="utf-8")
        + "% secondary:start\n\\node {secondary};\n% secondary:end\n",
        encoding="utf-8",
    )
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["source_sha256"] = _sha256(source_path)
    registry["selectors"].append(
        {
            "selector_id": "panel-a-secondary-label",
            "anchor_start": "% secondary:start",
            "anchor_end": "% secondary:end",
            "rendered_aliases": ["secondary"],
            "repair_role": "movable",
            "repair_family": "local_reposition",
            "protected_invariants": ["S60"],
            "semantic_object_refs": ["panel_a.axis", "panel_a.carrier_label"],
            "semantic_relation_refs": [
                "carrier_label_remains_clear_of_axis"
            ],
        }
    )
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    semantic_path = attempt / "semantic_attribution.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    semantic["selector_id"] = "panel-a-secondary-label"
    semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
    binding_path = attempt / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["semantic_attribution"]["sha256"] = _sha256(semantic_path)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic attribution lineage invalid",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_rejects_unrelated_selector_substitution(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    source_path = (
        workspace / "examples/demo/review/failure-first/execution-binding-v1/"
        "treatment_generated.tex"
    )
    source_path.write_text(
        source_path.read_text(encoding="utf-8")
        + "% secondary:start\n\\node {secondary};\n% secondary:end\n",
        encoding="utf-8",
    )
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["source_sha256"] = _sha256(source_path)
    secondary_selector = {
        "selector_id": "panel-a-secondary-label",
        "anchor_start": "% secondary:start",
        "anchor_end": "% secondary:end",
        "rendered_aliases": ["not-the-machine-finding"],
        "repair_role": "movable",
        "repair_family": "local_reposition",
        "protected_invariants": ["S60"],
        "semantic_object_refs": ["panel_a.axis", "panel_a.carrier_label"],
        "semantic_relation_refs": ["carrier_label_remains_clear_of_axis"],
    }
    registry["selectors"].append(secondary_selector)
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    target_path = attempt / "repair_targets.json"
    target = json.loads(target_path.read_text(encoding="utf-8"))
    target["targets"][0]["selector"] = {
        "kind": "semantic_anchor",
        "selector_id": secondary_selector["selector_id"],
        "anchor_start": secondary_selector["anchor_start"],
        "anchor_end": secondary_selector["anchor_end"],
    }
    target_path.write_text(json.dumps(target), encoding="utf-8")
    semantic_path = attempt / "semantic_attribution.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    semantic["selector_id"] = secondary_selector["selector_id"]
    semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
    binding_path = attempt / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["target_contract"]["sha256"] = _sha256(target_path)
    binding["semantic_attribution"]["sha256"] = _sha256(semantic_path)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="binding source attribution lineage invalid",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_rejects_forged_exact_semantic_attribution_with_null_refs(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["selectors"][0]["semantic_object_refs"] = []
    registry["selectors"][0]["semantic_relation_refs"] = []
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    semantic_path = attempt / "semantic_attribution.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    semantic["semantic_object_refs"] = None
    semantic["semantic_relation_refs"] = None
    semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
    binding_path = attempt / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["selector_registry"]["sha256"] = _sha256(registry_path)
    binding["semantic_attribution"]["sha256"] = _sha256(semantic_path)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic attribution references invalid",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_stored_pre_semantic_binding_remains_valid(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    binding = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    binding.pop("semantic_attribution")
    (attempt / "critique_repair_binding.json").write_text(
        json.dumps(binding), encoding="utf-8"
    )

    validated, paths = critique_repair_bridge.validate_adjudicated_repair_binding(
        attempt.relative_to(workspace) / "critique_repair_binding.json",
        fixture="demo",
        workspace_root=workspace,
    )

    assert "semantic_attribution" not in validated
    assert "semantic_attribution" not in paths


def test_bridge_rejects_unknown_semantic_references(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["selectors"][0]["semantic_relation_refs"] = ["unknown_relation"]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic relation reference is undeclared",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )

    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "attribution_handoff.json").exists()


def test_bridge_rejects_semantic_contract_hash_drift(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["semantic_contract"]["sha256"] = "sha256:" + "0" * 64
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic contract hash drift",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )


def test_bridge_rejects_corrupted_semantic_contract(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    semantic_contract_path = workspace / registry["semantic_contract"]["path"]
    semantic_contract_path.write_text("[unclosed\n", encoding="utf-8")
    registry["semantic_contract"]["sha256"] = _sha256(semantic_contract_path)
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic contract must be valid YAML",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )


def test_unmatched_alias_does_not_bypass_bad_semantic_contract_hash(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["selectors"][0]["rendered_aliases"] = ["not-present"]
    registry["semantic_contract"]["sha256"] = "sha256:" + "0" * 64
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="semantic contract hash drift",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            human_attributor_id="moon",
        )

    assert not (attempt / "attribution_handoff.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_bridge_rejects_null_semantic_contract_record(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["semantic_contract"] = None
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="selector registry semantic contract record is invalid",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )


@pytest.mark.parametrize(
    ("mutation", "reason_code", "missing_reference_kinds"),
    (
        ("ambiguous", "multiple_declared_movable_selectors", [
            "semantic_object",
            "semantic_relation",
        ]),
        ("unbound", "no_declared_alias_match", [
            "semantic_object",
            "semantic_relation",
        ]),
        ("missing_refs", "selected_selector_missing_semantic_refs", [
            "semantic_relation"
        ]),
    ),
)
def test_bridge_emits_handoff_only_for_unresolved_semantic_attribution(
    tmp_path: Path,
    mutation: str,
    reason_code: str,
    missing_reference_kinds: list[str],
) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if mutation == "ambiguous":
        registry["selectors"].append(
            {**registry["selectors"][0], "selector_id": "second-carrier-label"}
        )
    elif mutation == "unbound":
        registry["selectors"][0]["rendered_aliases"] = ["not-present"]
    else:
        registry["selectors"][0]["semantic_relation_refs"] = []
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    result = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        human_attributor_id="moon",
    )

    assert result["schema"] == "figure-agent.attribution-handoff.v1"
    assert result["evidence_role"] == "attribution_handoff"
    assert result["attempt_state"] == "adjudicated_unbound"
    assert result["required_actor"] == {"id": "moon", "role": "human_attributor"}
    assert result["reason_code"] == reason_code
    assert result["missing_reference_kinds"] == missing_reference_kinds
    assert result["publication_acceptance"] == "not_claimed"
    assert (attempt / "attribution_handoff.json").is_file()
    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_unresolved_attribution_without_human_id_fails_without_outputs(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["selectors"][0]["semantic_object_refs"] = []
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="human_attributor_id is required",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )

    assert list(attempt.glob("*attribution*.json")) == []
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_exact_source_without_semantic_contract_emits_handoff_only(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    del registry["semantic_contract"]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    result = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        human_attributor_id="moon",
    )

    assert result["reason_code"] == "semantic_boundary_missing"
    assert result["missing_reference_kinds"] == [
        "semantic_object",
        "semantic_relation",
    ]
    generated_names = [
        path.name
        for path in attempt.glob("*.json")
        if "collisions" not in path.name and "selectors" not in path.name
    ]
    assert generated_names == ["attribution_handoff.json"]


def test_binding_validator_parses_and_hashes_each_authority_from_one_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    observed = {
        attempt / "critique_repair_binding.json",
        attempt / "collisions.json",
        attempt / "repair_targets.json",
        workspace / "examples/demo/critique_adjudication.yaml",
        attempt / "source_selectors.json",
    }
    byte_reads = {path: 0 for path in observed}
    text_reads = {path: 0 for path in observed}
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def counted_read_bytes(path: Path) -> bytes:
        if path in byte_reads:
            byte_reads[path] += 1
        return original_read_bytes(path)

    def counted_read_text(
        path: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        if path in text_reads:
            text_reads[path] += 1
        return original_read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    monkeypatch.setattr(Path, "read_text", counted_read_text)

    critique_repair_bridge.validate_adjudicated_repair_binding(
        attempt.relative_to(workspace) / "critique_repair_binding.json",
        fixture="demo",
        workspace_root=workspace,
    )

    assert byte_reads == {path: 2 for path in observed}
    assert text_reads == {path: 0 for path in observed}


@pytest.mark.parametrize(
    "artifact_name",
    [
        "critique_repair_binding.json",
        "collisions.json",
        "repair_targets.json",
        "critique_adjudication.yaml",
        "source_selectors.json",
    ],
)
def test_binding_validator_rejects_authority_mutation_after_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact_name: str,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    selected = {
        "critique_repair_binding.json": (
            attempt / "critique_repair_binding.json"
        ),
        "collisions.json": attempt / "collisions.json",
        "repair_targets.json": attempt / "repair_targets.json",
        "critique_adjudication.yaml": (
            workspace / "examples/demo/critique_adjudication.yaml"
        ),
        "source_selectors.json": attempt / "source_selectors.json",
    }[artifact_name]
    original_read_bytes = Path.read_bytes
    selected_reads = 0

    def mutate_on_final_read(path: Path) -> bytes:
        nonlocal selected_reads
        data = original_read_bytes(path)
        if path == selected:
            selected_reads += 1
            if selected_reads == 2:
                return data + b"\n"
        return data

    monkeypatch.setattr(Path, "read_bytes", mutate_on_final_read)

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="changed during validation",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            attempt.relative_to(workspace) / "critique_repair_binding.json",
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_validator_rejects_six_field_fabrication(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    payload = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    fabricated = {
        key: payload[key]
        for key in (
            "schema",
            "fixture",
            "source",
            "target_contract",
            "attribution_state",
            "publication_acceptance",
        )
    }
    binding_path = attempt / "critique_repair_binding.json"
    binding_path.write_text(json.dumps(fabricated), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="top-level fields",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            binding_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_validator_rejects_noncanonical_filename(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    binding_path = attempt / "critique_repair_binding.json"
    wrong_path = binding_path.with_name("anything.json")
    binding_path.rename(wrong_path)

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="critique_repair_binding.json",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            wrong_path.relative_to(workspace),
            fixture="demo",
            workspace_root=workspace,
        )


def test_binding_validator_rejects_upstream_drift(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    binding = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=workspace / "examples" / "demo",
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    source = workspace / str(binding["source"]["path"])
    source.write_text(source.read_text(encoding="utf-8") + "% drift\n", encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="binding source hash drift",
    ):
        critique_repair_bridge.validate_adjudicated_repair_binding(
            attempt.relative_to(workspace) / "critique_repair_binding.json",
            fixture="demo",
            workspace_root=workspace,
        )


def test_bridge_to_attempt_local_post_review_preserves_canonical_baseline(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    example = workspace / "examples" / "demo"
    baseline_manifest = example / "build" / "audit_crops" / "manifest.json"
    baseline_hash = _sha256(baseline_manifest)
    binding = critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=example,
        critique_finding_id="C001",
        attempt_dir=attempt,
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    repaired_source = attempt / "repaired_generated.tex"
    repaired_render = attempt / "build" / "repaired_generated.png"
    repaired_render.parent.mkdir()
    Image.new("RGB", (800, 600), "white").save(repaired_render)
    repaired_pdf = attempt / "build" / "repaired_generated.pdf"
    repaired_pdf.write_bytes(b"%PDF-repaired\n")
    strict_status = attempt / "build" / "strict_status.json"
    strict_status.write_text(
        json.dumps(
            {
                "schema": authoring_repair_finalize.STRICT_STATUS_SCHEMA,
                "strict_requested": True,
                "detector_failed": False,
                "state": "passed",
            }
        ),
        encoding="utf-8",
    )
    detector_records = {}
    for name, schema in authoring_repair_finalize.REQUIRED_DETECTOR_REPORTS.items():
        report_path = attempt / "build" / f"{name}.json"
        report_path.write_text(
            json.dumps({"schema": schema or f"test.{name}.v1"}),
            encoding="utf-8",
        )
        detector_records[name] = {
            "path": report_path.relative_to(workspace).as_posix(),
            "sha256": _sha256(report_path),
            **({"schema": schema} if schema is not None else {}),
        }
    post_crop_dir = attempt / "build" / "audit_crops"
    post_manifest = post_crop_dir / "manifest.json"
    critique_zoom_crops.build_zoom_crop_pack(
        example,
        repaired_render,
        panel_crop_paths=(),
        output_dir=post_crop_dir,
        manifest_path=post_manifest,
    )
    assert _sha256(baseline_manifest) == baseline_hash
    assert binding["crop_manifest"]["path"] == (
        "examples/demo/build/audit_crops/manifest.json"
    )
    packet_path = attempt / "repair_packet.json"
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=(
                attempt / "critique_repair_binding.json"
            ).relative_to(workspace).as_posix(),
            output_path=repaired_source.relative_to(workspace).as_posix(),
        )
    )
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    repaired_source.write_text("\\node {repaired};\n", encoding="utf-8")
    receipt_path = attempt / "materialization_receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.repair-materialization-receipt.v2",
                "fixture": "demo",
                "decision": "materialized_machine_verified_human_review_pending",
                "packet_sha256": packet["packet_sha256"],
                "output_path": packet["output_path"],
                "output_sha256": _sha256(repaired_source),
                "post_render_verification": "passed",
                "external_compile": {
                    "command": [
                        "bash",
                        "scripts/compile.sh",
                        packet["output_path"],
                    ],
                    "returncode": 0,
                    "stdout_sha256": "sha256:" + "0" * 64,
                    "stderr_sha256": "sha256:" + "0" * 64,
                    "strict_status": {
                        "path": strict_status.relative_to(workspace).as_posix(),
                        "sha256": _sha256(strict_status),
                        "schema": authoring_repair_finalize.STRICT_STATUS_SCHEMA,
                        "state": "passed",
                    },
                    "detector_reports": detector_records,
                    "pdf": {
                        "path": repaired_pdf.relative_to(workspace).as_posix(),
                        "sha256": _sha256(repaired_pdf),
                    },
                    "png": {
                        "path": repaired_render.relative_to(workspace).as_posix(),
                        "sha256": _sha256(repaired_render),
                    }
                },
                "human_review": "pending",
                "publication_acceptance": "not_claimed",
                "recovery_required": False,
            }
        ),
        encoding="utf-8",
    )

    request = post_repair_visual_review.build_review_request(
        binding_path=attempt / "critique_repair_binding.json",
        packet_path=packet_path,
        materialization_receipt_path=receipt_path,
        crop_manifest_path=post_manifest,
        crop_roles={
            "target_crop": "full_q1",
            "neighbor_crop": "full_q2",
            "print_scale": "print_thumbnail",
        },
        workspace_root=workspace,
    )

    assert request["crop_manifest"]["path"] == post_manifest.relative_to(
        workspace
    ).as_posix()
    assert {item["crop_id"] for item in request["inspection_artifacts"] if "crop_id" in item} == {
        "full_q1",
        "full_q2",
        "print_thumbnail",
    }


def test_bridge_rejects_stale_adjudication(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique = workspace / "examples" / "demo" / "critique.md"
    critique.write_text(critique.read_text() + "# changed\n", encoding="utf-8")

    with pytest.raises(critique_repair_bridge.CritiqueRepairBridgeError, match="stale"):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_bridge_rejects_ambiguous_attribution(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text())
    registry["selectors"].append(
        {
            **registry["selectors"][0],
            "selector_id": "panel-a-second-label",
        }
    )
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="human_attributor_id is required",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_bridge_rejects_legacy_apply_without_repair_evidence(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    path = workspace / "examples" / "demo" / "critique_adjudication.yaml"
    payload = yaml.safe_load(path.read_text())
    del payload["decisions"][0]["repair_evidence"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="repair_evidence required",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_bridge_rejects_legacy_report_without_render_hash(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    report_path = attempt / "collisions.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    del report["render_sha256"]
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="hash-bound",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


@pytest.mark.parametrize("missing", ("render_pdf_sha256", "render_sha256"))
def test_bridge_rejects_report_missing_pdf_or_png_hash(
    tmp_path: Path, missing: str
) -> None:
    workspace, attempt = _fixture(tmp_path)
    report_path = attempt / "collisions.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    del report[missing]
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="hash-bound",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_bridge_never_overwrites_existing_artifacts(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    existing = attempt / "source_attribution.json"
    existing.write_text("historical\n", encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="already exists",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )

    assert existing.read_text(encoding="utf-8") == "historical\n"


def test_bridge_rejects_symlinked_attempt_directory(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    outside = tmp_path / "outside-attempt"
    outside.mkdir()
    alias = attempt.with_name("execution-repair-v2")
    alias.symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="must not traverse a symlink",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=alias,
            workspace_root=workspace,
        )


def test_bridge_rejects_fixture_that_is_not_direct_examples_child(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="direct child",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace.parent,
        )


def test_bridge_rejects_retired_critique_schema(
    tmp_path: Path,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    critique = workspace / "examples" / "demo" / "critique.md"
    text = critique.read_text(encoding="utf-8").replace(
        CRITIQUE_SCHEMA_V1_17, "figure-agent.critique.v1", 1
    )
    critique.write_text(text, encoding="utf-8")

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="retired",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_bridge_rejects_current_schema_with_stale_input_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, attempt = _fixture(tmp_path)
    monkeypatch.setattr(
        critique_adjudication,
        "_critique_metadata_mismatches",
        lambda _example_dir, *, repo_root: [
            "critique_input_hash mismatch; run /fig_critique demo"
        ],
    )

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="critique_input_hash mismatch",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_builder_rejects_redirected_crop_manifest_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    manifest_path = workspace / "examples/demo/build/audit_crops/manifest.json"
    original_read_bytes = critique_repair_bridge._read_bytes
    injected = False

    def redirect_snapshot(path: Path, *, label: str) -> bytes:
        nonlocal injected
        snapshot = original_read_bytes(path, label=label)
        if path == manifest_path and not injected:
            injected = True
            manifest = json.loads(snapshot.decode("utf-8"))
            manifest["render_path"] = "build/redirected.png"
            return json.dumps(manifest).encode("utf-8")
        return snapshot

    monkeypatch.setattr(
        critique_repair_bridge,
        "_read_bytes",
        redirect_snapshot,
    )

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match=(
            "current crop manifest render lineage invalid|"
            "bridge input drift before publication"
        ),
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )

    assert not (attempt / "source_attribution.json").exists()
    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_builder_rejects_spec_mutation_after_freshness_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    spec_path = workspace / "examples/demo/spec.yaml"
    original = critique_repair_bridge._assert_current_critique_metadata
    mutated = False

    def mutate_spec_after_freshness(
        example_dir: Path,
        *,
        plugin_root: Path,
    ) -> None:
        nonlocal mutated
        original(example_dir, plugin_root=plugin_root)
        if not mutated:
            mutated = True
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8") + "panels: []\n",
                encoding="utf-8",
            )

    monkeypatch.setattr(
        critique_repair_bridge,
        "_assert_current_critique_metadata",
        mutate_spec_after_freshness,
    )

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="bridge input drift before publication",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )

    assert not (attempt / "source_attribution.json").exists()
    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_bridge_honors_exclusive_transaction_lock(tmp_path: Path) -> None:
    workspace, attempt = _fixture(tmp_path)
    (attempt / ".critique-repair-bridge.lock").write_text(
        "other-owner\n", encoding="utf-8"
    )

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="transaction already active",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )


def test_exact_bridge_rejects_authority_mutation_after_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    original_read_bytes = critique_repair_bridge._read_bytes
    mutated = False

    def mutate_registry_after_snapshot(path: Path, *, label: str) -> bytes:
        nonlocal mutated
        snapshot = original_read_bytes(path, label=label)
        if path == registry_path and not mutated:
            mutated = True
            path.write_bytes(snapshot + b"\n")
        return snapshot

    monkeypatch.setattr(
        critique_repair_bridge,
        "_read_bytes",
        mutate_registry_after_snapshot,
    )

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="bridge input drift before publication",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )

    assert not (attempt / "source_attribution.json").exists()
    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_handoff_rejects_authority_mutation_after_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, attempt = _fixture(tmp_path)
    registry_path = attempt / "source_selectors.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["selectors"][0]["rendered_aliases"] = ["not-present"]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    report_path = attempt / "collisions.json"
    original_read_bytes = critique_repair_bridge._read_bytes
    mutated = False

    def mutate_report_after_snapshot(path: Path, *, label: str) -> bytes:
        nonlocal mutated
        snapshot = original_read_bytes(path, label=label)
        if path == report_path and not mutated:
            mutated = True
            path.write_bytes(snapshot + b"\n")
        return snapshot

    monkeypatch.setattr(
        critique_repair_bridge,
        "_read_bytes",
        mutate_report_after_snapshot,
    )

    with pytest.raises(
        critique_repair_bridge.CritiqueRepairBridgeError,
        match="bridge input drift before publication",
    ):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            human_attributor_id="moon",
        )

    assert not (attempt / "attribution_handoff.json").exists()
    assert not (attempt / "source_attribution.json").exists()
    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_bridge_rolls_back_partial_four_file_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, attempt = _fixture(tmp_path)
    original = critique_repair_bridge.repair_transaction.atomic_create_json
    writes = 0

    def fail_second_write(path: Path, payload: dict[str, object]) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("injected write failure")
        original(path, payload)

    monkeypatch.setattr(
        critique_repair_bridge.repair_transaction,
        "atomic_create_json",
        fail_second_write,
    )

    with pytest.raises(OSError, match="injected write failure"):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )

    assert not (attempt / "source_attribution.json").exists()
    assert not (attempt / "semantic_attribution.json").exists()
    assert not (attempt / "repair_targets.json").exists()
    assert not (attempt / "critique_repair_binding.json").exists()


def test_bridge_publish_race_preserves_competing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, attempt = _fixture(tmp_path)
    original = critique_repair_bridge.repair_transaction.atomic_create_json
    raced = False

    def race_first_write(path: Path, payload: dict[str, object]) -> None:
        nonlocal raced
        if not raced:
            raced = True
            path.write_text("competing-writer\n", encoding="utf-8")
        original(path, payload)

    monkeypatch.setattr(
        critique_repair_bridge.repair_transaction,
        "atomic_create_json",
        race_first_write,
    )

    with pytest.raises(FileExistsError):
        critique_repair_bridge.build_adjudicated_repair_target(
            example_dir=workspace / "examples" / "demo",
            critique_finding_id="C001",
            attempt_dir=attempt,
            workspace_root=workspace,
        )

    assert (attempt / "source_attribution.json").read_text(encoding="utf-8") == (
        "competing-writer\n"
    )
    assert not (attempt / "semantic_attribution.json").exists()
