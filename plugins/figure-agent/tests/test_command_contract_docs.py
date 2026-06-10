"""Operator-facing command contract drift checks."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

JSON_OUTPUT_COMMAND_SCRIPTS = {
    "fig_closeout.md": "fig_closeout.py",
    "fig_context_pack.md": "authoring_context_pack.py",
    "fig_drive.md": "fig_driver.py",
    "fig_e2e_smoke.md": "fig_e2e_smoke.py",
    "fig_improve.md": "fig_improve.py",
    "fig_loop.md": "fig_loop.py",
    "fig_queue.md": "fig_queue.py",
    "fig_queue_run.md": "fig_queue_run.py",
    "fig_run.md": "fig_run.py",
    "fig_status.md": "status.py",
}


def _read(relative_path: str) -> str:
    return (PLUGIN_ROOT / relative_path).read_text(encoding="utf-8")


def test_fig_critique_documents_v1_17_grounded_contract_fields() -> None:
    doc = _read("commands/fig_critique.md")

    required_strings = [
        "schema `figure-agent.critique.v1.17`",
        "`aesthetic_antipattern_audit`",
        "`weakest_panel_coherence`",
        "`reference_learning_accountability`",
        "Do not paste older schemas for grounded v1.17 critiques.",
    ]

    for required in required_strings:
        assert required in doc


def test_command_docs_do_not_describe_route_detail_as_v1_14_only() -> None:
    docs_by_path = {
        "commands/fig_critique.md": _read("commands/fig_critique.md"),
        "commands/fig_loop.md": _read("commands/fig_loop.md"),
        "commands/fig_drive.md": _read("commands/fig_drive.md"),
    }

    forbidden_fragments = [
        "For schema `figure-agent.critique.v1.14`, the summary",
        "When v1.14 route detail exists",
        "For schema `figure-agent.critique.v1.14`, the loop summary",
        "In v1.14, `tikz_vs_svg_polish_trigger",
    ]

    for path, doc in docs_by_path.items():
        for fragment in forbidden_fragments:
            assert fragment not in doc, f"{path} still uses v1.14-only wording"


def test_skill_documents_v1_17_l4_5_contract() -> None:
    doc = _read("skills/figure-agent/SKILL.md")

    for required in (
        "schema v1.17",
        "`aesthetic_antipattern_audit`",
        "`weakest_panel_coherence`",
        "`reference_learning_accountability`",
    ):
        assert required in doc


def test_fig_run_documents_explicit_json_output_spellings() -> None:
    doc = _read("commands/fig_run.md")

    assert "[--json | --format json]" in doc
    assert "`--json` and `--format json` are accepted" in doc


def test_command_docs_json_output_spellings_match_scripts() -> None:
    command_docs = sorted((PLUGIN_ROOT / "commands").glob("fig_*.md"))
    docs_with_json_usage = {
        path.name
        for path in command_docs
        if "[--json | --format json]" in path.read_text(encoding="utf-8")
    }

    assert docs_with_json_usage == set(JSON_OUTPUT_COMMAND_SCRIPTS)

    for doc_name, script_name in JSON_OUTPUT_COMMAND_SCRIPTS.items():
        script = _read(f"scripts/{script_name}")
        assert '"--json"' in script, doc_name
        assert '"--format"' in script, doc_name


def test_operator_docs_and_safe_commands_prefer_fig_agent_entrypoint() -> None:
    docs = {
        "README.md": _read("README.md"),
        "skills/figure-agent/SKILL.md": _read("skills/figure-agent/SKILL.md"),
        "docs/v0.9-operator-playbook.md": _read("docs/v0.9-operator-playbook.md"),
    }
    docs.update(
        {
            f"commands/{path.name}": path.read_text(encoding="utf-8")
            for path in (PLUGIN_ROOT / "commands").glob("fig_*.md")
        }
    )
    forbidden_patterns = [
        "bash scripts/compile.sh",
        "uv run python3 scripts/fig_driver.py",
        "uv run python3 scripts/fig_run.py",
        "uv run python3 scripts/fig_improve.py",
        "uv run python3 scripts/fig_queue.py",
        "uv run python3 scripts/fig_queue_run.py",
        "uv run python3 scripts/fig_closeout.py",
        "uv run python3 scripts/fig_e2e_smoke.py",
        "uv run python3 scripts/fig_loop.py",
        "uv run python3 scripts/status.py",
        "uv run python3 scripts/run_export.py",
        "uv run python scripts/run_export.py",
        "uv run python3 scripts/",
        "uv run python scripts/",
        "python3 scripts/",
        "PYTHONPATH=scripts",
    ]
    for doc_path, doc in docs.items():
        for forbidden in forbidden_patterns:
            assert forbidden not in doc, f"{doc_path} exposes {forbidden}"

    safe_commands = _read("scripts/fig_driver_commands.py")
    assert "fig-agent compile" in safe_commands
    assert "fig-agent export" in safe_commands
    assert "bash scripts/compile.sh" not in safe_commands
    assert "uv run python3 scripts/" not in safe_commands


def test_runtime_docs_define_cowork_entrypoint_fallback_and_root_split() -> None:
    docs = {
        "README.md": _read("README.md"),
        "skills/figure-agent/SKILL.md": _read("skills/figure-agent/SKILL.md"),
        "commands/fig_status.md": _read("commands/fig_status.md"),
    }

    for doc_path, doc in docs.items():
        assert '"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent"' in doc, doc_path
        assert "FIGURE_AGENT_PLUGIN_ROOT" in doc, doc_path
        assert "FIGURE_AGENT_WORKSPACE" in doc, doc_path
        assert "CLAUDE_PROJECT_DIR" in doc, doc_path
