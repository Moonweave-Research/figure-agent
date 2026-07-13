from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_context_fixture(
    workspace: Path,
    name: str = "context_demo",
    *,
    extra_spec: str = "",
    context_pack_extra: str = "",
) -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"""
name: {name}
title: Context Demo
style_profile: polymer-paper
{extra_spec}
authoring_context_pack:
  enabled: true
{context_pack_extra}
panels:
  - id: C
    caption: Trap energy diagram
    semantic_claims:
      - id: trap-depth
        claim: Deep traps are harder to escape than shallow traps.
    locked_invariants:
      - id: energy-up
        invariant: Energy increases upward in the trap diagram.
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("## §1. Topic\nCharge trapping\n", encoding="utf-8")
    (fixture / "design.md").write_text("Use compact visual grammar.\n", encoding="utf-8")
    (fixture / "authoring_plan.md").write_text(
        "Hero: panel C should read as deep trap first, then escape barrier.\n",
        encoding="utf-8",
    )
    (fixture / "panel_goals.md").write_text(
        "Panel C: make the reader compare shallow and deep trap escape paths.\n",
        encoding="utf-8",
    )
    return fixture


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_context_pack_cli_compiles_read_only_json_payload(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.authoring-context-pack.v1"
    assert payload["read_only"] is True
    assert payload["scope_boundary"]["generation_executor"] is False
    assert payload["scope_boundary"]["durable_paper_specific_knowledge_compilation"] is True
    assert payload["semantic_contracts"]["enabled"] is True
    assert payload["semantic_contracts"]["semantic_claims"][0]["id"] == "trap-depth"
    # context_demo != fig1_overview_v2_pair_001_vault: the per-fixture catalog is
    # scoped to its own fixture, so a non-matching fixture gets no per-fixture catalog
    assert payload["rule_catalog"] is None
    assert payload["sources"]["rule_catalog"] == ""
    assert "briefing" in payload["paper_context"]


def test_context_pack_includes_read_only_narrative_context(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    before = _file_snapshot(fixture)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert _file_snapshot(fixture) == before
    payload = json.loads(result.stdout)
    narrative = payload["narrative_context"]
    assert narrative["schema"] == "figure-agent.narrative-context.v1"
    assert narrative["read_only"] is True
    assert narrative["mode"] == "human_perspective_compiler"
    assert narrative["sources"]["briefing"].endswith("briefing.md")
    assert narrative["sources"]["panel_goals"].endswith("panel_goals.md")
    assert narrative["reader_contract"]["first_takeaway_source"] == "briefing.md"
    assert narrative["reader_contract"]["panel_story_inputs"]
    assert narrative["reader_contract"]["human_review_questions"]
    assert narrative["stop_boundaries"] == {
        "autonomous_patch_selection": False,
        "generation_executor": False,
        "model_calls": False,
        "prompt_loop": False,
        "rank_scoring": False,
        "source_mutation": False,
    }


def test_context_pack_scopes_per_fixture_catalog_to_its_own_fixture() -> None:
    # the pair001 catalog is selected by declared paper id, not by an ambient
    # hardcoded file path
    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "fig1_overview_v2_pair_001_vault",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=_env(PLUGIN_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    catalog = payload["rule_catalog"]
    assert catalog is not None
    assert catalog["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert payload["sources"]["rule_catalog"].endswith("authoring-rules-pair001.md")
    rule_ids = [rule["id"] for rule in catalog["rules"]]
    assert "pair001.panel-c-hero-split" in rule_ids


def test_context_pack_selects_rule_catalog_by_paper_id_for_later_figure(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(
        workspace,
        name="fig2_same_paper",
        extra_spec="paper_id: pair001\n",
    )

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "fig2_same_paper", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    catalog = payload["rule_catalog"]
    assert catalog is not None
    assert catalog["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert payload["sources"]["rule_catalog"].endswith("authoring-rules-pair001.md")
    assert "pair001.panel-c-hero-split" in [rule["id"] for rule in catalog["rules"]]


def test_context_pack_accepts_explicit_rule_catalog_selector(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(
        workspace,
        context_pack_extra="  rule_catalog: pair001\n",
    )

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["rule_catalog"]["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert payload["sources"]["rule_catalog"].endswith("authoring-rules-pair001.md")


def test_context_pack_rejects_unsafe_rule_catalog_selector(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(
        workspace,
        context_pack_extra="  rule_catalog: ../pair001\n",
    )

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "rule_catalog" in result.stdout


def test_context_pack_accepts_format_json_spelling(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--format",
            "json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["name"] == "context_demo"


def test_context_pack_injects_selected_layout_lane_contract_as_authoring_directive(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    review = fixture / "review"
    review.mkdir()
    (review / "layout_lanes.yaml").write_text(
        """
