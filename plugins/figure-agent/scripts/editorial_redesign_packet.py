"""Build read-only editorial redesign handoff packets."""

from __future__ import annotations

import fixture_identity

SCHEMA = "figure-agent.editorial-redesign-packet.v1"
MUTATION_BOUNDARY = "no_source_mutation"
DEFAULT_TARGET_STYLE_CLASS = "restrained editorial multipanel scientific schematic"
DEFAULT_MUST_PRESERVE = ["panel roles", "required labels", "semantic colors"]
MUST_NOT_DO = ["semantic rewrite", "SVG polish as repair", "accepted/golden mutation"]
HUMAN_QUESTION = (
    "I can prepare editorial redesign candidates under these guardrails. "
    "Should I proceed with candidate preparation?"
)


class EditorialRedesignPacketError(ValueError):
    """Raised when an editorial redesign handoff packet cannot be built safely."""


def _validate_fixture(fixture: str) -> None:
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise EditorialRedesignPacketError(f"fixture_invalid:{fixture}") from exc


def _require_present(payload: dict[str, object] | None, *, label: str) -> dict[str, object]:
    if not isinstance(payload, dict) or payload.get("state") != "present":
        raise EditorialRedesignPacketError(f"{label}_missing")
    return payload


def _string_list(value: object, *, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback.copy()
    items = [item for item in value if isinstance(item, str) and item.strip()]
    return items or fallback.copy()


def build_editorial_redesign_packet(
    fixture: str,
    *,
    style_pack: dict[str, object] | None,
    comparison: dict[str, object] | None,
) -> dict[str, object]:
    """Return a handoff-only request packet for editorial redesign candidates."""
    _validate_fixture(fixture)
    pack = _require_present(style_pack, label="style_benchmark_pack")
    comparison_payload = _require_present(comparison, label="style_benchmark_comparison")
    target_style_class = pack.get("target_style_class")
    if not isinstance(target_style_class, str) or not target_style_class.strip():
        target_style_class = DEFAULT_TARGET_STYLE_CLASS
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "mutation_boundary": MUTATION_BOUNDARY,
        "state": "ready_for_human_handoff_choice",
        "candidate_request": {
            "target_style_class": target_style_class,
            "must_preserve": _string_list(
                comparison_payload.get("forbidden_semantic_changes"),
                fallback=DEFAULT_MUST_PRESERVE,
            ),
            "must_not_do": MUST_NOT_DO.copy(),
        },
        "human_question": HUMAN_QUESTION,
        "next_agent_action": "prepare_editorial_redesign_candidates_only_after_human_approval",
    }
