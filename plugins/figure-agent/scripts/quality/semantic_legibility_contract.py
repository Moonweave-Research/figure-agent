from __future__ import annotations

from typing import Any

SCHEMA = "figure-agent.failure-first-semantic-contract.v1"


class SemanticLegibilityContractError(ValueError):
    pass


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _required_objects(payload: dict[str, Any]) -> list[str]:
    values = payload.get("required_objects")
    if (
        not isinstance(values, list)
        or not values
        or not all(_nonempty_string(value) for value in values)
        or len(set(values)) != len(values)
    ):
        raise SemanticLegibilityContractError("required_objects_invalid")
    return values


def _object_roles(section: dict[str, Any], required: set[str]) -> list[dict[str, Any]]:
    values = section.get("object_roles")
    if not isinstance(values, list):
        raise SemanticLegibilityContractError("object_roles_invalid")

    seen: set[str] = set()
    for item in values:
        if not isinstance(item, dict):
            raise SemanticLegibilityContractError("object_role_invalid")
        object_id = item.get("object_id")
        declared_role = item.get("declared_role")
        forbidden = item.get("forbidden_readings")
        if (
            not _nonempty_string(object_id)
            or object_id not in required
            or object_id in seen
            or not _nonempty_string(declared_role)
            or not isinstance(forbidden, list)
            or not all(_nonempty_string(value) for value in forbidden)
            or len(set(forbidden)) != len(forbidden)
        ):
            raise SemanticLegibilityContractError("object_role_invalid")
        if declared_role in forbidden:
            raise SemanticLegibilityContractError("object_role_contradiction")
        seen.add(object_id)

    if seen != required:
        raise SemanticLegibilityContractError("required_object_role_missing")
    return values


def _connector_endpoints(item: dict[str, Any], required: set[str], code: str) -> None:
    from_object = item.get("from_object")
    to_object = item.get("to_object")
    if (
        not _nonempty_string(from_object)
        or not _nonempty_string(to_object)
        or from_object not in required
        or to_object not in required
        or from_object == to_object
    ):
        raise SemanticLegibilityContractError(code)


def _visible_connectors(
    section: dict[str, Any], required: set[str]
) -> list[dict[str, Any]]:
    values = section.get("visible_connectors")
    if not isinstance(values, list):
        raise SemanticLegibilityContractError("visible_connectors_invalid")

    seen: set[str] = set()
    for item in values:
        if not isinstance(item, dict):
            raise SemanticLegibilityContractError("visible_connector_invalid")
        _connector_endpoints(item, required, "visible_connector_endpoint_invalid")
        connector_id = item.get("connector_id")
        if (
            not _nonempty_string(connector_id)
            or connector_id in seen
            or not _nonempty_string(item.get("declared_role"))
        ):
            raise SemanticLegibilityContractError("visible_connector_invalid")
        seen.add(connector_id)
    return values


def _forbidden_connectors(
    section: dict[str, Any], required: set[str]
) -> list[dict[str, Any]]:
    values = section.get("forbidden_connectors")
    if not isinstance(values, list):
        raise SemanticLegibilityContractError("forbidden_connectors_invalid")

    seen: set[tuple[str, str, str]] = set()
    for item in values:
        if not isinstance(item, dict):
            raise SemanticLegibilityContractError("forbidden_connector_invalid")
        _connector_endpoints(item, required, "forbidden_connector_endpoint_invalid")
        role = item.get("declared_role")
        if not _nonempty_string(role):
            raise SemanticLegibilityContractError("forbidden_connector_invalid")
        key = (item["from_object"], item["to_object"], role)
        if key in seen:
            raise SemanticLegibilityContractError("forbidden_connector_invalid")
        seen.add(key)
    return values


def _label_ownership(
    section: dict[str, Any], required: set[str]
) -> list[dict[str, Any]]:
    values = section.get("label_ownership")
    if not isinstance(values, list):
        raise SemanticLegibilityContractError("label_ownership_invalid")

    seen: set[str] = set()
    for item in values:
        if not isinstance(item, dict):
            raise SemanticLegibilityContractError("label_ownership_invalid")
        label_id = item.get("label_id")
        owner = item.get("owner")
        if (
            not _nonempty_string(label_id)
            or label_id in seen
            or not _nonempty_string(owner)
            or owner not in required
        ):
            raise SemanticLegibilityContractError("label_owner_invalid")
        seen.add(label_id)
    return values


def validate_semantic_legibility_contract(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise SemanticLegibilityContractError("schema_invalid")
    if payload.get("publication_acceptance") != "not_claimed":
        raise SemanticLegibilityContractError("publication_acceptance_invalid")

    required = set(_required_objects(payload))
    section = payload.get("semantic_legibility")
    if not isinstance(section, dict):
        raise SemanticLegibilityContractError("semantic_legibility_missing")

    object_roles = _object_roles(section, required)
    visible_connectors = _visible_connectors(section, required)
    forbidden_connectors = _forbidden_connectors(section, required)
    label_ownership = _label_ownership(section, required)

    return {
        **payload,
        "summary": {
            "object_role_count": len(object_roles),
            "visible_connector_count": len(visible_connectors),
            "forbidden_connector_count": len(forbidden_connectors),
            "label_ownership_count": len(label_ownership),
            "visual_review_required": True,
        },
    }
