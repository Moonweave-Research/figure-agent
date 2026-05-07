from __future__ import annotations

import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path

from fig1_l1_scene import build_scene
from verify_fig1_render_parity import SVG, generated_svg_text, render_parity_failures


RENDER_DEPS_AVAILABLE = all(find_spec(module) for module in ("drawsvg", "matplotlib", "numpy"))


class Fig1RenderParityTests(unittest.TestCase):
    @unittest.skipUnless(RENDER_DEPS_AVAILABLE, "render parity tests require drawsvg/matplotlib/numpy")
    def test_current_source_reproduces_tracked_svg(self) -> None:
        self.assertEqual(Path(SVG).read_text(), generated_svg_text(build_scene()))

    @unittest.skipUnless(RENDER_DEPS_AVAILABLE, "render parity tests require drawsvg/matplotlib/numpy")
    def test_detects_stale_tracked_svg_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stale_svg = Path(tmpdir) / "fig1_reference_semantic.svg"
            stale_svg.write_text(Path(SVG).read_text() + "\n<!-- stale -->\n")

            failures = render_parity_failures(stale_svg, scene=build_scene())

        self.assertTrue(any("render parity mismatch" in failure for failure in failures), failures)

    def test_gate_runner_includes_render_parity(self) -> None:
        from run_fig1_gates import GATES

        self.assertIn("verify_fig1_render_parity.py", {gate.script for gate in GATES})


if __name__ == "__main__":
    unittest.main()
