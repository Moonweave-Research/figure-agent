"""Generate deterministic candidate improvement sets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import bounded_coordinate_offset
import bounded_text_width
import candidate_contracts
import candidate_families
import critique_adjudication
import critique_contract
import figure_intent_model
import fixture_identity
import label_refit_derive
import quality_defect_ledger
import runtime_paths
from check_visual_clash import extract_pdf_words_and_page
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"
ZERO_HASH = "sha256:" + "0" * 64
COORDINATE_OFFSET_DEFECT_CLASSES = frozenset({"label_offset", "text_overlap", "whitespace_balance"})
ACTIONABILITY_REFUSAL_CODES = frozenset(
    {
        "stale_detector_evidence",
        "unknown_panel",
        "missing_selector_hash",
        "unsupported_candidate_family",
    }
)
EDIT_FAMILY = "bounded_coordinate_offset"
FAMILY = "bounded-coordinate-offset"
VARIANT_ID = "dx+0.10cm"
SEVERITY_RANK = {"blocker": 0, "action": 1, "major": 2, "minor": 3, "nit": 4}


class CandidateGeneratorError(ValueError):
    """Raised when candidate generation would violate fixture-local bounds."""


def _source_hash(source: Path) -> str:
    return file_sha256(source) if source.is_file() else ZERO_HASH


def _load_history_suppressions(
    paths: runtime_paths.RuntimePaths,
    name: str,
) -> dict[tuple[str, str], str]:
    path = paths.plugin_root / "docs" / "experience-log" / f"{name}.jsonl"
    for label, item in (
        ("docs", paths.plugin_root / "docs"),
        ("experience_log", paths.plugin_root / "docs" / "experience-log"),
        ("experience_log", path),
    ):
        if item.is_symlink():
            raise CandidateGeneratorError(f"{label}_symlink")
    if not path.is_file():
        return {}
    suppressions: dict[tuple[str, str], str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise CandidateGeneratorError("experience_log_unreadable") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CandidateGeneratorError(f"experience_record_invalid:{line_number}") from exc
        if not isinstance(record, dict):
            raise CandidateGeneratorError(f"experience_record_invalid:{line_number}")
        state = record.get("state") if isinstance(record.get("state"), dict) else {}
        target = state.get("target") if isinstance(state.get("target"), dict) else {}
        action = record.get("action") if isinstance(record.get("action"), dict) else {}
        outcome = record.get("outcome") if isinstance(record.get("outcome"), dict) else {}
        family = action.get("edit_family")
        subregion_key = target.get("subregion_key")
        if not isinstance(family, str) or not isinstance(subregion_key, str):
            continue
        reason = _suppression_reason(outcome)
        if reason is not None:
            suppressions[(family, subregion_key)] = reason
    return suppressions


def _suppression_reason(outcome: dict[str, Any]) -> str | None:
    if outcome.get("quality_movement") == "regressed":
        return "regressed"
    for key in ("human_label", "human_decision_kind", "apply_status"):
        value = outcome.get(key)
        if isinstance(value, str) and value.lower() in {"reject", "rejected"}:
            return "rejected"
    return None


def _validate_output_path(
    *,
    paths: runtime_paths.RuntimePaths,
    name: str,
    output_path: Path | None,
) -> None:
    if output_path is None:
        return
    try:
        candidate_contracts.fixture_local_output_path(
            paths.workspace_root,
            name,
            output_path.as_posix(),
        )
    except (ValueError, candidate_contracts.CandidateContractError) as exc:
        raise CandidateGeneratorError(str(exc)) from exc


def _fixture_source_path(paths: runtime_paths.RuntimePaths, name: str) -> Path:
    fixture = paths.examples_dir / name
    if fixture.is_symlink():
        raise CandidateGeneratorError("fixture_symlink_forbidden")
    lexical_source = fixture / f"{name}.tex"
    if lexical_source.is_symlink():
        raise CandidateGeneratorError("source_symlink_forbidden")
    source = candidate_contracts.fixture_relative_path(fixture, f"{name}.tex")
    return source


def _authority_floor(name: str, paths: runtime_paths.RuntimePaths) -> str:
    intent = figure_intent_model.build_intent_model(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    panels = intent.get("panels")
    if not isinstance(panels, list) or not panels:
        return "review_only"
    floors = [panel.get("apply_authority_floor") for panel in panels if isinstance(panel, dict)]
    if "rejected" in floors:
        return "rejected"
    if "review_only" in floors:
        return "review_only"
    if "apply_eligible" in floors:
        return "apply_eligible"
    return "review_only"


def _label_offset_candidate(
    *,
    name: str,
    candidate_id: str,
    source_rel: Path,
    line_number: int,
    line: str,
    replacement: str,
    apply_authority: str,
    target: dict[str, str],
    source_hash: str,
    source_defect: dict[str, Any] | None = None,
    edit_class: str = "label_offset",
    variant_id: str = VARIANT_ID,
    variant_dx_cm: float = 0.1,
    selector_text_hash: str | None = None,
) -> dict[str, Any]:
    selector = {
        "kind": "line_range_with_hash",
        "path": source_rel.as_posix(),
        "start_line": line_number,
        "end_line": line_number,
        "original_hash": candidate_contracts.canonical_hash(line),
        "source_hash": source_hash,
    }
    if selector_text_hash is not None:
        selector["selector_text_hash"] = selector_text_hash
    candidate = {
        "id": candidate_id,
        "target": target,
        "edit_class": edit_class,
        "edit_family": EDIT_FAMILY,
        "family": FAMILY,
        "variant_id": variant_id,
        "variant": {"id": variant_id, "dx_cm": variant_dx_cm},
        "source_hash": source_hash,
        "affected_files": [source_rel.as_posix()],
        "selector": selector,
        "operations": [
            {
                "kind": "replace_text",
                "semantic_kind": EDIT_FAMILY,
                "path": source_rel.as_posix(),
                "original": line,
                "replacement": replacement,
            }
        ],
        "risk": "low",
        "expected_delta": ["improve label clearance"],
        "semantic_risks": [],
        "rollback": {"strategy": "reverse_operations"},
        "verification": {
            "required_commands": [
                f"fig-agent compile {name} --strict",
                f"fig-agent status {name} --json",
            ]
        },
        "apply_authority": apply_authority,
        "blocked_if": ["semantic_invariant_failed", "render_failed"],
    }
    if source_defect is not None:
        candidate["source_defect"] = source_defect
    candidate["candidate_hash"] = candidate_contracts.canonical_hash(
        {
            "edit_family": EDIT_FAMILY,
            "source_defect": source_defect or {},
            "source_hash": source_hash,
            "source_path": source_rel.as_posix(),
            "start_line": line_number,
            "variant_id": variant_id,
        }
    )
    return candidate


def _fallback_actionability_gaps(defect: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    freshness = defect.get("freshness")
    if isinstance(freshness, dict) and freshness.get("state") == "stale":
        gaps.append("stale_detector_evidence")
    target = defect.get("target")
    if not isinstance(target, dict):
        gaps.append("unknown_panel")
    else:
        panel = target.get("panel")
        if not isinstance(panel, str) or not panel.strip() or panel.strip() == "unknown":
            gaps.append("unknown_panel")
    selector = defect.get("selector_hint")
    if not isinstance(selector, dict) or not isinstance(selector.get("selector_text_hash"), str):
        gaps.append("missing_selector_hash")
    return gaps


def _actionability_refusals(defect: dict[str, Any]) -> list[dict[str, str]]:
    actionability = defect.get("actionability")
    raw_gaps = actionability.get("gaps") if isinstance(actionability, dict) else None
    gaps = (
        [gap for gap in raw_gaps if isinstance(gap, str)]
        if isinstance(raw_gaps, list)
        else _fallback_actionability_gaps(defect)
    )
    defect_id = str(defect.get("id") or "")
    return [
        {"code": gap, "defect_id": defect_id} for gap in gaps if gap in ACTIONABILITY_REFUSAL_CODES
    ]


def _append_refusals(refusals: list[dict[str, str]], additions: list[dict[str, str]]) -> None:
    existing = {(item.get("code"), item.get("defect_id")) for item in refusals}
    for addition in additions:
        key = (addition.get("code"), addition.get("defect_id"))
        if key not in existing:
            refusals.append(addition)
            existing.add(key)


def _source_hash_refusals(
    defect: dict[str, Any],
    source_rel: Path,
    current_source_hash: str,
) -> list[dict[str, str]]:
    freshness = defect.get("freshness")
    source_hashes = freshness.get("source_hashes") if isinstance(freshness, dict) else None
    expected = source_hashes.get(source_rel.as_posix()) if isinstance(source_hashes, dict) else None
    if expected != current_source_hash:
        return [{"code": "stale_detector_evidence", "defect_id": str(defect.get("id") or "")}]
    return []


def _selector_start_line(defect: dict[str, Any], line_count: int) -> int | None:
    selector = defect.get("selector_hint")
    if not isinstance(selector, dict) or selector.get("kind") != "line_range":
        return None
    value = selector.get("value")
    if not isinstance(value, str) or ":" not in value:
        return None
    start = value.split(":", 1)[0].strip()
    if not start.isdigit():
        return None
    line_number = int(start)
    if line_number < 1 or line_number > line_count:
        return None
    return line_number


def _candidate_target(defect: dict[str, Any]) -> dict[str, str]:
    target = defect.get("target")
    return {
        "panel": str(target.get("panel") or "unknown") if isinstance(target, dict) else "unknown",
        "subregion": str(target.get("subregion") or "label-a")
        if isinstance(target, dict)
        else "label-a",
    }


def _source_defect(defect: dict[str, Any], ledger_hash: str) -> dict[str, Any]:
    return {
        "id": str(defect.get("id") or ""),
        "source": str(defect.get("source") or ""),
        "defect_class": str(defect.get("defect_class") or ""),
        "evidence": defect.get("evidence") or [],
        "source_fingerprint": str(defect.get("source_fingerprint") or ""),
        "ledger_hash": ledger_hash,
    }


def _defect_sort_key(
    defect: dict[str, Any],
    source_rel: Path,
    line_number: int,
) -> tuple[int, str, str, int, str, str, str]:
    severity = str(defect.get("severity") or "")
    return (
        SEVERITY_RANK.get(severity.lower(), 99),
        _candidate_target(defect)["panel"],
        source_rel.as_posix(),
        line_number,
        str(defect.get("source_fingerprint") or ""),
        EDIT_FAMILY,
        VARIANT_ID,
    )


def _defect_node_id(defect: dict[str, Any]) -> str | None:
    evidence = defect.get("evidence")
    if not isinstance(evidence, list):
        return None
    for entry in evidence:
        if isinstance(entry, dict):
            node_id = entry.get("node_id")
            if isinstance(node_id, str) and node_id.strip():
                return node_id.strip()
    return None


def _detector_candidate_index(example_dir: Path) -> dict[str, dict[str, Any]]:
    report = example_dir / "build" / "undeclared_geometry.json"
    if not report.is_file():
        return {}
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        return {}
    index: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
            index[candidate["id"]] = candidate
    return index


def _word_bbox_for_text(
    words: list[dict[str, Any]],
    nearest_text: str,
    line_bbox_pt: list[float],
) -> list[float] | None:
    """Return the bbox of the word matching nearest_text closest to the line."""
    line_cx = (line_bbox_pt[0] + line_bbox_pt[2]) / 2.0
    line_cy = (line_bbox_pt[1] + line_bbox_pt[3]) / 2.0
    best: list[float] | None = None
    best_dist = float("inf")
    for word in words:
        if str(word.get("text", "")) != nearest_text:
            continue
        try:
            bbox = [
                float(word["xmin"]),
                float(word["ymin"]),
                float(word["xmax"]),
                float(word["ymax"]),
            ]
        except (KeyError, TypeError, ValueError):
            continue
        word_cx = (bbox[0] + bbox[2]) / 2.0
        word_cy = (bbox[1] + bbox[3]) / 2.0
        dist = (word_cx - line_cx) ** 2 + (word_cy - line_cy) ** 2
        if dist < best_dist:
            best_dist = dist
            best = bbox
    return best


def _geometry_aware_replacement(
    defect: dict[str, Any],
    line: str,
    detector_index: dict[str, dict[str, Any]],
    pdf_path: Path,
) -> str | None:
    """Offset the near-miss line away from its flagged text, axis- and sign-aware.

    Falls back to None whenever the detector geometry or rendered words are not
    available, so the caller can use the blind first-coordinate offset.
    """
    node_id = _defect_node_id(defect)
    if node_id is None:
        return None
    detector_candidate = detector_index.get(node_id)
    if not isinstance(detector_candidate, dict):
        return None
    line_bbox = detector_candidate.get("bbox_pt")
    nearest_text = detector_candidate.get("nearest_text")
    if not isinstance(line_bbox, list) or len(line_bbox) != 4:
        return None
    if not isinstance(nearest_text, str) or not nearest_text:
        return None
    if not pdf_path.is_file():
        return None
    try:
        words, _page = extract_pdf_words_and_page(pdf_path)
    except Exception:  # noqa: BLE001 - rendered words are best-effort
        return None
    word_bbox = _word_bbox_for_text(words, nearest_text, line_bbox)
    if word_bbox is None:
        return None
    direction = bounded_coordinate_offset.offset_direction(line_bbox, word_bbox)
    if direction is None:
        return None
    axis, dx_cm = direction
    return bounded_coordinate_offset.offset_all_coordinates(line, axis=axis, dx_cm=dx_cm)


def _defect_candidates(
    name: str,
    paths: runtime_paths.RuntimePaths,
    lines: list[str],
    source_rel: Path,
    current_source_hash: str,
    apply_authority: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    ledger = quality_defect_ledger.build_quality_defect_ledger(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    defects = ledger.get("defects")
    if not isinstance(defects, list):
        return (
            [],
            [],
            {
                "safe_candidate_defect_count": 0,
                "candidate_supported_defect_count": 0,
                "unsupported_safe_defect_count": 0,
            },
        )
    refusals: list[dict[str, str]] = []
    sortable_candidates: list[tuple[tuple[int, str, str, int, str, str, str], dict[str, Any]]] = []
    safe_count = 0
    supported_count = 0
    unsupported_count = 0
    ledger_hash = str(ledger.get("ledger_hash") or "")
    example_dir = paths.examples_dir / name
    detector_index = _detector_candidate_index(example_dir)
    pdf_path = example_dir / "build" / f"{name}.pdf"
    history_suppressions = _load_history_suppressions(paths, name)
    for defect in defects:
        if not isinstance(defect, dict):
            continue
        if (defect.get("patchability") or {}).get("state") != "safe_candidate":
            continue
        safe_count += 1
        defect_class = str(defect.get("defect_class") or "")
        if defect_class not in COORDINATE_OFFSET_DEFECT_CLASSES:
            unsupported_count += 1
            _append_refusals(
                refusals,
                [
                    {
                        "code": "unsupported_candidate_family",
                        "defect_id": str(defect.get("id") or ""),
                    }
                ],
            )
            continue
        actionability_refusals = _actionability_refusals(defect)
        if actionability_refusals:
            _append_refusals(refusals, actionability_refusals)
            continue
        source_hash_refusals = _source_hash_refusals(defect, source_rel, current_source_hash)
        if source_hash_refusals:
            _append_refusals(refusals, source_hash_refusals)
            continue
        selector = defect.get("selector_hint")
        selector_hash = (
            selector.get("selector_text_hash") if isinstance(selector, dict) else None
        )
        if isinstance(selector_hash, str):
            suppressed_outcome = history_suppressions.get((EDIT_FAMILY, selector_hash))
            if suppressed_outcome is not None:
                _append_refusals(
                    refusals,
                    [
                        {
                            "code": "suppressed_by_history",
                            "defect_id": str(defect.get("id") or ""),
                            "edit_family": EDIT_FAMILY,
                            "subregion_key": selector_hash,
                            "outcome": suppressed_outcome,
                        }
                    ],
                )
                continue
        line_number = _selector_start_line(defect, len(lines))
        if line_number is None:
            continue
        supported_count += 1
        line = lines[line_number - 1]
        replacement = _geometry_aware_replacement(defect, line, detector_index, pdf_path)
        if replacement is None:
            replacement = bounded_coordinate_offset.offset_first_coordinate(line)
        if replacement is None:
            _append_refusals(
                refusals,
                [{"code": "no_bounded_operation", "defect_id": str(defect.get("id") or "")}],
            )
            continue
        candidate = _label_offset_candidate(
            name=name,
            candidate_id="",
            source_rel=source_rel,
            line_number=line_number,
            line=line,
            replacement=replacement,
            apply_authority=apply_authority,
            target=_candidate_target(defect),
            source_hash=current_source_hash,
            source_defect=_source_defect(defect, ledger_hash),
            selector_text_hash=selector_hash if isinstance(selector_hash, str) else None,
        )
        sortable_candidates.append((_defect_sort_key(defect, source_rel, line_number), candidate))
    candidates: list[dict[str, Any]] = []
    for index, (_sort_key, candidate) in enumerate(sorted(sortable_candidates), start=1):
        candidate["id"] = f"CAND{index:03d}"
        candidates.append(candidate)
    return (
        candidates,
        refusals,
        {
            "safe_candidate_defect_count": safe_count,
            "candidate_supported_defect_count": supported_count,
            "unsupported_safe_defect_count": unsupported_count,
        },
    )


def _candidate_metrics(
    candidates: list[dict[str, Any]],
    refusals: list[dict[str, str]],
    defect_counts: dict[str, int],
) -> dict[str, int | float]:
    supported_count = defect_counts["candidate_supported_defect_count"]
    candidate_defect_ids = {
        str(candidate.get("source_defect", {}).get("id") or "")
        for candidate in candidates
        if isinstance(candidate.get("source_defect"), dict)
    }
    return {
        "safe_candidate_defect_count": defect_counts["safe_candidate_defect_count"],
        "candidate_count": len(candidates),
        "candidate_defect_coverage": len(candidate_defect_ids) / supported_count
        if supported_count
        else 0.0,
        "refusal_count": len(refusals),
        "candidate_with_panel_count": sum(
            1
            for candidate in candidates
            if isinstance(candidate.get("target"), dict) and candidate["target"].get("panel")
        ),
        "candidate_with_family_count": sum(
            1 for candidate in candidates if isinstance(candidate.get("edit_family"), str)
        ),
        "candidate_with_source_hash_count": sum(
            1 for candidate in candidates if isinstance(candidate.get("source_hash"), str)
        ),
        "variant_count": len(
            {
                str(candidate.get("variant_id") or "")
                for candidate in candidates
                if candidate.get("variant_id")
            }
        ),
    }


def _finding_refit(finding: dict[str, Any], line: str) -> tuple[str, str, str, float] | None:
    """A `proposed_edit` (edit_class=label_refit) drives a value-preserving footprint
    refit: set the node's text-width AND reposition it, both bounded. This is the
    combined edit a single coordinate offset cannot author (e.g. widen a wrapped
    caption to one line so it fits the clean gap below a crossed axis). Text is never
    changed, so it rides the existing labels_unchanged verifier."""
    proposed = finding.get("proposed_edit")
    if not isinstance(proposed, dict) or proposed.get("edit_class") != "label_refit":
        return None
    target_cm = proposed.get("text_width_cm")
    reposition = proposed.get("reposition")
    if not isinstance(target_cm, (int, float)) or isinstance(target_cm, bool):
        return None
    if not isinstance(reposition, dict):
        return None
    axis = reposition.get("axis")
    dx_cm = reposition.get("dx_cm")
    if axis not in ("x", "y") or not isinstance(dx_cm, (int, float)) or isinstance(dx_cm, bool):
        return None
    widened = bounded_text_width.set_text_width(line, target_cm=float(target_cm))
    if widened is None:
        return None
    replacement = bounded_coordinate_offset.reposition_coordinate(
        widened, axis=axis, dx_cm=float(dx_cm)
    )
    if replacement is None:
        return None
    return (
        replacement,
        "label_refit",
        f"refit_w{float(target_cm):.2f}cm_{axis}{float(dx_cm):+.2f}cm",
        float(dx_cm),
    )


def _finding_offset(finding: dict[str, Any], line: str) -> tuple[str, str, str, float] | None:
    """Resolve (replacement, edit_class, variant_id, variant_dx_cm) for a finding's
    line. A structured `proposed_edit` (a value-preserving footprint refit) drives a
    combined text-width + reposition; else a `proposed_offset` drives a verifier-gated
    `label_reposition` past the 0.10cm nudge cap; else fall back to the bounded nudge."""
    refit = _finding_refit(finding, line)
    if refit is not None:
        return refit
    proposed = finding.get("proposed_offset")
    if isinstance(proposed, dict):
        axis = proposed.get("axis")
        dx_cm = proposed.get("dx_cm")
        if axis in ("x", "y") and isinstance(dx_cm, (int, float)) and not isinstance(dx_cm, bool):
            replacement = bounded_coordinate_offset.reposition_coordinate(
                line, axis=axis, dx_cm=float(dx_cm)
            )
            if replacement is not None:
                return (
                    replacement,
                    "label_reposition",
                    f"reposition_{axis}{float(dx_cm):+.2f}cm",
                    float(dx_cm),
                )
    replacement = bounded_coordinate_offset.offset_first_coordinate(line)
    if replacement is None:
        return None
    return (replacement, "label_offset", VARIANT_ID, 0.1)


def _node_text_from_finding(finding: dict[str, Any], lines: list[str]) -> str | None:
    """The node's `{...}` content spanning the finding's tex_lines range."""
    tex_lines = finding.get("tex_lines")
    if not (isinstance(tex_lines, list) and tex_lines and isinstance(tex_lines[0], int)):
        return None
    start = tex_lines[0]
    end = tex_lines[-1] if isinstance(tex_lines[-1], int) else start
    node_tex = "\n".join(lines[start - 1 : end])
    match = re.search(r"\{(.+?)\}", node_tex, re.DOTALL)
    return match.group(1) if match else None


def _finding_with_derived_edit(
    finding: dict[str, Any], lines: list[str], words: list[dict[str, Any]]
) -> dict[str, Any]:
    """When a finding carries no eye-supplied proposed_edit, derive a value-preserving
    label_refit from the figure itself: the crossed reference line from the .tex
    draws + the wrap line-count from the rendered words. Returns the finding
    unchanged when an edit is already present or no refit can be derived (the
    derived edit still rides the existing fail-loud verifier)."""
    if isinstance(finding.get("proposed_edit"), dict) or isinstance(
        finding.get("proposed_offset"), dict
    ):
        return finding
    tex_lines = finding.get("tex_lines")
    if not (isinstance(tex_lines, list) and tex_lines and isinstance(tex_lines[0], int)):
        return finding
    if not 1 <= tex_lines[0] <= len(lines):
        return finding
    node_line = lines[tex_lines[0] - 1]
    node_text = _node_text_from_finding(finding, lines)
    if node_text is None:
        return finding
    lines_count = label_refit_derive.node_line_count(node_text, words)
    derived = label_refit_derive.derive_refit(node_line, lines, lines_count)
    if derived is None:
        return finding
    return {**finding, "proposed_edit": derived}


def _load_build_words(name: str, paths: runtime_paths.RuntimePaths) -> list[dict[str, Any]]:
    """Rendered pdftotext words for the figure's build PDF (best-effort, [] if absent)."""
    pdf_path = paths.examples_dir / name / "build" / f"{name}.pdf"
    if not pdf_path.is_file():
        return []
    try:
        words, _page = extract_pdf_words_and_page(pdf_path)
    except Exception:  # noqa: BLE001 - rendered words are best-effort
        return []
    return words


