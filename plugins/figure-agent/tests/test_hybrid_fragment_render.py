from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "hybrid"))

from render_fragment import (  # noqa: E402
    FragmentRenderError,
    compare_svg_pdf_rasters,
    generate_deterministic_svg,
    render_svg_to_pdf,
)


def test_generator_runs_twice_with_network_disabled_and_requires_same_svg(
    tmp_path: Path,
) -> None:
    generator = tmp_path / "generator.py"
    generator.write_text(
        "import argparse, os\n"
        "p=argparse.ArgumentParser(); p.add_argument('--output', required=True); a=p.parse_args()\n"
        "assert os.environ['FIGURE_AGENT_NETWORK'] == 'disabled'\n"
        "open(a.output, 'w').write('<svg xmlns=\"http://www.w3.org/2000/svg\"/>')\n",
        encoding="utf-8",
    )
    output = tmp_path / "fragment.svg"

    result = generate_deterministic_svg(generator, output)

    assert output.read_text() == '<svg xmlns="http://www.w3.org/2000/svg"/>'
    assert result["repeatable"] is True
    assert result["network"] == "disabled"


def test_generator_accepts_repo_relative_paths(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    generator = fixture / "generator.py"
    generator.write_text(
        "import argparse\n"
        "p=argparse.ArgumentParser(); p.add_argument('--output', required=True); a=p.parse_args()\n"
        "open(a.output, 'w').write('<svg xmlns=\"http://www.w3.org/2000/svg\"/>')\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    generate_deterministic_svg(
        Path("fixture/generator.py"),
        Path("fixture/fragment.svg"),
    )

    assert (fixture / "fragment.svg").is_file()


def test_svg_to_pdf_reports_missing_renderer(monkeypatch, tmp_path: Path) -> None:
    svg = tmp_path / "fragment.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    monkeypatch.setattr(shutil, "which", lambda _name: None)

    with pytest.raises(FragmentRenderError, match="svg_to_pdf_renderer_unavailable"):
        render_svg_to_pdf(svg, tmp_path / "fragment.pdf")


@pytest.mark.skipif(
    shutil.which("rsvg-convert") is None or shutil.which("pdftocairo") is None,
    reason="requires rsvg-convert and pdftocairo",
)
def test_svg_and_pdf_fixed_rasters_are_visually_equivalent(tmp_path: Path) -> None:
    svg = tmp_path / "fragment.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
        '<rect x="20" y="20" width="160" height="80" rx="12" '
        'fill="#f4c56a" stroke="#502000" stroke-width="3"/>'
        "</svg>",
        encoding="utf-8",
    )
    pdf = tmp_path / "fragment.pdf"

    render_svg_to_pdf(svg, pdf)
    comparison = compare_svg_pdf_rasters(svg, pdf, width=800, height=480)

    assert comparison["equivalent"] is True
    assert comparison["mean_absolute_error"] <= 1.0
