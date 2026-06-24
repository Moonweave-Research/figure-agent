"""Compile read-only human-perspective narrative context."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

SCHEMA: Final = "figure-agent.narrative-context.v1"
_TEXT_LIMIT: Final = 12000
_SOURCE_FILES: Final = {
    "spec": "spec.yaml",
    "briefing": "briefing.md",
    "design": "design.md",
    "authoring_plan": "authoring_plan.md",
    "authoring_contract": "authoring_contract.md",
    "panel_goals": "panel_goals.md",
}
_HUMAN_REVIEW_QUESTIONS: Final = [
    "What should a reader understand in the first three seconds?",
    "Which panel or element is the visual hero?",
    "Does the panel order match the paper's argument order?",
    "What would a human illustrator simplify before adding detail?",
    "Could a proposed visual edit change scientific meaning?",
]
_MUST_NOT_INFER: Final = [
    "Do not infer unstated physics, mechanisms, or quantitative claims.",
    "Do not treat aesthetic preference as acceptance evidence.",
    "Do not select or apply source patches from narrative context alone.",
]


def _read_optional_text(path: Path) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= _TEXT_LIMIT:
        return text
    return text[:_TEXT_LIMIT].rstrip() + "\n...[truncated]"


def _relative(base: Path, path: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _sources(example_dir: Path, workspace_root: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    for key, filename in _SOURCE_FILES.items():
        path = example_dir / filename
        sources[key] = _relative(workspace_root, path) if path.is_file() else ""
    return sources


def _first_takeaway_source(sources: dict[str, str]) -> str:
    for key in ("briefing", "panel_goals", "authoring_plan", "design"):
        source = sources.get(key, "")
        if source:
            return Path(source).name
    return "not_configured"


def _panel_story_inputs(spec: dict[str, Any]) -> list[dict[str, Any]]:
    panels = spec.get("panels")
    if not isinstance(panels, list):
        return []
    story_inputs: list[dict[str, Any]] = []
    for index, panel in enumerate(panels, start=1):
        if not isinstance(panel, dict):
            continue
        story_inputs.append(
            {
                "id": str(panel.get("id") or f"panel_{index}"),
                "caption": str(panel.get("caption") or ""),
                "semantic_claim_count": len(panel.get("semantic_claims") or []),
                "locked_invariant_count": len(panel.get("locked_invariants") or []),
            }
        )
    return story_inputs


def _available_notes(example_dir: Path) -> dict[str, str]:
    notes: dict[str, str] = {}
    for key in ("briefing", "panel_goals", "authoring_plan", "design"):
        filename = _SOURCE_FILES[key]
        text = _read_optional_text(example_dir / filename)
        if text:
            notes[key] = text
    return notes


def build_narrative_context(
    example_dir: Path,
    *,
    workspace_root: Path,
    spec: dict[str, Any],
) -> dict[str, Any]:
    sources = _sources(example_dir, workspace_root)
    return {
        "schema": SCHEMA,
        "read_only": True,
        "mode": "human_perspective_compiler",
        "sources": sources,
        "reader_contract": {
            "first_takeaway_source": _first_takeaway_source(sources),
            "panel_story_inputs": _panel_story_inputs(spec),
            "available_notes": _available_notes(example_dir),
            "paper_series_anchors": [],
            "must_not_infer": list(_MUST_NOT_INFER),
            "human_review_questions": list(_HUMAN_REVIEW_QUESTIONS),
        },
        "stop_boundaries": {
            "autonomous_patch_selection": False,
            "generation_executor": False,
            "model_calls": False,
            "prompt_loop": False,
            "rank_scoring": False,
            "source_mutation": False,
        },
    }
