from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import authoring_rules  # noqa: E402


def test_pair001_rule_catalog_requires_source_anchored_rules() -> None:
    catalog = authoring_rules.load_rule_catalog(PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md")

    assert catalog["schema"] == "figure-agent.authoring-rules.v1"
    assert catalog["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert catalog["promotion_state"] == "n1_hypotheses"
    assert len(catalog["rules"]) >= 8
    for rule in catalog["rules"]:
        assert rule["id"].startswith("pair001.")
        assert rule["category"] in {
            "chemistry_semantics",
            "physics_semantics",
            "label_binding",
            "instrument_standard",
            "panel_layout",
            "style_lock",
        }
        assert rule["source"]["kind"] in {
            "iteration_comment",
            "critique_adjudication",
            "hand_patch_commit",
        }
        assert rule["source"]["locator"]
        assert rule["source"]["quote"]
        assert rule["transfer_policy"] in {"use_as_question", "use_as_constraint"}


def test_current_ispd_rules_preserve_manual_keyence_measurement() -> None:
    pair_catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )
    project_catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-project.md"
    )

    pair_text = "\n".join(rule["rule"] for rule in pair_catalog["rules"])
    assert "motion stage" not in pair_text.lower()
    assert "grounded-substrate" not in pair_text.lower()
    pair_ids = {rule["id"] for rule in pair_catalog["rules"]}
    assert "pair001.instrument-faceplate-bezel" not in pair_ids
    superseded_ids = {rule["id"] for rule in pair_catalog["superseded_rules"]}
    assert "pair001.panel-e-probe-above-sample" in superseded_ids
    assert "pair001.panel-e-side-view-apparatus" in superseded_ids
    assert "pair001.instrument-faceplate-bezel" in superseded_ids

    ispd_rule = next(
        rule
        for rule in project_catalog["rules"]
        if rule["id"] == "polymer_paper_project.ispd-keyence-manual-transfer"
    )
    assert "Keyence SK series" in ispd_rule["rule"]
    assert "manually transfer" in ispd_rule["rule"]
    assert "Kelvin probe" in ispd_rule["rule"]
    assert "exact model" in ispd_rule["rule"]
    assert "elongated bar-shaped sensor head" in ispd_rule["rule"]
    assert "short end face" in ispd_rule["rule"]
    assert "visible non-contact standoff" in ispd_rule["rule"]
    assert "cable to a separate amplifier or meter" in ispd_rule["rule"]
    charging_rule = next(
        rule
        for rule in project_catalog["rules"]
        if rule["id"] == "polymer_paper_project.ispd-two-terminal-corona-topology"
    )
    assert "two terminals" in charging_rule["rule"]
    assert "Do not add a grid" in charging_rule["rule"]
    assert "charging station" in charging_rule["rule"]
    assert "measurement station" in charging_rule["rule"]
    assert "exact polarity" in charging_rule["rule"]

    measurement_rule = next(
        rule
        for rule in project_catalog["rules"]
        if rule["id"] == "polymer_paper_project.ispd-measurement-grounded-backing"
    )
    assert "measurement station" in measurement_rule["rule"]
    assert "grounded conductive backing" in measurement_rule["rule"]
    assert "not the polymer film" in measurement_rule["rule"]

    floating_rule = next(
        rule
        for rule in project_catalog["rules"]
        if rule["id"] == "polymer_paper_project.floating-coulomb-isolation"
    )
    assert "trapped-charge label" in floating_rule["rule"]
    assert "representative charge marker" in floating_rule["rule"]
    active_ids = {rule["id"] for rule in project_catalog["rules"]}
    assert "polymer_paper_project.ispd-measurement-grounded-backing" in active_ids
    assert "polymer_paper_project.ispd-grounded-backing-plate" not in active_ids
    project_superseded_ids = {
        rule["id"] for rule in project_catalog["superseded_rules"]
    }
    assert "polymer_paper_project.ispd-grounded-backing-plate" in project_superseded_ids


def test_project_rule_preserves_floating_coulomb_topology() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-project.md"
    )

    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "polymer_paper_project.floating-coulomb-isolation"
    )
    assert "grounded voltage-source return" in rule["rule"]
    assert "sample and cantilever remain electrically floating" in rule["rule"]
    assert "points away from the driven electrode" in rule["rule"]


