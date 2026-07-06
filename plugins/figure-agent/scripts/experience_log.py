"""Append durable candidate experience records from existing artifacts."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import candidate_contracts
import convergence_models
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.experience-record.v1"


class ExperienceLogError(ValueError):
    """Raised when experience-log extraction or writes are unsafe."""


def _artifact_time(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise ExperienceLogError(f"{label}_symlink")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExperienceLogError(f"{label}_missing") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExperienceLogError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise ExperienceLogError(f"{label}_invalid")
    return payload


def _load_experience_records(plugin_root: Path, name: str) -> list[dict[str, Any]]:
    fixture_identity.validate_fixture_name(name)
    override = os.environ.get("FIG_AGENT_EXPERIENCE_LOG_DIR")
    log_dir = experience_log_dir(plugin_root)
    path = log_dir / f"{name}.jsonl"
    checks = (("experience_log", log_dir), ("experience_log", path))
    if not override:
        checks = (("docs", plugin_root / "docs"), *checks)
    for label, item in checks:
        if item.is_symlink():
            raise ExperienceLogError(f"{label}_symlink")
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExperienceLogError(f"experience_record_invalid:{line_number}") from exc
        if not isinstance(payload, dict):
            raise ExperienceLogError(f"experience_record_invalid:{line_number}")
        records.append(payload)
    return records


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(example_dir.parent.parent.resolve()).as_posix()
        except ValueError as exc:
            raise ExperienceLogError("path_escape") from exc


def _candidate_sandbox(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    candidates_root = build_dir / "candidates"
    sandbox = candidates_root / candidate_id
    for label, path in (
        ("build", build_dir),
        ("candidates", candidates_root),
        (candidate_id, sandbox),
    ):
        if path.is_symlink():
            raise ExperienceLogError(f"sandbox_symlink_forbidden:{label}")
    try:
        sandbox.resolve().relative_to(candidates_root.resolve())
    except ValueError as exc:
        raise ExperienceLogError("candidate_path_escape") from exc
    return sandbox


def _candidate_set_file(
    example_dir: Path,
    manifest: dict[str, Any],
    candidate_set_path: Path | None = None,
) -> Path:
    raw = (
        candidate_set_path.as_posix()
        if candidate_set_path is not None
        else manifest.get("candidate_set_path")
    )
    if not isinstance(raw, str) or not raw:
        raise ExperienceLogError("candidate_set_path_missing")
    try:
        path = candidate_contracts.candidate_set_input_path(
            example_dir.parent.parent,
            example_dir.name,
            raw,
        )
    except candidate_contracts.CandidateContractError as exc:
        raise ExperienceLogError("candidate_set_path_escape") from exc
    if path.is_symlink():
        raise ExperienceLogError("candidate_set_symlink")
    return path


def _candidate_from_set(candidate_set: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        raise ExperienceLogError("candidate_set_candidates_invalid")
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == candidate_id:
            return candidate
    raise ExperienceLogError("candidate_missing_from_set")


def _candidate_family(manifest: dict[str, Any], candidate: dict[str, Any]) -> str:
    value = (
        manifest.get("edit_family")
        or manifest.get("edit_class")
        or candidate.get("edit_family")
        or candidate.get("edit_class")
        or manifest.get("family")
        or candidate.get("family")
    )
    return str(value) if value else "unknown"


def _selector_text_hash(manifest: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    for payload in (candidate, manifest):
        selector = payload.get("selector")
        if isinstance(selector, dict) and isinstance(selector.get("selector_text_hash"), str):
            return selector["selector_text_hash"]
    return None


def _target(manifest: dict[str, Any], candidate: dict[str, Any]) -> dict[str, str]:
    target = candidate.get("target") if isinstance(candidate.get("target"), dict) else None
    if target is None and isinstance(manifest.get("target"), dict):
        target = manifest["target"]
    target = target or {}
    selector_hash = _selector_text_hash(manifest, candidate)
    subregion = str(target.get("subregion") or "unknown")
    return {
        "panel": str(target.get("panel") or "unknown"),
        "subregion_key": selector_hash or f"unstable:{subregion}",
    }


def _source_before_hash(example_dir: Path, name: str, apply_result: dict[str, Any]) -> str:
    changed_files = apply_result.get("changed_files")
    if isinstance(changed_files, list):
        for item in changed_files:
            if not isinstance(item, dict):
                continue
            if item.get("path") == f"{name}.tex" and isinstance(item.get("before_sha256"), str):
                return item["before_sha256"]
    source = example_dir / f"{name}.tex"
    return _sha256_file(source) if source.is_file() else ""


def _stage_status(payload: dict[str, Any], stage: str) -> str | None:
    value = payload.get(stage)
    if isinstance(value, dict):
        status = value.get("status")
        return str(status) if status is not None else None
    return str(value) if value is not None else None


def _post_apply_pipeline_ok(apply_status: str, post_apply: dict[str, Any]) -> bool:
    return apply_status == "applied" and all(
        _stage_status(post_apply, stage) == "success" for stage in ("compile", "export", "status")
    )


def _quality_movement(
    apply_status: str,
    post_apply: dict[str, Any],
    *,
    pipeline_ok: bool,
) -> str | None:
    class_verifiers = post_apply.get("class_verifiers")
    if apply_status == "rolled_back":
        return "regressed"
    if isinstance(class_verifiers, dict) and (
        class_verifiers.get("rolled_back") is True or class_verifiers.get("status") == "failed"
    ):
        return "regressed"
    detector_recheck = post_apply.get("detector_recheck")
    if isinstance(detector_recheck, dict) and detector_recheck.get("status") == "failed":
        return "regressed"
    if not pipeline_ok:
        return None
    if isinstance(detector_recheck, dict) and detector_recheck.get("status") == "success":
        return "improved"
    return "neutral"


def _verifier_statuses(post_apply: dict[str, Any]) -> dict[str, str]:
    class_verifiers = post_apply.get("class_verifiers")
    if not isinstance(class_verifiers, dict):
        return {}
    verifiers = class_verifiers.get("verifiers")
    if not isinstance(verifiers, list):
        return {}
    statuses: dict[str, str] = {}
    for item in verifiers:
        if not isinstance(item, dict) or not isinstance(item.get("verifier"), str):
            continue
        status = "pass" if item.get("status") == "success" else "fail"
        statuses[item["verifier"]] = status
    return statuses


def _pixel_delta(render_manifest: dict[str, Any]) -> dict[str, float | None]:
    visual_deltas = render_manifest.get("visual_deltas")
    if not isinstance(visual_deltas, dict):
        return {"changed_pixel_ratio": None}
    value = visual_deltas.get("changed_pixel_ratio")
    try:
        return {"changed_pixel_ratio": float(value)}
    except (TypeError, ValueError):
        return {"changed_pixel_ratio": None}


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _acceptance_payload(sandbox: Path) -> dict[str, Any] | None:
    path = sandbox / "acceptance.json"
    if not path.is_file():
        return None
    return _load_json(path, "acceptance")


def _record_with_id(record: dict[str, Any]) -> dict[str, Any]:
    record["record_id"] = candidate_contracts.canonical_hash(record)
    return record


def _convergence_summary(
    selected_attempt: dict[str, Any] | None,
    convergence_decision: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(selected_attempt, dict) or not isinstance(convergence_decision, dict):
        return None
    journal = (
        selected_attempt.get("journal_constraints")
        if isinstance(selected_attempt.get("journal_constraints"), dict)
        else {}
    )
    semantic = (
        selected_attempt.get("semantic_score")
        if isinstance(selected_attempt.get("semantic_score"), dict)
        else {}
    )
    aesthetic = (
        selected_attempt.get("aesthetic_score")
        if isinstance(selected_attempt.get("aesthetic_score"), dict)
        else {}
    )
    outputs = (
        selected_attempt.get("outputs") if isinstance(selected_attempt.get("outputs"), dict) else {}
    )
    return {
        "attempt_id": selected_attempt.get("attempt_id"),
        "decision": convergence_decision.get("decision"),
        "journal_guide_hash": selected_attempt.get("journal_guide_hash"),
        "journal_constraints_passed": journal.get("passed"),
        "semantic_complete": semantic.get("complete"),
        "aesthetic_overall": _float_or_none(aesthetic.get("overall")),
        "selected_aesthetic_score": _float_or_none(
            convergence_decision.get("selected_aesthetic_score")
        ),
        "outputs": dict(outputs),
        "output_formats": [key for key in ("editable", "pdf", "png", "svg") if outputs.get(key)],
    }


def _convergence_verifiers(convergence: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(convergence, dict):
        return {}
    decision = convergence.get("decision")
    return {
        "journal_constraints": (
            "pass" if convergence.get("journal_constraints_passed") is True else "fail"
        ),
        "convergence_decision": (
            "pass"
            if decision == "accept"
            else "defer"
            if decision in {"stop", "rollback", "human_review"}
            else "fail"
        ),
    }


def _attempt_from_experience_record(record: dict[str, Any]) -> dict[str, Any] | None:
    fixture = record.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        return None
    state = record.get("state") if isinstance(record.get("state"), dict) else {}
    outcome = record.get("outcome") if isinstance(record.get("outcome"), dict) else {}
    convergence = (
        outcome.get("convergence") if isinstance(outcome.get("convergence"), dict) else None
    )
    if convergence is None:
        return None
    attempt_id = convergence.get("attempt_id")
    spec_hash = state.get("base_tex_hash")
    journal_guide_hash = convergence.get("journal_guide_hash")
    if not (
        isinstance(attempt_id, str)
        and isinstance(spec_hash, str)
        and isinstance(journal_guide_hash, str)
    ):
        return None
    outputs = convergence.get("outputs") if isinstance(convergence.get("outputs"), dict) else {}
    attempt = {
        "schema": convergence_models.FIGURE_ATTEMPT_SCHEMA,
        "attempt_id": attempt_id,
        "figure_id": fixture,
        "user_goal": "experience-log prior convergence attempt",
        "target_medium": "journal_paper",
        "spec_hash": spec_hash,
        "journal_guide_hash": journal_guide_hash,
        "outputs": outputs,
        "journal_constraints": {
            "passed": convergence.get("journal_constraints_passed") is True,
            "violations": [],
        },
        "semantic_score": {
            "complete": convergence.get("semantic_complete") is True,
            "missing_elements": [],
            "incorrect_relations": [],
        },
        "aesthetic_score": {"overall": _float_or_none(convergence.get("aesthetic_overall")) or 0.0},
        "decision": convergence.get("decision"),
    }
    try:
        return convergence_models.validate_figure_attempt(attempt)
    except convergence_models.ConvergenceModelError:
        return None


def convergence_attempt_history(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> list[dict[str, Any]]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    history: list[dict[str, Any]] = []
    for record in _load_experience_records(paths.plugin_root, name):
        attempt = _attempt_from_experience_record(record)
        if attempt is not None:
            history.append(attempt)
    return history


def _is_ranked_candidate(candidate: dict[str, Any]) -> bool:
    return candidate.get("rank") is not None or candidate.get("rank_score") is not None


def _unchosen_record(
    *,
    name: str,
    created_at: str,
    base_tex_hash: str,
    candidate: dict[str, Any],
    n_candidates: int,
    manifest: dict[str, Any],
    candidate_set_path: Path,
    example_dir: Path,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("id") or "")
    fixture_identity.validate_fixture_name(candidate_id)
    selected_sandbox = _candidate_sandbox(example_dir, str(manifest["candidate_id"]))
    record = {
        "schema": SCHEMA,
        "fixture": name,
        "created_at": created_at,
        "state": {
            "base_tex_hash": base_tex_hash,
            "target": _target({}, candidate),
            "pre_apply_defects": [],
            "critique_finding_id": None,
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": _candidate_family({}, candidate),
            "params": {"operations": candidate.get("operations") or []},
            "candidate_hash": str(candidate.get("candidate_hash") or ""),
            "rank_score": _float_or_none(candidate.get("rank_score")),
            "rank": _int_or_none(candidate.get("rank")),
            "n_candidates": n_candidates,
        },
        "outcome": {
            "pipeline_ok": None,
            "apply_status": "unchosen",
            "quality_movement": None,
            "verifiers": {},
            "detector_recheck": {},
            "pixel_delta": {"changed_pixel_ratio": None},
            "human_label": None,
            "human_decision_kind": None,
        },
        "source_artifacts": [
            _fixture_relative(example_dir, candidate_set_path),
            _fixture_relative(example_dir, selected_sandbox / "apply_result.json"),
        ],
    }
    return _record_with_id(record)


def build_apply_record(
    name: str,
    candidate_id: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
) -> dict[str, Any]:
    return build_apply_records(
        name,
        candidate_id,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
        candidate_set_path=candidate_set_path,
    )[0]


def build_recommendation_record(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_rankings: list[dict[str, Any]],
    decision: dict[str, Any],
    recommendation: dict[str, Any],
    run_dir: Path,
    selected_attempt: dict[str, Any] | None = None,
    convergence_decision: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    fixture_identity.validate_fixture_name(candidate_id)
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = paths.examples_dir / name
    candidate = _candidate_from_set(candidate_set, candidate_id)
    rankings_by_id = {
        str(ranking.get("candidate_id") or ""): ranking
        for ranking in candidate_rankings
        if isinstance(ranking, dict)
    }
    ranking = rankings_by_id.get(candidate_id, {})
    ordered_ids = [
        str(ranking.get("candidate_id") or "")
        for ranking in candidate_rankings
        if isinstance(ranking, dict) and ranking.get("candidate_id")
    ]
    source_context = decision.get("source_context")
    evidence = recommendation.get("evidence") if isinstance(recommendation, dict) else {}
    evidence = evidence if isinstance(evidence, dict) else {}
    auto_accept_recommended = recommendation.get("status") == "auto_accept_recommended"
    convergence = _convergence_summary(selected_attempt, convergence_decision)
    convergence_deferred = (
        isinstance(convergence, dict)
        and convergence.get("decision") in {"stop", "rollback", "human_review"}
        and recommendation.get("status") == "blocked"
        and recommendation.get("recommendation") == "defer"
    )
    if not auto_accept_recommended and not convergence_deferred:
        raise ExperienceLogError("recommendation_not_ready")
    human_decision_kind = (
        "auto_accept_recommended" if auto_accept_recommended else "convergence_deferred"
    )
    record = {
        "schema": SCHEMA,
        "fixture": name,
        "created_at": _artifact_time(run_dir / "selected_acceptance_recommendation_000.json")
        if (run_dir / "selected_acceptance_recommendation_000.json").is_file()
        else datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "state": {
            "base_tex_hash": str(
                source_context.get("source_hash")
                if isinstance(source_context, dict)
                else decision.get("source_hash") or ""
            ),
            "target": _target({}, candidate),
            "pre_apply_defects": [],
            "critique_finding_id": None,
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": _candidate_family({}, candidate),
            "params": {"operations": candidate.get("operations") or []},
            "candidate_hash": str(candidate.get("candidate_hash") or ""),
            "rank_score": _float_or_none(ranking.get("rank_score")),
            "rank": _int_or_none(ranking.get("rank"))
            or (ordered_ids.index(candidate_id) + 1 if candidate_id in ordered_ids else None),
            "n_candidates": len(
                candidate_set.get("candidates")
                if isinstance(candidate_set.get("candidates"), list)
                else []
            ),
        },
        "outcome": {
            "pipeline_ok": True,
            "apply_status": "blocked",
            "quality_movement": "neutral",
            "verifiers": {
                "semantic_precheck": "pass"
                if evidence.get("semantic_precheck_status") == "pass"
                else "fail",
                "review_packet": "pass"
                if evidence.get("review_packet_status") == "ready"
                else "fail",
                "apply_readiness": "pass"
                if evidence.get("apply_readiness_status") == "ready_for_local_acceptance"
                else "fail",
                "acceptance_recommendation": "pass",
                **_convergence_verifiers(convergence),
            },
            "detector_recheck": {},
            "pixel_delta": {
                "changed_pixel_ratio": _float_or_none(evidence.get("full_changed_pixel_ratio"))
            },
            "human_label": None,
            "human_decision_kind": human_decision_kind,
            "automation_boundary": "recommendation_only",
            **(
                {
                    "deferral_reason": str(
                        recommendation.get("rationale")
                        or "convergence controller did not accept the selected attempt"
                    )
                }
                if convergence_deferred
                else {}
            ),
            **({"convergence": convergence} if convergence is not None else {}),
        },
        "source_artifacts": [
            _fixture_relative(example_dir, run_dir / "candidate_set_000.json"),
            _fixture_relative(example_dir, run_dir / "candidate_rankings_000.json"),
            _fixture_relative(
                example_dir,
                run_dir / "selected_semantic_precheck_000.json",
            ),
            _fixture_relative(example_dir, run_dir / "selected_review_packet_000.json"),
            _fixture_relative(
                example_dir,
                run_dir / "selected_acceptance_recommendation_000.json",
            ),
            *(
                [_fixture_relative(example_dir, run_dir / "selected_attempt_000.json")]
                if selected_attempt is not None
                else []
            ),
            *(
                [_fixture_relative(example_dir, run_dir / "convergence_decision_000.json")]
                if convergence_decision is not None
                else []
            ),
        ],
    }
    return _record_with_id(record)


def _recommendation_unchosen_record(
    *,
    name: str,
    created_at: str,
    base_tex_hash: str,
    candidate: dict[str, Any],
    ranking: dict[str, Any],
    rank: int | None,
    n_candidates: int,
    run_dir: Path,
    example_dir: Path,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("id") or "")
    fixture_identity.validate_fixture_name(candidate_id)
    record = {
        "schema": SCHEMA,
        "fixture": name,
        "created_at": created_at,
        "state": {
            "base_tex_hash": base_tex_hash,
            "target": _target({}, candidate),
            "pre_apply_defects": [],
            "critique_finding_id": None,
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": _candidate_family({}, candidate),
            "params": {"operations": candidate.get("operations") or []},
            "candidate_hash": str(candidate.get("candidate_hash") or ""),
            "rank_score": _float_or_none(ranking.get("rank_score")),
            "rank": _int_or_none(ranking.get("rank")) or rank,
            "n_candidates": n_candidates,
        },
        "outcome": {
            "pipeline_ok": None,
            "apply_status": "unchosen",
            "quality_movement": None,
            "verifiers": {},
            "detector_recheck": {},
            "pixel_delta": {"changed_pixel_ratio": None},
            "human_label": None,
            "human_decision_kind": "counterfactual_unchosen",
            "automation_boundary": "recommendation_only",
        },
        "source_artifacts": [
            _fixture_relative(example_dir, run_dir / "candidate_set_000.json"),
            _fixture_relative(example_dir, run_dir / "candidate_rankings_000.json"),
            _fixture_relative(
                example_dir,
                run_dir / "selected_acceptance_recommendation_000.json",
            ),
        ],
    }
    return _record_with_id(record)


def build_recommendation_records(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_rankings: list[dict[str, Any]],
    decision: dict[str, Any],
    recommendation: dict[str, Any],
    run_dir: Path,
    selected_attempt: dict[str, Any] | None = None,
    convergence_decision: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> list[dict[str, Any]]:
    selected = build_recommendation_record(
        name,
        candidate_id,
        candidate_set=candidate_set,
        candidate_rankings=candidate_rankings,
        decision=decision,
        recommendation=recommendation,
        run_dir=run_dir,
        selected_attempt=selected_attempt,
        convergence_decision=convergence_decision,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = paths.examples_dir / name
    candidates = (
        candidate_set.get("candidates") if isinstance(candidate_set.get("candidates"), list) else []
    )
    rankings_by_id = {
        str(ranking.get("candidate_id") or ""): ranking
        for ranking in candidate_rankings
        if isinstance(ranking, dict)
    }
    ordered_ids = [
        str(ranking.get("candidate_id") or "")
        for ranking in candidate_rankings
        if isinstance(ranking, dict) and ranking.get("candidate_id")
    ]
    records = [selected]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        other_id = str(candidate.get("id") or "")
        if other_id == candidate_id or other_id not in rankings_by_id:
            continue
        rank = ordered_ids.index(other_id) + 1 if other_id in ordered_ids else None
        records.append(
            _recommendation_unchosen_record(
                name=name,
                created_at=str(selected["created_at"]),
                base_tex_hash=str(selected["state"]["base_tex_hash"]),
                candidate=candidate,
                ranking=rankings_by_id[other_id],
                rank=rank,
                n_candidates=len(candidates),
                run_dir=run_dir,
                example_dir=example_dir,
            )
        )
    return records


def build_apply_records(
    name: str,
    candidate_id: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
) -> list[dict[str, Any]]:
    fixture_identity.validate_fixture_name(name)
    fixture_identity.validate_fixture_name(candidate_id)
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = paths.examples_dir / name
    sandbox = _candidate_sandbox(example_dir, candidate_id)
    manifest = _load_json(sandbox / "candidate_manifest.json", "candidate_manifest")
    resolved_candidate_set_path = _candidate_set_file(
        example_dir,
        manifest,
        candidate_set_path,
    )
    candidate_set = _load_json(resolved_candidate_set_path, "candidate_set")
    candidate = _candidate_from_set(candidate_set, candidate_id)
    render_manifest = _load_json(sandbox / "render_manifest.json", "render_manifest")
    apply_path = sandbox / "apply_result.json"
    apply_result = _load_json(apply_path, "apply_result")
    if apply_result.get("candidate_id") not in {None, candidate_id}:
        raise ExperienceLogError("candidate_id_mismatch")
    post_apply = apply_result.get("post_apply")
    post_apply = post_apply if isinstance(post_apply, dict) else {}
    apply_status = str(apply_result.get("status") or "unknown")
    pipeline_ok = _post_apply_pipeline_ok(apply_status, post_apply)
    quality_movement = _quality_movement(
        apply_status,
        post_apply,
        pipeline_ok=pipeline_ok,
    )
    acceptance = _acceptance_payload(sandbox)
    candidates = (
        candidate_set.get("candidates") if isinstance(candidate_set.get("candidates"), list) else []
    )
    created_at = _artifact_time(apply_path)
    base_tex_hash = _source_before_hash(example_dir, name, apply_result)
    record = {
        "schema": SCHEMA,
        "fixture": name,
        "created_at": created_at,
        "state": {
            "base_tex_hash": base_tex_hash,
            "target": _target(manifest, candidate),
            "pre_apply_defects": [],
            "critique_finding_id": None,
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": _candidate_family(manifest, candidate),
            "params": {
                "operations": candidate.get("operations") or manifest.get("operations") or []
            },
            "candidate_hash": str(
                manifest.get("candidate_hash") or candidate.get("candidate_hash") or ""
            ),
            "rank_score": _float_or_none(candidate.get("rank_score")),
            "rank": _int_or_none(candidate.get("rank")),
            "n_candidates": len(candidates),
        },
        "outcome": {
            "pipeline_ok": pipeline_ok,
            "apply_status": apply_status,
            "quality_movement": quality_movement,
            "verifiers": _verifier_statuses(post_apply),
            "detector_recheck": post_apply.get("detector_recheck")
            if isinstance(post_apply.get("detector_recheck"), dict)
            else {},
            "pixel_delta": _pixel_delta(render_manifest),
            "human_label": acceptance.get("decision") if isinstance(acceptance, dict) else None,
            "human_decision_kind": acceptance.get("decision_kind")
            if isinstance(acceptance, dict)
            else None,
        },
        "source_artifacts": [
            _fixture_relative(example_dir, resolved_candidate_set_path),
            _fixture_relative(example_dir, sandbox / "candidate_manifest.json"),
            _fixture_relative(example_dir, sandbox / "render_manifest.json"),
            _fixture_relative(example_dir, apply_path),
        ],
    }
    records = [_record_with_id(record)]
    for item in candidates:
        if isinstance(item, dict) and item.get("id") != candidate_id and _is_ranked_candidate(item):
            records.append(
                _unchosen_record(
                    name=name,
                    created_at=created_at,
                    base_tex_hash=base_tex_hash,
                    candidate=item,
                    n_candidates=len(candidates),
                    manifest=manifest,
                    candidate_set_path=resolved_candidate_set_path,
                    example_dir=example_dir,
                )
            )
    return records


def experience_log_dir(plugin_root: Path) -> Path:
    override = os.environ.get("FIG_AGENT_EXPERIENCE_LOG_DIR")
    return Path(override) if override else plugin_root / "docs" / "experience-log"


def _experience_log_path(name: str, plugin_root: Path) -> Path:
    override = os.environ.get("FIG_AGENT_EXPERIENCE_LOG_DIR")
    log_dir = experience_log_dir(plugin_root)
    path = log_dir / f"{name}.jsonl"
    checks = (("experience_log", log_dir), ("experience_log", path))
    if not override:
        checks = (("docs", plugin_root / "docs"), *checks)
    for label, item in checks:
        if item.is_symlink():
            raise ExperienceLogError(f"{label}_symlink")
    log_dir.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ExperienceLogError("experience_log_symlink")
    return path


def append_apply_record(
    name: str,
    candidate_id: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
) -> dict[str, Any]:
    records = build_apply_records(
        name,
        candidate_id,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
        candidate_set_path=candidate_set_path,
    )
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    output = _experience_log_path(name, paths.plugin_root)
    with output.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return {
        "schema": "figure-agent.experience-log-write.v1",
        "fixture": name,
        "record": records[0],
        "records": records,
        "writes": [f"docs/experience-log/{name}.jsonl"],
    }


def append_recommendation_record(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_rankings: list[dict[str, Any]],
    decision: dict[str, Any],
    recommendation: dict[str, Any],
    run_dir: Path,
    selected_attempt: dict[str, Any] | None = None,
    convergence_decision: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    records = build_recommendation_records(
        name,
        candidate_id,
        candidate_set=candidate_set,
        candidate_rankings=candidate_rankings,
        decision=decision,
        recommendation=recommendation,
        run_dir=run_dir,
        selected_attempt=selected_attempt,
        convergence_decision=convergence_decision,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    output = _experience_log_path(name, paths.plugin_root)
    with output.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return {
        "schema": "figure-agent.experience-log-write.v1",
        "fixture": name,
        "record": records[0],
        "records": records,
        "writes": [f"docs/experience-log/{name}.jsonl"],
    }
