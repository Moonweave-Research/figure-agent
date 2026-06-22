"""Generate deterministic candidate improvement sets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import bounded_coordinate_offset
import candidate_contracts
import candidate_families
import figure_intent_model
import fixture_identity
import quality_defect_ledger
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"
ZERO_HASH = "sha256:" + "0" * 64
COORDINATE_OFFSET_DEFECT_CLASSES = frozenset(
    {"label_offset", "text_overlap", "whitespace_balance"}
)


class CandidateGeneratorError(ValueError):
    """Raised when candidate generation would violate fixture-local bounds."""


def _source_hash(source: Path) -> str:
    return file_sha256(source) if source.is_file() else ZERO_HASH


def _validate_output_path(
    *,
    paths: runtime_paths.RuntimePaths,
    name: str,
    output_path: Path | None,
) -> None:
    if output_path is None:
        return
    try:
        candidate_contracts.fixture_local_output_path(
            paths.workspace_root,
            name,
            output_path.as_posix(),
        )
    except (ValueError, candidate_contracts.CandidateContractError) as exc:
        raise CandidateGeneratorError(str(exc)) from exc


def _fixture_source_path(paths: runtime_paths.RuntimePaths, name: str) -> Path:
    fixture = paths.examples_dir / name
    if fixture.is_symlink():
        raise CandidateGeneratorError("fixture_symlink_forbidden")
    lexical_source = fixture / f"{name}.tex"
    if lexical_source.is_symlink():
        raise CandidateGeneratorError("source_symlink_forbidden")
    source = candidate_contracts.fixture_relative_path(fixture, f"{name}.tex")
    return source


def _authority_floor(name: str, paths: runtime_paths.RuntimePaths) -> str:
    intent = figure_intent_model.build_intent_model(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    panels = intent.get("panels")
    if not isinstance(panels, list) or not panels:
        return "review_only"
    floors = [panel.get("apply_authority_floor") for panel in panels if isinstance(panel, dict)]
    if "rejected" in floors:
        return "rejected"
    if "review_only" in floors:
        return "review_only"
    if "apply_eligible" in floors:
        return "apply_eligible"
    return "review_only"


def _label_offset_candidate(
    *,
    name: str,
    source_rel: Path,
    line_number: int,
    line: str,
    replacement: str,
    apply_authority: str,
    source_defect: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = {
        "id": "CAND001",
        "target": {"panel": "unknown", "subregion": "label-a"},
        "edit_class": "label_offset",
        "affected_files": [source_rel.as_posix()],
        "selector": {
            "kind": "line_range_with_hash",
            "path": source_rel.as_posix(),
            "start_line": line_number,
            "end_line": line_number,
            "original_hash": candidate_contracts.canonical_hash(line),
        },
        "operations": [
            {
                "kind": "replace_text",
                "path": source_rel.as_posix(),
                "original": line,
                "replacement": replacement,
            }
        ],
        "risk": "low",
        "expected_delta": ["improve label clearance"],
        "semantic_risks": [],
        "rollback": {"strategy": "reverse_operations"},
        "verification": {
            "required_commands": [
                f"fig-agent compile {name} --strict",
                f"fig-agent status {name} --json",
            ]
        },
        "apply_authority": apply_authority,
        "blocked_if": ["semantic_invariant_failed", "render_failed"],
    }
    if source_defect is not None:
        candidate["source_defect"] = source_defect
    return candidate


def _defect_target_line(
    name: str,
    paths: runtime_paths.RuntimePaths,
    lines: list[str],
) -> tuple[int, str, str, dict[str, Any]] | None:
    ledger = quality_defect_ledger.build_quality_defect_ledger(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    defects = ledger.get("defects")
    if not isinstance(defects, list):
        return None
    for defect in defects:
        if not isinstance(defect, dict):
            continue
        if (defect.get("patchability") or {}).get("state") != "safe_candidate":
            continue
        defect_class = str(defect.get("defect_class") or "")
        if defect_class not in COORDINATE_OFFSET_DEFECT_CLASSES:
            continue
        selector = defect.get("selector_hint")
        if not isinstance(selector, dict) or selector.get("kind") != "line_range":
            continue
        value = selector.get("value")
        if not isinstance(value, str) or ":" not in value:
            continue
        start = value.split(":", 1)[0].strip()
        if not start.isdigit():
            continue
        line_number = int(start)
        if line_number < 1 or line_number > len(lines):
            continue
        line = lines[line_number - 1]
        replacement = bounded_coordinate_offset.offset_first_coordinate(line)
        if replacement is None:
            continue
        source_defect = {
            "id": str(defect.get("id") or ""),
            "source": str(defect.get("source") or ""),
            "defect_class": defect_class,
            "evidence": defect.get("evidence") or [],
            "source_fingerprint": str(defect.get("source_fingerprint") or ""),
        }
        return line_number, line, replacement, source_defect
    return None


def build_candidate_set(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    output_path: Path | None = None,
    panel: str | None = None,
    family: str | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    _validate_output_path(paths=paths, name=name, output_path=output_path)
    if panel is not None or family is not None:
        return candidate_families.build_family_candidates(
            name,
            panel=panel,
            family=family,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
        )

    source_rel = Path("examples") / name / f"{name}.tex"
    source = _fixture_source_path(paths, name)
    apply_authority = _authority_floor(name, paths)
    base = {
        "tex_hash": _source_hash(source),
        "status_hash": ZERO_HASH,
        "intent_model_hash": ZERO_HASH,
    }
    if not source.is_file():
        return {
            "schema": SCHEMA,
            "fixture": name,
            "base": base,
            "candidates": [],
            "refusals": [{"code": "source_missing"}],
        }

    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    candidates: list[dict[str, Any]] = []
    target = _defect_target_line(name, paths, lines)
    if target is not None:
        line_number, line, replacement, source_defect = target
        candidates.append(
            _label_offset_candidate(
                name=name,
                source_rel=source_rel,
                line_number=line_number,
                line=line,
                replacement=replacement,
                apply_authority=apply_authority,
                source_defect=source_defect,
            )
        )

    return {
        "schema": SCHEMA,
        "fixture": name,
        "base": base,
        "candidates": candidates,
        "refusals": [] if candidates else [{"code": "no_supported_candidate"}],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--panel")
    parser.add_argument("--family")
    args = parser.parse_args(argv)
    try:
        payload = build_candidate_set(args.name, panel=args.panel, family=args.family)
    except (CandidateGeneratorError, ValueError) as exc:
        print(f"candidate_generator: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