def test_pair001_requires_semantic_depth_cues_for_repeated_markers() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    rule = next(
        rule for rule in catalog["rules"] if rule["id"] == "pair001.depth-cues-need-semantics"
    )
    assert "glossy or ball-shaded" in rule["rule"]
    assert "declared 3D geometry or material relation" in rule["rule"]
    assert "does not require apparatus photorealism" in rule["rule"]


def test_pair001_preserves_paper_local_tau_d_semantics() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "pair001.tau-d-energy-domain-exception"
    )
    assert "energy-domain interval" in rule["rule"]
    assert "endpoints bound to those two peak positions" in rule["rule"]
    assert "do not add numeric ticks, point markers" in rule["rule"]
    assert "Do not move it onto the V_s(t) time axis" in rule["rule"]
    assert "source-bound exception" in rule["rule"]


def test_pair001_binds_raw_to_derived_transformations() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "pair001.raw-to-derived-arrow-bound"
    )
    assert "tail must touch the source plot boundary" in rule["rule"]
    assert "arrowhead must enter the derived-result region" in rule["rule"]
    assert "dedicated transformation lane" in rule["rule"]


def test_general_caliper_rule_requires_visible_endpoint_projections_at_reduction() -> None:
    skill = (PLUGIN_ROOT / "skills" / "figure-agent" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(skill.split())

    assert "Inspect both endpoint projections at final reduction" in normalized
    assert "collapses into a bracket cap, peak, marker, or boundary" in normalized
    assert "does not visibly establish the referent" in normalized


def test_pair001_rejects_unbound_particle_like_host_texture() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "pair001.host-texture-needs-physical-identity"
    )
    assert "same-size dots" in rule["rule"]
    assert "fillers, pores, or a second population" in rule["rule"]
    assert "continuous non-periodic disorder cues" in rule["rule"]
    assert "omit decorative texture" in rule["rule"]


def test_panel_c_amorphous_host_embedded_localization_regression() -> None:
    skill = (PLUGIN_ROOT / "skills" / "figure-agent" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(skill.split())
    assert "Panel C-style amorphous-host regression rule" in skill
    assert "small number of non-periodic traces" in skill
    assert "combined" in skill
    assert "coverage reads as one disordered host field" in skill
    assert "allow longer or visually entangled paths" in normalized
    assert "directly on a continuous host trace" in skill
    assert "short asymmetric" in skill
    assert "The core alone may carry the category" in skill
    assert "Audit the whole host field" in skill
    assert "winged-dot defect" in skill
    assert "repairing sparse matrix occupancy is preferred to shrinking the panel" in normalized

    repaired = (
        PLUGIN_ROOT
        / "examples"
        / "fig1_updated_agent_redraw_v1"
        / "review"
        / "failure-first"
        / "comparable-v3-repair-c5"
        / "repaired.tex"
    ).read_text(encoding="utf-8")
    panel_c = repaired.split("% Panel C", 1)[1].split("% Panel D", 1)[0]
    real_space = panel_c.split("% Energy-space view:", 1)[0]
    host_texture = real_space.split("% Local contrast follows", 1)[0]

    assert host_texture.count("plot[smooth] coordinates") == 5
    assert "specimen-spanning amorphous host" in real_space
    assert "entangled" in real_space
    assert "trap-free cross-field trace" in real_space
    assert "structural cues, not literal chain topology" in real_space
    assert real_space.count("line width=1.20pt") == 0
    assert "cAmber!36!black" not in real_space
    assert r"\fill[cBlue!13]" not in real_space
    assert r"\fill[cRed!12]" not in real_space
    assert "circle (0.075)" in real_space

    core_fills = re.findall(
        r"\\fill\[(cBlue|cRed)!80\] \(([0-9.]+),([0-9.]+)\) circle \(0\.075\);",
        real_space,
    )
    assert core_fills == [
        ("cBlue", "1.55", "1.63"),
        ("cBlue", "4.64", "2.84"),
        ("cRed", "2.72", "3.64"),
        ("cRed", "5.42", "1.64"),
    ]
    for protected in [
        "mobility edge",
        "thermal escape",
        "{$\\Delta E_t$}",
        "shallow",
        "deep",
        "DOS",
    ]:
        assert protected in panel_c


def test_pair001_requires_one_ground_symbol_grammar() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "pair001.ground-symbol-grammar-consistent"
    )
    assert "same three-bar tapered ground grammar" in rule["rule"]
    assert "different electrical reference" in rule["rule"]


