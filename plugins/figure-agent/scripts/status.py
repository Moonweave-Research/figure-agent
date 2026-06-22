"""Infer figure-pipeline stage from filesystem + spec.yaml only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import runtime_paths
import status_next_policy
import status_readiness_policy
from audit_evidence_summary import summarize_audit_evidence
from briefing_grounding import has_reference_free_grounding_context
from critique_lint import lint_critique
from export_freshness import EXPORT_FRESH, EXPORT_STALE, compute_export_state
from inputs import parse_spec
from next_action_summary import status_next_action_summary
from publication_gate import publication_gate_summary
from quality_manifest import (
    critique_freshness_diagnostics,
    critique_hash_freshness,
    critique_manifest_paths,
)
from reference_aesthetic_metrics import reference_aesthetic_metrics_summary
from reference_contract import (
    compute_reference_input_failures,
    declared_figure_reference_path,
    participating_panel_reference_paths,
)
from status_explanation import build_status_explanation
from svg_polish_manifest import (
    FINAL_ARTIFACT_POLISHED_SVG,
    compute_final_artifact_state,
)

# Shared build/export freshness source set. /fig_critique adds panel references
# for crop/reference comparisons, but status should not require a rebuild for
# critique-only panel-reference edits.
STYLE_LOCK_PATH = (
    runtime_paths.resolve_runtime_paths().styles_dir / "polymer-paper-preamble.sty"
)

_EXPORT_EXTS = (".pdf", ".svg", ".tif", ".tiff", ".png")
CRITIQUE_NOT_REQUIRED = "NOT_REQUIRED"
CRITIQUE_BRIEFING_REQUIRED = "BRIEFING_REQUIRED"
CRITIQUE_MISSING = "MISSING"
CRITIQUE_STALE = "STALE"
CRITIQUE_FRESH = "FRESH"
CRITIQUE_REFERENCE_MISSING = "REFERENCE_MISSING"

RENDER_NOT_SCAFFOLDED = "NOT_SCAFFOLDED"
RENDER_NOT_AUTHORED = "NOT_AUTHORED"
RENDER_MISSING = "MISSING"
RENDER_STALE = "STALE"
RENDER_FRESH = "FRESH"

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
        if not has_reference_free_grounding_context(example_dir):
            return CRITIQUE_NOT_REQUIRED
        critique_path = example_dir / "critique.md"
        if not critique_path.is_file():
            return CRITIQUE_BRIEFING_REQUIRED

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


def _append_critique_check(
    checks: list[tuple[str, str]], notes: list[str], critique_state: str
) -> None:
    if critique_state == CRITIQUE_NOT_REQUIRED:
        return
    checks.append(("critique", critique_state.lower()))
    if critique_state == CRITIQUE_MISSING:
        notes.append("critique_missing")
    elif critique_state == CRITIQUE_BRIEFING_REQUIRED:
        notes.append("critique_briefing_required")
    elif critique_state == CRITIQUE_STALE:
        notes.append("critique_stale")
    elif critique_state == CRITIQUE_REFERENCE_MISSING:
        notes.append("critique_reference_missing")


def _append_critique_lint_check(
    checks: list[tuple[str, str]],
    notes: list[str],
    example_dir: Path,
    critique_state: str,
) -> dict | None:
    if critique_state != CRITIQUE_FRESH:
        return None
    violations = lint_critique(example_dir)
    if not violations:
        checks.append(("critique_lint", "passed"))
        return {
            "state": "passed",
            "violation_count": 0,
            "first_category": None,
            "first_message": None,
        }
    checks.append(("critique_lint", "blocked"))
    notes.append("critique_lint_blocked")
    first = violations[0]
    return {
        "state": "blocked",
        "violation_count": len(violations),
        "first_category": first.category,
        "first_message": first.message,
    }


def _add_critique_lint_summary(result: dict, summary: dict | None) -> dict:
    if summary is not None:
        result["critique_lint_summary"] = summary
    return result


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


def _requires_publication_disclosure(spec: dict) -> bool:
    final_artifact = spec.get("final_artifact") if spec else None
    return (
        isinstance(final_artifact, dict)
        and final_artifact.get("kind") == FINAL_ARTIFACT_POLISHED_SVG
    )


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
    return status_readiness_policy.build_status_vector(
        stage=stage,
        notes=notes,
        accepted=accepted,
        exports_substate=exports_substate,
        render_state=render_state,
        critique_state=critique_state,
        final_artifact=final_artifact,
        publication_gate=publication_gate,
    )


def _with_status_explanation(result: dict) -> dict:
    result["status_explanation"] = build_status_explanation(result)
    result["next_action_summary"] = status_next_action_summary(result)
    return result


def _append_critique_freshness_diagnostics(result: dict, example_dir: Path) -> None:
    critique_path = example_dir / "critique.md"
    name = result.get("name")
    if not critique_path.is_file() or not isinstance(name, str) or not name:
        return
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return
    result["critique_freshness"] = critique_freshness_diagnostics(
        critique_path,
        example_dir,
        name,
        spec,
        style_lock_path=STYLE_LOCK_PATH,
    )


def _finalize_status(result: dict, example_dir: Path) -> dict:
    _append_critique_freshness_diagnostics(result, example_dir)
    result["audit_evidence"] = summarize_audit_evidence(example_dir)
    metrics_summary = reference_aesthetic_metrics_summary(example_dir)
    if metrics_summary is not None:
        state = metrics_summary.get("evaluation_state", "invalid")
        result["reference_aesthetic_metrics"] = metrics_summary
        result.setdefault("checks", []).append(("reference_aesthetic_metrics", state))
        if state in {"missing", "stale", "invalid"}:
            result.setdefault("notes", []).append(f"reference_aesthetic_metrics_{state}")
        elif state == "warning":
            result.setdefault("notes", []).append("reference_aesthetic_metrics_warning")
        elif state == "severe_divergence":
            result.setdefault("notes", []).append("reference_aesthetic_metrics_severe")
    return _with_status_explanation(result)


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
        return _finalize_status({
            "stage": 0,
            "name": name,
            "checks": [],
            "next": status_next_policy.select_next_hint(
                stage=0,
                name=name,
                notes=[],
                critique_state=CRITIQUE_NOT_REQUIRED,
                exports_substate=exports_substate,
            ),
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
        }, example_dir)

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
        require_disclosure=_requires_publication_disclosure(spec),
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
        return _finalize_status({
            "stage": 1,
            "name": name,
            "checks": checks,
            "next": status_next_policy.select_next_hint(
                stage=1,
                name=name,
                notes=notes,
                critique_state=critique_state,
                exports_substate=exports_substate,
            ),
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
        }, example_dir)

    # Stage 4: any export artifact present
    if exports_dir.exists() and _has_export_artifact(exports_dir, name):
        checks.append(("exports", "present"))
        _append_critique_check(checks, notes, critique_state)
        critique_lint_summary = _append_critique_lint_check(
            checks,
            notes,
            example_dir,
            critique_state,
        )
        partial = not _all_four_exports_present(exports_dir, name)
        if partial:
            notes.append("partial_export")
        export_paths = _existing_export_paths(exports_dir, name)
        source_stale = (
            _is_stale(sources, export_paths)
            if exports_substate != EXPORT_FRESH
            else False
        )
        export_content_stale = exports_substate == EXPORT_STALE
        is_stale = source_stale or export_content_stale
        if is_stale:
            notes.append("stale_export")
        # Priority: stale_export / partial_export stay above done, but their
        # remediation must include critique when run_export.py will enforce it.
        next_hint = status_next_policy.select_next_hint(
            stage=4,
            name=name,
            notes=notes,
            critique_state=critique_state,
            exports_substate=exports_substate,
            source_stale=source_stale,
            export_content_stale=export_content_stale,
            render_state=render_state,
            partial=partial,
            final_artifact=final_artifact,
            accepted=accepted,
        )
        return _finalize_status(
            _add_critique_lint_summary(
                {
                    "stage": 4,
                    "name": name,
                    "checks": checks,
                    "next": next_hint,
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
                },
                critique_lint_summary,
            ),
            example_dir,
        )

    # Stage 3: build pdf exists, fresh against tex+briefing+style-lock, no exports
    if build_pdf.exists() and tex_path.exists() and not _is_stale(sources, (build_pdf,)):
        checks.append(("build_pdf", "fresh"))
        _append_critique_check(checks, notes, critique_state)
        critique_lint_summary = _append_critique_lint_check(
            checks,
            notes,
            example_dir,
            critique_state,
        )
        return _finalize_status(
            _add_critique_lint_summary(
                {
                    "stage": 3,
                    "name": name,
                    "checks": checks,
                    "next": status_next_policy.select_next_hint(
                        stage=3,
                        name=name,
                        notes=notes,
                        critique_state=critique_state,
                        exports_substate=exports_substate,
                    ),
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
                },
                critique_lint_summary,
            ),
            example_dir,
        )

    # Stage 2: tex exists AND (no build pdf OR pdf stale relative to source set)
    if tex_path.exists():
        if not build_pdf.exists():
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "missing"))
        else:
            checks.append(("tex", "present"))
            checks.append(("build_pdf", "stale"))
        return _finalize_status({
            "stage": 2,
            "name": name,
            "checks": checks,
            "next": status_next_policy.select_next_hint(
                stage=2,
                name=name,
                notes=notes,
                critique_state=critique_state,
                exports_substate=exports_substate,
            ),
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
        }, example_dir)

    # Stage 1: spec.yaml exists, no .tex authored yet
    if spec_path.exists():
        checks.append(("spec_yaml", "present"))
        return _finalize_status({
            "stage": 1,
            "name": name,
            "checks": checks,
            "next": status_next_policy.select_next_hint(
                stage=1,
                name=name,
                notes=notes,
                critique_state=critique_state,
                exports_substate=exports_substate,
            ),
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
        }, example_dir)

    # Stage 0 fallback (directory exists but no spec.yaml)
    return _finalize_status({
        "stage": 0,
        "name": name,
        "checks": [],
        "next": status_next_policy.select_next_hint(
            stage=0,
            name=name,
            notes=[],
            critique_state=CRITIQUE_NOT_REQUIRED,
            exports_substate=exports_substate,
        ),
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
    }, example_dir)


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
    audit_evidence = result.get("audit_evidence")
    if isinstance(audit_evidence, dict):
        blocking_items = audit_evidence.get("blocking_items")
        blocking_text = ""
        if isinstance(blocking_items, list) and blocking_items:
            blocking_text = f" blocking={','.join(str(item) for item in blocking_items[:5])}"
        next_action = audit_evidence.get("next_action")
        next_text = f" next={next_action}" if next_action else ""
        print(
            "  Audit evidence: "
            f"{audit_evidence.get('evaluation_state', '?')} — "
            f"{audit_evidence.get('reason', '?')}"
            f"{blocking_text}{next_text}"
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
    explanation = result.get("status_explanation")
    if isinstance(explanation, dict):
        first_blocker = explanation.get("first_blocker")
        if isinstance(first_blocker, dict):
            code = first_blocker.get("code", "?")
            message = first_blocker.get("message", "?")
            command = first_blocker.get("next_command")
            manual = first_blocker.get("manual")
            suffix = " manual=true" if manual else ""
            command_text = f" next={command}" if command else ""
            print(f"  Explanation: {code} — {message}{command_text}{suffix}")
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


def main(argv: list[str] | None = None, *, workspace_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    emit_json = args.json or args.format == "json"
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)

    if args.name is None:
        examples_dir = paths.examples_dir
        if not examples_dir.is_dir():
            print("no examples/ directory found", file=sys.stderr)
            return 1
        results = []
        for entry in sorted(p for p in examples_dir.iterdir() if p.is_dir()):
            result = infer_stage(entry)
            if emit_json:
                results.append(result)
                continue
            marker = _accepted_marker(result.get("accepted"))
            exports = result.get("exports_substate", "?")
            ready = str(bool(result.get("release_ready"))).lower()
            line = (
                f"{result['name']}  stage {result['stage']}/4{marker}"
                f"  exports: {exports}  ready: {ready}"
            )
            publication_gate_state = result.get("publication_gate_state")
            if publication_gate_state and publication_gate_state != "NOT_APPLICABLE":
                line = f"{line}  publication: {publication_gate_state}"
            audit_evidence = result.get("audit_evidence")
            if isinstance(audit_evidence, dict):
                audit_state = audit_evidence.get("evaluation_state")
                if audit_state not in {"passed", "legacy", "not_applicable"}:
                    line = f"{line}  audit: {audit_state}"
            if result["notes"]:
                line = f"{line}  notes: {', '.join(result['notes'])}"
            print(line)
        if emit_json:
            print(json.dumps(results, indent=2, sort_keys=True, default=str))
        return 0

    try:
        example_dir = _resolve_example_dir_for_cli(args.name, workspace_root=paths.workspace_root)
    except ValueError as exc:
        print(f"invalid fixture path: {exc}", file=sys.stderr)
        return 1
    result = infer_stage(example_dir)
    if emit_json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        _print_single(result)
    return 0


def _resolve_example_dir_for_cli(value: str, *, workspace_root: Path | None = None) -> Path:
    return runtime_paths.resolve_example_dir_for_cli(value, workspace_root=workspace_root)


if __name__ == "__main__":
    sys.exit(main())
