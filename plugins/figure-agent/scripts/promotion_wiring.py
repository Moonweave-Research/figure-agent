"""G4 detector promotion wiring.

This module only routes detector outputs that already exist. It deliberately
does not infer visual intent or add new geometry detectors.
"""

from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths

QUEUE_SCHEMA = "figure-agent.promotion-queue.v1"
TRIAGE_SCHEMA = "figure-agent.promotion-triage.v1"
TEX_ASSERTIONS_SCHEMA = "figure-agent.tex-assertions.v1"
SEMANTIC_ASSERTIONS_SCHEMA = "figure-agent.semantic-assertions.v1"
SUPPORTED_TRIAGE_DEFECT_CLASSES = frozenset(
    {"label_offset", "text_overlap", "whitespace_balance"}
)
ALIGNMENT_ASSERTION_KINDS = frozenset(
    {
        "baseline_aligned",
        "top_aligned",
        "left_aligned",
        "right_aligned",
        "center_aligned_x",
        "center_aligned_y",
    }
)
_PANEL_HINT_RE = re.compile(r"^\s*%\s*Panel\s+([A-Za-z0-9_-]+)\b")


class PromotionWiringError(ValueError):
    """Raised when promotion evidence is missing, corrupt, or unsafe to use."""


AUTO_PROMOTE_ELIGIBILITY: dict[str, dict[str, Any]] = {
    "tex_assertions": {
        "detector": "tex_assertions",
        "promotion_tier": "auto",
        "eligible": True,
        "fail_closed": True,
        "p5_zero_match": True,
        "p5_multi_match": True,
        "blocking_reasons": [],
    },
    "semantic_assertions": {
        "detector": "semantic_assertions",
        "promotion_tier": "auto",
        "eligible": True,
        "fail_closed": True,
        "p5_zero_match": True,
        "p5_multi_match": True,
        "blocking_reasons": [],
    },
}

NON_PROMOTING_DETECTORS: dict[str, dict[str, str]] = {
    "layout_drift": {
        "detector": "layout_drift",
        "promotion_tier": "non_promoting",
        "reason": "reference-relative advisory; intentionally not read for ledger promotion",
    },
    "hyphenation": {
        "detector": "hyphenation",
        "promotion_tier": "non_promoting",
        "reason": "cosmetic advisory; intentionally not read for ledger promotion",
    },
    "physics_grounding": {
        "detector": "physics_grounding",
        "promotion_tier": "non_promoting",
        "reason": "document meta-check advisory; intentionally not read for ledger promotion",
    },
}


def detector_promotion_eligibility(detector: str) -> dict[str, Any]:
    try:
        return dict(AUTO_PROMOTE_ELIGIBILITY[detector])
    except KeyError as exc:
        raise PromotionWiringError(f"unknown_detector:{detector}") from exc


def non_promoting_detector_notes() -> dict[str, dict[str, str]]:
    return {key: dict(value) for key, value in NON_PROMOTING_DETECTORS.items()}


