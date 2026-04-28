from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "svg_to_png.sh"


def test_svg_to_png_forces_white_background_flag():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "-b white" in script


@pytest.mark.skipif(shutil.which("rsvg-convert") is None, reason="rsvg-convert not installed")
def test_svg_to_png_outputs_rgb_png_for_transparent_svg(tmp_path):
    svg = tmp_path / "transparent.svg"
    png = tmp_path / "out.png"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
  <text x="2" y="16" font-size="12" fill="black">A</text>
</svg>
""",
        encoding="utf-8",
    )

    subprocess.run(["bash", str(SCRIPT), str(svg), str(png)], check=True)

    with Image.open(png) as image:
        assert image.mode == "RGB"
