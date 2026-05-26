"""Shared audit-evidence summary for figure-agent operator UX."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from critique_lint import (
    CROP_AUDIT_ACCOUNTING_SCHEMAS,
    LABEL_PATH_ACCOUNTING_SCHEMAS,
    STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS,
    TEXT_BOUNDARY_ACCOUNTING_SCHEMAS,
    VISUAL_CLASH_ACCOUNTING_SCHEMAS,
)
from critique_schema_vocab import MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS
from quality_manifest import file_sha256, yaml_frontmatter

SUMMARY_SCHEMA = "figure-agent.audit-evidence-summary.v1"
EVALUATION_STATES = frozenset(
    {
        "passed",
        "needs_action",
        "missing_input",
        "stale_or_mismatched",
        "legacy",
        "not_applicable",
    }
)


def _base_summary(example_dir: Path, critique_schema: str | None) -> dict[str, Any]:
    return {
        "schema": SUMMARY_SCHEMA,
        "fixture": example_dir.name,
        "critique_schema": critique_schema,
        "evaluation_state": "not_applicable",
        "blocking_items": [],
        "next_action": "",
        "reason": "audit evidence is not applicable",
        "visual_clash": {
            "present": False,
            "candidate_count": 0,
            "accounted_count": 0,
            "missing_refs": [],
            "unknown_refs": [],
        },
        "text_boundary": {
            "present": False,
            "candidate_count": 0,
            "accounted_count": 0,
            "missing_refs": [],
            "unknown_refs": [],
        },
        "label_path": {
            "present": False,
            "candidate_count": 0,
            "accounted_count": 0,
            "missing_refs": [],
            "unknown_refs": [],
        },
        "crop_audit": {
            "manifest_present": False,
            "required_count": 0,
            "verdict_counts": {"defect": 0, "no_defect": 0, "uncertain": 0},
            "uncertain_crop_ids": [],
        },
    }


def _finish(
    summary: dict[str, Any],
    *,
    state: str,
    blocking_items: list[str],
    next_action: str,
    reason: str,
) -> dict[str, Any]:
    if state not in EVALUATION_STATES:
        raise ValueError(f"unsupported audit evidence state: {state}")
    summary["evaluation_state"] = state
    summary["blocking_items"] = blocking_items
    summary["next_action"] = next_action
    summary["reason"] = reason
    return summary


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "malformed"
    if not isinstance(payload, dict):
        return None, "malformed"
    return payload, None


def _visual_clash_candidate_ids(report: dict[str, Any]) -> tuple[list[str], str | None]:
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], "malformed"
    ids: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return [], "malformed"
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            return [], "malformed"
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            return [], "malformed"
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, None


def _text_boundary_candidate_ids(report: dict[str, Any]) -> tuple[list[str], str | None]:
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], "malformed"
    ids: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return [], "malformed"
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            return [], "malformed"
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            return [], "malformed"
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, None


def _label_path_candidate_ids(report: dict[str, Any]) -> tuple[list[str], str | None]:
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], "malformed"
    ids: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return [], "malformed"
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            return [], "malformed"
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            return [], "malformed"
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, None


def _micro_defects(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    return [item for item in raw_items if isinstance(item, dict)]


def _visual_clash_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in _micro_defects(frontmatter):
        ref = item.get("visual_clash_ref")
        if isinstance(ref, str) and ref.strip():
            refs.append(ref.strip())
    return refs


def _text_boundary_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in _micro_defects(frontmatter):
        ref = item.get("text_boundary_ref")
        if isinstance(ref, str) and ref.strip():
            refs.append(ref.strip())
    return refs


def _label_path_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in _micro_defects(frontmatter):
        ref = item.get("label_path_ref")
        if isinstance(ref, str) and ref.strip():
            refs.append(ref.strip())
    return refs


def _structured_accept_gaps(frontmatter: dict[str, Any]) -> list[str]:
    if frontmatter.get("schema") not in STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS:
        return []
    gaps: list[str] = []
    for item in _micro_defects(frontmatter):
        if item.get("status") != "accept_simplification":
            continue
        visual_clash_ref = item.get("visual_clash_ref")
        if not isinstance(visual_clash_ref, str) or not visual_clash_ref.strip():
            continue
        reason = item.get("accept_simplification_reason")
        rationale = item.get("accept_simplification_rationale")
        if (
            reason not in MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS
            or not isinstance(rationale, str)
            or not rationale.strip()
        ):
            gaps.append(visual_clash_ref.strip())
    return sorted(dict.fromkeys(gaps))


def _manifest_required_ids(manifest: dict[str, Any]) -> tuple[list[str], str | None]:
    required = manifest.get("required_crop_ids")
    if not isinstance(required, list):
        return [], "malformed"
    ids: list[str] = []
    for crop_id in required:
        if not isinstance(crop_id, str) or not crop_id.strip():
            return [], "malformed"
        ids.append(crop_id.strip())
    return ids, None


def _manifest_crop_by_id(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], str | None]:
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return {}, "malformed"
    crop_by_id: dict[str, dict[str, Any]] = {}
    for crop in crops:
        if not isinstance(crop, dict):
            return {}, "malformed"
        crop_id = crop.get("id")
        if not isinstance(crop_id, str) or not crop_id.strip():
            return {}, "malformed"
        crop_by_id[crop_id.strip()] = crop
    return crop_by_id, None


def _valid_manifest_crop_path(crop_path: Any) -> Path | None:
    if not isinstance(crop_path, str):
        return None
    relative_crop_path = Path(crop_path)
    if (
        relative_crop_path.is_absolute()
        or ".." in relative_crop_path.parts
        or relative_crop_path.parts[:2] != ("build", "audit_crops")
        or relative_crop_path.suffix != ".png"
    ):
        return None
    return relative_crop_path


def _mismatched_manifest_crop_ids(
    example_dir: Path,
    manifest: dict[str, Any],
    required_ids: list[str],
) -> tuple[list[str], str | None]:
    crop_by_id, error = _manifest_crop_by_id(manifest)
    if error is not None:
        return [], "malformed"
    mismatched: list[str] = []
    for crop_id in required_ids:
        crop = crop_by_id.get(crop_id)
        if crop is None:
            mismatched.append(crop_id)
            continue
        expected_hash = crop.get("sha256")
        crop_path = crop.get("path")
        if not isinstance(expected_hash, str) or not expected_hash.startswith("sha256:"):
            mismatched.append(crop_id)
            continue
        relative_crop_path = _valid_manifest_crop_path(crop_path)
        if relative_crop_path is None:
            mismatched.append(crop_id)
            continue
        absolute_crop_path = example_dir / relative_crop_path
        if not absolute_crop_path.is_file() or file_sha256(absolute_crop_path) != expected_hash:
            mismatched.append(crop_id)
    return mismatched, None


def _crop_audit_counts(
    frontmatter: dict[str, Any],
) -> tuple[dict[str, int], list[str], list[str]]:
    counts = {"defect": 0, "no_defect": 0, "uncertain": 0}
    uncertain_crop_ids: list[str] = []
    logged_crop_ids: list[str] = []
    raw_items = frontmatter.get("crop_audit_log")
    if not isinstance(raw_items, list):
        return counts, uncertain_crop_ids, logged_crop_ids
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        crop_id = item.get("crop_id")
        if isinstance(crop_id, str) and crop_id.strip():
            logged_crop_ids.append(crop_id.strip())
        verdict = item.get("verdict")
        if verdict in counts:
            counts[verdict] += 1
        if verdict == "uncertain":
            if isinstance(crop_id, str) and crop_id.strip():
                uncertain_crop_ids.append(crop_id.strip())
    return counts, uncertain_crop_ids, logged_crop_ids


def summarize_audit_evidence(example_dir: Path) -> dict[str, Any]:
    """Return a compact read-only summary of fixture audit evidence state."""
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        summary = _base_summary(example_dir, None)
        return _finish(
            summary,
            state="not_applicable",
            blocking_items=[],
            next_action="",
            reason="critique.md is absent; audit evidence is not applicable",
        )

    frontmatter = yaml_frontmatter(critique_path)
    critique_schema = frontmatter.get("schema")
    critique_schema_value = critique_schema if isinstance(critique_schema, str) else None
    summary = _base_summary(example_dir, critique_schema_value)
    if critique_schema not in VISUAL_CLASH_ACCOUNTING_SCHEMAS:
        return _finish(
            summary,
            state="legacy",
            blocking_items=[],
            next_action=f"/fig_critique {example_dir.name}",
            reason="critique schema predates current audit evidence accounting",
        )

    visual_report, visual_error = _load_json(example_dir / "build" / "visual_clash.json")
    if visual_error is not None:
        reason = "missing build/visual_clash.json"
        if visual_error == "malformed":
            reason = "malformed build/visual_clash.json"
        return _finish(
            summary,
            state="missing_input",
            blocking_items=["build/visual_clash.json"],
            next_action=f"/fig_compile {example_dir.name}",
            reason=reason,
        )

    candidate_ids, candidate_error = _visual_clash_candidate_ids(visual_report or {})
    if candidate_error is not None:
        return _finish(
            summary,
            state="missing_input",
            blocking_items=["build/visual_clash.json"],
            next_action=f"/fig_compile {example_dir.name}",
            reason="malformed build/visual_clash.json candidates",
        )
    refs = _visual_clash_refs(frontmatter)
    candidate_id_set = set(candidate_ids)
    ref_set = set(refs)
    missing_refs = [candidate_id for candidate_id in candidate_ids if candidate_id not in refs]
    unknown_refs = sorted(ref for ref in ref_set if ref not in candidate_id_set)
    summary["visual_clash"] = {
        "present": True,
        "candidate_count": len(candidate_ids),
        "accounted_count": len(ref_set & candidate_id_set),
        "missing_refs": missing_refs,
        "unknown_refs": unknown_refs,
    }

    text_missing_refs: list[str] = []
    text_unknown_refs: list[str] = []
    if critique_schema in TEXT_BOUNDARY_ACCOUNTING_SCHEMAS:
        text_report, text_error = _load_json(example_dir / "build" / "text_boundary_clash.json")
        if text_error is not None:
            reason = "missing build/text_boundary_clash.json"
            if text_error == "malformed":
                reason = "malformed build/text_boundary_clash.json"
            return _finish(
                summary,
                state="missing_input",
                blocking_items=["build/text_boundary_clash.json"],
                next_action=f"/fig_compile {example_dir.name}",
                reason=reason,
            )
        text_candidate_ids, text_candidate_error = _text_boundary_candidate_ids(text_report or {})
        if text_candidate_error is not None:
            return _finish(
                summary,
                state="missing_input",
                blocking_items=["build/text_boundary_clash.json"],
                next_action=f"/fig_compile {example_dir.name}",
                reason="malformed build/text_boundary_clash.json candidates",
            )
        text_refs = _text_boundary_refs(frontmatter)
        text_candidate_id_set = set(text_candidate_ids)
        text_ref_set = set(text_refs)
        text_missing_refs = [
            candidate_id for candidate_id in text_candidate_ids if candidate_id not in text_refs
        ]
        text_unknown_refs = sorted(ref for ref in text_ref_set if ref not in text_candidate_id_set)
        summary["text_boundary"] = {
            "present": True,
            "candidate_count": len(text_candidate_ids),
            "accounted_count": len(text_ref_set & text_candidate_id_set),
            "missing_refs": text_missing_refs,
            "unknown_refs": text_unknown_refs,
        }

    label_path_missing_refs: list[str] = []
    label_path_unknown_refs: list[str] = []
    if critique_schema in LABEL_PATH_ACCOUNTING_SCHEMAS:
        label_report, label_error = _load_json(
            example_dir / "build" / "label_path_proximity.json"
        )
        if label_error == "malformed":
            return _finish(
                summary,
                state="missing_input",
                blocking_items=["build/label_path_proximity.json"],
                next_action=f"/fig_compile {example_dir.name}",
                reason="malformed build/label_path_proximity.json",
            )
        if label_report is not None:
            label_candidate_ids, label_candidate_error = _label_path_candidate_ids(label_report)
            if label_candidate_error is not None:
                return _finish(
                    summary,
                    state="missing_input",
                    blocking_items=["build/label_path_proximity.json"],
                    next_action=f"/fig_compile {example_dir.name}",
                    reason="malformed build/label_path_proximity.json candidates",
                )
            label_refs = _label_path_refs(frontmatter)
            label_candidate_id_set = set(label_candidate_ids)
            label_ref_set = set(label_refs)
            label_path_missing_refs = [
                candidate_id
                for candidate_id in label_candidate_ids
                if candidate_id not in label_refs
            ]
            label_path_unknown_refs = sorted(
                ref for ref in label_ref_set if ref not in label_candidate_id_set
            )
            summary["label_path"] = {
                "present": True,
                "candidate_count": len(label_candidate_ids),
                "accounted_count": len(label_ref_set & label_candidate_id_set),
                "missing_refs": label_path_missing_refs,
                "unknown_refs": label_path_unknown_refs,
            }

    if critique_schema in CROP_AUDIT_ACCOUNTING_SCHEMAS:
        manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
        manifest, manifest_error = _load_json(manifest_path)
        if manifest_error is not None:
            reason = "missing build/audit_crops/manifest.json"
            if manifest_error == "malformed":
                reason = "malformed build/audit_crops/manifest.json"
            return _finish(
                summary,
                state="missing_input",
                blocking_items=["build/audit_crops/manifest.json"],
                next_action=f"/fig_critique {example_dir.name}",
                reason=reason,
            )
        required_ids, required_error = _manifest_required_ids(manifest or {})
        if required_error is not None:
            return _finish(
                summary,
                state="missing_input",
                blocking_items=["build/audit_crops/manifest.json"],
                next_action=f"/fig_critique {example_dir.name}",
                reason="malformed build/audit_crops/manifest.json required crop ids",
            )
        mismatched_crop_ids, mismatch_error = _mismatched_manifest_crop_ids(
            example_dir,
            manifest or {},
            required_ids,
        )
        if mismatch_error is not None:
            return _finish(
                summary,
                state="missing_input",
                blocking_items=["build/audit_crops/manifest.json"],
                next_action=f"/fig_critique {example_dir.name}",
                reason="malformed build/audit_crops/manifest.json crops",
            )
        if mismatched_crop_ids:
            summary["crop_audit"]["manifest_present"] = True
            summary["crop_audit"]["required_count"] = len(required_ids)
            return _finish(
                summary,
                state="stale_or_mismatched",
                blocking_items=mismatched_crop_ids,
                next_action=f"/fig_critique {example_dir.name}",
                reason="audit crop files do not match build/audit_crops/manifest.json",
            )
        verdict_counts, uncertain_crop_ids, logged_crop_ids = _crop_audit_counts(frontmatter)
        missing_crop_log_ids = [
            crop_id for crop_id in required_ids if crop_id not in set(logged_crop_ids)
        ]
        summary["crop_audit"] = {
            "manifest_present": True,
            "required_count": len(required_ids),
            "verdict_counts": verdict_counts,
            "uncertain_crop_ids": uncertain_crop_ids,
        }
        if missing_crop_log_ids:
            return _finish(
                summary,
                state="needs_action",
                blocking_items=missing_crop_log_ids,
                next_action=f"/fig_critique {example_dir.name}",
                reason="crop_audit_log is missing required crop ids",
            )
    else:
        uncertain_crop_ids = []

    accept_gaps = _structured_accept_gaps(frontmatter)
    if missing_refs or unknown_refs:
        blocking_items = missing_refs + unknown_refs
        return _finish(
            summary,
            state="needs_action",
            blocking_items=blocking_items,
            next_action=f"/fig_critique {example_dir.name}",
            reason="visual-clash candidates are not fully accounted in micro_defects",
        )
    if text_missing_refs or text_unknown_refs:
        blocking_items = text_missing_refs + text_unknown_refs
        return _finish(
            summary,
            state="needs_action",
            blocking_items=blocking_items,
            next_action=f"/fig_critique {example_dir.name}",
            reason="text-boundary candidates are not fully accounted in micro_defects",
        )
    if label_path_missing_refs or label_path_unknown_refs:
        blocking_items = label_path_missing_refs + label_path_unknown_refs
        return _finish(
            summary,
            state="needs_action",
            blocking_items=blocking_items,
            next_action=f"/fig_critique {example_dir.name}",
            reason="label-path proximity candidates are not fully accounted in micro_defects",
        )
    if accept_gaps:
        return _finish(
            summary,
            state="needs_action",
            blocking_items=accept_gaps,
            next_action=f"/fig_critique {example_dir.name}",
            reason=(
                "accepted visual-clash candidates need accept_simplification_reason "
                "and rationale"
            ),
        )
    if summary["crop_audit"]["uncertain_crop_ids"]:
        return _finish(
            summary,
            state="needs_action",
            blocking_items=summary["crop_audit"]["uncertain_crop_ids"],
            next_action="human_review: reread uncertain audit crops",
            reason="crop_audit_log contains uncertain crop verdicts",
        )

    return _finish(
        summary,
        state="passed",
        blocking_items=[],
        next_action=f"/fig_loop {example_dir.name} --goal <goal>",
        reason="audit evidence inputs are present and accounted",
    )
