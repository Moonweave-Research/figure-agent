"""Aggregate quality memory events into conservative ranking priors."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

import experience_log
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.quality-memory-index.v1"
ELIGIBLE_OUTCOMES = {"improved", "neutral", "regressed"}
ATTEMPT_EVENT_TYPES = {
    "candidate_rendered",
    "candidate_ranked",
    "candidate_recommended",
    "candidate_accepted",
    "candidate_applied",
    "candidate_rejected",
    "candidate_rolled_back",
}


class QualityMemoryIndexError(ValueError):
    """Raised when memory index writes would leave fixture boundaries."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _safe_count_bucket() -> dict[str, Any]:
    return {
        "event_count": 0,
        "attempts": 0,
        "improved": 0,
        "neutral": 0,
        "regressed": 0,
        "blocked": 0,
        "unknown": 0,
        "median_rank_delta": 0.0,
        "recommended_prior": 0.0,
    }


def _outcome_state(event: dict[str, Any]) -> str:
    outcome = event.get("outcome")
    if isinstance(outcome, dict):
        return str(outcome.get("state") or "unknown")
    return "unknown"


def _reward_state(event: dict[str, Any]) -> str:
    outcome = event.get("outcome")
    if not isinstance(outcome, dict):
        return "unknown"
    quality_movement = outcome.get("quality_movement")
    if quality_movement in ELIGIBLE_OUTCOMES:
        return str(quality_movement)
    return "unknown"


