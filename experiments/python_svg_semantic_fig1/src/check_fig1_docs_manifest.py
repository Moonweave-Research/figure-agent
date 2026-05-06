from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "README.md"
V14_HANDBACK = ROOT / "global_composition_asset_boundary_handback_v14.md"
V15_HANDBACK = ROOT / "scaffold_contract_handback_v15.md"
SCAFFOLD_CONTRACT = ROOT / "scaffold_contract_v1.md"
CAUSAL_BINDING = ROOT / "causal_reference_binding_v16.md"
V16_HANDBACK = ROOT / "causal_reference_handback_v16.md"
V17_HANDBACK = ROOT / "causal_visibility_handback_v17.md"
V18_HANDBACK = ROOT / "causal_readability_handback_v18.md"
V19_PROMPT = ROOT / "reference_fidelity_execution_prompt_v19.md"
V19_AUDIT = ROOT / "reference_fidelity_audit_v19.md"
V19_HANDBACK = ROOT / "reference_fidelity_handback_v19.md"
V20_PHYSICS_INVENTORY = ROOT / "physics_sanity_inventory_v20.md"
V20_PHYSICS_CONTRACT = ROOT / "physics_sanity_contract_v20.md"
V20_PHYSICS_HANDBACK = ROOT / "physics_sanity_gate_handback_v20.md"
V21_PROBE_OPTIONS = ROOT / "probe_force_target_options_v21.md"
V21_PROBE_HANDBACK = ROOT / "probe_force_target_handback_v21.md"
V22_VISUAL_REPORT = ROOT / "fig1_visual_judgment_report.md"
V22_VISUAL_HANDBACK = ROOT / "visual_judgment_report_handback_v22.md"

REQUIRED_MANIFEST_TOKENS = (
    "fig1_reference_semantic.svg",
    "fig1_reference_semantic.png",
    "reference_vs_fig1_reference_semantic.png",
    "visual_layout.yaml",
    "reference_layout_spec_v1.md",
    "scaffold_contract_v1.md",
    "causal_reference_binding_v16.md",
    "src/engine/scaffold.py",
    "src/verify_fig1_scaffold_contract.py",
    "src/verify_fig1_causal_binding.py",
    "src/verify_fig1_causal_visibility.py",
    "src/verify_fig1_physics_sanity.py",
    "src/run_fig1_gates.py",
    "src/verify_fig1_baseline_hash.py",
    "src/test_fig1_physics_sanity.py",
    "src/report_fig1_visual_judgment.py",
    "src/test_fig1_visual_judgment_report.py",
    "dos_reference_schematic_handback_v9.md",
    "dos_density_profile_handback_v10.md",
    "dos_schematic_polish_handback_v11.md",
    "visual_cohesion_handback_v12.md",
    "support_panel_cohesion_handback_v13.md",
    "global_composition_asset_boundary_handback_v14.md",
    "scaffold_contract_handback_v15.md",
    "causal_reference_handback_v16.md",
    "causal_visibility_handback_v17.md",
    "causal_readability_handback_v18.md",
    "reference_fidelity_execution_prompt_v19.md",
    "reference_fidelity_audit_v19.md",
    "reference_fidelity_handback_v19.md",
    "physics_sanity_inventory_v20.md",
    "physics_sanity_contract_v20.md",
    "physics_sanity_gate_handback_v20.md",
    "probe_force_target_options_v21.md",
    "probe_force_target_handback_v21.md",
    "fig1_visual_judgment_report.md",
    "visual_judgment_report_handback_v22.md",
    "legacy annotated redraw",
    "layout/style evidence only",
    "scaffold_contract_v1",
    "causal diagram is not ground_truth",
    "intentional visual semantic update",
    "v18 readability polish",
    "v19 reference-fidelity pass",
    "v20 physics sanity inventory",
    "v20 physics sanity layer",
    "v21 probe force-target pass",
    "v22 visual judgment report layer",
    "report-only inspection surface",
    "cantilever_leftward_repulsion",
    "force_target",
    "baseline hash",
)

REQUIRED_V14_TOKENS = (
    "Reusable asset candidates",
    "Fig1-only boundaries",
    "Human visual review",
)

