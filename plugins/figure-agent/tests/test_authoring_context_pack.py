from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import authoring_context_pack
import pytest

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


def _write_shape_profile(fixture: Path, relative_path: str = "attempts/a1/shape.yaml") -> Path:
    profile = fixture / relative_path
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(
        """
schema: figure-agent.shape-profile.v1
status: experimental_attempt_scoped
objects:
  - id: s60
    role: discrete_distribution
  - id: s80
    role: continuous_broad_distribution
relations:
  - kind: wider_than
    subject: s80
    object: s60
  - kind: same_encoding_family
    members: [s60, s80]
forbidden_claims: [fixed_peak_count, monotonic_disorder, decay_direction]
composition_header: increasing sulfur content
""".lstrip(),
        encoding="utf-8",
    )
    return profile


def _write_composition_profile(
    fixture: Path, relative_path: str = "attempts/a1/composition.yaml"
) -> Path:
    profile = fixture / relative_path
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(
        """
schema: figure-agent.composition-profile.v1
status: experimental_attempt_scoped
policy: preserve_llm_composition
requirements:
  - semantic_load_controls_area
  - related_panels_are_grouped
  - negative_space_is_reserved
forbidden:
  - fixed_coordinates
  - fixed_panel_rectangles
  - primitive_geometry
  - palette_override
""".lstrip(),
        encoding="utf-8",
    )
    return profile


def _write_aesthetic_intent(fixture: Path) -> Path:
    path = fixture / "aesthetic_intent.yaml"
    path.write_text(
        """
schema: figure-agent.aesthetic-intent.v2
fixture: context_demo
target_journal: Nature Communications
visual_maturity: polished
density: balanced
reference_style: multipanel_story
design_principles:
  - id: publication_restraint
    instruction: Add detail only when it strengthens an already declared object or relation.
must_avoid:
  - id: invented_measurement
    pattern: Do not make a conceptual panel look like measured data.
    severity: MAJOR
polish_triggers:
  - id: semantic_first
    condition: Preserve semantic boundaries before any optical refinement.
    recommended_path: continue_tikz
aesthetic_levers:
  - id: state_hierarchy
    dimension: component_fidelity
    intent: Make semantic states visibly distinct without adding new claims.
    priority: required
    positive_signals:
      - Occupied and unoccupied states are optically distinct.
    anti_patterns:
      - Repeated generic marks with no semantic hierarchy.
    allowed_adjustments:
      - Refine state-marker hierarchy.
    forbidden_adjustments:
      - Add new physical states.
    default_route: tikz_patch
""".lstrip(),
        encoding="utf-8",
    )
    return path


def test_context_pack_injects_non_coordinate_composition_profile(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    profile = _write_composition_profile(fixture)

    payload = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        composition_profile="attempts/a1/composition.yaml",
    )

    selected = payload["composition_profile"]
    assert selected["sha256"] == (
        f"sha256:{hashlib.sha256(profile.read_bytes()).hexdigest()}"
    )
    assert selected["policy"] == "preserve_llm_composition"
    assert selected["authoring_directives"]
    rendered = authoring_context_pack.render_text(payload)
    assert "## Composition Profile" in rendered
    assert "no coordinates or panel rectangles are prescribed" in rendered


