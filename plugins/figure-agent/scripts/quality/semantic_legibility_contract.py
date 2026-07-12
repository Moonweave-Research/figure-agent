from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.failure-first-semantic-contract.v1"
ELECTRICAL_STATES = {
    "source",
    "driven",
    "ground_reference",
    "floating",
    "non_electrical",
    "electrically_unmodeled",
}
ELECTRICAL_CONNECTION_ROLES = {
    "electrical_bias_lead",
    "electrical_contact",
    "electrical_lead",
    "ground_return",
    "grounded_source_return",
}
CONNECTOR_STYLE_FAMILIES = {
    "mechanical_attachment": "mechanical_",
    "separation_by_air_gap": "separation_",
    "force_direction": "force_",
    "electrical_bias_lead": "electrical_",
    "electrical_contact": "electrical_",
    "electrical_lead": "electrical_",
    "ground_return": "electrical_",
    "grounded_source_return": "electrical_",
}


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
        declared_role = item.get("declared_role")
        render_style = item.get("render_style")
        if (
            not _nonempty_string(connector_id)
            or connector_id in seen
            or not _nonempty_string(declared_role)
            or not _nonempty_string(render_style)
        ):
            raise SemanticLegibilityContractError("visible_connector_invalid")
        expected_prefix = CONNECTOR_STYLE_FAMILIES.get(declared_role)
        if expected_prefix is not None and not render_style.startswith(expected_prefix):
            raise SemanticLegibilityContractError(
                "visible_connector_style_role_mismatch"
            )
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


def _electrical_topology(
    section: dict[str, Any],
    required: set[str],
    visible_connectors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    topology = section.get("electrical_topology")
    visible_electrical = [
        item
        for item in visible_connectors
        if item["declared_role"] in ELECTRICAL_CONNECTION_ROLES
    ]
    if topology is None:
        if visible_electrical:
            raise SemanticLegibilityContractError(
                "electrical_connector_topology_missing"
            )
        return [], []
    if not isinstance(topology, dict):
        raise SemanticLegibilityContractError("electrical_topology_invalid")

    nodes = topology.get("nodes")
    connections = topology.get("connections")
    if not isinstance(nodes, list) or not isinstance(connections, list):
        raise SemanticLegibilityContractError("electrical_topology_invalid")

    states: dict[str, str] = {}
    for item in nodes:
        if not isinstance(item, dict):
            raise SemanticLegibilityContractError("electrical_node_invalid")
        object_id = item.get("object_id")
        state = item.get("declared_state")
        if (
            not _nonempty_string(object_id)
            or object_id not in required
            or object_id in states
            or state not in ELECTRICAL_STATES
        ):
            raise SemanticLegibilityContractError("electrical_node_invalid")
        states[object_id] = state

    seen: set[str] = set()
    topology_records: set[tuple[str, str, str, str]] = set()
    for item in connections:
        if not isinstance(item, dict):
            raise SemanticLegibilityContractError("electrical_connection_invalid")
        _connector_endpoints(item, set(states), "electrical_connection_endpoint_invalid")
        connection_id = item.get("connection_id")
        if (
            not _nonempty_string(connection_id)
            or connection_id in seen
            or not _nonempty_string(item.get("declared_role"))
        ):
            raise SemanticLegibilityContractError("electrical_connection_invalid")
        seen.add(connection_id)
        topology_records.add(
            (
                connection_id,
                item["from_object"],
                item["to_object"],
                item["declared_role"],
            )
        )
        endpoint_states = {
            states[item["from_object"]],
            states[item["to_object"]],
        }
        if "floating" in endpoint_states:
            raise SemanticLegibilityContractError("floating_object_connected")
        if "non_electrical" in endpoint_states:
            raise SemanticLegibilityContractError("non_electrical_object_connected")
        if "electrically_unmodeled" in endpoint_states:
            raise SemanticLegibilityContractError(
                "electrically_unmodeled_object_connected"
            )

    for item in visible_electrical:
        record = (
            item["connector_id"],
            item["from_object"],
            item["to_object"],
            item["declared_role"],
        )
        if record not in topology_records:
            raise SemanticLegibilityContractError(
                "electrical_connector_topology_missing"
            )

    return nodes, connections


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
    electrical_nodes, electrical_connections = _electrical_topology(
        section, required, visible_connectors
    )

    return {
        **payload,
        "summary": {
            "object_role_count": len(object_roles),
            "visible_connector_count": len(visible_connectors),
            "forbidden_connector_count": len(forbidden_connectors),
            "label_ownership_count": len(label_ownership),
            "electrical_node_count": len(electrical_nodes),
            "electrical_connection_count": len(electrical_connections),
            "floating_object_count": sum(
                item["declared_state"] == "floating" for item in electrical_nodes
            ),
            "visual_review_required": True,
        },
    }


def load_semantic_legibility_contract(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SemanticLegibilityContractError("contract_file_invalid") from exc
    return validate_semantic_legibility_contract(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an opt-in semantic legibility contract."
    )
    parser.add_argument("contract", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = load_semantic_legibility_contract(args.contract)
    except SemanticLegibilityContractError as exc:
        print(f"ERROR semantic_legibility_contract: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        summary = payload["summary"]
        print(
            "OK semantic_legibility_contract: "
            f"objects={summary['object_role_count']} "
            f"connectors={summary['visible_connector_count']} "
            f"labels={summary['label_ownership_count']} "
            "visual_review_required=true"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
