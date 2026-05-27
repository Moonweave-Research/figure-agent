# Journal Art-Direction Playbook Design

## Context

`figure-agent` has become strong at preventing broken figures from passing
silently. It now checks compile/export/status freshness, high-zoom crops,
visual-clash/text-boundary/label-path evidence, reference-calibrated critique,
fixture-local aesthetic intent, aesthetic lever accounting, SVG-polish
readiness, and paper-wide aesthetic coherence.

That still leaves a different class of failure: a figure can be technically
valid, semantically grounded, and visually uncluttered while still reading as
generic, immature, preset-like, or not quite journal-art-directed. The user
feedback is consistent: top-tier figures require the host LLM to reason about
abstract qualities such as restraint, typography authority, white-space
breathing, hierarchy, anti-generic finish, and when hand-crafted polish is
appropriate.

The current plugin can ask whether a figure is correct. It can also require a
fixture-specific aesthetic lever audit when `aesthetic_intent.yaml` uses schema
v2. It does not yet provide a reusable journal-level design vocabulary that
explains what "not childish", "professional", "clean", "Nature-like", or
"hand-crafted but restrained" means in operational critique terms.

## Existing Layers

The new layer must fit these existing responsibilities:

- `aesthetic_intent.yaml`: fixture-local target and route levers.
- `paper_aesthetic_context`: manuscript-series coherence across fixtures.
- `critique_reference_pack.yaml`: visual/reference calibration for a fixture.
- `top_tier_audit`: high-impact journal audit slots.
- `editorial_art_direction`: art-direction route and risk slots.
- `journal_grade_assessment`: advisory scoring, never a release bypass.
- SVG polish manifests and recipes: bounded post-export optical edits.

The missing layer is reusable journal art-direction language. It should tell
the host critique what to look for before it says "looks polished".

## Non-Goals

- No figure drawing.
- No automatic TikZ patching.
- No automatic SVG polish.
- No external web or reference scraping.
- No numeric score gate.
- No release, accepted, golden, export, or publication-provenance mutation.
- No claim that passing the playbook guarantees Nature/Science acceptance.
- No hidden global playbook that silently applies to every fixture.
- No replacement for fixture-local `aesthetic_intent.yaml` or
  `paper_aesthetic_context`.

## Design Principle

Treat top-tier taste as a bounded critique vocabulary, not as an absolute
quality oracle.

The plugin should force the host LLM to enumerate a small set of reusable
journal-art-direction checks:

1. Which professional positive signal is visible?
2. Which immature or generic anti-pattern is present or absent?
3. Which evidence in the current artifact supports the verdict?
4. Which route is appropriate: keep patching TikZ, perform bounded SVG polish,
   backport semantics, or ask for human art direction?
5. Which edit class is forbidden because it would change scientific meaning or
   violate venue restraint?

The result is not "the plugin makes Nature figures automatically." The result
is that the critique loop asks the right questions and cannot silently pass
generic taste prose.

## Contract Location

Add optional playbook packs under:

```text
examples/_journal_art_direction_playbooks/<playbook_id>.yaml
```

Fixtures opt in explicitly through `spec.yaml`:

```yaml
journal_art_direction_playbook: nature-communications-main-text-v1
```

The explicit fixture opt-in is deliberate. Test fixtures, dogfood fixtures, and
paper figures coexist in `examples/`; an ambient default would create false
coupling. A future paper-context v2 may reference a default playbook, but v1
keeps the route explicit and easy to reason about.

## Pack Schema

