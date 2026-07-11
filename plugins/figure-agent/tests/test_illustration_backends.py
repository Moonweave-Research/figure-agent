from __future__ import annotations

import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from illustration_backend import (  # noqa: E402
    IllustrationBackendError,
    load_backend_profile,
)
from illustration_backend_svg import render_svg  # noqa: E402
from illustration_backend_tikz import render_tikz  # noqa: E402
from illustration_scene import compile_illustration_scene  # noqa: E402
from render_illustration_motif import render_pair  # noqa: E402

GRAMMAR_PATH = (
    PLUGIN_ROOT / "styles" / "illustration-grammar" / "sulfur_trap_domain.v1.yaml"
)
INSTANCE_PATH = (
    PLUGIN_ROOT
    / "examples"
    / "fig3_trap_schematic_slice4_illustration_grammar"
    / "motif_instance.yaml"
)
TIKZ_PROFILE_PATH = (
    PLUGIN_ROOT
    / "styles"
    / "illustration-grammar"
    / "backends"
    / "polymer-tikz.v1.yaml"
)
SVG_PROFILE_PATH = (
    PLUGIN_ROOT
    / "styles"
    / "illustration-grammar"
    / "backends"
    / "polymer-svg.v1.yaml"
)


def test_backends_preserve_the_same_semantic_slots() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    tikz = render_tikz(scene, TIKZ_PROFILE_PATH)
    svg = render_svg(scene, SVG_PROFILE_PATH)

    for semantic_id in scene["semantic_ids"]:
        assert f"figure-agent:start {semantic_id}" in tikz
        assert f'id="{semantic_id}"' in svg


def test_unsupported_token_fails_instead_of_falling_back() -> None:
    scene = copy.deepcopy(compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH))
    scene["resolved_tokens"]["curvature"] = "airbrush_blob"

    with pytest.raises(IllustrationBackendError, match="token_unsupported"):
        render_svg(scene, SVG_PROFILE_PATH)


def test_backend_profiles_cover_identical_visual_roles() -> None:
    tikz_profile = load_backend_profile(TIKZ_PROFILE_PATH, backend="tikz")
    svg_profile = load_backend_profile(SVG_PROFILE_PATH, backend="svg")

    assert set(tikz_profile["color_roles"]) == set(svg_profile["color_roles"])
    assert set(tikz_profile["stroke_families"]) == set(svg_profile["stroke_families"])
    assert set(tikz_profile["emphasis"]) == set(svg_profile["emphasis"])


def test_backends_preserve_visual_orientation_across_coordinate_conventions() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    tikz = render_tikz(scene, TIKZ_PROFILE_PATH)
    svg = render_svg(scene, SVG_PROFILE_PATH)

    assert "(0.4, 4.15)" in tikz
    assert 'd="M 8 17 C' in svg


def test_backend_strokes_have_equivalent_physical_weight() -> None:
    tikz_profile = load_backend_profile(TIKZ_PROFILE_PATH, backend="tikz")
    svg_profile = load_backend_profile(SVG_PROFILE_PATH, backend="svg")
    svg_units_per_tex_point = 100 / (5.0 * 72.27 / 2.54)

    for role, tikz_width in tikz_profile["stroke_families"].items():
        points = float(tikz_width.removesuffix("pt"))
        assert svg_profile["stroke_families"][role] == pytest.approx(
            points * svg_units_per_tex_point,
            abs=0.01,
        )


def test_svg_is_geometry_only_and_self_contained() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    svg = render_svg(scene, SVG_PROFILE_PATH)
    root = ET.fromstring(svg)
    local_tags = {element.tag.rsplit("}", 1)[-1] for element in root.iter()}

    assert "text" not in local_tags
    assert "script" not in local_tags
    assert "style" not in local_tags
    assert "image" not in local_tags
    assert "filter" not in svg
    assert "url(" not in svg
    assert "http" not in svg.removeprefix('<svg xmlns="http://www.w3.org/2000/svg"')


def test_render_pair_is_byte_deterministic_and_records_non_acceptance(tmp_path: Path) -> None:
    first = render_pair(
        GRAMMAR_PATH,
        INSTANCE_PATH,
        TIKZ_PROFILE_PATH,
        SVG_PROFILE_PATH,
        tmp_path,
    )
    second = render_pair(
        GRAMMAR_PATH,
        INSTANCE_PATH,
        TIKZ_PROFILE_PATH,
        SVG_PROFILE_PATH,
        tmp_path,
    )
    manifest = yaml.safe_load((tmp_path / "render_manifest.yaml").read_text(encoding="utf-8"))

    assert first == second
    assert manifest["artifacts"] == first["artifacts"]
    assert manifest["publication_acceptance"] == "not_claimed"
