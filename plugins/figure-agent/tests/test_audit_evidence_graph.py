from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_ROOT))

import audit_evidence_graph  # noqa: E402


def _write_minimal_fixture(workspace: Path, name: str = "smoke_trap_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: smoke_trap_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    return fixture


def _node_by_id(graph: dict, node_id: str) -> dict:
    return next(node for node in graph["nodes"] if node["id"] == node_id)


def test_audit_evidence_graph_missing_fixture_returns_explicit_missing_nodes(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    graph = audit_evidence_graph.build_audit_evidence_graph(
        "missing_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert graph["schema"] == audit_evidence_graph.SCHEMA
    assert graph["name"] == "missing_demo"
    assert graph["first_blocker"]["code"] == "source_not_scaffolded"
    assert _node_by_id(graph, "source:spec.yaml")["exists"] is False
    assert _node_by_id(graph, "build:missing_demo.pdf")["exists"] is False


def test_audit_evidence_graph_minimal_fixture_has_source_nodes_and_hashes(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace)

    graph = audit_evidence_graph.build_audit_evidence_graph(
        "smoke_trap_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    spec_node = _node_by_id(graph, "source:spec.yaml")
    style_node = _node_by_id(graph, "style:polymer-paper-preamble.sty")
    assert spec_node["exists"] is True
    assert spec_node["sha256"].startswith("sha256:")
    assert style_node["exists"] is True
    assert style_node["path"] == "styles/polymer-paper-preamble.sty"
    assert graph["readiness"]["workflow_ready"] is False
    assert graph["first_blocker"]["code"] == "source_not_authored"


def test_audit_evidence_graph_is_deterministic(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace)

    first = audit_evidence_graph.build_audit_evidence_graph(
        "smoke_trap_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    second = audit_evidence_graph.build_audit_evidence_graph(
        "smoke_trap_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert first == second
    assert [node["id"] for node in first["nodes"]] == sorted(
        node["id"] for node in first["nodes"]
    )
    assert [edge["id"] for edge in first["edges"]] == sorted(
        edge["id"] for edge in first["edges"]
    )


def test_audit_evidence_graph_blocks_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    (fixture / "critique.md").symlink_to(outside)

    graph = audit_evidence_graph.build_audit_evidence_graph(
        "smoke_trap_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    critique_node = _node_by_id(graph, "source:critique.md")
    assert critique_node["exists"] is True
    assert critique_node["blocked"] is True
    assert critique_node["reason"] == "path_escape"
    assert "sha256" not in critique_node


def test_audit_evidence_graph_duplicate_node_guard() -> None:
    nodes = [{"id": "same"}, {"id": "same"}]
    edges: list[dict] = []

    try:
        audit_evidence_graph._sort_and_validate(nodes, edges)
    except ValueError as exc:
        assert "duplicate graph node ids" in str(exc)
    else:
        raise AssertionError("duplicate nodes should fail")


def test_fig_agent_helper_allowlist_includes_audit_evidence_graph() -> None:
    fig_agent = (PLUGIN_ROOT / "bin" / "fig-agent").read_text(encoding="utf-8")

    assert '"audit_evidence_graph.py"' in fig_agent