```yaml
schema: figure-agent.journal-art-direction-playbook.v1
playbook_id: nature-communications-main-text-v1
target_journal: Nature Communications
venue_context: main_text
visual_maturity: restrained
design_center:
  - id: editorial_restraint
    dimension: maturity
    instruction: "Prefer compact, controlled scientific illustration over decorative emphasis."
    priority: required
    positive_signals:
      - "labels are compact and subordinate to the visual evidence"
    anti_patterns:
      - "poster-like saturation or decorative gradients without semantic role"
    evidence_prompts:
      - "Would this panel still look professional at journal print scale?"
  - id: typography_authority
    dimension: typography
    instruction: "Use label hierarchy that feels typeset, not slide-like."
    priority: required
    positive_signals:
      - "math subscripts and labels align without crowding or optical heaviness"
    anti_patterns:
      - "large explanatory labels competing with the scientific object"
    evidence_prompts:
      - "Are labels visually quiet while remaining readable?"
  - id: whitespace_breathing
    dimension: whitespace
    instruction: "Keep local density controlled enough that the reader can parse structure without hunting."
    priority: recommended
    positive_signals:
      - "busy regions still have visible resting space around labels and key objects"
    anti_patterns:
      - "small gaps that technically avoid overlap but still feel stacked or cramped"
    evidence_prompts:
      - "Name the densest region and whether its spacing still feels intentional."
anti_patterns:
  - id: toy_schematic
    dimension: maturity
    severity: MAJOR
    pattern: "oversized arrows, generic rounded blocks, or cartoon emphasis"
    preferred_route: continue_tikz
  - id: preset_macro_feel
    dimension: hand_craft
    severity: MINOR
    pattern: "repeated elements look mechanically identical where organic variance is expected"
    preferred_route: ready_for_svg_polish
positive_signals:
  - id: restrained_hero
    dimension: hierarchy
    signal: "one clear first-fixation element without making the panel poster-like"
    evidence_prompt: "Name the first visual object noticed and why it is appropriate."
  - id: print_scale_calm
    dimension: typography
    signal: "labels remain readable and quiet at target print scale"
    evidence_prompt: "Check the print-scale crop before claiming typography authority."
polish_route_rules:
  - id: tikz_until_semantics_close
    condition: "Scientific structure, labels, or relative placement still need semantic changes."
    recommended_path: continue_tikz
    forbidden_actions:
      - "hide semantic ambiguity behind SVG polish"
  - id: svg_for_optical_finish
    condition: "Semantics are stable, but anti-aliasing, spacing, stroke joins, or glyph alignment limit finish."
    recommended_path: ready_for_svg_polish
    forbidden_actions:
      - "move scientific components or alter labels semantically"
human_review_triggers:
  - id: taste_direction_conflict
    condition: "The playbook and fixture aesthetic intent recommend incompatible visual maturity."
    severity: MAJOR
```

## Closed Enums

- `target_journal`: reuse `aesthetic_intent.py` target journals.
- `venue_context`: `main_text`, `extended_data`, `supplementary`,
  `graphical_abstract`, `cover_like`.
- `visual_maturity`: reuse `aesthetic_intent.py` visual maturities.
- `dimension`: `maturity`, `hierarchy`, `whitespace`, `typography`,
  `color`, `line_weight`, `component_detail`, `hand_craft`,
  `cross_panel_consistency`, `polish_route`.
- `priority`: `required`, `recommended`, `optional`.
- `severity`: `BLOCKER`, `MAJOR`, `MINOR`, `NIT`.
- `recommended_path` / `preferred_route`: `continue_tikz`,
  `ready_for_svg_polish`, `semantic_backport_required`,
  `needs_human_art_direction`.

## Validation Rules

- `schema` must equal `figure-agent.journal-art-direction-playbook.v1`.
- `spec.yaml.journal_art_direction_playbook` and `playbook_id` must be safe ids:
  start with an ASCII letter or number, then use only ASCII letters, numbers,
  `_`, `.`, and `-`; no slash, backslash, whitespace, or hidden-file names.
- `playbook_id` must match the filename stem.
- `target_journal`, `venue_context`, and `visual_maturity` must use closed
  enums.
- `design_center` must contain 3-10 unique items.
- Each design-center item requires non-empty `id`, `dimension`, `instruction`,
  `priority`, `positive_signals`, `anti_patterns`, and `evidence_prompts`.
- `anti_patterns` must contain 2-10 unique items.
- Each anti-pattern requires non-empty `id`, `dimension`, `severity`,
  `pattern`, and `preferred_route`.
- `positive_signals` must contain 2-10 unique items.
- Each positive signal requires non-empty `id`, `dimension`, `signal`, and
  `evidence_prompt`.
