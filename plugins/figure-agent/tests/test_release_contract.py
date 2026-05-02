"""Release metadata contract checks."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_plugin_manifest_version_matches_pyproject() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    assert plugin["version"] == pyproject["project"]["version"]


def test_active_docs_define_semantic_tikz_reference_workflow() -> None:
    docs_by_path = {
        "docs/architecture-overview.md": (
            REPO_ROOT / "docs" / "architecture-overview.md"
        ).read_text(),
        "README.md": (REPO_ROOT / "README.md").read_text(),
        "skills/figure-agent/SKILL.md": (
            REPO_ROOT / "skills" / "figure-agent" / "SKILL.md"
        ).read_text(),
    }
    contract_strings = [
        "reference PNG -> OCR + palette clusters + optional vtracer structural hints",
        "coordinate_hints.yaml -> semantic TikZ authoring",
        "SVG-to-TikZ path conversion is not the active workflow",
    ]

    for doc_path, doc_text in docs_by_path.items():
        for contract_string in contract_strings:
            assert contract_string in doc_text, f"{doc_path} missing: {contract_string}"


def test_authoring_prompt_forbids_path_dump_final_source() -> None:
    prompt = (REPO_ROOT / "prompts" / "llm_author_tikz.md").read_text()

    assert "Do not convert SVG paths into the final TikZ source" in prompt
    assert "Do not pass through SVG path output" in prompt
    assert "Do not emit raw traced path clouds" in prompt
    assert "Use coordinate_hints.yaml as placement evidence" in prompt
    assert "semantic TikZ macros and named drawing constructs" in prompt
    assert "{{structural_regions}}" in prompt
    assert "{{selection_notes}}" in prompt
    assert "precise placement guidelines" not in prompt
    assert "falls inside the stated bounding box" not in prompt


def test_authoring_prompt_requires_semantic_first_order() -> None:
    prompt = (REPO_ROOT / "prompts" / "llm_author_tikz.md").read_text()

    assert "Authoring order (semantic-first)" in prompt
    assert "Look at the reference PNG first" in prompt
    assert "Do not start from coordinate_hints alone" in prompt
    assert "Use coordinate_hints.yaml only to refine placement" in prompt
    assert "recover the missing detail" in prompt
    assert (
        "Do not pass through SVG path output" in prompt
    )  # Maps to step 4; independent from forbids test


def test_fig_extract_documents_structural_hints_as_optional() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_extract.md").read_text()
    extractor = (REPO_ROOT / "scripts" / "reference_extract.py").read_text()

    assert "optional vtracer structural hints" in command_doc
    assert "structural hints are authoring evidence, not final source" in command_doc
    assert "OCR + palette clusters still remain useful" in command_doc
    assert "structural_regions:" in command_doc
    assert "status: ok                   # ok | unavailable | failed" in command_doc
    assert "`structural_regions.status: unavailable`" in command_doc
    assert "`structural_regions.status: failed`" in command_doc
    assert "optional vtracer structural hints" in extractor
    assert "authoring evidence, not final source" in extractor
    assert "OCR + palette clusters still remain useful" in extractor
    assert "The hints carry two structures" not in extractor
