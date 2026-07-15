"""Attempt-scoped composition assistance that preserves authoring freedom."""

from __future__ import annotations

from collections.abc import Mapping

SCHEMA = "figure-agent.composition-profile.v1"
STATUS = "experimental_attempt_scoped"
POLICY = "preserve_llm_composition"
REQUIREMENTS = [
    "semantic_load_controls_area",
    "related_panels_are_grouped",
    "negative_space_is_reserved",
]
FORBIDDEN = [
    "fixed_coordinates",
    "fixed_panel_rectangles",
    "primitive_geometry",
    "palette_override",
]
DIRECTIVES = [
    (
        "Choose the figure composition yourself from the scientific narrative; "
        "do not default to equal-size panels unless their semantic load is equal."
    ),
    "Allocate more area to the primary explanatory scene than to supporting evidence.",
    "Group panels that form one causal reading sequence and preserve visible negative space.",
    (
        "Treat panel count, panel proportions, and reading path as authoring decisions; "
        "no coordinates or panel rectangles are prescribed by this profile."
    ),
]
EXPECTED_KEYS = {"schema", "status", "policy", "requirements", "forbidden"}


class CompositionProfileError(ValueError):
    """Raised when a composition profile exceeds the bounded intervention."""


def _reject_nested_payload(value: object, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in {"coordinates", "panels", "sizes", "colors", "directives"}:
                raise CompositionProfileError(f"forbidden key '{key}' at {path}")
            _reject_nested_payload(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_nested_payload(child, f"{path}[{index}]")


def compile_composition_profile(payload: dict[str, object]) -> dict[str, object]:
    """Validate the fixed intervention and emit deterministic authoring directives."""
    if not isinstance(payload, dict):
        raise CompositionProfileError("payload must be a mapping")
    _reject_nested_payload(payload)
    if set(payload) != EXPECTED_KEYS:
        raise CompositionProfileError(
            "payload keys must be exactly: " + ", ".join(sorted(EXPECTED_KEYS))
        )
    if payload["schema"] != SCHEMA:
        raise CompositionProfileError(f"schema must equal {SCHEMA}")
    if payload["status"] != STATUS:
        raise CompositionProfileError(f"status must equal {STATUS}")
    if payload["policy"] != POLICY:
        raise CompositionProfileError(f"policy must equal {POLICY}")
    if payload["requirements"] != REQUIREMENTS:
        raise CompositionProfileError("requirements must match the bounded profile")
    if payload["forbidden"] != FORBIDDEN:
        raise CompositionProfileError("forbidden must match the bounded profile")
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "policy": POLICY,
        "requirements": list(REQUIREMENTS),
        "forbidden": list(FORBIDDEN),
        "authoring_directives": list(DIRECTIVES),
    }
