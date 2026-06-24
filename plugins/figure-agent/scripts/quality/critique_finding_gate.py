"""Human-gated critique finding eligibility for bounded candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from critique_adjudication import adjudication_is_stale, load_adjudication
from critique_contract import CritiqueContractError, critique_finding_id, critique_findings
from quality_manifest import yaml_frontmatter

SAFE_CATEGORY_CLASSES = {
    "hierarchy": "text_overlap",
    "label_placement": "text_overlap",
    "whitespace": "whitespace_balance",
}


def two_int_tex_lines(finding: dict[str, Any]) -> tuple[int, int] | None:
    tex_lines = finding.get("tex_lines")
    if (
        not isinstance(tex_lines, list)
        or len(tex_lines) != 2
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in tex_lines)
    ):
        return None
    start, end = tex_lines
    if start < 1 or end < start:
        return None
    return start, end


def bounded_defect_class(finding: dict[str, Any]) -> str | None:
    category = str(finding.get("category") or "").strip().lower()
    return SAFE_CATEGORY_CLASSES.get(category)


def kept_bounded_findings(example_dir: Path) -> dict[str, dict[str, Any]]:
    critique_path = example_dir / "critique.md"
    adjudication_path = example_dir / "critique_adjudication.yaml"
    if not critique_path.is_file() or not adjudication_path.is_file():
        return {}
    try:
        if adjudication_is_stale(adjudication_path, critique_path):
            return {}
        frontmatter = yaml_frontmatter(critique_path)
        adjudication = load_adjudication(adjudication_path)
    except CritiqueContractError:
        return {}

    keep_decisions = {
        str(item.get("finding_id") or "").strip(): item
        for item in adjudication.get("decisions", [])
        if isinstance(item, dict) and item.get("decision") == "keep"
    }
    if not keep_decisions:
        return {}

    kept: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(critique_findings(frontmatter)):
        try:
            finding_id = critique_finding_id(finding, f"critique finding {index}")
        except CritiqueContractError:
            continue
        decision = keep_decisions.get(finding_id)
        tex_lines = two_int_tex_lines(finding)
        defect_class = bounded_defect_class(finding)
        if decision is None or tex_lines is None or defect_class is None:
            continue
        kept[finding_id] = {
            "decision": decision,
            "defect_class": defect_class,
            "finding": finding,
            "tex_lines": tex_lines,
        }
    return kept
