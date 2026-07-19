#!/usr/bin/env python3
"""Bind one fresh adjudicated critique finding to one exact repair target."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import critique_adjudication
import finding_source_attribution
import fixture_identity
import repair_transaction
import yaml
from critique_contract import (
    critique_finding_id,
    critique_findings,
)

BINDING_SCHEMA = "figure-agent.adjudicated-repair-binding.v1"
SEMANTIC_ATTRIBUTION_SCHEMA = "figure-agent.semantic-finding-attribution.v1"
ATTRIBUTION_HANDOFF_SCHEMA = "figure-agent.attribution-handoff.v1"
REPAIR_ATTEMPT = re.compile(r"execution-repair-v[1-9][0-9]*")
SUPPORTED_CATEGORIES = frozenset({"hierarchy", "label_placement", "whitespace"})
CROP_MANIFEST_SCHEMA = "figure-agent.audit-crop-manifest.v1"
BINDING_FIELDS_LEGACY = frozenset(
    {
        "schema",
        "fixture",
        "critique",
        "adjudication",
        "machine_finding",
        "selector_registry",
        "source",
        "spec",
        "current_render",
        "current_pdf",
        "crop_manifest",
        "attribution_state",
        "target_contract",
        "publication_acceptance",
    }
)
BINDING_FIELDS = BINDING_FIELDS_LEGACY | {"semantic_attribution"}
BINDING_RECORD_FIELDS = {
    "critique": frozenset({"path", "sha256", "finding_id"}),
    "adjudication": frozenset({"path", "sha256", "decision"}),
    "machine_finding": frozenset(
        {"report_path", "report_sha256", "finding_id"}
    ),
    "selector_registry": frozenset({"path", "sha256"}),
    "source": frozenset({"path", "sha256"}),
    "spec": frozenset({"path", "sha256"}),
    "current_render": frozenset({"path", "sha256"}),
    "current_pdf": frozenset({"path", "sha256"}),
    "crop_manifest": frozenset({"path", "sha256"}),
    "target_contract": frozenset({"path", "sha256"}),
    "semantic_attribution": frozenset({"path", "sha256"}),
}
TARGET_CONTRACT_FIELDS = frozenset(
    {"schema", "source_path", "source_sha256", "targets"}
)
TARGET_FIELDS = frozenset(
    {
        "finding",
        "attribution",
        "selector",
        "repair_family",
        "protected_invariants",
    }
)
TARGET_SELECTOR_FIELDS = frozenset(
    {"kind", "selector_id", "anchor_start", "anchor_end"}
)


class CritiqueRepairBridgeError(ValueError):
    """Raised when an adjudicated finding cannot be bound exactly and freshly."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _json_payload_sha256(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _relative(path: Path, *, root: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise CritiqueRepairBridgeError(f"{label} must remain inside workspace") from exc


def _workspace_file(root: Path, value: object, *, label: str) -> Path:
    relative = Path(str(value or ""))
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise CritiqueRepairBridgeError(f"{label} must be workspace-relative and safe")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CritiqueRepairBridgeError(f"{label} must not traverse a symlink")
    if not current.is_file():
        raise CritiqueRepairBridgeError(f"{label} must be a regular file")
    return current


def _workspace_directory(root: Path, value: Path, *, label: str) -> Path:
    candidate = Path(os.path.abspath(value)) if value.is_absolute() else root / value
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise CritiqueRepairBridgeError(f"{label} must remain inside workspace") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CritiqueRepairBridgeError(f"{label} must not traverse a symlink")
    if not current.is_dir():
        raise CritiqueRepairBridgeError(f"{label} must be an existing directory")
    return current


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CritiqueRepairBridgeError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise CritiqueRepairBridgeError(f"{label} must be a JSON object")
    return payload


