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
                "selectors": [
                    {
                        "selector_id": "panel-a-carrier-label",
                        "anchor_start": "% label:start",
                        "anchor_end": "% label:end",
                        "rendered_aliases": ["carrier"],
                        "repair_role": "movable",
                        "repair_family": "local_reposition",
                        "protected_invariants": ["S60"],
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
    assert json.loads((attempt / "source_attribution.json").read_text())[
        "summary"
    ]["exact"] == 1
    assert json.loads((attempt / "critique_repair_binding.json").read_text()) == result


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
    repaired_source.write_text("\\node {repaired};\n", encoding="utf-8")
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
    packet = {
        "schema": "figure-agent.repair-execution-packet.v3",
        "fixture": "demo",
        "target_contract": binding["target_contract"],
        "output_path": repaired_source.relative_to(workspace).as_posix(),
        "publication_acceptance": "not_claimed",
    }
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(packet)
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
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
        match="exact attribution required",
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


def test_bridge_rolls_back_partial_three_file_write(
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
