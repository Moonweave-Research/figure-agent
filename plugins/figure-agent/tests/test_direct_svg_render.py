from __future__ import annotations

from pathlib import Path

import pytest
from direct_svg_candidate import DirectSvgCandidateError
from direct_svg_render import render_with_receipt


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("svg_path", "/tmp/candidate.svg", "svg_path_invalid"),
        ("svg_path", "../candidate.svg", "svg_path_invalid"),
        ("output_path", "renders/../../escape.png", "output_path_invalid"),
        ("semantic_packet", "contract\\packet.yaml", "semantic_packet_path_invalid"),
        ("fontconfig_file", "/tmp/fontconfig.xml", "fontconfig_path_invalid"),
        ("font_file", "../font.otf", "font_path_invalid"),
    ],
)
def test_renderer_rejects_absolute_non_posix_and_traversal_paths(
    tmp_path: Path, field: str, value: str, error: str
) -> None:
    arguments = {
        "root": tmp_path,
        "svg_path": "candidate.svg",
        "output_path": "candidate.png",
        "semantic_packet": "contract/packet.yaml",
        "panel": "C",
        "width": 120,
        "height": 80,
        "fontconfig_file": "contract/fontconfig.xml",
        "font_file": "contract/font.otf",
    }
    arguments[field] = value

    with pytest.raises(DirectSvgCandidateError, match=error):
        render_with_receipt(**arguments)
