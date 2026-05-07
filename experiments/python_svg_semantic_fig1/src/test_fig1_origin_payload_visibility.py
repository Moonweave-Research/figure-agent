from __future__ import annotations

import unittest
from dataclasses import replace
from importlib.util import find_spec

from fig1_l1_scene import build_scene


RENDER_DEPS_AVAILABLE = all(find_spec(module) for module in ("drawsvg", "matplotlib", "numpy"))


class Fig1OriginPayloadVisibilityTests(unittest.TestCase):
    @unittest.skipUnless(RENDER_DEPS_AVAILABLE, "origin payload visibility tests require drawsvg/matplotlib/numpy")
    def test_origin_heat_and_chain_payload_labels_are_visible(self) -> None:
        from render_fig1_l1 import svg_text_for_scene

        scene = build_scene()
        origin = scene.object_by_id("sulfur_polymer_origin").payload
        svg = svg_text_for_scene(scene)

        self.assertIn(origin.heat_label, svg)
        self.assertIn(origin.chain_label, svg)

    @unittest.skipUnless(RENDER_DEPS_AVAILABLE, "origin payload visibility tests require drawsvg/matplotlib/numpy")
    def test_origin_label_rendering_tracks_payload_mutation(self) -> None:
        from render_fig1_l1 import svg_text_for_scene

        scene = build_scene()
        origin = scene.object_by_id("sulfur_polymer_origin").payload
        mutated_origin = replace(origin, heat_label="Heat 140 C", chain_label="-S8- chain")
        svg = svg_text_for_scene(scene.replace_payload("sulfur_polymer_origin", mutated_origin))

        self.assertIn("Heat 140 C", svg)
        self.assertIn("-S8- chain", svg)
        self.assertNotIn(origin.heat_label, svg)
        self.assertNotIn(origin.chain_label, svg)
        self.assertNotIn(">Delta<", svg)
        self.assertNotIn(">Sx<", svg)


if __name__ == "__main__":
    unittest.main()
