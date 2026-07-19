"""Explicit visually-re-reviewed to development-accepted verdict adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_post_review_authority as authority
import human_decision_record
import repair_transaction

ACTION = "closed_loop_development_verdict"
STOP_BOUNDARY = "workflow_agent"


class ClosedLoopDevelopmentVerdictError(ValueError):
    """Raised when an explicit development verdict is not current and bound."""


def _load_verdict(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        content = path.read_bytes()
        payload = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopDevelopmentVerdictError("development_verdict_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopDevelopmentVerdictError("development_verdict_invalid")
    return payload, content


def _assert_current_state(
    state: dict[str, Any],
    state_path: Path,
    *,
    workspace_root: Path,
) -> None:
    projection = closed_loop_current_state.resolve_current_attempt(
        workspace_root,
        state["fixture"],
    )
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != "visually_re_reviewed"
        or projection.get("required_actor") != "human_reviewer"
        or projection.get("terminal") is not False
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path")
        != state_path.relative_to(workspace_root).as_posix()
        or projection.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopDevelopmentVerdictError(
            "closed_loop_canonical_current_state_drift"
        )


def _validated_plan(
    fixture: str,
    *,
    state_path: Path,
    verdict_path: Path,
    workspace_root: Path,
    expected_state_sha256: str | None,
) -> dict[str, Any]:
    state, published_state_path = authority.load_published_state(
        workspace_root=workspace_root,
        fixture=fixture,
        state_path=state_path,
    )
    if state["state"] != "visually_re_reviewed":
        raise ClosedLoopDevelopmentVerdictError(
            "closed_loop_state_not_visually_re_reviewed"
        )
    if (
        expected_state_sha256 is not None
        and state["state_sha256"] != expected_state_sha256
    ):
        raise ClosedLoopDevelopmentVerdictError(
            "closed_loop_projected_state_hash_mismatch"
        )
    verdict_path = authority.workspace_file(
        workspace_root,
        verdict_path,
        label="development_verdict",
    )
    if verdict_path.parent != published_state_path.parent:
        raise ClosedLoopDevelopmentVerdictError(
            "development_verdict_and_state_must_be_adjacent"
        )
    verdict, verdict_bytes = _load_verdict(verdict_path)
    normalized = human_decision_record.validate_development_verdict(
        verdict,
        fixture=fixture,
        attempt_id=state["attempt_id"],
        state_path=published_state_path.relative_to(workspace_root).as_posix(),
        state_sha256=state["state_sha256"],
    )
    return {
        "state": state,
        "state_path": published_state_path,
        "verdict_path": verdict_path,
        "verdict_bytes": verdict_bytes,
        "reviewer": normalized["reviewer"],
        "decision_kind": normalized["decision_kind"],
        "next_state": normalized["next_state"],
        "evidence_role": normalized["evidence_role"],
        "next_state_path": published_state_path.parent
        / f"state-{state['sequence'] + 1:03d}-{normalized['next_state']}.json",
    }


def _expected_terminal_state(
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    return closed_loop_attempt_state.transition_state(
        plan["state"],
        next_state=str(plan["next_state"]),
        actor=str(plan["reviewer"]),
        actor_role="human_reviewer",
        evidence={str(plan["evidence_role"]): plan["verdict_path"]},
        workspace_root=workspace_root,
        previous_state_path=plan["state_path"],
    )


def _matching_published_verdict(
    fixture: str,
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any] | None:
    next_state_path = plan["next_state_path"]
    if not next_state_path.exists() and not next_state_path.is_symlink():
        return None
    try:
        published, published_path = authority.load_published_state(
            workspace_root=workspace_root,
            fixture=fixture,
            state_path=next_state_path,
        )
        expected = _expected_terminal_state(plan, workspace_root=workspace_root)
    except (
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopDevelopmentVerdictError(
            f"development_verdict_recovery_invalid:{exc}"
        ) from exc
    if published_path != next_state_path or published != expected:
        raise ClosedLoopDevelopmentVerdictError(
            "development_verdict_state_conflict"
        )
    projection = closed_loop_current_state.resolve_current_attempt(
        workspace_root,
        fixture,
    )
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != plan["next_state"]
        or projection.get("required_actor") != "none"
        or projection.get("terminal") is not True
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path")
        != published_path.relative_to(workspace_root).as_posix()
        or projection.get("state_sha256") != published["state_sha256"]
    ):
        raise ClosedLoopDevelopmentVerdictError(
            "closed_loop_canonical_current_state_drift"
        )
    return published


def _recovered_result(plan: dict[str, Any], published: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": ACTION,
        "stop_boundary": "none",
        "stop_reason": f"{plan['next_state']}_recovered",
        "required_actor": "none",
        "created": False,
        "input_state": plan["state"],
        "input_state_path": plan["state_path"],
        "next_state": plan["next_state"],
        "next_state_path": plan["next_state_path"],
        "verdict_path": plan["verdict_path"],
        "reviewer": plan["reviewer"],
        "decision_kind": plan["decision_kind"],
        "evidence_role": plan["evidence_role"],
        "published_state": published,
        "publication_acceptance": "not_claimed",
    }


def _matching_or_assert_current(
    fixture: str,
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any] | None:
    published = _matching_published_verdict(
        fixture,
        plan,
        workspace_root=workspace_root,
    )
    if published is not None:
        return published
    try:
        _assert_current_state(
            plan["state"],
            plan["state_path"],
            workspace_root=workspace_root,
        )
    except ClosedLoopDevelopmentVerdictError as exc:
        if str(exc) != "closed_loop_canonical_current_state_drift":
            raise
        published = _matching_published_verdict(
            fixture,
            plan,
            workspace_root=workspace_root,
        )
        if published is not None:
            return published
        raise
    return None


def run_development_verdict(
    fixture: str,
    *,
    state_path: Path,
    verdict_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate or publish one explicit terminal development verdict."""
    root = Path(os.path.abspath(workspace_root))
    try:
        plan = _validated_plan(
            fixture,
            state_path=state_path,
            verdict_path=verdict_path,
            workspace_root=root,
            expected_state_sha256=expected_state_sha256,
        )
        if not execute:
            published = _matching_or_assert_current(
                fixture,
                plan,
                workspace_root=root,
            )
            if published is not None:
                return _recovered_result(plan, published)
            return {
                "action": ACTION,
                "stop_boundary": STOP_BOUNDARY,
                "stop_reason": "plan_only",
                "required_actor": "workflow_agent",
                "created": False,
                "input_state": plan["state"],
                "input_state_path": plan["state_path"],
                "next_state": plan["next_state"],
                "next_state_path": plan["next_state_path"],
                "verdict_path": plan["verdict_path"],
                "reviewer": plan["reviewer"],
                "decision_kind": plan["decision_kind"],
                "evidence_role": plan["evidence_role"],
                "publication_acceptance": "not_claimed",
            }

        with closed_loop_attempt_state.attempt_transition_lock(
            plan["state_path"].parent
        ):
            current = _validated_plan(
                fixture,
                state_path=state_path,
                verdict_path=verdict_path,
                workspace_root=root,
                expected_state_sha256=expected_state_sha256,
            )
            published = _matching_or_assert_current(
                fixture,
                current,
                workspace_root=root,
            )
            if published is not None:
                return _recovered_result(current, published)
            if current["verdict_bytes"] != plan["verdict_bytes"]:
                raise ClosedLoopDevelopmentVerdictError(
                    "development_verdict_inputs_drifted"
                )
            next_state = _expected_terminal_state(
                current,
                workspace_root=root,
            )
            next_state_path = closed_loop_attempt_state.publish_state(
                next_state,
                workspace_root=root,
            )
        return {
            "action": ACTION,
            "stop_boundary": "none",
            "stop_reason": current["next_state"],
            "required_actor": "none",
            "created": True,
            "input_state": current["state"],
            "input_state_path": current["state_path"],
            "next_state": current["next_state"],
            "next_state_path": next_state_path,
            "verdict_path": current["verdict_path"],
            "reviewer": current["reviewer"],
            "decision_kind": current["decision_kind"],
            "evidence_role": current["evidence_role"],
            "published_state": next_state,
            "publication_acceptance": "not_claimed",
        }
    except ClosedLoopDevelopmentVerdictError:
        raise
    except (
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        human_decision_record.HumanDecisionRecordError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopDevelopmentVerdictError(
            f"development_verdict_failed:{exc}"
        ) from exc
