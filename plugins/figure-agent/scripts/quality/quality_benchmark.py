"""Lightweight quality benchmark runner for figure-agent."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import benchmark_contracts
import benchmark_detector_reports
import candidate_generator
import candidate_rank
import candidate_render
import fixture_identity
import quality_memory_index
import runtime_paths
import yaml

LIST_SCHEMA = "figure-agent.quality-benchmark-list.v1"
RUN_SCHEMA = "figure-agent.quality-benchmark-run.v1"
COMPARE_SCHEMA = "figure-agent.quality-benchmark-comparison.v1"
TREND_SCHEMA = "figure-agent.quality-benchmark-trend.v1"
VISUAL_ATTRIBUTION_SCHEMA = "figure-agent.visual-attribution-suite.v1"
VISUAL_ATTRIBUTION_STATES = {"exact", "ambiguous", "unbound"}
VISUAL_REVIEW_OUTCOMES = {"true_positive", "false_positive"}
VISUAL_EVIDENCE_OUTCOMES = {"false_positive", "linked_defect"}
TREND_REGRESSION_METRICS = (
    "completed_rate",
    "render_success_rate",
    "candidate_specific_rank_rate",
)


class QualityBenchmarkError(ValueError):
    """Raised when benchmark execution would violate local safety boundaries."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id(suite: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{suite}"


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


def _load_suites(plugin_root: Path) -> dict[str, dict[str, Any]]:
    suites = quality_memory_index._load_quality_suites(plugin_root)  # type: ignore[attr-defined]
    suites_path = plugin_root / "benchmarks" / "quality_suites.yaml"
    if suites_path.is_symlink():
        raise QualityBenchmarkError("suite_manifest_symlink")
    payload = yaml.safe_load(suites_path.read_text(encoding="utf-8")) or {}
    raw_suites = payload.get("suites") if isinstance(payload, dict) else {}
    raw_suites = raw_suites if isinstance(raw_suites, dict) else {}
    normalized: dict[str, dict[str, Any]] = {}
    for suite, fixtures in sorted(suites.items()):
        raw = raw_suites.get(suite)
        raw = raw if isinstance(raw, dict) else {}
        normalized[suite] = {
            "description": str(raw.get("description") or ""),
            "fixtures": fixtures,
        }
        for key in ("kind", "corpus"):
            value = raw.get(key)
            if isinstance(value, str) and value:
                normalized[suite][key] = value
    return normalized


