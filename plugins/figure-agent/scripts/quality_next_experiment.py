"""Recommend the next read-only quality experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import quality_benchmark
import runtime_paths

SCHEMA = "figure-agent.quality-next-experiment.v1"
ALLOWED_COMMANDS = {
    "fig-agent benchmark-run --suite smoke --json",
}
FORBIDDEN_TOKENS = ("--write", "--apply", "--accept", "--overwrite", "--force")


def _safe_command(command: str) -> bool:
    if command not in ALLOWED_COMMANDS:
        return False
    return not any(token in command for token in FORBIDDEN_TOKENS)


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
    command = "fig-agent benchmark-run --suite smoke --json"
    return {
        "schema": SCHEMA,
        "suite": "smoke",
        "fixture_count": len(smoke_fixtures) if isinstance(smoke_fixtures, list) else 0,
        "recommendation": {
            "kind": "benchmark_preview",
            "command": command,
            "allowed": _safe_command(command),
            "reason_codes": [
                "smoke_suite_is_release_blocking",
                "preview_command_has_no_write_flags",
            ],
        },
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
