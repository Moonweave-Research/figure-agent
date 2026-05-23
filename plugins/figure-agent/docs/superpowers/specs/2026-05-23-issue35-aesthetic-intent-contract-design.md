# Issue 35 Design — Aesthetic Intent Contract

## Context

`figure-agent` is intentionally a quality kernel, not an autonomous
illustrator. The current critique contract already asks the host model to fill
top-tier and editorial art-direction slots, but the target aesthetic is only
implicit in `briefing.md`, `critique_reference_pack.yaml`, and the current
render. That creates a weak grounding path for subjective-but-important
qualities such as visual maturity, restraint, density, and hand-crafted polish.

The fix should not reintroduce rejected absolute LLM quality judgment. Instead,
it should provide a fixture-local intent contract that the existing critique
slots must use as evidence.

## Architecture

Add a small optional parser module:

- `scripts/aesthetic_intent.py`

The module owns:

- `AESTHETIC_INTENT_SCHEMA = "figure-agent.aesthetic-intent.v1"`
- `load_aesthetic_intent(path: Path) -> dict[str, Any]`
- `load_optional_aesthetic_intent(example_dir: Path) -> dict[str, Any] | None`
- controlled `AestheticIntentError`

`scripts/critique_brief.py` loads the optional pack and emits
`## Aesthetic Intent Calibration` only when the file exists.

`scripts/quality_manifest.py` includes `aesthetic_intent.yaml` in
`critique_manifest_paths()` when present, so intent edits make existing
`critique.md` stale.

## Contract

```yaml
schema: figure-agent.aesthetic-intent.v1
fixture: <example-dir-name>
target_journal: Nature Communications | Nature Materials | Science | ACS | internal | unknown
visual_maturity: restrained | polished | editorial | cover_like
density: sparse | balanced | dense
reference_style: mechanism_schematic | apparatus_schematic | multipanel_story | data_plus_schematic | graphical_abstract
design_principles:
  - id: <stable-id>
    instruction: "<one concrete aesthetic directive>"
must_avoid:
  - id: <stable-id>
    pattern: "<anti-pattern to penalize>"
    severity: BLOCKER | MAJOR | MINOR | NIT
polish_triggers:
  - id: <stable-id>
    condition: "<when generated TikZ should hand off to polish or art direction>"
    recommended_path: continue_tikz | ready_for_svg_polish | needs_human_art_direction | semantic_backport_required
```

Validation rules:

- `schema` must match exactly.
- `fixture` must match the example directory name in optional loader.
- enum fields must use the closed sets above.
- `design_principles`, `must_avoid`, and `polish_triggers` must be non-empty
  lists.
- each item must have a non-empty `id`.
- item ids must be unique within their own list.
- each `design_principles[]` item must have non-empty `instruction`.
- each `must_avoid[]` item must have non-empty `pattern` and valid `severity`.
- each `polish_triggers[]` item must have non-empty `condition` and valid
  `recommended_path`.

## Brief Behavior

When present, the section appears before `## Author intent`:

```markdown
## Aesthetic Intent Calibration
Host LLM MUST apply this fixture-specific aesthetic target when filling
top_tier_audit.aesthetic_coherence, editorial_art_direction.visual_identity,
editorial_art_direction.aesthetic_risk, and
editorial_art_direction.tikz_vs_svg_polish_trigger.

- Target journal: Nature Materials
- Visual maturity: editorial
- Density: balanced
- Reference style: multipanel_story

### Design Principles
- mature_restraint: avoid cartoon-like oversized labels and decorative gradients

### Must-Avoid Patterns
- toy_diagram severity=MAJOR: rounded generic blocks and unmodulated flat color

### Polish Triggers
- svg_micro_polish path=ready_for_svg_polish: semantically correct TikZ lacks
  print-scale optical refinement
```

The section is prompt evidence only. It does not add a new output schema field
and does not let scores override existing gates.

## Compatibility

Missing `aesthetic_intent.yaml` preserves current behavior. Legacy critiques
remain parseable. Adding the file changes the critique input hash but not render
freshness, compile behavior, export behavior, or accepted/golden state.

## Tests

- valid aesthetic intent loads successfully;
- duplicate ids and invalid enums fail with `AestheticIntentError`;
- optional loader rejects fixture mismatch;
- `critique_brief.py` includes the calibration section when present;
- missing file omits the section;
- malformed file surfaces as `CritiqueBriefError`;
- `quality_manifest.critique_manifest_paths()` includes the file and hash
  changes when it changes.
