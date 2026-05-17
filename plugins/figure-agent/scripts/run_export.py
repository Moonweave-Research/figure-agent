"""Orchestrator for /fig_export.

Reads exports/ sub-state for `<name>` and dispatches:

  MISSING / STALE  -> regenerate (PDF copy, dvisvgm SVG, pdftocairo TIFF, rsvg-convert PNG)
  FRESH            -> no-op
  TRACKED_GOLDEN   -> skip with warning. --force-golden overrides.

Usage: uv run python scripts/run_export.py <name> [--force-golden] [--skip-critique]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_freshness import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)
from reference_contract import compute_reference_input_failures  # noqa: E402
from status import (  # noqa: E402
    CRITIQUE_MISSING,
    CRITIQUE_REFERENCE_MISSING,
    CRITIQUE_STALE,
    compute_critique_state,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _regenerate(example_dir: Path, name: str) -> None:
    build_pdf = example_dir / "build" / f"{name}.pdf"
    exports_dir = example_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    exports_pdf = exports_dir / f"{name}.pdf"
    exports_svg = exports_dir / f"{name}.svg"
    exports_png = exports_dir / f"{name}.png"
    exports_tif_stem = str(exports_dir / name)

    subprocess.run(
        ["bash", "scripts/export_svg.sh", str(build_pdf), str(exports_svg)],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(
        ["pdftocairo", "-tiff", "-r", "600", "-singlefile", str(build_pdf), exports_tif_stem],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(
        ["bash", "scripts/svg_to_png.sh", str(exports_svg), str(exports_png)],
        cwd=REPO_ROOT,
        check=True,
    )
    shutil.copy(build_pdf, exports_pdf)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument(
        "--force-golden", action="store_true", help="override TRACKED_GOLDEN protection"
    )
    parser.add_argument(
        "--skip-critique",
        action="store_true",
        help="export even when reference-grounded critique is missing or stale",
    )
    args = parser.parse_args()

    example_dir = REPO_ROOT / "examples" / args.name
    if not example_dir.is_dir():
        print(f"run_export.py: examples/{args.name}/ not found", file=sys.stderr)
        return 1

    try:
        critique_state = compute_critique_state(example_dir, args.name)
    except ValueError as exc:
        print(f"run_export.py: invalid spec.yaml: {exc}", file=sys.stderr)
        return 1
    if critique_state == CRITIQUE_REFERENCE_MISSING:
        failures = "; ".join(compute_reference_input_failures(example_dir))
        print(
            f"run_export.py: {failures}; fix declared reference inputs before /fig_export.",
            file=sys.stderr,
        )
        return 1

    if not args.skip_critique:
        if critique_state in {CRITIQUE_MISSING, CRITIQUE_STALE}:
            note = "critique_missing" if critique_state == CRITIQUE_MISSING else "critique_stale"
            print(
                f"run_export.py: {note} for {args.name}; run /fig_critique {args.name} "
                "before /fig_export, or pass --skip-critique to override.",
                file=sys.stderr,
            )
            return 1

    state = compute_export_state(example_dir, args.name)

    if state == EXPORT_FRESH:
        print(f"run_export.py: exports/ already FRESH for {args.name}; no-op")
        return 0

    if state == EXPORT_TRACKED_GOLDEN and not args.force_golden:
        print(
            f"run_export.py: exports/ for {args.name} is TRACKED_GOLDEN; "
            f"use --force-golden to overwrite",
            file=sys.stderr,
        )
        return 0  # not an error — golden protection is the success path

    # Regenerate path requires build/PDF.
    build_pdf = example_dir / "build" / f"{args.name}.pdf"
    if not build_pdf.is_file():
        print(
            f"run_export.py: build/{args.name}.pdf not found; run /fig_compile first",
            file=sys.stderr,
        )
        return 1

    _regenerate(example_dir, args.name)
    print(f"run_export.py: regenerated exports/ for {args.name} (was {state})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
