"""Release metadata contract checks."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_ROOT))

from fig_driver import MODES as FIG_DRIVER_MODES  # noqa: E402
from plugin_install_freshness import SCHEMA as INSTALL_FRESHNESS_SCHEMA  # noqa: E402
from plugin_package_audit import find_packaging_junk, main, remove_paths  # noqa: E402

EXPECTED_RELEASE_VERSION = "0.9.2"
EXPECTED_RELEASE_DATE = "2026-06-02"


def _issue_suffix_value(suffix: str) -> int:
    value = 0
    for char in suffix:
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value


def _issue_suffix_from_value(value: int) -> str:
    suffix = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        suffix = chr(ord("A") + remainder) + suffix
    return suffix


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

    assert "scripts/plugin_install_freshness.py" in readme
    assert INSTALL_FRESHNESS_SCHEMA in readme
    assert "source_package_hygiene" in readme
    assert "source_git_hygiene" in readme
    assert "marketplace_source_hygiene" in readme
    assert "installed_example_source_hygiene" in readme
    assert "scripts/plugin_package_audit.py" in readme
    assert "--max-mib" in readme
    assert "--preserve-fixture-artifacts" in readme
    assert "~/.claude/plugins/cache/" in readme


def test_docs_explain_external_review_findings_are_human_gates() -> None:
    docs_by_path = {
        "README.md": (REPO_ROOT / "README.md").read_text(),
        "commands/fig_critique.md": (
            REPO_ROOT / "commands" / "fig_critique.md"
        ).read_text(),
    }

    for doc_path, text in docs_by_path.items():
        assert "external_vision_review.yaml" in text, doc_path
        assert "unresolved findings" in text, doc_path
        assert "human gate" in text, doc_path


def test_fig_queue_docs_cover_all_driver_modes() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_queue.md").read_text()

    assert "driver mode:" in command_doc
    for mode in FIG_DRIVER_MODES:
        assert f"`{mode}`" in command_doc, f"fig_queue docs omit driver mode {mode!r}"


def test_readme_current_state_matches_plugin_version() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())

    assert f"Current state (v{plugin['version']})" in readme
    assert "SVG polish" in readme
    assert "What's experimental / proposed (not built)" not in readme
    experimental_section = readme.partition("What remains experimental / proposed")[2]
    assert experimental_section
    assert "docs/svg-polish-pipeline.md" not in experimental_section


def test_issue_100_inventory_consistency_check_matches_plugin_version() -> None:
    inventory = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md"
    ).read_text()
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    consistency_check = inventory.partition("## Documentation Consistency Check")[2]
    normalized = " ".join(consistency_check.split())

    assert f"current plugin as v{plugin['version']}" in normalized


def test_current_readme_documents_release_boundaries() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert f"Current state (v{EXPECTED_RELEASE_VERSION})" in readme
    assert "docs/v0.9-operator-playbook.md" in readme
    for required in [
        "single next-action summary",
        "Bounded safe runner",
        "Loop-centered improvement orchestrator",
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
        "Loop-Centered Improvement",
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


def test_fig_queue_docs_describe_svg_blocking_sources_from_gate_and_readiness() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_queue.md").read_text()

    assert "svg_polish_gate.blocking_items" in command_doc
    assert "svg_polish_readiness.blocking_items" in command_doc
    summary_section = command_doc.partition("`summary` includes:")[2].partition(
        "`command_plan` includes:"
    )[0]
    assert "by_svg_polish_blocking_source" in summary_section
    assert "gate/readiness" in summary_section


def test_fig_queue_docs_describe_table_grouped_summary_counts() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_queue.md").read_text()

    assert "human-readable table" in command_doc
    assert "summary by_action=" in command_doc
    assert "summary by_svg_polish_next_action=" in command_doc
    assert "mirror the JSON `summary` object" in command_doc


def test_fig_queue_docs_exclude_complete_rows_from_blocking_source() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_queue.md").read_text()

    assert "mode-scoped `complete` rows use `null`" in command_doc
    assert "not counted as a blocker" in command_doc


def test_fig_queue_docs_separate_complete_rows_from_command_plan_blockers() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_queue.md").read_text()

    assert "`blocked_count` | number of rows blocked by" in command_doc
    assert "`complete_count`" in command_doc
    assert "`command_plan.complete`" in command_doc
    assert "non-executable but not blocked" in command_doc


def test_fig_queue_run_docs_describe_execute_dry_run_conflict() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_queue_run.md").read_text()

    assert "`--execute --dry-run` is rejected" in command_doc
    assert "ambiguous safety conflict" in command_doc


def test_readme_and_skill_route_journal_inspection_through_summary_script() -> None:
    docs_by_path = {
        "README.md": (REPO_ROOT / "README.md").read_text(),
        "skills/figure-agent/SKILL.md": (
            REPO_ROOT / "skills" / "figure-agent" / "SKILL.md"
        ).read_text(),
    }

    for doc_path, text in docs_by_path.items():
        assert "fig_run_journal.py" in text, doc_path
        assert "Do not replay commands" in text, doc_path


def test_current_changelog_covers_operator_release() -> None:
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    top_entry = changelog.partition("## [0.9.0]")[0]

    assert f"## [{EXPECTED_RELEASE_VERSION}] - {EXPECTED_RELEASE_DATE}" in top_entry
    for required in [
        "Issue 95",
        "/fig_improve",
        "loop-centered",
        "host critique",
        "optional-improvement",
        "Issues 97 and 98",
        "v1.17 grounded critique contract sync",
        "aesthetic_antipattern_audit",
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
        f"current release-candidate truth through v{EXPECTED_RELEASE_VERSION} / Issues 95-100"
        in closeout
    )
    assert "after Issue 33 / PR #47" not in closeout
    assert "start with Issue 34" not in closeout
    assert "Issue 48" in closeout
    assert "implemented on main" in issue_48
    assert "implemented on branch" not in issue_48


def test_issue_100_inventory_header_and_surface_counts_match_current_tree() -> None:
    inventory = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md"
    ).read_text()
    latest_issue = max(
        _issue_suffix_value(match.group(1))
        for match in re.finditer(r"Issue 100([A-Z]+)", inventory)
    )
    latest_issue_suffix = _issue_suffix_from_value(latest_issue)

    script_count = len(list((REPO_ROOT / "scripts").glob("*.py")))
    test_count = len(list((REPO_ROOT / "tests").glob("test_*.py")))
    command_doc_count = len(list((REPO_ROOT / "commands").glob("fig_*.md")))

    assert f"through Issue 100{latest_issue_suffix}" in inventory
    assert f"branch baseline: `main` after Issue 100{latest_issue_suffix}" in inventory
    assert (
        f"Current inventory is {script_count} scripts, {test_count} tests, "
        f"and {command_doc_count} command docs."
    ) in inventory


def test_issue_100_inventory_tracks_latest_issue_file_suffix() -> None:
    inventory = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md"
    ).read_text()
    issue_dir = REPO_ROOT / "docs" / "superpowers" / "issues"
    issue_values: list[int] = []
    for path in issue_dir.glob("*issue-100*.md"):
        title = path.read_text().splitlines()[0]
        combined_match = re.search(r"Issue 100([A-Z])/([A-Z])", title)
        if combined_match:
            issue_values.extend(
                _issue_suffix_value(suffix) for suffix in combined_match.groups()
            )
            continue
        if match := re.search(r"Issue 100([A-Z]+)", title):
            issue_values.append(_issue_suffix_value(match.group(1)))
    latest_issue_file = max(issue_values)
    latest_issue_suffix = _issue_suffix_from_value(latest_issue_file)

    assert f"through Issue 100{latest_issue_suffix}" in inventory
    assert f"branch baseline: `main` after Issue 100{latest_issue_suffix}" in inventory


def test_issue_100_inventory_completion_summary_tracks_latest_issue_file_suffix() -> None:
    inventory = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md"
    ).read_text()
    issue_dir = REPO_ROOT / "docs" / "superpowers" / "issues"
    issue_values: list[int] = []
    for path in issue_dir.glob("*issue-100*.md"):
        title = path.read_text().splitlines()[0]
        combined_match = re.search(r"Issue 100([A-Z])/([A-Z])", title)
        if combined_match:
            issue_values.extend(
                _issue_suffix_value(suffix) for suffix in combined_match.groups()
            )
            continue
        if match := re.search(r"Issue 100([A-Z]+)", title):
            issue_values.append(_issue_suffix_value(match.group(1)))
    latest_issue_suffix = _issue_suffix_from_value(max(issue_values))
    completion_summary = inventory.partition("## Recommended Execution Order")[2]

    assert f"**Issue 100{latest_issue_suffix} " in completion_summary


def test_issue_100_inventory_update_analysis_tracks_latest_issue_file_suffix() -> None:
    inventory = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md"
    ).read_text()
    issue_dir = REPO_ROOT / "docs" / "superpowers" / "issues"
    issue_values: list[int] = []
    for path in issue_dir.glob("*issue-100*.md"):
        title = path.read_text().splitlines()[0]
        combined_match = re.search(r"Issue 100([A-Z])/([A-Z])", title)
        if combined_match:
            issue_values.extend(
                _issue_suffix_value(suffix) for suffix in combined_match.groups()
            )
            continue
        if match := re.search(r"Issue 100([A-Z]+)", title):
            issue_values.append(_issue_suffix_value(match.group(1)))
    latest_issue_suffix = _issue_suffix_from_value(max(issue_values))
    update_analysis = inventory.partition("## Additional Update Analysis")[2].partition(
        "## Edge-Case Review"
    )[0]

    assert f"Issue 100{latest_issue_suffix}" in update_analysis
    assert "next candidate was\n**Issue 100A**" not in update_analysis
    assert "Issue 100B/100C together" not in update_analysis


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


def test_completed_issue_headers_do_not_claim_branch_or_worktree_only() -> None:
    stale_phrases = (
        "implemented in branch",
        "implemented on branch",
        "implemented in working tree",
        "implemented in worktree",
        "pending commit",
        "pending merge",
    )
    stale_headers = []
    for issue_path in sorted((REPO_ROOT / "docs" / "superpowers" / "issues").glob("*.md")):
        header = "\n".join(issue_path.read_text().splitlines()[:8])
        for stale_phrase in stale_phrases:
            if stale_phrase in header:
                stale_headers.append(f"{issue_path.name}: {stale_phrase}")

    assert stale_headers == []


def test_readme_documents_status_and_driver_first_workflow() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "/fig_drive" in readme
    assert "/fig_status fig3_trap_concept" in readme
    assert "canonical first check" in readme
    assert "Export, release, or\npolish only when" in readme


def test_readme_core_commands_cover_command_docs() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    core_commands_section = readme.partition("## Core commands")[2].partition(
        "## A typical figure"
    )[0]

    missing = []
    for command_doc in sorted((REPO_ROOT / "commands").glob("fig_*.md")):
        command = f"/{command_doc.stem}"
        if command not in core_commands_section:
            missing.append(command)

    assert missing == []


def test_skill_quick_command_list_covers_readme_core_commands() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    skill = (REPO_ROOT / "skills" / "figure-agent" / "SKILL.md").read_text()
    core_commands_section = readme.partition("## Core commands")[2].partition(
        "## A typical figure"
    )[0]
    readme_commands = set(re.findall(r"^/(fig_[a-z0-9_]+)", core_commands_section, re.M))
    skill_commands = set(re.findall(r"^/(fig_[a-z0-9_]+)", skill, re.M))
    missing = sorted(readme_commands - skill_commands)

    assert missing == []


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


def test_plugin_package_audit_can_preserve_fixture_artifacts_in_dev_cleanup(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plugin_root = tmp_path / "figure-agent"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (plugin_root / "examples" / "demo" / "build").mkdir(parents=True)
    (plugin_root / "examples" / "demo" / "exports").mkdir(parents=True)
    (plugin_root / "examples" / "demo" / "build" / "demo.pdf").write_bytes(b"%PDF")
    (plugin_root / "examples" / "demo" / "exports" / "demo.pdf").write_bytes(b"%PDF")
    (plugin_root / ".venv" / "bin").mkdir(parents=True)
    (plugin_root / ".pytest_cache").mkdir()

    result = main(
        [str(plugin_root), "--clean", "--preserve-fixture-artifacts", "--max-mib", "300"]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "JUNK" in output
    assert not (plugin_root / ".venv").exists()
    assert not (plugin_root / ".pytest_cache").exists()
    assert (plugin_root / "examples" / "demo" / "build" / "demo.pdf").is_file()
    assert (plugin_root / "examples" / "demo" / "exports" / "demo.pdf").is_file()


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


def test_plugin_package_audit_does_not_remove_tracked_paths_in_dev_worktree(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    plugin_root = repo_root / "plugins" / "figure-agent"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / "examples" / "demo" / "build").mkdir(parents=True)
    (plugin_root / "examples" / "demo" / "exports").mkdir(parents=True)
    (plugin_root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    tracked_build = plugin_root / "examples" / "demo" / "build" / ".gitkeep"
    tracked_export = plugin_root / "examples" / "demo" / "exports" / "demo.pdf"
    tracked_build.write_text("", encoding="utf-8")
    tracked_export.write_bytes(b"%PDF")
    (plugin_root / ".pytest_cache").mkdir()

    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "add", "plugins/figure-agent/examples"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    junk = find_packaging_junk(plugin_root)

    assert plugin_root / ".pytest_cache" in junk
    assert plugin_root / "examples" / "demo" / "build" not in junk
    assert plugin_root / "examples" / "demo" / "exports" not in junk

    remove_paths(junk)

    assert tracked_build.is_file()
    assert tracked_export.is_file()
    assert not (plugin_root / ".pytest_cache").exists()


def test_schema_module_map_covers_script_schema_constants() -> None:
    module_map = (
        REPO_ROOT
        / "docs"
        / "superpowers"
        / "issues"
        / "2026-06-01-issue-100hi-schema-module-map.md"
    ).read_text()
    missing: list[str] = []
    for script_path in sorted(SCRIPTS_ROOT.glob("*.py")):
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id != "SCHEMA" and not target.id.endswith("_SCHEMA"):
                    continue
                if not isinstance(node.value, ast.Constant):
                    continue
                schema = node.value.value
                if not isinstance(schema, str) or not schema.startswith("figure-agent."):
                    continue
                critique_shorthand = schema.replace("figure-agent.critique.", "")
                if (
                    schema.startswith("figure-agent.critique.v")
                    and critique_shorthand in module_map
                ):
                    continue
                if schema not in module_map:
                    missing.append(f"{schema} ({script_path.relative_to(REPO_ROOT)})")

    assert missing == []
