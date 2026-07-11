"""Generate and render deterministic semantic SVG fragments."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat


class FragmentRenderError(RuntimeError):
    """Raised when fragment generation or rendering cannot be proven safe."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise FragmentRenderError(f"command_failed: {command[0]}: {detail}")


def _network_disabled_command(command: list[str]) -> list[str]:
    sandbox = shutil.which("sandbox-exec")
    if sandbox is None:
        raise FragmentRenderError("network_sandbox_unavailable")
    profile = "(version 1) (allow default) (deny network*)"
    return [sandbox, "-p", profile, *command]


def generate_deterministic_svg(generator_path: Path, output_path: Path) -> dict[str, Any]:
    """Run a generator twice in a network-denied sandbox and require byte identity."""
    generator_path = generator_path.resolve()
    output_path = output_path.resolve()
    if generator_path.is_symlink() or not generator_path.is_file():
        raise FragmentRenderError("generator_missing")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = {
        key: value
        for key, value in os.environ.items()
        if key.lower() not in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}
    }
    env.update(
        {
            "FIGURE_AGENT_NETWORK": "disabled",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
    )
    with tempfile.TemporaryDirectory() as temporary:
        generated: list[Path] = []
        for index in (1, 2):
            candidate = Path(temporary) / f"fragment-{index}.svg"
            command = _network_disabled_command(
                [sys.executable, str(generator_path), "--output", str(candidate)]
            )
            _run(command, cwd=generator_path.parent, env=env)
            if not candidate.is_file():
                raise FragmentRenderError("generator_output_missing")
            generated.append(candidate)
        if generated[0].read_bytes() != generated[1].read_bytes():
            raise FragmentRenderError("generator_output_nondeterministic")
        shutil.copyfile(generated[0], output_path)
    return {
        "repeatable": True,
        "network": "disabled",
        "svg_sha256": _sha256(output_path),
    }


def render_svg_to_pdf(svg_path: Path, pdf_path: Path) -> dict[str, str]:
    """Render an SVG to PDF with the declared local renderer."""
    renderer = shutil.which("rsvg-convert")
    if renderer is None:
        raise FragmentRenderError("svg_to_pdf_renderer_unavailable")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    _run([renderer, "-b", "white", "-f", "pdf", "-o", str(pdf_path), str(svg_path)])
    return {"renderer": renderer, "pdf_sha256": _sha256(pdf_path)}


def compare_svg_pdf_rasters(
    svg_path: Path,
    pdf_path: Path,
    *,
    width: int,
    height: int,
    max_mean_absolute_error: float = 1.0,
) -> dict[str, Any]:
    """Compare fixed-size rasterizations to detect geometry or clipping drift."""
    svg_renderer = shutil.which("rsvg-convert")
    pdf_renderer = shutil.which("pdftocairo")
    if svg_renderer is None or pdf_renderer is None:
        raise FragmentRenderError("raster_comparison_renderer_unavailable")
    if width <= 0 or height <= 0:
        raise FragmentRenderError("raster_dimensions_invalid")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        svg_png = root / "svg.png"
        pdf_prefix = root / "pdf"
        _run(
            [
                svg_renderer,
                "-b",
                "white",
                "-f",
                "png",
                "-w",
                str(width),
                "-h",
                str(height),
                "-o",
                str(svg_png),
                str(svg_path),
            ]
        )
        _run(
            [
                pdf_renderer,
                "-singlefile",
                "-png",
                "-scale-to-x",
                str(width),
                "-scale-to-y",
                str(height),
                str(pdf_path),
                str(pdf_prefix),
            ]
        )
        with (
            Image.open(svg_png) as svg_image,
            Image.open(pdf_prefix.with_suffix(".png")) as pdf_image,
        ):
            svg_rgb = svg_image.convert("RGB")
            pdf_rgb = pdf_image.convert("RGB")
            if svg_rgb.size != pdf_rgb.size:
                raise FragmentRenderError("raster_size_mismatch")
            difference = ImageChops.difference(svg_rgb, pdf_rgb)
            mean_error = round(sum(ImageStat.Stat(difference).mean) / 3.0, 6)
    return {
        "width": width,
        "height": height,
        "mean_absolute_error": mean_error,
        "equivalent": mean_error <= max_mean_absolute_error,
    }
