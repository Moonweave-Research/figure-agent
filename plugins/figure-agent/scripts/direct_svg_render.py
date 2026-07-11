"""Canonical deterministic CLI for semantic direct-SVG candidate rendering."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

import PIL
from direct_svg_candidate import (
    DirectSvgCandidateError,
    render_candidate,
    validate_candidate_from_semantic_packet,
)


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _rsvg_receipt() -> dict[str, str]:
    executable = shutil.which("rsvg-convert")
    if executable is None:
        raise DirectSvgCandidateError("rsvg_convert_missing")
    try:
        version = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise DirectSvgCandidateError("rsvg_version_failed") from exc
    return {"executable": executable, "version": version}


def render_with_receipt(
    *,
    svg_path: Path,
    output_path: Path,
    semantic_packet: Path,
    panel: str,
    width: int,
    height: int,
    fontconfig_file: Path,
    font_file: Path,
    receipt_base: Path,
) -> dict[str, Any]:
    """Validate, render twice, normalize RGB output, and report the runtime."""
    validate_candidate_from_semantic_packet(
        svg_path,
        semantic_packet,
        panel=panel,
    )
    rendered = render_candidate(
        svg_path,
        output_path,
        width=width,
        height=height,
        fontconfig_file=fontconfig_file,
    )
    base = receipt_base.resolve()

    def receipt_path(path: Path) -> str:
        resolved = path.resolve()
        try:
            return str(resolved.relative_to(base))
        except ValueError:
            return str(resolved)

    return {
        "schema": "figure-agent.direct-svg-runtime-receipt.v1",
        "source_sha256": rendered["source_sha256"],
        "render_sha256": rendered["render_sha256"],
        "semantic_packet_sha256": _sha256(semantic_packet),
        "fontconfig": {
            "path": receipt_path(fontconfig_file),
            "sha256": _sha256(fontconfig_file),
        },
        "font": {
            "path": receipt_path(font_file),
            "sha256": _sha256(font_file),
        },
        "rsvg": _rsvg_receipt(),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "pillow": {"version": PIL.__version__},
        "environment": {
            "FONTCONFIG_FILE": str(fontconfig_file.resolve()),
            "FONTCONFIG_PATH": str(fontconfig_file.parent.resolve()),
            "LANG": os.environ.get("LANG"),
            "LC_ALL": os.environ.get("LC_ALL"),
        },
        "width": width,
        "height": height,
        "publication_acceptance": "not_claimed",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--semantic-packet", type=Path, required=True)
    parser.add_argument("--panel", choices=("C", "F"), required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--fontconfig", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--receipt-base", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = _parser().parse_args()
    receipt = render_with_receipt(
        svg_path=args.svg,
        output_path=args.output,
        semantic_packet=args.semantic_packet,
        panel=args.panel,
        width=args.width,
        height=args.height,
        fontconfig_file=args.fontconfig,
        font_file=args.font,
        receipt_base=args.receipt_base,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
