"""Bind a compiled PDF to the content bytes that produced it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

SCHEMA = "figure-agent.render-input-manifest.v1"
FRESH = "FRESH"
MISSING = "MISSING"
INVALID = "INVALID"
STALE = "STALE"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_path(render_pdf: Path) -> Path:
    return render_pdf.with_name(f"{render_pdf.stem}_render_inputs.json")


def build_manifest(
    *, fixture: str, render_pdf: Path, inputs: Mapping[str, Path]
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "render": {
            "path": f"build/{render_pdf.name}",
            "sha256": _sha256(render_pdf),
        },
        "inputs": {
            role: {"sha256": _sha256(path)}
            for role, path in sorted(inputs.items())
        },
    }


def write_manifest(
    *, fixture: str, render_pdf: Path, inputs: Mapping[str, Path], output: Path
) -> None:
    payload = build_manifest(fixture=fixture, render_pdf=render_pdf, inputs=inputs)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def freshness(
    *, manifest: Path, fixture: str, render_pdf: Path, inputs: Mapping[str, Path]
) -> str:
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
    declared_inputs = payload.get("inputs")
    if not isinstance(declared_inputs, dict) or set(declared_inputs) != set(inputs):
        return INVALID
    for role, path in inputs.items():
        declared = declared_inputs.get(role)
        if not isinstance(declared, dict) or set(declared) != {"sha256"}:
            return INVALID
        if not path.is_file() or declared.get("sha256") != _sha256(path):
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--input", action="append", default=[])
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
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
