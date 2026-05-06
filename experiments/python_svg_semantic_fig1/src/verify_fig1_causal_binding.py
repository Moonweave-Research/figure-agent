from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
BINDING_DOC = ROOT / "causal_reference_binding_v16.md"
HANDBACK = ROOT / "causal_reference_handback_v16.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

EXPECTED_CHAIN = (
    "I(t) ~ t^-n",
    "n",
    "Debye exp(-t/tau)",
    "tau_d",
    "g(Et)",
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _read_required(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text()


def main() -> int:
    try:
        from fig1_l1_scene import build_scene
    except ModuleNotFoundError as exc:
        return _fail(f"missing Fig1 scene module: {exc}")

    try:
        binding_doc = _read_required(BINDING_DOC)
        handback = _read_required(HANDBACK)
    except FileNotFoundError as exc:
        return _fail(f"missing causal reference document: {exc.filename}")

    scene = build_scene()

    if scene.reference.authority == "ground_truth":
        return _fail("visual scaffold reference must not become ground_truth")
    if scene.reference.source != "experiments/python_svg_semantic_fig1/reference/source_variant_aesthetic_ref.png":
        return _fail("visual scaffold authority moved away from the original aesthetic reference")
    if str(BINDING_DOC) not in scene.source_files:
        return _fail("scene source files do not include the v16 causal binding document")

    origin = scene.object_by_id("sulfur_polymer_origin").payload
    if "S-rich segments" not in getattr(origin, "causal_segments", ()):
        return _fail("origin payload missing S-rich segment causal binding")
    mechanisms = tuple(getattr(origin, "trap_origin_mechanisms", ()))
    for token in ("chemical origin", "physical origin", "localized traps"):
        if not any(token in mechanism for mechanism in mechanisms):
            return _fail(f"origin payload missing trap-origin mechanism: {token}")

    decay = scene.object_by_id("power_law_decay").payload
    if getattr(decay, "causal_role", "") != "experiment_current_decay_to_power_law_exponent":
        return _fail("power-law decay payload missing experiment-to-exponent causal role")
    if getattr(decay, "extracted_parameter", "") != "n":
        return _fail("power-law decay payload missing extracted parameter n")

    flow = scene.object_by_id("trap_model_flow").payload
    if tuple(getattr(flow, "causal_chain", ())) != EXPECTED_CHAIN:
        return _fail("trap model flow causal chain does not match the v16 reference")
    if getattr(flow, "debye_reference_label", "") != "Discharge Debye reference":
        return _fail("trap model flow missing Debye reference binding")
    if getattr(flow, "delay_parameter", "") != "tau_d":
        return _fail("trap model flow missing tau_d delay binding")
    if getattr(flow, "output_distribution", "") != "g(Et)":
        return _fail("trap model flow missing g(Et) output binding")

    ispd = scene.object_by_id("ispd_plot").payload
    if getattr(ispd, "trap_depth_output", "") != "g(Et)":
        return _fail("ISPD payload missing trap-depth output binding")

    hero = scene.object_by_id("deep_trap_hero").payload
    if getattr(hero, "causal_role", "") != "converged_trap_depth_picture":
        return _fail("hero payload missing converged trap-depth picture role")
    if getattr(hero, "converged_picture_label", "") != "converged trap-depth picture":
        return _fail("hero payload missing converged trap-depth picture label")

    required_doc_tokens = (
        "visual scaffold authority",
        "causal/semantic reference",
        "not ground_truth",
        "not a pixel-tracing target",
        "I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)",
        "S-rich segments",
        "localized traps",
        "converged trap-depth picture",
    )
    combined_docs = binding_doc + "\n" + handback
    for token in required_doc_tokens:
        if token not in combined_docs:
            return _fail(f"causal binding docs missing token: {token}")

    print("fig1 causal binding passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