schema: figure-agent.layout-lanes.v1
label_groups:
  - id: narrative
    required_terms: [applied, trapping, during, conduction]
  - id: bias
    required_terms: [V]
rules:
  - id: narrative_clear_of_bias
    kind: minimum_clearance
    first: narrative
    second: bias
    minimum_normalized_clearance: 0.015
""".lstrip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--layout-contract",
            "review/layout_lanes.yaml",
            "--json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["sources"]["layout_lanes"].endswith(
        "examples/context_demo/review/layout_lanes.yaml"
    )
    assert payload["layout_constraints"]["schema"] == "figure-agent.layout-lanes.v1"
    assert payload["layout_constraints"]["authoring_directives"] == [
        "Keep text group [applied, trapping, during, conduction] at least 0.015 "
        "page-diagonal units clear of text group [V]."
    ]


def test_context_pack_injects_region_containment_and_plot_clearance_directives(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    review = fixture / "review"
    review.mkdir()
    (review / "layout_lanes.yaml").write_text(
        """
schema: figure-agent.layout-lanes.v1
label_groups:
  - id: title
    required_terms: [Mechanism]
  - id: note
    required_terms: [decays]
regions:
  - id: panel_a
    normalized_bbox: [0.0, 0.0, 0.5, 1.0]
  - id: decay_plot
    normalized_bbox: [0.1, 0.2, 0.5, 0.8]
rules:
  - id: title_in_panel
    kind: contained_in_region
    group: title
    region: panel_a
    minimum_normalized_inset: 0.01
  - id: note_clear_of_plot
    kind: minimum_clearance_from_region
    group: note
    region: decay_plot
    minimum_normalized_clearance: 0.02
""".lstrip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--layout-contract",
            "review/layout_lanes.yaml",
            "--json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["layout_constraints"]["authoring_directives"] == [
        "Keep text group [Mechanism] inside region [panel_a] with at least 0.01 "
        "normalized page inset.",
        "Keep text group [decays] at least 0.02 page-diagonal units clear of "
        "region [decay_plot].",
    ]


def test_context_pack_injects_declared_text_budget_directives(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    review = fixture / "review"
    review.mkdir()
    (review / "layout_lanes.yaml").write_text(
        """
schema: figure-agent.layout-lanes.v1
label_groups: []
regions:
  - id: page
    normalized_bbox: [0.0, 0.0, 1.0, 1.0]
  - id: panel_a
    normalized_bbox: [0.0, 0.0, 0.5, 1.0]
text_budgets:
  - id: figure_text
    region: page
    maximum_words: 45
  - id: panel_a_text
    region: panel_a
    maximum_words: 22
rules: []
""".lstrip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--layout-contract",
            "review/layout_lanes.yaml",
            "--json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["layout_constraints"]["authoring_directives"] == [
        "Keep region [page] at or below 45 rendered words.",
        "Keep region [panel_a] at or below 22 rendered words.",
    ]


def test_context_pack_rejects_layout_contract_through_symlinked_parent(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "layout_lanes.yaml").write_text(
        "schema: figure-agent.layout-lanes.v1\nlabel_groups: []\nrules: []\n",
        encoding="utf-8",
    )
    (fixture / "review").symlink_to(outside, target_is_directory=True)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--layout-contract",
            "review/layout_lanes.yaml",
            "--json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "layout contract must remain inside the fixture" in result.stdout


def test_context_pack_injects_project_scope_conventions(tmp_path: Path) -> None:
    # cross-figure conventions (e.g. vertical cantilever) must reach every figure's
    # context pack, not stay locked to the fig1 pilot catalog
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    project = payload["project_rule_catalog"]
    assert project is not None
    rule_ids = [rule["id"] for rule in project["rules"]]
    assert "polymer_paper_project.cantilever-vertical-clip-top" in rule_ids
    assert payload["sources"]["project_rule_catalog"].endswith("authoring-rules-project.md")


def test_context_pack_text_renders_project_conventions(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Project Rule Catalog" in result.stdout
    assert "cantilever vertical" in result.stdout.lower()
