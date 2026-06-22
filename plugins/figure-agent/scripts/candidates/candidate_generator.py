"""Generate deterministic candidate improvement sets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import bounded_coordinate_offset
import candidate_contracts
import candidate_families
import figure_intent_model
import fixture_identity
import quality_defect_ledger
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"
ZERO_HASH = "sha256:" + "0" * 64
COORDINATE_OFFSET_DEFECT_CLASSES = frozenset(
    {"label_offset", "text_overlap", "whitespace_balance"}
)
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
) -> dict[str, Any]:
    candidate = {
        "id": candidate_id,
        "target": target,
        "edit_class": "label_offset",
        "edit_family": EDIT_FAMILY,
        "family": FAMILY,
        "variant_id": VARIANT_ID,
        "variant": {"id": VARIANT_ID, "dx_cm": 0.1},
        "source_hash": source_hash,
        "affected_files": [source_rel.as_posix()],
        "selector": {
            "kind": "line_range_with_hash",
            "path": source_rel.as_posix(),
            "start_line": line_number,
            "end_line": line_number,
            "original_hash": candidate_contracts.canonical_hash(line),
            "source_hash": source_hash,
        },
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
            "variant_id": VARIANT_ID,
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
        {"code": gap, "defect_id": defect_id}
        for gap in gaps
        if gap in ACTIONABILITY_REFUSAL_CODES
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
        return [], [], {
            "safe_candidate_defect_count": 0,
            "candidate_supported_defect_count": 0,
            "unsupported_safe_defect_count": 0,
        }
    refusals: list[dict[str, str]] = []
    sortable_candidates: list[tuple[tuple[int, str, str, int, str, str, str], dict[str, Any]]] = []
    safe_count = 0
    supported_count = 0
    unsupported_count = 0
    ledger_hash = str(ledger.get("ledger_hash") or "")
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
        line_number = _selector_start_line(defect, len(lines))
        if line_number is None:
            continue
        supported_count += 1
        line = lines[line_number - 1]
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
        )
        sortable_candidates.append((_defect_sort_key(defect, source_rel, line_number), candidate))
    candidates: list[dict[str, Any]] = []
    for index, (_sort_key, candidate) in enumerate(sorted(sortable_candidates), start=1):
        candidate["id"] = f"CAND{index:03d}"
        candidates.append(candidate)
    return candidates, refusals, {
        "safe_candidate_defect_count": safe_count,
        "candidate_supported_defect_count": supported_count,
        "unsupported_safe_defect_count": unsupported_count,
    }


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
