from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "export_svg.sh"
def test_export_svg_rejects_output_without_svg_suffix(tmp_path: Path) -> None:
    """The shell wrapper must reject output paths that lack the .svg suffix
    so dvisvgm does not silently write a no-extension stray file."""
    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%dummy\n")  # not a real PDF; dvisvgm is unreached
    no_ext_output = tmp_path / "out_without_suffix"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(pdf), str(no_ext_output)],
        capture_output=True,
        env={**os.environ, "PATH": "/usr/bin:/bin"},
        text=True,
    )
    assert result.returncode != 0
    assert "must end with .svg" in result.stderr
    assert not no_ext_output.exists()


def test_export_svg_uses_renderer_stable_outlined_glyphs() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    assert "--no-fonts=1" in script
    assert "--font-format=woff2" not in script
