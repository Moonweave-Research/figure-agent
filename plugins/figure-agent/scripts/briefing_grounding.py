from __future__ import annotations

from pathlib import Path
from typing import Final

from inputs import parse_briefing

AUDIT_SIGNAL_RELATIVE_PATHS: Final = (
    Path("build") / "visual_clash.json",
    Path("build") / "text_boundary_clash.json",
    Path("build") / "label_path_proximity.json",
    Path("build") / "undeclared_geometry.json",
    Path("build") / "audit_crops" / "manifest.json",
)
RULE_SECTION_NUMBERS: Final = (3, 6, 7)
RULE_SECTION_TITLES: Final = (
    "correctness",
    "constraints",
    "physics invariants",
    "semantic constraints",
    "scope",
    "must",
    "must avoid",
)
INTENT_SECTION_TITLES: Final = (
    "claim to test",
    "topic",
    "figure identity",
    "purpose",
)
_RULE_TITLE_MARKERS: Final = (
    "correct",
    "invariant",
    "physics",
    "rule",
    "semantic",
    "constraint",
)
_RULE_BODY_MARKERS: Final = (
    "must",
    "must not",
    "do not",
    "wrong",
    "never",
    "not ",
    "required",
)
_MIN_INTENT_CHARS: Final = 40


def _has_audit_signal(example_dir: Path) -> bool:
    return any(
        (example_dir / relative_path).is_file()
        for relative_path in AUDIT_SIGNAL_RELATIVE_PATHS
    )


def _has_rule_marker(title: str, body: str) -> bool:
    title_text = title.lower()
    body_text = body.lower()
    return any(marker in title_text for marker in _RULE_TITLE_MARKERS) or any(
        marker in body_text for marker in _RULE_BODY_MARKERS
    )


def _has_rule_list_item(body: str) -> bool:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            return True
        first_token = stripped.split(maxsplit=1)[0] if stripped else ""
        if first_token[:-1].isdigit() and first_token.endswith((".", ")")):
            return True
    return False


def explicit_briefing_rule_text(sections: dict[int | str, tuple[str, str]]) -> str:
    blocks: list[str] = []
    candidates: list[tuple[str, tuple[str, str]]] = [
        (f"§{section_number}", sections.get(section_number, ("", "")))
        for section_number in RULE_SECTION_NUMBERS
    ]
    candidates.extend(
        (title, sections.get(title, ("", ""))) for title in RULE_SECTION_TITLES
    )
    seen_titles: set[str] = set()
    for section_label, (title, body) in candidates:
        rule_body = body.strip()
        if rule_body and _has_rule_marker(title, rule_body) and _has_rule_list_item(rule_body):
            normalized_title = title.casefold()
            if normalized_title in seen_titles:
                continue
            seen_titles.add(normalized_title)
            blocks.append(f"### Briefing {section_label}: {title}\n{rule_body}")
    return "\n\n".join(blocks)


def has_reference_free_grounding_context(example_dir: Path) -> bool:
    briefing_path = example_dir / "briefing.md"
    if not briefing_path.is_file() or not _has_audit_signal(example_dir):
        return False
    sections = parse_briefing(briefing_path.read_text(encoding="utf-8"))
    intent = ""
    for title in INTENT_SECTION_TITLES:
        intent = sections.get(title, ("", ""))[1].strip()
        if intent:
            break
    if not intent:
        intent = sections.get(1, ("", ""))[1].strip()
    return len(intent) >= _MIN_INTENT_CHARS and bool(explicit_briefing_rule_text(sections))
