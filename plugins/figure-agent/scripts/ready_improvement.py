"""Read-only optional improvement discovery for ready figure states."""

from __future__ import annotations

from typing import Any

SCHEMA = "figure-agent.ready-improvement-summary.v1"

ACTION_COMPLETE = "complete"
ACTION_RELEASE_BLOCKED = "release_blocked"
ACTION_HUMAN_GATE_STOP = "human_gate_stop"
ACTION_PATCH_HANDOFF_STOP = "patch_handoff_stop"
ACTION_POLISH_HANDOFF_STOP = "polish_handoff_stop"

STOP_ACCEPTED_OR_FINAL_READY = "accepted_or_final_ready_required"
STOP_FORCE_GOLDEN = "force_golden_required"
STOP_HUMAN_GATE = "human_gate_required"
STOP_PATCH_HANDOFF = "patch_handoff_required"
STOP_AMBIGUOUS_PATCH = "ambiguous_patch_selection"
STOP_SEMANTIC_BACKPORT = "semantic_backport_required"

READY_LOOP_STOPS = {"verify_only_complete", "no_actionable_findings"}
READY_MANUAL_STOPS = {STOP_ACCEPTED_OR_FINAL_READY, STOP_FORCE_GOLDEN}
BLOCKING_ACTIONS = {
    ACTION_HUMAN_GATE_STOP,
    ACTION_PATCH_HANDOFF_STOP,
    ACTION_POLISH_HANDOFF_STOP,
}
BLOCKING_STOPS = {
    STOP_HUMAN_GATE,
    STOP_PATCH_HANDOFF,
    STOP_AMBIGUOUS_PATCH,
    STOP_SEMANTIC_BACKPORT,
}


def _non_empty_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _summary_base(*, state: str, safe_to_ship: bool) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "source": "latest_loop_checkpoint",
        "state": state,
        "safe_to_ship": safe_to_ship,
        "blocks_release": False,
        "auto_patch_allowed": False,
        "candidate_count": 0,
        "candidates": [],
    }


def _loop_checkpoint_is_ready(loop_checkpoint: dict[str, Any]) -> bool:
    stop_reason = _non_empty_string(loop_checkpoint.get("final_stop_reason"))
    if stop_reason in READY_LOOP_STOPS:
        return True
    next_action = _non_empty_string(loop_checkpoint.get("recommended_next_action"))
    return stop_reason == "status_action_required" and "--force-golden" in str(next_action)


def _has_blocking_shape(
    *,
    action: str,
    stop_boundary: str | None,
    loop_checkpoint: dict[str, Any],
) -> bool:
    if action in BLOCKING_ACTIONS:
        return True
    if stop_boundary in BLOCKING_STOPS:
        return True
    stop_reason = _non_empty_string(loop_checkpoint.get("final_stop_reason"))
    if stop_reason in {
        "human_gate_required",
        "patch_target_recommended",
        "active_subregion_recommended",
        "ambiguous_patch_selection",
        "semantic_backport_required",
    }:
        return True
    escalation = _non_empty_string(loop_checkpoint.get("escalation_level"))
    return escalation in {"human_review_required", "ambiguous_patch_selection"}


def _verdict_counts_block(verdict_counts: Any) -> bool:
    return isinstance(verdict_counts, dict) and (
        _positive_int(verdict_counts.get("fail"))
        or _positive_int(verdict_counts.get("needs_human"))
    )


def _loop_audits_have_blockers(loop_checkpoint: dict[str, Any]) -> bool:
    top_tier = loop_checkpoint.get("top_tier_audit_summary")
    if isinstance(top_tier, dict) and (
        _positive_int(top_tier.get("blocking_high_impact_count"))
        or top_tier.get("worst_verdict") in {"fail", "needs_human"}
        or _verdict_counts_block(top_tier.get("verdict_counts"))
    ):
        return True

    editorial = loop_checkpoint.get("editorial_art_direction_summary")
    if isinstance(editorial, dict) and (
        _positive_int(editorial.get("blocking_high_impact_count"))
        or editorial.get("polish_recommended_path") == "needs_human_art_direction"
        or editorial.get("worst_verdict") in {"fail", "needs_human"}
        or editorial.get("human_art_direction_gate_verdict") in {"fail", "needs_human"}
        or _verdict_counts_block(editorial.get("verdict_counts"))
    ):
        return True

    crop_audit = loop_checkpoint.get("crop_audit_summary")
    if isinstance(crop_audit, dict) and crop_audit.get("evaluation_state") == "needs_action":
        return True

    aesthetic = loop_checkpoint.get("aesthetic_lever_summary")
    if isinstance(aesthetic, dict) and aesthetic.get("evaluation_state") in {
        "blocked",
        "needs_human",
    }:
        return True

    journal_playbook = loop_checkpoint.get("journal_art_direction_playbook_summary")
    return isinstance(journal_playbook, dict) and journal_playbook.get(
        "evaluation_state"
    ) in {"blocked", "needs_human"}