- `polish_route_rules` must contain 2-8 unique items and must include at least
  one `continue_tikz` rule and one `ready_for_svg_polish` rule.
- `human_review_triggers` must contain 1-6 unique items.
- Unknown future mapping fields may be preserved by the parser but must not
  bypass required-field validation.

The size limits are intentional. A playbook that tries to enumerate every
possible taste judgment becomes another attention-management problem.

## Critique Brief Behavior

When a fixture opts in, `/fig_critique` emits a new section after
`## Paper-Wide Aesthetic Context` and before fixture-local
`## Aesthetic Intent Calibration`:

```markdown
## Journal Art-Direction Playbook
Host LLM MUST use this playbook as the journal-level taste vocabulary for the
current critique. Generic claims such as "looks polished" are invalid unless
they cite exact playbook anchors and current-artifact evidence.

- Playbook id: nature-communications-main-text-v1
- Target journal: Nature Communications
- Venue context: main_text
- Visual maturity: restrained

### Design Center
- editorial_restraint priority=required dimension=maturity:
  Prefer compact, controlled scientific illustration over decorative emphasis.
  positive_signals: labels are compact and subordinate to the visual evidence
  anti_patterns: poster-like saturation or decorative gradients without semantic role
  evidence_prompts: Would this panel still look professional at journal print scale?

### Anti-Patterns
- toy_schematic severity=MAJOR route=continue_tikz:
  oversized arrows, generic rounded blocks, or cartoon emphasis

### Positive Signals
- restrained_hero dimension=hierarchy:
  one clear first-fixation element without making the panel poster-like

### Polish Route Rules
- tikz_until_semantics_close path=continue_tikz:
  Scientific structure, labels, or relative placement still need semantic changes.

### Human Review Triggers
- taste_direction_conflict severity=MAJOR:
  The playbook and fixture aesthetic intent recommend incompatible visual maturity.

### Exact Playbook Anchors
- Required design_center ids: editorial_restraint, typography_authority, whitespace_breathing
- Accepted anchor set: nature-communications-main-text-v1, Nature Communications,
  main_text, restrained, editorial_restraint, typography_authority,
  whitespace_breathing, toy_schematic, preset_macro_feel, restrained_hero,
  print_scale_calm, tikz_until_semantics_close, svg_for_optical_finish,
  taste_direction_conflict
```

## Critique Output Contract

When the playbook exists, `/fig_critique` should bump the critique schema and
rubric to the next version:

- `schema: figure-agent.critique.v1.12`
- `rubric_version: figure-agent.critique-rubric.v1.12`

The output adds:

```yaml
journal_art_direction_playbook_audit:
  schema: figure-agent.journal-art-direction-playbook-audit.v1
  playbook_id: nature-communications-main-text-v1
  venue_context: main_text
  design_center:
    - id: editorial_restraint
      verdict: pass | weak | fail | needs_human | not_applicable
      evidence: "<current artifact evidence>"
      positive_signal_refs:
        - restrained_hero
      anti_pattern_refs:
        - toy_schematic
      route: none | continue_tikz | ready_for_svg_polish | semantic_backport_required | needs_human_art_direction
      linked_evidence:
        - "top_tier_audit.aesthetic_coherence"
      rationale: "<why this verdict follows from the playbook>"
  route_rule_applied:
    id: tikz_until_semantics_close
    recommended_path: continue_tikz
    rationale: "<why this route wins>"
  human_review_triggers:
    - id: taste_direction_conflict
      active: false
      rationale: "<why not active, or what conflict requires review>"
```

Rules:

- Every `design_center[]` item in the playbook must appear exactly once in
  `journal_art_direction_playbook_audit.design_center`.
- `id` values must match the playbook.
- `priority: required` items cannot use `not_applicable`.
- Non-passing items require non-empty `evidence`, at least one
  `anti_pattern_refs` or human-review trigger, non-`none` route, and visible
  `linked_evidence`.
- `pass` items require non-empty `evidence`, at least one
  `positive_signal_refs`, and `route: none`.
