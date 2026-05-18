"""Parse and validate critique adjudication decisions."""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Any

import yaml
from quality_manifest import file_sha256

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.critique-adjudication.v1"
CRITIQUE_SCHEMA_V1 = "figure-agent.critique.v1"
CRITIQUE_SCHEMA_V1_1 = "figure-agent.critique.v1.1"
ALLOWED_DECISIONS = frozenset({"apply", "dismiss", "defer", "needs_human", "resolved"})
_PATCH_EVIDENCE_REQUIRED = frozenset({"apply", "resolved"})
_ALLOWED_CONCEPTUAL_REFERENCES = frozenset(
    {"provided_reference", "briefing", "reference_pack", "not_provided"}
)


class CritiqueAdjudicationError(ValueError):
    """Expected user-facing error for malformed critique adjudication files."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CritiqueAdjudicationError(f"{label} must be a mapping")
    return value


def _require_non_empty_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise CritiqueAdjudicationError(f"{label} must be a non-empty list")
    return value


def _require_mapping_items(value: Any, label: str) -> list[dict[str, Any]]:
    items = _require_non_empty_list(value, label)
    mappings: list[dict[str, Any]] = []
    for index, raw_item in enumerate(items):
        mappings.append(_require_mapping(raw_item, f"{label}[{index}]"))
    return mappings


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CritiqueAdjudicationError(f"{label}.{key} must be a non-empty string")
    return value


def _validate_hash(value: str) -> None:
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise CritiqueAdjudicationError(
            "adjudication.source_critique_hash must be a sha256-prefixed string"
        )


def validate_adjudication(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a critique adjudication mapping and return it unchanged."""
    data = _require_mapping(data, "adjudication")
    schema = data.get("schema")
    if schema != SCHEMA:
        raise CritiqueAdjudicationError(f"adjudication.schema must be {SCHEMA}")

    _require_non_empty_string(data, "fixture", label="adjudication")
    source_hash = _require_non_empty_string(data, "source_critique_hash", label="adjudication")
    _validate_hash(source_hash)

    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise CritiqueAdjudicationError("adjudication.decisions must be a list")

    seen_finding_ids: set[str] = set()
    for index, raw_decision in enumerate(decisions):
        decision_label = f"adjudication.decisions[{index}]"
        decision_item = _require_mapping(raw_decision, decision_label)
        finding_id = _require_non_empty_string(decision_item, "finding_id", label=decision_label)
        if finding_id in seen_finding_ids:
            raise CritiqueAdjudicationError(
                f"{decision_label}.duplicate finding_id: {finding_id}"
            )
        seen_finding_ids.add(finding_id)
        decision_value = _require_non_empty_string(decision_item, "decision", label=decision_label)
        if decision_value not in ALLOWED_DECISIONS:
            allowed = ", ".join(sorted(ALLOWED_DECISIONS))
            raise CritiqueAdjudicationError(
                f"{decision_label}.decision must be one of: {allowed}"
            )
        _require_non_empty_string(decision_item, "reason", label=decision_label)
        if decision_value in _PATCH_EVIDENCE_REQUIRED:
            _require_non_empty_string(decision_item, "patch_target", label=decision_label)
            _require_non_empty_string(decision_item, "evidence", label=decision_label)

    return data


