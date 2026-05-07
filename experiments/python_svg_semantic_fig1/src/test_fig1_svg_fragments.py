from __future__ import annotations

import unittest

from engine.svg_fragments import (
    SvgFragment,
    basic_svg_tag_counts,
    prefix_svg_ids,
    strip_outer_svg,
    wrapped_fragment_svg,
)


class SvgFragmentTests(unittest.TestCase):
    def test_strip_outer_svg_keeps_inner_content(self) -> None:
        source = '<?xml version="1.0"?><svg width="10" height="10" viewBox="0 0 10 10"><defs><path id="p"/></defs><g><text>A</text></g></svg>'

        inner = strip_outer_svg(source)

        self.assertIn("<defs>", inner)
        self.assertIn("<text>A</text>", inner)
        self.assertNotIn("<svg", inner)
        self.assertNotIn("</svg>", inner)

    def test_strip_outer_svg_handles_doctype_before_svg(self) -> None:
        source = '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n<svg width="10" height="10"><g><path id="line"/></g></svg>'

        inner = strip_outer_svg(source)

        self.assertIn("<path", inner)
        self.assertNotIn("<?xml", inner)
        self.assertNotIn("<!DOCTYPE", inner)
        self.assertNotIn("<svg", inner)

    def test_prefix_svg_ids_updates_references(self) -> None:
        source = '<defs><clipPath id="clip"><path id="path_a"/></clipPath></defs><g clip-path="url(#clip)"><use href="#path_a"/></g>'

        prefixed = prefix_svg_ids(source, "fig1_test")

        self.assertIn('id="fig1_test_clip"', prefixed)
        self.assertIn('id="fig1_test_path_a"', prefixed)
        self.assertIn("url(#fig1_test_clip)", prefixed)
        self.assertIn('href="#fig1_test_path_a"', prefixed)
        self.assertNotIn('id="clip"', prefixed)

    def test_wrapped_fragment_exposes_semantic_metadata(self) -> None:
        fragment = SvgFragment(
            inner_svg='<text x="1" y="2">log t</text>',
            view_box="0 0 100 50",
            width=100,
            height=50,
            subrenderer="matplotlib",
            role="electrical-decay-plot",
        )

        wrapped = wrapped_fragment_svg(
            fragment,
            x=10,
            y=20,
            semantic_id="power_law_decay",
            kind="PowerLawDecayPlot",
        )

        self.assertIn('data-semantic-id="power_law_decay"', wrapped)
        self.assertIn('data-semantic-kind="PowerLawDecayPlot"', wrapped)
        self.assertIn('data-subrenderer="matplotlib"', wrapped)
        self.assertIn('data-fragment-role="electrical-decay-plot"', wrapped)
        self.assertIn('<svg x="10.000" y="20.000"', wrapped)
        self.assertIn("<text", wrapped)

    def test_basic_svg_tag_counts_counts_core_tags(self) -> None:
        counts = basic_svg_tag_counts(
            "<svg><path/><path/><text>A</text><g><clipPath/></g></svg>"
        )

        self.assertEqual(counts["path"], 2)
        self.assertEqual(counts["text"], 1)
        self.assertEqual(counts["clipPath"], 1)


if __name__ == "__main__":
    unittest.main()