def _read_bytes(path: Path, *, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CritiqueRepairBridgeError(f"{label} could not be read") from exc


def _load_json_bytes(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CritiqueRepairBridgeError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise CritiqueRepairBridgeError(f"{label} must be a JSON object")
    return payload


def _load_yaml_bytes(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(data.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise CritiqueRepairBridgeError(f"{label} must be valid YAML") from exc
    if not isinstance(payload, dict):
        raise CritiqueRepairBridgeError(f"{label} must be a YAML mapping")
    return payload


def _load_critique_frontmatter_bytes(data: bytes) -> dict[str, Any]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise CritiqueRepairBridgeError("critique must be valid UTF-8") from exc
    if not lines or lines[0].strip() != "---":
        raise CritiqueRepairBridgeError("critique frontmatter is missing")
    end_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        ),
        None,
    )
    if end_index is None:
        raise CritiqueRepairBridgeError("critique frontmatter is unterminated")
    try:
        payload = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError as exc:
        raise CritiqueRepairBridgeError("critique frontmatter must be valid YAML") from exc
    if not isinstance(payload, dict):
        raise CritiqueRepairBridgeError("critique frontmatter must be a mapping")
    return payload


def _assert_input_snapshots_current(snapshots: dict[Path, bytes]) -> None:
    for path, snapshot in snapshots.items():
        if _read_bytes(path, label=f"bridge input {path.name}") != snapshot:
            raise CritiqueRepairBridgeError(
                "bridge input drift before publication"
            )


def _assert_current_critique_metadata(
    example_dir: Path,
    *,
    plugin_root: Path,
) -> None:
    try:
        mismatches = critique_adjudication._critique_metadata_mismatches(
            example_dir,
            repo_root=plugin_root,
        )
    except critique_adjudication.CritiqueAdjudicationError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    if mismatches:
        raise CritiqueRepairBridgeError("; ".join(mismatches))


def _validate_crop_manifest_snapshot(
    data: bytes,
    *,
    fixture: str,
    example_dir: Path,
    render_path: Path,
    pdf_path: Path,
    label: str,
    allow_legacy_minimal: bool = False,
) -> None:
    manifest = _load_json_bytes(data, label=label)
    if allow_legacy_minimal and manifest == {"schema": CROP_MANIFEST_SCHEMA}:
        return
    try:
        expected_render = render_path.relative_to(example_dir).as_posix()
        expected_pdf = pdf_path.relative_to(example_dir).as_posix()
    except ValueError as exc:
        raise CritiqueRepairBridgeError(
            f"{label} render artifacts must remain inside the fixture"
        ) from exc
    manifest_render = manifest.get("render_path")
    if (
        manifest.get("schema") != CROP_MANIFEST_SCHEMA
        or manifest.get("fixture") != fixture
        or manifest_render != expected_render
        or not isinstance(manifest_render, str)
        or Path(manifest_render).with_suffix(".pdf").as_posix() != expected_pdf
    ):
        raise CritiqueRepairBridgeError(f"{label} render lineage invalid")


def _current_critique_inputs(
    example_dir: Path,
    *,
    plugin_root: Path,
    workspace_root: Path,
) -> tuple[Path, Path, Path, Path]:
    example_relative = example_dir.relative_to(workspace_root)
    _workspace_file(
        workspace_root,
        (example_relative / "critique.md").as_posix(),
        label="current critique",
    )
    try:
        critique_adjudication.build_adjudication_scaffold(example_dir)
    except critique_adjudication.CritiqueAdjudicationError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    spec_path = _workspace_file(
        workspace_root,
        (example_relative / "spec.yaml").as_posix(),
        label="current spec",
    )
    manifest_path = _workspace_file(
        workspace_root,
        (example_relative / "build" / "audit_crops" / "manifest.json").as_posix(),
        label="current crop manifest",
    )
    manifest = _load_json(manifest_path, label="current crop manifest")
    if (
        manifest.get("schema") != CROP_MANIFEST_SCHEMA
        or manifest.get("fixture") != example_dir.name
    ):
        raise CritiqueRepairBridgeError("current crop manifest is invalid")
    render_relative = Path(str(manifest.get("render_path") or ""))
    if render_relative.is_absolute() or not render_relative.parts or any(
        part in {"", ".", ".."} for part in render_relative.parts
    ):
        raise CritiqueRepairBridgeError("current crop manifest render_path is invalid")
    render_path = _workspace_file(
        workspace_root,
        (example_dir.relative_to(workspace_root) / render_relative).as_posix(),
        label="current render",
    )
    pdf_path = _workspace_file(
        workspace_root,
        (
            example_dir.relative_to(workspace_root)
            / render_relative.with_suffix(".pdf")
        ).as_posix(),
        label="current PDF",
    )
    if pdf_path.stem != render_path.stem:
        raise CritiqueRepairBridgeError("current PDF/render generation mismatch")
    return spec_path, manifest_path, render_path, pdf_path


def _validate_report_lineage(
    report: dict[str, Any],
    *,
    fixture: str,
    current_render: Path,
    current_pdf: Path,
    example_dir: Path,
    workspace_root: Path,
    current_render_sha256: str | None = None,
    current_pdf_sha256: str | None = None,
) -> None:
    expected_render_path = current_render.relative_to(example_dir).as_posix()
    expected_pdf_path = current_pdf.relative_to(example_dir).as_posix()
    report_render_path = Path(str(report.get("render_path") or ""))
    report_pdf_path = Path(str(report.get("render_pdf") or ""))
    if (
        report.get("schema") != "figure-agent.text-collisions.v1"
        or report.get("fixture") != fixture
        or report.get("render_path") != expected_render_path
        or report.get("render_sha256")
        != (current_render_sha256 or _sha256(current_render))
        or report.get("render_pdf") != expected_pdf_path
        or report.get("render_pdf_sha256")
        != (current_pdf_sha256 or _sha256(current_pdf))
        or report_render_path.stem != report_pdf_path.stem
    ):
        raise CritiqueRepairBridgeError(
            "finding report must be hash-bound to the current fixture render"
        )
    for label, relative in (
        ("finding report render", report_render_path),
        ("finding report PDF", report_pdf_path),
    ):
        _workspace_file(
            workspace_root,
            (example_dir.relative_to(workspace_root) / relative).as_posix(),
            label=label,
        )


def _attempt_path(
    attempt_dir: Path,
    *,
    example_dir: Path,
    workspace_root: Path,
) -> Path:
    attempt = _workspace_directory(
        workspace_root, attempt_dir, label="attempt_dir"
    )
    expected_parent = example_dir / "review" / "failure-first"
    if attempt.parent != expected_parent or REPAIR_ATTEMPT.fullmatch(attempt.name) is None:
        raise CritiqueRepairBridgeError(
            "attempt_dir must be an execution-repair-vN directory for the fixture"
        )
    return attempt


def validate_adjudicated_repair_binding_snapshot(
    binding_path: str | Path,
    *,
    fixture: str,
    workspace_root: Path,
) -> tuple[dict[str, Any], dict[str, Path], str]:
    """Validate one repair binding from coherent per-artifact byte snapshots."""
    workspace_root = workspace_root.resolve()
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise CritiqueRepairBridgeError("binding fixture invalid") from exc
    relative = Path(binding_path)
    if relative.name != "critique_repair_binding.json":
        raise CritiqueRepairBridgeError(
            "binding filename must be critique_repair_binding.json"
        )
    binding_file = _workspace_file(
        workspace_root,
        relative.as_posix(),
        label="adjudicated repair binding",
    )
    example_dir = workspace_root / "examples" / fixture
    _attempt_path(
        binding_file.parent,
        example_dir=example_dir,
        workspace_root=workspace_root,
    )
    binding_bytes = _read_bytes(
        binding_file, label="adjudicated repair binding"
    )
    binding = _load_json_bytes(
        binding_bytes, label="adjudicated repair binding"
    )
    binding_fields = set(binding)
    if binding_fields not in {BINDING_FIELDS_LEGACY, BINDING_FIELDS}:
        raise CritiqueRepairBridgeError("binding top-level fields are invalid")
    if binding.get("schema") != BINDING_SCHEMA:
        raise CritiqueRepairBridgeError("binding schema invalid")
    if binding.get("fixture") != fixture:
        raise CritiqueRepairBridgeError("binding fixture mismatch")
    if binding.get("attribution_state") != "exact":
        raise CritiqueRepairBridgeError("binding requires exact attribution")
    if binding.get("publication_acceptance") != "not_claimed":
        raise CritiqueRepairBridgeError(
            "binding publication acceptance must be not_claimed"
        )

    records: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    snapshots: dict[str, bytes] = {}
    aliases = {
        "machine_finding": ("report", "report_path", "report_sha256"),
        "current_render": ("before_render", "path", "sha256"),
        "current_pdf": ("before_pdf", "path", "sha256"),
        "crop_manifest": ("baseline_crop_manifest", "path", "sha256"),
    }
    labels = {
        "target_contract": "target contract",
        "semantic_attribution": "semantic attribution",
    }
    record_fields = (
        BINDING_RECORD_FIELDS
        if "semantic_attribution" in binding_fields
        else {
            key: value
            for key, value in BINDING_RECORD_FIELDS.items()
            if key != "semantic_attribution"
        }
    )
    for key, expected_fields in record_fields.items():
        label = labels.get(key, key)
        record = binding.get(key)
        if not isinstance(record, dict) or set(record) != expected_fields:
            raise CritiqueRepairBridgeError(f"binding {label} record is invalid")
        records[key] = record
        alias, path_key, hash_key = aliases.get(key, (key, "path", "sha256"))
        path = _workspace_file(
            workspace_root,
            record.get(path_key),
            label=f"binding {key}",
        )
        snapshot = _read_bytes(path, label=f"binding {key}")
        if record.get(hash_key) != _sha256_bytes(snapshot):
            raise CritiqueRepairBridgeError(f"binding {label} hash drift")
        paths[alias] = path
        snapshots[alias] = snapshot

    critique_id = records["critique"].get("finding_id")
    machine_id = records["machine_finding"].get("finding_id")
    if not isinstance(critique_id, str) or not critique_id.strip():
        raise CritiqueRepairBridgeError("binding critique finding id invalid")
    if not isinstance(machine_id, str) or not machine_id.strip():
        raise CritiqueRepairBridgeError("binding machine finding id invalid")
    if records["adjudication"].get("decision") != "apply":
        raise CritiqueRepairBridgeError("binding adjudication decision invalid")

    try:
        raw_adjudication = yaml.safe_load(
            snapshots["adjudication"].decode("utf-8")
        )
        adjudication = critique_adjudication.validate_adjudication(
            raw_adjudication
        )
    except (
        UnicodeDecodeError,
        yaml.YAMLError,
        critique_adjudication.CritiqueAdjudicationError,
    ) as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    if (
        adjudication.get("fixture") != fixture
        or adjudication.get("source_critique_hash")
        != _sha256_bytes(snapshots["critique"])
    ):
        raise CritiqueRepairBridgeError("binding adjudication lineage invalid")
    decisions = [
        item
        for item in adjudication.get("decisions", [])
        if isinstance(item, dict) and item.get("decision") == "apply"
    ]
    if len(decisions) != 1 or decisions[0].get("finding_id") != critique_id:
        raise CritiqueRepairBridgeError("binding adjudication apply decision invalid")
    evidence = decisions[0].get("repair_evidence")
    if (
        not isinstance(evidence, dict)
        or set(evidence)
        != {"report_path", "finding_id", "selector_registry_path"}
        or evidence.get("report_path")
        != records["machine_finding"].get("report_path")
        or evidence.get("finding_id") != machine_id
        or evidence.get("selector_registry_path")
        != records["selector_registry"].get("path")
    ):
        raise CritiqueRepairBridgeError("binding repair evidence lineage invalid")

    if paths["before_pdf"].stem != paths["before_render"].stem:
        raise CritiqueRepairBridgeError("binding PDF/render generation mismatch")
    report = _load_json_bytes(
        snapshots["report"], label="binding machine report"
    )
    try:
        expected_render = paths["before_render"].relative_to(example_dir).as_posix()
        expected_pdf = paths["before_pdf"].relative_to(example_dir).as_posix()
    except ValueError as exc:
        raise CritiqueRepairBridgeError(
            "binding render artifacts must remain inside the fixture"
        ) from exc
    _validate_crop_manifest_snapshot(
        snapshots["baseline_crop_manifest"],
        fixture=fixture,
        example_dir=example_dir,
        render_path=paths["before_render"],
        pdf_path=paths["before_pdf"],
        label="binding crop manifest",
        allow_legacy_minimal="semantic_attribution" not in binding_fields,
    )
    if "semantic_attribution" in binding_fields:
        _assert_current_critique_metadata(
            example_dir,
            plugin_root=Path(__file__).resolve().parents[1],
        )
    if (
        report.get("schema") != "figure-agent.text-collisions.v1"
        or report.get("fixture") != fixture
        or report.get("render_path") != expected_render
        or report.get("render_sha256")
        != _sha256_bytes(snapshots["before_render"])
        or report.get("render_pdf") != expected_pdf
        or report.get("render_pdf_sha256")
        != _sha256_bytes(snapshots["before_pdf"])
        or Path(expected_render).stem != Path(expected_pdf).stem
    ):
        raise CritiqueRepairBridgeError("binding machine report lineage invalid")

    selector_registry = _load_json_bytes(
        snapshots["selector_registry"], label="binding selector registry"
    )
    semantic_contract_record = selector_registry.get("semantic_contract")
    if "semantic_attribution" in binding_fields:
        if (
            not isinstance(semantic_contract_record, dict)
            or set(semantic_contract_record) != {"path", "sha256"}
        ):
            raise CritiqueRepairBridgeError(
                "binding semantic contract record is invalid"
            )
        semantic_contract_path = _workspace_file(
            workspace_root,
            semantic_contract_record.get("path"),
            label="binding semantic contract",
        )
        semantic_contract_bytes = _read_bytes(
            semantic_contract_path, label="binding semantic contract"
        )
        if semantic_contract_record.get("sha256") != _sha256_bytes(
            semantic_contract_bytes
        ):
            raise CritiqueRepairBridgeError("binding semantic contract hash drift")
        paths["semantic_contract"] = semantic_contract_path
        snapshots["semantic_contract"] = semantic_contract_bytes
    source_record = records["source"]
    if (
        selector_registry.get("schema")
        != "figure-agent.source-selector-registry.v1"
        or selector_registry.get("source_path") != source_record.get("path")
        or selector_registry.get("source_sha256") != source_record.get("sha256")
    ):
        raise CritiqueRepairBridgeError("binding selector source lineage invalid")
    target = _load_json_bytes(
        snapshots["target_contract"], label="binding target contract"
    )
    targets = target.get("targets")
    selected_target = (
        targets[0] if isinstance(targets, list) and len(targets) == 1 else None
    )
    if (
        set(target) != TARGET_CONTRACT_FIELDS
        or target.get("schema") != "figure-agent.repair-target-contract.v1"
        or target.get("source_path") != source_record.get("path")
        or target.get("source_sha256") != source_record.get("sha256")
        or not isinstance(selected_target, dict)
        or set(selected_target) != TARGET_FIELDS
        or selected_target.get("finding")
        != {
            "report_path": records["machine_finding"].get("report_path"),
            "id": machine_id,
        }
        or selected_target.get("attribution") != {"state": "exact"}
    ):
        raise CritiqueRepairBridgeError("binding target lineage invalid")
    target_selector = selected_target.get("selector")
    matching_selectors = [
        selector
        for selector in selector_registry.get("selectors", [])
        if isinstance(selector, dict)
        and isinstance(target_selector, dict)
        and selector.get("selector_id") == target_selector.get("selector_id")
    ]
    declared_selector = matching_selectors[0] if len(matching_selectors) == 1 else None
    if (
        not isinstance(target_selector, dict)
        or set(target_selector) != TARGET_SELECTOR_FIELDS
        or target_selector.get("kind") != "semantic_anchor"
        or not isinstance(declared_selector, dict)
        or declared_selector.get("repair_role") != "movable"
        or target_selector.get("anchor_start")
        != declared_selector.get("anchor_start")
        or target_selector.get("anchor_end") != declared_selector.get("anchor_end")
        or selected_target.get("repair_family")
        != declared_selector.get("repair_family")
        or selected_target.get("protected_invariants")
        != declared_selector.get("protected_invariants")
    ):
        raise CritiqueRepairBridgeError("binding target selector lineage invalid")
    try:
        source_attribution = finding_source_attribution.attribute_findings_from_bytes(
            report,
            selector_registry,
            source_bytes=snapshots["source"],
        )
    except finding_source_attribution.SourceAttributionError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    selected_source_attribution = [
        item
        for item in source_attribution.get("findings", [])
        if isinstance(item, dict) and item.get("finding_id") == machine_id
    ]
    if (
        len(selected_source_attribution) != 1
        or selected_source_attribution[0].get("state") != "exact"
        or selected_source_attribution[0].get("selected_selector_id")
        != target_selector.get("selector_id")
    ):
        raise CritiqueRepairBridgeError(
            "binding source attribution lineage invalid"
        )
    if "semantic_attribution" in binding_fields:
        semantic_attribution = _load_json_bytes(
            snapshots["semantic_attribution"],
            label="binding semantic attribution",
        )
        if (
            set(semantic_attribution)
            != {
                "schema",
                "fixture",
                "machine_finding",
                "semantic_contract",
                "source",
                "selector_id",
                "semantic_object_refs",
                "semantic_relation_refs",
                "attribution_state",
                "publication_acceptance",
            }
            or semantic_attribution.get("schema") != SEMANTIC_ATTRIBUTION_SCHEMA
            or semantic_attribution.get("fixture") != fixture
            or semantic_attribution.get("machine_finding")
            != {
                "report_path": records["machine_finding"].get("report_path"),
                "report_sha256": records["machine_finding"].get(
                    "report_sha256"
                ),
                "finding_id": machine_id,
            }
            or semantic_attribution.get("semantic_contract")
            != semantic_contract_record
            or semantic_attribution.get("source") != source_record
            or semantic_attribution.get("selector_id")
            != target_selector.get("selector_id")
            or semantic_attribution.get("attribution_state") != "exact"
            or semantic_attribution.get("publication_acceptance") != "not_claimed"
        ):
            raise CritiqueRepairBridgeError(
                "binding semantic attribution lineage invalid"
            )
        try:
            resolution = finding_source_attribution.resolve_semantic_selector(
                registry=selector_registry,
                attribution=source_attribution,
                finding_id=machine_id,
                semantic_contract=yaml.safe_load(
                    snapshots["semantic_contract"].decode("utf-8")
                ),
            )
        except (
            OSError,
            UnicodeDecodeError,
            yaml.YAMLError,
            finding_source_attribution.SourceAttributionError,
        ) as exc:
            raise CritiqueRepairBridgeError(str(exc)) from exc
        resolved_object_refs = resolution.get("semantic_object_refs")
        resolved_relation_refs = resolution.get("semantic_relation_refs")
        refs_are_valid = all(
            isinstance(refs, list)
            and bool(refs)
            and all(isinstance(ref, str) and bool(ref.strip()) for ref in refs)
            and len(set(refs)) == len(refs)
            for refs in (resolved_object_refs, resolved_relation_refs)
        )
        if (
            resolution.get("state") != "exact"
            or resolution.get("selector_id") != target_selector.get("selector_id")
            or resolution.get("missing_reference_kinds") != []
            or not refs_are_valid
            or semantic_attribution.get("semantic_object_refs")
            != resolved_object_refs
            or semantic_attribution.get("semantic_relation_refs")
            != resolved_relation_refs
        ):
            raise CritiqueRepairBridgeError(
                "binding semantic attribution references invalid"
            )
    for alias, path in paths.items():
        if _read_bytes(path, label=f"binding {alias}") != snapshots[alias]:
            raise CritiqueRepairBridgeError(
                f"binding {alias} changed during validation"
            )
    if (
        _read_bytes(binding_file, label="adjudicated repair binding")
        != binding_bytes
    ):
        raise CritiqueRepairBridgeError(
            "adjudicated repair binding changed during validation"
        )
    return binding, paths, _sha256_bytes(binding_bytes)


def validate_adjudicated_repair_binding(
    binding_path: str | Path,
    *,
    fixture: str,
    workspace_root: Path,
) -> tuple[dict[str, Any], dict[str, Path]]:
    """Validate the complete live authority graph for one repair binding."""
    binding, paths, _binding_sha256 = (
        validate_adjudicated_repair_binding_snapshot(
            binding_path,
            fixture=fixture,
            workspace_root=workspace_root,
        )
    )
    return binding, paths


def _selected_finding(frontmatter: dict[str, Any], finding_id: str) -> dict[str, Any]:
    matches = [
        finding
        for index, finding in enumerate(critique_findings(frontmatter))
        if critique_finding_id(finding, f"critique finding {index}") == finding_id
    ]
    if len(matches) != 1:
        raise CritiqueRepairBridgeError("critique finding must resolve exactly once")
    category = str(matches[0].get("category") or "").strip().lower()
    if category not in SUPPORTED_CATEGORIES:
        raise CritiqueRepairBridgeError("critique finding category is not supported")
    return matches[0]


def build_adjudicated_repair_target(
    *,
    example_dir: Path,
    critique_finding_id: str,
    attempt_dir: Path,
    workspace_root: Path,
    plugin_root: Path | None = None,
    human_attributor_id: str | None = None,
) -> dict[str, object]:
    """Publish an exact semantic binding or a human-attribution handoff."""
    workspace_root = workspace_root.resolve()
    plugin_root = (
        plugin_root.resolve()
        if plugin_root is not None
        else Path(__file__).resolve().parents[1]
    )
    example_dir = _workspace_directory(
        workspace_root, example_dir, label="example_dir"
    )
    if example_dir.parent != workspace_root / "examples":
        raise CritiqueRepairBridgeError(
            "example_dir must be a direct child of workspace examples"
        )
    try:
        fixture_identity.validate_fixture_name(example_dir.name)
    except ValueError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    attempt = _attempt_path(
        attempt_dir,
        example_dir=example_dir,
        workspace_root=workspace_root,
    )
    output_paths = {
        "source_attribution": attempt / "source_attribution.json",
        "semantic_attribution": attempt / "semantic_attribution.json",
        "target_contract": attempt / "repair_targets.json",
        "binding": attempt / "critique_repair_binding.json",
        "handoff": attempt / "attribution_handoff.json",
    }
    if any(path.exists() or path.is_symlink() for path in output_paths.values()):
        raise CritiqueRepairBridgeError("bridge output already exists")

    critique_path = example_dir / "critique.md"
    adjudication_path = _workspace_file(
        workspace_root,
        (
            example_dir.relative_to(workspace_root)
            / "critique_adjudication.yaml"
        ).as_posix(),
        label="critique adjudication",
    )
    try:
        (
            spec_path,
            crop_manifest_path,
            current_render_path,
            current_pdf_path,
        ) = _current_critique_inputs(
            example_dir,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
        )
    except critique_adjudication.CritiqueAdjudicationError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    input_snapshots = {
        path: _read_bytes(path, label=f"bridge input {path.name}")
        for path in (
            critique_path,
            adjudication_path,
            spec_path,
            current_render_path,
            current_pdf_path,
            crop_manifest_path,
        )
    }
    _assert_current_critique_metadata(example_dir, plugin_root=plugin_root)
    _assert_input_snapshots_current(input_snapshots)
    frontmatter = _load_critique_frontmatter_bytes(input_snapshots[critique_path])
    try:
        adjudication = critique_adjudication.validate_adjudication(
            _load_yaml_bytes(
                input_snapshots[adjudication_path],
                label="critique adjudication",
            )
        )
    except critique_adjudication.CritiqueAdjudicationError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    if adjudication.get("source_critique_hash") != _sha256_bytes(
        input_snapshots[critique_path]
    ):
        raise CritiqueRepairBridgeError("critique adjudication is stale")
    fixture = example_dir.name
    if adjudication.get("fixture") != fixture:
        raise CritiqueRepairBridgeError("adjudication fixture mismatch")
    _validate_crop_manifest_snapshot(
        input_snapshots[crop_manifest_path],
        fixture=fixture,
        example_dir=example_dir,
        render_path=current_render_path,
        pdf_path=current_pdf_path,
        label="current crop manifest",
    )
    _selected_finding(frontmatter, critique_finding_id)
    decisions = [
        item
        for item in adjudication.get("decisions", [])
        if isinstance(item, dict) and item.get("finding_id") == critique_finding_id
    ]
    if len(decisions) != 1 or decisions[0].get("decision") != "apply":
        raise CritiqueRepairBridgeError("one apply decision is required")
    evidence = decisions[0].get("repair_evidence")
    if not isinstance(evidence, dict):
        raise CritiqueRepairBridgeError("repair_evidence required for closed-loop apply")

    report_path = _workspace_file(
        workspace_root, evidence.get("report_path"), label="finding report"
    )
    registry_path = _workspace_file(
        workspace_root,
        evidence.get("selector_registry_path"),
        label="selector registry",
    )
    input_snapshots[report_path] = _read_bytes(
        report_path, label="bridge input finding report"
    )
    input_snapshots[registry_path] = _read_bytes(
        registry_path, label="bridge input selector registry"
    )
    report = _load_json_bytes(
        input_snapshots[report_path], label="finding report"
    )
    _validate_report_lineage(
        report,
        fixture=fixture,
        current_render=current_render_path,
        current_pdf=current_pdf_path,
        example_dir=example_dir,
        workspace_root=workspace_root,
        current_render_sha256=_sha256_bytes(
            input_snapshots[current_render_path]
        ),
        current_pdf_sha256=_sha256_bytes(input_snapshots[current_pdf_path]),
    )
    registry = _load_json_bytes(
        input_snapshots[registry_path], label="selector registry"
    )
    source_path = _workspace_file(
        workspace_root, registry.get("source_path"), label="bound source"
    )
    input_snapshots[source_path] = _read_bytes(
        source_path, label="bridge input bound source"
    )
    machine_finding_id = str(evidence.get("finding_id") or "")
    try:
        attribution = finding_source_attribution.attribute_findings_from_bytes(
            report,
            registry,
            source_bytes=input_snapshots[source_path],
        )
        report_relative = _relative(
            report_path, root=workspace_root, label="finding report"
        )
    except finding_source_attribution.SourceAttributionError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc

    selected = [
        item
        for item in attribution.get("findings", [])
        if isinstance(item, dict) and item.get("finding_id") == machine_finding_id
    ]
    if len(selected) != 1:
        raise CritiqueRepairBridgeError(
            "selected finding attribution must resolve once"
        )
    source_resolution = selected[0]
    semantic_contract_record = registry.get("semantic_contract")
    semantic_contract_path: Path | None = None
    if "semantic_contract" in registry:
        if (
            not isinstance(semantic_contract_record, dict)
            or set(semantic_contract_record) != {"path", "sha256"}
        ):
            raise CritiqueRepairBridgeError(
                "selector registry semantic contract record is invalid"
            )
        semantic_contract_path = _workspace_file(
            workspace_root,
            semantic_contract_record.get("path"),
            label="semantic contract",
        )
        input_snapshots[semantic_contract_path] = _read_bytes(
            semantic_contract_path, label="bridge input semantic contract"
        )
        semantic_contract_bytes = input_snapshots[semantic_contract_path]
        if semantic_contract_record.get("sha256") != _sha256_bytes(
            semantic_contract_bytes
        ):
            raise CritiqueRepairBridgeError("semantic contract hash drift")
        semantic_contract = _load_yaml_bytes(
            semantic_contract_bytes, label="semantic contract"
        )
        try:
            semantic_resolution = (
                finding_source_attribution.resolve_semantic_selector(
                    registry=registry,
                    attribution=attribution,
                    finding_id=machine_finding_id,
                    semantic_contract=semantic_contract,
                )
            )
        except finding_source_attribution.SourceAttributionError as exc:
            raise CritiqueRepairBridgeError(str(exc)) from exc
    elif source_resolution.get("state") != "exact":
        semantic_resolution = {
            "state": source_resolution.get("state"),
            "reason_code": source_resolution.get("reason_code"),
            "candidate_selector_ids": sorted(
                {
                    item["selector_id"]
                    for item in source_resolution.get("matched_selectors", [])
                    if isinstance(item, dict)
                    and item.get("repair_role") == "movable"
                    and isinstance(item.get("selector_id"), str)
                }
            ),
            "missing_reference_kinds": [
                "semantic_object",
                "semantic_relation",
            ],
        }
    else:
        semantic_resolution = {
            "state": "unbound",
            "reason_code": "semantic_boundary_missing",
            "candidate_selector_ids": [source_resolution["selected_selector_id"]],
            "missing_reference_kinds": [
                "semantic_object",
                "semantic_relation",
            ],
        }
    if semantic_resolution["state"] != "exact":
        if not isinstance(human_attributor_id, str) or not human_attributor_id.strip():
            raise CritiqueRepairBridgeError(
                "human_attributor_id is required for attribution handoff"
            )
        handoff: dict[str, object] = {
            "schema": ATTRIBUTION_HANDOFF_SCHEMA,
            "fixture": fixture,
            "machine_finding": {
                "report_path": report_relative,
                "report_sha256": _sha256_bytes(input_snapshots[report_path]),
                "finding_id": machine_finding_id,
            },
            "evidence_role": "attribution_handoff",
            "attempt_state": "adjudicated_unbound",
            "required_actor": {
                "id": human_attributor_id.strip(),
                "role": "human_attributor",
            },
            "reason_code": semantic_resolution["reason_code"],
            "candidate_selector_ids": semantic_resolution[
                "candidate_selector_ids"
            ],
            "missing_reference_kinds": semantic_resolution[
                "missing_reference_kinds"
            ],
            "allowed_action": "declare_or_select_semantic_source_authority",
            "forbidden_actions": [
                "source_mutation",
                "repair_target_materialization",
                "publication_acceptance",
            ],
            "publication_acceptance": "not_claimed",
        }
        handoff_path = output_paths["handoff"]
        try:
            with repair_transaction.exclusive_lock(
                attempt / ".critique-repair-bridge.lock",
                owner="critique_repair_bridge",
            ):
                if any(
                    path.exists() or path.is_symlink()
                    for path in output_paths.values()
                ):
                    raise CritiqueRepairBridgeError("bridge output already exists")
                _assert_input_snapshots_current(input_snapshots)
                repair_transaction.atomic_create_json(handoff_path, handoff)
        except repair_transaction.RepairTransactionError as exc:
            raise CritiqueRepairBridgeError(
                "bridge transaction already active"
            ) from exc
        return handoff

    try:
        target_contract = finding_source_attribution.build_repair_target_contract(
            report_path=report_relative,
            report=report,
            registry=registry,
            attribution=attribution,
            finding_id=machine_finding_id,
        )
    except finding_source_attribution.SourceAttributionError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc

    source_record = {
        "path": _relative(source_path, root=workspace_root, label="bound source"),
        "sha256": _sha256_bytes(input_snapshots[source_path]),
    }
    machine_finding_record = {
        "report_path": report_relative,
        "report_sha256": _sha256_bytes(input_snapshots[report_path]),
        "finding_id": machine_finding_id,
    }
    semantic_attribution: dict[str, object] = {
        "schema": SEMANTIC_ATTRIBUTION_SCHEMA,
        "fixture": fixture,
        "machine_finding": machine_finding_record,
        "semantic_contract": semantic_contract_record,
        "source": source_record,
        "selector_id": semantic_resolution["selector_id"],
        "semantic_object_refs": semantic_resolution["semantic_object_refs"],
        "semantic_relation_refs": semantic_resolution["semantic_relation_refs"],
        "attribution_state": "exact",
        "publication_acceptance": "not_claimed",
    }

    target_contract_sha256 = _json_payload_sha256(target_contract)
    binding: dict[str, object] = {
        "schema": BINDING_SCHEMA,
        "fixture": fixture,
        "critique": {
            "path": _relative(critique_path, root=workspace_root, label="critique"),
            "sha256": _sha256_bytes(input_snapshots[critique_path]),
            "finding_id": critique_finding_id,
        },
        "adjudication": {
            "path": _relative(
                adjudication_path, root=workspace_root, label="adjudication"
            ),
            "sha256": _sha256_bytes(input_snapshots[adjudication_path]),
            "decision": "apply",
        },
        "machine_finding": machine_finding_record,
        "selector_registry": {
            "path": _relative(
                registry_path, root=workspace_root, label="selector registry"
            ),
            "sha256": _sha256_bytes(input_snapshots[registry_path]),
        },
        "source": source_record,
        "spec": {
            "path": _relative(spec_path, root=workspace_root, label="spec"),
            "sha256": _sha256_bytes(input_snapshots[spec_path]),
        },
        "current_render": {
            "path": _relative(
                current_render_path,
                root=workspace_root,
                label="current render",
            ),
            "sha256": _sha256_bytes(input_snapshots[current_render_path]),
        },
        "current_pdf": {
            "path": _relative(
                current_pdf_path,
                root=workspace_root,
                label="current PDF",
            ),
            "sha256": _sha256_bytes(input_snapshots[current_pdf_path]),
        },
        "crop_manifest": {
            "path": _relative(
                crop_manifest_path,
                root=workspace_root,
                label="current crop manifest",
            ),
            "sha256": _sha256_bytes(input_snapshots[crop_manifest_path]),
        },
        "attribution_state": "exact",
        "target_contract": {
            "path": _relative(
                output_paths["target_contract"],
                root=workspace_root,
                label="target contract",
            ),
            "sha256": target_contract_sha256,
        },
        "semantic_attribution": {
            "path": _relative(
                output_paths["semantic_attribution"],
                root=workspace_root,
                label="semantic attribution",
            ),
            "sha256": _json_payload_sha256(semantic_attribution),
        },
        "publication_acceptance": "not_claimed",
    }
    payloads = {
        output_paths["source_attribution"]: attribution,
        output_paths["semantic_attribution"]: semantic_attribution,
        output_paths["target_contract"]: target_contract,
        output_paths["binding"]: binding,
    }
    expected_hashes = {
        path: _json_payload_sha256(payload)
        for path, payload in payloads.items()
    }
    try:
        with repair_transaction.exclusive_lock(
            attempt / ".critique-repair-bridge.lock",
            owner="critique_repair_bridge",
        ):
            if any(path.exists() or path.is_symlink() for path in output_paths.values()):
                raise CritiqueRepairBridgeError("bridge output already exists")
            _assert_input_snapshots_current(input_snapshots)
            try:
                for path, payload in payloads.items():
                    repair_transaction.atomic_create_json(path, payload)
            except Exception:
                for path, expected_hash in expected_hashes.items():
                    if path.is_file() and _sha256(path) == expected_hash:
                        path.unlink()
                raise
    except repair_transaction.RepairTransactionError as exc:
        raise CritiqueRepairBridgeError(
            "bridge transaction already active"
        ) from exc
    return binding


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path,
    workspace_root: Path,
) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent adjudicated-repair-target")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--finding-id", required=True)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--human-attributor-id")
    args = parser.parse_args(argv)
    try:
        fixture_identity.validate_fixture_name(args.fixture)
        attempt = workspace_root / Path(args.attempt_dir)
        result = build_adjudicated_repair_target(
            example_dir=workspace_root / "examples" / args.fixture,
            critique_finding_id=args.finding_id,
            attempt_dir=attempt,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
            human_attributor_id=args.human_attributor_id,
        )
    except (OSError, UnicodeDecodeError, ValueError, CritiqueRepairBridgeError) as exc:
        print(f"fig-agent adjudicated-repair-target: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
