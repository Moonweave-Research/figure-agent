# scripts/loop/fig_loop_stop_router.py
"""Pure cause -> fix-mode router (Slice 3, data descriptor only — no apply).

Maps a classified sub-region report to a Route dispatch descriptor. Carries the
refusal code STRING for lever_exhausted (candidate_families.py has zero
anti_pattern_id fields; the Hand mapping is a deferred Slice-5 deliverable).
Fix-modes do not act in Slice 3; route_stop_cause never imports a fix-mode
module and never applies anything. action strings are data only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Route:
    cause: str
    fix_mode: str
    action: str | None
    payload: Any
    blocked_by: Any


def route_stop_cause(subregion_report: dict[str, Any]) -> Route:
    cause = str(subregion_report.get("stop_cause") or "")
    if cause == "gate_capped":
        return Route(cause, "gate", "evaluate_gate_lift", None, subregion_report.get("blocked_by"))
    if cause == "lever_exhausted":
        refusal_codes = subregion_report.get("refusal_codes") or []
        if refusal_codes:
            return Route(cause, "hand", "extend_candidate_family", str(refusal_codes[0]), None)
        return Route(cause, "hand", "human_art_direction", None, None)
    if cause == "decision_weak":
        return Route(
            cause,
            "eye",
            "ground_decision_against_reference",
            subregion_report.get("reference_handle"),
            None,
        )
    if cause == "headroom_blind":
        return Route(
            cause, "eye", "raise_critique_ceiling", subregion_report.get("unused_lever_id"), None
        )
    return Route(cause, "none", None, None, None)
