from __future__ import annotations

import sys
from pathlib import Path

import yaml
from document_status import (
    GOVERNED_DOCUMENT_SUFFIXES,
    classify_document,
    load_policy,
    shippable_document_paths,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "checks"))


def test_document_policy_classifies_every_governed_document() -> None:
    policy = load_policy()
    documents = [
        path
        for path in (PLUGIN_ROOT / "docs").rglob("*")
        if path.is_file() and path.suffix.lower() in GOVERNED_DOCUMENT_SUFFIXES
    ]

    statuses = [
        classify_document(path.relative_to(PLUGIN_ROOT), policy=policy)
        for path in documents
    ]

    assert statuses
    assert not [status.path for status in statuses if status.classification == "unclassified"]
    assert [status.path for status in statuses if status.classification == "authority"] == [
        "docs/figure-agent.md"
    ]


def test_document_class_semantics_fail_closed() -> None:
    authority = classify_document("docs/figure-agent.md")
    project_state = classify_document("docs/current-sulfur-paper-figure-state.md")
    historical = classify_document("docs/architecture-v0.14-convergence-contract.md")
    unknown = classify_document("docs/a-future-unregistered-plan.md")
    comparison = classify_document(
        "docs/style-benchmark-comparisons/2026-07-01-wave-f/"
        "fig3_trapping_concept.json"
    )
    experience = classify_document(
        "docs/experience-log/fig1_overview_v5f_v013_dogfood_001_vault.jsonl"
    )

    assert (authority.active, authority.ship, authority.agent_executable) == (
        True,
        True,
        True,
    )
    assert (project_state.active, project_state.ship, project_state.agent_executable) == (
        True,
        False,
        True,
    )
    assert (historical.active, historical.ship, historical.agent_executable) == (
        False,
        False,
        False,
    )
    assert (unknown.active, unknown.ship, unknown.agent_executable) == (
        False,
        False,
        False,
    )
    assert comparison.classification == "evidence"
    assert not comparison.ship and not comparison.agent_executable
    assert experience.classification == "evidence"
    assert not experience.ship and not experience.agent_executable


def test_only_approved_active_docs_are_shippable() -> None:
    shippable = {
        path.relative_to(PLUGIN_ROOT).as_posix()
        for path in shippable_document_paths()
    }

    assert "docs/figure-agent.md" in shippable
    assert "docs/architecture-overview.md" in shippable
    assert "docs/document-status.yaml" in shippable
    assert "docs/public-command-route.yaml" in shippable
    assert "docs/current-sulfur-paper-figure-state.md" not in shippable
    assert "docs/product-spec.md" not in shippable
    assert "docs/architecture-v0.14-convergence-contract.md" not in shippable
    assert not any(path.endswith((".json", ".jsonl")) for path in shippable)


def test_json_and_jsonl_are_governed_document_extensions() -> None:
    assert {".json", ".jsonl"} <= GOVERNED_DOCUMENT_SUFFIXES


def test_imperative_historical_docs_surface_status_before_instructions() -> None:
    paths = (
        "docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md",
        "docs/superpowers/specs/2026-07-02-total-review-execution-plan.md",
    )

    for relative in paths:
        text = (PLUGIN_ROOT / relative).read_text(encoding="utf-8")
        first_nonempty = next(line for line in text.splitlines() if line.strip())
        assert first_nonempty.startswith(
            "> **Document status: Historical evidence — non-authoritative"
        )
        assert text.count("**Document status:") == 1


def test_policy_declares_complete_boolean_semantics() -> None:
    payload = yaml.safe_load(
        (PLUGIN_ROOT / "docs" / "document-status.yaml").read_text(encoding="utf-8")
    )
    for name in ("authority", "reference", "project_state", "evidence", "historical"):
        semantics = payload["classes"][name]
        assert set(semantics) == {"active", "ship", "agent_executable"}
        assert all(isinstance(value, bool) for value in semantics.values())


def test_every_packaged_root_file_is_classified() -> None:
    import package_cowork_plugin
    from check_document_status import PACKAGED_ROOT_FILES, check

    shipped = {
        path.name
        for path in package_cowork_plugin._included_files()
        if path.parent == PLUGIN_ROOT
    }

    assert shipped == set(PACKAGED_ROOT_FILES), (
        "packaging ships a root file the document policy does not classify"
    )
    result = check()
    assert result["unclassified"] == []
    assert result["passed"] is True
