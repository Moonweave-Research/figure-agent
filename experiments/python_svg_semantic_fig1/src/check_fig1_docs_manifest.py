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
    "src/run_fig1_gates.py",
    "src/verify_fig1_baseline_hash.py",
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
    "legacy annotated redraw",
    "layout/style evidence only",
    "scaffold_contract_v1",
    "causal diagram is not ground_truth",
    "intentional visual semantic update",
    "v18 readability polish",
    "v19 reference-fidelity pass",
    "v20 physics sanity inventory",
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

    print("fig1 docs manifest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