def load_adjudication(path: Path) -> dict[str, Any]:
    """Load and validate a critique adjudication YAML file."""
    if not path.is_file():
        raise CritiqueAdjudicationError(f"missing adjudication: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise CritiqueAdjudicationError(f"invalid UTF-8 in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CritiqueAdjudicationError(f"invalid YAML in {path}: {exc}") from exc
    return validate_adjudication(data)


def write_adjudication(path: Path, data: dict[str, Any]) -> None:
    """Validate and write a critique adjudication YAML file."""
    validated = validate_adjudication(data)
    path.write_text(
        yaml.safe_dump(validated, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _critique_frontmatter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CritiqueAdjudicationError(f"missing critique: {path}")

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise CritiqueAdjudicationError(f"invalid UTF-8 in {path}: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise CritiqueAdjudicationError(f"missing critique frontmatter: {path}")

    end_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if end_index is None:
        raise CritiqueAdjudicationError(f"unterminated critique frontmatter: {path}")

    try:
        data = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError as exc:
        raise CritiqueAdjudicationError(f"invalid YAML in {path}: {exc}") from exc
    return _require_mapping(data, "critique frontmatter")


def _finding_id(finding: dict[str, Any], label: str) -> str:
    value = finding.get("id")
    if not isinstance(value, str) or not value.strip():
        raise CritiqueAdjudicationError(f"{label}.id must be a non-empty string")
    return value.strip()


def _validate_v1_1_audit(frontmatter: dict[str, Any]) -> None:
    audit = _require_mapping(
        frontmatter.get("audit_enumeration"),
        "critique frontmatter.audit_enumeration",
    )
    structural = _require_mapping(
        audit.get("structural_completeness"),
        "critique frontmatter.audit_enumeration.structural_completeness",
    )
    _require_mapping_items(
        structural.get("components"),
        "critique frontmatter.audit_enumeration.structural_completeness.components",
    )
    _require_mapping_items(
        structural.get("missing_from_reference"),
        (
            "critique frontmatter.audit_enumeration."
            "structural_completeness.missing_from_reference"
        ),
    )
    _require_mapping_items(
        audit.get("label_target_matching"),
        "critique frontmatter.audit_enumeration.label_target_matching",
    )
    _require_mapping_items(
        audit.get("physical_plausibility"),
        "critique frontmatter.audit_enumeration.physical_plausibility",
    )
    conceptual_items = _require_mapping_items(
        audit.get("conceptual_completeness"),
        "critique frontmatter.audit_enumeration.conceptual_completeness",
    )
    for index, item in enumerate(conceptual_items):
        reference = item.get("reference")
        if reference not in _ALLOWED_CONCEPTUAL_REFERENCES:
            allowed = ", ".join(sorted(_ALLOWED_CONCEPTUAL_REFERENCES))
            raise CritiqueAdjudicationError(
                "critique frontmatter.audit_enumeration.conceptual_completeness"
                f"[{index}].reference must be one of: {allowed}"
            )


def _patch_target_from_tex_lines(fixture: str, finding: dict[str, Any]) -> str:
    tex_lines = finding.get("tex_lines")
    if (
        not isinstance(tex_lines, list)
        or len(tex_lines) != 2
        or not all(isinstance(value, int) for value in tex_lines)
    ):
        return ""
    start, end = tex_lines
    return f"examples/{fixture}/{fixture}.tex lines {start}-{end}"


def _findings_from_critique(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    panels = frontmatter.get("panels", [])
    if panels is None:
        panels = []
    if not isinstance(panels, list):
        raise CritiqueAdjudicationError("critique frontmatter.panels must be a list")
    for panel_index, raw_panel in enumerate(panels):
        panel_label = f"critique frontmatter.panels[{panel_index}]"
        panel = _require_mapping(raw_panel, panel_label)
        panel_findings = panel.get("findings", [])
        if panel_findings is None:
            panel_findings = []
        if not isinstance(panel_findings, list):
            raise CritiqueAdjudicationError(f"{panel_label}.findings must be a list")
        for finding_index, raw_finding in enumerate(panel_findings):
            finding_label = f"{panel_label}.findings[{finding_index}]"
            findings.append(_require_mapping(raw_finding, finding_label))

    top_level_findings = frontmatter.get("findings", [])
    if top_level_findings is None:
        top_level_findings = []
    if not isinstance(top_level_findings, list):
        raise CritiqueAdjudicationError("critique frontmatter.findings must be a list")
    for finding_index, raw_finding in enumerate(top_level_findings):
        finding_label = f"critique frontmatter.findings[{finding_index}]"
        findings.append(_require_mapping(raw_finding, finding_label))

    return findings


def build_adjudication_scaffold(example_dir: Path) -> dict[str, Any]:
    """Build a conservative adjudication scaffold from critique.md frontmatter."""
    critique_path = example_dir / "critique.md"
    frontmatter = _critique_frontmatter(critique_path)
    critique_schema = frontmatter.get("schema")
    if critique_schema == CRITIQUE_SCHEMA_V1:
        warnings.warn(
            (
                f"{CRITIQUE_SCHEMA_V1} is legacy; v1.1 critiques should include "
                "audit_enumeration"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
    elif critique_schema == CRITIQUE_SCHEMA_V1_1:
        _validate_v1_1_audit(frontmatter)
    elif isinstance(critique_schema, str) and critique_schema.startswith("figure-agent.critique."):
        raise CritiqueAdjudicationError(f"unsupported critique schema: {critique_schema}")
    fixture_value = frontmatter.get("fixture")
    fixture = (
        fixture_value.strip()
        if isinstance(fixture_value, str) and fixture_value.strip()
        else example_dir.name
    )

    decisions: list[dict[str, str]] = []
    for index, finding in enumerate(_findings_from_critique(frontmatter)):
        label = f"critique finding {index}"
        finding_id = _finding_id(finding, label)
        patch_target = _patch_target_from_tex_lines(fixture, finding)
        status = str(finding.get("status", "")).strip().lower()
        if status == "resolved":
            decisions.append(
                {
                    "finding_id": finding_id,
                    "decision": "resolved",
                    "reason": f"Critique marks {finding_id} as resolved.",
                    "patch_target": patch_target or f"examples/{fixture}/{fixture}.tex",
                    "evidence": f"critique.md marks {finding_id} status resolved.",
                }
            )
        else:
            decisions.append(
                {
                    "finding_id": finding_id,
                    "decision": "needs_human",
                    "reason": (
                        f"Review {finding_id} before selecting apply, dismiss, defer, or resolved."
                    ),
                    "patch_target": patch_target,
                    "evidence": f"critique.md finding {finding_id}.",
                }
            )

    return validate_adjudication(
        {
            "schema": SCHEMA,
            "fixture": fixture,
            "source_critique_hash": file_sha256(critique_path),
            "decisions": decisions,
        }
    )


def scaffold_adjudication(example_dir: Path, *, force: bool = False) -> Path:
    """Write critique_adjudication.yaml from critique.md unless it already exists."""
    path = example_dir / "critique_adjudication.yaml"
    if path.exists() and not force:
        raise CritiqueAdjudicationError(f"{path} already exists; pass --force to overwrite")
    write_adjudication(path, build_adjudication_scaffold(example_dir))
    return path


def adjudication_is_stale(adjudication_path: Path, critique_path: Path) -> bool:
    """Return true when adjudication was made against different critique content."""
    adjudication = load_adjudication(adjudication_path)
    if not critique_path.is_file():
        raise CritiqueAdjudicationError(f"missing critique: {critique_path}")
    return adjudication["source_critique_hash"] != file_sha256(critique_path)


def _resolve_example_dir(value: str, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "examples":
        return repo_root / path
    if len(path.parts) == 1:
        return repo_root / "examples" / value
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="create critique_adjudication.yaml from critique.md frontmatter",
    )
    scaffold_parser.add_argument("example", help="fixture name, examples/<name>, or path")
    scaffold_parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    scaffold_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)

    args = parser.parse_args(argv)
    if args.command == "scaffold":
        example_dir = _resolve_example_dir(args.example, args.repo_root)
        try:
            path = scaffold_adjudication(example_dir, force=args.force)
        except CritiqueAdjudicationError as exc:
            print(f"critique_adjudication.py: {exc}", file=sys.stderr)
            return 1
        print(f"critique_adjudication.py: wrote {path}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
