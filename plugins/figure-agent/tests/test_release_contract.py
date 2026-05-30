"""Release metadata contract checks."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_ROOT))

from plugin_package_audit import find_packaging_junk, remove_paths  # noqa: E402

EXPECTED_RELEASE_VERSION = "0.9.0"
EXPECTED_RELEASE_DATE = "2026-05-30"


def test_plugin_manifest_version_matches_pyproject() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    assert plugin["version"] == pyproject["project"]["version"]


def test_release_metadata_matches_current_version() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    uv_lock = (REPO_ROOT / "uv.lock").read_text()

    assert plugin["version"] == EXPECTED_RELEASE_VERSION
    assert pyproject["project"]["version"] == EXPECTED_RELEASE_VERSION
    assert (
        f'name = "figure-agent"\nversion = "{EXPECTED_RELEASE_VERSION}"'
        in uv_lock
    )


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


def test_readme_documents_plugin_package_audit() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "scripts/plugin_package_audit.py" in readme
    assert "--max-mib" in readme
    assert "~/.claude/plugins/cache/" in readme


def test_readme_current_state_matches_plugin_version() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())

    assert f"Current state (v{plugin['version']})" in readme
    assert "SVG polish" in readme
    assert "What's experimental / proposed (not built)" not in readme
    experimental_section = readme.partition("What remains experimental / proposed")[2]
    assert experimental_section
    assert "docs/svg-polish-pipeline.md" not in experimental_section


def test_current_readme_documents_release_boundaries() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert f"Current state (v{EXPECTED_RELEASE_VERSION})" in readme
    assert "docs/v0.9-operator-playbook.md" in readme
    for required in [
        "single next-action summary",
        "Bounded safe runner",
        "Operator queue",
        "multi-fixture",
        "journal style-pack catalog",
        "external vision review",
        "not a hidden auto-designer",
        "cannot certify Nature/Science acceptance",
    ]:
        assert required in readme

    boundary_section = readme.partition("## Current state")[2]
    assert "Automatic" in boundary_section
    assert "Semi-automatic" in boundary_section
    assert "Opt-in" in boundary_section
    assert "Manual" in boundary_section


def test_v0_9_operator_playbook_documents_command_sequence_and_boundaries() -> None:
    playbook = (REPO_ROOT / "docs" / "v0.9-operator-playbook.md").read_text()

    for required in [
        "Single fixture",
        "Multi-Fixture Queue",
        "Host Critique Refresh",
        "Closeout After Patch Or Export",
        "Release And Golden Gate",
        "What v0.9 Still Does Not Do",
        "The command plan is the authority for batch execution",
        "It does not automatically produce top-tier art direction",
        "It does not mutate accepted/golden/publication state",
    ]:
        assert required in playbook


def test_current_changelog_covers_operator_release() -> None:
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    top_entry = changelog.partition("## [0.8.2]")[0]

    assert f"## [{EXPECTED_RELEASE_VERSION}] - {EXPECTED_RELEASE_DATE}" in top_entry
    for required in [
        "Issue 70",
        "Issue 71",
        "Issue 88",
        "Issue 89",
        "guided autonomy",
        "multi-fixture queue",
        "operator handoff",
        "not a hidden auto-designer",
    ]:
        assert required in top_entry


def test_closeout_status_matches_current_release_truth() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    closeout = (
        REPO_ROOT
        / "docs"
        / "milestones"
        / "2026-05-21-plugin-development-closeout-status.md"
    ).read_text()
    issue_48 = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-05-26-issue-48-svg-polish-promotion-readiness.md"
    ).read_text()

    assert f"current release-candidate truth through v{plugin['version']}" in closeout
    assert (
        f"current release-candidate truth through v{EXPECTED_RELEASE_VERSION} / Issue 89"
        in closeout
    )
    assert "after Issue 33 / PR #47" not in closeout
    assert "start with Issue 34" not in closeout
    assert "Issue 48" in closeout
    assert "implemented on main" in issue_48
    assert "implemented on branch" not in issue_48


def test_v0_9_issue_statuses_are_mainline_ready() -> None:
    issue_files = {
        "Issue 57": "2026-05-27-issue-57-real-fixture-audit-adoption.md",
        "Issue 58": "2026-05-27-issue-58-single-next-action-ux.md",
        "Issue 59": "2026-05-27-issue-59-svg-polish-promotion-dogfood.md",
        "Issue 60": "2026-05-27-issue-60-style-pack-catalog.md",
        "Issue 61": "2026-05-27-issue-61-external-second-opinion-vision.md",
        "Issue 62": "2026-05-27-issue-62-v0-8-release-hardening.md",
        "Issue 64": "2026-05-28-issue-64-loop-summary-and-export-closeout-ux.md",
        "Issue 70": "2026-05-29-issue-70-operator-grade-guided-autonomy.md",
        "Issue 88": "2026-05-30-issue-88-queue-operator-ergonomics-and-closeout.md",
        "Issue 89": "2026-05-30-issue-89-v0-9-operator-grade-release-candidate.md",
    }

    for issue_name, file_name in issue_files.items():
        text = (REPO_ROOT / "docs" / "superpowers" / "issues" / file_name).read_text()
        assert "implemented in branch" not in text, issue_name
        assert "Status: proposed" not in text, issue_name
        assert "Status: in progress" not in text, issue_name
        assert "Status: completed" in text or "Status: implemented" in text, issue_name


def test_readme_documents_status_and_driver_first_workflow() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "/fig_drive" in readme
    assert "/fig_status fig3_trap_concept" in readme
    assert "canonical first check" in readme
    assert "Export, release, or\npolish only when" in readme


def test_active_docs_describe_svg_polish_handoff_as_shipped() -> None:
    overview = (REPO_ROOT / "docs" / "architecture-overview.md").read_text()

    assert "scaffolding UX in progress" not in overview
    assert "svg_polish_recipe.py" in overview
    assert "svg_polish_executor.py" in overview
    assert "svg_polish_delta.py" in overview
    assert "/fig_drive --mode polish" in overview


def test_active_architecture_overview_uses_current_critique_loop_contract() -> None:
    overview = (REPO_ROOT / "docs" / "architecture-overview.md").read_text()

    assert "report-only for v0.2" not in overview
    assert "Report-only for v0.2" not in overview
    assert "accuracy ≥ 80%" not in overview
    assert "verify-only `/fig_loop`" in overview
    assert "`critique_adjudication.yaml`" in overview
    assert "`/fig_drive`" in overview


def test_plugin_package_audit_detects_and_removes_generated_junk(tmp_path: Path) -> None:
    plugin_root = tmp_path / "figure-agent"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / "commands").mkdir()
    (plugin_root / "scripts").mkdir()
    (plugin_root / "examples" / "demo" / "build").mkdir(parents=True)
    (plugin_root / "examples" / "demo" / "exports").mkdir(parents=True)
    (plugin_root / ".venv" / "bin").mkdir(parents=True)
    (plugin_root / ".pytest_cache").mkdir()
    (plugin_root / "dist").mkdir()
    (plugin_root / "figure_agent.egg-info").mkdir()
    (plugin_root / "commands" / "fig_status.md").write_text("status", encoding="utf-8")
    (plugin_root / "scripts" / "status.py").write_text("print('ok')", encoding="utf-8")
    (plugin_root / "examples" / "demo" / "build" / "demo.pdf").write_bytes(b"%PDF")

    junk = find_packaging_junk(plugin_root)

    assert plugin_root / ".venv" in junk
    assert plugin_root / ".pytest_cache" in junk
    assert plugin_root / "dist" in junk
    assert plugin_root / "figure_agent.egg-info" in junk
    assert plugin_root / "examples" / "demo" / "build" in junk
    assert plugin_root / "examples" / "demo" / "exports" in junk
    assert plugin_root / "commands" not in junk
    assert plugin_root / "scripts" not in junk

    remove_paths(junk)

    assert not (plugin_root / ".venv").exists()
    assert not (plugin_root / "examples" / "demo" / "build").exists()
    assert (plugin_root / "commands" / "fig_status.md").is_file()
    assert (plugin_root / "scripts" / "status.py").is_file()


def test_plugin_package_audit_removes_empty_wrapper_dirs(tmp_path: Path) -> None:
    plugin_root = tmp_path / "figure-agent"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / "commands").mkdir()
    (plugin_root / "plugins").mkdir()
    (plugin_root / "commands" / "fig_status.md").write_text("status", encoding="utf-8")

    junk = find_packaging_junk(plugin_root)

    assert plugin_root / "plugins" in junk

    remove_paths(junk)

    assert not (plugin_root / "plugins").exists()
    assert (plugin_root / "commands" / "fig_status.md").is_file()


def test_plugin_package_audit_removes_plugin_root_worktree_metadata(tmp_path: Path) -> None:
    plugin_root = tmp_path / "figure-agent"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / "commands").mkdir()
    (plugin_root / ".ralph").mkdir()
    (plugin_root / ".claude").mkdir()
    (plugin_root / "plugins" / "figure-agent" / ".ralph").mkdir(parents=True)
    (plugin_root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (plugin_root / "commands" / "fig_status.md").write_text("status", encoding="utf-8")

    junk = find_packaging_junk(plugin_root)

    assert plugin_root / ".ralph" in junk
    assert plugin_root / ".claude" in junk
    assert plugin_root / "plugins" in junk

    remove_paths(junk)

    assert not (plugin_root / ".ralph").exists()
    assert not (plugin_root / ".claude").exists()
    assert not (plugin_root / "plugins").exists()
    assert (plugin_root / "commands" / "fig_status.md").is_file()
