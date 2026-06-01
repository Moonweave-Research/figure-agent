---
description: Vision critique of compiled figure via host Claude Code (no external API). Writes structured critique.md (YAML front-matter + Markdown summary) for one fixture.
---

Generate a structured vision critique for a compiled figure using the **host Claude Code main loop** as the vision LLM. No external Anthropic API call; subscription tokens only.

**Usage**: `/fig_critique <name>`

`<name>` maps to `examples/<name>/`.

Prerequisites:
- `examples/<name>/build/<name>.png` exists (run `/fig_compile <name>` first)
- `examples/<name>/briefing.md` exists

Steps:

1. Run `uv run python3 scripts/critique_brief.py examples/<name>` to obtain the brief. The script verifies the build PNG is fresh against render sources (`<name>.tex`, `briefing.md`, `spec.yaml`, `polymer-paper-preamble.sty`); reference images, `coordinate_hints.yaml`, optional `critique_reference_pack.yaml`, optional `aesthetic_intent.yaml`, optional `spec.yaml.paper_aesthetic_context` packs, optional `spec.yaml.journal_art_direction_playbook` packs, optional SVG polish aesthetic delta packs, and authoring context are critique inputs and do not require a recompile by themselves. It then emits the briefing context, optional reference-conditioned authoring context, optional reference-calibrated top-tier comparison, optional paper-wide aesthetic context, optional journal art-direction playbook, optional aesthetic intent calibration or v2 aesthetic lever grammar, optional SVG polish aesthetic delta comparison, the line-numbered TikZ source, mandatory audit checklists, journal-grade quality axes, top-tier journal figure audit, editorial art-direction audit, journal-grade fresh re-audit assessment, high-zoom/print-scale audit images, and the severity/category rubric. If `spec.yaml.panels[]` declares both `reference_image` and `bbox_pdf_cm`, the brief also lists panel crop/reference image pairs for panel-grounded critique; if either field is missing, it emits a WARN and skips that panel comparison. If a participating reference path is missing (`spec.yaml.reference_image`, or panel `reference_image` with `bbox_pdf_cm`), STOP and fix the path or add the file before critique/export.

2. Use the **Read** tool on `examples/<name>/build/<name>.png` to load the rendered figure into the conversation. If the brief contains `## Per-panel reference contexts`, also Read every listed panel build crop and panel reference image. If the brief contains `## High-Zoom Visual Audit Crops`, also Read every listed crop before writing `critique.md`. These are attention crops; inspect each one separately for the closed-set micro-defects named in the brief. Do not treat a clean full-render view as proof that high-zoom crops are clean. If the brief contains `## Print-Scale Audit Images`, also Read every listed reduced-scale image before setting `journal_polish` or `publication_readiness` to `pass`. If the brief contains `## SVG Polish Aesthetic Delta`, also Read every listed before/after/diff image before judging whether SVG polish improved the artifact or introduced a regression. If the brief contains `## Visual Clash Candidates`, account for every listed `VC###` candidate in `micro_defects[].visual_clash_ref`, either as an open defect or an explicit `accept_simplification`. If the brief contains `## Text Boundary Clash Candidates`, account for every listed `TB###` candidate in `micro_defects[].text_boundary_ref`, either as an open defect or an explicit `accept_simplification`. If the brief contains `## Label-Path Proximity Candidates`, account for every listed `LP###` candidate in `micro_defects[].label_path_ref`, either as an open defect or an explicit `accept_simplification`. For schema v1.8+, every crop id in `build/audit_crops/manifest.json.required_crop_ids` must also appear exactly once in `crop_audit_log`. The host model inspects the images directly; do not call any external vision API.

