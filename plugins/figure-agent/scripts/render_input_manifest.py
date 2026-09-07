"""Bind a compiled PDF to the content bytes that produced it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import compile_run

SCHEMA = "figure-agent.render-input-manifest.v2"
FRESH = "FRESH"
MISSING = "MISSING"
INVALID = "INVALID"
STALE = "STALE"
UNBOUND = "UNBOUND"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_path(render_pdf: Path) -> Path:
    return render_pdf.with_name(f"{render_pdf.stem}_render_inputs.json")


def input_paths(example_dir: Path, name: str, style_lock: Path) -> dict[str, Path]:
    from style_contract import resolve_style

    style_lock, _ = resolve_style(example_dir, style_lock)
    candidates = {
        "source_tex": example_dir / f"{name}.tex",
        "briefing": example_dir / "briefing.md",
        "spec": example_dir / "spec.yaml",
        "claim_authority": example_dir / "claim_authority.yaml",
        "style_lock": style_lock,
    }
    return {role: path for role, path in candidates.items() if path.is_file()}


def recorder_inputs(recorder: Path, source_dir: Path, build_dir: Path) -> dict[str, Path]:
    """Read TeX's actual input set; auxiliary outputs are not authored dependencies."""
    paths = {}
    for line in recorder.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("INPUT "):
            continue
        path = Path(line[6:])
        path = (source_dir / path).resolve() if not path.is_absolute() else path.resolve()
        if path.is_relative_to(build_dir.resolve()) and path.suffix not in {".tex", ".sty"}:
            continue
        if not path.is_file():
            raise ValueError(f"recorded TeX input is missing: {path}")
        paths[str(path)] = path
    if not paths:
        raise ValueError("TeX recorder contains no input files")
    return paths


def build_manifest(
    *,
    fixture: str,
    render_pdf: Path,
    inputs: Mapping[str, Path],
    compile_run_id: str,
    recorder: Path | None = None,
    engine: Path | None = None,
) -> dict[str, object]:
    source_dir = inputs["source_tex"].parent.resolve()
    dependencies = {}
    toolchain = {}
    if recorder is not None:
        bound = {path.resolve() for path in inputs.values()}
        for path in recorder_inputs(recorder, source_dir, render_pdf.parent).values():
            if path in bound:
                continue
            if path.is_relative_to(source_dir):
                dependencies[str(path.relative_to(source_dir))] = _sha256(path)
            else:
                toolchain[str(path)] = _sha256(path)
    if engine is not None:
        toolchain[str(engine.resolve())] = _sha256(engine.resolve())
    payload = {
        "schema": SCHEMA,
        "fixture": fixture,
        "compile_run_id": compile_run_id,
        "render": {
            "path": f"build/{render_pdf.name}",
            "sha256": _sha256(render_pdf),
        },
        "inputs": {role: {"sha256": _sha256(path)} for role, path in sorted(inputs.items())},
        "dependencies": dependencies,
        "toolchain": toolchain,
    }
    png = render_pdf.with_suffix(".png")
    if png.is_file():
        payload["raster"] = {"path": f"build/{png.name}", "sha256": _sha256(png)}
    return payload


def write_manifest(
    *,
    fixture: str,
    render_pdf: Path,
    inputs: Mapping[str, Path],
    output: Path,
    compile_run_id: str,
    recorder: Path | None = None,
    engine: Path | None = None,
) -> None:
    payload = build_manifest(
        fixture=fixture,
        render_pdf=render_pdf,
        inputs=inputs,
        compile_run_id=compile_run_id,
        recorder=recorder,
        engine=engine,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def freshness(*, manifest: Path, fixture: str, render_pdf: Path, inputs: Mapping[str, Path]) -> str:
    if not manifest.is_file():
        return MISSING
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return INVALID
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return INVALID
    if payload.get("fixture") != fixture:
        return INVALID
    render = payload.get("render")
    if not isinstance(render, dict):
        return INVALID
    if render.get("path") != f"build/{render_pdf.name}":
        return INVALID
    if not render_pdf.is_file() or render.get("sha256") != _sha256(render_pdf):
        return STALE
    receipt = compile_run.verified_receipt(render_pdf.parent)
    if (
        receipt is None
        or payload.get("compile_run_id") != receipt.get("run_id")
        or receipt.get("render_pdf_sha256") != render.get("sha256")
    ):
        return UNBOUND
    declared_inputs = payload.get("inputs")
    if not isinstance(declared_inputs, dict) or set(declared_inputs) != set(inputs):
        return INVALID
    for role, path in inputs.items():
        declared = declared_inputs.get(role)
        if not isinstance(declared, dict) or set(declared) != {"sha256"}:
            return INVALID
        if not path.is_file() or declared.get("sha256") != _sha256(path):
            return STALE
    for field in ("dependencies", "toolchain"):
        bindings = payload.get(field)
        if not isinstance(bindings, dict):
            return INVALID
        for name, digest in bindings.items():
            if not isinstance(name, str) or not isinstance(digest, str):
                return INVALID
            path = Path(name)
            if field == "dependencies":
                if path.is_absolute() or ".." in path.parts:
                    return INVALID
                path = inputs["source_tex"].parent / path
            elif not path.is_absolute():
                return INVALID
            if not path.is_file() or _sha256(path) != digest:
                return STALE
    return FRESH


def raster_freshness(
    *,
    fixture: str,
    render_pdf: Path,
    inputs: Mapping[str, Path],
    png: Path,
) -> str:
    manifest = manifest_path(render_pdf)
    state = freshness(manifest=manifest, fixture=fixture, render_pdf=render_pdf, inputs=inputs)
    if state != FRESH:
        return state
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    raster = payload.get("raster")
    if not isinstance(raster, dict) or raster.get("path") != f"build/{png.name}":
        return UNBOUND
    if not png.is_file() or raster.get("sha256") != _sha256(png):
        return STALE
    return FRESH


def _parse_inputs(values: Sequence[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        role, separator, path = value.partition("=")
        if not separator or not role or not path or role in parsed:
            raise ValueError(f"invalid input binding: {value!r}")
        parsed[role] = Path(path).expanduser().resolve()
    if not parsed:
        raise ValueError("at least one --input binding is required")
    return parsed


def _authorized_run_id(render_pdf: Path) -> str:
    """Reject any caller that is not the compile that produced this render.

    Left open, this CLI is a public "declare these bytes fresh" command: point
    it at a stale PDF and the current sources and the manifest says FRESH with
    no LaTeX run. Only compile.sh knows the run id of a compile in progress.
    """
    run_id = os.environ.get(compile_run.RUN_ID_ENV, "")
    receipt = compile_run.load_receipt(compile_run.receipt_path(render_pdf.parent))
    if not run_id or receipt is None or receipt.get("run_id") != run_id:
        raise ValueError(
            "render input manifests are issued by compile.sh only: "
            f"{compile_run.RUN_ID_ENV} must name the run recorded in "
            f"{compile_run.RECEIPT_NAME}"
        )
    return run_id


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--recorder", type=Path)
    parser.add_argument("--engine", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        inputs = _parse_inputs(args.input)
        render_pdf = args.render.expanduser().resolve()
        write_manifest(
            fixture=args.fixture,
            render_pdf=render_pdf,
            inputs=inputs,
            output=args.json_output.expanduser().resolve(),
            compile_run_id=_authorized_run_id(render_pdf),
            recorder=args.recorder,
            engine=args.engine,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
