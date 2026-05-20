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
    _critique_frontmatter,
    _finding_id,
    _findings_from_critique,
    build_adjudication_scaffold,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CritiqueLintViolation:
    severity: str
    category: str
    message: str


def _duplicate_finding_id_violations(frontmatter: dict[str, Any]) -> list[CritiqueLintViolation]:
    seen: set[str] = set()
    violations: list[CritiqueLintViolation] = []
    for index, finding in enumerate(_findings_from_critique(frontmatter)):
        finding_id = _finding_id(finding, f"critique finding {index}")
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


def lint_critique(example_dir: Path) -> list[CritiqueLintViolation]:
    critique_path = example_dir / "critique.md"
    try:
        frontmatter = _critique_frontmatter(critique_path)
    except CritiqueAdjudicationError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_frontmatter",
                message=str(exc),
            )
        ]

    violations = _duplicate_finding_id_violations(frontmatter)
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
