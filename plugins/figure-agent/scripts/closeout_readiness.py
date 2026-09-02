"""Compact closeout readiness checklist preserving existing closeout gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import evidence_index
import fixture_identity
import publication_gate
import runtime_paths
import status_readiness_policy

SCHEMA = "figure-agent.closeout-readiness.v1"
# The release-gate checks below are computed here rather than by closeout, and
# belong after the source/export steps and before the derived rerun/contract
# steps that depend on them.
_GATE_CHECKS_AFTER_STEP_ID = "export"
ACCEPTED_BUT_STALE_REASON = (
    "accepted_but_stale: fixture has an accepted historical state, but current "
    "source, render, critique, or export evidence is stale. Re-run "
    "compile/critique/export and refresh acceptance before closeout."
)
ACCEPTED_BUT_UNATTESTED_REASON = (
    "accepted_but_unattested: the accepted declaration is not bound to the current "
    "source; the human attestation hash no longer matches. Re-run fig-agent attest "
    "from a terminal (or re-open the acceptance) before closeout."
)


class CloseoutReadinessError(ValueError):
    """Raised when closeout readiness cannot be computed."""


def _compute_closeout(name: str, *, repo_root: Path, runs_root: Path | None) -> dict[str, Any]:
    import fig_closeout

    return fig_closeout.compute_closeout(name, repo_root=repo_root, runs_root=runs_root)


def _required_step_ids() -> tuple[str, ...]:
    import fig_closeout

    return fig_closeout.REQUIRED_CLOSEOUT_STEP_IDS


def _check(
    *,
    check_id: str,
    state: str,
    reason: str,
    command: str | None = None,
    evidence_path: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "state": state,
        "reason": reason,
        "command": command,
        "evidence_path": evidence_path,
        "evidence": evidence or {},
    }


def _candidate_apply_check(index: dict[str, Any]) -> dict[str, Any]:
    candidate = index.get("candidate")
    if candidate is None:
        return _check(
            check_id="candidate_apply",
            state="not_required",
            reason="no candidate apply evidence is present",
        )
    apply_status = candidate.get("apply_status")
    apply_path = candidate.get("apply_result_path")
    if apply_status is None:
        return _check(
            check_id="candidate_apply",
            state="not_required",
            reason="candidate has not been applied",
            evidence_path=apply_path,
        )
    if apply_status == "applied":
        post_apply = candidate.get("post_apply") if isinstance(candidate, dict) else {}
        required = ("compile", "export", "status")
        missing = [
            stage
            for stage in required
            if not isinstance(post_apply, dict) or stage not in post_apply
        ]
        if missing:
            return _check(
                check_id="candidate_apply",
                state="blocked",
                reason=f"candidate post-apply checks missing: {', '.join(missing)}",
                evidence_path=apply_path,
                evidence={"post_apply": post_apply if isinstance(post_apply, dict) else {}},
            )
        failed = [stage for stage, status in (post_apply or {}).items() if status != "success"]
        if failed:
            return _check(
                check_id="candidate_apply",
                state="blocked",
                reason=f"candidate post-apply checks failed: {', '.join(failed)}",
                evidence_path=apply_path,
                evidence={"post_apply": post_apply},
            )
        return _check(
            check_id="candidate_apply",
            state="passed",
            reason="latest candidate apply result is applied and post-apply checks passed",
            evidence_path=apply_path,
            evidence={"post_apply": post_apply},
        )
    if apply_status == "applied_unverified":
        required_commands = candidate.get("required_commands")
        return _check(
            check_id="candidate_apply",
            state="blocked",
            reason="candidate apply verification has not run",
            evidence_path=apply_path,
            evidence={
                "required_commands": required_commands
                if isinstance(required_commands, list)
                else [],
            },
        )
    if apply_status == "stale":
        return _check(
            check_id="candidate_apply",
            state="blocked",
            reason="candidate apply result is stale against current source",
            evidence_path=apply_path,
        )
    return _check(
        check_id="candidate_apply",
        state="blocked",
        reason=f"candidate apply status is {apply_status}",
        evidence_path=apply_path,
    )


def _accepted_state_check(status: dict[str, Any]) -> dict[str, Any]:
    freshness_state = status.get("acceptance_freshness_state")
    evidence = {
        "acceptance_state": status.get("acceptance_state"),
        "acceptance_freshness_state": freshness_state,
        "workflow_ready": bool(status.get("workflow_ready")),
    }
    if freshness_state in status_readiness_policy.ACCEPTANCE_FRESHNESS_BLOCKING_STATES:
        return _check(
            check_id="accepted_state",
            state="blocked",
            reason=(
                ACCEPTED_BUT_STALE_REASON
                if freshness_state == "accepted_but_stale"
                else ACCEPTED_BUT_UNATTESTED_REASON
            ),
            evidence=evidence,
        )
    return _check(
        check_id="accepted_state",
        state="passed" if status.get("acceptance_state") == "ACCEPTED" else "not_required",
        reason=f"acceptance_freshness_state is {freshness_state or 'not reported'}",
        evidence=evidence,
    )


def _mapped_closeout_checks(closeout: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for step in closeout.get("steps", []):
        if not isinstance(step, dict):
            continue
        checks.append(
            _check(
                check_id=str(step.get("id") or "unknown"),
                state=str(step.get("state") or "blocked"),
                reason=str(step.get("reason") or ""),
                command=step.get("command") if isinstance(step.get("command"), str) else None,
                evidence_path=step.get("evidence_path")
                if isinstance(step.get("evidence_path"), str)
                else None,
                evidence=step.get("evidence") if isinstance(step.get("evidence"), dict) else {},
            )
        )
    return checks


def _checks_by_id(checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(check.get("id") or ""): check for check in checks}


def _golden_acceptance_check(
    *,
    status: dict[str, Any],
    closeout_checks: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if status.get("export_state") != "TRACKED_GOLDEN":
        return _check(
            check_id="golden_acceptance",
            state="not_required",
            reason="export_state is not TRACKED_GOLDEN",
        )
    export_check = closeout_checks.get("export", {})
    golden_acceptance = (
        export_check.get("evidence", {}).get("golden_acceptance")
        if isinstance(export_check.get("evidence"), dict)
        else None
    )
    if export_check.get("state") == "passed":
        return _check(
            check_id="golden_acceptance",
            state="passed",
            reason="current golden acceptance covers tracked golden export",
            evidence=golden_acceptance if isinstance(golden_acceptance, dict) else {},
        )
    return _check(
        check_id="golden_acceptance",
        state="blocked",
        reason="tracked golden export requires current golden acceptance",
        evidence=golden_acceptance if isinstance(golden_acceptance, dict) else {},
    )


# Final-artifact states that are release-safe. Mirrors the release-ready policy in
# status_readiness_policy, which treats only these as non-blocking. Any other value
# — the known-bad states AND any unrecognized string — blocks (known-good allowlist).
_KNOWN_GOOD_FINAL_ARTIFACT_STATES = frozenset({"NONE", "FRESH"})


def _final_artifact_check(status: dict[str, Any]) -> dict[str, Any]:
    state = status.get("final_artifact_state")
    kind = status.get("final_artifact_kind")
    path = status.get("final_artifact_path")
    evidence = {
        "final_artifact_state": state,
        "final_artifact_kind": kind,
        "final_artifact_path": path,
    }
    evidence_path = path if isinstance(path, str) else None
    if not state:
        return _check(
            check_id="final_artifact",
            state="not_required",
            reason="final_artifact_state is not reported",
            evidence_path=evidence_path,
            evidence=evidence,
        )
    if state in _KNOWN_GOOD_FINAL_ARTIFACT_STATES:
        return _check(
            check_id="final_artifact",
            state="passed",
            reason=f"final_artifact_state is {state}",
            evidence_path=evidence_path,
            evidence=evidence,
        )
    return _check(
        check_id="final_artifact",
        state="blocked",
        reason=f"final_artifact_state is {state}",
        evidence_path=evidence_path,
        evidence=evidence,
    )


def _release_check(status: dict[str, Any]) -> dict[str, Any]:
    failures = status.get("publication_gate_failures")
    failures_list = failures if isinstance(failures, list) else []
    publication_state = status.get("publication_gate_state")
    evidence = {
        "release_ready": bool(status.get("release_ready")),
        "final_ready": bool(status.get("final_ready")),
        "publication_gate_state": publication_state,
        "publication_gate_failures": failures_list,
    }
    if failures_list or not isinstance(failures, list):
        reason = (
            f"publication gate reports {len(failures_list)} failure(s)"
            if failures_list
            else "publication gate not evaluated (publication_gate_failures absent)"
        )
        return _check(
            check_id="release",
            state="blocked",
            reason=reason,
            evidence=evidence,
        )
    # An empty failure list is only meaningful when the gate actually ran and
    # passed. NOT_APPLICABLE means `accepted` was never declared — release
    # readiness cannot be inferred from a gate that never evaluated.
    if publication_state == publication_gate.PUBLICATION_GATE_PASS:
        return _check(
            check_id="release",
            state="passed",
            reason="publication gate passed",
            evidence=evidence,
        )
    if publication_state == publication_gate.PUBLICATION_GATE_NOT_APPLICABLE:
        return _check(
            check_id="release",
            state="blocked",
            reason="publication gate not evaluated (accepted is not declared)",
            evidence=evidence,
        )
    return _check(
        check_id="release",
        state="blocked",
        reason=f"publication gate state is {publication_state or 'not reported'}",
        evidence=evidence,
    )


def _missing_step_check(step_id: str) -> dict[str, Any]:
    return _check(
        check_id=step_id,
        state="blocked",
        reason=f"closeout did not emit required step {step_id}",
        evidence={"missing_step": step_id},
    )


def _ordered_checks(
    candidate_check: dict[str, Any],
    closeout_checks: list[dict[str, Any]],
    status: dict[str, Any],
) -> list[dict[str, Any]]:
    closeout_by_id = _checks_by_id(closeout_checks)
    required_ids = _required_step_ids()
    split = required_ids.index(_GATE_CHECKS_AFTER_STEP_ID) + 1
    checks = [candidate_check]
    checks.extend(
        closeout_by_id.get(step_id) or _missing_step_check(step_id)
        for step_id in required_ids[:split]
    )
    checks.append(_golden_acceptance_check(status=status, closeout_checks=closeout_by_id))
    checks.append(_accepted_state_check(status))
    checks.append(_final_artifact_check(status))
    checks.append(_release_check(status))
    checks.extend(
        closeout_by_id.get(step_id) or _missing_step_check(step_id)
        for step_id in required_ids[split:]
    )
    return checks


def build_closeout_readiness(
    name: str,
    *,
    candidate_id: str | None = None,
    candidate_set_path: Path | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    runs_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    index = evidence_index.build_evidence_index(
        name,
        candidate_id=candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    closeout = _compute_closeout(
        name,
        repo_root=paths.workspace_root,
        runs_root=runs_root,
    )
    status_payload = closeout.get("status", {}) if isinstance(closeout.get("status"), dict) else {}
    checks = _ordered_checks(
        _candidate_apply_check(index),
        _mapped_closeout_checks(closeout),
        status_payload,
    )
    incomplete = [check for check in checks if check["state"] not in {"passed", "not_required"}]
    next_check = next((check for check in checks if check["state"] == "needs_action"), None)
    if next_check is None:
        next_check = next((check for check in checks if check["state"] == "blocked"), None)
    return {
        "schema": SCHEMA,
        "figure_name": name,
        "status": "ready" if not incomplete else "blocked",
        "checks": checks,
        "next_action": next_check["command"] or next_check["reason"]
        if next_check
        else "closeout ready",
        "evidence_index_path": "build/evidence/evidence_index.json",
        "evidence_index": index,
        "closeout": {
            "schema": closeout.get("schema"),
            "closeout_complete": bool(closeout.get("closeout_complete")),
            "blocking_step_ids": closeout.get("blocking_step_ids", []),
            "status": closeout.get("status", {}),
        },
    }
