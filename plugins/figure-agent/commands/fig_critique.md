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

1. Run `uv run python3 scripts/critique_brief.py examples/<name>` to obtain the brief. The script verifies the build PNG is fresh against render sources (`<name>.tex`, `briefing.md`, `spec.yaml`, `polymer-paper-preamble.sty`); reference images, `coordinate_hints.yaml`, and authoring context are critique inputs and do not require a recompile by themselves. It then emits the briefing context, optional reference-conditioned authoring context, the line-numbered TikZ source, mandatory audit checklists, journal-grade quality axes, top-tier journal figure audit, journal-grade fresh re-audit assessment, and the severity/category rubric. If `spec.yaml.panels[]` declares both `reference_image` and `bbox_pdf_cm`, the brief also lists panel crop/reference image pairs for panel-grounded critique; if either field is missing, it emits a WARN and skips that panel comparison. If a participating reference path is missing (`spec.yaml.reference_image`, or panel `reference_image` with `bbox_pdf_cm`), STOP and fix the path or add the file before critique/export.

2. Use the **Read** tool on `examples/<name>/build/<name>.png` to load the rendered figure into the conversation. If the brief contains `## Per-panel reference contexts`, also Read every listed panel build crop and panel reference image. If the brief contains `## High-Zoom Visual Audit Crops`, also Read every listed crop before writing `critique.md`. These are original-pixel attention crops; inspect each one separately for the closed-set micro-defects named in the brief. Do not treat a clean full-render view as proof that high-zoom crops are clean. The host model inspects the images directly; do not call any external vision API.

3. Fill the mandatory audit checklists first, then fill `quality_axes` for every journal-grade audit axis, then fill `top_tier_audit`, then fill `journal_grade_assessment`. Do not collapse the axes into a single score. `publication_readiness` must be at least as severe as the most severe applicable upstream axis. Empty `audit_enumeration` blocks are invalid for schema v1.3, empty or malformed `quality_axes` blocks are invalid for schema v1.3, and missing/empty `top_tier_audit` slots are invalid for schema v1.3. Any `structural_defect`, `incomplete`, `BLOCKER`, `MAJOR`, `needs_patch`, or `block` item must either become a normal panel/top-level finding or be explicitly justified as `accept_simplification`, `human_review`, `revise_briefing`, or `block_release`. High-zoom crop findings must be represented as normal panel/top-level findings in schema v1.3; use the closed-set crop terms in `observation` until `micro_defects` schema v1.4 exists. Any `top_tier_audit.fail`, `top_tier_audit.needs_human`, or high-impact-blocking `top_tier_audit.weak` item must either become a normal panel/top-level finding that explicitly mentions `top_tier_audit.<slot_key>`, be represented in `quality_axes.blocking_items` with that same `top_tier_audit.<slot_key>` reference and a human/revise/block action, or be justified in `concrete_fix` as `accept_simplification`. For `patch` or `block_release` quality-axis actions, include the linked finding id in the relevant `blocking_items` entry, e.g. `C001 - <reason>`. Then apply the rubric from the brief — Sections A (physics correctness) and B (aesthetic placement) — and produce structured findings. For each finding, identify:
   - `severity`: BLOCKER / MAJOR / MINOR / NIT
   - `category`: structural / physics / label_placement / whitespace / hierarchy / palette / style
   - `tex_lines`: the source line numbers that need revision (cite from the line-numbered .tex in the brief)
   - `observation`: what is wrong, citing what is visible in the PNG
   - `suggested_fix`: a concrete edit to `<name>.tex`

4. Use the **Write** tool to create `examples/<name>/critique.md` with this exact format (YAML front-matter then Markdown body — schema v1.3):

```markdown
---
schema: figure-agent.critique.v1.3
fixture: <name>
generated_at: <ISO-8601 timestamp>
generator: critique_brief.py
generator_version: sha256:<generator hash>
rubric_version: figure-agent.critique-rubric.v1.3
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

6. **STOP.** Critique is **report-only**. Do not auto-edit `<name>.tex`; do not stage patches; do not re-compile. The author reads `critique.md`, decides which findings to apply, and edits manually. Auto-apply automation remains deferred until the patch-handoff loop has at least 10 real dogfood runs with conservative safety evidence.

For loop work, run `/fig_adjudicate <name>` after writing `critique.md` to
create `examples/<name>/critique_adjudication.yaml` with the current critique
hash. Review the generated decisions before marking exactly one finding as
`apply`.

Cost: 0원 (subscription tokens only). The plugin orchestrates; the host Claude Code main loop reads the PNG and produces the critique. `skills/figure-agent/SKILL.md` policy: delegate vision tasks to the host main loop; never call an external vision API directly.
