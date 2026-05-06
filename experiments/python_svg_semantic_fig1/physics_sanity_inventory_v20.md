# Fig1 Physics Sanity Inventory v20

## Scope

This inventory audits the current Fig1 L1 semantic renderer for basic academic/physics sanity. It is not a publication-grade theory validation layer and it is not a subjective visual-quality review. The target is narrower: prevent clearly wrong sign, direction, ordering, model-chain, authority, and claim errors that would be unacceptable under undergraduate-level electromagnetics, semiconductor/energy-level schematic conventions, and decay-model notation.

## Current Status

The project already has partial physics sanity coverage inside `src/verify_fig1_semantics.py` and `src/verify_fig1_causal_binding.py`. Those checks are useful but mixed into broader semantic, plot-grammar, and visual-policy gates. There is not yet an independent `physics-sanity` gate.

## Findings

| Area | Current Representation | Existing Check | Gap | v20 Classification |
| --- | --- | --- | --- | --- |
| Reference authority | `scene.reference.authority == "style_layout_evidence"` in `src/fig1_l1_scene.py`; docs state reference PNG is layout/style evidence only. | `verify_fig1_semantics.py`, `verify_fig1_scaffold_contract.py`, and `verify_fig1_causal_binding.py` reject `ground_truth` authority. | Covered, but belongs in a reusable physics/claim sanity checklist too because reference-overreach can create false scientific claims. | Already gated; mirror in physics sanity. |
| Band ordering | `BandDiagram` has LUMO at normalized y=0.18 and HOMO at y=0.82. Renderer draws energy arrow upward. | `verify_fig1_semantics.py::_check_trap_energy_model()` requires traps and DOS centers between LUMO/HOMO and ordered shallow-to-deep. | It does not explicitly fail if LUMO/HOMO labels are swapped while numeric order is preserved incorrectly by label. | Add explicit label/order invariant. |
| Trap positions | Shallow traps at 0.31-0.45; deep traps at 0.50-0.74; deep range label is 0.5-1.0 eV and quantitative status is schematic placeholder. | Existing check enforces bandgap containment, deep deeper than shallow, exact energy reference, exact placeholder status, and deep depth range. | Good coverage. Extend only if future payload adds real numeric units. | Already gated. |
| DOS dominance | Deep DOS width/area dominate shallow DOS; sampled DOS path is visible. | Existing checks enforce deep-to-shallow ratios, sampled DOS morphology, lobe separation, and label/lobe clearance. | Does not explicitly check positive width/height/sigma/sample parameters before geometry generation. | Add basic positive-parameter invariant. |
| P-E hysteresis | `PEHysteresisPlot` uses a schematic parametric hysteresis model with remanence=0.42. | Existing check enforces model id, sample count, and branch separation. | No explicit bounds for `remanence`, positive loop dimensions, or sample count minimum in a standalone physics layer. | Add basic model-parameter invariant. |
| Current decay | `PowerLawDecayPlot` uses `model="power_law_loglog"` and `slope=-0.72`; visible label is `I(t) ~ t^-n`. | Existing check enforces negative slope and monotonic decay on log-log axes. | It does not explicitly bind slope sign to `n > 0` wording, or reject a label that implies growth. | Add label/model consistency invariant. |
| Power-law to Debye chain | Causal chain is `I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)`. | `verify_fig1_causal_binding.py` enforces exact chain, Debye reference label, `tau_d`, and `g(Et)` output. | It does not explicitly state that Debye is a reference/bridge, not the same model as the power-law fit. It also cannot check tau positivity because no numeric tau payload exists. | Add claim-level invariant; defer numeric tau until payload exists. |
| ISPD / g(Et) output | `ISPDPlot.trap_depth_output == "g(Et)"`; interpretation panel and hero use g(Et)/trap-depth labels. | Causal binding and visibility gates require `g(Et)` output text. | Current gate does not scan docs/SVG for claims that `g(Et)` is a measured exact distribution in Fig1. | Add overclaim text scan. |
| Molecular origin | Origin payload records S-rich segments and mechanisms: chemical origin, physical origin, localized traps. | Causal binding checks the presence of these tokens. | This is narrative sanity, not proof of mechanism. Current docs mostly preserve that boundary. | Add claim-level overstatement scan only. |
| Probe charge sign | `PolymerCantilever.charge_sign == "+"`; charge markers visibly use `+`. | Existing verifier does not check charge sign against electrode sign. | Missing direct like-charge invariant. | Add physics sanity check. |
| Electrode sign | `Electrode.sign == "+"`; visible label is `+ V`. | Existing verifier checks electrode is to the right of the repulsion cue, not sign relation. | Missing relation check between `charge_sign`, `electrode.sign`, and `ForceArrow.sign_condition`. | Add physics sanity check. |
| Repulsion force arrow | `ForceArrow` starts near the charged cantilever and points right toward the electrode; metadata says `arrow_direction=reference_rightward_repulsion`; condition says trapped charge sign equals electrode sign. | Existing verifier checks arrow is rightward, electrode is to the right, and label is `Coulomb qE`. | Ambiguous physics target: for like charges, force on the charged cantilever should point away from the positive electrode, leftward. Rightward can be valid only if the arrow denotes force on the electrode or a reference-style repulsion field cue, but `ForceArrow` lacks `target`/`acted_on` semantics. | High-priority unresolved gap before strict fail. |
| Maxwell attraction cue | `MaxwellAttractionCue` is leftward and role is `secondary_reference_cue`. | Existing verifier enforces leftward, label, and secondary role. | Good coverage for visual hierarchy, but not tied to charge/electrode sign or force target. | Add relation to force hierarchy only after target semantics are clarified. |
| Forbidden framing | Terms like `actuator`, `bidirectional`, `force-balance` are forbidden in rendered SVG. | Existing semantic verifier scans rendered SVG text. | Does not scan docs/handbacks for stronger scientific overclaims. | Add docs/SVG claim scan in physics sanity. |
| Generated SVG semantic metadata | SVG embeds semantic IDs, kinds, payload geometry tokens, and role-tagged causal text. | Existing verifier checks semantic IDs, payload tokens, and visible causal roles. | Metadata has enough data for many sanity checks, but probe force target is not represented. | Add missing payload field before strict probe gate. |

