"""Read critique.md frontmatter and traverse critique findings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class CritiqueContractError(ValueError):
    """Expected user-facing error for malformed critique contract files."""


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CritiqueContractError(f"{label} must be a mapping")
    return value


def load_critique_frontmatter(path: Path) -> dict[str, Any]:
    """Load critique.md YAML frontmatter."""
    if not path.is_file():
        raise CritiqueContractError(f"missing critique: {path}")

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise CritiqueContractError(f"invalid UTF-8 in {path}: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise CritiqueContractError(f"missing critique frontmatter: {path}")

    end_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if end_index is None:
        raise CritiqueContractError(f"unterminated critique frontmatter: {path}")

    try:
        data = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError as exc:
        raise CritiqueContractError(f"invalid YAML in {path}: {exc}") from exc
    return require_mapping(data, "critique frontmatter")


def critique_finding_id(finding: dict[str, Any], label: str) -> str:
    """Return a validated critique finding id."""
    value = finding.get("id")
    if not isinstance(value, str) or not value.strip():
        raise CritiqueContractError(f"{label}.id must be a non-empty string")
    return value.strip()


def critique_findings(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    """Return panel-level and top-level critique findings in adjudication order."""
    findings: list[dict[str, Any]] = []

    panels = frontmatter.get("panels", [])
    if panels is None:
        panels = []
    if not isinstance(panels, list):
        raise CritiqueContractError("critique frontmatter.panels must be a list")
    for panel_index, raw_panel in enumerate(panels):
        panel_label = f"critique frontmatter.panels[{panel_index}]"
        panel = require_mapping(raw_panel, panel_label)
        panel_findings = panel.get("findings", [])
        if panel_findings is None:
            panel_findings = []
        if not isinstance(panel_findings, list):
            raise CritiqueContractError(f"{panel_label}.findings must be a list")
        for finding_index, raw_finding in enumerate(panel_findings):
            finding_label = f"{panel_label}.findings[{finding_index}]"
            findings.append(require_mapping(raw_finding, finding_label))

    top_level_findings = frontmatter.get("findings", [])
    if top_level_findings is None:
        top_level_findings = []
    if not isinstance(top_level_findings, list):
        raise CritiqueContractError("critique frontmatter.findings must be a list")
    for finding_index, raw_finding in enumerate(top_level_findings):
        finding_label = f"critique frontmatter.findings[{finding_index}]"
        findings.append(require_mapping(raw_finding, finding_label))

    return findings
