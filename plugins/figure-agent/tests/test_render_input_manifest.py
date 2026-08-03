from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import render_input_manifest  # noqa: E402


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, Path], Path]:
    root = tmp_path / "demo"
    build = root / "build"
    build.mkdir(parents=True)
    render = build / "demo.pdf"
    render.write_bytes(b"pdf")
    source = root / "demo.tex"
    style = tmp_path / "installed" / "polymer-paper-preamble.sty"
    source.write_text("source", encoding="utf-8")
    style.parent.mkdir()
    style.write_text("style", encoding="utf-8")
    output = render_input_manifest.manifest_path(render)
    inputs = {"source_tex": source, "style_lock": style}
    render_input_manifest.write_manifest(
        fixture="demo", render_pdf=render, inputs=inputs, output=output
    )
    return root, render, inputs, output


def test_manifest_freshness_ignores_copy_mtime_when_bytes_match(tmp_path: Path) -> None:
    _, render, inputs, output = _fixture(tmp_path)
    style = inputs["style_lock"]
    copied_style = tmp_path / "reinstalled" / style.name
    copied_style.parent.mkdir()
    copied_style.write_bytes(style.read_bytes())
    future = render.stat().st_mtime + 100
    os.utime(copied_style, (future, future))
    copied_inputs = {**inputs, "style_lock": copied_style}

    assert (
        render_input_manifest.freshness(
            manifest=output,
            fixture="demo",
            render_pdf=render,
            inputs=copied_inputs,
        )
        == render_input_manifest.FRESH
    )


def test_manifest_freshness_detects_input_and_render_drift(tmp_path: Path) -> None:
    _, render, inputs, output = _fixture(tmp_path)
    inputs["source_tex"].write_text("changed", encoding="utf-8")
    assert (
        render_input_manifest.freshness(
            manifest=output, fixture="demo", render_pdf=render, inputs=inputs
        )
        == render_input_manifest.STALE
    )

    inputs["source_tex"].write_text("source", encoding="utf-8")
    render.write_bytes(b"changed pdf")
    assert (
        render_input_manifest.freshness(
            manifest=output, fixture="demo", render_pdf=render, inputs=inputs
        )
        == render_input_manifest.STALE
    )


def test_manifest_freshness_fails_closed_on_invalid_role_set(tmp_path: Path) -> None:
    _, render, inputs, output = _fixture(tmp_path)

    assert (
        render_input_manifest.freshness(
            manifest=output,
            fixture="demo",
            render_pdf=render,
            inputs={**inputs, "spec": tmp_path / "missing.yaml"},
        )
        == render_input_manifest.INVALID
    )