## Already-Gated Basic Sanity

- Reference/scaffold must not become `ground_truth`.
- LUMO/HOMO trap bandgap containment is checked.
- Shallow traps must be shallower than deep traps.
- DOS shallow/deep centers must follow LUMO-to-HOMO energy order.
- Deep DOS lobe width/area must dominate shallow DOS.
- Power-law current decay must have negative slope.
- Computed decay path must monotonically decay with increasing log-time.
- P-E curve must have branch separation.
- Causal chain must preserve `I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)`.
- Maxwell attraction cue must stay secondary and leftward.
- Rendered SVG rejects forbidden force-balance/actuator framing terms.

## Not Yet Gated

- Explicit LUMO/HOMO label-to-position invariant.
- Positive numeric sanity for widths, heights, sigmas, sample counts, and remanence range.
- `I(t) ~ t^-n` label consistency with `slope < 0` and implied `n > 0`.
- Claim scan for overstatements such as exact/measured/proves when the payload is schematic.
- Probe force target semantics: force on cantilever vs force on electrode vs field cue.
- Direct charge/electrode sign relation check.
- Direct tie between `ForceArrow.sign_condition` and rendered charge/electrode signs.

## High-Priority Ambiguity

The probe panel is the only current physics-sanity risk that should not be turned into a hard fail until the semantic payload is clarified.

Current facts:

- trapped charge markers are `+`;
- electrode label is `+ V`;
- `ForceArrow.sign_condition` says trapped charge sign equals electrode sign;
- repulsion arrow points rightward toward the electrode;
- current visual copy says `Repulsion dominates over Maxwell attraction.`

For like charges, the force on the charged cantilever from the positive electrode should point away from the electrode. If the electrode is on the right, that force is leftward. A rightward red arrow is only physically defensible if it is explicitly the force on the electrode, the equal-and-opposite reaction force, or a schematic cue for separation/repulsive interaction rather than force-on-cantilever. The current `ForceArrow` payload does not say which one. v20 should not silently encode this ambiguity as correct.

Required follow-up before strict probe physics gate:

- Add or document `ForceArrow` target semantics, for example `force_target="electrode"` or `force_target="cantilever"`.
- If target is cantilever, the arrow should be leftward for `+` charge next to `+ V` electrode.
- If target is electrode, the current rightward arrow can pass, but the label should not imply force on the cantilever.
- If target is interaction cue, the verifier should check it as a cue, not as a vector force.

## Proposed v20 Contract

Create `physics_sanity_contract_v20.md` with three levels:

1. **Hard fail now**: basic invariants that are already unambiguous in the scene.
2. **Fail after payload clarification**: probe force target and charge/electrode vector logic.
3. **Document only**: advanced scientific correctness that Fig1 cannot validate, such as quantitative trap-depth extraction or real ISPD fit.

## Proposed v20 Gate

Create `src/verify_fig1_physics_sanity.py` as an independent gate and add it to `src/run_fig1_gates.py`.

Initial hard-fail checks:

- reference/scaffold authority is not `ground_truth`;
- band labels and normalized positions follow LUMO above HOMO in the drawn coordinate system;
- trap positions are inside bandgap and shallow precedes deep;
- DOS widths/heights/areas/sigma/sample counts are positive and deep dominance holds;
- P-E model dimensions are positive, samples are sufficient, and remanence is in a bounded schematic range;
- power-law model has `slope < 0`, label contains `t^-n`, and extracted parameter is `n`;
- causal chain order is exact and Debye remains a reference/bridge, not a measured equality;
- visible/docs text does not claim schematic payloads are exact measured distributions;
- `MaxwellAttractionCue.role == "secondary_reference_cue"`.

Probe checks should start as report-only or fail with a targeted message asking for force-target semantics, because the current payload is under-specified.

## Suggested Verification After Implementation

Run:

```bash
python experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py
python experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
python -m py_compile experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
```

Then intentionally mutate scene payloads in focused tests or script snippets to confirm failures for:

- swapped LUMO/HOMO labels or positions;
- shallow/deep trap inversion;
- non-negative power-law slope;
- invalid DOS/P-E dimensions;
- over-promoted `ground_truth` reference;
- probe like-charge force vector mismatch once target semantics exist.

## Bottom Line

The figure is not currently free of physics risk. Most energy, trap, DOS, and decay basics are already covered. The main gap is the absence of a dedicated physics-sanity gate and the under-specified probe force arrow. v20 should first formalize the contract, then add the independent gate, and only then harden probe vector logic after `ForceArrow` target semantics are explicit.
