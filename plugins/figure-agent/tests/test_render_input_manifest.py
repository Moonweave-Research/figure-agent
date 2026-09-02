from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import compile_run  # noqa: E402
import render_input_manifest  # noqa: E402
from compile_run_fixtures import issue_compile_run  # noqa: E402


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
    run_id = issue_compile_run(build, source_tex=source, render_pdf=render)
    render_input_manifest.write_manifest(
        fixture="demo",
        render_pdf=render,
        inputs=inputs,
        output=output,
        compile_run_id=run_id,
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


def test_manifest_without_a_compile_receipt_is_unbound(tmp_path: Path) -> None:
    _, render, inputs, output = _fixture(tmp_path)
    compile_run.receipt_path(render.parent).unlink()

    assert (
        render_input_manifest.freshness(
            manifest=output, fixture="demo", render_pdf=render, inputs=inputs
        )
        == render_input_manifest.UNBOUND
    )


def test_manifest_bound_to_another_compile_run_is_unbound(tmp_path: Path) -> None:
    root, render, inputs, output = _fixture(tmp_path)
    issue_compile_run(
        render.parent,
        source_tex=root / "demo.tex",
        render_pdf=render,
        run_id="a-different-run",
    )

    assert (
        render_input_manifest.freshness(
            manifest=output, fixture="demo", render_pdf=render, inputs=inputs
        )
        == render_input_manifest.UNBOUND
    )


def test_standalone_cli_refuses_to_declare_a_render_fresh(tmp_path: Path) -> None:
    """The public CLI must not be a "declare these bytes fresh" command."""
    root, render, inputs, output = _fixture(tmp_path)
    output.unlink()
    argv = [
        "--fixture",
        "demo",
        "--render",
        str(render),
        "--input",
        f"source_tex={inputs['source_tex']}",
        "--input",
        f"style_lock={inputs['style_lock']}",
        "--json-output",
        str(output),
    ]

    os.environ.pop(compile_run.RUN_ID_ENV, None)
    with pytest.raises(SystemExit):
        render_input_manifest.main(argv)
    assert not output.exists()

    os.environ[compile_run.RUN_ID_ENV] = "a-different-run"
    try:
        with pytest.raises(SystemExit):
            render_input_manifest.main(argv)
        assert not output.exists()

        os.environ[compile_run.RUN_ID_ENV] = f"run-{root.name}"
        assert render_input_manifest.main(argv) == 0
        assert output.is_file()
    finally:
        os.environ.pop(compile_run.RUN_ID_ENV, None)


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
