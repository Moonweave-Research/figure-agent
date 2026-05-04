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


def test_public_docs_do_not_route_to_deleted_legacy_commands() -> None:
    docs_by_path = {
        "README.md": (REPO_ROOT / "README.md").read_text(),
        "skills/figure-agent/SKILL.md": (
            REPO_ROOT / "skills" / "figure-agent" / "SKILL.md"
        ).read_text(),
        "commands/fig_new.md": (REPO_ROOT / "commands" / "fig_new.md").read_text(),
    }
    forbidden_strings = [
        "/fig_prompt",
        "/fig_preview_select",
        "prompt/image-gen orchestration remains available",
        "Prompt/image-gen orchestration from v0.1 remains available",
        "The earlier prompt/image-gen orchestration helpers remain available",
        "v0.1 line is active",
        "workflow remains available",
    ]

    for doc_path, doc_text in docs_by_path.items():
        for forbidden in forbidden_strings:
            assert forbidden not in doc_text, f"{doc_path} still contains {forbidden!r}"


def test_package_descriptions_name_quality_kernel_direction() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    marketplace = json.loads(
        (REPO_ROOT.parents[1] / ".claude-plugin" / "marketplace.json").read_text()
    )

    texts = [
        plugin["description"],
        pyproject["project"]["description"],
        marketplace["description"],
        marketplace["plugins"][0]["description"],
    ]

    for text in texts:
        assert "quality" in text.lower()
        assert "prompt intent control" not in text