def _safe_to_ship(
    *,
    status: dict[str, Any],
    action: str,
    stop_boundary: str | None,
    loop_checkpoint: dict[str, Any],
) -> bool:
    if _has_blocking_shape(
        action=action,
        stop_boundary=stop_boundary,
        loop_checkpoint=loop_checkpoint,
    ) or _loop_audits_have_blockers(loop_checkpoint):
        return False
    if action == ACTION_COMPLETE and stop_boundary is None:
        return True
    if action == ACTION_RELEASE_BLOCKED and stop_boundary in READY_MANUAL_STOPS:
        return True
    return status.get("release_ready") is True or status.get("final_ready") is True


def _candidate(
    *,
    source: str,
    source_id: str,
    kind: str,
    target: str,
    suggested_action: str,
    expected_gain: str,
    risk: str,
    required_actor: str,
    allowed_scope: list[str],
    reason: str,
) -> dict[str, Any]:
    return {
        "source": source,
        "source_id": source_id,
        "type": kind,
        "target": target,
        "suggested_action": suggested_action,
        "expected_gain": expected_gain,
        "risk": risk,
        "required_actor": required_actor,
        "allowed_scope": allowed_scope,
        "reason": reason,
    }


def _editorial_candidates(
    fixture: str,
    loop_checkpoint: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = loop_checkpoint.get("editorial_art_direction_summary")
    if not isinstance(summary, dict):
        return []
    if _verdict_counts_block(summary.get("verdict_counts")):
        return []
    if _positive_int(summary.get("blocking_high_impact_count")):
        return []
    if summary.get("worst_verdict") in {"fail", "needs_human"}:
        return []
    if summary.get("human_art_direction_gate_verdict") in {"fail", "needs_human"}:
        return []

    recommended_path = _non_empty_string(summary.get("polish_recommended_path"))
    detail = _non_empty_string(summary.get("polish_route_detail"))
    if recommended_path == "continue_tikz" and detail is not None:
        return [
            _candidate(
                source="editorial_art_direction_summary",
                source_id="tikz_vs_svg_polish_trigger",
                kind="tikz_micro_polish",
                target="remaining TikZ polish lever",
                suggested_action=(
                    "Review the structured route detail and patch one "
                    "source-level micro-polish target only if desired."
                ),
                expected_gain="low",
                risk="low",
                required_actor="workflow_agent",
                allowed_scope=[f"examples/{fixture}/{fixture}.tex"],
                reason=detail,
            )
        ]
    if recommended_path == "ready_for_svg_polish":
        reason = detail or "latest loop checkpoint routes optional SVG polish"
        return [
            _candidate(
                source="editorial_art_direction_summary",
                source_id="tikz_vs_svg_polish_trigger",
                kind="svg_polish",
                target="SVG polish handoff",
                suggested_action=(
                    "Use polish mode to check the existing SVG polish gate; "
                    "do not edit SVG unless that gate is ready."
                ),
                expected_gain="medium",
                risk="medium",
                required_actor="svg_editor",
                allowed_scope=[f"examples/{fixture}/polish/"],
                reason=reason,
            )
        ]
    return []


def _top_tier_candidates(loop_checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    summary = loop_checkpoint.get("top_tier_audit_summary")
    if not isinstance(summary, dict):
        return []
    if _verdict_counts_block(summary.get("verdict_counts")):
        return []
    if _positive_int(summary.get("blocking_high_impact_count")):
        return []
    if summary.get("worst_verdict") in {"fail", "needs_human"}:
        return []
    slots = summary.get("weak_or_failed_slots")
    if not isinstance(slots, list):
        return []
    candidates = []
    for slot in slots:
        source_id = _non_empty_string(slot)
        if source_id is None:
            continue
        candidates.append(
            _candidate(
                source="top_tier_audit_summary",
                source_id=source_id,
                kind="human_art_direction",
                target=source_id.replace("_", " "),
                suggested_action=(
                    "Review this non-blocking top-tier audit slot and decide "
                    "whether a small polish pass is worth the time."
                ),
                expected_gain="medium",
                risk="medium",
                required_actor="human_art_direction",
                allowed_scope=[],
                reason=f"top-tier audit slot {source_id} is weak but non-blocking",
            )
        )
    return candidates


def _aesthetic_candidate_type(route: str | None) -> tuple[str, str, str, list[str]]:
    if route == "svg_polish":
        return ("svg_polish", "medium", "svg_editor", ["polish/"])
    if route == "human_art_direction":
        return ("human_art_direction", "needs_human", "human_art_direction", [])
    if route == "accept_simplification":
        return ("accept_simplification_review", "low", "human_art_direction", [])
    return ("tikz_micro_polish", "low", "workflow_agent", ["<fixture>.tex"])


def _allowed_scope_from_template(fixture: str, scope_template: list[str]) -> list[str]:
    return [
        f"examples/{fixture}/{fixture}.tex"
        if item == "<fixture>.tex"
        else f"examples/{fixture}/{item}"
        for item in scope_template
    ]


def _aesthetic_lever_candidates(
    fixture: str,
    loop_checkpoint: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = loop_checkpoint.get("aesthetic_lever_summary")
    if not isinstance(summary, dict):
        return []
    if summary.get("evaluation_state") in {"needs_human", "blocked"}:
        return []
    if summary.get("evaluation_state") != "needs_patch":
        return []
    bottleneck = summary.get("next_aesthetic_bottleneck")
    if not isinstance(bottleneck, dict):
        return []
    lever_id = _non_empty_string(bottleneck.get("lever_id"))
    if lever_id is None:
        return []
    route = _non_empty_string(bottleneck.get("route"))
    kind, risk, actor, scope_template = _aesthetic_candidate_type(route)
    allowed_scope = _allowed_scope_from_template(fixture, scope_template)
    dimension = _non_empty_string(bottleneck.get("dimension")) or "aesthetic lever"
    return [
        _candidate(
            source="aesthetic_lever_summary",
            source_id=lever_id,
            kind=kind,
            target=dimension.replace("_", " "),
            suggested_action=(
                "Address exactly this weak aesthetic lever only if the "
                "operator wants another polish pass."
            ),
            expected_gain="medium" if risk != "low" else "low",
            risk=risk,
            required_actor=actor,
            allowed_scope=allowed_scope,
            reason=f"aesthetic lever {lever_id} remains weak via route {route or 'unknown'}",
        )
    ]


def _journal_playbook_candidates(
    fixture: str,
    loop_checkpoint: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = loop_checkpoint.get("journal_art_direction_playbook_summary")
    if not isinstance(summary, dict):
        return []
    if summary.get("evaluation_state") in {"needs_human", "blocked"}:
        return []
    if summary.get("evaluation_state") != "needs_patch":
        return []
    bottleneck = summary.get("next_journal_art_direction_bottleneck")
    if not isinstance(bottleneck, dict):
        return []
    item_id = _non_empty_string(bottleneck.get("id"))
    if item_id is None:
        return []
    route = _non_empty_string(bottleneck.get("route"))
    kind, risk, actor, scope_template = _aesthetic_candidate_type(route)
    allowed_scope = _allowed_scope_from_template(fixture, scope_template)
    return [
        _candidate(
            source="journal_art_direction_playbook_summary",
            source_id=item_id,
            kind=kind,
            target=item_id.replace("_", " "),
            suggested_action=(
                "Review this weak journal-playbook item as optional polish; "
                "do not treat it as a release blocker."
            ),
            expected_gain="medium",
            risk=risk,
            required_actor=actor,
            allowed_scope=allowed_scope,
            reason=f"journal playbook item {item_id} remains weak via route {route or 'unknown'}",
        )
    ]


def _with_stable_ids(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stable = sorted(
        candidates,
        key=lambda item: (
            str(item.get("source", "")),
            str(item.get("source_id", "")),
            str(item.get("type", "")),
        ),
    )
    for index, candidate in enumerate(stable, start=1):
        candidate["id"] = f"I{index:03d}"
    return stable


def build_ready_improvement_summary(
    *,
    fixture: str,
    status: dict[str, Any],
    action: str,
    stop_boundary: str | None,
    loop_checkpoint: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build an advisory improvement summary from structured loop evidence."""
    if loop_checkpoint is None:
        return None

    safe_to_ship = _safe_to_ship(
        status=status,
        action=action,
        stop_boundary=stop_boundary,
        loop_checkpoint=loop_checkpoint,
    )
    if not safe_to_ship or not _loop_checkpoint_is_ready(loop_checkpoint):
        return _summary_base(state="not_ready", safe_to_ship=False)

    candidates = []
    candidates.extend(_editorial_candidates(fixture, loop_checkpoint))
    candidates.extend(_top_tier_candidates(loop_checkpoint))
    candidates.extend(_aesthetic_lever_candidates(fixture, loop_checkpoint))
    candidates.extend(_journal_playbook_candidates(fixture, loop_checkpoint))
    candidates = _with_stable_ids(candidates)

    state = "ready_but_improvable" if candidates else "ready_no_actionable_improvement"
    summary = _summary_base(state=state, safe_to_ship=True)
    summary["candidate_count"] = len(candidates)
    summary["candidates"] = candidates
    return summary