3. Fill the mandatory audit checklists first, then fill `quality_axes` for every journal-grade audit axis, then fill `top_tier_audit`, then fill `editorial_art_direction`, then fill `journal_grade_assessment`, then fill `micro_defects` and `crop_audit_log` from the High-Zoom Visual Audit Crops, Print-Scale Audit Images, Visual Clash Candidates, Text Boundary Clash Candidates, and Label-Path Proximity Candidates. If the brief contains `## SVG Polish Aesthetic Delta`, compare before/after/diff and explicitly decide whether journal polish improved, whether any label/readability/spacing issue regressed, whether scientific semantics changed, and whether the next route remains SVG polish, returns to TikZ semantic backport, or requires human art direction. If the brief contains `## Journal Art-Direction Playbook`, also fill `journal_art_direction_playbook_audit`; every declared design-center id must appear exactly once, generic "looks polished" prose is invalid, and existing top-tier/editorial/journal assessment rationale must cite exact playbook anchors with current-artifact evidence. If the brief contains `Aesthetic Lever Grammar`, also fill `aesthetic_lever_audit` exactly once for every declared lever id and cite exact aesthetic-intent anchors with current-artifact evidence in the calibrated top-tier/editorial slots. If the brief contains `## Paper-Wide Aesthetic Context`, `top_tier_audit.cross_panel_semantic_grammar`, `top_tier_audit.aesthetic_coherence`, and `editorial_art_direction.visual_identity` must each cite at least one exact paper-wide anchor from the section with current-artifact evidence; generic art-direction prose is invalid once the fixture opts in. Do not collapse the axes into a single score. If the brief contains `Reference-Calibrated Top-Tier Comparison`, fill `journal_grade_assessment.reference_calibration`; scores must cite the reference pack and remain advisory. If the brief prints schema `figure-agent.critique.v1.17`, fill `aesthetic_antipattern_audit`, `weakest_panel_coherence`, and `reference_learning_accountability`; each route must be explicit (`none`, `tikz_patch`, `svg_polish`, `semantic_backport`, or `human_art_direction`) and each non-`none` route must have concrete current-artifact evidence. `publication_readiness` must be at least as severe as the most severe applicable upstream axis. Empty `audit_enumeration` blocks, empty or malformed `quality_axes`, missing/empty `top_tier_audit` slots, missing/empty `editorial_art_direction` slots, missing `tikz_vs_svg_polish_trigger.recommended_path`, missing route-specific `tikz_vs_svg_polish_trigger` rationale (`remaining_tikz_lever`, `svg_polish_candidate_reason`, `semantic_backport_reason`, or `human_art_direction_reason` according to route), missing/malformed `micro_defects`, missing/malformed `crop_audit_log`, missing/malformed `journal_art_direction_playbook_audit` when requested, missing/malformed `aesthetic_lever_audit` when requested, or missing/malformed v1.17 grounded-audit fields are invalid. Any `structural_defect`, `incomplete`, `BLOCKER`, `MAJOR`, `needs_patch`, or `block` item must either become a normal panel/top-level finding or be explicitly justified as `accept_simplification`, `human_review`, `revise_briefing`, or `block_release`. Any `micro_defects` item with `severity: BLOCKER` or `severity: MAJOR` must either link to a normal panel/top-level finding through `linked_finding_id` or use `status: accept_simplification`. Use `label_backdrop_overflows_outline` when a label fill/backdrop rectangle extends outside an enclosing instrument-box outline, use `label_glyph_overlaps_internal_drawing` when label glyphs or their backdrop cross same-box internal drawing such as a display rectangle, axis line, meter needle, or separator, use `label_crosses_column_rule` when text crosses a declared column rule, use `label_crosses_panel_boundary` when text crosses a declared panel/row boundary, use `label_overflows_row_box` when text escapes a declared containing row or panel box, use `label_stacked_on_reference_line` when a label visually stacks on a declared reference/baseline, use `label_curve_near_label` when a semantic curve passes too close to a label, and use `label_path_near_miss` for other declared label/path clearance failures. For every `VC###` listed in Visual Clash Candidates, include exactly one `micro_defects` item with `visual_clash_ref: VC###`; for every `TB###` listed in Text Boundary Clash Candidates, include exactly one `micro_defects` item with `text_boundary_ref: TB###`; for every `LP###` listed in Label-Path Proximity Candidates, include exactly one `micro_defects` item with `label_path_ref: LP###`; for every `micro_defects` item with `status: accept_simplification`, set `accept_simplification_reason` (`false_positive`, `intentional_schematic`, `outside_target_region`, `convention_acceptable`, or `decorative_background`) and `accept_simplification_rationale`. In `crop_audit_log`, use `verdict: uncertain` for ambiguous crops and `verdict: defect` only when `linked_micro_defect_id` names the matching `micro_defects[].id`. Any `top_tier_audit.fail`, `top_tier_audit.needs_human`, or high-impact-blocking `top_tier_audit.weak` item must either become a normal panel/top-level finding that explicitly mentions `top_tier_audit.<slot_key>`, be represented in `quality_axes.blocking_items` with that same `top_tier_audit.<slot_key>` reference and a human/revise/block action, or be justified in `concrete_fix` as `accept_simplification`. Any `editorial_art_direction.needs_human` item must become a normal panel/top-level finding that explicitly mentions `editorial_art_direction.<slot_key>` or be represented in `quality_axes.blocking_items` with the same reference and a human/revise/block action; it cannot be hidden behind `accept_simplification`. Any high-impact-blocking `editorial_art_direction.fail` or `editorial_art_direction.weak` item follows the same link paths, or may use `accept_simplification` only for an intentional simplification. For `patch` or `block_release` quality-axis actions, include the linked finding id in the relevant `blocking_items` entry, e.g. `C001 - <reason>`. For `aesthetic_lever_audit`, non-passing entries must include `observed_anti_patterns`, non-`none` routes must match the declared `default_route`, route `tikz_patch` through a normal finding or quality-axis blocker, route `svg_polish` through `editorial_art_direction.tikz_vs_svg_polish_trigger` only when that trigger says `ready_for_svg_polish`, route `semantic_backport` through that same trigger only when it says `semantic_backport_required`, and route `human_art_direction` through `editorial_art_direction.human_art_direction_gate` as a visible human gate. Then apply the rubric from the brief — Sections A (physics correctness) and B (aesthetic placement) — and produce structured findings. For each finding, identify:
   - `severity`: BLOCKER / MAJOR / MINOR / NIT
   - `category`: structural / physics / label_placement / whitespace / hierarchy / palette / style
   - `tex_lines`: the source line numbers that need revision (cite from the line-numbered .tex in the brief)
   - `observation`: what is wrong, citing what is visible in the PNG
   - `suggested_fix`: a concrete edit to `<name>.tex`

