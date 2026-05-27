# Paper-Wide Aesthetic Context Design

## Context

`figure-agent` now has strong single-figure audit surfaces:

- fixture-local `aesthetic_intent.yaml` v1/v2;
- reference-calibrated critique packs;
- top-tier and editorial art-direction critique slots;
- SVG-polish routing and aesthetic lever audits;
- deterministic text-boundary, visual-clash, label-path, zoom, and print-scale
  evidence gates.

The remaining aesthetic gap is not "can one figure be polished?" but "do the
figures in one manuscript read as one coherent visual series?" A single figure
can satisfy its own local aesthetic intent while still drifting from the
paper-wide visual language: palette restraint, typography hierarchy, line-weight
rhythm, panel grammar, density, iconography, and polish route.

The plugin should add paper-wide context as a grounding input for critique, not
as an autonomous illustrator or a score gate.

## Non-Goals

- No new figure drawing.
- No automatic SVG polish.
- No external reference or web search.
- No hidden mutation of `.tex`, accepted, golden, or export artifacts.
- No absolute claim that a figure is Nature/Science-ready.
- No global file that silently applies to every fixture under `examples/`.
- No replacement for fixture-local `aesthetic_intent.yaml`; paper context
  complements it.

## Design Principle

Paper-wide context must be explicit opt-in per fixture. The repo's `examples/`
directory contains fixtures from different dogfood and test contexts, so an
ambient `examples/paper_aesthetic_context.yaml` would create false coupling.

Each fixture opts in through `spec.yaml`:

```yaml
paper_aesthetic_context: inverse-vulcanization-charge-trapping
```

The loader resolves that id to:

```text
examples/_paper_aesthetic_contexts/inverse-vulcanization-charge-trapping.yaml
```

The pack applies to a fixture only if `figure_roles[]` contains that fixture.
If a fixture declares `paper_aesthetic_context` but the pack is missing,
malformed, or lacks a matching `figure_roles[].fixture`, `/fig_critique` should
fail with a controlled error rather than silently falling back to generic taste.

## Contract

Add optional paper-context packs under:

```text
examples/_paper_aesthetic_contexts/<paper_id>.yaml
```

Schema:

```yaml
schema: figure-agent.paper-aesthetic-context.v1
paper_id: inverse-vulcanization-charge-trapping
target_journal: Nature Communications | Nature Materials | Science | ACS | internal | unknown
visual_maturity: restrained | polished | editorial | cover_like
density: sparse | balanced | dense
shared_visual_language:
  - id: restrained_palette
    dimension: palette
    instruction: keep palette muted, low-saturation, and consistent across figures
    priority: required
    positive_signals:
      - repeated restrained accent colors across main figures
    anti_patterns:
      - one figure using poster-like saturation while others are restrained
  - id: typography_authority
    dimension: typography
    instruction: preserve compact journal-style label hierarchy across figures
    priority: required
    positive_signals:
      - labels use consistent scale and weight across panels
    anti_patterns:
      - oversized explanatory labels that read like slides
figure_roles:
  - fixture: fig1_overview_v2_pair_001_vault
    role: overview_mechanism
    must_align_with:
      - restrained_palette
      - typography_authority
    allowed_variations:
      - may use one stronger hero panel than downstream data figures
must_avoid:
  - id: series_drift
    pattern: one figure looks like a different design system from the rest
    severity: MAJOR
```

Closed enums:

- `target_journal`: same set as `aesthetic_intent.yaml`.
- `visual_maturity`: same set as `aesthetic_intent.yaml`.
- `density`: same set as `aesthetic_intent.yaml`.
- `shared_visual_language[].dimension`: `palette`, `typography`,
  `line_weight`, `whitespace`, `panel_grammar`, `iconography`,
  `data_ink`, `visual_identity`, `polish_route`, `figure_series`.
- `shared_visual_language[].priority`: `required`, `recommended`, `optional`.
- `figure_roles[].role`: `overview_mechanism`, `mechanism_detail`,
  `data_evidence`, `methods_apparatus`, `graphical_abstract`, `supplemental`.
- `must_avoid[].severity`: `BLOCKER`, `MAJOR`, `MINOR`, `NIT`.

Validation rules:

- `schema` must exactly equal `figure-agent.paper-aesthetic-context.v1`.
- `spec.yaml.paper_aesthetic_context` and pack `paper_id` must be safe ids:
  ASCII letters, numbers, `_`, `.`, and `-` only; no slash, backslash, or
  whitespace. This prevents path traversal when resolving the pack path.
- `paper_id` must be a non-empty string and match the filename stem.
- `target_journal`, `visual_maturity`, and `density` must be valid enums.
- `shared_visual_language` must be a non-empty list with unique ids and at
  most 12 items.
- Each shared language item must have non-empty `id`, `dimension`,
  `instruction`, `priority`, `positive_signals`, and `anti_patterns`.
- `figure_roles` must be a non-empty list with unique `fixture` values and at
  most 50 items.
- Each figure role must have a non-empty `fixture`, valid `role`,
  non-empty `must_align_with`, and optional `allowed_variations`.
- Every `must_align_with` id must refer to an existing
  `shared_visual_language[].id`.
- `must_avoid` must be a non-empty list with unique ids, non-empty `pattern`,
  valid `severity`, and at most 12 items.

## Brief Behavior

When a fixture opts in, `/fig_critique` emits a new section before
fixture-local `Aesthetic Intent Calibration`:

