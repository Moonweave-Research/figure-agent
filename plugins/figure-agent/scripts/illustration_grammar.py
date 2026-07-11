from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_SCHEMA = "figure-agent.illustration-grammar.v1"
_MOTIF_FAMILY = "sulfur_trap_domain"
_SEMANTIC_SLOTS = {
    "chain.backbones",
    "sulfur.regions",
    "sulfur.sites",
    "trap.levels",
    "trapped.carriers",
}
_LAYER_ORDER = [
    "sulfur.regions",
    "chain.backbones",
    "sulfur.sites",
    "trap.levels",
    "trapped.carriers",
]
_RELATIONS = [
    ["sulfur.sites", "attached_to", "chain.backbones"],
    ["sulfur.sites", "located_in", "sulfur.regions"],
    ["trap.levels", "co_located_with", "sulfur.regions"],
    ["trapped.carriers", "sits_on", "trap.levels"],
]
_VISUAL_TOKENS = {
    "stroke_families": ["support", "primary", "focal"],
    "color_roles": ["polymer", "sulfur", "carrier", "neutral"],
    "curvature": ["organic_backbone"],
    "joins": ["round"],
    "caps": ["round"],
    "emphasis": ["background", "structure", "focal"],
}
_OPTICAL_RULES = {
    "minimum_clearance_em": 0.35,
    "carrier_centering": "optical",
    "repeated_site_variation": "controlled",
}
_OWNERSHIP = {
    "grammar": ["motif_geometry", "layer_order", "visual_tokens"],
    "tikz": ["global_panel_composition", "typography", "labels", "inter_panel_arrows"],
}
_TOP_LEVEL_FIELDS = {
    "schema",
    "motif_family",
    "semantic_slots",
    "relations",
    "layer_order",
    "visual_tokens",
    "optical_rules",
    "ownership",
}


class IllustrationGrammarError(ValueError):
    """Raised when an illustration grammar violates the closed contract."""


def load_illustration_grammar(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise IllustrationGrammarError("grammar_invalid: expected a mapping")

    fields = set(payload)
    unknown = fields - _TOP_LEVEL_FIELDS
    if unknown:
        raise IllustrationGrammarError(f"field_forbidden: {sorted(unknown)[0]}")
    missing = _TOP_LEVEL_FIELDS - fields
    if missing:
        raise IllustrationGrammarError(f"field_missing: {sorted(missing)[0]}")
    if payload["schema"] != _SCHEMA:
        raise IllustrationGrammarError("schema_unsupported")
    if payload["motif_family"] != _MOTIF_FAMILY:
        raise IllustrationGrammarError("motif_family_invalid")

    semantic_slots = payload["semantic_slots"]
    if not isinstance(semantic_slots, list) or set(semantic_slots) != _SEMANTIC_SLOTS:
        raise IllustrationGrammarError("semantic_slots_invalid")
    if payload["layer_order"] != _LAYER_ORDER:
        raise IllustrationGrammarError("layer_order_incomplete")
    if payload["relations"] != _RELATIONS:
        raise IllustrationGrammarError("relations_invalid")
    if payload["visual_tokens"] != _VISUAL_TOKENS:
        raise IllustrationGrammarError("visual_tokens_invalid")
    if payload["optical_rules"] != _OPTICAL_RULES:
        raise IllustrationGrammarError("optical_rules_invalid")
    if payload["ownership"] != _OWNERSHIP:
        raise IllustrationGrammarError("ownership_invalid")

    return payload