- `route_rule_applied.id` must match one playbook route rule.
- `route_rule_applied.recommended_path` must match that rule.
- Active human-review triggers must surface through
  `editorial_art_direction.human_art_direction_gate` or a normal finding.
- The audit is advisory for quality, but required for critique validity when a
  playbook is declared.

## Lint Accountability

When `spec.yaml.journal_art_direction_playbook` is declared, `critique_lint.py`
should reject:

- missing or malformed playbook packs;
- missing `journal_art_direction_playbook_audit`;
- audit entries that omit declared `design_center[]` ids;
- unknown audit ids not present in the playbook;
- required design-center items marked `not_applicable`;
- non-passing audit entries without evidence, route, or linked evidence;
- `pass` entries without exact positive-signal references;
- route-rule mismatches;
- active human-review triggers not linked to visible critique gates;
- generic required slots that do not cite exact playbook anchors.

Required existing critique slots must cite at least one exact playbook anchor:

- `top_tier_audit.first_glance_message`
- `top_tier_audit.target_journal_fit`
- `top_tier_audit.visual_economy`
- `top_tier_audit.reduction_print_readability`
- `top_tier_audit.aesthetic_coherence`
- `editorial_art_direction.visual_identity`
- `editorial_art_direction.aesthetic_risk`
- `editorial_art_direction.tikz_vs_svg_polish_trigger`
- `journal_grade_assessment.rationale`

This does not mean all slots must pass. It means the critique must prove it
used the playbook rather than generic taste language.

## Freshness

`quality_manifest.critique_manifest_paths()` must include the resolved playbook
pack when `spec.yaml.journal_art_direction_playbook` is declared. This makes
existing critiques stale when journal-art-direction vocabulary changes.

Because `spec.yaml` is already a critique input, changing the declared playbook
id also makes existing critiques stale.

Missing playbooks preserve current behavior when the fixture does not opt in.
Missing or malformed playbooks produce controlled failures when the fixture
does opt in.

Expected rubric/schema precedence:

1. If a fixture declares a journal art-direction playbook, expect v1.12.
2. Else if `aesthetic_intent.yaml` uses schema v2, expect v1.11.
3. Else use the current v1.10 baseline.

v1.12 is a superset contract. If a fixture declares both a playbook and
`aesthetic_intent.yaml` schema v2, the v1.12 critique must include both
`journal_art_direction_playbook_audit` and the existing
`aesthetic_lever_audit`.

This prevents silently mutating older critique contracts in place.

## Interaction With Existing Layers

### Fixture Aesthetic Intent

`aesthetic_intent.yaml` remains the fixture-specific lever contract. The
playbook is reusable journal-level taste vocabulary. If they conflict, the
critique should surface the conflict through:

- `journal_art_direction_playbook_audit.human_review_triggers`;
- `editorial_art_direction.human_art_direction_gate`;
- a normal finding when the conflict blocks progress.

### Paper-Wide Aesthetic Context

`paper_aesthetic_context` says whether a figure belongs to the manuscript
series. The playbook says what journal-level visual maturity means. Both can be
present, and lint may require anchors from both. This is deliberate; series
coherence and journal art direction are different questions.

### SVG Polish

The playbook can recommend `ready_for_svg_polish`, but it must not bypass
existing SVG polish readiness gates. `fig_loop` and `fig_driver --mode polish`
remain the routing authority. A playbook route recommendation is evidence, not
permission to mutate SVG.

### Scores

The playbook may influence `journal_grade_assessment.next_quality_bottleneck`
and sub-score rationale, but it must not make `score_is_gateable: true` by
itself.

## Implementation Slices

### Issue 56A - Parser and Freshness

Files:

- `scripts/journal_art_direction_playbook.py`
- `scripts/quality_manifest.py`
- `tests/test_journal_art_direction_playbook.py`
- `tests/test_quality_manifest.py`

Outcomes:

- Resolve explicit `spec.yaml.journal_art_direction_playbook`.
- Validate playbook schema, safe ids, enum fields, item limits, and references.
- Include the resolved pack in critique freshness hashing.
- Preserve behavior for fixtures without the opt-in field.

### Issue 56B - Brief and Documentation