REQUIRED_SCAFFOLD_CONTRACT_TOKENS = (
    "Source file format: JSON object",
    "Normalized schema version: `scaffold_contract_v1`",
    "Human one-line sign-off",
    "not scientific ground truth",
)

REQUIRED_V15_TOKENS = (
    "not a visual polish pass",
    "ScaffoldContract.schema_version == \"scaffold_contract_v1\"",
    "layout/style evidence",
    "composition-grade",
    "Deferred Cleanup",
)

REQUIRED_CAUSAL_BINDING_TOKENS = (
    "visual scaffold authority",
    "causal/semantic reference",
    "not ground_truth",
    "not a pixel-tracing target",
    "I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)",
    "S-rich segments",
    "localized traps",
    "converged trap-depth picture",
)

REQUIRED_V16_TOKENS = (
    "not a visual polish pass",
    "visual scaffold authority",
    "semantic reference",
    "not ground_truth",
    "not a pixel-tracing target",
    "Human visual review",
)

REQUIRED_V17_TOKENS = (
    "intentional visual semantic update",
    "not a new scaffold",
    "S-rich segments",
    "localized traps",
    "extract n",
    "Converged trap-depth picture",
    "previous hash",
    "new hash",
    "Human visual review",
)

REQUIRED_V18_TOKENS = (
    "readability polish",
    "no new semantic content",
    "new scaffold",
    "existing visible causal cues",
    "No absolute min-font-size verifier",
    "Human visual review",
    "previous hash",
    "new hash",
    "src/run_fig1_gates.py",
    "src/verify_fig1_baseline_hash.py",
    "b43c192481c799e895bd616b57fdd3731dfc58b3bf2d5fcee932d204592c207f",
)

REQUIRED_V19_PROMPT_TOKENS = (
    "panel-by-panel reference fidelity audit",
    "Do not create a new scaffold",
    "Do not add new semantic content",
    "Do not pixel-trace the reference image",
    "sulfur polymer origin",
    "electrical evidence",
    "center hero",
    "interpretation",
    "macroscopic probe",
)

REQUIRED_V19_AUDIT_TOKENS = (
    "Interpretation panel first",
    "Electrical evidence second",
    "Do Now",
    "Needs Partial Reference Or User Taste Decision",
    "interpretation_card",
    "electrical_evidence_card",
)

REQUIRED_V19_HANDBACK_TOKENS = (
    "reference-fidelity polish pass",
    "interpretation and electrical evidence panels",
    "No new scaffold",
    "No new semantic content",
    "Human visual review",
    "previous hash",
    "new hash",
    "55702be313ca70192560a569c8d45949b575e5bfa960252acd9e72f7294e230a",
)

REQUIRED_V20_PHYSICS_INVENTORY_TOKENS = (
    "basic academic/physics sanity",
    "not a publication-grade theory validation layer",
    "independent `physics-sanity` gate",
    "LUMO/HOMO",
    "I(t) ~ t^-n",
    "Debye exp(-t/tau)",
    "g(Et)",
    "ForceArrow",
    "force_target",
    "High-Priority Ambiguity",
)

REQUIRED_V20_PHYSICS_CONTRACT_TOKENS = (
    "not publication-grade theory validation",
    "layout/style evidence only",
    "Hard Fail Now",
    "Fail After Payload Clarification",
    "Document Only",
    "LUMO/HOMO",
    "I(t) ~ t^-n",
    "Debye exp(-t/tau)",
    "g(Et)",
    "ForceArrow",
    "force_target",
    "Human visual review",
)

REQUIRED_V20_PHYSICS_HANDBACK_TOKENS = (
    "independent `physics-sanity` gate",
    "src/verify_fig1_physics_sanity.py",
    "src/test_fig1_physics_sanity.py",
    "src/run_fig1_gates.py",
    "No new scaffold",
    "No new semantic content",
    "ForceArrow",
    "force_target",
    "warning",
    "Human visual review",
    "previous hash",
    "new hash",
)

REQUIRED_V21_PROBE_OPTIONS_TOKENS = (
    "force_target=\"cantilever\"",
    "force_target=\"electrode\"",
    "force_target=\"interaction_cue\"",
    "Decision: `force_target=\"cantilever\"`",
    "Reference divergence acknowledged",
    "layout/style evidence only",
    "not ground_truth",
    "cantilever_leftward_repulsion",
    "Human visual review",
)