def test_pair001_binds_power_law_exponent_to_rendered_slope() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "pair001.power-law-slope-matches-exponent"
    )
    assert "larger n must have the more negative slope" in rule["rule"]
    assert "rendered endpoints" in rule["rule"]
    assert "label text alone" in rule["rule"]


def test_rule_catalog_rejects_unanchored_generic_guidance(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: fig1_overview_v2_pair_001_vault\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: pair001.bad\n"
        "    category: panel_layout\n"
        "    rule: Make the figure beautiful.\n"
        "    source:\n"
        "      kind: iteration_comment\n"
        "      locator: ''\n"
        "      quote: ''\n"
        "    transfer_policy: use_as_constraint\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(authoring_rules.AuthoringRuleError, match="source_anchor_missing"):
        authoring_rules.load_rule_catalog(path)


def test_rule_catalog_partitions_superseded_rules(tmp_path: Path) -> None:
    path = tmp_path / "lifecycle.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: demo\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: demo.current\n"
        "    category: instrument_standard\n"
        "    rule: Preserve the confirmed manual measurement.\n"
        "    source:\n"
        "      kind: iteration_comment\n"
        "      locator: review-current\n"
        "      quote: manual measurement\n"
        "    transfer_policy: use_as_constraint\n"
        "  - id: demo.old\n"
        "    category: instrument_standard\n"
        "    rule: Draw an automated stage.\n"
        "    source:\n"
        "      kind: iteration_comment\n"
        "      locator: review-old\n"
        "      quote: automated stage\n"
        "    transfer_policy: use_as_constraint\n"
        "    lifecycle: superseded\n"
        "    superseded_by: demo.current\n"
        "    superseded_reason: Later human review corrected the transfer agency.\n"
        "---\n",
        encoding="utf-8",
    )

    catalog = authoring_rules.load_rule_catalog(path)

    assert [rule["id"] for rule in catalog["rules"]] == ["demo.current"]
    assert [rule["id"] for rule in catalog["superseded_rules"]] == ["demo.old"]


def test_rule_catalog_rejects_superseded_rule_without_replacement(tmp_path: Path) -> None:
    path = tmp_path / "bad-lifecycle.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: demo\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: demo.old\n"
        "    category: instrument_standard\n"
        "    rule: Draw an automated stage.\n"
        "    source:\n"
        "      kind: iteration_comment\n"
        "      locator: review-old\n"
        "      quote: automated stage\n"
        "    transfer_policy: use_as_constraint\n"
        "    lifecycle: superseded\n"
        "    superseded_reason: Later human review corrected it.\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(authoring_rules.AuthoringRuleError, match="superseded_by_missing"):
        authoring_rules.load_rule_catalog(path)


def test_catalog_set_requires_live_supersession_target() -> None:
    stale_catalog = {
        "rules": [],
        "superseded_rules": [
            {
                "id": "demo.old",
                "superseded_by": "project.current",
            }
        ],
    }
    live_catalog = {
        "rules": [{"id": "project.current"}],
        "superseded_rules": [],
    }

    authoring_rules.validate_catalog_set([stale_catalog, live_catalog])

    with pytest.raises(
        authoring_rules.AuthoringRuleError, match="supersession_target_missing"
    ):
        authoring_rules.validate_catalog_set([stale_catalog])


def test_rule_catalog_accepts_project_namespace(tmp_path: Path) -> None:
    # a project-scope catalog (non-pair001 namespace) carries cross-figure conventions
    path = tmp_path / "project.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: polymer_paper_project\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: polymer_paper_project.cantilever-vertical-clip\n"
        "    category: instrument_standard\n"
        "    rule: Cantilever is vertical; clip on top, polymer hangs down.\n"
        "    source:\n"
        "      kind: hand_patch_commit\n"
        "      locator: fig3_floating_clip_protocol\n"
        "      quote: clip on TOP, polymer hangs down\n"
        "    transfer_policy: use_as_constraint\n"
        "---\n",
        encoding="utf-8",
    )

    catalog = authoring_rules.load_rule_catalog(path)
    assert catalog["rules"][0]["id"] == "polymer_paper_project.cantilever-vertical-clip"
    assert catalog["rules"][0]["category"] == "instrument_standard"