def _bbox_px(value: object, *, case_id: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        raise QualityBenchmarkError(f"visual_attribution_bbox_invalid: {case_id}")
    try:
        bbox = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise QualityBenchmarkError(
            f"visual_attribution_bbox_invalid: {case_id}"
        ) from exc
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        raise QualityBenchmarkError(f"visual_attribution_bbox_invalid: {case_id}")
    return bbox


def summarize_visual_attribution_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    finding_count = len(cases)
    true_positives = sum(
        1 for case in cases if case.get("review_outcome") == "true_positive"
    )
    false_positives = sum(
        1 for case in cases if case.get("review_outcome") == "false_positive"
    )
    attribution_counts = {
        state: sum(1 for case in cases if case.get("expected_attribution") == state)
        for state in sorted(VISUAL_ATTRIBUTION_STATES)
    }
    correction_minutes = [case.get("human_correction_minutes") for case in cases]
    total_minutes = (
        round(sum(float(value) for value in correction_minutes), 3)
        if correction_minutes and all(value is not None for value in correction_minutes)
        else None
    )
    return {
        "finding_count": finding_count,
        "reviewed_true_positive_count": true_positives,
        "reviewed_false_positive_count": false_positives,
        "exact_attribution_rate": (
            round(attribution_counts["exact"] / finding_count, 6) if finding_count else 0.0
        ),
        "ambiguous_attribution_rate": (
            round(attribution_counts["ambiguous"] / finding_count, 6)
            if finding_count
            else 0.0
        ),
        "unbound_attribution_rate": (
            round(attribution_counts["unbound"] / finding_count, 6)
            if finding_count
            else 0.0
        ),
        "human_correction_minutes": total_minutes,
    }


def load_visual_attribution_corpus(plugin_root: Path) -> dict[str, Any]:
    path = plugin_root / "benchmarks" / "visual_attribution_suite.yaml"
    if path.is_symlink():
        raise QualityBenchmarkError("visual_attribution_corpus_symlink")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise QualityBenchmarkError("visual_attribution_corpus_missing") from exc
    if not isinstance(payload, dict) or payload.get("schema") != VISUAL_ATTRIBUTION_SCHEMA:
        raise QualityBenchmarkError("visual_attribution_schema_invalid")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise QualityBenchmarkError("visual_attribution_cases_missing")
    normalized_cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_case in enumerate(cases):
        if not isinstance(raw_case, dict):
            raise QualityBenchmarkError(f"visual_attribution_case_invalid: {index}")
        if "expected_by_fixture" in raw_case:
            raise QualityBenchmarkError("fixture_specific_expectation_forbidden")
        if "expected_by_bbox" in raw_case:
            raise QualityBenchmarkError("coordinate_specific_expectation_forbidden")
        case_id = str(raw_case.get("id") or "")
        if not case_id or case_id in seen_ids:
            raise QualityBenchmarkError(f"visual_attribution_case_id_invalid: {index}")
        seen_ids.add(case_id)
        fixture = str(raw_case.get("fixture") or "")
        fixture_identity.validate_fixture_name(fixture)
        finding = raw_case.get("finding")
        if not isinstance(finding, dict):
            raise QualityBenchmarkError(f"visual_attribution_finding_invalid: {case_id}")
        normalized_finding = dict(finding)
        normalized_finding["bbox_px"] = _bbox_px(
            finding.get("bbox_px"),
            case_id=case_id,
        )
        review_outcome = str(raw_case.get("review_outcome") or "")
        if review_outcome not in VISUAL_REVIEW_OUTCOMES:
            raise QualityBenchmarkError(f"visual_attribution_review_invalid: {case_id}")
        expected = str(raw_case.get("expected_attribution") or "")
        if expected not in VISUAL_ATTRIBUTION_STATES:
            raise QualityBenchmarkError(f"visual_attribution_expected_invalid: {case_id}")
        minutes = raw_case.get("human_correction_minutes")
        if minutes is not None:
            try:
                minutes = float(minutes)
            except (TypeError, ValueError) as exc:
                raise QualityBenchmarkError(
                    f"visual_attribution_minutes_invalid: {case_id}"
                ) from exc
            if minutes < 0:
                raise QualityBenchmarkError(
                    f"visual_attribution_minutes_invalid: {case_id}"
                )
        normalized_cases.append(
            {
                **raw_case,
                "finding": normalized_finding,
                "review_outcome": review_outcome,
                "expected_attribution": expected,
                "human_correction_minutes": minutes,
            }
        )
    computed = summarize_visual_attribution_cases(normalized_cases)
    if payload.get("baseline_metrics") != computed:
        raise QualityBenchmarkError("visual_attribution_baseline_drift")
    historical = payload.get("historical_evidence")
    if not isinstance(historical, dict):
        raise QualityBenchmarkError("visual_attribution_historical_evidence_invalid")
    reviewed_evidence = payload.get("reviewed_evidence")
    if not isinstance(reviewed_evidence, list) or not reviewed_evidence:
        raise QualityBenchmarkError("visual_attribution_reviewed_evidence_missing")
    normalized_evidence: list[dict[str, Any]] = []
    seen_evidence_ids: set[str] = set()
    for index, raw_evidence in enumerate(reviewed_evidence):
        if not isinstance(raw_evidence, dict):
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_invalid: {index}"
            )
        evidence_id = str(raw_evidence.get("id") or "")
        if not evidence_id or evidence_id in seen_evidence_ids:
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_id_invalid: {index}"
            )
        seen_evidence_ids.add(evidence_id)
        source_relative = Path(str(raw_evidence.get("source_path") or ""))
        if (
            not source_relative.parts
            or source_relative.is_absolute()
            or ".." in source_relative.parts
        ):
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_path_invalid: {evidence_id}"
            )
        source_path = plugin_root / source_relative
        if source_path.is_symlink() or not source_path.is_file():
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_source_missing: {evidence_id}"
            )
        source_sha256 = str(raw_evidence.get("source_sha256") or "")
        actual_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if source_sha256 != actual_sha256:
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_hash_mismatch: {evidence_id}"
            )
        review_outcome = str(raw_evidence.get("review_outcome") or "")
        if review_outcome not in VISUAL_EVIDENCE_OUTCOMES:
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_outcome_invalid: {evidence_id}"
            )
        detector_ref = str(raw_evidence.get("detector_ref") or "")
        source_locator = str(raw_evidence.get("source_locator") or "")
        linked_finding_id = raw_evidence.get("linked_finding_id")
        if not detector_ref or not source_locator:
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_locator_invalid: {evidence_id}"
            )
        if review_outcome == "linked_defect" and not linked_finding_id:
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_link_invalid: {evidence_id}"
            )
        if raw_evidence.get("authority") != "reviewed_evidence_only":
            raise QualityBenchmarkError(
                f"visual_attribution_reviewed_evidence_authority_invalid: {evidence_id}"
            )
        normalized_evidence.append(
            {
                **raw_evidence,
                "source_path": source_relative.as_posix(),
                "source_sha256": source_sha256,
                "review_outcome": review_outcome,
                "detector_ref": detector_ref,
                "source_locator": source_locator,
            }
        )
    if {item["review_outcome"] for item in normalized_evidence} != (
        VISUAL_EVIDENCE_OUTCOMES
    ):
        raise QualityBenchmarkError(
            "visual_attribution_reviewed_evidence_outcomes_incomplete"
        )
    return {
        **payload,
        "cases": normalized_cases,
        "reviewed_evidence": normalized_evidence,
        "baseline_metrics": computed,
    }


