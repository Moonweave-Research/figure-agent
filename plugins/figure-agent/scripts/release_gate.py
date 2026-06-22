"""Run deterministic figure-agent Cowork release checks."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml

SCRIPT_ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_ROOT.parent

for script_dir in reversed(
    (
        SCRIPT_ROOT,
        SCRIPT_ROOT / "checks",
        SCRIPT_ROOT / "candidates",
        SCRIPT_ROOT / "quality",
        SCRIPT_ROOT / "loop",
        SCRIPT_ROOT / "driver",
        SCRIPT_ROOT / "svg_polish",
    )
):
    sys.path.insert(0, str(script_dir))

import benchmark_contracts  # noqa: E402
import benchmark_detector_reports  # noqa: E402
import package_cowork_plugin  # noqa: E402
import quality_benchmark  # noqa: E402

SCHEMA = "figure-agent.release-gate.v1"

TARGETED_TESTS = [
    "tests/test_figure_intent_model.py",
    "tests/test_candidate_contracts.py",
    "tests/test_candidate_generator.py",
    "tests/test_candidate_render.py",
    "tests/test_candidate_rank.py",
    "tests/test_candidate_review_packet.py",
    "tests/test_candidate_apply.py",
    "tests/test_evidence_index.py",
    "tests/test_evidence_sync.py",
    "tests/test_closeout_readiness.py",
    "tests/test_golden_acceptance.py",
    "tests/test_candidate_cli_contract.py",
    "tests/test_benchmark_contracts.py",
    "tests/test_benchmark_detector_reports.py",
    "tests/test_quality_benchmark.py",
    "tests/test_quality_benchmark_compare.py",
    "tests/test_quality_next_experiment.py",
    "tests/test_quality_defect_ledger.py",
    "tests/test_quality_patch_policy.py",
    "tests/test_quality_patch_plan.py",
    "tests/test_quality_patch_apply.py",
    "tests/test_quality_cli_contract.py",
    "tests/test_agent_next.py",
    "tests/test_mcp_facade.py",
    "tests/test_package_cowork_plugin.py",
    "tests/test_command_contract_docs.py",
    "tests/test_release_contract.py",
]

REQUIRED_PACKAGE_PATHS = {
    ".claude-plugin/plugin.json",
    ".mcp.json",
    "benchmarks/quality_suites.yaml",
    "mcp/figure_agent_server.py",
    "bin/fig-agent",
    "scripts",
    "styles",
    "commands",
    "skills",
}


def _step(
    name: str,
    state: str,
    *,
    command: list[str] | None = None,
    stdout: str = "",
    stderr: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, "state": state}
    if command is not None:
        payload["command"] = command
    if stdout:
        payload["stdout"] = _bounded(stdout)
    if stderr:
        payload["stderr"] = _bounded(stderr)
    if details:
        payload["details"] = details
    return payload


def _bounded(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _run_command(name: str, command: list[str], *, cwd: Path = PLUGIN_ROOT) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    return _step(
        name,
        "passed" if result.returncode == 0 else "failed",
        command=command,
        stdout=result.stdout,
        stderr=result.stderr,
        details={"returncode": result.returncode},
    )


def _zip_names(zip_path: Path) -> set[str]:
    with zipfile.ZipFile(zip_path) as archive:
        return set(archive.namelist())


def _verify_required_paths(names: set[str]) -> dict[str, Any]:
    missing = []
    for required in sorted(REQUIRED_PACKAGE_PATHS):
        if required.endswith("/"):
            prefix = required
        else:
            prefix = required + "/"
        if required not in names and not any(name.startswith(prefix) for name in names):
            missing.append(required)
    return _step(
        "package_required_paths",
        "passed" if not missing else "failed",
        details={"missing": missing},
    )


def _verify_excluded_paths(names: set[str]) -> dict[str, Any]:
    bad = sorted(
        name
        for name in names
        if "/build/" in name
        or name.startswith("build/")
        or "/exports/" in name
        or name.startswith("exports/")
        or ".venv/" in name
        or ".pytest_cache/" in name
        or ".ruff_cache/" in name
        or name.startswith("examples/fig1_overview_v2")
        or name.startswith("examples/golden_trap_depth_picture")
        or name.startswith("examples/n3_trial_")
        or name.startswith("examples/fig5_floating_clip_mechanism")
    )
    return _step(
        "package_excluded_paths",
        "passed" if not bad else "failed",
        details={"unexpected": bad[:50], "unexpected_count": len(bad)},
    )


def _smoke_fixture_names() -> list[str]:
    suites_path = PLUGIN_ROOT / "benchmarks" / "quality_suites.yaml"
    payload = yaml.safe_load(suites_path.read_text(encoding="utf-8")) or {}
    suites = payload.get("suites") if isinstance(payload, dict) else {}
    smoke = suites.get("smoke") if isinstance(suites, dict) else {}
    fixtures = smoke.get("fixtures") if isinstance(smoke, dict) else []
    if not isinstance(fixtures, list):
        return []
    return [fixture for fixture in fixtures if isinstance(fixture, str)]


def _verify_smoke_fixture_paths(names: set[str]) -> dict[str, Any]:
    missing: list[str] = []
    for fixture in _smoke_fixture_names():
        required = [
            f"examples/{fixture}/spec.yaml",
            f"examples/{fixture}/briefing.md",
            f"examples/{fixture}/{fixture}.tex",
            f"examples/{fixture}/benchmark_contract.yaml",
        ]
        try:
            contract = benchmark_contracts.load_contract(
                fixture,
                plugin_root=PLUGIN_ROOT,
                workspace_root=PLUGIN_ROOT,
                suite_role="smoke",
            )
        except benchmark_contracts.BenchmarkContractError:
            contract = {}
        reports = contract.get("detector_reports") if isinstance(contract, dict) else {}
        if isinstance(reports, dict):
            required.extend(
                f"examples/{fixture}/{report_path}"
                for report_path in reports.values()
                if isinstance(report_path, str)
            )
        missing.extend(path for path in required if path not in names)
    return _step(
        "package_smoke_fixtures",
        "passed" if not missing else "failed",
        details={"missing": missing},
    )


def _residual_refusals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    residuals: list[dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
        refusals = result.get("candidate_refusals")
        refusal_count = int(metrics.get("refusal_count") or 0)
        refusal_list = refusals if isinstance(refusals, list) else []
        if refusal_count <= 0 and not refusal_list:
            continue
        residuals.append(
            {
                "fixture": result.get("fixture"),
                "refusal_count": refusal_count,
                "refusals": refusal_list,
            }
        )
    return residuals


def _best_candidate_render_evidence(result: dict[str, Any]) -> dict[str, Any]:
    best_candidate = result.get("best_candidate")
    scores = result.get("scores")
    if isinstance(best_candidate, str) and isinstance(scores, list):
        for score in scores:
            if not isinstance(score, dict) or score.get("candidate_id") != best_candidate:
                continue
            return {
                "rank_basis": score.get("rank_basis"),
                "render_manifest_path": score.get("render_manifest_path"),
            }
    return {
        "rank_basis": result.get("best_candidate_rank_basis"),
        "render_manifest_path": result.get("best_candidate_render_manifest_path"),
    }


def _benchmark_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    summaries: list[dict[str, Any]] = []
    metric_keys = (
        "render_success_rate",
        "candidate_specific_rank_rate",
        "refusal_count",
    )
    for result in results:
        if not isinstance(result, dict):
            continue
        metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
        summary = {
            "fixture": result.get("fixture"),
            "status": result.get("status"),
            "render_mode": result.get("render_mode"),
            "candidate_count": result.get("candidate_count"),
            "rendered_count": result.get("rendered_count"),
            "ranked_count": result.get("ranked_count"),
            "best_candidate": result.get("best_candidate"),
            "metrics": {key: metrics.get(key) for key in metric_keys if key in metrics},
            "rank_basis_counts": result.get("rank_basis_counts"),
            "best_candidate_render_evidence": _best_candidate_render_evidence(result),
        }
        summaries.append(summary)
    return summaries


def _run_quality_benchmark_step(step_name: str, suite: str) -> dict[str, Any]:
    try:
        payload = quality_benchmark.run_benchmark_suite(
            suite,
            plugin_root=PLUGIN_ROOT,
            workspace_root=PLUGIN_ROOT,
            render=True,
        )
    except Exception as exc:  # noqa: BLE001 - release report should classify the failure.
        return _step(step_name, "failed", stderr=str(exc))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    failed = int(summary.get("failed") or 0)
    regressions = int(summary.get("regression_count") or 0)
    state = "passed" if failed == 0 and regressions == 0 else "failed"
    return _step(
        step_name,
        state,
        details={
            "run_id": payload.get("run_id"),
            "suite": payload.get("suite"),
            "summary": summary,
            "render_dependency_probe": payload.get("render_dependency_probe"),
            "benchmark_results": _benchmark_results(payload),
            "residual_refusals": _residual_refusals(payload),
        },
    )


def _run_smoke_benchmark() -> dict[str, Any]:
    return _run_quality_benchmark_step("smoke_benchmark", "smoke")


def _run_dogfood_benchmark() -> dict[str, Any]:
    return _run_quality_benchmark_step("dogfood_benchmark", "dogfood")


def _run_smoke_detector_generation() -> dict[str, Any]:
    failed: list[dict[str, Any]] = []
    previews: list[dict[str, Any]] = []
    for fixture in _smoke_fixture_names():
        try:
            payload = benchmark_detector_reports.build_detector_reports(
                fixture,
                suite="smoke",
                plugin_root=PLUGIN_ROOT,
                workspace_root=PLUGIN_ROOT,
                write=False,
            )
        except Exception as exc:  # noqa: BLE001 - release report should classify the failure.
            failed.append({"fixture": fixture, "reason": str(exc)})
            continue
        states = [
            str(report.get("state"))
            for report in payload.get("reports", [])
            if isinstance(report, dict)
        ]
        previews.append({"fixture": fixture, "states": states})
        if not states or any(state != "available" for state in states):
            failed.append({"fixture": fixture, "states": states})
        if payload.get("writes"):
            failed.append({"fixture": fixture, "reason": "preview_wrote_files"})
    return _step(
        "smoke_detector_generation",
        "passed" if not failed else "failed",
        details={"previews": previews, "failed": failed},
    )


def _benchmark_baseline_step() -> dict[str, Any]:
    baseline = PLUGIN_ROOT / "benchmarks" / "baselines" / "smoke.json"
    if not baseline.is_file():
        return _step(
            "benchmark_baseline",
            "warning",
            details={"reason": "benchmark_baseline_missing"},
        )
    return _step(
        "benchmark_baseline",
        "passed",
        details={"path": str(baseline.relative_to(PLUGIN_ROOT))},
    )


def _package_size_mib(root: Path) -> float:
    total = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    return total / (1024 * 1024)


def run_release_gate(
    *,
    output_dir: Path,
    max_mib: float,
    run_targeted_tests: bool = True,
    run_full_pytest: bool = True,
    run_ruff: bool = True,
    run_claude_validate: bool = True,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    if run_targeted_tests:
        steps.append(_run_command("targeted_tests", ["uv", "run", "pytest", "-q", *TARGETED_TESTS]))
    else:
        steps.append(_step("targeted_tests", "skipped", details={"reason": "explicit skip"}))

    if run_full_pytest:
        steps.append(_run_command("full_pytest", ["uv", "run", "pytest", "-q"]))
    else:
        steps.append(_step("full_pytest", "skipped", details={"reason": "explicit skip"}))

    if run_ruff:
        steps.append(_run_command("ruff", ["uv", "run", "ruff", "check", "."]))
    else:
        steps.append(_step("ruff", "skipped", details={"reason": "explicit skip"}))

    steps.append(_run_smoke_benchmark())
    steps.append(_run_dogfood_benchmark())
    steps.append(_run_smoke_detector_generation())
    steps.append(_benchmark_baseline_step())

    zip_path = package_cowork_plugin.build_zip(output_dir)
    steps.append(_step("build_zip", "passed", details={"zip_path": str(zip_path)}))

    names = _zip_names(zip_path)
    steps.append(_verify_required_paths(names))
    steps.append(_verify_smoke_fixture_paths(names))
    steps.append(_verify_excluded_paths(names))

    with tempfile.TemporaryDirectory(prefix="figure-agent-release-gate-") as raw_unpack:
        unpack_dir = Path(raw_unpack)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(unpack_dir)
        audit_command = [
            sys.executable,
            str(SCRIPT_ROOT / "plugin_package_audit.py"),
            str(unpack_dir),
            "--max-mib",
            str(max_mib),
        ]
        steps.append(_run_command("package_audit", audit_command))
        size_mib = _package_size_mib(unpack_dir)

        claude = shutil.which("claude")
        if not run_claude_validate:
            steps.append(
                _step(
                    "claude_validate_package",
                    "skipped",
                    details={"reason": "explicit skip"},
                )
            )
            steps.append(
                _step("claude_validate_marketplace", "skipped", details={"reason": "explicit skip"})
            )
        elif claude is None:
            steps.append(
                _step(
                    "claude_validate_package",
                    "skipped",
                    details={"reason": "claude not found"},
                )
            )
            steps.append(
                _step(
                    "claude_validate_marketplace",
                    "skipped",
                    details={"reason": "claude not found"},
                )
            )
        else:
            steps.append(
                _run_command(
                    "claude_validate_package",
                    [claude, "plugin", "validate", str(unpack_dir), "--strict"],
                )
            )
            marketplace = PLUGIN_ROOT.parents[1] / ".claude-plugin" / "marketplace.json"
            steps.append(
                _run_command(
                    "claude_validate_marketplace",
                    [claude, "plugin", "validate", str(marketplace)],
                    cwd=PLUGIN_ROOT.parents[1],
                )
            )

    failed = [step for step in steps if step["state"] == "failed"]
    return {
        "schema": SCHEMA,
        "success": not failed,
        "zip_path": str(zip_path),
        "package_size_mib": round(size_mib, 3),
        "steps": steps,
        "failure_categories": [step["name"] for step in failed],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/cowork"))
    parser.add_argument("--max-mib", type=float, default=50.0)
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--skip-targeted-tests", action="store_true")
    parser.add_argument("--skip-full-pytest", action="store_true")
    parser.add_argument("--skip-ruff", action="store_true")
    parser.add_argument("--skip-claude-validate", action="store_true")
    args = parser.parse_args(argv)

    report = run_release_gate(
        output_dir=args.output,
        max_mib=args.max_mib,
        run_targeted_tests=not args.skip_targeted_tests,
        run_full_pytest=not args.skip_full_pytest,
        run_ruff=not args.skip_ruff,
        run_claude_validate=not args.skip_claude_validate,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"success={str(report['success']).lower()}")
        print(f"zip_path={report['zip_path']}")
        print(f"package_size_mib={report['package_size_mib']}")
        for step in report["steps"]:
            print(f"{step['state']} {step['name']}")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