def _rank_score(event: dict[str, Any]) -> float | None:
    metrics = event.get("metrics")
    if not isinstance(metrics, dict):
        return None
    value = metrics.get("candidate_rank_score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_experience_records(plugin_root: Path, name: str) -> list[dict[str, Any]]:
    override = os.environ.get("FIG_AGENT_EXPERIENCE_LOG_DIR")
    log_dir = experience_log.experience_log_dir(plugin_root)
    path = log_dir / f"{name}.jsonl"
    checks = (("experience_log", log_dir), ("experience_log", path))
    if not override:
        checks = (("docs", plugin_root / "docs"), *checks)
    for label, item in checks:
        if item.is_symlink():
            raise QualityMemoryIndexError(f"{label}_symlink")
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise QualityMemoryIndexError(f"experience_record_invalid:{line_number}") from exc
        if not isinstance(payload, dict):
            raise QualityMemoryIndexError(f"experience_record_invalid:{line_number}")
        records.append(payload)
    return records


def _experience_log_fixture_names(plugin_root: Path) -> list[str]:
    log_dir = experience_log.experience_log_dir(plugin_root)
    if log_dir.is_symlink():
        raise QualityMemoryIndexError("experience_log_symlink")
    if not log_dir.is_dir():
        return []
    fixtures: list[str] = []
    for path in sorted(log_dir.glob("*.jsonl")):
        if path.is_symlink():
            raise QualityMemoryIndexError("experience_log_symlink")
        fixture = path.stem
        fixture_identity.validate_fixture_name(fixture)
        fixtures.append(fixture)
    return fixtures


def _event_from_experience_record(record: dict[str, Any]) -> dict[str, Any]:
    state = record.get("state") if isinstance(record.get("state"), dict) else {}
    action = record.get("action") if isinstance(record.get("action"), dict) else {}
    outcome = record.get("outcome") if isinstance(record.get("outcome"), dict) else {}
    target = state.get("target") if isinstance(state.get("target"), dict) else {}
    params = action.get("params") if isinstance(action.get("params"), dict) else {}
    operations = params.get("operations") if isinstance(params.get("operations"), list) else []
    first_operation = operations[0] if operations and isinstance(operations[0], dict) else {}
    template_id = action.get("template_id") or first_operation.get("template_id")
    apply_status = str(outcome.get("apply_status") or "unknown")
    human_decision_kind = outcome.get("human_decision_kind")
    quality_movement = outcome.get("quality_movement")
    outcome_state = str(quality_movement) if quality_movement in ELIGIBLE_OUTCOMES else apply_status
    rank_score = action.get("rank_score")
    event_type = "candidate_applied"
    if apply_status == "unchosen":
        event_type = "candidate_unchosen"
    elif human_decision_kind in {"auto_accept_recommended", "convergence_deferred"}:
        event_type = "candidate_recommended"
    return {
        "schema": "figure-agent.quality-memory-event.v1",
        "fixture": record.get("fixture"),
        "event_id": record.get("record_id"),
        "event_type": event_type,
        "created_at": record.get("created_at"),
        "source_artifact": f"docs/experience-log/{record.get('fixture')}.jsonl",
        "candidate_id": action.get("candidate_id"),
        "edit_family": action.get("edit_family"),
        "target": {
            "panel": target.get("panel"),
            "subregion": target.get("subregion_key"),
        },
        "pre_state": state,
        "post_state": {
            "candidate_hash": action.get("candidate_hash"),
            "template_id": template_id,
            "human_decision_kind": human_decision_kind,
        },
        "outcome": {
            "state": outcome_state,
            "pipeline_ok": outcome.get("pipeline_ok"),
            "quality_movement": quality_movement,
            "reason": apply_status,
            "evidence_paths": [f"docs/experience-log/{record.get('fixture')}.jsonl"],
        },
        "metrics": {"candidate_rank_score": rank_score} if rank_score is not None else {},
    }


def _is_unknown(value: str) -> bool:
    return value.strip() == "" or value == "unknown"


def _recommended_prior(bucket: dict[str, Any]) -> float:
    attempts = int(bucket["improved"]) + int(bucket["neutral"]) + int(bucket["regressed"])
    if attempts < 3:
        return 0.0
    raw = (
        int(bucket["improved"]) + 0.5 * int(bucket["neutral"]) - int(bucket["regressed"])
    ) / attempts
    return round(_clamp(raw * 0.25, -0.25, 0.25), 4)


def _reward_sparsity(
    *,
    eligible_attempt_count: int,
    counterfactual_count: int,
    prior_floor: int = 3,
) -> dict[str, Any]:
    state = "sparse" if 0 < eligible_attempt_count < prior_floor else "sufficient"
    if eligible_attempt_count == 0:
        state = "empty"
    return {
        "state": state,
        "eligible_attempt_count": eligible_attempt_count,
        "prior_floor": prior_floor,
        "counterfactual_unchosen_count": counterfactual_count,
        "mitigations": [
            "counterfactual_unchosen_rows",
            "cross_fixture_transfer",
        ]
        if state == "sparse"
        else [],
    }


def build_memory_index(
    events: list[dict[str, Any]],
    *,
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    families: dict[str, dict[str, Any]] = defaultdict(_safe_count_bucket)
    family_templates: dict[str, dict[str, Any]] = defaultdict(_safe_count_bucket)
    panel_patterns: dict[str, dict[str, Any]] = defaultdict(_safe_count_bucket)
    family_source_fixtures: dict[str, set[str]] = defaultdict(set)
    rank_scores: dict[str, list[float]] = defaultdict(list)
    template_rank_scores: dict[str, list[float]] = defaultdict(list)
    eligible_prior_count = 0
    candidate_event_count = 0
    unknown_event_count = 0
    counterfactual_unchosen_count = 0
    duplicate_experience_attempt_count = 0
    seen_experience_attempt_keys: set[tuple[str, str, str, str, str, str, str]] = set()

    for event in events:
        if not event.get("candidate_id"):
            continue
        candidate_event_count += 1
        family = str(event.get("edit_family") or "unknown")
        target = event.get("target") if isinstance(event.get("target"), dict) else {}
        panel = str(target.get("panel") or "unknown")
        subregion = str(target.get("subregion") or "unknown")
        pattern_key = f"{panel}:{subregion}:{family}"
        state = _outcome_state(event)
        reward_state = _reward_state(event)
        event_type = str(event.get("event_type") or "")
        pre_state = event.get("pre_state") if isinstance(event.get("pre_state"), dict) else {}
        post_state = event.get("post_state") if isinstance(event.get("post_state"), dict) else {}
        template_id = str(post_state.get("template_id") or "unknown")
        template_known = not _is_unknown(template_id)
        family_template_key = f"{family}::{template_id}"
        fixture = str(event.get("fixture") or "")
        stable_experience_key = (
            fixture,
            event_type,
            family,
            panel,
            subregion,
            str(pre_state.get("base_tex_hash") or ""),
            str(post_state.get("candidate_hash") or event.get("candidate_id") or ""),
        )
        duplicate_experience_attempt = (
            event_type in {"candidate_recommended", "candidate_unchosen"}
            and stable_experience_key in seen_experience_attempt_keys
        )
        if event_type in {"candidate_recommended", "candidate_unchosen"}:
            seen_experience_attempt_keys.add(stable_experience_key)
        if duplicate_experience_attempt:
            duplicate_experience_attempt_count += 1
        if event_type == "candidate_unchosen" and not duplicate_experience_attempt:
            counterfactual_unchosen_count += 1
        is_attempt = event_type in ATTEMPT_EVENT_TYPES
        family_known = not _is_unknown(family)
        target_known = not _is_unknown(panel) and not _is_unknown(subregion)
        unknown_outcome = (
            is_attempt
            and reward_state == "unknown"
            and (state in ELIGIBLE_OUTCOMES or state == "unknown")
        )
        if not family_known or not target_known or unknown_outcome:
            unknown_event_count += 1
        buckets = []
        if family_known:
            buckets.append(families[family])
            fixture = event.get("fixture")
            if isinstance(fixture, str) and fixture:
                family_source_fixtures[family].add(fixture)
        if family_known and template_known:
            buckets.append(family_templates[family_template_key])
        if family_known and target_known:
            buckets.append(panel_patterns[pattern_key])
        eligible_attempt = (
            is_attempt
            and family_known
            and target_known
            and reward_state in ELIGIBLE_OUTCOMES
            and not duplicate_experience_attempt
        )
        for bucket in buckets:
            bucket["event_count"] += 1
            if eligible_attempt:
                bucket["attempts"] += 1
            if eligible_attempt and reward_state == "improved":
                bucket["improved"] += 1
            elif eligible_attempt and reward_state == "neutral":
                bucket["neutral"] += 1
            elif eligible_attempt and reward_state == "regressed":
                bucket["regressed"] += 1
            elif state.startswith("blocked") and not duplicate_experience_attempt:
                bucket["blocked"] += 1
            elif not duplicate_experience_attempt:
                bucket["unknown"] += 1
        if eligible_attempt:
            eligible_prior_count += 1
        rank_score = _rank_score(event)
        if rank_score is not None and family_known and not duplicate_experience_attempt:
            rank_scores[family].append(rank_score)
        if (
            rank_score is not None
            and family_known
            and template_known
            and not duplicate_experience_attempt
        ):
            template_rank_scores[family_template_key].append(rank_score)

    for family, bucket in families.items():
        bucket["recommended_prior"] = _recommended_prior(bucket)
        bucket["prior_provenance"] = _prior_provenance(
            scope or {"kind": "events"},
            family_source_fixtures[family],
        )
        if rank_scores[family]:
            bucket["median_rank_delta"] = round(median(rank_scores[family]), 4)
    for bucket in panel_patterns.values():
        bucket["recommended_prior"] = _recommended_prior(bucket)
    for key, bucket in family_templates.items():
        bucket["recommended_prior"] = _recommended_prior(bucket)
        if template_rank_scores[key]:
            bucket["median_rank_delta"] = round(median(template_rank_scores[key]), 4)

    return {
        "schema": SCHEMA,
        "generated_at": _utc_now(),
        "scope": scope or {"kind": "events"},
        "event_count": len(events),
        "candidate_event_count": candidate_event_count,
        "unknown_event_count": unknown_event_count,
        "unknown_event_rate": round(unknown_event_count / candidate_event_count, 4)
        if candidate_event_count
        else 0.0,
        "duplicate_experience_attempt_count": duplicate_experience_attempt_count,
        "duplicate_experience_attempt_rate": round(
            duplicate_experience_attempt_count / candidate_event_count,
            4,
        )
        if candidate_event_count
        else 0.0,
        "eligible_prior_count": eligible_prior_count if eligible_prior_count >= 3 else 0,
        "reward_sparsity": _reward_sparsity(
            eligible_attempt_count=eligible_prior_count,
            counterfactual_count=counterfactual_unchosen_count,
        ),
        "families": dict(sorted(families.items())),
        "family_templates": dict(sorted(family_templates.items())),
        "panel_patterns": dict(sorted(panel_patterns.items())),
        "disallowed_priors": [
            {
                "key": "semantic_rewrite",
                "reason": "semantic edit families cannot receive apply priors",
            }
        ],
    }


def _prior_provenance(scope: dict[str, Any], source_fixtures: set[str]) -> dict[str, Any]:
    kind = scope.get("kind") if isinstance(scope, dict) else None
    locality = "event_scope"
    if kind == "fixture":
        locality = "fixture_local"
    elif kind == "suite":
        locality = "cross_fixture_transfer"
    return {
        "locality": locality,
        "scope": scope,
        "source_fixtures": sorted(source_fixtures),
    }


def _ensure_fixture_memory_output(example_dir: Path) -> Path:
    build_dir = example_dir / "build"
    memory_dir = build_dir / "memory"
    output = memory_dir / "quality_memory_index.json"
    for label, path in (("build", build_dir), ("memory", memory_dir), ("output", output)):
        if path.is_symlink():
            raise QualityMemoryIndexError(f"sandbox_symlink_forbidden: {label}")
    if build_dir.exists() and not build_dir.is_dir():
        raise QualityMemoryIndexError("build_not_directory")
    if memory_dir.exists() and not memory_dir.is_dir():
        raise QualityMemoryIndexError("memory_not_directory")
    memory_dir.mkdir(parents=True, exist_ok=True)
    for label, path in (("build", build_dir), ("memory", memory_dir)):
        if path.is_symlink():
            raise QualityMemoryIndexError(f"sandbox_symlink_forbidden: {label}")
    return output


def _forbidden_write_reason(path: Path) -> str | None:
    resolved = path.expanduser().resolve()
    parts = set(resolved.parts)
    if "CloudStorage" in parts or "Google Drive" in parts:
        return "cloud_storage_write_forbidden"
    if any(part.startswith("GoogleDrive") for part in resolved.parts):
        return "cloud_storage_write_forbidden"
    home = Path.home().resolve()
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return None
    if len(relative.parts) >= 2 and relative.parts[:2] == ("Library", "Caches"):
        return "home_cache_write_forbidden"
    if relative.parts and relative.parts[0] == ".cache":
        return "home_cache_write_forbidden"
    return None


def _reject_forbidden_write_path(path: Path) -> None:
    reason = _forbidden_write_reason(path)
    if reason is not None:
        raise QualityMemoryIndexError(reason)


def _load_quality_suites(plugin_root: Path) -> dict[str, list[str]]:
    suites_path = plugin_root / "benchmarks" / "quality_suites.yaml"
    if suites_path.is_symlink():
        raise QualityMemoryIndexError("suite_manifest_symlink")
    try:
        lines = suites_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise QualityMemoryIndexError("suite_manifest_missing") from exc
    suites: dict[str, list[str]] = {}
    current_suite: str | None = None
    in_fixtures = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line.startswith("  ") and not raw_line.startswith("    ") and stripped.endswith(":"):
            current_suite = stripped[:-1]
            fixture_identity.validate_fixture_name(current_suite)
            suites[current_suite] = []
            in_fixtures = False
            continue
        if current_suite and stripped == "fixtures:":
            in_fixtures = True
            continue
        if current_suite and in_fixtures and stripped.startswith("- "):
            fixture = stripped[2:].strip()
            fixture_identity.validate_fixture_name(fixture)
            suites[current_suite].append(fixture)
    return suites


def _ensure_suite_memory_output(workspace_root: Path, suite: str) -> Path:
    scratch_root = workspace_root / ".scratch"
    memory_root = scratch_root / "figure-agent-memory"
    suite_dir = memory_root / suite
    output = suite_dir / "quality_memory_index.json"
    for label, path in (
        ("scratch", scratch_root),
        ("memory", memory_root),
        ("suite", suite_dir),
        ("output", output),
    ):
        if path.is_symlink():
            raise QualityMemoryIndexError(f"sandbox_symlink_forbidden: {label}")
    suite_dir.mkdir(parents=True, exist_ok=True)
    for label, path in (("scratch", scratch_root), ("memory", memory_root), ("suite", suite_dir)):
        if path.is_symlink():
            raise QualityMemoryIndexError(f"sandbox_symlink_forbidden: {label}")
    _reject_forbidden_write_path(output)
    return output


def write_fixture_index(
    name: str,
    events: list[dict[str, Any]],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        raise QualityMemoryIndexError(f"examples/{name}/ not found")
    index = build_memory_index(events, scope={"kind": "fixture", "fixture": name})
    output = _ensure_fixture_memory_output(example_dir)
    _reject_forbidden_write_path(output)
    text = json.dumps(index, indent=2, sort_keys=True) + "\n"
    output.write_text(text, encoding="utf-8")
    index["writes"] = ["build/memory/quality_memory_index.json"]
    return index


def build_fixture_index(
    name: str,
    *,
    write: bool = False,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    records = _load_experience_records(paths.plugin_root, name)
    events = [_event_from_experience_record(record) for record in records]
    if write:
        return write_fixture_index(
            name,
            events,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
        )
    index = build_memory_index(events, scope={"kind": "fixture", "fixture": name})
    index["writes"] = []
    return index


def build_suite_index(
    suite: str,
    *,
    write: bool = False,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(suite)
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    suites = _load_quality_suites(paths.plugin_root)
    if suite not in suites:
        raise QualityMemoryIndexError(f"unknown_suite: {suite}")
    events: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    suite_fixtures = list(suites[suite])
    log_fixtures = _experience_log_fixture_names(paths.plugin_root)
    for fixture in sorted(dict.fromkeys([*suite_fixtures, *log_fixtures])):
        example_dir = paths.examples_dir / fixture
        records = _load_experience_records(paths.plugin_root, fixture)
        if not example_dir.is_dir() and not records:
            diagnostics.append(
                {"fixture": fixture, "status": "skipped", "reason": "missing_fixture"}
            )
            continue
        events.extend(_event_from_experience_record(record) for record in records)
        reason = ""
        if fixture not in suite_fixtures:
            reason = "out_of_suite_experience_log"
        elif not example_dir.is_dir():
            reason = "missing_fixture_with_experience_log"
        diagnostics.append({"fixture": fixture, "status": "included", "reason": reason})
    index = build_memory_index(events, scope={"kind": "suite", "suite": suite})
    index["suite_diagnostics"] = diagnostics
    if write:
        output = _ensure_suite_memory_output(paths.workspace_root, suite)
        output.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        index["writes"] = [f".scratch/figure-agent-memory/{suite}/quality_memory_index.json"]
    else:
        index["writes"] = []
    return index


def main(
    argv: list[str] | None = None,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="quality_memory_index.py")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--fixture")
    scope.add_argument("--suite")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.fixture:
        payload = build_fixture_index(
            args.fixture,
            write=args.write,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
        )
    else:
        payload = build_suite_index(
            args.suite,
            write=args.write,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
