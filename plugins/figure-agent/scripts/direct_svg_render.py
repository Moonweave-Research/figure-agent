"""Canonical deterministic CLI for semantic direct-SVG candidate rendering."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import PIL
from direct_svg_candidate import (
    DirectSvgCandidateError,
    render_candidate,
    semantic_requirements,
    validate_candidate,
    validate_candidate_from_semantic_packet,
)


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


BASE_COMMIT = "064a3cc62671ef0f086efb03f26c00d97bb783cd"


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
    return {"executable": "rsvg-convert", "version": version}


def _resolve_under_root(root: Path, value: str, *, field: str) -> tuple[Path, str]:
    """Resolve one POSIX-relative receipt path without allowing root escape."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise DirectSvgCandidateError(f"{field}_path_invalid")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or value != relative.as_posix():
        raise DirectSvgCandidateError(f"{field}_path_invalid")
    base = root.resolve()
    resolved = (base / Path(*relative.parts)).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise DirectSvgCandidateError(f"{field}_path_invalid") from exc
    return resolved, relative.as_posix()


def render_with_receipt(
    *,
    root: Path,
    svg_path: str,
    output_path: str,
    semantic_packet: str,
    panel: str,
    width: int,
    height: int,
    fontconfig_file: str,
    font_file: str,
    validation_mode: str = "declared_relation_coverage",
) -> dict[str, Any]:
    """Validate, render twice, normalize RGB output, and report the runtime."""
    resolved_svg, svg_receipt = _resolve_under_root(root, svg_path, field="svg")
    resolved_output, output_receipt = _resolve_under_root(root, output_path, field="output")
    resolved_packet, packet_receipt = _resolve_under_root(
        root, semantic_packet, field="semantic_packet"
    )
    resolved_fontconfig, fontconfig_receipt = _resolve_under_root(
        root, fontconfig_file, field="fontconfig"
    )
    resolved_font, font_receipt = _resolve_under_root(root, font_file, field="font")
    wrapper, wrapper_receipt = _resolve_under_root(
        root, "scripts/direct_svg_render.py", field="wrapper"
    )
    validator, validator_receipt = _resolve_under_root(
        root, "scripts/direct_svg_candidate.py", field="validator"
    )
    lock, lock_receipt = _resolve_under_root(root, "uv.lock", field="lock")
    if validation_mode == "declared_relation_coverage":
        validate_candidate_from_semantic_packet(
            resolved_svg,
            resolved_packet,
            panel=panel,
        )
    elif validation_mode == "historical_structure_replay":
        requirements = semantic_requirements(resolved_packet, panel=panel)
        validate_candidate(
            resolved_svg,
            required_ids=requirements["required_ids"],
            required_text=requirements["required_text"],
        )
    else:
        raise DirectSvgCandidateError("validation_mode_invalid")
    rendered = render_candidate(
        resolved_svg,
        resolved_output,
        width=width,
        height=height,
        fontconfig_file=resolved_fontconfig,
    )

    return {
        "schema": "figure-agent.direct-svg-runtime-receipt.v1",
        "path_base": "plugin_root",
        "validation_mode": validation_mode,
        "source_path": svg_receipt,
        "source_sha256": rendered["source_sha256"],
        "render_path": output_receipt,
        "render_sha256": rendered["render_sha256"],
        "semantic_packet": {"path": packet_receipt, "sha256": _sha256(resolved_packet)},
        "fontconfig": {
            "path": fontconfig_receipt,
            "sha256": _sha256(resolved_fontconfig),
        },
        "font": {
            "path": font_receipt,
            "sha256": _sha256(resolved_font),
        },
        "rsvg": _rsvg_receipt(),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "pillow": {"version": PIL.__version__},
        "environment": {
            "FONTCONFIG_FILE": fontconfig_receipt,
            "FONTCONFIG_PATH": PurePosixPath(fontconfig_receipt).parent.as_posix(),
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
        },
        "producer": {
            "wrapper_path": wrapper_receipt,
            "wrapper_sha256": _sha256(wrapper),
            "validator_path": validator_receipt,
            "validator_sha256": _sha256(validator),
            "lock_path": lock_receipt,
            "lock_sha256": _sha256(lock),
            "base_commit": BASE_COMMIT,
            "head_commit": "unavailable_precommit",
            "head_commit_status": "unavailable_precommit",
        },
        "width": width,
        "height": height,
        "publication_acceptance": "not_claimed",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--svg", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--semantic-packet", required=True)
    parser.add_argument("--panel", choices=("C", "F"), required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--fontconfig", required=True)
    parser.add_argument("--font", required=True)
    parser.add_argument(
        "--validation-mode",
        choices=("declared_relation_coverage", "historical_structure_replay"),
        default="declared_relation_coverage",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    receipt = render_with_receipt(
        root=args.root,
        svg_path=args.svg,
        output_path=args.output,
        semantic_packet=args.semantic_packet,
        panel=args.panel,
        width=args.width,
        height=args.height,
        fontconfig_file=args.fontconfig,
        font_file=args.font,
        validation_mode=args.validation_mode,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