def _run_visual_attribution_suite(
    suite: str,
    *,
    paths: runtime_paths.RuntimePaths,
    limit: int | None,
    render: bool,
    write: bool,
    run_id: str | None,
) -> dict[str, Any]:
    if render:
        raise QualityBenchmarkError("visual_attribution_render_not_supported")
    if write:
        raise QualityBenchmarkError("visual_attribution_write_not_supported")
    corpus = load_visual_attribution_corpus(paths.plugin_root)
    cases = list(corpus["cases"])
    if limit is not None:
        cases = cases[:limit]
    metrics = summarize_visual_attribution_cases(cases)
    results = [
        {
            "fixture": case["fixture"],
            "case_id": case["id"],
            "status": "completed",
            "detector": case["detector"],
            "review_outcome": case["review_outcome"],
            "expected_attribution": case["expected_attribution"],
            "human_correction_minutes": case["human_correction_minutes"],
            "metrics": {},
        }
        for case in cases
    ]
    return {
        "schema": RUN_SCHEMA,
        "run_id": run_id or _run_id(suite),
        "suite": suite,
        "suite_kind": "visual_attribution",
        "generated_at": _utc_now(),
        "fixture_count": len(cases),
        "render_dependency_probe": {"state": "not_requested", "tools": {}, "missing": []},
        "results": results,
        "summary": {
            "completed": len(cases),
            "skipped": 0,
            "failed": 0,
            "regression_count": 0,
        },
        "capability_metrics": {
            "completed_rate": 1.0 if cases else 0.0,
            "render_success_rate": 0.0,
            "candidate_specific_rank_rate": 0.0,
            "mean_rank_score": 0.0,
        },
        "attribution_metrics": metrics,
        "historical_evidence": corpus["historical_evidence"],
        "acceptance": "machine_valid_only",
        "tool_defect_candidates": [],
        "writes": [],
    }


def build_benchmark_list(*, plugin_root: Path | None = None) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root)
    return {
        "schema": LIST_SCHEMA,
        "generated_at": _utc_now(),
        "suites": _load_suites(paths.plugin_root),
    }


def _status_summary(example_dir: Path) -> dict[str, Any]:
    try:
        import status

        payload = status.infer_stage(example_dir)
    except Exception as exc:  # noqa: BLE001 - benchmark should degrade into diagnostics.
        return {"state": "unavailable", "reason": str(exc)}
    return {
        "state": "available",
        "workflow_ready": bool(payload.get("workflow_ready")),
        "render_state": payload.get("render_state"),
        "export_state": payload.get("export_state"),
        "critique_state": payload.get("critique_state"),
    }


def _candidate_manifest_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    apply_authority = str(candidate.get("apply_authority") or "review_only")
    if apply_authority == "rejected":
        hard_gate_state = "rejected"
    elif apply_authority == "apply_eligible":
        hard_gate_state = "pass"
    else:
        hard_gate_state = "human_required"
    return {
        "candidate_id": str(candidate.get("id") or "unknown"),
        "apply_authority": apply_authority,
        "edit_class": candidate.get("edit_class"),
        "family": candidate.get("family"),
        "verification": {"hard_gate_state": hard_gate_state},
    }


def _render_dependency_probe() -> dict[str, Any]:
    tools = {
        "lualatex": candidate_render._which("lualatex"),  # noqa: SLF001
        "pdftocairo": candidate_render._which("pdftocairo"),  # noqa: SLF001
    }
    missing = [name for name, path in tools.items() if path is None]
    return {
        "state": "fail" if missing else "pass",
        "tools": {
            name: {"available": path is not None, "path": path}
            for name, path in tools.items()
        },
        "missing": missing,
    }


def _fixture_artifact_path(example_dir: Path, relative: str) -> Path:
    path = candidate_render.candidate_contracts.fixture_relative_path(example_dir, relative)
    if path.is_symlink():
        raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {relative}")
    return path


def _first_panel_id(example_dir: Path) -> str | None:
    spec_path = _fixture_artifact_path(example_dir, "spec.yaml")
    if not spec_path.is_file():
        return None
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    panels = payload.get("panels")
    if not isinstance(panels, list):
        return None
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        panel_id = panel.get("id")
        if isinstance(panel_id, str) and panel_id:
            return panel_id
    return None


def _contract_candidate_family(contract: dict[str, Any]) -> str | None:
    if contract.get("state") != "present":
        return None
    families = contract.get("candidate_families")
    if not isinstance(families, list):
        return None
    for family in families:
        if isinstance(family, str) and family:
            return family
    return None


