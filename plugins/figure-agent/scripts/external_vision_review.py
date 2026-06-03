"""Optional external second-opinion vision review contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fixture_identity
import yaml

EXTERNAL_VISION_REVIEW_SCHEMA = "figure-agent.external-vision-review.v1"
EXTERNAL_VISION_REVIEW_FILENAME = "external_vision_review.yaml"

CONFIDENCES = frozenset({"low", "medium", "high"})
SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NIT"})
SUGGESTED_ACTIONS = frozenset({"patch", "human_review", "revise_briefing", "accept_simplification"})


class ExternalVisionReviewError(Exception):
    """Controlled error for malformed external vision review evidence."""


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExternalVisionReviewError(f"{label} must be a mapping")
    return value


def _require_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExternalVisionReviewError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_enum(
    data: dict[str, Any],
    key: str,
    allowed: frozenset[str],
    *,
    label: str,
) -> str:
    value = _require_string(data, key, label=label)
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ExternalVisionReviewError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _require_sha256(data: dict[str, Any], key: str, *, label: str) -> str:
    value = _require_string(data, key, label=label)
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise ExternalVisionReviewError(f"{label}.{key} must be sha256-prefixed")
    return value


def _require_timestamp(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        normalized = str(isoformat())
        data[key] = normalized
        return normalized
    raise ExternalVisionReviewError(f"{label}.{key} must be a non-empty timestamp")


def _require_relative_path(data: dict[str, Any], key: str, *, label: str) -> str:
    value = _require_string(data, key, label=label)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ExternalVisionReviewError(f"{label}.{key} must be a repo-relative safe path")
    return value


def _mapping_items(
    data: dict[str, Any],
    key: str,
    *,
    label: str,
    require_non_empty: bool,
    id_key: str | None = "id",
) -> list[dict[str, Any]]:
    raw_items = data.get(key)
    if not isinstance(raw_items, list):
        raise ExternalVisionReviewError(f"{label}.{key} must be a list")
    if require_non_empty and not raw_items:
        raise ExternalVisionReviewError(f"{label}.{key} must be a non-empty list")
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        item_label = f"{label}.{key}[{index}]"
        item = _require_mapping(raw_item, item_label)
        if id_key is not None:
            item_id = _require_string(item, id_key, label=item_label)
            if item_id in seen_ids:
                raise ExternalVisionReviewError(f"{item_label}.{id_key} is duplicated: {item_id}")
            seen_ids.add(item_id)
        items.append(item)
    return items


def _validate_reviewed_artifact(data: dict[str, Any]) -> None:
    artifact = _require_mapping(
        data.get("reviewed_artifact"),
        "external_vision_review.reviewed_artifact",
    )
    _require_relative_path(artifact, "path", label="external_vision_review.reviewed_artifact")
    _require_sha256(artifact, "hash", label="external_vision_review.reviewed_artifact")


def _validate_reviewed_crops(data: dict[str, Any]) -> None:
    for index, crop in enumerate(
        _mapping_items(
            data,
            "reviewed_crops",
            label="external_vision_review",
            require_non_empty=False,
            id_key="crop_id",
        )
    ):
        label = f"external_vision_review.reviewed_crops[{index}]"
        _require_relative_path(crop, "path", label=label)
        _require_sha256(crop, "hash", label=label)


def _validate_findings(data: dict[str, Any]) -> set[str]:
    finding_ids: set[str] = set()
    for index, finding in enumerate(
        _mapping_items(
            data,
            "findings",
            label="external_vision_review",
            require_non_empty=False,
        )
    ):
        label = f"external_vision_review.findings[{index}]"
        finding_id = _require_string(finding, "id", label=label)
        finding_ids.add(finding_id)
        _require_enum(finding, "severity", SEVERITIES, label=label)
        _require_string(finding, "observation", label=label)
        _require_string(finding, "evidence_ref", label=label)
        _require_enum(finding, "suggested_action", SUGGESTED_ACTIONS, label=label)
    return finding_ids


def _validate_conflicts(data: dict[str, Any], finding_ids: set[str]) -> None:
    for index, conflict in enumerate(
        _mapping_items(
            data,
            "conflicts",
            label="external_vision_review",
            require_non_empty=False,
            id_key=None,
        )
    ):
        label = f"external_vision_review.conflicts[{index}]"
        external_finding_id = _require_string(conflict, "external_finding_id", label=label)
        if external_finding_id not in finding_ids:
            raise ExternalVisionReviewError(
                f"{label}.external_finding_id is unknown: {external_finding_id}"
            )
        _require_string(conflict, "host_finding_id", label=label)
        _require_string(conflict, "summary", label=label)


def external_vision_review_opted_in(spec: dict[str, Any]) -> bool:
    value = spec.get("external_vision_review")
    if value is None or value is False:
        return False
    if value is True:
        return True
    raise ExternalVisionReviewError("spec.external_vision_review must be true when present")


def external_vision_review_path(example_dir: Path) -> Path:
    return example_dir / EXTERNAL_VISION_REVIEW_FILENAME


def _relative_to_example(example_dir: Path, path: Path) -> str:
    return str(path.relative_to(example_dir))


def _reviewed_crop_records(example_dir: Path) -> list[dict[str, str]]:
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    if not manifest_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExternalVisionReviewError(
            f"malformed build/audit_crops/manifest.json: {exc}"
        ) from exc
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        raise ExternalVisionReviewError("build/audit_crops/manifest.json crops must be a list")
    records: list[dict[str, str]] = []
    for index, crop in enumerate(crops):
        if not isinstance(crop, dict):
            raise ExternalVisionReviewError(
                f"build/audit_crops/manifest.json crops[{index}] must be a mapping"
            )
        crop_id = crop.get("id")
        crop_path = crop.get("path")
        if not isinstance(crop_id, str) or not crop_id.strip():
            raise ExternalVisionReviewError(
                f"build/audit_crops/manifest.json crops[{index}].id must be non-empty"
            )
        if not isinstance(crop_path, str) or not crop_path.strip():
            raise ExternalVisionReviewError(
                f"build/audit_crops/manifest.json crops[{index}].path must be non-empty"
            )
        crop_path = _require_relative_path(
            {"path": crop_path},
            "path",
            label=f"build/audit_crops/manifest.json crops[{index}]",
        )
        path = example_dir / crop_path
        if not path.is_file():
            raise ExternalVisionReviewError(
                f"build/audit_crops/manifest.json crop missing: {crop_path}"
            )
        records.append(
            {
                "crop_id": crop_id,
                "path": crop_path,
                "hash": _file_sha256(path),
            }
        )
    return sorted(records, key=lambda item: item["crop_id"])


def external_vision_review_template(
    example_dir: Path,
    *,
    reviewer: str = "external reviewer",
    reviewed_at: str | None = None,
) -> str:
    """Return a fresh starter external_vision_review.yaml for a fixture."""
    render_path = example_dir / "build" / f"{example_dir.name}.png"
    if not render_path.is_file():
        raise ExternalVisionReviewError(
            f"build/{example_dir.name}.png not found; run /fig_compile first"
        )
    data: dict[str, Any] = {
        "schema": EXTERNAL_VISION_REVIEW_SCHEMA,
        "fixture": example_dir.name,
        "reviewer": reviewer.strip() or "external reviewer",
        "reviewed_at": reviewed_at or _utc_now(),
        "confidence": "medium",
        "reviewed_artifact": {
            "path": _relative_to_example(example_dir, render_path),
            "hash": _file_sha256(render_path),
        },
        "reviewed_crops": _reviewed_crop_records(example_dir),
        "findings": [],
        "conflicts": [],
    }
    load_data = yaml.safe_load(yaml.safe_dump(data, sort_keys=False))
    if not isinstance(load_data, dict):
        raise ExternalVisionReviewError("generated external vision review is invalid")
    _validate_reviewed_artifact(load_data)
    _validate_reviewed_crops(load_data)
    _validate_conflicts(load_data, _validate_findings(load_data))
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def load_external_vision_review(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ExternalVisionReviewError(f"malformed YAML in {path}: {exc}") from exc
    data = _require_mapping(raw, "external_vision_review")
    schema = _require_string(data, "schema", label="external_vision_review")
    if schema != EXTERNAL_VISION_REVIEW_SCHEMA:
        raise ExternalVisionReviewError(
            f"external_vision_review.schema must equal {EXTERNAL_VISION_REVIEW_SCHEMA}"
        )
    _require_string(data, "fixture", label="external_vision_review")
    _require_string(data, "reviewer", label="external_vision_review")
    _require_timestamp(data, "reviewed_at", label="external_vision_review")
    _require_enum(data, "confidence", CONFIDENCES, label="external_vision_review")
    _validate_reviewed_artifact(data)
    _validate_reviewed_crops(data)
    finding_ids = _validate_findings(data)
    _validate_conflicts(data, finding_ids)
    return data


def load_optional_external_vision_review(
    example_dir: Path,
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    if not external_vision_review_opted_in(spec):
        return None
    path = external_vision_review_path(example_dir)
    if not path.is_file():
        raise ExternalVisionReviewError(f"missing external_vision_review: {path}")
    review = load_external_vision_review(path)
    if review.get("fixture") != example_dir.name:
        raise ExternalVisionReviewError(
            f"external_vision_review.fixture must match example directory name: {example_dir.name}"
        )
    return review


def _hash_record_state(example_dir: Path, record: dict[str, Any]) -> tuple[str, str | None]:
    rel_path = _require_relative_path(record, "path", label="external_vision_review.record")
    expected_hash = _require_sha256(record, "hash", label="external_vision_review.record")
    path = example_dir / rel_path
    if not path.is_file():
        return rel_path, "missing"
    if _file_sha256(path) != expected_hash:
        return rel_path, "stale"
    return rel_path, None


def external_vision_review_freshness(
    example_dir: Path,
    review: dict[str, Any],
) -> dict[str, Any]:
    stale_paths: list[str] = []
    missing_paths: list[str] = []
    errors: list[str] = []

    def mark_stale(path: str) -> None:
        if path not in stale_paths:
            stale_paths.append(path)

    artifact_path, artifact_state = _hash_record_state(
        example_dir,
        _require_mapping(
            review.get("reviewed_artifact"),
            "external_vision_review.reviewed_artifact",
        ),
    )
    if artifact_state == "stale":
        mark_stale(artifact_path)
    elif artifact_state == "missing":
        missing_paths.append(artifact_path)

    raw_crops = review.get("reviewed_crops")
    reviewed_crop_paths: set[str] = set()
    if isinstance(raw_crops, list):
        for raw_crop in raw_crops:
            if not isinstance(raw_crop, dict):
                continue
            crop_path, crop_state = _hash_record_state(example_dir, raw_crop)
            reviewed_crop_paths.add(crop_path)
            if crop_state == "stale":
                mark_stale(crop_path)
            elif crop_state == "missing":
                missing_paths.append(crop_path)

    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    if manifest_path.is_file():
        try:
            current_crop_paths = {record["path"] for record in _reviewed_crop_records(example_dir)}
        except ExternalVisionReviewError as exc:
            current_crop_paths = set()
            errors.append(str(exc))
        for path in sorted(current_crop_paths - reviewed_crop_paths):
            mark_stale(path)
        for path in sorted(reviewed_crop_paths - current_crop_paths):
            mark_stale(path)

    if errors:
        state = "invalid"
    elif missing_paths:
        state = "missing_artifact"
    elif stale_paths:
        state = "stale"
    else:
        state = "fresh"
    return {
        "state": state,
        "stale_paths": stale_paths,
        "missing_paths": missing_paths,
        "errors": errors,
    }


def _resolve_example_dir_for_cli(value: Path) -> Path:
    if value.is_absolute():
        return value
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise ExternalVisionReviewError(
                "invalid fixture path: expected examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise ExternalVisionReviewError(
                "invalid fixture path: relative fixture names must resolve under examples/"
            )
        return value
    raise ExternalVisionReviewError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, or an absolute path"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise ExternalVisionReviewError(f"invalid fixture path: {original}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate or template figure-agent external vision reviews."
    )
    parser.add_argument("path", nargs="?", type=Path, help="external_vision_review.yaml")
    parser.add_argument("--template", type=Path, help="example directory to template")
    parser.add_argument("--write-template", action="store_true", help="write canonical file")
    parser.add_argument("--force", action="store_true", help="overwrite existing template")
    parser.add_argument("--reviewer", default="external reviewer")
    parser.add_argument("--reviewed-at", default=None)
    args = parser.parse_args(argv)

    try:
        if args.template is not None:
            example_dir = _resolve_example_dir_for_cli(args.template)
            template = external_vision_review_template(
                example_dir,
                reviewer=args.reviewer,
                reviewed_at=args.reviewed_at,
            )
            if args.write_template:
                output_path = external_vision_review_path(example_dir)
                if output_path.exists() and not args.force:
                    raise ExternalVisionReviewError(
                        f"{output_path} already exists; pass --force to overwrite"
                    )
                output_path.write_text(template, encoding="utf-8")
                print(f"wrote {output_path}")
            else:
                print(template, end="")
            return 0
        if args.write_template:
            parser.error("--write-template requires --template EXAMPLE_DIR")
        if args.path is None:
            parser.error("provide external_vision_review.yaml or --template EXAMPLE_DIR")
        load_external_vision_review(args.path)
        print(f"OK: external vision review valid: {args.path}")
        return 0
    except ExternalVisionReviewError as exc:
        print(f"external_vision_review.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
