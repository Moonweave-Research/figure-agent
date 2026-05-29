"""Editorial art-direction routing helpers for fig_driver."""

from __future__ import annotations

from typing import Any

ROUTE_HUMAN_GATE = "human_gate"
ROUTE_READY_FOR_SVG_POLISH = "ready_for_svg_polish"
ROUTE_RUN_LOOP = "run_loop"
ROUTE_SEMANTIC_BACKPORT = "semantic_backport"
READINESS_SCHEMA = "figure-agent.svg-polish-readiness.v1"


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def editorial_review_requires_human_gate(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return False
    verdict_counts = summary.get("verdict_counts")
    return (
        summary.get("polish_recommended_path") == "needs_human_art_direction"
        or _positive_int(summary.get("blocking_high_impact_count"))
        or summary.get("worst_verdict") in {"fail", "needs_human"}
        or summary.get("human_art_direction_gate_verdict") in {"fail", "needs_human"}
        or (
            isinstance(verdict_counts, dict)
            and (
                _positive_int(verdict_counts.get("fail"))
                or _positive_int(verdict_counts.get("needs_human"))
            )
        )
    )


def editorial_polish_route(summary: Any) -> str | None:
    if not isinstance(summary, dict):
        return None
    polish_path = summary.get("polish_recommended_path")
    if polish_path == "semantic_backport_required":
        return ROUTE_SEMANTIC_BACKPORT
    if editorial_review_requires_human_gate(summary):
        return ROUTE_HUMAN_GATE
    if polish_path == "continue_tikz":
        return ROUTE_RUN_LOOP
    if polish_path == "ready_for_svg_polish":
        return ROUTE_READY_FOR_SVG_POLISH
    return None


def _verdict_for_readiness(summary: dict[str, Any]) -> str | None:
    for key in (
        "polish_trigger_verdict",
        "human_art_direction_gate_verdict",
        "worst_verdict",
    ):
        value = summary.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _blocking_item(summary: dict[str, Any], recommended_path: str) -> dict[str, Any]:
    item = {
        "source": "editorial_art_direction_summary",
        "id": "tikz_vs_svg_polish_trigger",
        "recommended_path": recommended_path,
    }
    verdict = _verdict_for_readiness(summary)
    if verdict is not None:
        item["verdict"] = verdict
    route_detail = summary.get("polish_route_detail")
    if isinstance(route_detail, str) and route_detail.strip():
        item["route_detail"] = route_detail.strip()
    return item


def _checkpoint_recommended_path(checkpoint: dict[str, Any]) -> str | None:
    editorial_summary = checkpoint.get("editorial_art_direction_summary")
    if not isinstance(editorial_summary, dict):
        return None
    recommended_path = editorial_summary.get("polish_recommended_path")
    if isinstance(recommended_path, str) and recommended_path.strip():
        return recommended_path.strip()
    return None


def _blocking_readiness(
    *,
    recommended_path: str | None,
    next_action: str,
    blocking_reason: str,
    blocking_items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": READINESS_SCHEMA,
        "source": "latest_loop_checkpoint",
        "can_start_svg_polish": False,
        "recommended_path": recommended_path,
        "next_action": next_action,
        "blocking_reason": blocking_reason,
        "blocking_items": blocking_items,
    }


def _loop_source_blocker(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    stop_reason = checkpoint.get("final_stop_reason")
    if not isinstance(stop_reason, str) or not stop_reason.strip():
        return None
    stop_reason = stop_reason.strip()
    if stop_reason == "verify_only_complete":
        return None
    if stop_reason in {
        "crop_audit_uncertain",
        "aesthetic_lever_needs_human",
        "top_tier_audit_required",
    }:
        return None

    next_action_by_stop = {
        "human_gate_required": "human_review",
        "patch_target_recommended": "patch_source",
        "ambiguous_patch_selection": "human_review",
        "status_action_required": "resolve_status_action",
    }
    next_action = next_action_by_stop.get(stop_reason, "run_fig_loop")
    recommended = checkpoint.get("recommended_next_action")
    if isinstance(recommended, str) and recommended.strip():
        reason = (
            f"latest /fig_loop checkpoint requires {next_action.replace('_', ' ')}: "
            f"{recommended.strip()}"
        )
        item = {
            "source": "latest_loop_checkpoint",
            "id": stop_reason,
            "recommended_next_action": recommended.strip(),
        }
    else:
        reason = f"latest /fig_loop checkpoint stopped at {stop_reason}"
        item = {"source": "latest_loop_checkpoint", "id": stop_reason}

    return _blocking_readiness(
        recommended_path=_checkpoint_recommended_path(checkpoint),
        next_action=next_action,
        blocking_reason=reason,
        blocking_items=[item],
    )


def _crop_audit_blocker(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    summary = checkpoint.get("crop_audit_summary")
    if not isinstance(summary, dict) or summary.get("evaluation_state") != "needs_action":
        return None
    crop_ids = summary.get("uncertain_crop_ids")
    if not isinstance(crop_ids, list):
        return None
    blocking_items = [
        {"source": "crop_audit_summary", "id": crop_id}
        for crop_id in crop_ids
        if isinstance(crop_id, str) and crop_id.strip()
    ]
    if not blocking_items:
        return None
    return _blocking_readiness(
        recommended_path=_checkpoint_recommended_path(checkpoint),
        next_action="review_crop_audit",
        blocking_reason="crop audit has uncertain required crop verdicts",
        blocking_items=blocking_items,
    )


def _aesthetic_lever_blocker(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    summary = checkpoint.get("aesthetic_lever_summary")
    if not isinstance(summary, dict) or summary.get("evaluation_state") != "needs_human":
        return None
    bottleneck = summary.get("next_aesthetic_bottleneck")
    lever_id = "aesthetic_lever"
    if isinstance(bottleneck, dict):
        raw_lever_id = bottleneck.get("lever_id")
        if isinstance(raw_lever_id, str) and raw_lever_id.strip():
            lever_id = raw_lever_id.strip()
    return _blocking_readiness(
        recommended_path=_checkpoint_recommended_path(checkpoint),
        next_action="human_art_direction_review",
        blocking_reason="aesthetic lever audit requires human art-direction review",
        blocking_items=[{"source": "aesthetic_lever_summary", "id": lever_id}],
    )


def _top_tier_blocker(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    summary = checkpoint.get("top_tier_audit_summary")
    if not isinstance(summary, dict):
        return None
    verdict_counts = summary.get("verdict_counts")
    blocks = (
        _positive_int(summary.get("blocking_high_impact_count"))
        or summary.get("worst_verdict") in {"fail", "needs_human"}
        or (
            isinstance(verdict_counts, dict)
            and (
                _positive_int(verdict_counts.get("fail"))
                or _positive_int(verdict_counts.get("needs_human"))
            )
        )
    )
    if not blocks:
        return None
    slots = summary.get("blocking_high_impact_slots")
    if not isinstance(slots, list) or not slots:
        slots = summary.get("weak_or_failed_slots")
    if not isinstance(slots, list) or not slots:
        slots = ["top_tier_audit"]
    blocking_items = [
        {"source": "top_tier_audit_summary", "id": slot}
        for slot in slots
        if isinstance(slot, str) and slot.strip()
    ]
    return _blocking_readiness(
        recommended_path=_checkpoint_recommended_path(checkpoint),
        next_action="human_art_direction_review",
        blocking_reason="top-tier audit has human-gated or high-impact-blocking items",
        blocking_items=blocking_items,
    )


def svg_polish_readiness(summary: Any) -> dict[str, Any] | None:
    if not isinstance(summary, dict):
        return None
    recommended_path = summary.get("polish_recommended_path")
    if not isinstance(recommended_path, str):
        return None
    recommended_path = recommended_path.strip()
    if recommended_path == "ready_for_svg_polish":
        route_detail = summary.get("polish_route_detail")
        route_detail = route_detail.strip() if isinstance(route_detail, str) else None
        if editorial_review_requires_human_gate(summary):
            readiness = {
                "schema": READINESS_SCHEMA,
                "source": "editorial_art_direction_summary",
                "can_start_svg_polish": False,
                "recommended_path": recommended_path,
                "next_action": "human_art_direction_review",
                "blocking_reason": (
                    "editorial polish trigger is ready, but editorial review "
                    "still has human-gated or high-impact-blocking items"
                ),
                "blocking_items": [_blocking_item(summary, recommended_path)],
            }
            if route_detail:
                readiness["route_detail"] = route_detail
            return readiness
        readiness = {
            "schema": READINESS_SCHEMA,
            "source": "editorial_art_direction_summary",
            "can_start_svg_polish": True,
            "recommended_path": recommended_path,
            "next_action": "start_svg_polish_recipe",
            "blocking_reason": None,
            "blocking_items": [],
        }
        if route_detail:
            readiness["route_detail"] = route_detail
        return readiness
    if recommended_path == "continue_tikz":
        route_detail = summary.get("polish_route_detail")
        route_detail = route_detail.strip() if isinstance(route_detail, str) else None
        reason = "editorial polish trigger recommends continue_tikz"
        if route_detail:
            reason = f"{reason}: {route_detail}"
        return {
            "schema": READINESS_SCHEMA,
            "source": "editorial_art_direction_summary",
            "can_start_svg_polish": False,
            "recommended_path": recommended_path,
            "next_action": "run_fig_loop",
            "blocking_reason": reason,
            "blocking_items": [_blocking_item(summary, recommended_path)],
        }
    if recommended_path == "semantic_backport_required":
        return {
            "schema": READINESS_SCHEMA,
            "source": "editorial_art_direction_summary",
            "can_start_svg_polish": False,
            "recommended_path": recommended_path,
            "next_action": "semantic_backport",
            "blocking_reason": (
                "editorial polish trigger requires semantic backport before SVG "
                "polish can count"
            ),
            "blocking_items": [_blocking_item(summary, recommended_path)],
        }
    if recommended_path == "needs_human_art_direction":
        return {
            "schema": READINESS_SCHEMA,
            "source": "editorial_art_direction_summary",
            "can_start_svg_polish": False,
            "recommended_path": recommended_path,
            "next_action": "human_art_direction_review",
            "blocking_reason": (
                "editorial polish trigger requires human art-direction review"
            ),
            "blocking_items": [_blocking_item(summary, recommended_path)],
        }
    return None


def svg_polish_readiness_from_checkpoint(
    checkpoint: dict[str, Any],
) -> dict[str, Any] | None:
    for blocker in (
        _crop_audit_blocker(checkpoint),
        _aesthetic_lever_blocker(checkpoint),
        _top_tier_blocker(checkpoint),
        _loop_source_blocker(checkpoint),
    ):
        if blocker is not None:
            return blocker
    existing = checkpoint.get("svg_polish_readiness")
    if isinstance(existing, dict) and existing.get("schema") == READINESS_SCHEMA:
        return existing
    readiness = svg_polish_readiness(checkpoint.get("editorial_art_direction_summary"))
    if readiness is None:
        return None
    readiness = dict(readiness)
    readiness["source"] = "latest_loop_checkpoint"
    return readiness
