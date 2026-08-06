"""Validate fixture-local claim certainty and decision boundaries.

The ledger does not decide science. It records where a human-authored review has
qualified or disputed a semantic contract so authoring cannot silently promote
that uncertainty back into an asserted figure claim.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml
from inputs import parse_spec
from semantic_contracts import SemanticContractError, collect_semantic_contracts

SCHEMA = "figure-agent.claim-authority.v1"
FILENAME = "claim_authority.yaml"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_KINDS = {
    "scientific_claim",
    "instrument_identity",
    "symbol_definition",
    "mechanism",
    "editorial_scope",
}
_STATES = {"supported", "schematic", "hypothesis", "unresolved", "conflicted", "forbidden"}
_HUMAN_STATES = {"unresolved", "conflicted"}
_BLOCKING_STATES = _HUMAN_STATES | {"forbidden"}


def _invalid(reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "path": FILENAME,
        "state": "INVALID",
        "reason": reason,
        "requires_human": False,
        "requires_contract_repair": True,
        "blocking_item_ids": [],
        "items": [],
    }


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_invalid")
    return value.strip()


def _string_list(value: object, *, field: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (
        not allow_empty and not value
    ) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field}_invalid")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field}_duplicate")
    return normalized


def _semantic_targets(spec: dict[str, Any]) -> set[str]:
    contracts = collect_semantic_contracts(spec)
    targets = {
        f"claim:{item['panel_id']}:{item['id']}"
        for item in contracts["semantic_claims"]
    }
    targets.update(
        f"invariant:{item['panel_id']}:{item['id']}"
        for item in contracts["locked_invariants"]
    )
    return targets


def load_claim_authority(example_dir: Path) -> dict[str, Any]:
    """Return a non-mutating claim-authority summary for one fixture."""

    path = example_dir / FILENAME
    if not path.exists() and not path.is_symlink():
        return {
            "schema": SCHEMA,
            "path": FILENAME,
            "state": "NOT_DECLARED",
            "requires_human": False,
            "requires_contract_repair": False,
            "blocking_item_ids": [],
            "items": [],
        }
    if path.is_symlink() or not path.is_file():
        return _invalid("claim_authority_not_regular")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
            return _invalid("schema_invalid")
        if payload.get("fixture") != example_dir.name:
            return _invalid("fixture_mismatch")
        spec_path = example_dir / "spec.yaml"
        if not spec_path.is_file():
            return _invalid("spec_missing")
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        declared_targets = _semantic_targets(spec)
        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            return _invalid("items_invalid")

        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_targets: set[str] = set()
        for index, raw in enumerate(raw_items):
            if not isinstance(raw, dict):
                return _invalid(f"items[{index}]_invalid")
            item_id = _text(raw.get("id"), field=f"items[{index}].id")
            if not _ID.fullmatch(item_id):
                return _invalid(f"items[{index}].id_unsafe")
            if item_id in seen_ids:
                return _invalid(f"duplicate_id:{item_id}")
            seen_ids.add(item_id)
            panel_id = _text(raw.get("panel_id"), field=f"items[{index}].panel_id")
            kind = _text(raw.get("kind"), field=f"items[{index}].kind")
            state = _text(raw.get("state"), field=f"items[{index}].state")
            if kind not in _KINDS:
                return _invalid(f"items[{index}].kind_unknown")
            if state not in _STATES:
                return _invalid(f"items[{index}].state_unknown")
            statement = _text(raw.get("statement"), field=f"items[{index}].statement")
            targets = _string_list(
                raw.get("targets", []),
                field=f"items[{index}].targets",
                allow_empty=True,
            )
            for target in targets:
                if target not in declared_targets:
                    return _invalid(f"unknown_target:{target}")
                _, target_panel, _ = target.split(":", 2)
                if target_panel != panel_id:
                    return _invalid(f"target_panel_mismatch:{target}")
                if target in seen_targets:
                    return _invalid(f"duplicate_target:{target}")
                seen_targets.add(target)
            evidence_refs = _string_list(
                raw.get("evidence_refs"),
                field=f"items[{index}].evidence_refs",
            )
            items.append(
                {
                    "id": item_id,
                    "panel_id": panel_id,
                    "kind": kind,
                    "state": state,
                    "statement": statement,
                    "targets": targets,
                    "evidence_refs": evidence_refs,
                }
            )
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, SemanticContractError) as exc:
        return _invalid(str(exc))

    blocking = [item for item in items if item["state"] in _BLOCKING_STATES]
    requires_human = any(item["state"] in _HUMAN_STATES for item in blocking)
    return {
        "schema": SCHEMA,
        "path": FILENAME,
        "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        "state": "BLOCKED" if blocking else "CLEAR",
        "requires_human": requires_human,
        "requires_contract_repair": any(
            item["state"] == "forbidden" for item in blocking
        ),
        "blocking_item_ids": [item["id"] for item in blocking],
        "items": items,
    }


def authoring_directives(summary: dict[str, Any]) -> list[str]:
    """Translate recorded epistemic state into non-generative authoring constraints."""

    directives: list[str] = []
    for item in summary.get("items", []):
        state = item["state"]
        prefix = {
            "supported": "Supported",
            "schematic": "Schematic only",
            "hypothesis": "Hypothesis only",
            "unresolved": "Unresolved; human decision required",
            "conflicted": "Conflicted; human decision required",
            "forbidden": "Forbidden by current authority",
        }[state]
        directives.append(f"{prefix} [{item['id']}]: {item['statement']}")
        if state in _BLOCKING_STATES:
            directives.extend(
                f"Do not assert target [{target}] until this item is resolved."
                for target in item["targets"]
            )
    return directives
