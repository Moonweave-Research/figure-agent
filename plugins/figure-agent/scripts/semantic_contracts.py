"""Validate opt-in authoring semantic contracts in spec.yaml payloads."""

from __future__ import annotations

from typing import Any

SCHEMA = "figure-agent.semantic-contracts.v1"


class SemanticContractError(ValueError):
    """Raised when spec.yaml semantic authoring contracts are malformed."""


def is_authoring_context_enabled(spec: dict[str, Any]) -> bool:
    config = spec.get("authoring_context_pack")
    return isinstance(config, dict) and config.get("enabled") is True


def _require_text(value: object, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticContractError(code)
    return value.strip()


def _panel_id(panel: dict[str, Any], index: int) -> str:
    value = panel.get("id")
    return str(value).strip() if value is not None and str(value).strip() else f"panel_{index + 1}"


def _normalize_claim(panel_id: str, value: object, index: int) -> dict[str, str]:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise SemanticContractError(f"panels[{panel_id}].semantic_claims[{index}]_empty")
        return {"id": f"{panel_id}.claim{index + 1}", "claim": text}
    if not isinstance(value, dict):
        raise SemanticContractError(f"panels[{panel_id}].semantic_claims[{index}]_invalid")
    claim_id = _require_text(
        value.get("id"),
        f"panels[{panel_id}].semantic_claims[{index}].id_missing",
    )
    claim = _require_text(
        value.get("claim") or value.get("text"),
        f"panels[{panel_id}].semantic_claims[{index}].claim_missing",
    )
    return {"id": claim_id, "claim": claim}


def _normalize_invariant(panel_id: str, value: object, index: int) -> dict[str, str]:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise SemanticContractError(f"panels[{panel_id}].locked_invariants[{index}]_empty")
        return {"id": f"{panel_id}.invariant{index + 1}", "invariant": text}
    if not isinstance(value, dict):
        raise SemanticContractError(f"panels[{panel_id}].locked_invariants[{index}]_invalid")
    invariant_id = _require_text(
        value.get("id"),
        f"panels[{panel_id}].locked_invariants[{index}].id_missing",
    )
    invariant = _require_text(
        value.get("invariant") or value.get("text"),
        f"panels[{panel_id}].locked_invariants[{index}].invariant_missing",
    )
    return {"id": invariant_id, "invariant": invariant}


def collect_semantic_contracts(spec: dict[str, Any]) -> dict[str, Any]:
    if not is_authoring_context_enabled(spec):
        return {
            "schema": SCHEMA,
            "enabled": False,
            "semantic_claims": [],
            "locked_invariants": [],
        }

    panels = spec.get("panels", [])
    if not isinstance(panels, list):
        raise SemanticContractError("panels_invalid")

    claims: list[dict[str, str]] = []
    invariants: list[dict[str, str]] = []
    for panel_index, panel in enumerate(panels):
        if not isinstance(panel, dict):
            continue
        panel_id = _panel_id(panel, panel_index)
        raw_claims = panel.get("semantic_claims", [])
        raw_invariants = panel.get("locked_invariants", [])
        if raw_claims is None:
            raw_claims = []
        if raw_invariants is None:
            raw_invariants = []
        if not isinstance(raw_claims, list):
            raise SemanticContractError(f"panels[{panel_id}].semantic_claims_invalid")
        if not isinstance(raw_invariants, list):
            raise SemanticContractError(f"panels[{panel_id}].locked_invariants_invalid")
        for claim_index, claim in enumerate(raw_claims):
            normalized = _normalize_claim(panel_id, claim, claim_index)
            normalized["panel_id"] = panel_id
            claims.append(normalized)
        for invariant_index, invariant in enumerate(raw_invariants):
            normalized = _normalize_invariant(panel_id, invariant, invariant_index)
            normalized["panel_id"] = panel_id
            invariants.append(normalized)

    return {
        "schema": SCHEMA,
        "enabled": True,
        "semantic_claims": claims,
        "locked_invariants": invariants,
    }


def semantic_claim_questions(spec: dict[str, Any]) -> list[str]:
    contracts = collect_semantic_contracts(spec)
    questions: list[str] = []
    for claim in contracts["semantic_claims"]:
        questions.append(
            f"[{claim['panel_id']}:{claim['id']}] Does the rendered panel visually support "
            f"this claim without adding unstated physics? {claim['claim']}"
        )
    return questions
