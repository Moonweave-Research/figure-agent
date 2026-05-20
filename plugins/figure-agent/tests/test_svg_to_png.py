from __future__ import annotations

import os
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


def test_svg_to_png_rejects_output_without_png_suffix(tmp_path):
    """A no-extension stray file in exports/ used to occur when the caller
    dropped the .png suffix. Defend at the script level so the caller sees
    an immediate error instead of silently producing a stray file."""
    svg = tmp_path / "in.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    no_ext_output = tmp_path / "out_without_suffix"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(svg), str(no_ext_output)],
        capture_output=True,
        env={**os.environ, "PATH": "/usr/bin:/bin"},
        text=True,
    )
    assert result.returncode != 0
    assert "must end with .png" in result.stderr
    assert not no_ext_output.exists()


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
