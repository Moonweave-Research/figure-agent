from __future__ import annotations

import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from hybrid.comparison_report import validate_human_verdict_bindings  # noqa: E402
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
SLICE4_NAME = "fig3_trap_schematic_slice4_illustration_grammar"
SLICE4_FIXTURE = PLUGIN_ROOT / "examples" / SLICE4_NAME
COMPARISON_MANIFEST = SLICE4_FIXTURE / "review" / "comparison_manifest.yaml"


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


def test_open_tikz_paths_never_receive_fill_options() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    tikz = render_tikz(scene, TIKZ_PROFILE_PATH)
    backbone_block = tikz.split(
        "% figure-agent:start chain.backbones\n",
        1,
    )[1].split("% figure-agent:end chain.backbones", 1)[0]
    trap_block = tikz.split("% figure-agent:start trap.levels\n", 1)[1].split(
        "% figure-agent:end trap.levels",
        1,
    )[0]

    assert "fill=" not in backbone_block
    assert "fill=" not in trap_block


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


def test_sulfur_sites_lower_as_the_same_compound_charge_glyph() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    tikz = render_tikz(scene, TIKZ_PROFILE_PATH)
    svg = render_svg(scene, SVG_PROFILE_PATH)

    glyph = scene["resolved_tokens"]["glyphs"]["sulfur.sites"]
    expected_glyphs = next(
        len(layer["objects"])
        for layer in scene["layers"]
        if layer["semantic_id"] == "sulfur.sites"
    )
    assert glyph["kind"] == "sulfur_negative"
    assert tikz.count("figure-agent:glyph sulfur_negative") == expected_glyphs
    assert svg.count('data-glyph="sulfur_negative"') == expected_glyphs


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
    compiled_scene = yaml.safe_load(
        (tmp_path / "sulfur_trap_domain.scene.yaml").read_text(encoding="utf-8")
    )

    assert first == second
    assert manifest["artifacts"] == first["artifacts"]
    assert manifest["artifacts"]["scene"]["path"] == "sulfur_trap_domain.scene.yaml"
    assert compiled_scene == compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    assert manifest["publication_acceptance"] == "not_claimed"


def test_slice4_fixture_binds_three_comparable_artifacts() -> None:
    comparison = yaml.safe_load(COMPARISON_MANIFEST.read_text(encoding="utf-8"))

    assert set(comparison["variants"]) == {
        "raw_svg_slice3",
        "grammar_tikz",
        "grammar_svg",
    }
    assert comparison["grammar_pair_same_scene"] is True
    assert comparison["raw_svg_comparator_basis"] == "same_semantic_boundary"
    assert comparison["slice3_source_immutable"] is True
    assert comparison["publication_acceptance"] == "not_claimed"


def test_slice4_rejected_verdict_is_fresh_and_does_not_claim_acceptance() -> None:
    verdict_path = SLICE4_FIXTURE / "review" / "human_illustration_verdict.yaml"
    verdict = yaml.safe_load(verdict_path.read_text(encoding="utf-8"))
    binding = validate_human_verdict_bindings(verdict_path, SLICE4_FIXTURE)

    assert binding["stale"] is False
    assert verdict["reviewer"] == {
        "name": "최문영",
        "reviewed_at": "2026-07-11",
    }
    assert verdict["raw_svg_vs_grammar_svg"] == "worse"
    assert verdict["grammar_svg_vs_tikz_language"] == "matched"
    assert verdict["grammar_tikz_artifact"] == "rejected"
    assert verdict["grammar_svg_artifact"] == "rejected"
    assert verdict["review_state"] == "completed"
    assert verdict["publication_acceptance"] == "not_claimed"
