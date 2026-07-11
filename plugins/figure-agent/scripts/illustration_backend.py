from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

_PROFILE_SCHEMA = "figure-agent.illustration-backend-profile.v1"
_PROFILE_FIELDS = {
    "schema",
    "backend",
    "canvas",
    "color_roles",
    "stroke_families",
    "emphasis",
    "supported_tokens",
}
_COLOR_ROLES = {"polymer", "sulfur", "carrier", "neutral"}
_STROKE_FAMILIES = {"support", "primary", "focal"}
_EMPHASIS = {"background", "structure", "focal"}


class IllustrationBackendError(ValueError):
    """Raised when a scene or backend profile cannot be lowered safely."""


def load_backend_profile(path: Path, backend: str) -> dict[str, Any]:
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict) or set(profile) != _PROFILE_FIELDS:
        raise IllustrationBackendError("profile_fields_invalid")
    if profile["schema"] != _PROFILE_SCHEMA or profile["backend"] != backend:
        raise IllustrationBackendError("profile_schema_or_backend_invalid")
    if set(profile["color_roles"]) != _COLOR_ROLES:
        raise IllustrationBackendError("color_roles_invalid")
    if set(profile["stroke_families"]) != _STROKE_FAMILIES:
        raise IllustrationBackendError("stroke_families_invalid")
    if set(profile["emphasis"]) != _EMPHASIS:
        raise IllustrationBackendError("emphasis_invalid")
    if profile["supported_tokens"] != {
        "curvature": ["organic_backbone"],
        "joins": ["round"],
        "caps": ["round"],
        "glyphs": ["sulfur_negative"],
    }:
        raise IllustrationBackendError("supported_tokens_invalid")
    _validate_profile_values(profile, backend)
    return profile


def validate_scene_tokens(scene: dict[str, Any], profile: dict[str, Any]) -> None:
    if scene.get("schema") != "figure-agent.illustration-scene.v1":
        raise IllustrationBackendError("scene_schema_invalid")
    tokens = scene.get("resolved_tokens")
    if not isinstance(tokens, dict):
        raise IllustrationBackendError("tokens_invalid")
    supported = profile["supported_tokens"]
    checks = {
        "curvature": "curvature",
        "join": "joins",
        "cap": "caps",
    }
    for scene_key, profile_key in checks.items():
        if tokens.get(scene_key) not in supported[profile_key]:
            raise IllustrationBackendError(f"token_unsupported: {scene_key}")
    slot_roles = tokens.get("slot_roles")
    if not isinstance(slot_roles, dict) or set(slot_roles) != set(scene["semantic_ids"]):
        raise IllustrationBackendError("slot_roles_invalid")
    for roles in slot_roles.values():
        if (
            roles.get("stroke_family") not in profile["stroke_families"]
            or roles.get("color_role") not in profile["color_roles"]
            or roles.get("emphasis") not in profile["emphasis"]
        ):
            raise IllustrationBackendError("token_unsupported: slot_role")
    glyphs = tokens.get("glyphs")
    if not isinstance(glyphs, dict) or set(glyphs) != {"sulfur.sites"}:
        raise IllustrationBackendError("glyph_bindings_invalid")
    site_glyph = glyphs["sulfur.sites"]
    if (
        site_glyph.get("kind") not in supported["glyphs"]
        or not 0.0 < site_glyph.get("mark_half_width_ratio", 0.0) < 1.0
        or not 0.0 < site_glyph.get("mark_stroke_ratio", 0.0) <= 1.0
    ):
        raise IllustrationBackendError("token_unsupported: glyph")


def style_for_slot(
    scene: dict[str, Any],
    profile: dict[str, Any],
    slot: str,
) -> dict[str, Any]:
    roles = scene["resolved_tokens"]["slot_roles"][slot]
    return {
        "color": profile["color_roles"][roles["color_role"]],
        "stroke": profile["stroke_families"][roles["stroke_family"]],
        "opacity": profile["emphasis"][roles["emphasis"]],
    }


def _validate_profile_values(profile: dict[str, Any], backend: str) -> None:
    if not all(
        isinstance(value, int | float) and 0.0 <= value <= 1.0
        for value in profile["emphasis"].values()
    ):
        raise IllustrationBackendError("emphasis_value_invalid")
    if backend == "svg":
        if profile["canvas"] != {"view_box": [0, 0, 100, 100]}:
            raise IllustrationBackendError("canvas_invalid")
        colors = profile["color_roles"].values()
        if not all(
            set(value) == {"stroke", "fill"}
            and all(re.fullmatch(r"#[0-9A-F]{6}", item) for item in value.values())
            for value in colors
        ):
            raise IllustrationBackendError("color_value_invalid")
        if not all(
            isinstance(value, int | float) and value > 0
            for value in profile["stroke_families"].values()
        ):
            raise IllustrationBackendError("stroke_value_invalid")
        return
    if backend != "tikz" or profile["canvas"] != {"scale_cm": 5.0}:
        raise IllustrationBackendError("canvas_invalid")
    if not all(
        set(value) == {"stroke", "fill"}
        and all(re.fullmatch(r"[A-Za-z][A-Za-z0-9!]*", item) for item in value.values())
        for value in profile["color_roles"].values()
    ):
        raise IllustrationBackendError("color_value_invalid")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?pt", value)
        for value in profile["stroke_families"].values()
    ):
        raise IllustrationBackendError("stroke_value_invalid")
