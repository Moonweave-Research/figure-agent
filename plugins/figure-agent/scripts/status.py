"""Infer figure-pipeline stage from filesystem + spec.yaml only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_freshness import EXPORT_STALE, EXPORT_TRACKED_GOLDEN, compute_export_state
from inputs import parse_spec

# Shared build/export freshness source set. /fig_critique adds panel references
# for crop/reference comparisons, but status should not require a rebuild for
# critique-only panel-reference edits.
STYLE_LOCK_PATH = Path(__file__).resolve().parent.parent / "styles" / "polymer-paper-preamble.sty"

_NEXT_0 = "run /fig_new <name> to create the figure scaffold."
_NEXT_1 = (
    "author examples/<name>/<name>.tex from briefing.md"
    " (cp styles/tex_template.tex to start), then /fig_compile <name>."
)
_NEXT_2 = "run /fig_compile <name> to compile the TikZ source."
# Stage 3: prefer /fig_export unless reference grounding makes critique required.
_NEXT_3 = "run /fig_critique <name> for vision review (optional), then /fig_export <name>."
_NEXT_3_CRITIQUE_REQUIRED = (
    "run /fig_critique <name> before /fig_export <name>"
    " because reference-grounded critique is missing or stale."
)
_NEXT_4 = (
    "done — outputs in examples/<name>/exports/."
    " To revise, edit <name>.tex and re-run /fig_compile then /fig_export."
)
_NEXT_4_STALE = "exports are stale — re-run /fig_compile <name> then /fig_export <name>."
_NEXT_4_EXPORT_STALE = "exports are stale or incomplete — re-run /fig_export <name>."
_NEXT_4_TRACKED_STALE = (
    "tracked golden artifact is intentionally stale;"
    " to roll forward run /fig_export <name> --force-golden."
)
_NEXT_4_TRACKED_PARTIAL = (
    "tracked golden exports are incomplete;"
    " to roll forward missing artifacts run /fig_export <name> --force-golden."
)
_NEXT_4_PARTIAL = (
    "exports are incomplete — re-run /fig_export <name> to generate the"
    " missing PDF/SVG/TIFF/PNG artifacts."
)
_NEXT_4_NOT_ACCEPTED = (
    "golden fixture is not accepted yet — resolve examples/<name>/QUALITY_AUDIT.md"
    " defects, then set accepted: true in spec.yaml."
)
_NEXT_4_CRITIQUE_REQUIRED = (
    "run /fig_critique <name> before treating exports as final;"
    " if no edits are needed, existing exports can remain in place."
)
_NEXT_MISSING_BRIEFING = "complete examples/<name>/briefing.md before continuing."

_EXPORT_EXTS = (".pdf", ".svg", ".tif", ".tiff", ".png")
CRITIQUE_NOT_REQUIRED = "NOT_REQUIRED"
CRITIQUE_MISSING = "MISSING"
CRITIQUE_STALE = "STALE"
CRITIQUE_FRESH = "FRESH"


def _has_export_artifact(directory: Path, name: str) -> bool:
    for ext in _EXPORT_EXTS:
        if (directory / f"{name}{ext}").exists():
            return True
    return False


def _all_four_exports_present(exports_dir: Path, name: str) -> bool:
    has_pdf = (exports_dir / f"{name}.pdf").exists()
    has_svg = (exports_dir / f"{name}.svg").exists()
    has_tif = (exports_dir / f"{name}.tif").exists() or (exports_dir / f"{name}.tiff").exists()
    has_png = (exports_dir / f"{name}.png").exists()
    return has_pdf and has_svg and has_tif and has_png


def _source_paths(example_dir: Path, name: str, spec: dict) -> tuple[Path, ...]:
    """Sources that should be older than any compiled/exported artifact."""
    candidates: list[Path] = [
        example_dir / f"{name}.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ]
    ref_image_str = spec.get("reference_image")
    if ref_image_str:
        ref_path = example_dir / ref_image_str
        if ref_path.is_file():
            candidates.append(ref_path)
    hints_path = example_dir / "coordinate_hints.yaml"
    if hints_path.exists():
        candidates.append(hints_path)
    candidates.append(STYLE_LOCK_PATH)
    return tuple(path for path in candidates if path.exists())


def _panel_reference_paths(example_dir: Path, spec: dict) -> tuple[Path, ...]:
    paths: list[Path] = []
    for panel in spec.get("panels", []):
        if panel.get("bbox_pdf_cm") is None:
            continue
        reference = panel.get("reference_image")
        if not isinstance(reference, str) or not reference.strip():
            continue
        ref_path = example_dir / reference.strip()
        if ref_path.is_file():
            paths.append(ref_path)
    return tuple(paths)


def _critique_source_paths(example_dir: Path, name: str, spec: dict) -> tuple[Path, ...]:
    paths = list(_source_paths(example_dir, name, spec))
    paths.extend(_panel_reference_paths(example_dir, spec))
    return tuple(dict.fromkeys(paths))


def compute_critique_state(example_dir: Path, name: str, spec: dict | None = None) -> str:
    """Return NOT_REQUIRED/MISSING/STALE/FRESH for reference-grounded critique."""
    spec_path = example_dir / "spec.yaml"
    if spec is None:
        if not spec_path.exists():
            return CRITIQUE_NOT_REQUIRED
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))

    has_figure_reference = False
    reference_image = spec.get("reference_image") if spec else None
    if isinstance(reference_image, str) and reference_image.strip():
        has_figure_reference = (example_dir / reference_image.strip()).is_file()
    has_panel_reference = bool(_panel_reference_paths(example_dir, spec))
    if not has_figure_reference and not has_panel_reference:
        return CRITIQUE_NOT_REQUIRED

    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return CRITIQUE_MISSING
    if _is_stale(_critique_source_paths(example_dir, name, spec), (critique_path,)):
        return CRITIQUE_STALE
    return CRITIQUE_FRESH


def _critique_needs_action(state: str) -> bool:
    return state in {CRITIQUE_MISSING, CRITIQUE_STALE}


def _append_critique_check(
    checks: list[tuple[str, str]], notes: list[str], critique_state: str
) -> None:
    if critique_state == CRITIQUE_NOT_REQUIRED:
        return
    checks.append(("critique", critique_state.lower()))
    if critique_state == CRITIQUE_MISSING:
        notes.append("critique_missing")
    elif critique_state == CRITIQUE_STALE:
        notes.append("critique_stale")


def _is_stale(sources: tuple[Path, ...], targets: tuple[Path, ...]) -> bool:
    """True if any source file is newer than the oldest target file."""
    target_mtimes = [path.stat().st_mtime for path in targets if path.exists()]
    if not target_mtimes:
        return False
    oldest_target = min(target_mtimes)
    for source in sources:
        if source.stat().st_mtime > oldest_target:
            return True
    return False


def _existing_export_paths(exports_dir: Path, name: str) -> tuple[Path, ...]:
    found = []
    for ext in _EXPORT_EXTS:
        path = exports_dir / f"{name}{ext}"
        if path.exists():
            found.append(path)
    return tuple(found)


def _append_prerequisite_notes(
    notes: list[str], spec: dict, previews_dir: Path, briefing_path: Path
) -> None:
    if not briefing_path.exists():
        notes.append("missing_briefing")

    previews_corrupted = previews_dir.exists() and not previews_dir.is_dir()
    if previews_corrupted:
        notes.append("previews_not_directory")


def _resolve_accepted(spec: dict) -> bool | None:
    """Return literal bool from spec['accepted']; coerce other shapes to None."""
    value = spec.get("accepted") if spec else None
    if value is True or value is False:
        return value
    return None


def _accepted_marker(accepted: bool | None) -> str:
    if accepted is True:
        return " (accepted)"
    if accepted is False:
        return " (not accepted)"
    return ""


def _append_reference_image_check(
    checks: list[tuple[str, str]], notes: list[str], spec: dict, example_dir: Path
) -> None:
    reference_image = spec.get("reference_image") if spec else None
    if not reference_image or not isinstance(reference_image, str) or not reference_image.strip():
        return

    reference_image = reference_image.strip()
    checks.append(("reference_image", reference_image))
    reference_path = example_dir / reference_image
    if not reference_path.is_file():
        notes.append("reference_image_missing")
        return

    # Layer 2.5: coordinate_hints.yaml is auto-detected by file presence.
    # Surface missing/stale/parse-error states as notes so the user knows
    # to run /fig_extract; we never block the stage advance on it because
    # Layer 2.5 is optional.
    hints_path = example_dir / "coordinate_hints.yaml"
    if not hints_path.exists():
        notes.append("coordinate_hints_missing")
        return
    checks.append(("coordinate_hints", "present"))
    try:
        import yaml as _yaml

        hints_data = _yaml.safe_load(hints_path.read_text(encoding="utf-8")) or {}
    except Exception:
        notes.append("coordinate_hints_parse_error")
        return
    if hints_path.stat().st_mtime < reference_path.stat().st_mtime:
        notes.append("coordinate_hints_stale")
    from reference_extract import EXTRACTION_VERSION as _EXTRACTION_VERSION  # noqa: PLC0415

    hints_version = (hints_data.get("metadata") or {}).get("extraction_version")
    if hints_version != _EXTRACTION_VERSION:
        notes.append("coordinate_hints_outdated")


def _append_panel_reference_checks(notes: list[str], spec: dict, example_dir: Path) -> None:
    for panel in spec.get("panels", []):
        if panel.get("bbox_pdf_cm") is None:
            continue
        reference = panel.get("reference_image")
        if not isinstance(reference, str) or not reference.strip():
            continue
        if not (example_dir / reference.strip()).is_file():
            notes.append("panel_reference_image_missing")
            return  # one note is enough; caller can see spec.yaml for details


def infer_stage(example_dir: Path) -> dict:
    name = example_dir.name
    exports_substate = compute_export_state(example_dir, name)
    if not example_dir.exists() or not example_dir.is_dir():
        return {
            "stage": 0,
            "name": name,
            "checks": [],
            "next": _NEXT_0.replace("<name>", name),
            "notes": [],
            "accepted": None,
            "exports_substate": exports_substate,
        }

    spec_path = example_dir / "spec.yaml"
    tex_path = example_dir / f"{name}.tex"
    briefing_path = example_dir / "briefing.md"
    build_pdf = example_dir / "build" / f"{name}.pdf"
    previews_dir = example_dir / "previews"
    exports_dir = example_dir / "exports"

    checks: list[tuple[str, str]] = []
    notes: list[str] = []

    spec: dict = {}
    if spec_path.exists():
        try:
            spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        except ValueError:
            notes.append("style_profile_unknown")
            import yaml as _yaml  # noqa: PLC0415

            raw = _yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            spec = raw if isinstance(raw, dict) else {}

    accepted = _resolve_accepted(spec)
    sources = _source_paths(example_dir, name, spec)
    critique_state = compute_critique_state(example_dir, name, spec)
    _append_prerequisite_notes(notes, spec, previews_dir, briefing_path)
    _append_reference_image_check(checks, notes, spec, example_dir)
    _append_panel_reference_checks(notes, spec, example_dir)

    if spec_path.exists() and not briefing_path.exists():
        checks.append(("spec_yaml", "present"))
        checks.append(("briefing_md", "missing"))
        return {
            "stage": 1,
            "name": name,
            "checks": checks,
            "next": _NEXT_MISSING_BRIEFING.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 4: any export artifact present
    if exports_dir.exists() and _has_export_artifact(exports_dir, name):
        checks.append(("exports", "present"))
        _append_critique_check(checks, notes, critique_state)
        partial = not _all_four_exports_present(exports_dir, name)
        if partial:
            notes.append("partial_export")
        export_paths = _existing_export_paths(exports_dir, name)
        source_stale = _is_stale(sources, export_paths)
        export_content_stale = exports_substate == EXPORT_STALE
        is_stale = source_stale or export_content_stale
        if is_stale:
            notes.append("stale_export")
        # Priority: stale_export > partial_export > critique_required > not_accepted > done.
        # critique_required sits above not_accepted: you cannot meaningfully accept
        # a figure whose reference-grounded critique is missing or stale.
        # partial_export sits above both because incomplete artifacts block manuscript use.
        if is_stale and exports_substate == EXPORT_TRACKED_GOLDEN:
            next_template = _NEXT_4_TRACKED_STALE
        elif source_stale:
            next_template = _NEXT_4_STALE
        elif export_content_stale:
            next_template = _NEXT_4_EXPORT_STALE
        elif partial and exports_substate == EXPORT_TRACKED_GOLDEN:
            next_template = _NEXT_4_TRACKED_PARTIAL
        elif partial:
            next_template = _NEXT_4_PARTIAL
        elif _critique_needs_action(critique_state):
            next_template = _NEXT_4_CRITIQUE_REQUIRED
        elif accepted is False:
            next_template = _NEXT_4_NOT_ACCEPTED
        else:
            next_template = _NEXT_4
        return {
            "stage": 4,
            "name": name,
            "checks": checks,
            "next": next_template.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 3: build pdf exists, fresh against tex+briefing+style-lock, no exports
    if build_pdf.exists() and tex_path.exists() and not _is_stale(sources, (build_pdf,)):
        checks.append(("build_pdf", "fresh"))
        _append_critique_check(checks, notes, critique_state)
        next_template = (
            _NEXT_3_CRITIQUE_REQUIRED if _critique_needs_action(critique_state) else _NEXT_3
        )
        return {
            "stage": 3,
            "name": name,
            "checks": checks,
            "next": next_template.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 2: tex exists AND (no build pdf OR pdf stale relative to source set)
    if tex_path.exists():
        if not build_pdf.exists():
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "missing"))
        else:
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "stale"))
        return {
            "stage": 2,
            "name": name,
            "checks": checks,
            "next": _NEXT_2.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 1: spec.yaml exists, no .tex authored yet
    if spec_path.exists():
        checks.append(("spec_yaml", "present"))
        return {
            "stage": 1,
            "name": name,
            "checks": checks,
            "next": _NEXT_1.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 0 fallback (directory exists but no spec.yaml)
    return {
        "stage": 0,
        "name": name,
        "checks": [],
        "next": _NEXT_0.replace("<name>", name),
        "notes": [],
        "accepted": accepted,
        "exports_substate": exports_substate,
    }


def _print_single(result: dict) -> None:
    name = result["name"]
    stage = result["stage"]
    next_hint = result["next"]
    checks = result["checks"]
    notes = result["notes"]
    marker = _accepted_marker(result.get("accepted"))
    print(f"{name} — stage {stage}/4{marker}")
    for key, val in checks:
        print(f"  {key}: {val}")
    print(f"  Next: {next_hint}")
    if substate := result.get("exports_substate"):
        print(f"  Exports: {substate}")
    if notes:
        print(f"  Notes: {', '.join(notes)}")


def main() -> int:
    if len(sys.argv) == 1:
        examples_dir = Path("examples")
        if not examples_dir.is_dir():
            print("no examples/ directory found", file=sys.stderr)
            return 1
        for entry in sorted(p for p in examples_dir.iterdir() if p.is_dir()):
            result = infer_stage(entry)
            marker = _accepted_marker(result.get("accepted"))
            exports = result.get("exports_substate", "?")
            line = f"{result['name']}  stage {result['stage']}/4{marker}  exports: {exports}"
            if result["notes"]:
                line = f"{line}  notes: {', '.join(result['notes'])}"
            print(line)
        return 0

    example_dir = Path(sys.argv[1])
    if (
        not example_dir.is_absolute()
        and len(example_dir.parts) == 1
        and not example_dir.exists()
        and (Path("examples") / example_dir).is_dir()
    ):
        example_dir = Path("examples") / example_dir
    result = infer_stage(example_dir)
    _print_single(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
