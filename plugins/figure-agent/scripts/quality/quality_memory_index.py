"""Aggregate quality memory events into conservative ranking priors."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

import fixture_identity
import quality_memory_events
import runtime_paths

SCHEMA = "figure-agent.quality-memory-index.v1"
ELIGIBLE_OUTCOMES = {"improved", "neutral", "regressed"}
ATTEMPT_EVENT_TYPES = {
    "candidate_rendered",
    "candidate_ranked",
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


def _rank_score(event: dict[str, Any]) -> float | None:
    metrics = event.get("metrics")
    if not isinstance(metrics, dict):
        return None
    value = metrics.get("candidate_rank_score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_unknown(value: str) -> bool:
    return value.strip() == "" or value == "unknown"


def _recommended_prior(bucket: dict[str, Any]) -> float:
    attempts = int(bucket["improved"]) + int(bucket["neutral"]) + int(bucket["regressed"])
    if attempts < 3:
        return 0.0
    raw = (
        int(bucket["improved"])
        + 0.5 * int(bucket["neutral"])
        - int(bucket["regressed"])
    ) / attempts
    return round(_clamp(raw * 0.25, -0.25, 0.25), 4)


def build_memory_index(
    events: list[dict[str, Any]],
    *,
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    families: dict[str, dict[str, Any]] = defaultdict(_safe_count_bucket)
    panel_patterns: dict[str, dict[str, Any]] = defaultdict(_safe_count_bucket)
    rank_scores: dict[str, list[float]] = defaultdict(list)
    eligible_prior_count = 0
    candidate_event_count = 0
    unknown_event_count = 0

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
        event_type = str(event.get("event_type") or "")
        is_attempt = event_type in ATTEMPT_EVENT_TYPES
        family_known = not _is_unknown(family)
        target_known = not _is_unknown(panel) and not _is_unknown(subregion)
        unknown_outcome = is_attempt and state == "unknown"
        if not family_known or not target_known or unknown_outcome:
            unknown_event_count += 1
        buckets = []
        if family_known:
            buckets.append(families[family])
        if family_known and target_known:
            buckets.append(panel_patterns[pattern_key])
        eligible_attempt = (
            is_attempt and family_known and target_known and state in ELIGIBLE_OUTCOMES
        )
        for bucket in buckets:
            bucket["event_count"] += 1
            if eligible_attempt:
                bucket["attempts"] += 1
            if eligible_attempt and state == "improved":
                bucket["improved"] += 1
            elif eligible_attempt and state == "neutral":
                bucket["neutral"] += 1
            elif eligible_attempt and state == "regressed":
                bucket["regressed"] += 1
            elif state.startswith("blocked"):
                bucket["blocked"] += 1
            else:
                bucket["unknown"] += 1
        if eligible_attempt:
            eligible_prior_count += 1
        rank_score = _rank_score(event)
        if rank_score is not None and family_known:
            rank_scores[family].append(rank_score)

    for family, bucket in families.items():
        bucket["recommended_prior"] = _recommended_prior(bucket)
        if rank_scores[family]:
            bucket["median_rank_delta"] = round(median(rank_scores[family]), 4)
    for bucket in panel_patterns.values():
        bucket["recommended_prior"] = _recommended_prior(bucket)

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
        "eligible_prior_count": eligible_prior_count if eligible_prior_count >= 3 else 0,
        "families": dict(sorted(families.items())),
        "panel_patterns": dict(sorted(panel_patterns.items())),
        "disallowed_priors": [
            {
                "key": "semantic_rewrite",
                "reason": "semantic edit families cannot receive apply priors",
            }
        ],
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
    log = quality_memory_events.build_memory_log(
        name,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    events = [event for event in log.get("events", []) if isinstance(event, dict)]
    if write:
        return write_fixture_index(
            name,
            events,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
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
    for fixture in suites[suite]:
        example_dir = paths.examples_dir / fixture
        if not example_dir.is_dir():
            diagnostics.append(
                {"fixture": fixture, "status": "skipped", "reason": "missing_fixture"}
            )
            continue
        log = quality_memory_events.build_memory_log(
            fixture,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
        )
        events.extend(event for event in log.get("events", []) if isinstance(event, dict))
        diagnostics.append({"fixture": fixture, "status": "included", "reason": ""})
    index = build_memory_index(events, scope={"kind": "suite", "suite": suite})
    index["suite_diagnostics"] = diagnostics
    if write:
        output = _ensure_suite_memory_output(paths.workspace_root, suite)
        output.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        index["writes"] = [
            f".scratch/figure-agent-memory/{suite}/quality_memory_index.json"
        ]
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
