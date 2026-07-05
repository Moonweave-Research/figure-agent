"""Recommend the next read-only quality experiment."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

import quality_benchmark
import quality_memory_index
import runtime_paths

SCHEMA = "figure-agent.quality-next-experiment.v1"
FORBIDDEN_TOKENS = ("--write", "--apply", "--accept", "--overwrite", "--force")
DEFAULT_FAMILIES = (
    "hierarchy_rebalance",
    "panel_c_hero_finish",
    "apparatus_strengthen",
    "panel_f_final_finish",
    "panel_f_label_route_finish",
    "panel_f_boundary_polish",
    "density_reduce",
)


def _safe_command(command: str) -> bool:
    if any(token in command for token in FORBIDDEN_TOKENS):
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if parts == ["fig-agent", "benchmark-run", "--suite", "smoke", "--json"]:
        return True
    if len(parts) < 8 or parts[:2] != ["fig-agent", "quality-search"]:
        return False
    if "--json" not in parts or "--execute" not in parts:
        return False
    if "--max-iterations" not in parts:
        return False
    max_index = parts.index("--max-iterations")
    return max_index + 1 < len(parts) and parts[max_index + 1] == "1"


def _bounded_int(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


def _family_stats(memory: dict[str, Any], family: str) -> dict[str, Any]:
    families = memory.get("families")
    bucket = families.get(family) if isinstance(families, dict) else None
    if not isinstance(bucket, dict):
        bucket = {}
    attempts = _bounded_int(bucket.get("attempts"))
    improved = _bounded_int(bucket.get("improved"))
    neutral = _bounded_int(bucket.get("neutral"))
    regressed = _bounded_int(bucket.get("regressed"))
    empirical_reward = (improved + 0.5 * neutral) / attempts if attempts else 0.5
    arm_uncertainty = 1.0 if attempts == 0 else 1.0 / (attempts + 1)
    return {
        "attempts": attempts,
        "improved": improved,
        "neutral": neutral,
        "regressed": regressed,
        "empirical_reward": round(empirical_reward, 4),
        "arm_uncertainty": round(arm_uncertainty, 4),
    }


def _fixture_uncertainty(memory: dict[str, Any]) -> float:
    candidate_event_count = _bounded_int(memory.get("candidate_event_count"))
    return 1.0 if candidate_event_count == 0 else round(1.0 / (candidate_event_count + 1), 4)


def _families_for_fixture(memory: dict[str, Any]) -> list[str]:
    families = list(DEFAULT_FAMILIES)
    memory_families = memory.get("families")
    if isinstance(memory_families, dict):
        for family in sorted(memory_families):
            if family not in families:
                families.append(family)
    return families


def _experiment_candidates(
    fixtures: list[str],
    *,
    paths: runtime_paths.RuntimePaths,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for fixture in fixtures:
        memory = quality_memory_index.build_fixture_index(
            fixture,
            write=False,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        )
        fixture_uncertainty = _fixture_uncertainty(memory)
        for family in _families_for_fixture(memory):
            stats = _family_stats(memory, family)
            information_score = round(stats["arm_uncertainty"] + fixture_uncertainty, 4)
            candidates.append(
                {
                    "fixture": fixture,
                    "family": family,
                    "information_score": information_score,
                    "fixture_uncertainty": fixture_uncertainty,
                    **stats,
                    "source": "experience_log_via_quality_memory_index",
                }
            )
    return sorted(
        candidates,
        key=lambda item: (
            -float(item["information_score"]),
            str(item["fixture"]),
            DEFAULT_FAMILIES.index(item["family"])
            if item["family"] in DEFAULT_FAMILIES
            else len(DEFAULT_FAMILIES),
            str(item["family"]),
        ),
    )


def _quality_search_command(fixture: str, family: str) -> str:
    goal = f"probe {family} arm uncertainty"
    return " ".join(
        [
            "fig-agent",
            "quality-search",
            fixture,
            "--goal",
            shlex.quote(goal),
            "--execute",
            "--max-iterations",
            "1",
            "--json",
        ]
    )


def build_next_experiment(
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    benchmark_list = quality_benchmark.build_benchmark_list(plugin_root=paths.plugin_root)
    smoke = benchmark_list.get("suites", {}).get("smoke", {})
    smoke_fixtures = smoke.get("fixtures") if isinstance(smoke, dict) else []
    fixtures = (
        [str(fixture) for fixture in smoke_fixtures]
        if isinstance(smoke_fixtures, list)
        else []
    )
    candidates = _experiment_candidates(fixtures, paths=paths)
    selected = candidates[0] if candidates else None
    command = (
        _quality_search_command(str(selected["fixture"]), str(selected["family"]))
        if isinstance(selected, dict)
        else "fig-agent benchmark-run --suite smoke --json"
    )
    return {
        "schema": SCHEMA,
        "suite": "smoke",
        "fixture_count": len(fixtures),
        "recommendation": {
            "kind": "fixture_family_uncertainty_probe"
            if isinstance(selected, dict)
            else "benchmark_preview",
            "command": command,
            "allowed": _safe_command(command),
            "fixture": selected.get("fixture") if isinstance(selected, dict) else None,
            "family": selected.get("family") if isinstance(selected, dict) else None,
            "information_score": selected.get("information_score")
            if isinstance(selected, dict)
            else None,
            "arm_uncertainty": selected.get("arm_uncertainty")
            if isinstance(selected, dict)
            else None,
            "fixture_uncertainty": selected.get("fixture_uncertainty")
            if isinstance(selected, dict)
            else None,
            "arm_statistics": selected if isinstance(selected, dict) else None,
            "reason_codes": [
                "highest_fixture_family_arm_uncertainty",
                "read_only_quality_search_preview",
            ],
        },
        "candidate_count": len(candidates),
        "top_candidates": candidates[:10],
    }


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    del args
    payload = build_next_experiment(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
