"""Binding rendered label text back to its TikZ node."""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import tex_node_index  # noqa: E402


def test_node_body_is_the_last_group_not_the_first() -> None:
    """A calc coordinate carries braces of its own. Reading the first group as
    the label binds a coordinate expression and calls it a label."""
    tex = "\\node[labelMicro] at ({\\leftEdge+0.5*\\cellWidth},0.88)\n    {occupancy};\n"

    nodes = tex_node_index.node_index(tex)

    assert [node["text"] for node in nodes] == ["occupancy"]


def test_source_line_anchors_on_the_node_keyword() -> None:
    tex = "% preamble\n\\node[x] at (0,0)\n    {trapped charge};\n"

    assert tex_node_index.node_index(tex)[0]["source_line"] == 2


def test_markup_is_stripped_so_source_compares_against_rendered_words() -> None:
    tex = "\\node at (0,0) {$E_\\mathrm{app}$};\n"

    assert tex_node_index.node_index(tex)[0]["text"] == "E app"


def test_unique_phrase_binds_and_ambiguity_refuses() -> None:
    tex = (
        "\\node at (0,0) {field-on charging};\n"
        "\\node at (1,0) {field-on hold};\n"
        "\\node at (2,0) {recovery};\n"
    )

    assert tex_node_index.unique_source_line(tex, "recovery") == 3
    # "field-on" is in two nodes: a guess would be worse than no answer.
    assert tex_node_index.unique_source_line(tex, "field-on") is None
    assert tex_node_index.unique_source_line(tex, "absent") is None
    assert tex_node_index.unique_source_line(tex, "  ") is None


def test_an_unterminated_node_is_skipped_rather_than_guessed() -> None:
    assert tex_node_index.node_index("\\node at (0,0) {dangling}\n") == []


def test_binds_a_real_label_in_a_real_fixture() -> None:
    """The parser has to survive an authored figure, not only crafted input."""
    source = (
        PLUGIN_ROOT
        / "examples"
        / "fig5_cantilever_actuation_artifact_v2"
        / "fig5_cantilever_actuation_artifact_v2.tex"
    )
    if not source.is_file():
        return
    tex = source.read_text(encoding="utf-8")

    line = tex_node_index.unique_source_line(tex, "clip: GND")

    assert line is not None
    assert "clip: GND" in tex.splitlines()[line - 1]
