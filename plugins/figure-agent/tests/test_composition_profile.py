from __future__ import annotations

import composition_profile
import pytest


def _payload() -> dict[str, object]:
    return {
        "schema": "figure-agent.composition-profile.v1",
        "status": "experimental_attempt_scoped",
        "policy": "preserve_llm_composition",
        "requirements": [
            "semantic_load_controls_area",
            "related_panels_are_grouped",
            "negative_space_is_reserved",
        ],
        "forbidden": [
            "fixed_coordinates",
            "fixed_panel_rectangles",
            "primitive_geometry",
            "palette_override",
        ],
    }


def test_compiles_non_coordinate_composition_assistance() -> None:
    compiled = composition_profile.compile_composition_profile(_payload())

    assert compiled["policy"] == "preserve_llm_composition"
    assert compiled["authoring_directives"]
    assert all("(" not in item for item in compiled["authoring_directives"])
    assert "fixed_coordinates" in compiled["forbidden"]


def test_rejects_user_supplied_coordinates_or_directives() -> None:
    for key, value in (
        ("coordinates", [[0, 0]]),
        ("directives", ["make panel A huge"]),
    ):
        payload = _payload()
        payload[key] = value
        with pytest.raises(composition_profile.CompositionProfileError):
            composition_profile.compile_composition_profile(payload)
