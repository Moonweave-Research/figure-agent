"""Editorial art-direction routing helpers for fig_driver."""

from __future__ import annotations

from typing import Any

ROUTE_HUMAN_GATE = "human_gate"
ROUTE_READY_FOR_SVG_POLISH = "ready_for_svg_polish"
ROUTE_RUN_LOOP = "run_loop"
ROUTE_SEMANTIC_BACKPORT = "semantic_backport"


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
