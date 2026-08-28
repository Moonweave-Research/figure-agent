#!/usr/bin/env python3
"""Validate a ResearchOS paper-artifact registry without promoting its figures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

REGISTRY_SCHEMA = "researchos.figure-registry.v1"
REPORT_SCHEMA = "researchos.paper-artifact-registry-check.v1"
VALID_LIFECYCLES = {"canonical", "paper_draft", "paper_partial"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finding(code: str, *, figure_id: str | None = None, **details: object) -> dict[str, object]:
    finding: dict[str, object] = {"code": code, **details}
    if figure_id is not None:
        finding["figure_id"] = figure_id
    return finding


def _artifact_entries(figure: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    paper_artifact = figure.get("paper_artifact")
    if isinstance(paper_artifact, dict):
        entries.extend(value for value in paper_artifact.values() if isinstance(value, dict))
    paper_components = figure.get("paper_components")
    if isinstance(paper_components, list):
        entries.extend(value for value in paper_components if isinstance(value, dict))
    return entries


def build_report(root: Path, registry_path: Path) -> dict[str, object]:
    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    verified: list[dict[str, str]] = []
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return {
            "schema": REPORT_SCHEMA,
            "state": "INVALID",
            "registry": str(registry_path),
            "errors": [_finding("registry_unreadable", detail=str(exc))],
            "warnings": warnings,
            "verified": verified,
        }

    if not isinstance(payload, dict) or payload.get("schema") != REGISTRY_SCHEMA:
        actual = payload.get("schema") if isinstance(payload, dict) else None
        return {
            "schema": REPORT_SCHEMA,
            "state": "INVALID",
            "registry": str(registry_path),
            "errors": [
                _finding(
                    "invalid_registry_schema",
                    expected=REGISTRY_SCHEMA,
                    actual=actual,
                )
            ],
            "warnings": warnings,
            "verified": verified,
        }

    figures = payload.get("figures")
    if not isinstance(figures, dict) or not figures:
        errors.append(_finding("missing_figures"))
        figures = {}

    for figure_id, raw_figure in sorted(figures.items()):
        if not isinstance(figure_id, str) or not isinstance(raw_figure, dict):
            errors.append(_finding("invalid_figure_entry", figure_id=str(figure_id)))
            continue
        lifecycle = raw_figure.get("lifecycle")
        if lifecycle not in VALID_LIFECYCLES:
            errors.append(_finding("invalid_lifecycle", figure_id=figure_id, lifecycle=lifecycle))
        entries = _artifact_entries(raw_figure)
        if lifecycle == "paper_partial" and not isinstance(
            raw_figure.get("paper_components"), list
        ):
            errors.append(_finding("partial_figure_missing_components", figure_id=figure_id))
        if lifecycle != "paper_partial" and not isinstance(raw_figure.get("paper_artifact"), dict):
            errors.append(_finding("figure_missing_paper_artifact", figure_id=figure_id))
        if not entries:
            errors.append(_finding("figure_without_verifiable_artifact", figure_id=figure_id))

        for entry in entries:
            relative_path = entry.get("path")
            if not isinstance(relative_path, str) or not relative_path:
                errors.append(_finding("artifact_missing_path", figure_id=figure_id))
                continue
            candidate = Path(relative_path)
            if candidate.is_absolute() or ".." in candidate.parts:
                errors.append(
                    _finding(
                        "artifact_path_not_project_relative",
                        figure_id=figure_id,
                        path=relative_path,
                    )
                )
                continue
            artifact_path = root / candidate
            if not artifact_path.is_file():
                errors.append(_finding("artifact_missing", figure_id=figure_id, path=relative_path))
                continue
            expected_hash = entry.get("sha256")
            if expected_hash is not None and (
                not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash)
            ):
                errors.append(
                    _finding("invalid_artifact_sha256", figure_id=figure_id, path=relative_path)
                )
                continue
            actual_hash = _sha256(artifact_path)
            if expected_hash is not None and actual_hash != expected_hash:
                errors.append(
                    _finding(
                        "artifact_hash_mismatch",
                        figure_id=figure_id,
                        path=relative_path,
                        expected=expected_hash,
                        actual=actual_hash,
                    )
                )
                continue
            if expected_hash is None:
                warnings.append(
                    _finding(
                        "artifact_hash_unpinned",
                        figure_id=figure_id,
                        path=relative_path,
                    )
                )
            verified.append({"figure_id": figure_id, "path": relative_path, "sha256": actual_hash})

        candidate_links = raw_figure.get("candidate_links", [])
        if candidate_links is not None and not isinstance(candidate_links, list):
            errors.append(_finding("invalid_candidate_links", figure_id=figure_id))
        elif isinstance(candidate_links, list):
            for candidate_link in candidate_links:
                if not isinstance(candidate_link, dict) or candidate_link.get(
                    "lifecycle"
                ) != "candidate":
                    errors.append(_finding("invalid_candidate_link", figure_id=figure_id))

    return {
        "schema": REPORT_SCHEMA,
        "state": "PASSED" if not errors else "FAILED",
        "registry": str(registry_path),
        "root": str(root),
        "errors": errors,
        "warnings": warnings,
        "verified": verified,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    registry_path = args.registry if args.registry.is_absolute() else root / args.registry
    report = build_report(root, registry_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{report['state']}: {len(report['verified'])} artifact binding(s) verified")
        for finding in report["errors"]:
            print(f"ERROR {finding}")
        for finding in report["warnings"]:
            print(f"WARNING {finding}")
    return 0 if report["state"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