def test_project_catalog_carries_current_poly_s_dib_microstructure_rule() -> None:
    catalog = authoring_rules.load_rule_catalog(
        Path(__file__).resolve().parents[1] / "docs" / "authoring-rules-project.md"
    )
    rules = {rule["id"]: rule for rule in catalog["rules"]}

    rule = rules["polymer_paper_project.poly-s-dib-bis-thiocumyl-motif"]
    assert rule["category"] == "chemistry_semantics"
    assert "Ar-C(CH3)2-Sx" in rule["rule"]
    assert "representative bis-thiocumyl" in rule["rule"]
    assert "current predominant bis-thiocumyl" not in rule["rule"]
    assert "single exact constitutional repeat" in rule["rule"]

    legibility = rules[
        "polymer_paper_project.chemical-skeletal-junction-legibility"
    ]
    assert legibility["category"] == "chemistry_semantics"
    assert "orthogonal cross" in legibility["rule"]
    assert "continuation bond" in legibility["rule"]

    zoom = rules["polymer_paper_project.chemical-zoom-integrity"]
    assert zoom["category"] == "chemistry_semantics"
    assert "enlarged vector scale" in zoom["rule"]
    assert "decorative colour seam mid-bond" in zoom["rule"]
    assert "alkene" in zoom["rule"]

    consistency = rules["polymer_paper_project.cross-panel-chemical-topology"]
    assert consistency["category"] == "chemistry_semantics"
    assert "same mandatory atom connectivity across panels" in consistency["rule"]
    assert "polysulfide directly to an aryl carbon" in consistency["rule"]

    evidence = rules[
        "polymer_paper_project.composition-schematic-evidence-boundary"
    ]
    assert evidence["category"] == "chemistry_semantics"
    assert "sulfur weight-percent sample names" in evidence["rule"]
    assert "qualitative artistic correlate" in evidence["rule"]
    assert "never report those glyph counts as measured sulfur rank" in evidence["rule"]

    traps = rules["polymer_paper_project.trap-landscape-evidence-boundary"]
    assert traps["category"] == "physics_semantics"
    assert "shallow states closer to the mobility edge" in traps["rule"]
    assert "bimodal shallow/deep DOS" in traps["rule"]
    assert "curve widths and amplitudes remain qualitative" in traps["rule"]
    assert "rectangular colour windows" in traps["rule"]
    assert "bounded energy bands" in traps["rule"]
    assert "carrier sign" in traps["rule"]

    binding = rules["polymer_paper_project.real-space-energy-binding"]
    assert binding["category"] == "physics_semantics"
    assert "same mixed population" in binding["rule"]
    assert "not trajectories" in binding["rule"]
    assert "Bind every localized core to a visible host trace" in binding["rule"]
    assert "free particle" in binding["rule"]
    assert "glowing particles" in binding["rule"]

    transient = rules[
        "polymer_paper_project.transient-power-law-evidence-boundary"
    ]
    assert transient["category"] == "physics_semantics"
    assert "plot log I against log t" in transient["rule"]
    assert "slope is -n" in transient["rule"]
    assert "high-n line must be visibly steeper" in transient["rule"]
    assert "Debye references" in transient["rule"]
    assert "measurement-like scatter markers" in transient["rule"]

    ispd = rules[
        "polymer_paper_project.ispd-decay-and-inversion-evidence-boundary"
    ]
    assert ispd["category"] == "physics_semantics"
    assert "measurement-to-inference chain" in ispd["rule"]
    assert "tail visibly above and separate from the time axis" in ispd["rule"]
    assert "exact finite-time zero" in ispd["rule"]
    assert "do not overlay measurement-like point markers" in ispd["rule"]
    assert "source-bound sampled coordinates" in ispd["rule"]
    assert "do not state a precise peak-height ratio" in ispd["rule"]

    titles = rules["polymer_paper_project.panel-title-object-language"]
    assert titles["category"] == "panel_layout"
    assert "object- or phenomenon-level panel titles" in titles["rule"]
    assert "generic process labels such as model or schematic" in titles["rule"]


def test_rule_catalog_rejects_malformed_rule_id(tmp_path: Path) -> None:
    path = tmp_path / "badid.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: polymer_paper_project\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: NoNamespaceDot\n"
        "    category: instrument_standard\n"
        "    rule: A rule whose id has no namespace dot.\n"
        "    source:\n"
        "      kind: hand_patch_commit\n"
        "      locator: x\n"
        "      quote: y\n"
        "    transfer_policy: use_as_constraint\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(authoring_rules.AuthoringRuleError, match="rule_id_invalid"):
        authoring_rules.load_rule_catalog(path)
