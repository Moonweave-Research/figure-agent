from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import fixture_identity
import runtime_paths

SCHEMA: Final = "figure-agent.composition-rank-result.v1"
RENDER_MANIFEST_SCHEMA: Final = "figure-agent.composition-render-manifest.v1"


class CompositionRankError(ValueError):
    pass


def _diagnostic(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _workspace_root(workspace_root: Path | None) -> Path:
    return runtime_paths.resolve_runtime_paths(workspace_root=workspace_root).workspace_root


def _has_stale_evidence(freshness_vector: dict[str, Any] | None) -> bool:
    if freshness_vector is None:
        return False
    status = freshness_vector.get("status")
    if not isinstance(status, dict):
        return False
    return any(value == "stale" for value in status.values())


def _freshness_vector(
    candidate_set: dict[str, Any],
    freshness_vector: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if freshness_vector is not None:
        return freshness_vector
    value = candidate_set.get("freshness_vector")
    return value if isinstance(value, dict) else None


def _candidate_id(candidate: dict[str, Any]) -> str:
    value = str(candidate.get("id") or "")
    fixture_identity.validate_fixture_name(value)
    return value


def _candidates(candidate_set: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        raise CompositionRankError("candidate_set_invalid")
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _safe_fixture_path(fixture: Path, path: Path) -> Path:
    try:
        relative = path.relative_to(fixture)
    except ValueError as exc:
        raise CompositionRankError("path_escape") from exc
    cursor = fixture
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise CompositionRankError("sandbox_symlink_forbidden")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(fixture.resolve(strict=False))
    except ValueError as exc:
        raise CompositionRankError("path_escape") from exc
    return path


def _load_render_manifest(fixture: Path, candidate_id: str) -> dict[str, Any] | None:
    manifest = _safe_fixture_path(
        fixture,
        fixture / "build" / "candidates" / candidate_id / "composition_render_manifest.json",
    )
    if not manifest.exists():
        return None
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompositionRankError("render_manifest_invalid")
    if payload.get("schema") != RENDER_MANIFEST_SCHEMA:
        raise CompositionRankError("render_manifest_invalid")
    if payload.get("fixture") != fixture.name or payload.get("candidate_id") != candidate_id:
        raise CompositionRankError("render_manifest_identity_mismatch")
    return payload


def _stage_status(render_manifest: dict[str, Any] | None, stage: str) -> str:
    if render_manifest is None:
        return "missing"
    stages = render_manifest.get("stages")
    if not isinstance(stages, dict):
        return "missing"
    value = stages.get(stage)
    if not isinstance(value, dict):
        return "missing"
    return str(value.get("status") or "missing")


def _hard_gates(render_manifest: dict[str, Any] | None) -> dict[str, str]:
    return {
        "prepare": _stage_status(render_manifest, "prepare"),
        "compile": _stage_status(render_manifest, "compile"),
        "export": _stage_status(render_manifest, "export"),
        "crop": _stage_status(render_manifest, "crop"),
        "evaluate": _stage_status(render_manifest, "evaluate"),
    }


def _is_prepare_only(gates: dict[str, str]) -> bool:
    return gates == {
        "prepare": "success",
        "compile": "not_run",
        "export": "not_run",
        "crop": "not_run",
        "evaluate": "not_run",
    }


def _render_status(gates: dict[str, str]) -> str:
    if _is_prepare_only(gates):
        return "prepared_needs_human_review"
    return "not_prepared"


def _deterministic_findings(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_delta = candidate.get("composition_lint_delta")
    delta = raw_delta if isinstance(raw_delta, dict) else {}
    raw_findings = delta.get("deterministic")
    if not isinstance(raw_findings, list):
        return []
    findings: list[dict[str, Any]] = []
    for finding in raw_findings:
        if not isinstance(finding, dict):
            continue
        if not all(key in finding for key in ("metric", "evidence_object", "threshold")):
            continue
        findings.append({**finding, "mode": "deterministic"})
    return findings


def _human_commentary(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_delta = candidate.get("composition_lint_delta")
    delta = raw_delta if isinstance(raw_delta, dict) else {}
    raw_findings = delta.get("human_commentary")
    if not isinstance(raw_findings, list):
        return []
    commentary: list[dict[str, Any]] = []
    for finding in raw_findings:
        if isinstance(finding, dict):
            commentary.append(
                {
                    **finding,
                    "mode": "human_commentary",
                    "rank_eligible": False,
                    "blocking_allowed": False,
                }
            )
    return commentary


def _deterministic_score(findings: list[dict[str, Any]], gates: dict[str, str]) -> int:
    if not _is_prepare_only(gates):
        return -100
    score = 0
    for finding in findings:
        delta = str(finding.get("delta") or "")
        if delta == "improved":
            score += 1
        elif delta == "regressed":
            score -= 1
    return score


def _ranked_candidate(fixture: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = _candidate_id(candidate)
    render_manifest = _load_render_manifest(fixture, candidate_id)
    gates = _hard_gates(render_manifest)
    deterministic = _deterministic_findings(candidate)
    family = str(candidate.get("family") or "unknown")
    return {
        "candidate_id": candidate_id,
        "family": family,
        "render_status": _render_status(gates),
        "hard_gate_state": "reviewable" if _is_prepare_only(gates) else "blocked",
        "hard_gates": gates,
        "composition_lint_delta": {
            "deterministic": deterministic,
            "human_commentary": _human_commentary(candidate),
        },
        "rank_evidence": {
            "deterministic_delta_score": _deterministic_score(deterministic, gates)
        },
        "effective_apply_authority": "review_only",
        "auto_apply_allowed": False,
    }


def rank_composition_candidates(
    name: str,
    *,
    candidate_set: dict[str, Any],
    freshness_vector: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    workspace = _workspace_root(workspace_root)
    if _has_stale_evidence(_freshness_vector(candidate_set, freshness_vector)):
        return {
            "schema": SCHEMA,
            "fixture": name,
            "status": "proposed_unranked",
            "ranked_candidates": [],
            "diagnostics": [
                _diagnostic(
                    "stale_evidence_proposed_unranked",
                    "fresh evidence is required before ranking",
                )
            ],
        }
    fixture = workspace / "examples" / name
    ranked = [_ranked_candidate(fixture, candidate) for candidate in _candidates(candidate_set)]
    ranked.sort(
        key=lambda item: (
            int(item["rank_evidence"]["deterministic_delta_score"]),
            str(item["candidate_id"]),
        ),
        reverse=True,
    )
    return {
        "schema": SCHEMA,
        "fixture": name,
        "status": "ranked",
        "rank_policy": {
            "basis": ["hard_gates", "deterministic_composition_lint_delta"],
            "human_commentary_rank_eligible": False,
            "aesthetic_scoring_allowed": False,
        },
        "ranked_candidates": ranked,
        "diagnostics": [],
    }