4. Use the **Write** tool to create `examples/<name>/critique.md` with the exact YAML front-matter format printed by the brief. Fixtures without advanced opt-ins, or with legacy ungrounded inputs, may use the v1.10 shape below when the brief prints v1.10. Fixtures with v1.14-era opt-ins use the v1.14 shape printed by the brief. Grounded fixtures with audit crop manifests, undeclared geometry evidence, or SVG polish delta evidence use schema `figure-agent.critique.v1.17` and must include the v1.17 grounded-audit fields described above. Do not paste older schemas for grounded v1.17 critiques.

```markdown
---
schema: figure-agent.critique.v1.10
fixture: <name>
generated_at: <ISO-8601 timestamp>
generator: critique_brief.py
generator_version: sha256:<generator hash>
rubric_version: figure-agent.critique-rubric.v1.10
critique_input_hash: sha256:<input manifest hash>
verdict: ready | revise | block
audit_enumeration:
  structural_completeness:
    components:
      - component: <name>
        mount_support: yes|no|N/A
        rationale: "<one-line>"
        connections: "<endpoint audit>"
    missing_from_reference:
      - element: <name>
        status: intentional_omission | incomplete
        rationale: "<one-line>"
  label_target_matching:
    - label: "<text>"
      nearest_object: "<drawn-object-name>"
      intended_target: "<from-briefing-or-spec>"
      matches: true | false
      proposed_fix: "<concrete or empty if matches=true>"
  physical_plausibility:
    - check: cable_gravity | floating_components | spatial_proximity | direction_orientation | material_distinction
      finding: "<what was observed>"
      verdict: convention_acceptable | structural_defect
  conceptual_completeness:
    - element: <name>
      reference: provided_reference | briefing | reference_pack | not_provided
      severity: BLOCKER | MAJOR | MINOR | NIT
      proposed_action: add | expand | accept_simplification
quality_axes:
  message_storyline:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<message/story verdict rationale>"
    evidence: "<visible evidence, briefing/spec reference, or finding id>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  panel_role_coherence:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<panel role coherence summary>"
    evidence: "<panel ids and visual evidence>"
    panel_roles:
      - panel_id: "<id>"
        role: setup | mechanism | result | comparison | control | zoom | model | workflow | context
        role_quality: clear | weak | missing | redundant
        rationale: "<one-line>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  subregion_integration:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<sub-region/global integration summary>"
    evidence: "<subregion id, log evidence, or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  component_fidelity:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<component fidelity summary>"
    evidence: "<component audit ids or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  scientific_plausibility:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<scientific plausibility summary>"
    evidence: "<theory guard, briefing invariant, or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  composition_layout:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<layout/composition summary>"
    evidence: "<visible evidence, checker output, or finding id>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  label_annotation_semantics:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<label semantics summary>"
    evidence: "<label-target audit ids or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  journal_polish:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<polish summary>"
    evidence: "<visible evidence or export-scale issue>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  reference_fidelity:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<reference fidelity summary>"
    evidence: "<reference path, panel id, or reference_pack note>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  publication_readiness:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<conservative readiness summary>"
    evidence: "<axis verdict summary>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
top_tier_audit:
  first_glance_message:
    verdict: pass | weak | fail | needs_human
    finding: "<what a reader understands in 3/10/30 seconds>"
    concrete_fix: "<specific figure edit or accept_simplification>"
    blocks_high_impact: true | false
  target_journal_fit:
    verdict: pass | weak | fail | needs_human
    finding: "<fit to target journal or generic high-impact schematic standard>"
    concrete_fix: "<specific edit or human art-direction question>"
    blocks_high_impact: true | false
  novelty_claim_support:
    verdict: pass | weak | fail | needs_human
    finding: "<whether the visual supports the manuscript's central claim>"
    concrete_fix: "<specific edit or claim-figure alignment question>"
    blocks_high_impact: true | false
  figure_caption_coupling:
    verdict: pass | weak | fail | needs_human
    finding: "<whether caption and figure share the right explanatory burden>"
    concrete_fix: "<specific figure or caption-side recommendation>"
    blocks_high_impact: true | false
  visual_economy:
    verdict: pass | weak | fail | needs_human
    finding: "<unnecessary ink, redundant marks, or missing explanatory marks>"
    concrete_fix: "<delete, simplify, or emphasize one concrete element>"
    blocks_high_impact: true | false
  cross_panel_semantic_grammar:
    verdict: pass | weak | fail | needs_human
    finding: "<color, arrow, shape, texture, and label grammar across panels>"
    concrete_fix: "<one grammar normalization edit>"
    blocks_high_impact: true | false
  reader_misinterpretation_risk:
    verdict: pass | weak | fail | needs_human
    finding: "<most likely wrong interpretation by a qualified reader>"
    concrete_fix: "<specific guardrail label, spacing, or visual cue>"
    blocks_high_impact: true | false
  reduction_print_readability:
    verdict: pass | weak | fail | needs_human
    finding: "<1-column, 2-column, thumbnail, grayscale, or print weakness>"
    concrete_fix: "<specific scale/contrast/typography edit>"
    blocks_high_impact: true | false
  accessibility_color_robustness:
    verdict: pass | weak | fail | needs_human
    finding: "<colorblind/grayscale/contrast/texture redundancy assessment>"
    concrete_fix: "<specific redundant encoding or contrast edit>"
    blocks_high_impact: true | false
  aesthetic_coherence:
    verdict: pass | weak | fail | needs_human
    finding: "<style authority across line weights, detail level, depth cues>"
    concrete_fix: "<specific style-normalization edit>"
    blocks_high_impact: true | false
editorial_art_direction:
  hero_focus:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  narrative_choreography:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  illustration_readiness:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  abstraction_consistency:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  reference_class_fit:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  visual_identity:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  claim_payload_fit:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  aesthetic_risk:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
  tikz_vs_svg_polish_trigger:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
    recommended_path: continue_tikz | ready_for_svg_polish | needs_human_art_direction | semantic_backport_required
  human_art_direction_gate:
    verdict: pass | weak | fail | needs_human
    evidence: "<specific current-artifact evidence>"
    rationale: "<why this matters for target-journal illustration quality>"
    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
    blocks_high_impact: true | false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:<input manifest hash>
  benchmark_level: draft | solid_manuscript | high_impact_candidate | needs_human_art_direction | blocked
  confidence: low | medium | high
  blockers: []
  regression_detected: true | false
  regressions: []
  score_is_gateable: true | false
  next_quality_bottleneck: storyline | composition | component_fidelity | scientific_plausibility | label_semantics | polish | reference_fidelity | export_scale_readability | human_policy
  rationale: "<current artifact-only quality rationale>"
  overall_score: 0-100
  sub_scores:
    storyline: 0-100
    composition: 0-100
    component_fidelity: 0-100
    scientific_plausibility: 0-100
    label_semantics: 0-100
    polish: 0-100
    reference_fidelity: 0-100
    export_scale_readability: 0-100
  score_rationale: "<why these numbers describe only the current artifact>"
micro_defects:
  - id: M001
    crop: examples/<name>/build/audit_crops/<crop>.png
    kind: line_crosses_label | wire_crosses_label | arrow_tip_fused | label_target_detached | floating_semantic_cue | drawing_order_suspect | print_scale_unreadable | label_backdrop_overflows_outline | label_glyph_overlaps_internal_drawing | label_crosses_panel_boundary | label_crosses_column_rule | label_overflows_row_box | label_stacked_on_reference_line | label_curve_near_label | label_path_near_miss
    severity: BLOCKER | MAJOR | MINOR | NIT
    observation: "<visible micro-defect from a crop, print-scale image, or audit candidate>"
    linked_finding_id: "<P001/C001 or empty when accept_simplification>"
    visual_clash_ref: "<VC001 or empty when not from visual_clash.json>"
    text_boundary_ref: "<TB001 or empty when not from text_boundary_clash.json>"
    label_path_ref: "<LP001 or empty when not from label_path_proximity.json>"
    status: open | resolved | accept_simplification
    accept_simplification_reason: "<required enum when status=accept_simplification>"
    accept_simplification_rationale: "<required when status=accept_simplification>"
crop_audit_log:
  - crop_id: <crop id from build/audit_crops/manifest.json>
    path: build/audit_crops/<crop>.png
    source: <manifest source, e.g. full_render or visual_clash:VC001>
    inspected: true
    verdict: defect | no_defect | uncertain
    linked_micro_defect_id: "<M001 when verdict=defect or empty>"
    rationale: "<local geometry reason from direct crop inspection>"
panels:
  - id: <panel id>
    findings:
      - id: P001
        severity: MAJOR
        category: structural
        tex_lines: [42, 57]
        observation: "panel crop omits the ring geometry present in the panel reference"
        suggested_fix: "add the missing ring motif inside the panel bbox"
        status: open
findings:
  - id: C001
    severity: MAJOR
    category: structural | physics | label_placement | whitespace | hierarchy | palette | style
    tex_lines: [42, 57]
    observation: "trap depth arrow direction contradicts briefing §6"
    suggested_fix: "reverse arrow and relabel Et axis"
    status: open
---

# Vision Critique — <name>

<one-paragraph overall verdict, then per-finding prose discussion>
```

