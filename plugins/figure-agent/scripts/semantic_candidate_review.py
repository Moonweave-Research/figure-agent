from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import semantic_contracts
import yaml

SCHEMA = "figure-agent.semantic-candidate-review.v1"
STATE_SCHEMA = "figure-agent.semantic-review-state.v1"
ALLOWED_VERDICTS = {"pass", "needs_human", "semantic_risk", "invalid_or_stale"}
AUTHORITY_FIELDS = {"apply_authority", "effective_apply_authority", "accepted", "operations"}
PURE_MECHANICAL_FAMILIES = {"bounded_coordinate_offset", "coordinate_offset", "label_offset"}
PURE_MECHANICAL_OPERATIONS = {"coordinate_offset", "bounded_coordinate_offset"}
SPEC_BLOCKING_REASONS_KEY = "_semantic_review_blocking_reasons"


class SemanticCandidateReviewError(ValueError):
    pass


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _review_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "semantic_review.json"


def load_spec(example_dir: Path) -> dict[str, Any]:
    spec_path = example_dir / "spec.yaml"
    if spec_path.is_symlink() or not spec_path.is_file():
        if not spec_path.exists() and not spec_path.is_symlink():
            return {}
        return {"semantic_review_required": True, SPEC_BLOCKING_REASONS_KEY: ["spec_unreadable"]}
    try:
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {"semantic_review_required": True, SPEC_BLOCKING_REASONS_KEY: ["spec_unreadable"]}
    if not isinstance(payload, dict):
        return {"semantic_review_required": True, SPEC_BLOCKING_REASONS_KEY: ["spec_unreadable"]}
    return payload


