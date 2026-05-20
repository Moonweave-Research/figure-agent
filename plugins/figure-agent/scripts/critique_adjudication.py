"""Parse and validate critique adjudication decisions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from critique_contract import (  # noqa: E402
    CritiqueContractError,
    critique_finding_id,
    critique_findings,
    load_critique_frontmatter,
    require_mapping,
)
from critique_schema_validator import validate_critique_schema  # noqa: E402
from inputs import parse_spec  # noqa: E402
from quality_manifest import (  # noqa: E402
    CRITIQUE_RUBRIC_VERSION,
    compute_critique_input_hash,
    critique_generator_version,
    file_sha256,
    yaml_frontmatter,
)
from reference_contract import (  # noqa: E402
    compute_reference_input_failures,
    declared_figure_reference_path,
    participating_panel_reference_paths,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.critique-adjudication.v1"
ALLOWED_DECISIONS = frozenset({"apply", "dismiss", "defer", "needs_human", "resolved"})
_PATCH_EVIDENCE_REQUIRED = frozenset({"apply", "resolved"})


CritiqueAdjudicationError = CritiqueContractError
_require_mapping = require_mapping


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


_critique_frontmatter = load_critique_frontmatter
_finding_id = critique_finding_id


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


_findings_from_critique = critique_findings


def build_adjudication_scaffold(example_dir: Path) -> dict[str, Any]:
    """Build a conservative adjudication scaffold from critique.md frontmatter."""
    critique_path = example_dir / "critique.md"
    frontmatter = _critique_frontmatter(critique_path)
    validate_critique_schema(frontmatter)
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


def _critique_metadata_mismatches(
    example_dir: Path,
    *,
    repo_root: Path,
) -> list[str]:
    name = example_dir.name
    critique_path = example_dir / "critique.md"
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return ["missing spec.yaml; cannot determine critique freshness"]
    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    reference_failures = compute_reference_input_failures(example_dir, spec)
    if reference_failures:
        return [
            "critique_state=REFERENCE_MISSING; fix reference inputs before "
            f"/fig_critique {name}"
        ]
    has_reference = (
        declared_figure_reference_path(example_dir, spec) is not None
        or bool(participating_panel_reference_paths(example_dir, spec))
    )
    if not has_reference:
        return [f"critique_state=NOT_REQUIRED; no /fig_critique {name} sync needed"]
    if not critique_path.is_file():
        return [f"critique_state=MISSING; run /fig_critique {name}"]

    metadata = yaml_frontmatter(critique_path)
    generator_path = repo_root / "scripts" / "critique_brief.py"
    expected = {
        "critique_input_hash": compute_critique_input_hash(
            example_dir,
            name,
            spec,
            style_lock_path=repo_root / "styles" / "polymer-paper-preamble.sty",
            base_dir=repo_root,
        ),
        "generator_version": critique_generator_version(generator_path),
        "rubric_version": CRITIQUE_RUBRIC_VERSION,
    }
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        actual = metadata.get(key)
        if not isinstance(actual, str) or not actual.strip():
            mismatches.append(f"{key} missing; run /fig_critique {name}")
        elif actual.strip() != expected_value:
            mismatches.append(f"{key} mismatch; run /fig_critique {name}")
    return mismatches


def _decision_ids(adjudication: dict[str, Any]) -> list[str]:
    return [
        str(decision.get("finding_id", "")).strip()
        for decision in adjudication.get("decisions", [])
        if isinstance(decision, dict)
    ]


def _decision_sync_shape(adjudication: dict[str, Any]) -> list[dict[str, str]]:
    shape: list[dict[str, str]] = []
    for raw_decision in adjudication.get("decisions", []):
        if not isinstance(raw_decision, dict):
            continue
        decision = str(raw_decision.get("decision", "")).strip()
        shape.append(
            {
                "finding_id": str(raw_decision.get("finding_id", "")).strip(),
                "resolved_state": "resolved" if decision == "resolved" else "not_resolved",
            }
        )
    return shape


def sync_adjudication(
    example_dir: Path,
    *,
    force: bool = False,
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Refresh adjudication hash only when critique.md is already fresh."""
    mismatches = _critique_metadata_mismatches(example_dir, repo_root=repo_root)
    if mismatches:
        raise CritiqueAdjudicationError("; ".join(mismatches))

    path = example_dir / "critique_adjudication.yaml"
    scaffold = build_adjudication_scaffold(example_dir)
    if force or not path.exists():
        write_adjudication(path, scaffold)
        return path

    existing = load_adjudication(path)
    existing_ids = _decision_ids(existing)
    scaffold_ids = _decision_ids(scaffold)
    if existing_ids != scaffold_ids:
        raise CritiqueAdjudicationError(
            "adjudication finding ids differ from critique.md; run "
            f"critique_adjudication.py scaffold {example_dir.name} --force"
        )
    if _decision_sync_shape(existing) != _decision_sync_shape(scaffold):
        raise CritiqueAdjudicationError(
            "adjudication decisions differ from current critique scaffold; run "
            f"critique_adjudication.py scaffold {example_dir.name} --force"
        )
    existing["source_critique_hash"] = scaffold["source_critique_hash"]
    write_adjudication(path, existing)
    return path


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

    sync_parser = subparsers.add_parser(
        "sync",
        help="refresh critique_adjudication.yaml hash after a fresh critique",
    )
    sync_parser.add_argument("example", help="fixture name, examples/<name>, or path")
    sync_parser.add_argument("--force", action="store_true", help="recreate the scaffold")
    sync_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)

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
    if args.command == "sync":
        example_dir = _resolve_example_dir(args.example, args.repo_root)
        try:
            path = sync_adjudication(example_dir, force=args.force, repo_root=args.repo_root)
        except CritiqueAdjudicationError as exc:
            print(f"critique_adjudication.py: {exc}", file=sys.stderr)
            return 1
        print(f"critique_adjudication.py: synced {path}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
