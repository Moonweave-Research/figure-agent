"""Attempt-scoped qualitative shape-profile contract."""

from __future__ import annotations

from collections.abc import Mapping

SCHEMA = "figure-agent.shape-profile.v1"
STATUS = "experimental_attempt_scoped"

_DIRECTIVES = [
    "Render [s80] visibly wider in energy than [s60].",
    "Use one shared outline, fill, and stroke encoding family for [s60, s80].",
    (
        "Use composition header [increasing sulfur content] without a curve-to-curve "
        "causal arrow."
    ),
    (
        "Do not assert unresolved claims [fixed_peak_count, monotonic_disorder, "
        "decay_direction]."
    ),
]
_FORBIDDEN_KEYS = frozenset(
    {"coordinates", "control_points", "gaussian", "peak_count", "normalization", "threshold"}
)
_EXPECTED_KEYS = frozenset(
    {"schema", "status", "objects", "relations", "forbidden_claims", "composition_header"}
)
_OBJECTS = [
    {"id": "s60", "role": "discrete_distribution"},
    {"id": "s80", "role": "continuous_broad_distribution"},
]
_RELATIONS = [
    {"kind": "wider_than", "subject": "s80", "object": "s60"},
    {"kind": "same_encoding_family", "members": ["s60", "s80"]},
]
_FORBIDDEN_CLAIMS = ["fixed_peak_count", "monotonic_disorder", "decay_direction"]
_COMPOSITION_HEADER = "increasing sulfur content"


class ShapeProfileError(ValueError):
    """Controlled error for an invalid qualitative shape profile."""


def _reject_forbidden_keys(value: object, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS:
                raise ShapeProfileError(f"forbidden key '{key}' at {path}")
            _reject_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{path}[{index}]")


def _require_exact_keys(value: dict[object, object], expected: set[str], label: str) -> None:
    if set(value) != expected:
        expected_text = ", ".join(sorted(expected))
        raise ShapeProfileError(f"{label} keys must be exactly: {expected_text}")


def _validate_objects(value: object) -> None:
    if not isinstance(value, list):
        raise ShapeProfileError("objects must be a list")
    seen_ids: set[str] = set()
    normalized: list[dict[str, str]] = []
    for index, raw_object in enumerate(value):
        if not isinstance(raw_object, dict):
            raise ShapeProfileError(f"objects[{index}] must be a mapping")
        _require_exact_keys(raw_object, {"id", "role"}, f"objects[{index}]")
        object_id = raw_object["id"]
        role = raw_object["role"]
        if not isinstance(object_id, str) or not isinstance(role, str):
            raise ShapeProfileError(f"objects[{index}] id and role must be strings")
        if object_id in seen_ids:
            raise ShapeProfileError(f"duplicate object id: {object_id}")
        seen_ids.add(object_id)
        normalized.append({"id": object_id, "role": role})
    expected_by_id = {item["id"]: item["role"] for item in _OBJECTS}
    actual_by_id = {item["id"]: item["role"] for item in normalized}
    if actual_by_id != expected_by_id:
        raise ShapeProfileError("objects must be exactly the required s60 and s80 roles")


def _validate_relations(value: object, object_ids: set[str]) -> None:
    if not isinstance(value, list):
        raise ShapeProfileError("relations must be a list")
    normalized: list[dict[str, object]] = []
    for index, raw_relation in enumerate(value):
        if not isinstance(raw_relation, dict):
            raise ShapeProfileError(f"relations[{index}] must be a mapping")
        kind = raw_relation.get("kind")
        if kind not in {"wider_than", "same_encoding_family"}:
            raise ShapeProfileError(f"unsupported relation kind at relations[{index}]: {kind!r}")
        expected_keys = (
            {"kind", "subject", "object"}
            if kind == "wider_than"
            else {"kind", "members"}
        )
        _require_exact_keys(raw_relation, expected_keys, f"relations[{index}]")
        endpoints = (
            [raw_relation["subject"], raw_relation["object"]]
            if kind == "wider_than"
            else raw_relation["members"]
        )
        if not isinstance(endpoints, list) or not all(isinstance(item, str) for item in endpoints):
            raise ShapeProfileError(f"relations[{index}] endpoints must be a list of strings")
        for endpoint in endpoints:
            if endpoint not in object_ids:
                raise ShapeProfileError(f"unknown object id in relations[{index}]: {endpoint}")
        normalized.append(dict(raw_relation))
    expected_by_kind = {item["kind"]: item for item in _RELATIONS}
    actual_by_kind = {item["kind"]: item for item in normalized}
    if len(normalized) != len(actual_by_kind) or actual_by_kind != expected_by_kind:
        raise ShapeProfileError("relations must be exactly wider_than and same_encoding_family")


def compile_shape_profile(payload: dict[str, object]) -> dict[str, object]:
    """Compile a validated qualitative profile into authoring directives."""
    if not isinstance(payload, dict):
        raise ShapeProfileError("payload must be a mapping")
    _reject_forbidden_keys(payload)
    _require_exact_keys(payload, set(_EXPECTED_KEYS), "payload")
    if payload["schema"] != SCHEMA:
        raise ShapeProfileError(f"schema must equal {SCHEMA}")
    if payload["status"] != STATUS:
        raise ShapeProfileError(f"status must equal {STATUS}")
    _validate_objects(payload["objects"])
    _validate_relations(payload["relations"], {"s60", "s80"})
    forbidden_claims = payload["forbidden_claims"]
    if (
        not isinstance(forbidden_claims, list)
        or not all(isinstance(item, str) for item in forbidden_claims)
        or len(forbidden_claims) != len(set(forbidden_claims))
        or set(forbidden_claims) != set(_FORBIDDEN_CLAIMS)
    ):
        raise ShapeProfileError("forbidden_claims must be exactly the three unresolved claims")
    if payload["composition_header"] != _COMPOSITION_HEADER:
        raise ShapeProfileError(f"composition_header must equal {_COMPOSITION_HEADER!r}")
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "objects": [dict(item) for item in _OBJECTS],
        "relations": [dict(item) for item in _RELATIONS],
        "forbidden_claims": list(_FORBIDDEN_CLAIMS),
        "composition_header": _COMPOSITION_HEADER,
        "authoring_directives": list(_DIRECTIVES),
    }