```markdown
## Paper-Wide Aesthetic Context
Host LLM MUST evaluate whether this figure remains coherent with the declared
paper-wide visual language. The critique must cite exact paper context anchors
in `top_tier_audit.cross_panel_grammar`,
`top_tier_audit.aesthetic_coherence`, and
`editorial_art_direction.visual_identity`.

- Paper id: inverse-vulcanization-charge-trapping
- Target journal: Nature Communications
- Visual maturity: editorial
- Density: balanced
- Figure role: overview_mechanism

### Required Shared Visual Language
- restrained_palette priority=required: keep palette muted...
- typography_authority priority=required: preserve compact...

### Allowed Role Variations
- may use one stronger hero panel than downstream data figures

### Paper-Wide Must-Avoid Patterns
- series_drift severity=MAJOR: one figure looks like a different design system...
```

The exact anchors are:

- `paper_id`
- `target_journal`
- `visual_maturity`
- `density`
- the matching `figure_roles[].role`
- every `shared_visual_language[].id` listed in the fixture's
  `must_align_with`
- every `must_avoid[].id`

The host model may cite more anchors, but the lint contract should require at
least one exact paper-wide anchor in each required critique slot.

## Interaction With Fixture Aesthetic Intent

Paper-wide context is higher-level than fixture-local `aesthetic_intent.yaml`.
The intended order is:

1. Paper-wide context defines visual series constraints.
2. Fixture aesthetic intent defines local emphasis and polish levers.
3. The current artifact is judged against both, if both exist.

If they appear to conflict, the critique should surface the conflict through
`editorial_art_direction.human_art_direction_gate` or a normal finding. The
parser should not attempt semantic conflict resolution in v1.

When both files exist, lint may require both paper-wide anchors and
fixture-local anchors. This is deliberate: a critique should prove it consumed
both levels rather than collapsing them into generic art-direction prose.

## Freshness

`quality_manifest.critique_manifest_paths()` must include the resolved paper
context pack when `spec.yaml.paper_aesthetic_context` is declared. This makes
existing `critique.md` stale when paper-wide taste constraints change.

Because `spec.yaml` is already part of the critique source set, changing the
declared paper context id also makes critiques stale.

Missing paper context preserves current behavior when the fixture does not opt
in. Missing or malformed paper context is a controlled critique-brief/lint
failure when the fixture does opt in.

## Lint Accountability

When `spec.yaml.paper_aesthetic_context` is declared, `critique_lint.py` should
require exact paper-wide anchor citations in:

- `top_tier_audit.cross_panel_grammar`
- `top_tier_audit.aesthetic_coherence`
- `editorial_art_direction.visual_identity`

Missing anchors should produce a controlled `paper_aesthetic_context_accounting`
blocker. Fixtures without `spec.yaml.paper_aesthetic_context` keep legacy lint
behavior.

Do not extend `aesthetic_lever_audit.dimension` in this slice. Existing fixture
`aesthetic_intent.yaml` v2 dimensions remain unchanged. A future v2 of the
paper-wide context can add a dedicated series-lever audit if dogfood shows that
the three required critique slots are not enough.

## Implementation Slices

### Issue 55A - Parser and Freshness

Files:

- `scripts/paper_aesthetic_context.py`
- `scripts/quality_manifest.py`
- `tests/test_paper_aesthetic_context.py`
- `tests/test_quality_manifest.py`

Outcomes:

- Parse and validate `examples/_paper_aesthetic_contexts/<paper_id>.yaml`.
- Resolve packs only from explicit `spec.yaml.paper_aesthetic_context`.
- Include the resolved pack in critique freshness hashing.
- Preserve behavior for fixtures without the opt-in field.

### Issue 55B - Critique Brief Section

Files:

- `scripts/critique_brief.py`
- `tests/test_critique_brief.py`
- `commands/fig_critique.md`
- `skills/figure-agent/SKILL.md`

Outcomes:

- Emit `## Paper-Wide Aesthetic Context`.
- Show only the matching figure role and its required shared language ids.
- Instruct host critiques to cite paper-wide anchors in the required slots.
- Fail with a controlled `CritiqueBriefError` for missing/malformed opted-in
  packs.

### Issue 55C - Lint Accountability

Files:

- `scripts/critique_lint.py`
- `tests/test_critique_lint.py`

Outcomes:

- Reject opted-in critiques that do not cite paper-wide anchors in the required
  slots.
- Accept critiques that cite exact anchors.
- Keep fixtures without paper context unchanged.
- Surface malformed opted-in packs as controlled blockers.

### Issue 55D - Dogfood and Closeout

Files:

- one real fixture opt-in pack, likely for the active inverse-vulcanization
  figure family;
- milestone documentation.

Outcomes:

- Dogfood on one fixture without changing figure source.
- Confirm `critique_input_hash` changes when the paper context changes.
- Confirm `/fig_critique` brief includes the section.
- Confirm lint catches a generic critique that ignores the paper context.

## Testing Plan

Targeted verification after each slice:

```bash
uv run pytest -q tests/test_paper_aesthetic_context.py tests/test_quality_manifest.py
uv run pytest -q tests/test_critique_brief.py
uv run pytest -q tests/test_critique_lint.py
uv run ruff check scripts/paper_aesthetic_context.py scripts/critique_brief.py scripts/quality_manifest.py scripts/critique_lint.py tests/test_paper_aesthetic_context.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_critique_lint.py
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

- **Global coupling risk:** avoid an ambient root context file. Require
  `spec.yaml.paper_aesthetic_context`.
- **Generic critique risk:** lint exact anchor usage, as with fixture
  `aesthetic_intent.yaml`.
- **Over-gating risk:** paper-wide context should gate only critique quality,
  not compile/export/release by itself.
- **Fixture mismatch risk:** pack must explicitly list each opted-in fixture.
- **Schema drift risk:** add a new parser module instead of overloading
  `aesthetic_intent.py`.
- **Taste absolutism risk:** do not convert paper context into hard numeric
  quality scores. It is critique grounding and evidence accountability.
