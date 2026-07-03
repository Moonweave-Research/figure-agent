"""Human-readable status explanation for /fig_status and fig_driver."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

PLUGIN_STATE = "plugin_state"
FIXTURE_FRESHNESS = "fixture_freshness"
HUMAN_BLOCKER = "human_blocker"

_BUCKET_KEYS = (PLUGIN_STATE, FIXTURE_FRESHNESS, "human_blockers")


def _entry(
    *,
    code: str,
    category: str,
    message: str,
    next_command: str | None = None,
    manual: bool = False,
) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "message": message,
        "next_command": next_command,
        "manual": manual,
    }


def _command(name: object, slash: str) -> str:
    return f"{slash} {name}" if isinstance(name, str) and name else slash


def _append_if(
    bucket: list[dict[str, Any]],
    condition: bool,
    *,
    code: str,
    category: str,
    message: str,
    next_command: str | None = None,
    manual: bool = False,
) -> None:
    if condition:
        bucket.append(
            _entry(
                code=code,
                category=category,
                message=message,
                next_command=next_command,
                manual=manual,
            )
        )


def build_status_explanation(status: Mapping[str, Any]) -> dict[str, Any]:
    """Derive a compact UX explanation from the existing status vector."""
    name = status.get("name")
    render = status.get("render_state")
    critique = status.get("critique_state")
    export = status.get("export_state")
    acceptance = status.get("acceptance_state")
    final_artifact = status.get("final_artifact_state")
    adjudication = status.get("adjudication_state")
    publication_gate = status.get("publication_gate_state")
    stage = status.get("stage")
    release_ready = status.get("release_ready")
    final_ready = status.get("final_ready")
    release_decision = status.get("release_decision")

    plugin_state: list[dict[str, Any]] = []
    fixture_freshness: list[dict[str, Any]] = []
    human_blockers: list[dict[str, Any]] = []

    _append_if(
        fixture_freshness,
        render == "NOT_SCAFFOLDED",
        code="source_not_scaffolded",
        category=FIXTURE_FRESHNESS,
        message=(
            "fixture directory or spec.yaml is missing; scaffold the fixture before "
            "compile/export."
        ),
    )
    _append_if(
        fixture_freshness,
        render == "NOT_AUTHORED",
        code="source_not_authored",
        category=FIXTURE_FRESHNESS,
        message="TikZ source is missing; author <name>.tex before compile/export.",
    )
    _append_if(
        fixture_freshness,
        render == "MISSING",
        code="render_missing",
        category=FIXTURE_FRESHNESS,
        message="build PDF is missing; compile the TikZ source before review or export.",
        next_command=_command(name, "/fig_compile"),
    )
    _append_if(
        fixture_freshness,
        render == "STALE",
        code="render_stale",
        category=FIXTURE_FRESHNESS,
        message="build PDF is older than its source set; refresh the render first.",
        next_command=_command(name, "/fig_compile"),
    )
    _append_if(
        fixture_freshness,
        critique == "REFERENCE_MISSING",
        code="critique_reference_missing",
        category=FIXTURE_FRESHNESS,
        message="declared critique reference input is missing; fix spec.yaml or add the file.",
        manual=True,
    )
    _append_if(
        fixture_freshness,
        critique == "MISSING",
        code="critique_missing",
        category=FIXTURE_FRESHNESS,
        message="reference-grounded critique.md is missing; run host vision critique.",
        next_command=_command(name, "/fig_critique"),
        manual=True,
    )
    _append_if(
        fixture_freshness,
        critique == "BRIEFING_REQUIRED",
        code="critique_briefing_required",
        category=FIXTURE_FRESHNESS,
        message=(
            "briefing-grounded critique.md is missing; run host vision critique "
            "against explicit briefing rules and detector evidence."
        ),
        next_command=_command(name, "/fig_critique"),
        manual=True,
    )
    _append_if(
        fixture_freshness,
        critique == "STALE",
        code="critique_stale",
        category=FIXTURE_FRESHNESS,
        message="critique.md is stale against the current critique input hash.",
        next_command=_command(name, "/fig_critique"),
        manual=True,
    )
    _append_if(
        plugin_state,
        critique == "NOT_REQUIRED",
        code="critique_not_required",
        category=PLUGIN_STATE,
        message="no reference-grounded critique is required for this fixture.",
    )
    _append_if(
        fixture_freshness,
        adjudication in {"MISSING", "STALE", "INVALID"},
        code=f"adjudication_{str(adjudication).lower()}",
        category=FIXTURE_FRESHNESS,
        message="critique_adjudication.yaml is missing, stale, or invalid; scaffold adjudication before review closure.",
        next_command=_command(name, "/fig_adjudicate"),
    )
    _append_if(
        fixture_freshness,
        "critique_lint_blocked" in status.get("notes", []),
        code="critique_lint_blocked",
        category=FIXTURE_FRESHNESS,
        message="critique.md is hash-fresh but fails critique_lint.py accountability checks.",
        next_command=_command(name, "/fig_critique"),
        manual=True,
    )
    _append_if(
        fixture_freshness,
        export == "MISSING",
        code="export_missing",
        category=FIXTURE_FRESHNESS,
        message="export artifacts are missing.",
        next_command=_command(name, "/fig_export"),
    )
    _append_if(
        fixture_freshness,
        export == "STALE",
        code="export_stale",
        category=FIXTURE_FRESHNESS,
        message="export artifacts are stale or incomplete.",
        next_command=_command(name, "/fig_export"),
    )
    _append_if(
        human_blockers,
        export == "TRACKED_GOLDEN",
        code="export_tracked_golden",
        category=HUMAN_BLOCKER,
        message="tracked golden exports require deliberate roll-forward approval.",
        next_command=f"{_command(name, '/fig_export')} --force-golden",
        manual=True,
    )
    _append_if(
        fixture_freshness,
        final_artifact in {"MISSING", "INVALID", "STALE", "BLOCKED"},
        code=f"final_artifact_{str(final_artifact).lower()}",
        category=FIXTURE_FRESHNESS,
        message=f"final artifact state is {final_artifact}; resolve it before final release.",
        manual=final_artifact == "BLOCKED",
    )
    _append_if(
        human_blockers,
        acceptance == "NOT_ACCEPTED",
        code="not_accepted",
        category=HUMAN_BLOCKER,
        message="fixture is not accepted; QUALITY_AUDIT.md and accepted state need human action.",
        manual=True,
    )
    release_decision_state = (
        release_decision.get("state") if isinstance(release_decision, Mapping) else None
    )
    release_decision_applies = (
        isinstance(stage, int)
        and stage >= 4
        and acceptance == "NOT_DECLARED"
        and release_ready is False
        and final_ready is False
    )
    _append_if(
        human_blockers,
        release_decision_applies and release_decision_state == "acceptance_authorized",
        code="release_acceptance_decision_recorded",
        category=HUMAN_BLOCKER,
        message=(
            "valid human decision record exists; status is read-only and release-state "
            "mutation still requires the explicit release operation."
        ),
        next_command=release_decision.get("release_operation")
        if isinstance(release_decision, Mapping)
        else None,
        manual=True,
    )
    _append_if(
        human_blockers,
        release_decision_applies and release_decision_state == "non_release_requested",
        code=f"release_deferred_for_{release_decision.get('route', 'non_release')}"
        if isinstance(release_decision, Mapping)
        else "release_deferred_for_non_release",
        category=HUMAN_BLOCKER,
        message=(
            "valid human decision record routes this fixture to non-release work; "
            "release acceptance remains blocked."
        ),
        manual=True,
    )
    _append_if(
        human_blockers,
        release_decision_applies and release_decision_state != "acceptance_authorized"
        and release_decision_state != "non_release_requested",
        code="acceptance_not_declared",
        category=HUMAN_BLOCKER,
        message=(
            "fixture has no accepted or final-ready declaration; release requires "
            "explicit human acceptance or a valid final artifact path."
        ),
        manual=True,
    )
    _append_if(
        human_blockers,
        publication_gate in {"HUMAN_ACCEPTANCE_REQUIRED", "PROVENANCE_REQUIRED"},
        code="publication_gate_required",
        category=HUMAN_BLOCKER,
        message=f"publication gate is {publication_gate}; provenance or acceptance is human-only.",
        manual=True,
    )

    blocking_candidates = [
        *fixture_freshness,
        *human_blockers,
    ]
    first_blocker = (
        blocking_candidates[0]
        if blocking_candidates
        else _entry(
            code="none",
            category=PLUGIN_STATE,
            message="no blocking fixture freshness or human publication gate is visible.",
        )
    )
    buckets = {
        PLUGIN_STATE: plugin_state,
        FIXTURE_FRESHNESS: fixture_freshness,
        "human_blockers": human_blockers,
    }
    return {
        "summary": first_blocker["message"],
        "first_blocker": first_blocker,
        "buckets": {key: buckets[key] for key in _BUCKET_KEYS},
    }
