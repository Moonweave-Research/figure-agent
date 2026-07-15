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
from critique_contract import (
    critique_finding_id,
    critique_findings,
    load_critique_frontmatter,
)

BINDING_SCHEMA = "figure-agent.adjudicated-repair-binding.v1"
REPAIR_ATTEMPT = re.compile(r"execution-repair-v[1-9][0-9]*")
SUPPORTED_CATEGORIES = frozenset({"hierarchy", "label_placement", "whitespace"})
CROP_MANIFEST_SCHEMA = "figure-agent.audit-crop-manifest.v1"


class CritiqueRepairBridgeError(ValueError):
    """Raised when an adjudicated finding cannot be bound exactly and freshly."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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
        mismatches = critique_adjudication._critique_metadata_mismatches(
            example_dir,
            repo_root=plugin_root,
        )
    except critique_adjudication.CritiqueAdjudicationError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    if mismatches:
        raise CritiqueRepairBridgeError("; ".join(mismatches))
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
) -> None:
    expected_render_path = current_render.relative_to(example_dir).as_posix()
    expected_pdf_path = current_pdf.relative_to(example_dir).as_posix()
    report_render_path = Path(str(report.get("render_path") or ""))
    report_pdf_path = Path(str(report.get("render_pdf") or ""))
    if (
        report.get("schema") != "figure-agent.text-collisions.v1"
        or report.get("fixture") != fixture
        or report.get("render_path") != expected_render_path
        or report.get("render_sha256") != _sha256(current_render)
        or report.get("render_pdf") != expected_pdf_path
        or report.get("render_pdf_sha256") != _sha256(current_pdf)
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
) -> dict[str, object]:
    """Write additive exact-attribution artifacts for one fresh apply decision."""
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
        "attribution": attempt / "source_attribution.json",
        "target_contract": attempt / "repair_targets.json",
        "binding": attempt / "critique_repair_binding.json",
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
        frontmatter = load_critique_frontmatter(critique_path)
        adjudication = critique_adjudication.load_adjudication(adjudication_path)
        if critique_adjudication.adjudication_is_stale(
            adjudication_path, critique_path
        ):
            raise CritiqueRepairBridgeError("critique adjudication is stale")
    except critique_adjudication.CritiqueAdjudicationError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc
    fixture = example_dir.name
    if adjudication.get("fixture") != fixture:
        raise CritiqueRepairBridgeError("adjudication fixture mismatch")
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
    report = _load_json(report_path, label="finding report")
    _validate_report_lineage(
        report,
        fixture=fixture,
        current_render=current_render_path,
        current_pdf=current_pdf_path,
        example_dir=example_dir,
        workspace_root=workspace_root,
    )
    registry = _load_json(registry_path, label="selector registry")
    source_path = _workspace_file(
        workspace_root, registry.get("source_path"), label="bound source"
    )
    machine_finding_id = str(evidence.get("finding_id") or "")
    try:
        attribution = finding_source_attribution.attribute_findings(
            report, registry, source_path=source_path
        )
        selected = [
            item
            for item in attribution.get("findings", [])
            if isinstance(item, dict)
            and item.get("finding_id") == machine_finding_id
        ]
        if len(selected) != 1 or selected[0].get("state") != "exact":
            raise CritiqueRepairBridgeError(
                "exact attribution required for selected machine finding"
            )
        report_relative = _relative(
            report_path, root=workspace_root, label="finding report"
        )
        target_contract = finding_source_attribution.build_repair_target_contract(
            report_path=report_relative,
            report=report,
            registry=registry,
            attribution=attribution,
            finding_id=machine_finding_id,
        )
    except finding_source_attribution.SourceAttributionError as exc:
        raise CritiqueRepairBridgeError(str(exc)) from exc

    target_contract_sha256 = _json_payload_sha256(target_contract)
    binding: dict[str, object] = {
        "schema": BINDING_SCHEMA,
        "fixture": fixture,
        "critique": {
            "path": _relative(critique_path, root=workspace_root, label="critique"),
            "sha256": _sha256(critique_path),
            "finding_id": critique_finding_id,
        },
        "adjudication": {
            "path": _relative(
                adjudication_path, root=workspace_root, label="adjudication"
            ),
            "sha256": _sha256(adjudication_path),
            "decision": "apply",
        },
        "machine_finding": {
            "report_path": report_relative,
            "report_sha256": _sha256(report_path),
            "finding_id": machine_finding_id,
        },
        "selector_registry": {
            "path": _relative(
                registry_path, root=workspace_root, label="selector registry"
            ),
            "sha256": _sha256(registry_path),
        },
        "source": {
            "path": _relative(source_path, root=workspace_root, label="bound source"),
            "sha256": _sha256(source_path),
        },
        "spec": {
            "path": _relative(spec_path, root=workspace_root, label="spec"),
            "sha256": _sha256(spec_path),
        },
        "current_render": {
            "path": _relative(
                current_render_path,
                root=workspace_root,
                label="current render",
            ),
            "sha256": _sha256(current_render_path),
        },
        "current_pdf": {
            "path": _relative(
                current_pdf_path,
                root=workspace_root,
                label="current PDF",
            ),
            "sha256": _sha256(current_pdf_path),
        },
        "crop_manifest": {
            "path": _relative(
                crop_manifest_path,
                root=workspace_root,
                label="current crop manifest",
            ),
            "sha256": _sha256(crop_manifest_path),
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
        "publication_acceptance": "not_claimed",
    }
    payloads = {
        output_paths["attribution"]: attribution,
        output_paths["target_contract"]: target_contract,
        output_paths["binding"]: binding,
    }
    expected_hashes = {
        path: _json_payload_sha256(payload)
        for path, payload in payloads.items()
    }
    input_paths = (
        critique_path,
        adjudication_path,
        report_path,
        registry_path,
        source_path,
        spec_path,
        current_render_path,
        current_pdf_path,
        crop_manifest_path,
    )
    input_hashes = {path: _sha256(path) for path in input_paths}
    try:
        with repair_transaction.exclusive_lock(
            attempt / ".critique-repair-bridge.lock",
            owner="critique_repair_bridge",
        ):
            if any(path.exists() or path.is_symlink() for path in output_paths.values()):
                raise CritiqueRepairBridgeError("bridge output already exists")
            if any(_sha256(path) != digest for path, digest in input_hashes.items()):
                raise CritiqueRepairBridgeError("bridge input drift before publication")
            if critique_adjudication.adjudication_is_stale(
                adjudication_path, critique_path
            ):
                raise CritiqueRepairBridgeError("critique adjudication is stale")
            _validate_report_lineage(
                _load_json(report_path, label="finding report"),
                fixture=fixture,
                current_render=current_render_path,
                current_pdf=current_pdf_path,
                example_dir=example_dir,
                workspace_root=workspace_root,
            )
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
        )
    except (OSError, UnicodeDecodeError, ValueError, CritiqueRepairBridgeError) as exc:
        print(f"fig-agent adjudicated-repair-target: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
