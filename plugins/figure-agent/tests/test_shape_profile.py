from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import shape_profile  # noqa: E402


def _valid_payload() -> dict[str, object]:
    return {
        "schema": "figure-agent.shape-profile.v1",
        "status": "experimental_attempt_scoped",
        "objects": [
            {"id": "s60", "role": "discrete_distribution"},
            {"id": "s80", "role": "continuous_broad_distribution"},
        ],
        "relations": [
            {"kind": "wider_than", "subject": "s80", "object": "s60"},
            {"kind": "same_encoding_family", "members": ["s60", "s80"]},
        ],
        "forbidden_claims": [
            "fixed_peak_count",
            "monotonic_disorder",
            "decay_direction",
        ],
        "composition_header": "increasing sulfur content",
    }


def test_compile_shape_profile_returns_normalized_authoring_contract() -> None:
    payload = _valid_payload()

    result = shape_profile.compile_shape_profile(payload)

    assert result == {
        **payload,
        "authoring_directives": [
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
        ],
    }


def test_compile_shape_profile_normalizes_collection_order() -> None:
    payload = _valid_payload()
    objects = payload["objects"]
    relations = payload["relations"]
    forbidden_claims = payload["forbidden_claims"]
    assert isinstance(objects, list)
    assert isinstance(relations, list)
    assert isinstance(forbidden_claims, list)
    payload["objects"] = list(reversed(objects))
    payload["relations"] = list(reversed(relations))
    payload["forbidden_claims"] = list(reversed(forbidden_claims))

    result = shape_profile.compile_shape_profile(payload)

    assert result["objects"] == _valid_payload()["objects"]
    assert result["relations"] == _valid_payload()["relations"]
    assert result["forbidden_claims"] == _valid_payload()["forbidden_claims"]


def _invalid_cases() -> list[tuple[str, dict[str, object], str]]:
    cases: list[tuple[str, dict[str, object], str]] = []

    duplicate = deepcopy(_valid_payload())
    duplicate["objects"] = [
        {"id": "s60", "role": "discrete_distribution"},
        {"id": "s60", "role": "continuous_broad_distribution"},
    ]
    cases.append(("duplicate ids", duplicate, "duplicate object id"))

    unknown_endpoint = deepcopy(_valid_payload())
    unknown_endpoint["relations"] = [
        {"kind": "wider_than", "subject": "s80", "object": "missing"},
        {"kind": "same_encoding_family", "members": ["s60", "s80"]},
    ]
    cases.append(("unknown endpoint", unknown_endpoint, "unknown object id"))

    missing_relation = deepcopy(_valid_payload())
    missing_relation["relations"] = [
        {"kind": "same_encoding_family", "members": ["s60", "s80"]}
    ]
    cases.append(("missing relation", missing_relation, "relations must be exactly"))

    extra_claim = deepcopy(_valid_payload())
    extra_claim["forbidden_claims"] = [
        "fixed_peak_count",
        "monotonic_disorder",
        "decay_direction",
        "causal_order",
    ]
    cases.append(("extra claim", extra_claim, "forbidden_claims must be exactly"))

    wrong_header = deepcopy(_valid_payload())
    wrong_header["composition_header"] = "increasing temperature"
    cases.append(("wrong header", wrong_header, "composition_header must equal"))

    wrong_role = deepcopy(_valid_payload())
    wrong_role["objects"] = [
        {"id": "s60", "role": "gaussian_curve"},
        {"id": "s80", "role": "continuous_broad_distribution"},
    ]
    cases.append(("wrong role", wrong_role, "objects must be exactly"))

    wrong_relation_kind = deepcopy(_valid_payload())
    wrong_relation_kind["relations"] = [
        {"kind": "narrower_than", "subject": "s80", "object": "s60"},
        {"kind": "same_encoding_family", "members": ["s60", "s80"]},
    ]
    cases.append(("wrong relation kind", wrong_relation_kind, "relation kind"))

    malformed_objects = deepcopy(_valid_payload())
    malformed_objects["objects"] = "s60,s80"
    cases.append(("malformed objects", malformed_objects, "objects must be a list"))

    forbidden_nested_key = deepcopy(_valid_payload())
    forbidden_nested_key["metadata"] = {"nested": [{"coordinates": [0, 1]}]}
    cases.append(("forbidden nested key", forbidden_nested_key, "forbidden key 'coordinates'"))

    return cases


@pytest.mark.parametrize(("case", "payload", "message"), _invalid_cases())
def test_compile_shape_profile_rejects_invalid_profiles(
    case: str, payload: dict[str, object], message: str
) -> None:
    assert case
    with pytest.raises(shape_profile.ShapeProfileError, match=message):
        shape_profile.compile_shape_profile(payload)


@pytest.mark.parametrize(
    "forbidden_key",
    ["coordinates", "control_points", "gaussian", "peak_count", "normalization", "threshold"],
)
def test_compile_shape_profile_rejects_forbidden_keys_recursively(forbidden_key: str) -> None:
    payload = _valid_payload()
    objects = payload["objects"]
    assert isinstance(objects, list)
    first_object = objects[0]
    assert isinstance(first_object, dict)
    first_object["metadata"] = {"nested": [{forbidden_key: "value"}]}

    with pytest.raises(
        shape_profile.ShapeProfileError, match=f"forbidden key '{forbidden_key}'"
    ):
        shape_profile.compile_shape_profile(payload)