def _adjudicated_apply_candidates(
    name: str,
    paths: runtime_paths.RuntimePaths,
    lines: list[str],
    source_rel: Path,
    current_source_hash: str,
    apply_authority: str,
) -> list[dict[str, Any]]:
    """Emit a candidate anchored to each adjudicated `apply` finding's tex_lines.

    The ledger-driven path keys candidates off detector geometry; an `apply`
    finding carries the host-eye diagnosis (its own tex_lines) that the detector
    ledger does not. This wires that finding line into a bounded label offset so
    the candidate targets the diagnosed element instead of unrelated geometry.
    """
    example_dir = paths.examples_dir / name
    adjudication_path = example_dir / "critique_adjudication.yaml"
    critique_path = example_dir / "critique.md"
    if not adjudication_path.is_file() or not critique_path.is_file():
        return []
    try:
        adjudication = critique_adjudication.load_adjudication(adjudication_path)
        frontmatter = critique_contract.load_critique_frontmatter(critique_path)
    except (
        critique_adjudication.CritiqueAdjudicationError,
        critique_contract.CritiqueContractError,
    ):
        return []
    findings_by_id: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(critique_contract.critique_findings(frontmatter)):
        finding_id = finding.get("id")
        if isinstance(finding_id, str) and finding_id.strip():
            findings_by_id.setdefault(finding_id.strip(), finding)
    candidates: list[dict[str, Any]] = []
    words = _load_build_words(name, paths)
    for decision in adjudication.get("decisions", []):
        if not isinstance(decision, dict) or decision.get("decision") != "apply":
            continue
        finding = findings_by_id.get(str(decision.get("finding_id") or ""))
        if finding is None:
            continue
        tex_lines = finding.get("tex_lines")
        if not (isinstance(tex_lines, list) and tex_lines and isinstance(tex_lines[0], int)):
            continue
        line_number = tex_lines[0]
        if line_number < 1 or line_number > len(lines):
            continue
        line = lines[line_number - 1]
        # Approach 2: with no eye-supplied diagnosis, derive a label_refit from the
        # figure's own geometry (crossed line from .tex + wrap count from the render).
        finding = _finding_with_derived_edit(finding, lines, words)
        offset = _finding_offset(finding, line)
        if offset is None:
            continue
        replacement, edit_class, variant_id, variant_dx_cm = offset
        finding_id = str(finding.get("id"))
        candidates.append(
            _label_offset_candidate(
                name=name,
                candidate_id="",
                source_rel=source_rel,
                line_number=line_number,
                line=line,
                replacement=replacement,
                apply_authority=apply_authority,
                target={
                    "panel": str(finding.get("panel") or "unknown"),
                    "subregion": f"adjudicated:{finding_id}",
                },
                source_hash=current_source_hash,
                source_defect={
                    "id": finding_id,
                    "source": "adjudicated_finding",
                    "defect_class": str(finding.get("category") or "label_offset"),
                    "evidence": [],
                    "source_fingerprint": "",
                    "ledger_hash": "",
                    "target_texts": [
                        str(text)
                        for text in (finding.get("target_texts") or [])
                        if isinstance(text, str)
                    ],
                },
                edit_class=edit_class,
                variant_id=variant_id,
                variant_dx_cm=variant_dx_cm,
            )
        )
    return candidates


