"""Operator-facing command contract drift checks."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


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
