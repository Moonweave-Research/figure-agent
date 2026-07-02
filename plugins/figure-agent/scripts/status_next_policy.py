"""Next-action hint policy for /fig_status."""

from __future__ import annotations

from collections.abc import Mapping

from export_freshness import EXPORT_TRACKED_GOLDEN

_NEXT_0 = "run /fig_new <name> to create the figure scaffold."
_NEXT_1 = (
    "author examples/<name>/<name>.tex from briefing.md"
    " (cp styles/tex_template.tex to start), then /fig_compile <name>."
)
_NEXT_2 = "run /fig_compile <name> to compile the TikZ source."
_NEXT_3 = (
    "run /fig_critique <name> for pre-export grounded review when useful,"
    " then /fig_export <name>."
)
_NEXT_3_CRITIQUE_REQUIRED = (
    "run /fig_critique <name> before /fig_export <name>"
    " because grounded pre-export critique is missing or stale."
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
    "tracked golden artifact is stale and grounded critique is missing or stale;"
    " run /fig_compile <name>, then /fig_critique <name>,"
    " then /fig_export <name> --force-golden."
)
_NEXT_4_TRACKED_EXPORT_STALE_CRITIQUE_REQUIRED = (
    "tracked golden artifact is stale and grounded critique is missing or stale;"
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
_NEXT_4_ACCEPTANCE_NOT_DECLARED = (
    "fixture has no accepted or final-ready declaration — keep iterating with"
    " /fig_loop <name>, or make an explicit human acceptance/final-artifact"
    " decision before release."
)
_NEXT_4_ACCEPTANCE_AUTHORIZED = (
    "valid human decision record exists; release-state mutation still requires "
    "explicit operation: <release_operation>."
)
_NEXT_4_NON_RELEASE_DECISION = (
    "valid human decision record requests <route>; keep release blocked and route "
    "to non-release work before acceptance."
)
_NEXT_4_CRITIQUE_REQUIRED = (
    "run /fig_critique <name> as a final review of the current rendered candidate"
    " before treating exports as final;"
    " if no edits are needed, existing exports can remain in place."
)
_NEXT_CRITIQUE_LINT_BLOCKED = (
    "run /fig_critique <name> to rewrite critique.md so it passes critique_lint.py"
    " before continuing."
)
_NEXT_REFERENCE_MISSING = (
    "fix declared reference inputs in spec.yaml or add the missing files before continuing."
)
_NEXT_MISSING_BRIEFING = "complete examples/<name>/briefing.md before continuing."
_NEXT_SPEC_PARSE_ERROR = "fix malformed examples/<name>/spec.yaml before continuing."
_NEXT_STYLE_PROFILE_UNKNOWN = (
    "fix unknown style_profile in examples/<name>/spec.yaml before continuing."
)
_NEXT_FINAL_ARTIFACT_MISSING = "final artifact is missing — regenerate exports before continuing."
_NEXT_FINAL_ARTIFACT_INVALID = (
    "final artifact is invalid — fix spec.yaml and rerun /fig_status <name>."
)
_NEXT_FINAL_ARTIFACT_STALE = "final artifact is stale — rerun compile/export before continuing."
_NEXT_FINAL_ARTIFACT_BLOCKED = (
    "final artifact requires semantic backport (semantic_backport_required)"
    " — patch TikZ/briefing/spec, then rerun compile/export/critique as needed."
)


def critique_needs_action(state: str) -> bool:
    return state in {"BRIEFING_REQUIRED", "MISSING", "STALE", "REFERENCE_MISSING"}


def _spec_next_template(notes: list[str]) -> str | None:
    if "spec_parse_error" in notes:
        return _NEXT_SPEC_PARSE_ERROR
    if "style_profile_unknown" in notes:
        return _NEXT_STYLE_PROFILE_UNKNOWN
    return None


def _final_artifact_next_template(final_artifact: Mapping[str, object] | None) -> str | None:
    if final_artifact is None:
        return None
    state = final_artifact.get("state")
    if state == "MISSING":
        return _NEXT_FINAL_ARTIFACT_MISSING
    if state == "INVALID":
        return _NEXT_FINAL_ARTIFACT_INVALID
    if state == "STALE":
        return _NEXT_FINAL_ARTIFACT_STALE
    if state == "BLOCKED":
        return _NEXT_FINAL_ARTIFACT_BLOCKED
    return None


def _select_stage_4_template(
    *,
    notes: list[str],
    critique_state: str,
    exports_substate: str,
    source_stale: bool,
    export_content_stale: bool,
    render_state: str,
    partial: bool,
    final_artifact: Mapping[str, object] | None,
    accepted: bool | None,
    release_decision: Mapping[str, object] | None,
) -> str:
    is_stale = source_stale or export_content_stale
    spec_next_template = _spec_next_template(notes)
    if spec_next_template is not None:
        return spec_next_template
    if "missing_briefing" in notes:
        return _NEXT_MISSING_BRIEFING
    if "critique_lint_blocked" in notes:
        return _NEXT_CRITIQUE_LINT_BLOCKED
    if critique_state == "REFERENCE_MISSING":
        return _NEXT_REFERENCE_MISSING
    if is_stale and critique_needs_action(critique_state):
        if exports_substate == EXPORT_TRACKED_GOLDEN:
            if render_state == "FRESH":
                return _NEXT_4_TRACKED_EXPORT_STALE_CRITIQUE_REQUIRED
            return _NEXT_4_TRACKED_STALE_CRITIQUE_REQUIRED
        if source_stale and render_state != "FRESH":
            return _NEXT_4_STALE_CRITIQUE_REQUIRED
        return _NEXT_4_EXPORT_STALE_CRITIQUE_REQUIRED
    if is_stale and exports_substate == EXPORT_TRACKED_GOLDEN:
        return _NEXT_4_TRACKED_STALE
    if source_stale and render_state != "FRESH":
        return _NEXT_4_STALE
    if export_content_stale:
        return _NEXT_4_EXPORT_STALE
    if source_stale:
        return _NEXT_4_EXPORT_STALE
    if partial and exports_substate == EXPORT_TRACKED_GOLDEN:
        return _NEXT_4_TRACKED_PARTIAL
    if partial:
        return _NEXT_4_PARTIAL
    if critique_needs_action(critique_state):
        return _NEXT_4_CRITIQUE_REQUIRED
    final_artifact_template = _final_artifact_next_template(final_artifact)
    if final_artifact_template is not None:
        return final_artifact_template
    if accepted is False:
        return _NEXT_4_NOT_ACCEPTED
    if accepted is None:
        if release_decision is not None:
            state = release_decision.get("state")
            if state == "acceptance_authorized":
                return _NEXT_4_ACCEPTANCE_AUTHORIZED.replace(
                    "<release_operation>",
                    str(release_decision.get("release_operation") or "inspect status"),
                )
            if state == "non_release_requested":
                return _NEXT_4_NON_RELEASE_DECISION.replace(
                    "<route>",
                    str(release_decision.get("route") or "non-release work"),
                )
        return _NEXT_4_ACCEPTANCE_NOT_DECLARED
    return _NEXT_4


def select_next_hint(
    *,
    stage: int,
    name: str,
    notes: list[str],
    critique_state: str,
    exports_substate: str,
    source_stale: bool = False,
    export_content_stale: bool = False,
    render_state: str = "FRESH",
    partial: bool = False,
    final_artifact: Mapping[str, object] | None = None,
    accepted: bool | None = None,
    release_decision: Mapping[str, object] | None = None,
) -> str:
    if stage == 0:
        template = _NEXT_0
    elif stage == 1:
        template = _spec_next_template(notes)
        if template is None:
            template = _NEXT_MISSING_BRIEFING if "missing_briefing" in notes else _NEXT_1
    elif stage == 2:
        template = _spec_next_template(notes)
        if template is None:
            template = _NEXT_MISSING_BRIEFING if "missing_briefing" in notes else _NEXT_2
    elif stage == 3:
        template = _spec_next_template(notes)
        if template is None:
            if "missing_briefing" in notes:
                template = _NEXT_MISSING_BRIEFING
            elif "critique_lint_blocked" in notes:
                template = _NEXT_CRITIQUE_LINT_BLOCKED
            elif critique_state == "REFERENCE_MISSING":
                template = _NEXT_REFERENCE_MISSING
            elif critique_needs_action(critique_state):
                template = _NEXT_3_CRITIQUE_REQUIRED
            else:
                template = _NEXT_3
    elif stage == 4:
        template = _select_stage_4_template(
            notes=notes,
            critique_state=critique_state,
            exports_substate=exports_substate,
            source_stale=source_stale,
            export_content_stale=export_content_stale,
            render_state=render_state,
            partial=partial,
            final_artifact=final_artifact,
            accepted=accepted,
            release_decision=release_decision,
        )
    else:
        raise ValueError(f"unsupported status stage: {stage}")
    return template.replace("<name>", name)
