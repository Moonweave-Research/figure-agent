# Figure-Agent Style Pack Catalog

Status: initial catalog, explicit opt-in only

This catalog gives agents reusable language for journal-level taste decisions.
It does not apply any global style default, and it does not guarantee journal
acceptance. It only grounds `/fig_critique` and `/fig_loop` so vague requests
like "make it Nature-like" become concrete audit anchors.

## Pack Layers

Figure-agent uses three separate layers:

1. `examples/_journal_art_direction_playbooks/<id>.yaml`
   - Journal or venue convention.
   - Opt in from `examples/<fixture>/spec.yaml` with:
     `journal_art_direction_playbook: <id>`.
   - Good for target-journal maturity, anti-patterns, and polish-route rules.

2. `examples/_paper_aesthetic_contexts/<id>.yaml`
   - Paper-wide visual series convention.
   - Opt in from `examples/<fixture>/spec.yaml` with:
     `paper_aesthetic_context: <id>`.
   - Good for making multiple figures look like one paper.

3. `examples/<fixture>/aesthetic_intent.yaml`
   - Fixture-local intent and overrides.
   - Use this when a specific figure needs a hero, a relaxation, or a stricter
     local boundary than the shared pack.

The fixture-local file should refine the selected catalog pack. It should not
silently contradict the pack. If it does, the critique should route to human art
direction.

## Journal Playbooks

| Playbook | Venue | Use When | Avoid When |
| --- | --- | --- | --- |
| `nc-main-text` | Nature Communications main text | You need restrained, mature, clean scientific illustration with no decorative push. | The figure is a graphical abstract, cover-like scene, or needs expressive atmosphere. |
| `nature-materials-dense` | Nature Materials main text | Material specificity, interfaces, component fidelity, and dense but ordered mechanism detail matter. | The figure is so compact that material-detail cues would overload the story. |
| `science-compact` | Science main text | The figure must explain quickly with tight spacing and economical labels. | The claim needs slower material-rich inspection rather than one-pass compression. |
| `graphical-abstract-expressive` | Graphical abstract / cover-like | The venue explicitly permits a stronger hero, atmosphere, or organic finish. | Any normal main-text figure unless a human author explicitly opts in. |

## Paper Contexts

| Paper Context | Use When | Default Character |
| --- | --- | --- |
| `nc-main-text-series` | A paper needs a restrained Nature Communications main-text family. | Balanced density, muted semantic accents, compact typography. |
| `nature-materials-dense-series` | A paper needs material-rich mechanism figures with shared motifs. | Dense editorial detail, material-specific iconography. |
| `science-compact-series` | A paper needs compact explanatory figures across the series. | Tight story path, short labels, no prose clutter. |
| `graphical-abstract-expressive-series` | A graphical abstract or cover-like visual family is explicitly requested. | Strong hero, meaningful atmosphere, explicit opt-in boundary. |

The catalog paper contexts use template fixture names. They are not attached to
real examples by default. To use one, copy or extend its `figure_roles` with the
actual fixture names, then opt in from each fixture's `spec.yaml`.

## Selection Rules

Use `nc-main-text` first for conservative manuscript figures. Move to
`nature-materials-dense` only when the figure genuinely needs material-specific
detail to read professionally. Use `science-compact` when compression and fast
storytelling matter more than material richness. Use the expressive packs only
for graphical abstracts, cover-like scenes, or explicitly approved art
direction.

Main-text packs intentionally forbid decorative/cover-style effects by default.
If a requested "hand-crafted" effect changes semantics, hides a missing
component, or makes the figure feel like a poster, keep the route in TikZ or
ask for human art direction. SVG polish is only for finish-level changes after
the figure's source-level structure is stable.

## Example Opt-In

```yaml
name: fig1_overview
journal_art_direction_playbook: nc-main-text
paper_aesthetic_context: nc-main-text-series
```

Use `aesthetic_intent.yaml` for fixture-specific levers:

```yaml
schema: figure-agent.aesthetic-intent.v2
fixture: fig1_overview
target_journal: Nature Communications
visual_maturity: restrained
density: balanced
reference_style: multipanel_story
design_principles:
  - id: main_text_restraint
    instruction: preserve restrained NC main-text maturity while polishing one hero panel
must_avoid:
  - id: cover_style_leak
    pattern: glow, wash, or poster-like gradient appears in a main-text panel
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantics are stable and only typography or stroke finish remains
    recommended_path: ready_for_svg_polish
aesthetic_levers:
  - id: hero_without_poster
    dimension: hero_hierarchy
    intent: give the main panel a clear first glance without decorative treatment
    priority: required
    positive_signals:
      - one entry point is visible without oversized labels or glow
    anti_patterns:
      - the figure reads as graphical abstract instead of main-text schematic
    allowed_adjustments:
      - rebalance whitespace and local contrast in TikZ
    forbidden_adjustments:
      - add cover-like atmosphere without human approval
    default_route: tikz_patch
```

## Review Checklist

Before selecting a pack, ask:

- Is this a main-text figure or a graphical abstract?
- Does the figure need material richness, compact story compression, or
  restrained overview clarity?
- Are any requested effects semantic repairs rather than optical finish?
- Does the selected pack conflict with fixture-local `aesthetic_intent.yaml`?
- Would a future agent know exactly why this pack was chosen?
