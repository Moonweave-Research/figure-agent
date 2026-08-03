"""Freshness state for SVG-first figure folders."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SOURCE_MISSING = "SOURCE_MISSING"
EXPORT_MISSING = "EXPORT_MISSING"
EXPORT_PARTIAL = "EXPORT_PARTIAL"
EXPORT_STALE = "EXPORT_STALE"
EXPORT_FRESH = "EXPORT_FRESH"

REQUIRED_EXPORT_EXTS = (".pdf", ".png", ".tif")


def _source_path(figure_dir: Path, name: str) -> Path:
    return figure_dir / "source" / f"{name}.svg"


def _export_paths(figure_dir: Path, name: str) -> tuple[Path, ...]:
    return tuple(figure_dir / "exports" / f"{name}{ext}" for ext in REQUIRED_EXPORT_EXTS)


def _input_paths(figure_dir: Path, name: str) -> tuple[Path, ...]:
    candidates = [
        _source_path(figure_dir, name),
        figure_dir / "spec.yaml",
        figure_dir / "underlay" / f"{name}.underlay.svg",
    ]
    return tuple(path for path in candidates if path.exists())


def compute_export_state(figure_dir: Path, name: str) -> str:
    """Return source/export freshness for SVG-first artifact outputs."""
    source = _source_path(figure_dir, name)
    if not source.is_file():
        return SOURCE_MISSING

    exports = _export_paths(figure_dir, name)
    existing = [path for path in exports if path.is_file()]
    if not existing:
        return EXPORT_MISSING
    if len(existing) != len(exports):
        return EXPORT_PARTIAL

    newest_input = max(path.stat().st_mtime for path in _input_paths(figure_dir, name))
    oldest_export = min(path.stat().st_mtime for path in exports)
    if newest_input > oldest_export:
        return EXPORT_STALE
    return EXPORT_FRESH


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SVG-first figure freshness.")
    parser.add_argument("name")
    parser.add_argument("--examples-root", type=Path, default=Path("examples"))
    args = parser.parse_args()
    state = compute_export_state(args.examples_root / args.name, args.name)
    print(f"{args.name}: {state}")
    return 1 if state in {SOURCE_MISSING, EXPORT_STALE} else 0


if __name__ == "__main__":
    sys.exit(main())
