"""Validate optional host/subagent inspection trace artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from critique_contract import CritiqueContractError, require_mapping  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

SCHEMA = "figure-agent.inspection-trace.v1"
ALLOWED_SOURCES = frozenset({"host_llm", "subagent", "human", "external_tool"})
ALLOWED_VERDICTS = frozenset({"inspected", "skipped", "unavailable"})

InspectionTraceError = CritiqueContractError


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InspectionTraceError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _validate_hash(value: str, *, label: str) -> None:
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise InspectionTraceError(f"{label} must be a sha256-prefixed string")


def _resolve_artifact_path(fixture_dir: Path, relative_path: str, *, label: str) -> Path:
    raw_path = Path(relative_path)
    if raw_path.is_absolute():
        raise InspectionTraceError(f"{label}.path must be fixture-relative")
    resolved = (fixture_dir / raw_path).resolve()
    fixture_root = fixture_dir.resolve()
    if not resolved.is_relative_to(fixture_root):
        raise InspectionTraceError(f"{label}.path must stay inside the fixture directory")
    if not resolved.is_file():
        raise InspectionTraceError(f"{label}: missing inspected artifact: {relative_path}")
    return resolved


def validate_inspection_trace(data: dict[str, Any], *, fixture_dir: Path) -> dict[str, Any]:
    """Validate an inspection trace mapping and return it unchanged."""
    trace = require_mapping(data, "inspection_trace")
    schema = trace.get("schema")
    if schema != SCHEMA:
        raise InspectionTraceError(f"inspection_trace.schema must be {SCHEMA}")

    fixture = _require_non_empty_string(trace, "fixture", label="inspection_trace")
    if fixture != fixture_dir.name:
        raise InspectionTraceError(
            f"inspection_trace.fixture must be {fixture_dir.name}, got {fixture}"
        )

    source = _require_non_empty_string(trace, "source", label="inspection_trace")
    if source not in ALLOWED_SOURCES:
        allowed = ", ".join(sorted(ALLOWED_SOURCES))
        raise InspectionTraceError(f"inspection_trace.source must be one of: {allowed}")

    artifacts = trace.get("inspected_artifacts")
    if not isinstance(artifacts, list):
        raise InspectionTraceError("inspection_trace.inspected_artifacts must be a list")
    if not artifacts:
        raise InspectionTraceError(
            "inspection_trace.inspected_artifacts must be a non-empty list"
        )

    seen_ids: set[str] = set()
    for index, raw_item in enumerate(artifacts):
        label = f"inspection_trace.inspected_artifacts[{index}]"
        item = require_mapping(raw_item, label)
        artifact_id = _require_non_empty_string(item, "id", label=label)
        if artifact_id in seen_ids:
            raise InspectionTraceError(f"{label}.duplicate id: {artifact_id}")
        seen_ids.add(artifact_id)

        relative_path = _require_non_empty_string(item, "path", label=label)
        artifact_path = _resolve_artifact_path(fixture_dir, relative_path, label=label)

        artifact_hash = _require_non_empty_string(item, "sha256", label=label)
        _validate_hash(artifact_hash, label=f"{label}.sha256")
        expected_hash = file_sha256(artifact_path)
        if artifact_hash != expected_hash:
            raise InspectionTraceError(
                f"{label}.hash mismatch for {relative_path}: "
                f"expected {expected_hash}, got {artifact_hash}"
            )

        verdict = _require_non_empty_string(item, "verdict", label=label)
        if verdict not in ALLOWED_VERDICTS:
            allowed = ", ".join(sorted(ALLOWED_VERDICTS))
            raise InspectionTraceError(f"{label}.verdict must be one of: {allowed}")
        _require_non_empty_string(item, "note", label=label)

    return trace


def load_inspection_trace(path: Path, *, fixture_dir: Path | None = None) -> dict[str, Any]:
    """Load and validate an inspection_trace.yaml file."""
    if not path.is_file():
        raise InspectionTraceError(f"missing inspection trace: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise InspectionTraceError(f"invalid UTF-8 in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise InspectionTraceError(f"invalid YAML in {path}: {exc}") from exc
    return validate_inspection_trace(data, fixture_dir=fixture_dir or path.parent)


def load_optional_inspection_trace(
    fixture_dir: Path,
    *,
    filename: str = "inspection_trace.yaml",
) -> dict[str, Any]:
    """Load an optional inspection trace sidecar for a fixture."""
    path = fixture_dir / filename
    if not path.exists():
        return {
            "schema": "figure-agent.inspection-trace-summary.v1",
            "state": "not_applicable",
            "reason": f"{filename} is not present",
            "trace": None,
        }
    trace = load_inspection_trace(path, fixture_dir=fixture_dir)
    return {
        "schema": "figure-agent.inspection-trace-summary.v1",
        "state": "pass",
        "reason": f"{filename} is valid",
        "trace": trace,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="validate optional inspection_trace.yaml for a fixture",
    )
    validate_parser.add_argument("example", type=Path, help="fixture directory")
    validate_parser.add_argument("--filename", default="inspection_trace.yaml")

    args = parser.parse_args(argv)
    if args.command == "validate":
        try:
            result = load_optional_inspection_trace(args.example, filename=args.filename)
        except InspectionTraceError as exc:
            print(f"inspection_trace.py: {exc}", file=sys.stderr)
            return 1
        if result["state"] == "not_applicable":
            print(f"inspection_trace.py: {result['reason']}")
        else:
            print(f"inspection_trace.py: valid {args.example / args.filename}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
