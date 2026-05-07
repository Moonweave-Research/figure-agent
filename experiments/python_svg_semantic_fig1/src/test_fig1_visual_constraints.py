from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.visual_constraints import semantic_group_bboxes


class Fig1VisualConstraintsTests(unittest.TestCase):
    def test_nested_svg_fragment_offsets_child_bbox(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">
<g data-semantic-id="plot">
  <svg x="80" y="40" width="60" height="50" viewBox="0 0 60 50">
    <path d="M 5 5 L 55 45" stroke="#000000" stroke-width="2"/>
  </svg>
</g>
</svg>"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "fragment.svg"
            path.write_text(svg, encoding="utf-8")

            bbox = semantic_group_bboxes(path)["plot"]

        self.assertGreaterEqual(bbox.left, 84.0)
        self.assertGreaterEqual(bbox.top, 44.0)
        self.assertLessEqual(bbox.right, 136.0)
        self.assertLessEqual(bbox.bottom, 86.0)


if __name__ == "__main__":
    unittest.main()