5. Before handing off to adjudication or loop work, run:

```bash
uv run python3 scripts/critique_lint.py <name>
```

If lint reports `duplicate_finding_id`, rename findings so ids are unique across
all panel and top-level findings. If lint reports `critique_contract`, repair
the malformed frontmatter or missing top-tier link before running
`critique_adjudication.py scaffold`.

Use `panels: []` when no panel-level reference comparison was available. Keep cross-panel and whole-figure issues in top-level `findings:`; do not move existing figure-level findings under `panels:`.

`verdict` rules:
- `ready` — zero BLOCKER and zero MAJOR findings
- `revise` — any MAJOR or MINOR findings (or NIT-only)
- `block` — at least one BLOCKER physics violation that makes the figure unsuitable for manuscript use

6. **STOP.** Critique is **report-only**. Do not auto-edit `<name>.tex`; do
not stage patches; do not re-compile. The author or outer agent reads
`critique.md`, runs `/fig_adjudicate <name>`, and decides which findings to
apply. `/fig_critique` never mutates source files. Any later patch-assisted
mutation must go through `/fig_loop` handoff plus the explicit bounded diff
executor documented in `/fig_loop`; generated auto-edits from critique prose
remain deferred until separately specified and dogfooded.

For loop work, run `/fig_adjudicate <name>` after writing `critique.md` to
create `examples/<name>/critique_adjudication.yaml` with the current critique
hash. Review the generated decisions before marking exactly one finding as
`apply`.

Cost: 0원 (subscription tokens only). The plugin orchestrates; the host Claude Code main loop reads the PNG and produces the critique. `skills/figure-agent/SKILL.md` policy: delegate vision tasks to the host main loop; never call an external vision API directly.
