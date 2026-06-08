"""Generate deterministic candidate improvement sets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"
ZERO_HASH = "sha256:" + "0" * 64


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
    example_dir = paths.examples_dir / name
    try:
        output_path.expanduser().resolve().relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateGeneratorError("path_escape") from exc


def _label_offset_candidate(
    *,
    name: str,
    source_rel: Path,
    line: str,
) -> dict[str, Any]:
    replacement = line.replace("(0,0)", "(0.2,0)", 1)
    return {
        "id": "CAND001",
        "target": {"panel": "unknown", "subregion": "label-a"},
        "edit_class": "label_offset",
        "affected_files": [source_rel.as_posix()],
        "selector": {
            "kind": "line_range_with_hash",
            "path": source_rel.as_posix(),
            "start_line": 1,
            "end_line": 1,
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
        "apply_authority": "apply_eligible",
        "blocked_if": ["semantic_invariant_failed", "render_failed"],
    }


def build_candidate_set(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    _validate_output_path(paths=paths, name=name, output_path=output_path)

    source_rel = Path("examples") / name / f"{name}.tex"
    source = paths.workspace_root / source_rel
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
    if len(lines) == 1 and "(0,0)" in lines[0]:
        candidates.append(
            _label_offset_candidate(
                name=name,
                source_rel=source_rel,
                line=lines[0],
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
    args = parser.parse_args(argv)
    try:
        payload = build_candidate_set(args.name)
    except (CandidateGeneratorError, ValueError) as exc:
        print(f"candidate_generator: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