def _load_json_object(path: Path, *, label: str, missing_ok: bool = False) -> dict[str, Any] | None:
    if not path.is_file():
        if missing_ok:
            return None
        raise PromotionWiringError(f"{label}_missing:{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromotionWiringError(f"{label}_unreadable:{path}") from exc
    if not isinstance(payload, dict):
        raise PromotionWiringError(f"{label}_schema:expected_object")
    return payload


def load_detector_report(path: Path, detector: str) -> dict[str, Any]:
    payload = _load_json_object(path, label=detector)
    assert payload is not None
    if detector == "tex_assertions":
        if payload.get("schema") != TEX_ASSERTIONS_SCHEMA:
            raise PromotionWiringError(f"{detector}_schema:{payload.get('schema')}")
        issues = payload.get("issues")
        if not isinstance(issues, list):
            raise PromotionWiringError(f"{detector}_schema:issues")
    elif detector == "semantic_assertions":
        if payload.get("schema") != SEMANTIC_ASSERTIONS_SCHEMA:
            raise PromotionWiringError(f"{detector}_schema:{payload.get('schema')}")
        issues = payload.get("issues")
        if not isinstance(issues, list):
            raise PromotionWiringError(f"{detector}_schema:issues")
    elif detector == "visual_clash":
        _validate_visual_clash_report(payload)
    else:
        raise PromotionWiringError(f"unknown_detector:{detector}")
    return payload


def _validate_visual_clash_report(payload: dict[str, Any]) -> None:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise PromotionWiringError("visual_clash_schema:candidates")
    total = payload.get("total")
    if total is not None and (isinstance(total, bool) or not isinstance(total, int)):
        raise PromotionWiringError("visual_clash_schema:total")
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise PromotionWiringError(f"visual_clash_schema:candidate[{index}]")
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise PromotionWiringError(f"visual_clash_schema:candidate[{index}].id")
        bbox = candidate.get("bbox_px")
        if (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or any(isinstance(value, bool) or not isinstance(value, int) for value in bbox)
        ):
            raise PromotionWiringError(f"visual_clash_schema:candidate[{index}].bbox_px")


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _source_rel(name: str) -> str:
    return f"examples/{name}/{name}.tex"


def _current_source_hashes(example_dir: Path, name: str) -> dict[str, str]:
    source = example_dir / f"{name}.tex"
    if not source.is_file():
        raise PromotionWiringError(f"source_tex_missing:{source}")
    return {_source_rel(name): _hash_file(source)}


def _source_lines(example_dir: Path, name: str) -> list[str]:
    source = example_dir / f"{name}.tex"
    if not source.is_file():
        raise PromotionWiringError(f"source_tex_missing:{source}")
    try:
        return source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise PromotionWiringError(f"source_tex_unreadable:{source}") from exc


def _selector_text_hash(lines: list[str], start: int, end: int) -> str:
    if start < 1 or end < start or end > len(lines):
        raise PromotionWiringError(f"triage_tex_line_out_of_range:{start}:{end}")
    selected = "\n".join(lines[start - 1 : end])
    encoded = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def _semantic_edit_line(lines: list[str], issue: dict[str, Any]) -> int | None:
    edit_target = issue.get("edit_target")
    if not isinstance(edit_target, str) or not edit_target.strip():
        return None
    target = edit_target.strip()
    braced = "{" + target + "}"
    render_lines = [
        (index, line)
        for index, line in enumerate(lines, start=1)
        if not line.lstrip().startswith("%")
    ]
    matches = [
        index
        for index, line in render_lines
        if braced in line
    ]
    if not matches:
        matches = [index for index, line in render_lines if target in line]
    if not matches:
        raise PromotionWiringError(f"semantic_assertions_source_anchor_missing:{target}")
    if len(matches) > 1:
        raise PromotionWiringError(f"semantic_assertions_source_anchor_ambiguous:{target}")
    return matches[0]


def _panel_markers(lines: list[str]) -> list[tuple[int, str]]:
    markers: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        match = _PANEL_HINT_RE.match(line)
        if match:
            markers.append((index, match.group(1)))
    return markers


def _panel_for_line(markers: list[tuple[int, str]], line_number: int) -> str:
    panel = ""
    for marker_line, marker_panel in markers:
        if marker_line > line_number:
            break
        panel = marker_panel
    if not panel:
        raise PromotionWiringError(f"triage_panel_missing:{line_number}")
    return panel


def _visual_clash_evidence(
    name: str,
    item_id: str,
    queue_item: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "uri": f"figure://{name}/audit/visual-clash",
            "node_id": item_id,
            "crop_paths": queue_item.get("crop_paths", []),
            "evidence_inline": queue_item.get("evidence_inline", []),
        }
    ]


def _crop_paths(example_dir: Path, clash_id: str) -> list[Path]:
    crop_dir = example_dir / "build" / "audit_crops" / "visual_clash"
    return sorted(path for path in crop_dir.glob(f"{clash_id}_*.png") if path.is_file())


def _rel(example_dir: Path, path: Path) -> str:
    return path.relative_to(example_dir).as_posix()


