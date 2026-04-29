from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "export_svg.sh"


def test_export_svg_rejects_output_without_svg_suffix(tmp_path: Path) -> None:
    """Mirror of test_svg_to_png_rejects_output_without_png_suffix — the same
    no-extension stray file failure mode applies to pdftocairo -svg if the
    caller drops the .svg suffix."""
    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%dummy\n")  # not a real PDF; pdftocairo is unreached
    no_ext_output = tmp_path / "out_without_suffix"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(pdf), str(no_ext_output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "must end with .svg" in result.stderr
    assert not no_ext_output.exists()
