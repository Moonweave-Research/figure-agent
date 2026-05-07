from __future__ import annotations

import hashlib
import unittest

from engine.domain_primitives import PowerLawDecayPlot


class MatplotlibSubrendererTests(unittest.TestCase):
    def test_decay_fragment_preserves_log_labels(self) -> None:
        from engine.matplotlib_subrenderers import power_law_decay_fragment

        payload = PowerLawDecayPlot(
            title="Current decay",
            model="power_law",
            slope=-0.72,
            log_t_min=-3,
            log_t_max=3,
            log_i_top=0,
            log_i_bottom=-8,
            samples=64,
            label="extract n",
            color="#a81016",
        )

        fragment = power_law_decay_fragment(payload, width=180, height=120)

        self.assertEqual(fragment.subrenderer, "matplotlib")
        self.assertEqual(fragment.role, "electrical-decay-plot")
        self.assertIn("<text", fragment.inner_svg)
        self.assertIn("log t", fragment.inner_svg)
        self.assertIn("log I", fragment.inner_svg)
        self.assertIn("<path", fragment.inner_svg)

    def test_matplotlib_fragments_are_deterministic(self) -> None:
        from engine.matplotlib_subrenderers import power_law_decay_fragment

        payload = PowerLawDecayPlot(
            title="Current decay",
            model="power_law",
            slope=-0.72,
            log_t_min=-3,
            log_t_max=3,
            log_i_top=0,
            log_i_bottom=-8,
            samples=64,
            label="extract n",
            color="#a81016",
        )

        first = power_law_decay_fragment(payload, width=180, height=120).inner_svg
        second = power_law_decay_fragment(payload, width=180, height=120).inner_svg

        self.assertEqual(
            hashlib.sha256(first.encode()).hexdigest(),
            hashlib.sha256(second.encode()).hexdigest(),
        )


class MatplotlibStyleAdapterTests(unittest.TestCase):
    def test_fig1_decay_style_keeps_semantic_labels(self) -> None:
        from engine.matplotlib_subrenderers import (
            fig1_electrical_style,
            power_law_decay_fragment,
        )

        payload = PowerLawDecayPlot(
            title="Current decay",
            model="power_law",
            slope=-0.72,
            log_t_min=-3,
            log_t_max=3,
            log_i_top=0,
            log_i_bottom=-8,
            samples=64,
            label="extract n",
            color="#0b4bb3",
        )

        fragment = power_law_decay_fragment(
            payload, width=168, height=108, style=fig1_electrical_style()
        )

        self.assertIn("log t", fragment.inner_svg)
        self.assertIn("log I", fragment.inner_svg)
        self.assertIn("extract n", fragment.inner_svg)
        self.assertNotIn(">0<", fragment.inner_svg)
        self.assertNotIn(">2<", fragment.inner_svg)

    def test_fig1_style_fragments_are_deterministic(self) -> None:
        from engine.matplotlib_subrenderers import (
            fig1_electrical_style,
            power_law_decay_fragment,
        )

        payload = PowerLawDecayPlot(
            title="Current decay",
            model="power_law",
            slope=-0.72,
            log_t_min=-3,
            log_t_max=3,
            log_i_top=0,
            log_i_bottom=-8,
            samples=64,
            label="extract n",
            color="#0b4bb3",
        )
        style = fig1_electrical_style()

        first = power_law_decay_fragment(
            payload, width=168, height=108, style=style
        ).inner_svg
        second = power_law_decay_fragment(
            payload, width=168, height=108, style=style
        ).inner_svg

        self.assertEqual(
            hashlib.sha256(first.encode()).hexdigest(),
            hashlib.sha256(second.encode()).hexdigest(),
        )


class RdkitSubrendererTests(unittest.TestCase):
    def test_s8_fragment_generates_svg_paths(self) -> None:
        from engine.rdkit_subrenderers import s8_ring_fragment

        fragment = s8_ring_fragment(width=130, height=110)

        self.assertEqual(fragment.subrenderer, "rdkit")
        self.assertEqual(fragment.role, "origin-s8-ring")
        self.assertIn("<path", fragment.inner_svg)
        self.assertGreaterEqual(fragment.inner_svg.count("<path"), 8)

    def test_s8_fragment_is_deterministic(self) -> None:
        from engine.rdkit_subrenderers import s8_ring_fragment

        first = s8_ring_fragment(width=130, height=110).inner_svg
        second = s8_ring_fragment(width=130, height=110).inner_svg

        self.assertEqual(
            hashlib.sha256(first.encode()).hexdigest(),
            hashlib.sha256(second.encode()).hexdigest(),
        )


class LibraryPreviewScriptTests(unittest.TestCase):
    def test_preview_script_is_importable(self) -> None:
        import preview_fig1_library_subrenderers as preview

        self.assertTrue(str(preview.OUT_DIR).endswith("fig1_v27_library_subrenderers"))
        self.assertTrue(callable(preview.build_preview_svg))


if __name__ == "__main__":
    unittest.main()