REQUIRED_V21_PROBE_HANDBACK_TOKENS = (
    "semantic contract migration",
    "No new scaffold",
    "force_target=\"cantilever\"",
    "Force on cantilever",
    "cantilever_leftward_repulsion",
    "charge/electrode separation",
    "force-arrow start proximity",
    "bend-state consistency",
    "previous hash",
    "new hash",
    "0ceca15c136d21cb73676dcd91fb9a50aec54e41e05cd2b541dba0caef3b8edf",
    "Human visual review",
)

REQUIRED_V22_VISUAL_REPORT_TOKENS = (
    "Fig1 Visual Judgment Report v22",
    "report-only visual judgment layer",
    "Human visual review remains required",
    "Panel Density",
    "Text / Text Near-Collision",
    "Text / Shape Conflict",
    "Visual Hierarchy",
    "Reading Order",
    "Reference Divergence",
    "Human Review Prompts",
    "force_target=cantilever",
    "cantilever_leftward_repulsion",
)

REQUIRED_V22_VISUAL_HANDBACK_TOKENS = (
    "report-only visual judgment layer",
    "src/report_fig1_visual_judgment.py",
    "src/test_fig1_visual_judgment_report.py",
    "fig1_visual_judgment_report.md",
    "Panel Density",
    "Text / Text Near-Collision",
    "Text / Shape Conflict",
    "Visual Hierarchy",
    "Reading Order",
    "Reference Divergence",
    "Human Review Prompts",
    "No absolute min-font-size verifier",
    "force_target=cantilever",
    "cantilever_leftward_repulsion",
    "Human visual review remains required",
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    if not MANIFEST.exists():
        return _fail(f"missing experiment manifest: {MANIFEST}")
    manifest = MANIFEST.read_text()
    for token in REQUIRED_MANIFEST_TOKENS:
        if token not in manifest:
            return _fail(f"experiment manifest missing token: {token}")

    if not V14_HANDBACK.exists():
        return _fail(f"missing v14 asset-boundary handback: {V14_HANDBACK}")
    handback = V14_HANDBACK.read_text()
    for token in REQUIRED_V14_TOKENS:
        if token not in handback:
            return _fail(f"v14 handback missing asset-boundary token: {token}")

    if not SCAFFOLD_CONTRACT.exists():
        return _fail(f"missing scaffold contract doc: {SCAFFOLD_CONTRACT}")
    scaffold_contract = SCAFFOLD_CONTRACT.read_text()
    for token in REQUIRED_SCAFFOLD_CONTRACT_TOKENS:
        if token not in scaffold_contract:
            return _fail(f"scaffold contract doc missing token: {token}")

    if not V15_HANDBACK.exists():
        return _fail(f"missing v15 scaffold handback: {V15_HANDBACK}")
    v15_handback = V15_HANDBACK.read_text()
    for token in REQUIRED_V15_TOKENS:
        if token not in v15_handback:
            return _fail(f"v15 scaffold handback missing token: {token}")

    if not CAUSAL_BINDING.exists():
        return _fail(f"missing causal binding doc: {CAUSAL_BINDING}")
    causal_binding = CAUSAL_BINDING.read_text()
    for token in REQUIRED_CAUSAL_BINDING_TOKENS:
        if token not in causal_binding:
            return _fail(f"causal binding doc missing token: {token}")

    if not V16_HANDBACK.exists():
        return _fail(f"missing v16 causal handback: {V16_HANDBACK}")
    v16_handback = V16_HANDBACK.read_text()
    for token in REQUIRED_V16_TOKENS:
        if token not in v16_handback:
            return _fail(f"v16 causal handback missing token: {token}")

    if not V17_HANDBACK.exists():
        return _fail(f"missing v17 visibility handback: {V17_HANDBACK}")
    v17_handback = V17_HANDBACK.read_text()
    for token in REQUIRED_V17_TOKENS:
        if token not in v17_handback:
            return _fail(f"v17 visibility handback missing token: {token}")

    if not V18_HANDBACK.exists():
        return _fail(f"missing v18 readability handback: {V18_HANDBACK}")
    v18_handback = V18_HANDBACK.read_text()
    for token in REQUIRED_V18_TOKENS:
        if token not in v18_handback:
            return _fail(f"v18 readability handback missing token: {token}")

    if not V19_PROMPT.exists():
        return _fail(f"missing v19 reference-fidelity prompt: {V19_PROMPT}")
    v19_prompt = V19_PROMPT.read_text()
    for token in REQUIRED_V19_PROMPT_TOKENS:
        if token not in v19_prompt:
            return _fail(f"v19 reference-fidelity prompt missing token: {token}")

    if not V19_AUDIT.exists():
        return _fail(f"missing v19 reference-fidelity audit: {V19_AUDIT}")
    v19_audit = V19_AUDIT.read_text()
    for token in REQUIRED_V19_AUDIT_TOKENS:
        if token not in v19_audit:
            return _fail(f"v19 reference-fidelity audit missing token: {token}")

    if not V19_HANDBACK.exists():
        return _fail(f"missing v19 reference-fidelity handback: {V19_HANDBACK}")
    v19_handback = V19_HANDBACK.read_text()
    for token in REQUIRED_V19_HANDBACK_TOKENS:
        if token not in v19_handback:
            return _fail(f"v19 reference-fidelity handback missing token: {token}")

    if not V20_PHYSICS_INVENTORY.exists():
        return _fail(f"missing v20 physics sanity inventory: {V20_PHYSICS_INVENTORY}")
    v20_inventory = V20_PHYSICS_INVENTORY.read_text()
    for token in REQUIRED_V20_PHYSICS_INVENTORY_TOKENS:
        if token not in v20_inventory:
            return _fail(f"v20 physics sanity inventory missing token: {token}")

    if not V20_PHYSICS_CONTRACT.exists():
        return _fail(f"missing v20 physics sanity contract: {V20_PHYSICS_CONTRACT}")
    v20_contract = V20_PHYSICS_CONTRACT.read_text()
    for token in REQUIRED_V20_PHYSICS_CONTRACT_TOKENS:
        if token not in v20_contract:
            return _fail(f"v20 physics sanity contract missing token: {token}")

    if not V20_PHYSICS_HANDBACK.exists():
        return _fail(f"missing v20 physics sanity handback: {V20_PHYSICS_HANDBACK}")
    v20_handback = V20_PHYSICS_HANDBACK.read_text()
    for token in REQUIRED_V20_PHYSICS_HANDBACK_TOKENS:
        if token not in v20_handback:
            return _fail(f"v20 physics sanity handback missing token: {token}")

    if not V21_PROBE_OPTIONS.exists():
        return _fail(f"missing v21 probe force target options: {V21_PROBE_OPTIONS}")
    v21_options = V21_PROBE_OPTIONS.read_text()
    for token in REQUIRED_V21_PROBE_OPTIONS_TOKENS:
        if token not in v21_options:
            return _fail(f"v21 probe force target options missing token: {token}")

    if not V21_PROBE_HANDBACK.exists():
        return _fail(f"missing v21 probe force target handback: {V21_PROBE_HANDBACK}")
    v21_handback = V21_PROBE_HANDBACK.read_text()
    for token in REQUIRED_V21_PROBE_HANDBACK_TOKENS:
        if token not in v21_handback:
            return _fail(f"v21 probe force target handback missing token: {token}")

    if not V22_VISUAL_REPORT.exists():
        return _fail(f"missing v22 visual judgment report: {V22_VISUAL_REPORT}")
    v22_report = V22_VISUAL_REPORT.read_text()
    for token in REQUIRED_V22_VISUAL_REPORT_TOKENS:
        if token not in v22_report:
            return _fail(f"v22 visual judgment report missing token: {token}")

    if not V22_VISUAL_HANDBACK.exists():
        return _fail(f"missing v22 visual judgment handback: {V22_VISUAL_HANDBACK}")
    v22_handback = V22_VISUAL_HANDBACK.read_text()
    for token in REQUIRED_V22_VISUAL_HANDBACK_TOKENS:
        if token not in v22_handback:
            return _fail(f"v22 visual judgment handback missing token: {token}")

    print("fig1 docs manifest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