def test_context_pack_binds_optional_aesthetic_intent_as_authoring_directives(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    intent = _write_aesthetic_intent(fixture)

    payload = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    selected = payload["aesthetic_intent"]
    assert selected["path"] == "examples/context_demo/aesthetic_intent.yaml"
    assert selected["sha256"] == f"sha256:{hashlib.sha256(intent.read_bytes()).hexdigest()}"
    assert selected["schema"] == "figure-agent.aesthetic-intent.v2"
    assert selected["authoring_directives"] == [
        (
            "Preserve publication_restraint: Add detail only when it strengthens an "
            "already declared object or relation."
        ),
        "For state_hierarchy: Make semantic states visibly distinct without adding new claims.",
        "Avoid state_hierarchy anti-patterns: Repeated generic marks with no semantic hierarchy.",
        "Allowed for state_hierarchy: Refine state-marker hierarchy.",
        "Forbidden for state_hierarchy: Add new physical states.",
        "Use tikz_patch for state_hierarchy by default.",
    ]
    assert "## Aesthetic Intent" in authoring_context_pack.render_text(payload)


def test_fig3_context_pack_binds_human_detail_uplift_direction() -> None:
    payload = authoring_context_pack.build_context_pack(
        "fig3_resistance_mechanism",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )

    directives = payload["aesthetic_intent"]["authoring_directives"]
    assert (
        "For material_state_hierarchy: Make carrier, trap, and terminal slow-release "
        "state roles optically distinct without adding a new physical state."
    ) in directives
    assert (
        "For irregular_support_field: Make S80 read as a dense irregular energy-state "
        "field, never as a fitted density-of-states envelope."
    ) in directives
    assert (
        "For cross_panel_finish: Increase detail through hierarchy and state distinction, "
        "not through measured-data cues or decorative texture."
    ) in directives
    assert all("Fig1" not in directive for directive in directives)


def test_context_pack_outer_cli_forwards_composition_profile(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    profile = _write_composition_profile(fixture)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--composition-profile",
            "attempts/a1/composition.yaml",
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
    assert payload["composition_profile"]["path"] == (
        "attempts/a1/composition.yaml"
    )
    assert payload["composition_profile"]["sha256"] == (
        f"sha256:{hashlib.sha256(profile.read_bytes()).hexdigest()}"
    )


def test_build_context_pack_injects_selected_shape_profile(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    profile = _write_shape_profile(fixture)

    payload = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        shape_profile="attempts/a1/shape.yaml",
    )

    assert payload["shape_profile"] == {
        "path": "attempts/a1/shape.yaml",
        "sha256": f"sha256:{hashlib.sha256(profile.read_bytes()).hexdigest()}",
        "schema": "figure-agent.shape-profile.v1",
        "status": "experimental_attempt_scoped",
        "objects": [
            {"id": "s60", "role": "discrete_distribution"},
            {"id": "s80", "role": "continuous_broad_distribution"},
        ],
        "relations": [
            {"kind": "wider_than", "subject": "s80", "object": "s60"},
            {"kind": "same_encoding_family", "members": ["s60", "s80"]},
        ],
        "forbidden_claims": [
            "fixed_peak_count",
            "monotonic_disorder",
            "decay_direction",
        ],
        "composition_header": "increasing sulfur content",
        "authoring_directives": [
            "Render [s80] visibly wider in energy than [s60].",
            "Use one shared outline, fill, and stroke encoding family for [s60, s80].",
            (
                "Use composition header [increasing sulfur content] without a curve-to-curve "
                "causal arrow."
            ),
            (
                "Do not assert unresolved claims [fixed_peak_count, monotonic_disorder, "
                "decay_direction]."
            ),
        ],
    }


def test_context_pack_cli_forwards_selected_shape_profile_once(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    profile = _write_shape_profile(fixture)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--shape-profile",
            "attempts/a1/shape.yaml",
            "--json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    selected = json.loads(result.stdout)["shape_profile"]
    assert selected["path"] == "attempts/a1/shape.yaml"
    assert selected["sha256"] == f"sha256:{hashlib.sha256(profile.read_bytes()).hexdigest()}"
    assert selected["authoring_directives"][0] == (
        "Render [s80] visibly wider in energy than [s60]."
    )


def test_context_pack_cli_renders_selected_shape_profile_directives_by_default(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    _write_shape_profile(fixture)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--shape-profile",
            "attempts/a1/shape.yaml",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "## Shape Profile" in result.stdout
    assert "- Render [s80] visibly wider in energy than [s60]." in result.stdout
    assert (
        "- Use one shared outline, fill, and stroke encoding family for [s60, s80]."
        in result.stdout
    )
    assert (
        "- Use composition header [increasing sulfur content] without a curve-to-curve "
        "causal arrow." in result.stdout
    )
    assert (
        "- Do not assert unresolved claims [fixed_peak_count, monotonic_disorder, "
        "decay_direction]." in result.stdout
    )


def test_context_pack_injects_declared_label_path_clearance_before_generation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(
        workspace,
        extra_spec="""
label_path_proximity_checks:
  - id: panel_a_carrier_path
    kind: polyline
    role: semantic_carrier_path
    points_pdf_cm:
      - [1.0, 1.0]
      - [2.0, 2.0]
      - [3.0, 1.5]
    clearance_pt: 4.0
    text_phrases:
      - id: carrier_key
        words: [carrier, path]
""",
    )

    payload = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert payload["path_constraints"]["schema"] == (
        "figure-agent.label-path-proximity.v1"
    )
    assert payload["path_constraints"]["authoring_directives"] == [
        "Keep text phrase [carrier path] at least 4 pt clear of declared path "
        "[panel_a_carrier_path] (semantic_carrier_path; PDF-cm polyline "
        "[(1, 1), (2, 2), (3, 1.5)])."
    ]
    rendered = authoring_context_pack.render_text(payload)
    assert "## Declared Label-Path Constraints" in rendered
    assert payload["path_constraints"]["authoring_directives"][0] in rendered


def test_context_pack_outer_cli_rejects_explicit_empty_shape_profile(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--shape-profile",
            "",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "shape profile must be a fixture-relative safe path" in result.stdout


def test_context_pack_does_not_auto_select_shape_profile_from_spec(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(
        workspace,
        extra_spec="shape_profile: attempts/a1/shape.yaml\n",
    )
    _write_shape_profile(fixture)

    payload = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert "shape_profile" not in payload


def test_context_pack_maps_invalid_shape_profile_to_controlled_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    profile = _write_shape_profile(fixture)
    profile.write_text(profile.read_text(encoding="utf-8").replace(".v1", ".v2"), encoding="utf-8")

    with pytest.raises(authoring_context_pack.AuthoringContextPackError, match="schema must equal"):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            shape_profile="attempts/a1/shape.yaml",
        )


@pytest.mark.parametrize("yaml_payload", ["[]\n", "shape-profile\n", "null\n"])
def test_context_pack_maps_non_mapping_shape_profile_payload_to_controlled_error(
    tmp_path: Path,
    yaml_payload: str,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    profile = fixture / "attempts" / "a1" / "shape.yaml"
    profile.parent.mkdir(parents=True)
    profile.write_text(yaml_payload, encoding="utf-8")

    with pytest.raises(
        authoring_context_pack.AuthoringContextPackError,
        match="payload must be a mapping",
    ):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            shape_profile="attempts/a1/shape.yaml",
        )


@pytest.mark.parametrize(
    "selector",
    [
        "/tmp/shape.yaml",
        "../shape.yaml",
        "attempts/./shape.yaml",
        "attempts//shape.yaml",
        "attempts/a1/../shape.yaml",
        "attempts/a1/shape.yaml/",
    ],
)
def test_context_pack_rejects_unsafe_shape_profile_paths(
    tmp_path: Path,
    selector: str,
) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    with pytest.raises(authoring_context_pack.AuthoringContextPackError, match="shape profile"):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            shape_profile=selector,
        )


def test_context_pack_rejects_missing_shape_profile(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    with pytest.raises(authoring_context_pack.AuthoringContextPackError, match="not found"):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            shape_profile="attempts/a1/missing.yaml",
        )


def test_context_pack_rejects_symlinked_shape_profile_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    target = _write_shape_profile(fixture, "attempts/a1/target.yaml")
    (target.parent / "shape.yaml").symlink_to(target)

    with pytest.raises(authoring_context_pack.AuthoringContextPackError, match="symlinked"):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            shape_profile="attempts/a1/shape.yaml",
        )


def test_context_pack_rejects_shape_profile_through_symlinked_parent_escape(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    outside = tmp_path / "outside"
    target = _write_shape_profile(outside, "shape.yaml")
    (fixture / "attempts").symlink_to(target.parent, target_is_directory=True)

    with pytest.raises(authoring_context_pack.AuthoringContextPackError, match="symlinked"):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            shape_profile="attempts/shape.yaml",
        )


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


def test_context_pack_binds_explicit_curated_visual_assets(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(
        workspace,
        context_pack_extra=(
            "  visual_asset_ids:\n"
            "    - panel_f_floating_cantilever\n"
        ),
    )

    payload = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assets = payload["visual_assets"]
    assert assets["schema"] == "figure-agent.authoring-visual-assets.v1"
    assert assets["catalog_path"] == "styles/snippets/INDEX.yaml"
    assert len(assets["selected"]) == 1
    selected = assets["selected"][0]
    assert selected["id"] == "panel_f_floating_cantilever"
    assert selected["status"] == "reviewed_reusable"
    assert selected["path"] == "styles/snippets/panel-f-floating-cantilever.tex"
    assert selected["sha256"].startswith("sha256:")
    assert selected["contract"]["path"].endswith(".contract.yaml")
    assert selected["transfer_receipt"]["path"].endswith(".transfer.yaml")
    assert selected["authoring_directives"]

    rendered = authoring_context_pack.render_text(payload)
    assert "## Curated Visual Assets" in rendered
    assert "panel_f_floating_cantilever" in rendered
    assert "Do not redraw its owned geometry" in rendered


def test_context_pack_rejects_unknown_curated_visual_asset(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(
        workspace,
        context_pack_extra="  visual_asset_ids: [missing_asset]\n",
    )

    with pytest.raises(
        authoring_context_pack.AuthoringContextPackError,
        match="visual asset id is not present in the curated catalog",
    ):
        authoring_context_pack.build_context_pack(
            "context_demo",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
        )


def test_context_pack_rejects_non_reusable_catalog_status(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    catalog_dir = plugin_root / "styles" / "snippets"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "planned.tex").write_text("% not reusable\n", encoding="utf-8")
    (catalog_dir / "INDEX.yaml").write_text(
        "snippets:\n"
        "  planned_asset:\n"
        "    file: styles/snippets/planned.tex\n"
        "    status: planned\n",
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_context_pack.AuthoringContextPackError,
        match="visual asset is not reusable: planned_asset",
    ):
        authoring_context_pack._authoring_visual_assets(
            plugin_root,
            {
                "authoring_context_pack": {
                    "visual_asset_ids": ["planned_asset"],
                }
            },
        )


def test_context_pack_rejects_stale_transfer_receipt(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    catalog_dir = plugin_root / "styles" / "snippets"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "asset.tex").write_text("% asset\n", encoding="utf-8")
    (catalog_dir / "asset.contract.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    (catalog_dir / "asset.transfer.yaml").write_text(
        "shared_bindings:\n"
        "  styles/snippets/asset.tex: sha256:stale\n"
        "  styles/snippets/asset.contract.yaml: sha256:stale\n",
        encoding="utf-8",
    )
    (catalog_dir / "INDEX.yaml").write_text(
        "snippets:\n"
        "  asset:\n"
        "    file: styles/snippets/asset.tex\n"
        "    contract: styles/snippets/asset.contract.yaml\n"
        "    transfer_receipt: styles/snippets/asset.transfer.yaml\n"
        "    status: reviewed_reusable\n",
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_context_pack.AuthoringContextPackError,
        match="visual asset transfer receipt is stale: asset",
    ):
        authoring_context_pack._authoring_visual_assets(
            plugin_root,
            {"authoring_context_pack": {"visual_asset_ids": ["asset"]}},
        )


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


def test_context_pack_injects_moved_group_neighbor_clearance_directive(
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
  - id: moved_label
    required_phrase: distribution breadth
  - id: axis_label
    required_phrase: trap energy E
  - id: magnitude_label
    required_phrase: magnitude
rules:
  - id: moved_label_neighbor_clearance
    kind: minimum_clearance_from_groups
    group: moved_label
    other_groups: [axis_label, magnitude_label]
    minimum_normalized_clearance: 0.01
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
        "Keep text group [distribution breadth] at least 0.01 page-diagonal "
        "units clear of each declared neighboring text group: "
        "[trap energy E]; [magnitude]."
    ]


def test_context_pack_rejects_colliding_expanded_layout_result_ids(
    tmp_path: Path,
) -> None:
    fixture = _write_context_fixture(tmp_path / "workspace")
    review = fixture / "review"
    review.mkdir()
    (review / "layout_lanes.yaml").write_text(
        """
schema: figure-agent.layout-lanes.v1
label_groups:
  - id: moved
    required_phrase: distribution breadth
  - id: axis
    required_phrase: trap energy E
rules:
  - id: moved_neighbors
    kind: minimum_clearance_from_groups
    group: moved
    other_groups: [axis]
    minimum_normalized_clearance: 0.01
  - id: moved_neighbors:axis
    kind: minimum_clearance
    first: moved
    second: axis
    minimum_normalized_clearance: 0.01
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_context_pack.AuthoringContextPackError,
        match="duplicate layout result id",
    ):
        authoring_context_pack._layout_constraints(
            fixture, "review/layout_lanes.yaml"
        )


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


def test_context_pack_injects_panel_owned_required_phrase_directive(
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
  - id: panel_b_x_axis_label
    required_phrase: trap energy E
    region: panel_b
regions:
  - id: panel_b
    normalized_bbox: [0.5, 0.0, 1.0, 1.0]
rules:
  - id: panel_b_x_axis_label_owned
    kind: contained_in_region
    group: panel_b_x_axis_label
    region: panel_b
    minimum_normalized_inset: 0.005
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
        "Keep text group [trap energy E] inside region [panel_b] with at least "
        "0.005 normalized page inset."
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
    assert "## Shape Profile" not in result.stdout