def _state(
    *,
    status: str,
    required_before_apply: bool,
    human_required: bool,
    blocking_reasons: list[str],
    review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review_blocks_apply = status in {"needs_human", "semantic_risk"}
    return {
        "schema": STATE_SCHEMA,
        "status": status,
        "verdict": status if status in ALLOWED_VERDICTS else "invalid_or_stale",
        "required_before_apply": required_before_apply,
        "blocks_apply": review_blocks_apply or (required_before_apply and status != "pass"),
        "human_required": human_required,
        "blocking_reasons": blocking_reasons,
        "reviewed_artifacts": review.get("reviewed_artifacts", []) if review else [],
        "semantic_invariants": review.get("semantic_invariants", []) if review else [],
        "findings": review.get("findings", []) if review else [],
        "conflicts": review.get("conflicts", []) if review else [],
        "reviewer": review.get("reviewer") if review else None,
        "reviewed_at": review.get("reviewed_at") if review else None,
    }


def _safe_artifact_path(example_dir: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = example_dir / path
    if candidate.is_symlink():
        return None
    try:
        candidate.resolve().relative_to(example_dir.resolve())
    except ValueError:
        return None
    return candidate


def _semantic_risks(manifest: dict[str, Any]) -> list[str]:
    risks = manifest.get("semantic_risks")
    if not isinstance(risks, list):
        return []
    return [str(risk) for risk in risks if str(risk).strip()]


def _candidate_panel(manifest: dict[str, Any]) -> str | None:
    panel = manifest.get("panel")
    return str(panel) if isinstance(panel, str) and panel.strip() else None


def _has_locked_invariants(spec: dict[str, Any], manifest: dict[str, Any]) -> bool:
    contracts = semantic_contracts.collect_semantic_contracts(spec)
    invariants = contracts.get("locked_invariants")
    if not isinstance(invariants, list) or not invariants:
        return False
    panel = _candidate_panel(manifest)
    return panel is None or any(
        isinstance(item, dict) and item.get("panel_id") == panel for item in invariants
    )


def _is_pure_mechanical(manifest: dict[str, Any]) -> bool:
    family = str(
        manifest.get("edit_family")
        or manifest.get("edit_class")
        or manifest.get("family")
        or ""
    )
    if family not in PURE_MECHANICAL_FAMILIES:
        return False
    operations = manifest.get("operations")
    if not isinstance(operations, list) or not operations:
        return False
    for operation in operations:
        if not isinstance(operation, dict):
            return False
        mechanical_kind = str(
            operation.get("semantic_kind") or operation.get("kind") or ""
        )
        if mechanical_kind not in PURE_MECHANICAL_OPERATIONS:
            return False
    return True


def _requirement_reasons(manifest: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    spec_reasons = spec.get(SPEC_BLOCKING_REASONS_KEY)
    if isinstance(spec_reasons, list):
        reasons.extend(str(reason) for reason in spec_reasons if str(reason).strip())
    if _semantic_risks(manifest):
        reasons.append("semantic_risk")
    if spec.get("semantic_review_required") is True:
        reasons.append("semantic_review_required")
    if _has_locked_invariants(spec, manifest):
        reasons.append("locked_invariants")
    if not _is_pure_mechanical(manifest):
        reasons.append("not_pure_mechanical")
    return reasons


def _load_review(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    if path.is_symlink():
        raise SemanticCandidateReviewError("semantic_review_symlink")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SemanticCandidateReviewError("semantic_review_unreadable") from exc
    if not isinstance(payload, dict):
        raise SemanticCandidateReviewError("semantic_review_invalid")
    return payload


def _invalid_reasons(
    example_dir: Path,
    manifest: dict[str, Any],
    review: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if review.get("schema") != SCHEMA:
        reasons.append("schema_invalid")
    if review.get("fixture") != example_dir.name:
        reasons.append("fixture_mismatch")
    if review.get("candidate_id") != manifest.get("candidate_id"):
        reasons.append("candidate_id_mismatch")
    if review.get("candidate_hash") != manifest.get("candidate_hash"):
        reasons.append("candidate_hash_mismatch")
    verdict = review.get("verdict")
    if verdict not in ALLOWED_VERDICTS:
        reasons.append("verdict_invalid")
    if AUTHORITY_FIELDS & set(review):
        reasons.append("authority_field_forbidden")
    artifacts = review.get("reviewed_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        reasons.append("reviewed_artifacts_missing")
        return reasons
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            reasons.append("reviewed_artifact_invalid")
            continue
        path = _safe_artifact_path(example_dir, artifact.get("path"))
        if path is None or not path.is_file():
            reasons.append("reviewed_artifact_missing")
            continue
        if artifact.get("sha256") != _file_sha256(path):
            reasons.append("reviewed_artifact_stale")
    return sorted(set(reasons))


def build_semantic_review_state(
    example_dir: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review_required_reasons = _requirement_reasons(manifest, spec or {})
    if "spec_unreadable" in review_required_reasons:
        return _state(
            status="missing",
            required_before_apply=True,
            human_required=True,
            blocking_reasons=review_required_reasons,
        )
    required = bool(review_required_reasons)
    review = _load_review(_review_path(manifest_path))
    if review is None:
        return _state(
            status="missing",
            required_before_apply=required,
            human_required=required,
            blocking_reasons=review_required_reasons,
        )
    invalid_reasons = _invalid_reasons(example_dir, manifest, review)
    if invalid_reasons:
        return _state(
            status="invalid_or_stale",
            required_before_apply=required,
            human_required=required,
            blocking_reasons=invalid_reasons,
            review=review,
        )
    verdict = str(review.get("verdict"))
    human_required = bool(review.get("human_required")) or verdict in {
        "needs_human",
        "semantic_risk",
    }
    blocking_reasons = []
    if verdict != "pass":
        blocking_reasons.extend(review_required_reasons)
        if verdict in {"needs_human", "semantic_risk"}:
            blocking_reasons.append(verdict)
    return _state(
        status=verdict,
        required_before_apply=required,
        human_required=human_required,
        blocking_reasons=sorted(set(blocking_reasons)),
        review=review,
    )


def semantic_blocking_reasons(state: dict[str, Any]) -> list[str]:
    if state.get("blocks_apply") is not True:
        return []
    reasons = state.get("blocking_reasons")
    if not isinstance(reasons, list) or not reasons:
        return [str(state.get("status") or "blocked")]
    return [str(reason) for reason in reasons if str(reason).strip()]
