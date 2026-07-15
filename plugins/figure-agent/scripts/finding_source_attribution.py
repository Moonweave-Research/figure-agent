#!/usr/bin/env python3
"""Bind rendered findings to declared, hash-bound TikZ source selectors.

The mapper never infers ownership from coordinates. A rendered token must match
an explicit selector alias, and exactly one matching selector must be declared
``movable`` before a repair target can be emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from quality.semantic_legibility_contract import (
    SemanticLegibilityContractError,
    validate_semantic_legibility_contract,
)

ATTRIBUTION_SCHEMA_ID = "figure-agent.finding-source-attribution.v1"
REGISTRY_SCHEMA_ID = "figure-agent.source-selector-registry.v1"
TARGET_SCHEMA_ID = "figure-agent.repair-target-contract.v1"
SEMANTIC_ATTRIBUTION_SCHEMA_ID = "figure-agent.semantic-finding-attribution.v1"
REPORT_COLLECTIONS = {
    "figure-agent.text-collisions.v1": "collisions",
    "figure-agent.label-hyphenation.v1": "issues",
}


class SourceAttributionError(ValueError):
    """Raised when declared source attribution cannot be evaluated safely."""


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    collection = REPORT_COLLECTIONS.get(str(report.get("schema")))
    if collection is None or not isinstance(report.get(collection), list):
        raise SourceAttributionError("finding report schema is unsupported")
    return [item for item in report[collection] if isinstance(item, dict)]


def _finding_texts(finding: dict[str, Any]) -> list[str]:
    texts = finding.get("texts")
    if isinstance(texts, list):
        return [str(text) for text in texts if isinstance(text, str) and text]
    text = finding.get("text")
    return [text] if isinstance(text, str) and text else []


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def _validated_selectors(
    registry: dict[str, Any], source_text: str
) -> list[dict[str, Any]]:
    if registry.get("schema") != REGISTRY_SCHEMA_ID:
        raise SourceAttributionError("selector registry schema is invalid")
    selectors = registry.get("selectors")
    if not isinstance(selectors, list) or not selectors:
        raise SourceAttributionError("selector registry must declare selectors")
    validated: list[dict[str, Any]] = []
    source_lines = source_text.splitlines()
    seen_ids: set[str] = set()
    for selector in selectors:
        if not isinstance(selector, dict):
            raise SourceAttributionError("selector must be an object")
        selector_id = selector.get("selector_id")
        start = selector.get("anchor_start")
        end = selector.get("anchor_end")
        aliases = selector.get("rendered_aliases")
        role = selector.get("repair_role")
        if (
            not isinstance(selector_id, str)
            or not selector_id
            or selector_id in seen_ids
            or not isinstance(start, str)
            or not isinstance(end, str)
            or not isinstance(aliases, list)
            or not aliases
            or any(not isinstance(alias, str) or not alias for alias in aliases)
            or role not in {"fixed", "movable"}
        ):
            raise SourceAttributionError("selector declaration is invalid")
        starts = [index for index, line in enumerate(source_lines) if line == start]
        ends = [index for index, line in enumerate(source_lines) if line == end]
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            raise SourceAttributionError("selector anchors must resolve exactly once")
        seen_ids.add(selector_id)
        validated.append(selector)
    return validated


def attribute_findings(
    report: dict[str, Any],
    registry: dict[str, Any],
    *,
    source_path: Path,
) -> dict[str, Any]:
    return attribute_findings_from_bytes(
        report,
        registry,
        source_bytes=source_path.read_bytes(),
    )


def attribute_findings_from_bytes(
    report: dict[str, Any],
    registry: dict[str, Any],
    *,
    source_bytes: bytes,
) -> dict[str, Any]:
    """Attribute findings from one caller-owned source byte snapshot."""
    source_hash = _sha256(source_bytes)
    if registry.get("source_sha256") != source_hash:
        raise SourceAttributionError("source hash does not match selector registry")
    source_text = source_bytes.decode("utf-8")
    selectors = _validated_selectors(registry, source_text)

    attributed: list[dict[str, Any]] = []
    for finding in _findings(report):
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not finding_id:
            raise SourceAttributionError("every finding must have a stable id")
        texts = _finding_texts(finding)
        matches: list[dict[str, Any]] = []
        for selector in selectors:
            aliases = {_normalized(alias) for alias in selector["rendered_aliases"]}
            matched_texts = sorted(
                text for text in texts if _normalized(text) in aliases
            )
            if matched_texts:
                matches.append(
                    {
                        "selector_id": selector["selector_id"],
                        "matched_texts": matched_texts,
                        "repair_role": selector["repair_role"],
                    }
                )
        matches.sort(key=lambda item: item["selector_id"])
        movable = [item for item in matches if item["repair_role"] == "movable"]
        if len(movable) == 1:
            state = "exact"
            reason_code = "one_declared_movable_selector"
            selected = movable[0]["selector_id"]
        elif len(movable) > 1:
            state = "ambiguous"
            reason_code = "multiple_declared_movable_selectors"
            selected = None
        elif matches:
            state = "unbound"
            reason_code = "no_declared_movable_selector"
            selected = None
        else:
            state = "unbound"
            reason_code = "no_declared_alias_match"
            selected = None
        attributed.append(
            {
                "finding_id": finding_id,
                "state": state,
                "reason_code": reason_code,
                "matched_selectors": matches,
                "selected_selector_id": selected,
            }
        )

    return {
        "schema": ATTRIBUTION_SCHEMA_ID,
        "fixture": report.get("fixture"),
        "source": {
            "path": registry.get("source_path"),
            "sha256": source_hash,
        },
        "findings": attributed,
        "summary": {
            state: sum(item["state"] == state for item in attributed)
            for state in ("ambiguous", "exact", "unbound")
        },
    }


def build_repair_target_contract(
    *,
    report_path: str,
    report: dict[str, Any],
    registry: dict[str, Any],
    attribution: dict[str, Any],
    finding_id: str,
) -> dict[str, Any]:
    findings = [item for item in _findings(report) if item.get("id") == finding_id]
    mappings = [
        item
        for item in attribution.get("findings", [])
        if isinstance(item, dict) and item.get("finding_id") == finding_id
    ]
    if len(findings) != 1 or len(mappings) != 1 or mappings[0].get("state") != "exact":
        raise SourceAttributionError("selected finding must have exact attribution")
    selected_id = mappings[0]["selected_selector_id"]
    selectors = [
        item
        for item in registry["selectors"]
        if item.get("selector_id") == selected_id
    ]
    if len(selectors) != 1:
        raise SourceAttributionError("selected selector must resolve exactly once")
    selector = selectors[0]
    repair_family = selector.get("repair_family")
    invariants = selector.get("protected_invariants")
    if not isinstance(repair_family, str) or not isinstance(invariants, list) or not invariants:
        raise SourceAttributionError("movable selector lacks repair policy")
    return {
        "schema": TARGET_SCHEMA_ID,
        "source_path": registry["source_path"],
        "source_sha256": registry["source_sha256"],
        "targets": [
            {
                "finding": {"report_path": report_path, "id": finding_id},
                "attribution": {"state": "exact"},
                "selector": {
                    "kind": "semantic_anchor",
                    "selector_id": selector["selector_id"],
                    "anchor_start": selector["anchor_start"],
                    "anchor_end": selector["anchor_end"],
                },
                "repair_family": repair_family,
                "protected_invariants": list(invariants),
            }
        ],
    }


def resolve_semantic_selector(
    *,
    registry: dict[str, Any],
    attribution: dict[str, Any],
    finding_id: str,
    semantic_contract: dict[str, Any],
) -> dict[str, Any]:
    """Resolve declared semantic refs without inferring from coordinates."""
    try:
        validated_contract = validate_semantic_legibility_contract(
            semantic_contract
        )
    except SemanticLegibilityContractError as exc:
        raise SourceAttributionError(f"semantic contract is invalid: {exc}") from exc
    required_objects = set(validated_contract["required_objects"])
    protected_relations = validated_contract.get("protected_relations")
    if (
        not isinstance(protected_relations, list)
        or not protected_relations
        or any(
            not isinstance(relation, str) or not relation.strip()
            for relation in protected_relations
        )
        or len(set(protected_relations)) != len(protected_relations)
    ):
        raise SourceAttributionError(
            "semantic contract protected_relations are invalid"
        )
    declared_relations = set(protected_relations)
    mappings = [
        item
        for item in attribution.get("findings", [])
        if isinstance(item, dict) and item.get("finding_id") == finding_id
    ]
    if len(mappings) != 1:
        raise SourceAttributionError("selected finding attribution must resolve once")
    mapping = mappings[0]
    candidate_ids = sorted(
        {
            item["selector_id"]
            for item in mapping.get("matched_selectors", [])
            if isinstance(item, dict)
            and item.get("repair_role") == "movable"
            and isinstance(item.get("selector_id"), str)
        }
    )
    if mapping.get("state") != "exact":
        return {
            "state": mapping.get("state"),
            "reason_code": mapping.get("reason_code"),
            "candidate_selector_ids": candidate_ids,
            "missing_reference_kinds": [
                "semantic_object",
                "semantic_relation",
            ],
        }
    selector_id = mapping.get("selected_selector_id")
    selectors = [
        item
        for item in registry.get("selectors", [])
        if isinstance(item, dict) and item.get("selector_id") == selector_id
    ]
    if len(selectors) != 1:
        raise SourceAttributionError("selected selector must resolve exactly once")
    selector = selectors[0]
    object_refs = selector.get("semantic_object_refs")
    relation_refs = selector.get("semantic_relation_refs")
    for label, refs in (
        ("semantic object", object_refs),
        ("semantic relation", relation_refs),
    ):
        if not isinstance(refs, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in refs
        ) or len(set(refs)) != len(refs):
            raise SourceAttributionError(f"{label} references are invalid")
    unknown_objects = sorted(set(object_refs) - required_objects)
    if unknown_objects:
        raise SourceAttributionError("semantic object reference is undeclared")
    unknown_relations = sorted(set(relation_refs) - declared_relations)
    if unknown_relations:
        raise SourceAttributionError("semantic relation reference is undeclared")
    missing = [
        name
        for name, refs in (
            ("semantic_object", object_refs),
            ("semantic_relation", relation_refs),
        )
        if not refs
    ]
    if missing:
        return {
            "state": "unbound",
            "reason_code": "selected_selector_missing_semantic_refs",
            "candidate_selector_ids": [selector_id],
            "missing_reference_kinds": missing,
        }
    return {
        "state": "exact",
        "reason_code": "one_declared_semantic_selector",
        "selector_id": selector_id,
        "candidate_selector_ids": [selector_id],
        "missing_reference_kinds": [],
        "semantic_object_refs": sorted(object_refs),
        "semantic_relation_refs": sorted(relation_refs),
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceAttributionError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Attribute machine findings to declared TikZ source selectors."
    )
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--finding-id", required=True)
    parser.add_argument("--attribution-out", type=Path, required=True)
    parser.add_argument("--target-contract-out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        outputs = (args.attribution_out, args.target_contract_out)
        if outputs[0].resolve(strict=False) == outputs[1].resolve(strict=False):
            raise SourceAttributionError("output paths must be distinct")
        if any(path.exists() or path.is_symlink() for path in outputs):
            raise SourceAttributionError("attribution output already exists")
        report = _load_json(args.report)
        registry = _load_json(args.registry)
        attribution = attribute_findings(
            report,
            registry,
            source_path=args.source,
        )
        contract = build_repair_target_contract(
            report_path=str(args.report),
            report=report,
            registry=registry,
            attribution=attribution,
            finding_id=args.finding_id,
        )
        _write_json(args.attribution_out, attribution)
        _write_json(args.target_contract_out, contract)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SourceAttributionError) as exc:
        print(f"finding-source-attribution: {exc}")
        return 1
    print(json.dumps(attribution, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
