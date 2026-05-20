"""Infer figure-pipeline stage from filesystem + spec.yaml only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_freshness import EXPORT_FRESH, EXPORT_STALE, EXPORT_TRACKED_GOLDEN, compute_export_state
from inputs import parse_spec
from publication_gate import publication_gate_summary
from quality_manifest import critique_hash_freshness, critique_manifest_paths
from reference_contract import (
    compute_reference_input_failures,
    declared_figure_reference_path,
    participating_panel_reference_paths,
)
from svg_polish_manifest import (
    FINAL_ARTIFACT_FRESH,
    FINAL_ARTIFACT_NONE,
    FINAL_ARTIFACT_POLISHED_SVG,
    compute_final_artifact_state,
)

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
_NEXT_4_STALE_CRITIQUE_REQUIRED = (
    "exports are stale — re-run /fig_compile <name>, then /fig_critique <name>,"
    " then /fig_export <name>."
)
_NEXT_4_EXPORT_STALE_CRITIQUE_REQUIRED = (
    "exports are stale or incomplete — run /fig_critique <name>,"
    " then /fig_export <name>."
)
_NEXT_4_TRACKED_STALE = (
    "tracked golden artifact is intentionally stale;"
    " to roll forward run /fig_export <name> --force-golden."
)
_NEXT_4_TRACKED_STALE_CRITIQUE_REQUIRED = (
    "tracked golden artifact is stale and reference-grounded critique is missing or stale;"
    " run /fig_compile <name>, then /fig_critique <name>,"
    " then /fig_export <name> --force-golden."
)
_NEXT_4_TRACKED_EXPORT_STALE_CRITIQUE_REQUIRED = (
    "tracked golden artifact is stale and reference-grounded critique is missing or stale;"
    " run /fig_critique <name>, then /fig_export <name> --force-golden."
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
_NEXT_REFERENCE_MISSING = (
    "fix declared reference inputs in spec.yaml or add the missing files before continuing."
)
_NEXT_MISSING_BRIEFING = "complete examples/<name>/briefing.md before continuing."
_NEXT_SPEC_PARSE_ERROR = "fix malformed examples/<name>/spec.yaml before continuing."
_NEXT_STYLE_PROFILE_UNKNOWN = (
    "fix unknown style_profile in examples/<name>/spec.yaml before continuing."
)
_NEXT_FINAL_ARTIFACT_MISSING = (
    "final artifact is missing — create or restore the declared polished SVG, audit,"
    " and polish/svg_polish_manifest.yaml, then rerun /fig_status <name>."
)
_NEXT_FINAL_ARTIFACT_INVALID = (
    "final artifact is invalid — fix spec.yaml final_artifact and"
    " polish/svg_polish_manifest.yaml, then rerun /fig_status <name>."
)
_NEXT_FINAL_ARTIFACT_STALE = (
    "final artifact is stale — refresh polish/svg_polish_manifest.yaml after"
    " source/export/critique/polish changes, then rerun /fig_status <name>."
)
_NEXT_FINAL_ARTIFACT_BLOCKED = (
    "final artifact requires semantic backport — patch TikZ/briefing/spec,"
    " rerun compile/export/critique as needed, then recreate the polish manifest."
)

_EXPORT_EXTS = (".pdf", ".svg", ".tif", ".tiff", ".png")
CRITIQUE_NOT_REQUIRED = "NOT_REQUIRED"
CRITIQUE_MISSING = "MISSING"
CRITIQUE_STALE = "STALE"
CRITIQUE_FRESH = "FRESH"
CRITIQUE_REFERENCE_MISSING = "REFERENCE_MISSING"

RENDER_NOT_SCAFFOLDED = "NOT_SCAFFOLDED"
RENDER_NOT_AUTHORED = "NOT_AUTHORED"
RENDER_MISSING = "MISSING"
RENDER_STALE = "STALE"
RENDER_FRESH = "FRESH"

ACCEPTANCE_ACCEPTED = "ACCEPTED"
ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"
ACCEPTANCE_NOT_DECLARED = "NOT_DECLARED"
_NON_BLOCKING_WORKFLOW_NOTE_PREFIXES = ("coordinate_hints_", "final_artifact_")
_SPEC_PARSE_ERROR_KEY = "__spec_parse_error__"


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
    """Render sources that should be older than compiled/exported artifacts."""
    candidates: list[Path] = [
        example_dir / f"{name}.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ]
    candidates.append(STYLE_LOCK_PATH)
    return tuple(path for path in candidates if path.exists())


def _authoring_context_paths(example_dir: Path) -> tuple[Path, ...]:
    candidates = (
        example_dir / "authoring_contract.md",
        example_dir / "reference" / "reference_pack.md",
        example_dir / "authoring_plan.md",
        example_dir / "theory_guard.md",
        example_dir / "subregion_iteration_log.md",
    )
    return tuple(path for path in candidates if path.is_file())


def _critique_source_paths(example_dir: Path, name: str, spec: dict) -> tuple[Path, ...]:
    return critique_manifest_paths(example_dir, name, spec, style_lock_path=STYLE_LOCK_PATH)


def compute_critique_state(example_dir: Path, name: str, spec: dict | None = None) -> str:
    """Return NOT_REQUIRED/MISSING/STALE/FRESH for reference-grounded critique."""
    spec_path = example_dir / "spec.yaml"
    if spec is None:
        if not spec_path.exists():
            return CRITIQUE_NOT_REQUIRED
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))

    if compute_reference_input_failures(example_dir, spec):
        return CRITIQUE_REFERENCE_MISSING

    has_figure_reference = declared_figure_reference_path(example_dir, spec) is not None
    has_panel_reference = bool(participating_panel_reference_paths(example_dir, spec))
    if not has_figure_reference and not has_panel_reference:
        return CRITIQUE_NOT_REQUIRED

    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return CRITIQUE_MISSING
    hash_freshness = critique_hash_freshness(
        critique_path,
        example_dir,
        name,
        spec,
        style_lock_path=STYLE_LOCK_PATH,
    )
    if hash_freshness is not None:
        return CRITIQUE_FRESH if hash_freshness else CRITIQUE_STALE
    if _is_stale(_critique_source_paths(example_dir, name, spec), (critique_path,)):
        return CRITIQUE_STALE
    return CRITIQUE_FRESH


def _critique_needs_action(state: str) -> bool:
    return state in {CRITIQUE_MISSING, CRITIQUE_STALE, CRITIQUE_REFERENCE_MISSING}


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
    elif critique_state == CRITIQUE_REFERENCE_MISSING:
        notes.append("critique_reference_missing")


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


def _acceptance_state(accepted: bool | None) -> str:
    if accepted is True:
        return ACCEPTANCE_ACCEPTED
    if accepted is False:
        return ACCEPTANCE_NOT_ACCEPTED
    return ACCEPTANCE_NOT_DECLARED


def _compute_render_state(
    example_dir: Path,
    spec_path: Path,
    tex_path: Path,
    build_pdf: Path,
    sources: tuple[Path, ...],
) -> str:
    if not example_dir.exists() or not example_dir.is_dir() or not spec_path.exists():
        return RENDER_NOT_SCAFFOLDED
    if not tex_path.exists():
        return RENDER_NOT_AUTHORED
    if not build_pdf.exists():
        return RENDER_MISSING
    if _is_stale(sources, (build_pdf,)):
        return RENDER_STALE
    return RENDER_FRESH


def _workflow_ready(
    stage: int,
    notes: list[str],
    exports_substate: str,
    render_state: str,
    critique_state: str,
) -> bool:
    blocking_notes = [
        note
        for note in notes
        if not note.startswith(_NON_BLOCKING_WORKFLOW_NOTE_PREFIXES)
    ]
    return (
        stage == 4
        and not blocking_notes
        and render_state == RENDER_FRESH
        and exports_substate in {EXPORT_FRESH, EXPORT_TRACKED_GOLDEN}
        and not _critique_needs_action(critique_state)
    )


def _golden_ready(workflow_ready: bool, accepted: bool | None) -> bool:
    return workflow_ready and accepted is True


def _release_ready(golden_ready: bool, exports_substate: str, final_artifact: dict) -> bool:
    if not golden_ready or exports_substate != EXPORT_FRESH:
        return False
    if final_artifact["state"] not in {FINAL_ARTIFACT_NONE, FINAL_ARTIFACT_FRESH}:
        return False
    if final_artifact["kind"] == FINAL_ARTIFACT_POLISHED_SVG:
        return final_artifact["state"] == FINAL_ARTIFACT_FRESH
    return True


def _default_final_artifact(name: str) -> dict:
    return compute_final_artifact_state(example_dir=Path("."), name=name, spec={})


def _final_artifact_state(example_dir: Path, name: str, spec: dict) -> dict:
    return compute_final_artifact_state(
        example_dir,
        name,
        spec,
        style_lock_path=STYLE_LOCK_PATH,
        spec_parse_error=bool(spec.get(_SPEC_PARSE_ERROR_KEY)),
    )


def _final_artifact_next_template(final_artifact: dict) -> str | None:
    state = final_artifact["state"]
    if state == "MISSING":
        return _NEXT_FINAL_ARTIFACT_MISSING
    if state == "INVALID":
        return _NEXT_FINAL_ARTIFACT_INVALID
    if state == "STALE":
        return _NEXT_FINAL_ARTIFACT_STALE
    if state == "BLOCKED":
        return _NEXT_FINAL_ARTIFACT_BLOCKED
    return None


def _spec_next_template(notes: list[str]) -> str | None:
    if "spec_parse_error" in notes:
        return _NEXT_SPEC_PARSE_ERROR
    if "style_profile_unknown" in notes:
        return _NEXT_STYLE_PROFILE_UNKNOWN
    return None


def _status_vector(
    stage: int,
    notes: list[str],
    accepted: bool | None,
    exports_substate: str,
    render_state: str,
    critique_state: str,
    final_artifact: dict | None = None,
    publication_gate: dict | None = None,
) -> dict:
    final_artifact = final_artifact or _default_final_artifact("")
    publication_gate = publication_gate or {
        "publication_gate_state": "NOT_APPLICABLE",
        "publication_gate_failures": [],
    }
    workflow_ready = _workflow_ready(stage, notes, exports_substate, render_state, critique_state)
    golden_ready = _golden_ready(workflow_ready, accepted)
    release_ready = _release_ready(golden_ready, exports_substate, final_artifact)
    return {
        "render_state": render_state,
        "critique_state": critique_state,
        "export_state": exports_substate,
        "acceptance_state": _acceptance_state(accepted),
        "final_artifact_state": final_artifact["state"],
        "final_artifact_kind": final_artifact["kind"],
        "final_artifact_path": final_artifact["path"],
        "workflow_ready": workflow_ready,
        "golden_ready": golden_ready,
        "release_ready": release_ready,
        "final_ready": release_ready,
        **publication_gate,
    }


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


def _safe_raw_spec_mapping(raw: object) -> dict:
    if not isinstance(raw, dict):
        return {"panels": []}
    spec = dict(raw)
    panels = spec.get("panels", [])
    if isinstance(panels, list):
        spec["panels"] = [panel for panel in panels if isinstance(panel, dict)]
    else:
        spec["panels"] = []
    return spec


def _has_top_level_final_artifact_key(text: str) -> bool:
    if text.lstrip().startswith("{"):
        return _flow_mapping_has_top_level_key(text, "final_artifact")

    lines = [
        line
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        return False
    root_indent = min(len(line) - len(line.lstrip(" ")) for line in lines)
    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == root_indent and (
            stripped.startswith("final_artifact:")
            or stripped.startswith("'final_artifact':")
            or stripped.startswith('"final_artifact":')
        ):
            return True
    return False


def _flow_mapping_has_top_level_key(text: str, key: str) -> bool:
    compact = "".join(text.split())
    if not compact.startswith("{"):
        return False
    depth = 0
    token_start = 1
    in_quote = ""
    escape = False
    for index, char in enumerate(compact):
        if in_quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_quote:
                in_quote = ""
            continue
        if char in {"'", '"'}:
            in_quote = char
            continue
        if char in "{[":
            depth += 1
            continue
        if char in "}]":
            depth -= 1
            continue
        if char == "," and depth == 1:
            token_start = index + 1
            continue
        if char == ":" and depth == 1:
            candidate = compact[token_start:index].strip("'\" ")
            if candidate == key:
                return True
    return False


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
            **_status_vector(
                0,
                [],
                None,
                exports_substate,
                RENDER_NOT_SCAFFOLDED,
                CRITIQUE_NOT_REQUIRED,
                _default_final_artifact(name),
            ),
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
            spec_text = spec_path.read_text(encoding="utf-8")
            spec = parse_spec(spec_text)
        except (UnicodeDecodeError, ValueError) as exc:
            import yaml as _yaml  # noqa: PLC0415

            try:
                raw = _yaml.safe_load(spec_text)
            except (NameError, _yaml.YAMLError):
                notes.append("spec_parse_error")
                spec = {"panels": []}
                if "spec_text" in locals() and _has_top_level_final_artifact_key(spec_text):
                    spec[_SPEC_PARSE_ERROR_KEY] = True
            else:
                if "style_profile" in str(exc):
                    notes.append("style_profile_unknown")
                else:
                    notes.append("spec_parse_error")
                if raw is not None:
                    spec = _safe_raw_spec_mapping(raw)

    accepted = _resolve_accepted(spec)
    publication_gate = publication_gate_summary(
        example_dir / "QUALITY_AUDIT.md",
        accepted=accepted,
    )
    sources = _source_paths(example_dir, name, spec)
    critique_state = compute_critique_state(example_dir, name, spec)
    render_state = _compute_render_state(example_dir, spec_path, tex_path, build_pdf, sources)
    _append_prerequisite_notes(notes, spec, previews_dir, briefing_path)
    _append_reference_image_check(checks, notes, spec, example_dir)
    _append_panel_reference_checks(notes, spec, example_dir)
    final_artifact = _final_artifact_state(example_dir, name, spec)
    notes.extend(final_artifact["notes"])

    if spec_path.exists() and not briefing_path.exists():
        checks.append(("spec_yaml", "present"))
        checks.append(("briefing_md", "missing"))
        return {
            "stage": 1,
            "name": name,
            "checks": checks,
            "next": (_spec_next_template(notes) or _NEXT_MISSING_BRIEFING).replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
            **_status_vector(
                1,
                notes,
                accepted,
                exports_substate,
                render_state,
                critique_state,
                final_artifact,
                publication_gate,
            ),
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
        # Priority: stale_export / partial_export stay above done, but their
        # remediation must include critique when run_export.py will enforce it.
        spec_next_template = _spec_next_template(notes)
        if spec_next_template is not None:
            next_template = spec_next_template
        elif "missing_briefing" in notes:
            next_template = _NEXT_MISSING_BRIEFING
        elif critique_state == CRITIQUE_REFERENCE_MISSING:
            next_template = _NEXT_REFERENCE_MISSING
        elif is_stale and _critique_needs_action(critique_state):
            if exports_substate == EXPORT_TRACKED_GOLDEN:
                if render_state == RENDER_FRESH:
                    next_template = _NEXT_4_TRACKED_EXPORT_STALE_CRITIQUE_REQUIRED
                else:
                    next_template = _NEXT_4_TRACKED_STALE_CRITIQUE_REQUIRED
            elif source_stale and render_state != RENDER_FRESH:
                next_template = _NEXT_4_STALE_CRITIQUE_REQUIRED
            else:
                next_template = _NEXT_4_EXPORT_STALE_CRITIQUE_REQUIRED
        elif is_stale and exports_substate == EXPORT_TRACKED_GOLDEN:
            next_template = _NEXT_4_TRACKED_STALE
        elif source_stale and render_state != RENDER_FRESH:
            next_template = _NEXT_4_STALE
        elif export_content_stale:
            next_template = _NEXT_4_EXPORT_STALE
        elif source_stale:
            next_template = _NEXT_4_EXPORT_STALE
        elif partial and exports_substate == EXPORT_TRACKED_GOLDEN:
            next_template = _NEXT_4_TRACKED_PARTIAL
        elif partial:
            next_template = _NEXT_4_PARTIAL
        elif _critique_needs_action(critique_state):
            next_template = _NEXT_4_CRITIQUE_REQUIRED
        elif _final_artifact_next_template(final_artifact) is not None:
            next_template = _final_artifact_next_template(final_artifact)
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
            **_status_vector(
                4,
                notes,
                accepted,
                exports_substate,
                render_state,
                critique_state,
                final_artifact,
                publication_gate,
            ),
        }

    # Stage 3: build pdf exists, fresh against tex+briefing+style-lock, no exports
    if build_pdf.exists() and tex_path.exists() and not _is_stale(sources, (build_pdf,)):
        checks.append(("build_pdf", "fresh"))
        _append_critique_check(checks, notes, critique_state)
        spec_next_template = _spec_next_template(notes)
        if spec_next_template is not None:
            next_template = spec_next_template
        elif "missing_briefing" in notes:
            next_template = _NEXT_MISSING_BRIEFING
        elif critique_state == CRITIQUE_REFERENCE_MISSING:
            next_template = _NEXT_REFERENCE_MISSING
        elif _critique_needs_action(critique_state):
            next_template = _NEXT_3_CRITIQUE_REQUIRED
        else:
            next_template = _NEXT_3
        return {
            "stage": 3,
            "name": name,
            "checks": checks,
            "next": next_template.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
            **_status_vector(
                3,
                notes,
                accepted,
                exports_substate,
                render_state,
                critique_state,
                final_artifact,
                publication_gate,
            ),
        }

    # Stage 2: tex exists AND (no build pdf OR pdf stale relative to source set)
    if tex_path.exists():
        if not build_pdf.exists():
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "missing"))
        else:
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "stale"))
        spec_next_template = _spec_next_template(notes)
        if spec_next_template is not None:
            next_template = spec_next_template
        else:
            next_template = (
                _NEXT_MISSING_BRIEFING if "missing_briefing" in notes else _NEXT_2
            )
        return {
            "stage": 2,
            "name": name,
            "checks": checks,
            "next": next_template.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
            **_status_vector(
                2,
                notes,
                accepted,
                exports_substate,
                render_state,
                critique_state,
                final_artifact,
                publication_gate,
            ),
        }

    # Stage 1: spec.yaml exists, no .tex authored yet
    if spec_path.exists():
        checks.append(("spec_yaml", "present"))
        next_template = _spec_next_template(notes) or _NEXT_1
        return {
            "stage": 1,
            "name": name,
            "checks": checks,
            "next": next_template.replace("<name>", name),
            "notes": notes,
            "accepted": accepted,
            "exports_substate": exports_substate,
            **_status_vector(
                1,
                notes,
                accepted,
                exports_substate,
                render_state,
                critique_state,
                final_artifact,
                publication_gate,
            ),
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
        **_status_vector(
            0,
            [],
            accepted,
            exports_substate,
            render_state,
            critique_state,
            _default_final_artifact(name),
            publication_gate,
        ),
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
    if result.get("final_artifact_state"):
        print(
            "  Final artifact: "
            f"{result.get('final_artifact_kind', '?')} "
            f"{result.get('final_artifact_state', '?')} "
            f"{result.get('final_artifact_path', '?')}"
        )
    final_ready = str(bool(result.get("final_ready"))).lower()
    print(
        "  States: "
        f"render={result.get('render_state', '?')} "
        f"critique={result.get('critique_state', '?')} "
        f"export={result.get('export_state', '?')} "
        f"acceptance={result.get('acceptance_state', '?')} "
        f"workflow_ready={str(bool(result.get('workflow_ready'))).lower()} "
        f"golden_ready={str(bool(result.get('golden_ready'))).lower()} "
        f"release_ready={str(bool(result.get('release_ready'))).lower()} "
        f"final_ready={final_ready}"
    )
    publication_gate_state = result.get("publication_gate_state")
    if publication_gate_state and publication_gate_state != "NOT_APPLICABLE":
        print(f"  Publication gate: {publication_gate_state}")
        failures = result.get("publication_gate_failures")
        if isinstance(failures, list) and failures:
            first = failures[0]
            if isinstance(first, dict):
                print(
                    "  Publication blocker: "
                    f"{first.get('code', '?')} — {first.get('required_action', '?')}"
                )
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
            ready = str(bool(result.get("release_ready"))).lower()
            line = (
                f"{result['name']}  stage {result['stage']}/4{marker}"
                f"  exports: {exports}  ready: {ready}"
            )
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
