"""Explicit human acceptance for closeout/golden roll-forward."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import closeout_readiness
import evidence_hash
import fixture_identity
import git_tracked
import human_decision_record
import publication_gate
import runtime_paths

SCHEMA = "figure-agent.golden-acceptance.v1"
DECISIONS = {"accept", "reject", "defer"}


class GoldenAcceptanceError(ValueError):
    """Raised when closeout/golden acceptance is not allowed."""


def _sha256_fixture_file(path: Path, label: str) -> str | None:
    if path.is_symlink():
        raise GoldenAcceptanceError(f"sandbox_symlink_forbidden: {label}")
    return evidence_hash.sha256_file(path) if path.is_file() else None


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def _packet_moment(timestamp: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _authorizing_decision_record(name: str, plugin_root: Path) -> dict[str, str] | None:
    """Return the newest decision record that authorizes this release, if any.

    The record says "accept_current_generated_export", but nothing in it pins
    which export was current when a human signed it, so the acceptance names
    the authorization it rode: an accept riding a months-old decision is then
    legible in the receipt instead of indistinguishable from a fresh one.
    `write_golden_acceptance` uses that timestamp to refuse an accept of a
    changed export under an older authorization.

    Two requirements make the record evidence rather than a formality. It must
    be committed, because an agent that can write a JSON file could otherwise
    author its own authorization; git being unavailable fails closed here. And
    the newest one wins: `sorted(glob(...))` returned the lexicographically
    first, which under date-prefixed directories is the oldest.
    """
    records_root = plugin_root / "docs" / "decision-records"
    if not records_root.is_dir():
        return None
    authorizations: list[tuple[datetime, str, dict[str, str]]] = []
    for path in sorted(records_root.glob("**/*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            record = human_decision_record.validate_decision_record(raw)
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            human_decision_record.HumanDecisionRecordError,
        ):
            continue
        if (
            record.get("fixture") == name
            and record.get("packet_schema") == human_decision_record.RELEASE_DECISION_PACKET_SCHEMA
            and record.get("decision_kind") == "accept_current_generated_export"
            and git_tracked.is_tracked(path, plugin_root)
        ):
            timestamp = str(record.get("packet_timestamp") or "")
            authorizations.append(
                (
                    _packet_moment(timestamp) or datetime.min.replace(tzinfo=UTC),
                    path.as_posix(),
                    {
                        "path": path.relative_to(plugin_root).as_posix(),
                        "sha256": evidence_hash.sha256_file(path),
                        "packet_timestamp": timestamp,
                        "queue_run_id": str(record.get("queue_run_id") or ""),
                    },
                )
            )
    if not authorizations:
        return None
    return max(authorizations, key=lambda entry: (entry[0], entry[1]))[2]


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise GoldenAcceptanceError("path_escape") from exc


def _ensure_safe_write_target(example_dir: Path, output: Path) -> None:
    build_dir = example_dir / "build"
    for label, path in (
        ("build", build_dir),
        ("closeout", output.parent),
        ("golden_acceptance.json", output),
    ):
        if path.is_symlink():
            raise GoldenAcceptanceError(f"sandbox_symlink_forbidden: {label}")


def _export_hashes(example_dir: Path, name: str) -> dict[str, str]:
    exports_dir = example_dir / "exports"
    hashes: dict[str, str] = {}
    for ext in ("pdf", "svg", "png", "tif", "tiff"):
        path = exports_dir / f"{name}.{ext}"
        if path.is_symlink():
            raise GoldenAcceptanceError(f"sandbox_symlink_forbidden: exports/{path.name}")
        if path.is_file():
            hashes["tif" if ext == "tiff" else ext] = evidence_hash.sha256_file(path)
    return hashes


def _refuse_reused_authorization(
    output: Path,
    exports: dict[str, str],
    authorization: dict[str, str] | None,
) -> None:
    """Refuse to accept a different export under an authorization that predates
    the previous acceptance.

    The decision record does not name an export, so one signature accepted
    every later export of the fixture forever: swapping in another figure's PDF
    and re-running the accept produced a receipt whose release_authorization was
    byte-identical and whose export hash had moved. The prior receipt is the
    missing anchor — the human signed after it, or they did not sign for this.
    """
    if not output.is_file():
        return
    try:
        prior = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoldenAcceptanceError("prior_golden_acceptance_unreadable") from exc
    if not isinstance(prior, dict) or prior.get("exports") == exports:
        return
    authorized_at = _packet_moment(str((authorization or {}).get("packet_timestamp") or ""))
    accepted_at = _packet_moment(str(prior.get("reviewed_at") or ""))
    if authorized_at is None or accepted_at is None or authorized_at <= accepted_at:
        raise GoldenAcceptanceError("release_authorization_predates_export_change")


def _allowed_pre_acceptance_blocks(readiness: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = []
    for check in readiness.get("checks", []):
        if not isinstance(check, dict):
            continue
        if check.get("state") in {"passed", "not_required"}:
            continue
        check_id = check.get("id")
        reason = str(check.get("reason") or "")
        if check_id == "export" and "tracked golden export" in reason:
            allowed.append(check)
            continue
        if check_id == "golden_acceptance" and "tracked golden export" in reason:
            allowed.append(check)
            continue
        # Only a loop record that is stale purely because the export artifacts
        # moved may be waived. The old substring test on the reason sentence
        # matched every path under exports/, so any stale loop record was
        # waived once /fig_export had run.
        if check_id == "loop_rerun":
            evidence = check.get("evidence")
            if not isinstance(evidence, dict):
                continue
            # (a) the loop record is stale only because the export artifacts
            # moved, or (b) it is waiting on prerequisites that are themselves
            # part of this pre-acceptance set.
            blocked_by = evidence.get("blocked_by")
            waived_prerequisites = isinstance(blocked_by, list) and set(blocked_by) <= {
                "export",
                "golden_acceptance",
            }
            if evidence.get("newest_input_is_export_artifact") or waived_prerequisites:
                allowed.append(check)
            continue
        # The chicken-and-egg case this waiver exists for is "release_ready is
        # false only because acceptance has not happened yet". `release_ready
        # is False` alone is not that case: _release_check blocks whenever the
        # publication gate did not pass, so the old test also waived a release
        # blocked by invalid_human_attestation or PROVENANCE_REQUIRED, and the
        # check could never block an accept. A passing gate is the floor.
        if check_id == "release":
            evidence = check.get("evidence")
            if (
                isinstance(evidence, dict)
                and evidence.get("release_ready") is False
                and evidence.get("publication_gate_state") == publication_gate.PUBLICATION_GATE_PASS
                and not evidence.get("publication_gate_failures")
            ):
                allowed.append(check)
            continue
        continue
    return allowed


def write_golden_acceptance(
    name: str,
    *,
    decision: str,
    reviewer: str,
    rationale: str,
    accept_golden: bool,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    if decision not in DECISIONS:
        raise GoldenAcceptanceError("decision must be accept, reject, or defer")
    if not reviewer.strip() or not rationale.strip():
        raise GoldenAcceptanceError("reviewer and rationale are required")
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    authorization = _authorizing_decision_record(name, paths.plugin_root)
    if decision == "accept" and authorization is None:
        raise GoldenAcceptanceError("release_decision_record_required")
    readiness = closeout_readiness.build_closeout_readiness(
        name,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    export_state = readiness.get("evidence_index", {}).get("status", {}).get("export_state")
    if decision == "accept" and export_state == "TRACKED_GOLDEN" and not accept_golden:
        raise GoldenAcceptanceError("accept_golden_required")
    blocking = _allowed_pre_acceptance_blocks(readiness)
    disallowed = [
        check
        for check in readiness.get("checks", [])
        if isinstance(check, dict)
        and check.get("state") not in {"passed", "not_required"}
        and check not in blocking
    ]
    if decision == "accept" and disallowed:
        raise GoldenAcceptanceError("closeout_not_ready")
    output = example_dir / "build" / "closeout" / "golden_acceptance.json"
    _ensure_safe_write_target(example_dir, output)
    exports = _export_hashes(example_dir, name)
    if decision == "accept":
        _refuse_reused_authorization(output, exports, authorization)
    output.parent.mkdir(parents=True, exist_ok=True)
    tex_path = example_dir / f"{name}.tex"
    critique_path = example_dir / "critique.md"
    apply_path_value = (
        readiness.get("evidence_index", {}).get("candidate", {}).get("apply_result_path")
        if isinstance(readiness.get("evidence_index", {}).get("candidate"), dict)
        else None
    )
    apply_path = example_dir / apply_path_value if isinstance(apply_path_value, str) else None
    payload = {
        "schema": SCHEMA,
        "figure_name": name,
        "decision": decision,
        "reviewer": reviewer,
        "reviewed_at": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        ),
        "rationale": rationale,
        "accept_golden": accept_golden,
        "release_authorization": authorization,
        "source_sha256": _sha256_fixture_file(tex_path, f"{name}.tex"),
        "exports": exports,
        "critique_sha256": _sha256_fixture_file(critique_path, "critique.md"),
        "closeout_readiness_sha256": _canonical_hash(readiness),
        "latest_apply_result_sha256": _sha256_fixture_file(
            apply_path,
            str(apply_path_value),
        )
        if apply_path is not None
        else None,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "schema": "figure-agent.golden-acceptance-write-result.v1",
        "figure_name": name,
        "path": _fixture_relative(example_dir, output),
    }
