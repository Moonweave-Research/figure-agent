"""Lint critique.md without writing adjudication state."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    build_adjudication_scaffold,
)
from critique_contract import (  # noqa: E402
    CritiqueContractError,
    critique_finding_id,
    critique_findings,
    load_critique_frontmatter,
)
from critique_evidence_lint import critique_evidence_violations  # noqa: E402
from critique_schema_vocab import MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
VISUAL_CLASH_ACCOUNTING_SCHEMA = "figure-agent.critique.v1.7"
CROP_AUDIT_ACCOUNTING_SCHEMA = "figure-agent.critique.v1.8"
VISUAL_CLASH_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.7",
        "figure-agent.critique.v1.8",
        "figure-agent.critique.v1.9",
        "figure-agent.critique.v1.10",
    }
)
CROP_AUDIT_ACCOUNTING_SCHEMAS = frozenset(
    {"figure-agent.critique.v1.8", "figure-agent.critique.v1.9", "figure-agent.critique.v1.10"}
)
STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS = frozenset({"figure-agent.critique.v1.10"})
_VISUAL_CLASH_ACCEPT_MIN_OBSERVATION_CHARS = 80
_VISUAL_CLASH_ACCEPT_RATIONALE_MARKERS = (
    "false positive",
    "not ",
    "intentional",
    "acceptable because",
    "separate",
    "distinct",
    "outside",
    "axis",
    "legend",
    "background",
    "decorative",
    "convention",
)
_HISTORICAL_VISUAL_CLASH_FIXTURE = "fig1_visual_clash_regression"
_HISTORICAL_VISUAL_CLASH_EXPECTED_KINDS = {
    ("VC026", "V"): "label_glyph_overlaps_internal_drawing",
    ("VC027", "s"): "label_glyph_overlaps_internal_drawing",
    ("VC050", "HV+"): "label_backdrop_overflows_outline",
}


@dataclass(frozen=True)
class CritiqueLintViolation:
    severity: str
    category: str
    message: str


def _duplicate_finding_id_violations(frontmatter: dict[str, Any]) -> list[CritiqueLintViolation]:
    seen: set[str] = set()
    violations: list[CritiqueLintViolation] = []
    for index, finding in enumerate(critique_findings(frontmatter)):
        finding_id = critique_finding_id(finding, f"critique finding {index}")
        if finding_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="duplicate_finding_id",
                    message=f"duplicate finding_id: {finding_id}",
                )
            )
        seen.add(finding_id)
    return violations


def _audit_evidence_violations(frontmatter: dict[str, Any]) -> list[CritiqueLintViolation]:
    return [
        CritiqueLintViolation(
            severity="blocker",
            category=violation.category,
            message=violation.message,
        )
        for violation in critique_evidence_violations(frontmatter)
    ]


def _visual_clash_candidate_ids(report_path: Path) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not report_path.is_file():
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message="missing build/visual_clash.json for visual_clash_ref validation",
            )
        ]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message=f"malformed build/visual_clash.json: {exc}",
            )
        ]
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message="build/visual_clash.json candidates must be a list",
            )
        ]
    ids: list[str] = []
    violations: list[CritiqueLintViolation] = []
    seen: set[str] = set()
    for index, raw_candidate in enumerate(candidates):
        if not isinstance(raw_candidate, dict):
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accounting",
                    message=f"build/visual_clash.json candidates[{index}] must be a mapping",
                )
            )
            continue
        candidate_id = raw_candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accounting",
                    message=f"build/visual_clash.json candidates[{index}].id is required",
                )
            )
            continue
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accounting",
                    message=f"duplicate visual clash candidate id: {candidate_id}",
                )
            )
            continue
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, violations


def _micro_defect_visual_clash_refs(frontmatter: dict[str, Any]) -> list[str]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    refs: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        value = raw_item.get("visual_clash_ref")
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    return refs


def _visual_clash_accept_simplification_violations(
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    violations: list[CritiqueLintViolation] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        visual_clash_ref = raw_item.get("visual_clash_ref")
        if (
            raw_item.get("status") != "accept_simplification"
            or not isinstance(visual_clash_ref, str)
            or not visual_clash_ref.strip()
        ):
            continue
        defect_id = raw_item.get("id")
        if frontmatter.get("schema") in STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS:
            reason = raw_item.get("accept_simplification_reason")
            rationale = raw_item.get("accept_simplification_rationale")
            if reason not in MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS:
                violations.append(
                    CritiqueLintViolation(
                        severity="blocker",
                        category="visual_clash_accept_simplification",
                        message=(
                            "visual-clash-linked accept_simplification requires "
                            "accept_simplification_reason with a supported enum value: "
                            f"{visual_clash_ref.strip()} ({defect_id})"
                        ),
                    )
                )
                continue
            if not isinstance(rationale, str) or not rationale.strip():
                violations.append(
                    CritiqueLintViolation(
                        severity="blocker",
                        category="visual_clash_accept_simplification",
                        message=(
                            "visual-clash-linked accept_simplification requires "
                            "accept_simplification_rationale: "
                            f"{visual_clash_ref.strip()} ({defect_id})"
                        ),
                    )
                )
            continue
        observation = raw_item.get("observation")
        if not isinstance(observation, str):
            observation = ""
        normalized_observation = " ".join(observation.split())
        rationale = normalized_observation.lower()
        has_concrete_length = (
            len(normalized_observation) >= _VISUAL_CLASH_ACCEPT_MIN_OBSERVATION_CHARS
        )
        names_candidate = visual_clash_ref.strip() in normalized_observation
        gives_non_defect_reason = any(
            marker in rationale for marker in _VISUAL_CLASH_ACCEPT_RATIONALE_MARKERS
        )
        if has_concrete_length and names_candidate and gives_non_defect_reason:
            continue
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accept_simplification",
                message=(
                    "visual-clash-linked accept_simplification requires a concrete "
                    "observation naming the candidate id and explaining why it is "
                    f"not a defect: {visual_clash_ref.strip()} ({defect_id})"
                ),
            )
        )
    return violations


def _visual_clash_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in VISUAL_CLASH_ACCOUNTING_SCHEMAS:
        return []
    candidate_ids, violations = _visual_clash_candidate_ids(
        example_dir / "build" / "visual_clash.json"
    )
    if violations or not candidate_ids:
        return violations
    refs = _micro_defect_visual_clash_refs(frontmatter)
    accounted = set(refs)
    duplicate_refs = sorted({ref for ref in refs if refs.count(ref) > 1})
    if duplicate_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message=f"duplicate visual_clash_ref entries: {', '.join(duplicate_refs)}",
            )
        ]
    candidate_id_set = set(candidate_ids)
    unknown_refs = sorted(ref for ref in accounted if ref not in candidate_id_set)
    if unknown_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message=f"unknown visual_clash_ref entries: {', '.join(unknown_refs)}",
            )
        ]
    missing = [candidate_id for candidate_id in candidate_ids if candidate_id not in accounted]
    if not missing:
        return _visual_clash_accept_simplification_violations(frontmatter)
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="visual_clash_accounting",
            message=(
                "visual_clash.json candidates must be referenced by "
                f"micro_defects[].visual_clash_ref; missing: {', '.join(missing)}"
            ),
        )
    ]


def _micro_defects_by_visual_clash_ref(frontmatter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        visual_clash_ref = raw_item.get("visual_clash_ref")
        if isinstance(visual_clash_ref, str) and visual_clash_ref.strip():
            result[visual_clash_ref.strip()] = raw_item
    return result


def _historical_visual_clash_regression_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in VISUAL_CLASH_ACCOUNTING_SCHEMAS:
        return []
    report_path = example_dir / "build" / "visual_clash.json"
    if not report_path.is_file():
        return []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(report, dict):
        return []
    fixture = report.get("fixture")
    if (
        example_dir.name != _HISTORICAL_VISUAL_CLASH_FIXTURE
        and fixture != _HISTORICAL_VISUAL_CLASH_FIXTURE
    ):
        return []
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return []
    defects_by_ref = _micro_defects_by_visual_clash_ref(frontmatter)
    violations: list[CritiqueLintViolation] = []
    for raw_candidate in candidates:
        if not isinstance(raw_candidate, dict):
            continue
        candidate_id = raw_candidate.get("id")
        text = raw_candidate.get("text")
        if not isinstance(candidate_id, str) or not isinstance(text, str):
            continue
        expected_kind = _HISTORICAL_VISUAL_CLASH_EXPECTED_KINDS.get(
            (candidate_id.strip(), text.strip())
        )
        if expected_kind is None:
            continue
        defect = defects_by_ref.get(candidate_id.strip())
        if defect is None:
            continue
        if defect.get("kind") == expected_kind:
            continue
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="historical_visual_clash_regression",
                message=(
                    f"{_HISTORICAL_VISUAL_CLASH_FIXTURE} candidate {candidate_id.strip()} "
                    f"({text.strip()}) must use micro_defects[].kind={expected_kind}"
                ),
            )
        )
    return violations


def _crop_manifest_required_ids(
    example_dir: Path,
    manifest_path: Path,
) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not manifest_path.is_file():
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message="missing build/audit_crops/manifest.json for crop_audit_log validation",
            )
        ]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"malformed build/audit_crops/manifest.json: {exc}",
            )
        ]
    required = manifest.get("required_crop_ids")
    if not isinstance(required, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message="build/audit_crops/manifest.json required_crop_ids must be a list",
            )
        ]
    ids: list[str] = []
    for index, crop_id in enumerate(required):
        if not isinstance(crop_id, str) or not crop_id.strip():
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=(
                        "build/audit_crops/manifest.json "
                        f"required_crop_ids[{index}] must be a non-empty string"
                    ),
                )
            ]
        ids.append(crop_id.strip())
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message="build/audit_crops/manifest.json crops must be a list",
            )
        ]
    crop_by_id = {
        crop.get("id").strip(): crop
        for crop in crops
        if isinstance(crop, dict) and isinstance(crop.get("id"), str) and crop.get("id").strip()
    }
    for crop_id in ids:
        crop = crop_by_id.get(crop_id)
        if crop is None:
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"required crop id missing from manifest crops: {crop_id}",
                )
            ]
        expected_hash = crop.get("sha256")
        if (
            not isinstance(expected_hash, str)
            or not expected_hash.startswith("sha256:")
            or len(expected_hash) != len("sha256:") + 64
        ):
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"manifest crop {crop_id} must include sha256:<64 hex chars>",
                )
            ]
        hash_suffix = expected_hash.removeprefix("sha256:")
        if hash_suffix.lower() != hash_suffix or any(
            char not in "0123456789abcdef" for char in hash_suffix
        ):
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"manifest crop {crop_id} must use lowercase sha256 hex",
                )
            ]
        crop_path = crop.get("path")
        relative_crop_path = Path(crop_path) if isinstance(crop_path, str) else None
        if (
            relative_crop_path is None
            or relative_crop_path.is_absolute()
            or ".." in relative_crop_path.parts
            or relative_crop_path.parts[:2] != ("build", "audit_crops")
            or relative_crop_path.suffix != ".png"
        ):
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"manifest crop {crop_id} path must point to build/audit_crops/*.png",
                )
            ]
        absolute_crop_path = example_dir / relative_crop_path
        if not absolute_crop_path.is_file():
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"missing crop file for manifest crop {crop_id}: {crop_path}",
                )
            ]
        actual_hash = file_sha256(absolute_crop_path)
        if actual_hash != expected_hash:
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"hash mismatch for manifest crop {crop_id}: {crop_path}",
                )
            ]
    return ids, []


def _crop_audit_log_items(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = frontmatter.get("crop_audit_log")
    if not isinstance(raw_items, list):
        return []
    return [item for item in raw_items if isinstance(item, dict)]


def _crop_audit_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in CROP_AUDIT_ACCOUNTING_SCHEMAS:
        return []
    required_ids, violations = _crop_manifest_required_ids(
        example_dir,
        example_dir / "build" / "audit_crops" / "manifest.json"
    )
    if violations or not required_ids:
        return violations

    items = _crop_audit_log_items(frontmatter)
    crop_ids = [
        item["crop_id"].strip()
        for item in items
        if isinstance(item.get("crop_id"), str) and item["crop_id"].strip()
    ]
    duplicate_ids = sorted({crop_id for crop_id in crop_ids if crop_ids.count(crop_id) > 1})
    if duplicate_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"duplicate crop_audit_log crop_id entries: {', '.join(duplicate_ids)}",
            )
        ]
    required_set = set(required_ids)
    unknown_ids = sorted(crop_id for crop_id in crop_ids if crop_id not in required_set)
    if unknown_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"unknown crop_audit_log crop_id entries: {', '.join(unknown_ids)}",
            )
        ]
    missing = [crop_id for crop_id in required_ids if crop_id not in crop_ids]
    if missing:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"missing required crop_audit_log entries: {', '.join(missing)}",
            )
        ]

    micro_defect_ids = {
        item.get("id")
        for item in frontmatter.get("micro_defects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    unlinked_defect_crops = [
        str(item.get("crop_id"))
        for item in items
        if item.get("verdict") == "defect"
        and item.get("linked_micro_defect_id") not in micro_defect_ids
    ]
    if unlinked_defect_crops:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=(
                    "defect crop_audit_log entries must link to micro_defects[].id: "
                    + ", ".join(unlinked_defect_crops)
                ),
            )
        ]
    return []


def lint_critique(example_dir: Path) -> list[CritiqueLintViolation]:
    critique_path = example_dir / "critique.md"
    try:
        frontmatter = load_critique_frontmatter(critique_path)
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_frontmatter",
                message=str(exc),
            )
        ]

    try:
        violations = _duplicate_finding_id_violations(frontmatter)
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_contract",
                message=str(exc),
            )
        ]
    if violations:
        return violations

    if frontmatter.get("schema") in STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS:
        violations.extend(_visual_clash_accept_simplification_violations(frontmatter))
    if violations:
        return violations

    try:
        build_adjudication_scaffold(example_dir)
    except CritiqueAdjudicationError as exc:
        evidence_violations = _audit_evidence_violations(frontmatter)
        if evidence_violations and "print-scale audit evidence" in str(exc):
            violations.extend(evidence_violations)
        else:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="critique_contract",
                    message=str(exc),
                )
            )
    if violations:
        return violations
    violations.extend(_audit_evidence_violations(frontmatter))
    violations.extend(_visual_clash_accounting_violations(example_dir, frontmatter))
    violations.extend(_historical_visual_clash_regression_violations(example_dir, frontmatter))
    violations.extend(_crop_audit_accounting_violations(example_dir, frontmatter))
    return violations


def _resolve_example_dir(value: str, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "examples":
        return repo_root / path
    if len(path.parts) == 1:
        return repo_root / "examples" / value
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", help="fixture name, examples/<name>, or path")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    example_dir = _resolve_example_dir(args.example, args.repo_root)
    violations = lint_critique(example_dir)
    if not violations:
        print(f"OK: critique lint passed for {example_dir.name}")
        return 0
    for violation in violations:
        print(f"{violation.severity.upper()}: {violation.category}: {violation.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