Files:

- `scripts/critique_brief.py`
- `commands/fig_critique.md`
- `skills/figure-agent/SKILL.md`
- `tests/test_critique_brief.py`

Outcomes:

- Emit `## Journal Art-Direction Playbook`.
- Include exact accepted anchors and route rules.
- Explain how the playbook differs from fixture aesthetic intent and
  paper-wide context.
- Fail with a controlled `CritiqueBriefError` for malformed opted-in packs.

### Issue 56C - Critique Schema v1.12 and Lint Accountability

Files:

- `scripts/critique_schema_vocab.py`
- `scripts/critique_schema_validator.py`
- `scripts/critique_lint.py`
- `scripts/quality_manifest.py`
- `scripts/critique_brief.py`
- `tests/test_critique_schema_validator.py`
- `tests/test_critique_lint.py`
- `tests/test_quality_manifest.py`

Outcomes:

- Add v1.12 schema/rubric only for opted-in playbook fixtures.
- Validate `journal_art_direction_playbook_audit`.
- Reject generic or incomplete playbook accounting.
- Keep legacy v1.10/v1.11 critiques parseable when no playbook is declared.

### Issue 56D - Loop Surfacing

Files:

- `scripts/fig_loop.py`
- `tests/test_fig_loop.py`
- `commands/fig_loop.md`

Outcomes:

- Surface a compact `journal_art_direction_playbook_summary` in loop JSON when
  a v1.12 critique exists.
- Do not create a new stop boundary unless an existing human/top-tier/aesthetic
  gate is activated.
- Preserve verify-only behavior.

### Issue 56E - Dogfood and Closeout

Files:

- one narrow fixture opt-in pack or synthetic dogfood fixture;
- milestone documentation.

Outcomes:

- Confirm the brief forces concrete art-direction language.
- Confirm lint rejects generic "professional polish" prose.
- Confirm a playbook edit stales the critique.
- Confirm no source/export/accepted/golden mutation occurs.

## Testing Plan

Targeted verification after each slice:

```bash
uv run pytest -q tests/test_journal_art_direction_playbook.py tests/test_quality_manifest.py
uv run pytest -q tests/test_critique_brief.py
uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_lint.py
uv run pytest -q tests/test_fig_loop.py
uv run ruff check scripts/journal_art_direction_playbook.py scripts/quality_manifest.py scripts/critique_brief.py scripts/critique_schema_validator.py scripts/critique_lint.py scripts/fig_loop.py tests/test_journal_art_direction_playbook.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_fig_loop.py
git diff --check
```

Final verification:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Risks and Guardrails

- **Over-checklist risk:** keep pack item counts small and role-independent.
- **Taste absolutism risk:** the playbook is a critique vocabulary, not a
  guarantee of journal acceptance.
- **Schema churn risk:** use v1.12 only when a fixture explicitly opts in.
- **Layer confusion risk:** keep paper-wide context, fixture aesthetic intent,
  and journal playbook separate in naming and brief order.
- **SVG bypass risk:** playbook route recommendations remain subordinate to
  existing SVG polish readiness gates.
- **Generic anchor gaming risk:** require current-artifact evidence, not only
  string citation of an anchor id.
- **Fixture churn risk:** dogfood can use synthetic fixtures first; real figure
  opt-in should be a separate narrow commit to avoid staling active figure work.

## Review Questions

1. Does this layer add a missing journal-design vocabulary rather than duplicate
   fixture-local `aesthetic_intent.yaml`?
2. Are the schema and item limits small enough that host LLM attention remains
   focused?
3. Does v1.12 preserve legacy v1.10/v1.11 behavior for non-opted-in fixtures?
4. Can a critique still pass with generic prose? If yes, lint is not strict
   enough.
5. Can the playbook accidentally authorize SVG polish or release? If yes, the
   route boundary is wrong.

## Current Recommendation

Proceed with Issue 56A-C only after this spec is reviewed. Issue 56D and 56E
should stay in the issue document but do not need to ship in the first coding
slice unless dogfood shows that loop surfacing is necessary immediately.

No known design blocker remains in this spec draft.
