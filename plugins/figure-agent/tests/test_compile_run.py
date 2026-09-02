"""Tests for the compile-run receipt every build artifact is bound to."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import compile_run  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(tmp_path: Path, *, state: str = compile_run.PASSED) -> tuple[Path, Path, Path]:
    build = tmp_path / "fixture" / "build"
    build.mkdir(parents=True)
    source = build.parent / "fixture.tex"
    source.write_text("source", encoding="utf-8")
    render = build / "fixture.pdf"
    render.write_bytes(b"%PDF")
    compile_run.write_receipt(
        output=compile_run.receipt_path(build),
        payload=compile_run.build_receipt(
            run_id="run-1",
            started_at="2026-01-01T00:00:00Z",
            engine="lualatex",
            strict_requested=True,
            state=state,
            source_tex=source,
            render_pdf=render if state == compile_run.PASSED else None,
        ),
    )
    return build, source, render


def test_receipt_round_trips_and_names_the_render(tmp_path: Path) -> None:
    build, _, render = _run(tmp_path)

    receipt = compile_run.verified_receipt(build)

    assert receipt is not None
    assert receipt["run_id"] == "run-1"
    assert receipt["render_pdf"] == render.name
    assert receipt["engine"] == "lualatex"
    assert receipt["strict_requested"] is True


def test_receipt_stops_binding_once_the_render_changes(tmp_path: Path) -> None:
    build, _, render = _run(tmp_path)
    render.write_bytes(b"%PDF different")

    assert compile_run.verified_receipt(build) is None


def test_receipt_stops_binding_once_the_render_is_gone(tmp_path: Path) -> None:
    build, _, render = _run(tmp_path)
    render.unlink()

    assert compile_run.verified_receipt(build) is None


def test_failed_run_binds_nothing(tmp_path: Path) -> None:
    build, _, _ = _run(tmp_path, state=compile_run.FAILED)

    assert compile_run.load_receipt(compile_run.receipt_path(build)) is not None
    assert compile_run.verified_receipt(build) is None


def test_unparseable_or_foreign_schema_receipt_loads_as_none(tmp_path: Path) -> None:
    build, _, _ = _run(tmp_path)
    path = compile_run.receipt_path(build)

    path.write_text("{ not json", encoding="utf-8")
    assert compile_run.load_receipt(path) is None

    payload = {"schema": "something.else.v1", "run_id": "run-1", "state": "passed"}
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert compile_run.load_receipt(path) is None


def test_current_source_sha_tracks_the_file_not_the_receipt(tmp_path: Path) -> None:
    build, source, _ = _run(tmp_path)
    receipt = compile_run.verified_receipt(build)
    assert receipt is not None
    assert compile_run.current_source_sha256(build, receipt) == receipt["source_tex_sha256"]

    source.write_text("edited after the compile", encoding="utf-8")

    assert compile_run.current_source_sha256(build, receipt) != receipt["source_tex_sha256"]


def test_compile_exports_the_run_id_before_the_detectors_run() -> None:
    """The checkers can only record the run id if compile.sh exports it first."""
    script = (REPO_ROOT / "scripts" / "compile.sh").read_text(encoding="utf-8")

    export = f'export {compile_run.RUN_ID_ENV}="$COMPILE_RUN_ID"'
    assert export in script
    for checker in (
        "check_silhouette_morphology.py",
        "check_text_boundary_clash.py",
        "check_label_path_proximity.py",
        "strict_status.py",
        "render_input_manifest.py",
    ):
        assert script.index(export) < script.index(checker), checker