def _build_contract_candidate_set(
    fixture: str,
    *,
    example_dir: Path,
    contract: dict[str, Any],
    paths: runtime_paths.RuntimePaths,
) -> dict[str, Any]:
    default_set = candidate_generator.build_candidate_set(
        fixture,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    default_candidates = default_set.get("candidates")
    if isinstance(default_candidates, list) and default_candidates:
        return default_set
    family = _contract_candidate_family(contract)
    panel = _first_panel_id(example_dir) if family is not None else None
    if family is None or panel is None:
        return default_set
    return candidate_generator.build_candidate_set(
        fixture,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
        panel=panel,
        family=family,
    )


def _load_fixture_json(example_dir: Path, relative: str | None) -> dict[str, Any] | None:
    if relative is None:
        return None
    path = _fixture_artifact_path(example_dir, relative)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualityBenchmarkError(f"candidate_artifact_invalid: {relative}")
    return payload


def _stage_status(render_manifest: dict[str, Any] | None, stage: str) -> str:
    if not isinstance(render_manifest, dict):
        return "unrendered"
    stages = render_manifest.get("stages")
    if not isinstance(stages, dict):
        return "unrendered"
    value = stages.get(stage)
    if not isinstance(value, dict):
        return "unrendered"
    return str(value.get("status") or "unrendered")


def _rank_basis(render_manifest: dict[str, Any] | None, *, render_requested: bool) -> str:
    if not render_requested:
        return "unrendered"
    if not isinstance(render_manifest, dict):
        return "blocked"
    statuses = [
        _stage_status(render_manifest, stage)
        for stage in ("compile", "export", "evaluate")
    ]
    if "dependency_missing" in statuses:
        return "dependency_missing"
    if "failed" in statuses:
        return "failed"
    if "blocked" in statuses:
        return "blocked"
    if _stage_status(render_manifest, "evaluate") == "rendered_needs_human_review":
        return "candidate_specific_render"
    return "blocked"


def _render_mode(
    rank_basis_counts: dict[str, int],
    *,
    render_requested: bool,
    candidate_count: int,
) -> str:
    if not render_requested:
        return "not_requested"
    if candidate_count == 0:
        return "blocked"
    if rank_basis_counts.get("dependency_missing", 0):
        return "dependency_missing"
    if rank_basis_counts.get("failed", 0):
        return "failed"
    if rank_basis_counts.get("blocked", 0):
        return "blocked"
    if rank_basis_counts.get("candidate_specific_render", 0) == candidate_count:
        return "rendered"
    return "blocked"


def _empty_render_mode(render_requested: bool) -> str:
    return "blocked" if render_requested else "not_requested"


def _rank_basis_counts() -> dict[str, int]:
    return {
        "candidate_specific_render": 0,
        "dependency_missing": 0,
        "blocked": 0,
        "failed": 0,
        "unrendered": 0,
    }


def _rendered_by_candidate(
    example_dir: Path,
    render_result: dict[str, Any],
) -> dict[str, tuple[dict[str, Any] | None, dict[str, Any] | None]]:
    rendered = render_result.get("rendered")
    if not isinstance(rendered, list):
        return {}
    mapped: dict[str, tuple[dict[str, Any] | None, dict[str, Any] | None]] = {}
    for item in rendered:
        if not isinstance(item, dict):
            continue
        candidate_id = item.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            continue
        candidate_manifest = _load_fixture_json(example_dir, item.get("manifest"))
        render_manifest = _load_fixture_json(example_dir, item.get("render_manifest"))
        if (
            isinstance(candidate_manifest, dict)
            and candidate_manifest.get("candidate_id") != candidate_id
        ):
            candidate_manifest = None
        if (
            isinstance(render_manifest, dict)
            and render_manifest.get("candidate_id") != candidate_id
        ):
            render_manifest = None
        mapped[candidate_id] = (candidate_manifest, render_manifest)
    return mapped


def _load_fixture_memory_index(example_dir: Path) -> dict[str, Any] | None:
    build_dir = example_dir / "build"
    memory_dir = build_dir / "memory"
    output = memory_dir / "quality_memory_index.json"
    for path in (build_dir, memory_dir, output):
        if path.is_symlink():
            raise QualityBenchmarkError("sandbox_symlink_forbidden: memory_index")
    if not output.is_file():
        return None
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualityBenchmarkError("memory_index_invalid")
    return payload


def _metric_value(report: dict[str, Any], metric: str, key: str) -> float | None:
    metrics = report.get("metrics")
    if isinstance(metrics, dict):
        metric_payload = metrics.get(metric)
        if isinstance(metric_payload, dict):
            try:
                return float(metric_payload.get(key))
            except (TypeError, ValueError):
                return None
    bucket = report.get(key)
    if isinstance(bucket, dict):
        try:
            return float(bucket.get(metric))
        except (TypeError, ValueError):
            return None
    return None


def _movement_passes(baseline: float, candidate: float, operator: str) -> bool:
    if operator == "decrease":
        return candidate < baseline
    if operator == "decrease_or_equal":
        return candidate <= baseline
    if operator == "increase":
        return candidate > baseline
    if operator == "increase_or_equal":
        return candidate >= baseline
    if operator == "unchanged":
        return candidate == baseline
    return False


def _detector_evaluation(example_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    if contract.get("state") != "present":
        return {"state": "not_available", "movements": [], "missing": []}
    expected = contract.get("expected_movement")
    if not isinstance(expected, dict) or not expected:
        return {"state": "not_required", "movements": [], "missing": []}
    reports = contract.get("detector_reports")
    reports = reports if isinstance(reports, dict) else {}
    loaded_reports: dict[str, dict[str, Any]] = {}
    movements: list[dict[str, Any]] = []
    missing: list[str] = []
    failed = False
    for metric, operator in expected.items():
        metric_name = str(metric)
        detector = metric_name.split(".", 1)[0]
        report_rel = reports.get(detector)
        if not isinstance(report_rel, str):
            missing.append(f"{detector}:report_path")
            failed = True
            continue
        report_path = example_dir / report_rel
        if report_path.is_symlink():
            missing.append(f"{detector}:report_symlink")
            failed = True
            continue
        if not report_path.is_file():
            missing.append(f"{detector}:report_missing")
            failed = True
            continue
        if detector not in loaded_reports:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                missing.append(f"{detector}:report_invalid")
                failed = True
                continue
            loaded_reports[detector] = payload
        baseline = benchmark_detector_reports.metric_value(
            loaded_reports[detector],
            metric_name,
            "baseline",
        )
        candidate = benchmark_detector_reports.metric_value(
            loaded_reports[detector],
            metric_name,
            "candidate",
        )
        if baseline is None or candidate is None:
            missing.append(f"{metric_name}:metric_missing")
            failed = True
            continue
        passed = _movement_passes(baseline, candidate, str(operator))
        failed = failed or not passed
        movements.append(
            {
                "metric": metric_name,
                "baseline": baseline,
                "candidate": candidate,
                "operator": str(operator),
                "state": "passed" if passed else "failed",
            }
        )
    if missing:
        state = "missing"
    elif failed:
        state = "failed"
    else:
        state = "passed"
    return {"state": state, "movements": movements, "missing": missing}


def _detector_failure_reason(
    detector_evaluation: dict[str, Any],
    *,
    contract: dict[str, Any],
    suite_role: str | None,
) -> str | None:
    release = contract.get("release") if isinstance(contract.get("release"), dict) else {}
    release_blocking = suite_role == "smoke" or bool(release.get("release_blocking"))
    if not release_blocking:
        return None
    state = str(detector_evaluation.get("state") or "")
    if state == "missing":
        return "required_detector_missing"
    if state == "failed":
        return "expected_detector_movement_failed"
    return None


def _run_fixture(
    fixture: str,
    *,
    paths: runtime_paths.RuntimePaths,
    render: bool,
    render_dependency_probe: dict[str, Any] | None = None,
    suite_role: str | None = None,
) -> dict[str, Any]:
    example_dir = paths.examples_dir / fixture
    try:
        contract = benchmark_contracts.load_contract(
            fixture,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
            suite_role=suite_role,
        )
    except benchmark_contracts.BenchmarkContractError as exc:
        return {
            "fixture": fixture,
            "status": "failed",
            "reason": str(exc),
            "contract": {
                "schema": benchmark_contracts.SCHEMA,
                "state": "invalid",
                "fixture": fixture,
                "reason": str(exc),
            },
            "candidate_count": 0,
            "rendered_count": 0,
            "ranked_count": 0,
            "render_mode": _empty_render_mode(render),
            "hard_gate_failures": [],
            "best_candidate": None,
            "memory_prior_used": False,
            "detector_evaluation": {"state": "unavailable", "movements": [], "missing": []},
            "metrics": {},
        }
    if not example_dir.is_dir():
        return {
            "fixture": fixture,
            "status": "skipped",
            "reason": "missing_fixture",
            "contract": contract,
            "candidate_count": 0,
            "rendered_count": 0,
            "ranked_count": 0,
            "render_mode": _empty_render_mode(render),
            "hard_gate_failures": [],
            "best_candidate": None,
            "memory_prior_used": False,
            "metrics": {},
        }
    status_payload = _status_summary(example_dir)
    try:
        detector_evaluation = _detector_evaluation(example_dir, contract)
        candidate_set = _build_contract_candidate_set(
            fixture,
            example_dir=example_dir,
            contract=contract,
            paths=paths,
        )
        candidates = [
            candidate
            for candidate in candidate_set.get("candidates", [])
            if isinstance(candidate, dict)
        ]
        rendered_by_candidate: dict[
            str,
            tuple[dict[str, Any] | None, dict[str, Any] | None],
        ] = {}
        if render:
            render_result = candidate_render.render_candidate_set(
                fixture,
                candidate_set,
                plugin_root=paths.plugin_root,
                workspace_root=paths.workspace_root,
                compile=True,
                export=True,
                evaluate=True,
            )
            rendered_by_candidate = _rendered_by_candidate(example_dir, render_result)
        memory_index = _load_fixture_memory_index(example_dir)
        scores = []
        rank_basis_counts = _rank_basis_counts()
        for candidate in candidates:
            candidate_id = str(candidate.get("id") or "")
            candidate_manifest, render_manifest = rendered_by_candidate.get(
                candidate_id,
                (None, None),
            )
            basis = _rank_basis(render_manifest, render_requested=render)
            rank_basis_counts[basis] += 1
            score_manifest = (
                candidate_manifest
                if isinstance(candidate_manifest, dict)
                else _candidate_manifest_from_candidate(candidate)
            )
            score = candidate_rank.score_manifest(
                score_manifest,
                render_manifest=render_manifest if render else None,
                candidate=candidate,
                memory_index=memory_index,
                detector_evaluation=detector_evaluation,
            )
            score["candidate_hash"] = candidate.get("candidate_hash")
            score["candidate_manifest_path"] = (
                f"build/candidates/{candidate_id}/candidate_manifest.json"
                if isinstance(candidate_manifest, dict)
                else None
            )
            score["render_manifest_path"] = (
                f"build/candidates/{candidate_id}/render_manifest.json"
                if isinstance(render_manifest, dict)
                else None
            )
            score["rank_basis"] = basis
            source_defect = candidate.get("source_defect")
            if isinstance(source_defect, dict):
                score["source_defect"] = source_defect
            scores.append(score)
        scores.sort(key=lambda score: (-float(score["rank_score"]), str(score["candidate_id"])))
        hard_gate_failures = [
            str(score["candidate_id"])
            for score in scores
            if score.get("hard_gate_state") == "rejected"
        ]
        mean_rank = (
            round(sum(float(score["rank_score"]) for score in scores) / len(scores), 4)
            if scores
            else 0.0
        )
        detector_failure_reason = _detector_failure_reason(
            detector_evaluation,
            contract=contract,
            suite_role=suite_role,
        )
        candidate_count = len(candidates)
        rendered_count = rank_basis_counts["candidate_specific_render"]
        render_mode = _render_mode(
            rank_basis_counts,
            render_requested=render,
            candidate_count=candidate_count,
        )
        render_success_rate = rendered_count / candidate_count if candidate_count else 0.0
        candidate_specific_rank_rate = rendered_count / len(scores) if scores else 0.0
        return {
            "fixture": fixture,
            "status": "failed" if detector_failure_reason else "completed",
            **({"reason": detector_failure_reason} if detector_failure_reason else {}),
            "contract": contract,
            "candidate_count": candidate_count,
            "rendered_count": rendered_count,
            "ranked_count": len(scores),
            "render_mode": render_mode,
            "rank_basis_counts": rank_basis_counts,
            "scores": scores,
            "candidate_refusals": candidate_set.get("refusals", []),
            "hard_gate_failures": hard_gate_failures,
            "best_candidate": scores[0]["candidate_id"] if scores else None,
            "memory_prior_used": memory_index is not None,
            "detector_evaluation": detector_evaluation,
            "status_summary": status_payload,
            "metrics": {
                "candidate_count": candidate_count,
                "safe_candidate_defect_count": candidate_set.get("metrics", {}).get(
                    "safe_candidate_defect_count",
                    0,
                ),
                "safe_candidate_coverage": candidate_set.get("metrics", {}).get(
                    "candidate_defect_coverage",
                    0.0,
                ),
                "refusal_count": len(candidate_set.get("refusals", [])),
                "compile_success_rate": 1.0 if status_payload.get("state") == "available" else 0.0,
                "render_success_rate": render_success_rate,
                "candidate_specific_rank_rate": candidate_specific_rank_rate,
                "new_blocker_count": len(hard_gate_failures),
                "stale_evidence_block_count": 0,
                "mean_rank_score": mean_rank,
                "regression_count": len(hard_gate_failures),
            },
        }
    except Exception as exc:  # noqa: BLE001 - one fixture must not abort the suite.
        return {
            "fixture": fixture,
            "status": "failed",
            "reason": str(exc),
            "contract": contract,
            "candidate_count": 0,
            "rendered_count": 0,
            "ranked_count": 0,
            "render_mode": _empty_render_mode(render),
            "hard_gate_failures": [],
            "best_candidate": None,
            "memory_prior_used": False,
            "detector_evaluation": {"state": "unavailable", "movements": [], "missing": []},
            "metrics": {},
        }


def _ensure_run_output(workspace_root: Path, run_id: str) -> Path:
    fixture_identity.validate_fixture_name(run_id)
    scratch_root = workspace_root / ".scratch"
    benchmark_root = scratch_root / "figure-agent-benchmarks"
    run_dir = benchmark_root / run_id
    output = run_dir / "run.json"
    for label, path in (
        ("scratch", scratch_root),
        ("benchmark", benchmark_root),
        ("run", run_dir),
        ("output", output),
    ):
        if path.is_symlink():
            raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {label}")
    reason = _forbidden_write_reason(output)
    if reason is not None:
        raise QualityBenchmarkError(reason)
    run_dir.mkdir(parents=True, exist_ok=False)
    return output


def _trend_output(workspace_root: Path, suite: str) -> Path:
    fixture_identity.validate_fixture_name(suite)
    scratch_root = workspace_root / ".scratch"
    benchmark_root = scratch_root / "figure-agent-benchmarks"
    trend_root = benchmark_root / "trends"
    output = trend_root / f"{suite}.jsonl"
    for label, path in (
        ("scratch", scratch_root),
        ("benchmark", benchmark_root),
        ("trends", trend_root),
        ("trend", output),
    ):
        if path.is_symlink():
            raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {label}")
    reason = _forbidden_write_reason(output)
    if reason is not None:
        raise QualityBenchmarkError(reason)
    trend_root.mkdir(parents=True, exist_ok=True)
    for label, path in (
        ("scratch", scratch_root),
        ("benchmark", benchmark_root),
        ("trends", trend_root),
    ):
        if path.is_symlink():
            raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {label}")
    return output


def _relative_to_workspace(workspace_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError as exc:
        raise QualityBenchmarkError("benchmark_output_escape") from exc


def _capability_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    fixture_count = len(results)
    completed = sum(1 for result in results if result.get("status") == "completed")
    metric_names = (
        "render_success_rate",
        "candidate_specific_rank_rate",
        "mean_rank_score",
    )
    metrics = {
        "completed_rate": round(completed / fixture_count, 4) if fixture_count else 0.0,
    }
    for metric_name in metric_names:
        values = [_metric(result, metric_name) for result in results]
        metrics[metric_name] = (
            round(sum(values) / len(values), 4) if values else 0.0
        )
    return metrics


def _last_trend_row(path: Path) -> dict[str, Any] | None:
    if path.is_symlink():
        raise QualityBenchmarkError("sandbox_symlink_forbidden: trend")
    if not path.is_file():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    payload = json.loads(lines[-1])
    if not isinstance(payload, dict):
        raise QualityBenchmarkError("benchmark_trend_invalid")
    return payload


def _trend_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": TREND_SCHEMA,
        "generated_at": payload.get("generated_at"),
        "run_id": payload.get("run_id"),
        "suite": payload.get("suite"),
        "summary": payload.get("summary", {}),
        "capability_metrics": payload.get("capability_metrics", {}),
    }


def _trend_regression_tool_defects(
    *,
    suite: str,
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(previous, dict):
        return []
    previous_metrics = previous.get("capability_metrics")
    current_metrics = current.get("capability_metrics")
    if not isinstance(previous_metrics, dict) or not isinstance(current_metrics, dict):
        return []
    defects: list[dict[str, Any]] = []
    for metric in TREND_REGRESSION_METRICS:
        previous_value = _metric({"metrics": previous_metrics}, metric)
        current_value = _metric({"metrics": current_metrics}, metric)
        if current_value >= previous_value:
            continue
        defects.append(
            {
                "id": f"BTD{len(defects) + 1:03d}",
                "symptom": "benchmark loop capability regressed",
                "expected_behavior": (
                    "loop capability metrics should not regress between trend rows"
                ),
                "actual_behavior": {
                    "suite": suite,
                    "metric": metric,
                    "previous": previous_value,
                    "current": current_value,
                    "previous_run_id": previous.get("run_id"),
                    "current_run_id": current.get("run_id"),
                },
                "minimal_reproduction": f"fig-agent benchmark-run --suite {suite} --write --json",
                "recommended_fix": (
                    "inspect benchmark trend regression before trusting loop automation"
                ),
            }
        )
    return defects


def _append_trend_row(
    workspace_root: Path,
    payload: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    suite = str(payload.get("suite") or "")
    output = _trend_output(workspace_root, suite)
    previous = _last_trend_row(output)
    row = _trend_row(payload)
    defects = _trend_regression_tool_defects(
        suite=suite,
        previous=previous,
        current=row,
    )
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return _relative_to_workspace(workspace_root, output), defects


def _load_run(workspace_root: Path, run_id: str) -> dict[str, Any]:
    try:
        fixture_identity.validate_fixture_name(run_id)
    except ValueError as exc:
        raise QualityBenchmarkError(str(exc)) from exc
    scratch_root = workspace_root / ".scratch"
    benchmark_root = scratch_root / "figure-agent-benchmarks"
    run_dir = benchmark_root / run_id
    output = run_dir / "run.json"
    for label, path in (
        ("scratch", scratch_root),
        ("benchmark", benchmark_root),
        ("run", run_dir),
        ("output", output),
    ):
        if path.is_symlink():
            raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {label}")
    if not output.is_file():
        raise QualityBenchmarkError(f"benchmark_run_missing: {run_id}")
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualityBenchmarkError(f"benchmark_run_invalid: {run_id}")
    return payload


def _result_by_fixture(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    results = run.get("results")
    if not isinstance(results, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for result in results:
        if isinstance(result, dict) and isinstance(result.get("fixture"), str):
            mapped[result["fixture"]] = result
    return mapped


def _metric(result: dict[str, Any], key: str) -> float:
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        return 0.0
    try:
        return float(metrics.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _best_candidate_has_render_evidence(result: dict[str, Any]) -> bool:
    rank_basis = result.get("best_candidate_rank_basis")
    render_manifest_path = result.get("best_candidate_render_manifest_path")
    if isinstance(rank_basis, str) or isinstance(render_manifest_path, str):
        return rank_basis == "candidate_specific_render" and bool(render_manifest_path)

    best_candidate = result.get("best_candidate")
    scores = result.get("scores")
    if not isinstance(best_candidate, str) or not isinstance(scores, list):
        return False
    for score in scores:
        if not isinstance(score, dict) or score.get("candidate_id") != best_candidate:
            continue
        return (
            score.get("rank_basis") == "candidate_specific_render"
            and bool(score.get("render_manifest_path"))
        )
    return False


def _compare_fixture(
    fixture: str,
    baseline: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    regressions: list[str] = []
    if baseline is None:
        regressions.append("new_fixture_without_baseline")
    if candidate is None:
        regressions.append("missing_candidate_fixture")
        return {
            "fixture": fixture,
            "baseline_status": baseline.get("status") if baseline else None,
            "candidate_status": None,
            "regressions": regressions,
        }
    baseline_failures = set(baseline.get("hard_gate_failures", []) if baseline else [])
    candidate_failures = set(candidate.get("hard_gate_failures", []))
    new_failures = sorted(candidate_failures - baseline_failures)
    if new_failures:
        regressions.append(f"new_hard_gate_failures:{','.join(new_failures)}")
    if (
        baseline
        and baseline.get("status") == "completed"
        and candidate.get("status") != "completed"
    ):
        regressions.append(f"status_regression:{candidate.get('status')}")
    if (
        not new_failures
        and _metric(candidate, "new_blocker_count") > _metric(baseline or {}, "new_blocker_count")
    ):
        regressions.append("new_blocker_count_increased")
    if baseline and _metric(candidate, "render_success_rate") < _metric(
        baseline,
        "render_success_rate",
    ):
        regressions.append("render_success_rate_decreased")
    if baseline and _metric(candidate, "candidate_specific_rank_rate") < _metric(
        baseline,
        "candidate_specific_rank_rate",
    ):
        regressions.append("candidate_specific_rank_rate_decreased")
    if (
        baseline
        and _best_candidate_has_render_evidence(baseline)
        and not _best_candidate_has_render_evidence(candidate)
    ):
        regressions.append("best_candidate_render_evidence_missing")
    return {
        "fixture": fixture,
        "baseline_status": baseline.get("status") if baseline else None,
        "candidate_status": candidate.get("status"),
        "baseline_rank_score": _metric(baseline or {}, "mean_rank_score"),
        "candidate_rank_score": _metric(candidate, "mean_rank_score"),
        "regressions": regressions,
    }


def compare_benchmark_runs(
    baseline_run: str,
    candidate_run: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    baseline = _load_run(paths.workspace_root, baseline_run)
    candidate = _load_run(paths.workspace_root, candidate_run)
    baseline_results = _result_by_fixture(baseline)
    candidate_results = _result_by_fixture(candidate)
    fixtures = sorted(set(baseline_results) | set(candidate_results))
    comparisons = [
        _compare_fixture(
            fixture,
            baseline_results.get(fixture),
            candidate_results.get(fixture),
        )
        for fixture in fixtures
    ]
    regression_count = sum(len(item["regressions"]) for item in comparisons)
    return {
        "schema": COMPARE_SCHEMA,
        "generated_at": _utc_now(),
        "baseline_run": baseline_run,
        "candidate_run": candidate_run,
        "fixture_comparisons": comparisons,
        "summary": {
            "fixture_count": len(fixtures),
            "regression_count": regression_count,
        },
    }


def run_benchmark_suite(
    suite: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    limit: int | None = None,
    render: bool = False,
    write: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(suite)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    suites = _load_suites(paths.plugin_root)
    if suite not in suites:
        raise QualityBenchmarkError(f"unknown_suite: {suite}")
    if suites[suite].get("kind") == "visual_attribution":
        return _run_visual_attribution_suite(
            suite,
            paths=paths,
            limit=limit,
            render=render,
            write=write,
            run_id=run_id,
        )
    fixtures = list(suites[suite]["fixtures"])
    if limit is not None:
        fixtures = fixtures[:limit]
    run_id = run_id or _run_id(suite)
    render_dependency_probe = _render_dependency_probe() if render else {
        "state": "not_requested",
        "tools": {},
        "missing": [],
    }
    results = [
        _run_fixture(
            fixture,
            paths=paths,
            render=render,
            render_dependency_probe=render_dependency_probe,
            suite_role=suite,
        )
        for fixture in fixtures
    ]
    summary = {
        "completed": sum(1 for result in results if result["status"] == "completed"),
        "skipped": sum(1 for result in results if result["status"] == "skipped"),
        "failed": sum(1 for result in results if result["status"] == "failed"),
        "regression_count": sum(
            len(result.get("hard_gate_failures", []))
            for result in results
            if result["status"] == "completed"
        ),
    }
    capability_metrics = _capability_metrics(results)
    payload = {
        "schema": RUN_SCHEMA,
        "run_id": run_id,
        "suite": suite,
        "generated_at": _utc_now(),
        "fixture_count": len(fixtures),
        "render_dependency_probe": render_dependency_probe,
        "results": results,
        "summary": summary,
        "capability_metrics": capability_metrics,
        "tool_defect_candidates": [],
        "writes": [],
    }
    if write:
        output = _ensure_run_output(paths.workspace_root, run_id)
        trend_write, tool_defects = _append_trend_row(paths.workspace_root, payload)
        payload["tool_defect_candidates"] = tool_defects
        payload["writes"] = [
            f".scratch/figure-agent-benchmarks/{run_id}/run.json",
            trend_write,
        ]
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="quality_benchmark.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--suite", required=True)
    run_parser.add_argument("--limit", type=int)
    run_parser.add_argument("--render", action="store_true")
    run_parser.add_argument("--write", action="store_true")
    run_parser.add_argument("--json", action="store_true")
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("baseline_run")
    compare_parser.add_argument("candidate_run")
    compare_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "list":
        payload = build_benchmark_list(plugin_root=plugin_root)
    elif args.command == "run":
        payload = run_benchmark_suite(
            args.suite,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
            limit=args.limit,
            render=args.render,
            write=args.write,
        )
    else:
        payload = compare_benchmark_runs(
            args.baseline_run,
            args.candidate_run,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
