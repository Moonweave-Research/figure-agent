"""Lint critique.md without writing adjudication state."""

from __future__ import annotations

import argparse
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

REPO_ROOT = Path(__file__).resolve().parent.parent
PRINT_SCALE_EVIDENCE_TOKENS = (
    "print-scale",
    "print_scale",
    "print_178mm",
    "print_thumbnail",
)


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


def _text_mentions_print_scale_evidence(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in PRINT_SCALE_EVIDENCE_TOKENS)
    if isinstance(value, list):
        return any(_text_mentions_print_scale_evidence(item) for item in value)
    if isinstance(value, dict):
        return any(_text_mentions_print_scale_evidence(item) for item in value.values())
    return False


def _audit_evidence_violations(frontmatter: dict[str, Any]) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") != "figure-agent.critique.v1.4":
        return []
    quality_axes = frontmatter.get("quality_axes")
    if not isinstance(quality_axes, dict):
        return []
    violations: list[CritiqueLintViolation] = []
    for axis_name in ("journal_polish", "publication_readiness"):
        axis = quality_axes.get(axis_name)
        if not isinstance(axis, dict) or axis.get("verdict") != "pass":
            continue
        if _text_mentions_print_scale_evidence(axis.get("evidence")):
            continue
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="audit_evidence",
                message=(
                    f"{axis_name} verdict is pass but evidence does not name "
                    "print-scale audit evidence"
                ),
            )
        )
    return violations


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