def _metric_score(metric: Any) -> float:
    if isinstance(metric, dict):
        numeric = [
            float(value)
            for value in metric.values()
            if not isinstance(value, bool) and isinstance(value, (int, float))
        ]
        return max(numeric) if numeric else 0.0
    if not isinstance(metric, bool) and isinstance(metric, (int, float)):
        return float(metric)
    return 0.0


def build_promotion_queue(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    top_n: int = 5,
    write: bool = False,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    report_path = example_dir / "build" / "visual_clash.json"
    report = load_detector_report(report_path, "visual_clash")
    candidates = [item for item in report["candidates"] if isinstance(item, dict)]
    items: list[dict[str, Any]] = []
    for candidate in candidates:
        clash_id = str(candidate["id"]).strip()
        crops = _crop_paths(example_dir, clash_id)
        if not crops:
            raise PromotionWiringError(f"promotion_queue_missing_crop:{clash_id}")
        evidence_inline = [
            {
                "kind": "image",
                "path": _rel(example_dir, crop),
                "sha256": _hash_file(crop),
            }
            for crop in crops
        ]
        items.append(
            {
                "id": clash_id,
                "source_detector": "visual_clash",
                "promotion_tier": "review_queue",
                "kind": candidate.get("kind"),
                "text": candidate.get("text"),
                "bbox_px": candidate.get("bbox_px"),
                "metric": candidate.get("metric"),
                "crop_paths": [_rel(example_dir, crop) for crop in crops],
                "evidence_inline": evidence_inline,
                "tex_lines": None,
                "defect_class": None,
                "action": "human_review_required",
            }
        )
    ranked = sorted(items, key=lambda item: (-_metric_score(item.get("metric")), str(item["id"])))
    payload = {
        "schema": QUEUE_SCHEMA,
        "fixture": name,
        "source_detector": "visual_clash",
        "source_hashes": _current_source_hashes(example_dir, name),
        "visual_clash_report_sha256": _hash_file(report_path),
        "status": "review_required" if items else "empty",
        "total": len(items),
        "top_items": [str(item["id"]) for item in ranked[:top_n]],
        "items": items,
        "non_promoting_detectors": list(non_promoting_detector_notes().values()),
    }
    if write:
        output = example_dir / "build" / "promotion_queue.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_promotion_queue(path: Path) -> dict[str, Any]:
    payload = _load_json_object(path, label="promotion_queue")
    assert payload is not None
    if payload.get("schema") != QUEUE_SCHEMA:
        raise PromotionWiringError(f"promotion_queue_schema:{payload.get('schema')}")
    items = payload.get("items")
    if not isinstance(items, list):
        raise PromotionWiringError("promotion_queue_schema:items")
    ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise PromotionWiringError(f"promotion_queue_schema:item[{index}]")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise PromotionWiringError(f"promotion_queue_schema:item[{index}].id")
        ids.add(item_id.strip())
    if len(ids) != len(items):
        raise PromotionWiringError("promotion_queue_schema:duplicate_ids")
    source_hashes = payload.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise PromotionWiringError("promotion_queue_schema:source_hashes")
    report_hash = payload.get("visual_clash_report_sha256")
    if not isinstance(report_hash, str) or not report_hash.startswith("sha256:"):
        raise PromotionWiringError("promotion_queue_schema:visual_clash_report_sha256")
    return payload


def _parse_accept_ids(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def _parse_tex_lines(values: list[str]) -> dict[str, list[int]]:
    parsed: dict[str, list[int]] = {}
    for value in values:
        parts = value.split(":")
        if len(parts) != 3:
            raise PromotionWiringError(f"tex_lines_invalid:{value}")
        item_id, start_raw, end_raw = parts
        try:
            start = int(start_raw)
            end = int(end_raw)
        except ValueError as exc:
            raise PromotionWiringError(f"tex_lines_invalid:{value}") from exc
        if start < 1 or end < start:
            raise PromotionWiringError(f"tex_lines_invalid:{value}")
        parsed[item_id] = [start, end]
    return parsed


def _parse_defect_classes(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        parts = value.split(":")
        if len(parts) != 2:
            raise PromotionWiringError(f"defect_class_invalid:{value}")
        item_id, defect_class = parts
        if defect_class not in SUPPORTED_TRIAGE_DEFECT_CLASSES:
            raise PromotionWiringError(f"defect_class_unsupported:{defect_class}")
        parsed[item_id] = defect_class
    return parsed


def triage_promotion_queue(
    name: str,
    *,
    accept: str,
    reject_rest: bool,
    tex_lines: list[str],
    defect_classes: list[str],
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    queue_path = example_dir / "build" / "promotion_queue.json"
    report_path = example_dir / "build" / "visual_clash.json"
    queue = load_promotion_queue(queue_path)
    report = load_detector_report(report_path, "visual_clash")
    queue_fixture = queue.get("fixture")
    if queue_fixture != name:
        raise PromotionWiringError(f"promotion_queue_fixture_mismatch:{queue_fixture}")
    current_source_hashes = _current_source_hashes(example_dir, name)
    if queue.get("source_hashes") != current_source_hashes:
        raise PromotionWiringError("promotion_queue_source_hash_mismatch")
    if queue.get("visual_clash_report_sha256") != _hash_file(report_path):
        raise PromotionWiringError("promotion_queue_visual_clash_hash_mismatch")
    report_ids = {
        str(item["id"]).strip()
        for item in report["candidates"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    items = {
        str(item["id"]): item
        for item in queue["items"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    accepted_ids = _parse_accept_ids(accept)
    unknown = sorted(accepted_ids - set(items))
    if unknown:
        raise PromotionWiringError(f"triage_unknown_ids:{','.join(unknown)}")
    line_map = _parse_tex_lines(tex_lines)
    class_map = _parse_defect_classes(defect_classes)
    missing_lines = sorted(accepted_ids - set(line_map))
    missing_classes = sorted(accepted_ids - set(class_map))
    if missing_lines:
        raise PromotionWiringError(f"triage_missing_tex_lines:{','.join(missing_lines)}")
    if missing_classes:
        raise PromotionWiringError(f"triage_missing_defect_class:{','.join(missing_classes)}")
    missing_report = sorted(accepted_ids - report_ids)
    if missing_report:
        raise PromotionWiringError(f"triage_missing_visual_clash_ids:{','.join(missing_report)}")
    lines = _source_lines(example_dir, name)
    panel_markers = _panel_markers(lines)
    accepted: list[dict[str, Any]] = []
    for item_id in sorted(accepted_ids):
        item = items[item_id]
        evidence_inline = item.get("evidence_inline")
        if not isinstance(evidence_inline, list) or not evidence_inline:
            raise PromotionWiringError(f"triage_missing_evidence_crop:{item_id}")
        for evidence_item in evidence_inline:
            if not isinstance(evidence_item, dict):
                raise PromotionWiringError(f"triage_evidence_schema:{item_id}")
            crop_path = evidence_item.get("path")
            expected_hash = evidence_item.get("sha256")
            if not isinstance(crop_path, str) or not isinstance(expected_hash, str):
                raise PromotionWiringError(f"triage_evidence_schema:{item_id}")
            resolved_crop = example_dir / crop_path
            if not resolved_crop.is_file() or _hash_file(resolved_crop) != expected_hash:
                raise PromotionWiringError(f"triage_evidence_hash_mismatch:{item_id}")
        defect_class = class_map[item_id]
        start, end = line_map[item_id]
        selector_hint: dict[str, Any] = {"kind": "line_range", "value": f"{start}:{end}"}
        selector_hint["selector_text_hash"] = _selector_text_hash(lines, start, end)
        panel = _panel_for_line(panel_markers, start)
        accepted.append(
            {
                "id": item_id,
                "promoted_by": "triage",
                "source_detector": "visual_clash",
                "tex_lines": [start, end],
                "defect_class": defect_class,
                "selector_hint": selector_hint,
                "target": {"panel": panel, "subregion": f"{defect_class}#0"},
                "bbox_px": item.get("bbox_px"),
                "text": item.get("text"),
                "evidence": _visual_clash_evidence(name, item_id, item),
            }
        )
    rejected = sorted(set(items) - accepted_ids) if reject_rest else []
    payload = {
        "schema": TRIAGE_SCHEMA,
        "fixture": name,
        "promotion_queue_sha256": _hash_file(queue_path),
        "visual_clash_report_sha256": _hash_file(report_path),
        "source_hashes": current_source_hashes,
        "accepted": accepted,
        "rejected": rejected,
    }
    if write:
        output = example_dir / "build" / "promotion_triage.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_promotion_triage(path: Path, *, missing_ok: bool = True) -> dict[str, Any] | None:
    payload = _load_json_object(path, label="promotion_triage", missing_ok=missing_ok)
    if payload is None:
        return None
    if payload.get("schema") != TRIAGE_SCHEMA:
        raise PromotionWiringError(f"promotion_triage_schema:{payload.get('schema')}")
    accepted = payload.get("accepted")
    rejected = payload.get("rejected")
    if not isinstance(accepted, list) or not isinstance(rejected, list):
        raise PromotionWiringError("promotion_triage_schema:accepted_rejected")
    source_hashes = payload.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise PromotionWiringError("promotion_triage_schema:source_hashes")
    queue_hash = payload.get("promotion_queue_sha256")
    if not isinstance(queue_hash, str) or not queue_hash.startswith("sha256:"):
        raise PromotionWiringError("promotion_triage_schema:promotion_queue_sha256")
    report_hash = payload.get("visual_clash_report_sha256")
    if not isinstance(report_hash, str) or not report_hash.startswith("sha256:"):
        raise PromotionWiringError("promotion_triage_schema:visual_clash_report_sha256")
    return payload


def auto_promoted_defects(example_dir: Path, name: str) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = []
    defects.extend(_auto_promoted_tex_defects(example_dir, name))
    defects.extend(_auto_promoted_semantic_defects(example_dir, name))
    return defects


def _auto_promoted_tex_defects(example_dir: Path, name: str) -> list[dict[str, Any]]:
    report_path = example_dir / "build" / "tex_assertions.json"
    if not report_path.is_file():
        return []
    report = load_detector_report(report_path, "tex_assertions")
    if report.get("source_tex") != f"{name}.tex":
        raise PromotionWiringError(f"tex_assertions_source_tex_mismatch:{report.get('source_tex')}")
    source_hashes = report.get("source_hashes")
    if source_hashes != _current_source_hashes(example_dir, name):
        raise PromotionWiringError("tex_assertions_source_hash_mismatch")
    promotable_issues: list[dict[str, Any]] = []
    for issue in report["issues"]:
        if not isinstance(issue, dict):
            raise PromotionWiringError("tex_assertions_schema:issue")
        status = issue.get("status")
        if status in {"violated", "anchor_missing", "anchor_ambiguous"}:
            promotable_issues.append(issue)
    if not promotable_issues:
        return []
    defects: list[dict[str, Any]] = []
    for issue in promotable_issues:
        status = issue.get("status")
        issue_id = str(issue.get("id") or "tex_assertion")
        evidence: dict[str, Any] = {
            "uri": f"figure://{name}/audit/tex-assertions",
            "node_id": issue_id,
            "status": status,
        }
        for key in ("measured_delta_cm", "delta_cm", "margin_cm"):
            if key in issue:
                evidence[key] = issue[key]
        defects.append(
            {
                "source": "deterministic_audit",
                "source_detector": "tex_assertions",
                "promoted_by": "auto",
                "evidence": [evidence],
                "severity": "action",
                "owner": "tool",
                "defect_class": "tex_assertion_violation",
                "affected_files": [f"examples/{name}/{name}.tex"],
                "freshness": {"state": "fresh", "source_hashes": source_hashes},
                "selector_hint": {"kind": "assertion_id", "value": issue_id},
                "target": {"panel": "unknown", "subregion": "tex_assertion_violation#0"},
                "suggested_change": {
                    "operation_type": "human_review_required",
                    "summary": str(
                        issue.get("message")
                        or "Resolve declared TeX assertion violation"
                    ),
                    "patch": "",
                },
            }
        )
    return defects


def _auto_promoted_semantic_defects(example_dir: Path, name: str) -> list[dict[str, Any]]:
    report_path = example_dir / "build" / "semantic_assertions.json"
    if not report_path.is_file():
        return []
    report = load_detector_report(report_path, "semantic_assertions")
    source_hashes = report.get("source_hashes")
    if source_hashes != _current_source_hashes(example_dir, name):
        raise PromotionWiringError("semantic_assertions_source_hash_mismatch")
    lines = _source_lines(example_dir, name)
    defects: list[dict[str, Any]] = []
    for issue in report["issues"]:
        if not isinstance(issue, dict):
            raise PromotionWiringError("semantic_assertions_schema:issue")
        status = issue.get("status")
        if status not in {"violated", "anchor_missing", "anchor_ambiguous"}:
            continue
        issue_id = str(issue.get("id") or "semantic_assertion")
        kind = issue.get("kind")
        is_alignment = kind in ALIGNMENT_ASSERTION_KINDS
        edit_line = (
            _semantic_edit_line(lines, issue)
            if is_alignment and status == "violated"
            else None
        )
        actionable_alignment = is_alignment and status == "violated" and edit_line is not None
        selector_hint: dict[str, Any] = {"kind": "assertion_id", "value": issue_id}
        if edit_line is not None:
            selector_hint = {
                "kind": "line_range",
                "value": f"{edit_line}:{edit_line}",
                "assertion_id": issue_id,
                "edit_target": issue.get("edit_target"),
                "selector_text_hash": _selector_text_hash(lines, edit_line, edit_line),
            }
        panel = issue.get("target_panel")
        if not isinstance(panel, str) or not panel.strip():
            panel = "unknown"
        evidence: dict[str, Any] = {
            "uri": f"figure://{name}/audit/semantic-assertions",
            "node_id": issue_id,
            "status": status,
        }
        for key in (
            "kind",
            "targets",
            "edit_target",
            "measured_delta_pt",
            "measured_delta_cm",
            "tolerance_cm",
        ):
            if key in issue:
                evidence[key] = issue[key]
        defects.append(
            {
                "source": "deterministic_audit",
                "source_detector": "semantic_assertions",
                "promoted_by": "auto",
                "evidence": [evidence],
                "severity": "action",
                "owner": "tool",
                "defect_class": "label_offset"
                if actionable_alignment
                else "semantic_assertion_violation",
                "affected_files": [f"examples/{name}/{name}.tex"],
                "freshness": {"state": "fresh", "source_hashes": source_hashes},
                "selector_hint": selector_hint,
                "target": {"panel": panel.strip(), "subregion": f"{issue_id}#0"},
                "suggested_change": {
                    "operation_type": "bounded_coordinate_offset"
                    if actionable_alignment
                    else "human_review_required",
                    "summary": str(
                        issue.get("message")
                        or "Resolve declared semantic assertion violation"
                    ),
                    "patch": "",
                },
            }
        )
    return defects


def triage_promoted_defects(example_dir: Path, name: str) -> list[dict[str, Any]]:
    triage_path = example_dir / "build" / "promotion_triage.json"
    triage = load_promotion_triage(triage_path)
    if triage is None:
        return []
    if triage.get("fixture") != name:
        raise PromotionWiringError(f"promotion_triage_fixture_mismatch:{triage.get('fixture')}")
    queue_path = example_dir / "build" / "promotion_queue.json"
    report_path = example_dir / "build" / "visual_clash.json"
    queue = load_promotion_queue(queue_path)
    report = load_detector_report(report_path, "visual_clash")
    if triage.get("promotion_queue_sha256") != _hash_file(queue_path):
        raise PromotionWiringError("promotion_triage_queue_hash_mismatch")
    if triage.get("visual_clash_report_sha256") != _hash_file(report_path):
        raise PromotionWiringError("promotion_triage_visual_clash_hash_mismatch")
    current_source_hashes = _current_source_hashes(example_dir, name)
    if triage.get("source_hashes") != current_source_hashes:
        raise PromotionWiringError("promotion_triage_source_hash_mismatch")
    queue_items = {
        str(item["id"]): item
        for item in queue["items"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    report_ids = {
        str(item["id"]).strip()
        for item in report["candidates"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    defects: list[dict[str, Any]] = []
    for item in triage["accepted"]:
        if not isinstance(item, dict):
            raise PromotionWiringError("promotion_triage_schema:accepted_item")
        item_id = item.get("id")
        defect_class = item.get("defect_class")
        tex_lines = item.get("tex_lines")
        if (
            not isinstance(item_id, str)
            or defect_class not in SUPPORTED_TRIAGE_DEFECT_CLASSES
            or not isinstance(tex_lines, list)
            or len(tex_lines) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in tex_lines)
        ):
            raise PromotionWiringError("promotion_triage_schema:accepted_item")
        if item_id not in queue_items or item_id not in report_ids:
            raise PromotionWiringError(f"promotion_triage_missing_source_item:{item_id}")
        queue_item = queue_items[item_id]
        queue_evidence = queue_item.get("evidence_inline")
        if not isinstance(queue_evidence, list) or not queue_evidence:
            raise PromotionWiringError(f"promotion_triage_missing_evidence_crop:{item_id}")
        for evidence_item in queue_evidence:
            if not isinstance(evidence_item, dict):
                raise PromotionWiringError(f"promotion_triage_schema:evidence_inline:{item_id}")
            crop_path = evidence_item.get("path")
            expected_hash = evidence_item.get("sha256")
            if not isinstance(crop_path, str) or not isinstance(expected_hash, str):
                raise PromotionWiringError(f"promotion_triage_schema:evidence_inline:{item_id}")
            resolved_crop = example_dir / crop_path
            if not resolved_crop.is_file() or _hash_file(resolved_crop) != expected_hash:
                raise PromotionWiringError(f"promotion_triage_evidence_hash_mismatch:{item_id}")
        start, end = tex_lines
        selector_hint = item.get("selector_hint")
        if not isinstance(selector_hint, dict) or not isinstance(
            selector_hint.get("selector_text_hash"),
            str,
        ):
            raise PromotionWiringError(f"promotion_triage_selector_hash_missing:{item_id}")
        target = item.get("target")
        if not isinstance(target, dict) or not isinstance(target.get("panel"), str):
            raise PromotionWiringError(f"promotion_triage_target_missing:{item_id}")
        defects.append(
            {
                "source": "critique_adjudication",
                "source_detector": "visual_clash",
                "promoted_by": "triage",
                "evidence": _visual_clash_evidence(name, item_id, queue_item),
                "severity": "action",
                "owner": "tool",
                "defect_class": defect_class,
                "affected_files": [f"examples/{name}/{name}.tex"],
                "freshness": {"state": "fresh", "source_hashes": current_source_hashes},
                "selector_hint": selector_hint,
                "target": target,
                "suggested_change": {
                    "operation_type": "tikz_coordinate_adjust",
                    "summary": f"Resolve triaged visual_clash {item_id}",
                    "patch": "",
                },
            }
        )
    return defects


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="promotion_wiring")
    sub = parser.add_subparsers(dest="command", required=True)
    queue_parser = sub.add_parser("promotion-queue")
    queue_parser.add_argument("name")
    queue_parser.add_argument("--write", action="store_true")
    queue_parser.add_argument("--json", action="store_true")
    triage_parser = sub.add_parser("triage")
    triage_parser.add_argument("name")
    triage_parser.add_argument("--accept", required=True)
    triage_parser.add_argument("--reject-rest", action="store_true")
    triage_parser.add_argument("--tex-lines", action="append", default=[])
    triage_parser.add_argument("--defect-class", action="append", default=[])
    triage_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "promotion-queue":
            payload = build_promotion_queue(
                args.name,
                plugin_root=plugin_root,
                workspace_root=workspace_root,
                write=args.write,
            )
        else:
            payload = triage_promotion_queue(
                args.name,
                accept=args.accept,
                reject_rest=args.reject_rest,
                tex_lines=args.tex_lines,
                defect_classes=args.defect_class,
                plugin_root=plugin_root,
                workspace_root=workspace_root,
            )
    except PromotionWiringError as exc:
        print(f"fig-agent {args.command}: {exc}")
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
