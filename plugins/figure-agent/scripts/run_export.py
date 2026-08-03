"""Orchestrator for /fig_export.

Reads exports/ sub-state for `<name>` and dispatches:

  MISSING / STALE  -> regenerate (PDF copy, dvisvgm SVG, pdftocairo TIFF, rsvg-convert PNG)
  FRESH            -> no-op
  TRACKED_GOLDEN   -> skip with warning. --force-golden overrides.

Usage: uv run python scripts/run_export.py <name> [--force-golden] [--skip-critique]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent
SCRIPT_IMPORT_DIRS = (
    SCRIPTS_DIR,
    SCRIPTS_DIR / "checks",
    SCRIPTS_DIR / "candidates",
    SCRIPTS_DIR / "quality",
    SCRIPTS_DIR / "loop",
    SCRIPTS_DIR / "driver",
)
for script_dir in reversed(SCRIPT_IMPORT_DIRS):
    sys.path.insert(0, str(script_dir))

import current_candidate  # noqa: E402
import fixture_identity  # noqa: E402
import runtime_paths  # noqa: E402
from check_tex_assertions import BLOCKING_STATUSES as TEX_BLOCKING_STATUSES  # noqa: E402
from check_tex_assertions import (  # noqa: E402
    TexAssertionError,
    check_tex_assertions,
    parse_tex_assertions,
)
from check_visual_clash import extract_pdf_words_and_page  # noqa: E402
from critique_lint import lint_critique  # noqa: E402
from export_freshness import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)
from reference_contract import compute_reference_input_failures  # noqa: E402
from semantic_assertions import (  # noqa: E402
    SemanticAssertionError,
    check_semantic_assertions,
)
from semantic_assertions import parse_assertions as parse_semantic_assertions  # noqa: E402
from status import (  # noqa: E402
    CRITIQUE_BRIEFING_REQUIRED,
    CRITIQUE_FRESH,
    CRITIQUE_MISSING,
    CRITIQUE_REFERENCE_MISSING,
    CRITIQUE_STALE,
    compute_critique_state,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _regenerate(
    example_dir: Path,
    name: str,
    *,
    build_pdf: Path | None = None,
    plugin_root: Path | None = None,
) -> None:
    plugin_root = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root or REPO_ROOT
    ).plugin_root
    build_pdf = build_pdf or example_dir / "build" / f"{name}.pdf"
    exports_dir = example_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    exports_pdf = exports_dir / f"{name}.pdf"
    exports_svg = exports_dir / f"{name}.svg"
    exports_png = exports_dir / f"{name}.png"
    exports_tif_stem = str(exports_dir / name)

    subprocess.run(
        ["bash", "scripts/export_svg.sh", str(build_pdf), str(exports_svg)],
        cwd=plugin_root,
        check=True,
    )
    subprocess.run(
        ["pdftocairo", "-tiff", "-r", "600", "-singlefile", str(build_pdf), exports_tif_stem],
        cwd=plugin_root,
        check=True,
    )
    subprocess.run(
        ["bash", "scripts/svg_to_png.sh", str(exports_svg), str(exports_png)],
        cwd=plugin_root,
        check=True,
    )
    shutil.copy(build_pdf, exports_pdf)


def _load_spec(spec_path: Path) -> dict:
    if not spec_path.is_file():
        return {}
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _export_inputs(example_dir: Path, name: str) -> tuple[Path, Path]:
    """Resolve the source/render pair status already treats as current.

    An explicit current-candidate pointer is evidence selection, not promotion:
    exports remain draft artifacts under the fixture root and acceptance stays
    human-gated. Invalid or incomplete pointers fail closed instead of silently
    exporting a different root source.
    """

    candidate = current_candidate.resolve_current_candidate(example_dir)
    if candidate.get("state") == "NOT_DECLARED":
        return (
            example_dir / f"{name}.tex",
            example_dir / "build" / f"{name}.pdf",
        )
    if candidate.get("state") != "VALID":
        raise ValueError(
            "current candidate is invalid: " + str(candidate.get("reason") or "unknown")
        )
    evidence_paths = candidate.get("evidence_paths")
    render_relative = (
        evidence_paths.get("render_pdf") if isinstance(evidence_paths, dict) else None
    )
    source_relative = candidate.get("source_path")
    if not isinstance(source_relative, str) or not isinstance(render_relative, str):
        raise ValueError("current candidate source/render evidence is incomplete")
    source_path = (example_dir / source_relative).resolve()
    build_pdf = (example_dir / render_relative).resolve()
    if candidate.get("render_state") != "FRESH":
        raise ValueError(
            "current candidate render is not fresh: "
            + str(candidate.get("render_state") or "unknown")
        )
    return source_path, build_pdf


def _live_tex_blockers(
    example_dir: Path, name: str, tex_path: Path | None = None
) -> list[dict]:
    """Re-run the tex-assertion check against the current source at export time.

    Never reads build/tex_assertions.json: it is gitignored (absent on a fresh
    checkout) and goes stale when .tex is edited without recompiling, so trusting
    it fails open on the reversed-arrow physics this gate exists to catch.
    """
    tex_path = tex_path or example_dir / f"{name}.tex"
    assertions = parse_tex_assertions(
        _load_spec(example_dir / "spec.yaml"), source_name=tex_path.name
    )
    if not assertions:
        return []
    if not tex_path.is_file():
        return [
            {
                "id": assertions[0]["id"],
                "status": "anchor_missing",
                "message": f"{tex_path} missing; cannot verify declared tex_assertions",
            }
        ]
    issues = check_tex_assertions(tex_path.read_text(encoding="utf-8"), assertions)
    return [issue for issue in issues if issue["status"] in TEX_BLOCKING_STATUSES]


def _live_semantic_blockers(
    example_dir: Path, name: str, pdf_path: Path | None = None
) -> list[dict]:
    """Re-run the semantic-assertion check against the current render at export time."""
    assertions = parse_semantic_assertions(_load_spec(example_dir / "spec.yaml"))
    if not assertions:
        return []
    pdf_path = pdf_path or example_dir / "build" / f"{name}.pdf"
    if not pdf_path.is_file():
        return [
            {
                "id": assertions[0]["id"],
                "status": "anchor_missing",
                "message": f"{pdf_path} missing; cannot verify declared semantic_assertions",
            }
        ]
    words, _ = extract_pdf_words_and_page(pdf_path)
    issues = check_semantic_assertions(words, assertions)
    return [issue for issue in issues if issue["status"] != "indeterminate"]


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
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
    args = parser.parse_args(argv)
    if (
        plugin_root is None
        and workspace_root is None
        and "FIGURE_AGENT_WORKSPACE" not in os.environ
        and "CLAUDE_PROJECT_DIR" not in os.environ
    ):
        paths = runtime_paths.resolve_runtime_paths(plugin_root=REPO_ROOT, workspace_root=REPO_ROOT)
    else:
        paths = runtime_paths.resolve_runtime_paths(
            plugin_root=plugin_root,
            workspace_root=workspace_root,
        )

    try:
        fixture_identity.validate_fixture_name(args.name)
    except ValueError as exc:
        print(f"run_export.py: {exc}", file=sys.stderr)
        return 1

    example_dir = paths.examples_dir / args.name
    if not example_dir.is_dir():
        print(f"run_export.py: examples/{args.name}/ not found", file=sys.stderr)
        return 1

    try:
        tex_path, build_pdf = _export_inputs(example_dir, args.name)
    except ValueError as exc:
        print(f"run_export.py: {exc}; run /fig_status and /fig_compile first", file=sys.stderr)
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
        if critique_state in {CRITIQUE_BRIEFING_REQUIRED, CRITIQUE_MISSING, CRITIQUE_STALE}:
            note = "critique_stale" if critique_state == CRITIQUE_STALE else "critique_missing"
            print(
                f"run_export.py: {note} for {args.name}; run /fig_critique {args.name} "
                "before /fig_export, or pass --skip-critique to override.",
                file=sys.stderr,
            )
            return 1
        if critique_state == CRITIQUE_FRESH:
            critique_violations = lint_critique(example_dir)
            if critique_violations:
                first_violation = critique_violations[0]
                print(
                    "run_export.py: critique_invalid for "
                    f"{args.name}: {first_violation.category}: {first_violation.message}; "
                    "fix critique.md or pass --skip-critique to override.",
                    file=sys.stderr,
                )
                return 1

    # Physics gate (not bypassed by --skip-critique): a violated/unverified
    # assertion is wrong or unchecked physics — no render detector catches a
    # reversed force/bend (tex_assertions) or a reversed above/left-of relation
    # (semantic_assertions), so a figure must not export with one open. The checks
    # re-run live against the current source/render here; a cached build/*.json is
    # never trusted (gitignored => absent on fresh checkout; stale after a .tex edit
    # without recompile). Malformed assertions or an unreadable render fail closed.
    for label, compute in (
        ("tex_assertions", lambda: _live_tex_blockers(example_dir, args.name, tex_path)),
        (
            "semantic_assertions",
            lambda: _live_semantic_blockers(example_dir, args.name, build_pdf),
        ),
    ):
        try:
            blockers = compute()
        except (TexAssertionError, SemanticAssertionError) as exc:
            print(
                f"run_export.py: {label}_invalid for {args.name}: {exc}; "
                "fix the declared assertion before /fig_export.",
                file=sys.stderr,
            )
            return 1
        except RuntimeError as exc:
            print(
                f"run_export.py: {label}_unverifiable for {args.name}: {exc}; "
                "cannot read the render to verify physics before /fig_export.",
                file=sys.stderr,
            )
            return 1
        if blockers:
            first = blockers[0]
            print(
                f"run_export.py: {label}_unverified for {args.name}: "
                f"{first.get('id')} {first.get('status')}: {first.get('message')}; "
                "fix the figure's physics (or the assertion) before /fig_export.",
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
    if not build_pdf.is_file():
        print(
            f"run_export.py: {build_pdf} not found; run /fig_compile first",
            file=sys.stderr,
        )
        return 1

    root_build_pdf = example_dir / "build" / f"{args.name}.pdf"
    if build_pdf == root_build_pdf:
        _regenerate(example_dir, args.name, plugin_root=paths.plugin_root)
    else:
        _regenerate(
            example_dir,
            args.name,
            build_pdf=build_pdf,
            plugin_root=paths.plugin_root,
        )
    print(f"run_export.py: regenerated exports/ for {args.name} (was {state})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
