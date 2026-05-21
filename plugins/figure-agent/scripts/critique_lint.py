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

REPO_ROOT = Path(__file__).resolve().parent.parent
VISUAL_CLASH_ACCOUNTING_SCHEMA = "figure-agent.critique.v1.7"


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
        return [], []
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


def _visual_clash_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") != VISUAL_CLASH_ACCOUNTING_SCHEMA:
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
        return []
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
