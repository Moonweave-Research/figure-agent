# Fig1 v19 Reference Fidelity Audit

## Overall Judgment

The v18 figure has reached scaffold-level fidelity: the five-panel composition, center hero placement, support-to-hero flow, and visible causal narrative are recognizable against the reference. It has not reached reference-level completion. The remaining gap is mainly inside panels: lower visual density, weaker scientific plot conventions, less deliberate text hierarchy, and simplified device/diagram styling. The next work should strengthen reference-fidelity discipline before moving into broad reinterpretation.

## Panel Gap Table

| Panel | Current Fidelity | Main Gap | Classification | Next Direction |
| --- | --- | --- | --- | --- |
| Sulfur polymer origin | Medium | Structure is present, but the reference uses a stronger checklist/rationale block while v18 uses sparse causal dots and a thin footer. | Renderer polish + reinterpretation candidate | Keep current causal cue, but decide whether the lower block should stay semantic-causal or return closer to reference-style evidence bullets. |
| Electrical evidence | Medium-low | Plot frames are clean but too schematic; current decay lacks the reference's log-axis credibility and P-E lacks the bold axis/guide rhythm. | Renderer polish | Improve scientific plot visual grammar without adding dense real-plot ticks that violate existing schematic policy. |
| Center hero | Medium | Hero scaffold is strong, but the band/DOS region is less dense and less commanding than the reference; energy axis, trap tracks, and DOS lobe feel thinner. | Renderer polish | Defer to a hero-specific pass after plot grammar improves; avoid changing scaffold bounds first. |
| Interpretation | Low | This is the weakest panel. The reference has clear boxed causal steps, a large decay plot, Debye bridge, DOS output, and a strong conclusion band. v18 has the same semantics but too much whitespace and weak flow emphasis. | Renderer polish + possible scaffold limitation | Make this the first v19 implementation target. It stress-tests flow text, plot density, Debye bridge, DOS output, and conclusion hierarchy. |
| Macroscopic probe | Medium | Device composition is recognizable, but the reference has stronger cantilever head detail, charge markers embedded in the beam, clearer force-field rhythm, and a stronger footer. | Renderer polish + partial-reference candidate | Defer until user provides a preferred device/probe style or after interpretation/electrical are stronger. |

## Ranked Next Actions

1. **Interpretation panel first.** This panel has the largest gap and the highest tool value. Improve the existing causal chain presentation, enlarge the decay/Debye/DOS relationship, and restore a stronger conclusion band while keeping the current causal semantics.
2. **Electrical evidence second.** Improve schematic plot credibility: bolder axis hierarchy, clearer current-decay log cue, better slope guide placement, and stronger P-E/current visual balance. Keep the no-over-real-plot policy.
3. **Hero third.** After plot grammar improves, tune hero density: thicker trap-level rhythm, stronger DOS axis/label spacing, and more reference-like callout hierarchy.
4. **Origin/probe later.** These are good candidates for user-provided partial references because the right style depends more on taste: checklist evidence versus causal cue for origin, and exact device idiom for probe.

## Do Now

- Work only inside the existing scaffold.
- Choose at most two implementation targets: `interpretation_card` and `electrical_evidence_card`.
- Make renderer-local changes in `src/render_fig1_l1.py`.
- Preserve existing semantic payloads and causal roles.
- Keep visual policy checks separate in `src/fig1_visual_policies.py`.
- Add verifier coverage only for repeated structural failures, not absolute aesthetic preferences.

## Needs Partial Reference Or User Taste Decision

- Whether the origin panel should return closer to the reference's three evidence bullets or keep the v17/v18 causal relation strip.
- Whether the macroscopic probe should mimic the reference's cantilever head and beam charge placement more closely or move toward a cleaner journal schematic.
- Whether the hero callout should keep the v18 causal wording or use a more reference-like interpretive sentence.

## Proposed v19 Implementation Target

Start with an interpretation-panel polish pass, then an electrical-panel plot-grammar pass.

The interpretation pass should:

- increase the visual weight of the causal chain without creating new semantic content,
- make the decay plot, Debye bridge, and DOS output read as one pipeline,
- reduce unused whitespace,
- strengthen the conclusion cue,
- keep role-tagged causal text visible.

The electrical pass should:

- make the P-E and current-decay plots more credible as scientific schematics,
- improve axis/guide/label hierarchy,
- preserve the existing no-real-plot-frame constraints,
- keep `extract n` visible and readable.

## Verification Plan For Later Renderer Changes

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
python experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_scaffold_contract.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_causal_binding.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_causal_visibility.py
python experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
python -m py_compile experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
git status --short --branch
```

After visual output is settled, update `src/verify_fig1_baseline_hash.py` to the new SVG hash and add a handback describing the v19 visual boundary.
