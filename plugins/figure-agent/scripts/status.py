"""Infer figure-pipeline stage from filesystem + spec.yaml only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_freshness import compute_export_state
from inputs import parse_spec

# Match review_brief's freshness source set so /fig_status and /fig_review agree.
STYLE_LOCK_PATH = Path(__file__).resolve().parent.parent / "styles" / "polymer-paper-preamble.sty"

_NEXT_0 = "run /fig_new <name> to create the figure scaffold."
# Stage 1/2 next-hints reference the legacy image-gen orchestration path.
# Mark them explicitly so users know the active alternative (author the .tex
# directly via the briefing-driven workflow described in
# docs/architecture-overview.md Layer 3).
_NEXT_1 = (
    "[legacy] run /fig_prompt <name> to generate the normalized image-gen"
    " prompt — or skip directly to authoring examples/<name>/<name>.tex"
    " from briefing.md (active workflow)."
)
_NEXT_2 = (
    "[legacy] run /fig_preview_select <name> to record your chosen preview —"
    " or skip directly to authoring examples/<name>/<name>.tex (active workflow)."
)
_NEXT_3 = (
    "author examples/<name>/<name>.tex"
    " (cp styles/tex_template.tex to start), then /fig_compile <name>."
)
_NEXT_4 = "run /fig_compile <name> to compile the TikZ source."
# Stage 5: prefer the active /fig_export gate; /fig_review is legacy.
_NEXT_5 = "run /fig_export <name> (or [legacy] /fig_review <name> for an external critic brief)."
_NEXT_6 = (
    "done — outputs in examples/<name>/exports/."
    " To revise, edit <name>.tex and re-run /fig_compile then /fig_export."
)
_NEXT_6_STALE = "exports are stale — re-run /fig_compile <name> then /fig_export <name>."
_NEXT_6_PARTIAL = (
    "exports are incomplete — re-run /fig_export <name> to generate the"
    " missing PDF/SVG/TIFF/PNG artifacts."
)
_NEXT_6_NOT_ACCEPTED = (
    "golden fixture is not accepted yet — resolve examples/<name>/QUALITY_AUDIT.md"
    " defects, then set accepted: true in spec.yaml."
)
_NEXT_MISSING_BRIEFING = "complete examples/<name>/briefing.md before continuing."

_EXPORT_EXTS = (".pdf", ".svg", ".tif", ".tiff", ".png")


def _has_image_files(directory: Path, exts: set[str] | None = None) -> bool:
    if exts is None:
        exts = {".png", ".jpg", ".jpeg"}
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name == ".gitkeep":
            continue
        if entry.suffix.lower() in exts:
            return True
    return False


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


def _source_paths(example_dir: Path, name: str) -> tuple[Path, ...]:
    """Sources that should be older than any compiled artifact (matches review_brief)."""
    candidates = [example_dir / f"{name}.tex", example_dir / "briefing.md", STYLE_LOCK_PATH]
    return tuple(path for path in candidates if path.exists())


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

    selected_preview = spec.get("selected_preview") if spec else None
    if selected_preview and isinstance(selected_preview, str) and selected_preview.strip():
        if not (previews_dir.is_dir() and (previews_dir / selected_preview).is_file()):
            notes.append("selected_preview_missing")


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

        _yaml.safe_load(hints_path.read_text(encoding="utf-8"))
    except Exception:
        notes.append("coordinate_hints_parse_error")
        return
    if hints_path.stat().st_mtime < reference_path.stat().st_mtime:
        notes.append("coordinate_hints_stale")


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
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))

    accepted = _resolve_accepted(spec)
    sources = _source_paths(example_dir, name)
    _append_prerequisite_notes(notes, spec, previews_dir, briefing_path)
    _append_reference_image_check(checks, notes, spec, example_dir)

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

    # Stage 6: any export artifact present
    if exports_dir.exists() and _has_export_artifact(exports_dir, name):
        checks.append(("exports", "present"))
        partial = not _all_four_exports_present(exports_dir, name)
        if partial:
            notes.append("partial_export")
        export_paths = _existing_export_paths(exports_dir, name)
        is_stale = _is_stale(sources, export_paths)
        if is_stale:
            notes.append("stale_export")
        # Priority: stale_export > partial_export > not_accepted > done.
        # partial_export sits above not-accepted because incomplete artifacts
        # block both manuscript use and the golden contract gate.
        if is_stale:
            next_template = _NEXT_6_STALE
        elif partial:
            next_template = _NEXT_6_PARTIAL
        elif accepted is False:
            next_template = _NEXT_6_NOT_ACCEPTED
        else:
            next_template = _NEXT_6
        return {
            "stage": 6,
            "name": name,
            "checks": checks,
            "next": next_template.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 5: build pdf exists, fresh against tex+briefing+style-lock, no exports
    if build_pdf.exists() and tex_path.exists() and not _is_stale(sources, (build_pdf,)):
        checks.append(("build_pdf", "fresh"))
        return {
            "stage": 5,
            "name": name,
            "checks": checks,
            "next": _NEXT_5.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 4: tex exists AND (no build pdf OR pdf stale relative to source set)
    if tex_path.exists():
        if not build_pdf.exists():
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "missing"))
        else:
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "stale"))
        return {
            "stage": 4,
            "name": name,
            "checks": checks,
            "next": _NEXT_4.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 3: selected_preview is a non-empty string, no tex
    selected_preview = spec.get("selected_preview") if spec else None
    if selected_preview and isinstance(selected_preview, str) and selected_preview.strip():
        checks.append(("selected_preview", selected_preview))
        return {
            "stage": 3,
            "name": name,
            "checks": checks,
            "next": _NEXT_3.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    previews_has_images = previews_dir.is_dir() and _has_image_files(previews_dir)

    # Stage 2: previews/ has image files AND selected_preview unset/null/empty
    if previews_has_images:
        checks.append(("previews", "has images"))
        checks.append(("selected_preview", "unset"))
        return {
            "stage": 2,
            "name": name,
            "checks": checks,
            "next": _NEXT_2.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
        }

    # Stage 1: spec.yaml exists AND previews/ has no image files
    if spec_path.exists():
        checks.append(("spec_yaml", "present"))
        checks.append(("previews", "empty"))
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
    print(f"{name} — stage {stage}/6{marker}")
    for key, val in checks:
        print(f"  {key}: {val}")
    print(f"  Next: {next_hint}")
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
            line = f"{result['name']}  stage {result['stage']}/6{marker}"
            if result["notes"]:
                line = f"{line}  notes: {', '.join(result['notes'])}"
            print(line)
        return 0

    example_dir = Path(sys.argv[1])
    result = infer_stage(example_dir)
    _print_single(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
