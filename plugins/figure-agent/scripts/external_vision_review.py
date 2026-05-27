"""Optional external second-opinion vision review contract."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

EXTERNAL_VISION_REVIEW_SCHEMA = "figure-agent.external-vision-review.v1"
EXTERNAL_VISION_REVIEW_FILENAME = "external_vision_review.yaml"

CONFIDENCES = frozenset({"low", "medium", "high"})
SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NIT"})
SUGGESTED_ACTIONS = frozenset(
    {"patch", "human_review", "revise_briefing", "accept_simplification"}
)


class ExternalVisionReviewError(Exception):
    """Controlled error for malformed external vision review evidence."""


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


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
                raise ExternalVisionReviewError(
                    f"{item_label}.{id_key} is duplicated: {item_id}"
                )
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
    if value is None:
        return False
    if value is True:
        return True
    raise ExternalVisionReviewError("spec.external_vision_review must be true when present")


def external_vision_review_path(example_dir: Path) -> Path:
    return example_dir / EXTERNAL_VISION_REVIEW_FILENAME


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
            "external_vision_review.fixture must match example directory name: "
            f"{example_dir.name}"
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

    artifact_path, artifact_state = _hash_record_state(
        example_dir,
        _require_mapping(
            review.get("reviewed_artifact"),
            "external_vision_review.reviewed_artifact",
        ),
    )
    if artifact_state == "stale":
        stale_paths.append(artifact_path)
    elif artifact_state == "missing":
        missing_paths.append(artifact_path)

    raw_crops = review.get("reviewed_crops")
    if isinstance(raw_crops, list):
        for raw_crop in raw_crops:
            if not isinstance(raw_crop, dict):
                continue
            crop_path, crop_state = _hash_record_state(example_dir, raw_crop)
            if crop_state == "stale":
                stale_paths.append(crop_path)
            elif crop_state == "missing":
                missing_paths.append(crop_path)

    if missing_paths:
        state = "missing_artifact"
    elif stale_paths:
        state = "stale"
    else:
        state = "fresh"
    return {
        "state": state,
        "stale_paths": stale_paths,
        "missing_paths": missing_paths,
    }