def build_candidate_set(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    output_path: Path | None = None,
    panel: str | None = None,
    family: str | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    _validate_output_path(paths=paths, name=name, output_path=output_path)
    if panel is not None or family is not None:
        return candidate_families.build_family_candidates(
            name,
            panel=panel,
            family=family,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
        )

    source_rel = Path("examples") / name / f"{name}.tex"
    source = _fixture_source_path(paths, name)
    apply_authority = _authority_floor(name, paths)
    base = {
        "tex_hash": _source_hash(source),
        "status_hash": ZERO_HASH,
        "intent_model_hash": ZERO_HASH,
    }
    if not source.is_file():
        return {
            "schema": SCHEMA,
            "fixture": name,
            "base": base,
            "candidates": [],
            "refusals": [{"code": "source_missing"}],
            "metrics": _candidate_metrics(
                [],
                [{"code": "source_missing"}],
                {
                    "safe_candidate_defect_count": 0,
                    "candidate_supported_defect_count": 0,
                    "unsupported_safe_defect_count": 0,
                },
            ),
        }

    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    candidates, refusals, defect_counts = _defect_candidates(
        name,
        paths,
        lines,
        source_rel,
        base["tex_hash"],
        apply_authority,
    )
    covered_lines = {
        candidate["selector"]["start_line"]
        for candidate in candidates
        if isinstance(candidate.get("selector"), dict)
    }
    for adjudicated in _adjudicated_apply_candidates(
        name,
        paths,
        lines,
        source_rel,
        base["tex_hash"],
        apply_authority,
    ):
        start_line = adjudicated["selector"]["start_line"]
        if start_line in covered_lines:
            continue
        covered_lines.add(start_line)
        candidates.append(adjudicated)
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"CAND{index:03d}"
    if not candidates and not refusals:
        refusals = [{"code": "no_supported_candidate"}]

    return {
        "schema": SCHEMA,
        "fixture": name,
        "base": base,
        "candidates": candidates,
        "refusals": refusals,
        "metrics": _candidate_metrics(candidates, refusals, defect_counts),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--panel")
    parser.add_argument("--family")
    args = parser.parse_args(argv)
    try:
        payload = build_candidate_set(args.name, panel=args.panel, family=args.family)
    except (CandidateGeneratorError, ValueError) as exc:
        print(f"candidate_generator: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
