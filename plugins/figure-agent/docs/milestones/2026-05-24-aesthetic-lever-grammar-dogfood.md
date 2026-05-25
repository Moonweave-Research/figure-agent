# Aesthetic Lever Grammar Dogfood

**Date:** 2026-05-24 KST
**Issue:** `docs/superpowers/issues/2026-05-24-issue-43-aesthetic-lever-grammar.md`
**Status:** contract dogfood complete; independent host-vision art review still recommended before release use

## Scope

This dogfood applies the Issue 43 v2 aesthetic-lever contract to the existing
real fixture `fig1_overview_v2_pair_001_vault`.

Files intentionally changed:

- `examples/fig1_overview_v2_pair_001_vault/aesthetic_intent.yaml`
- `examples/fig1_overview_v2_pair_001_vault/critique.md`
- `examples/fig1_overview_v2_pair_001_vault/critique_adjudication.yaml`

No TikZ source, accepted state, golden contract, export artifact, or publication
provenance file was edited for this dogfood. `/fig_compile` was run only to
refresh local generated build artifacts required by `critique_brief.py`; those
generated files are not part of the evidence commit.

## Fixture Intent Upgrade

`aesthetic_intent.yaml` was upgraded from
`figure-agent.aesthetic-intent.v1` to `figure-agent.aesthetic-intent.v2`.

Declared levers:

1. `maturity_restraint` — `maturity`
2. `panel_c_hero_hierarchy` — `hero_hierarchy`
3. `row2_whitespace_breathing` — `whitespace_breathing`
4. `print_typography_authority` — `typography_authority`
5. `semantic_color_economy` — `color_harmony`
6. `line_weight_rhythm` — `line_weight_rhythm`
7. `component_fidelity_finish` — `component_fidelity`
8. `hand_craft_escape_route` — `hand_craft`
9. `cross_panel_grammar` — `cross_panel_grammar`

Parser check:

```text
figure-agent.aesthetic-intent.v2 9
maturity_restraint,panel_c_hero_hierarchy,row2_whitespace_breathing,print_typography_authority,semantic_color_economy,line_weight_rhythm,component_fidelity_finish,hand_craft_escape_route,cross_panel_grammar
```

## Brief Evidence

After refreshing render state, `critique_brief.py` emitted the v1.11 contract:

```text
## Aesthetic Lever Grammar (host LLM MUST enumerate)
schema: figure-agent.critique.v1.11
rubric_version: figure-agent.critique-rubric.v1.11
critique_input_hash: sha256:9c56f65ff0e0da15e9bc959a9308816d147bf26147c240bd95cb6f4c41ee1b55
```

This proves that v2 intent changes the host-critique output contract rather
than silently reusing the older v1.10 anchor-only critique surface.

## Critique Evidence

`critique.md` was refreshed to schema `figure-agent.critique.v1.11` and now
contains `aesthetic_lever_audit` entries for all nine declared levers.

The dogfood intentionally preserves the existing v1.9 visual findings instead
of inventing new source edits. The useful new signal is that the old broad
label/readability issue is now mapped onto a bounded aesthetic lever:

```text
evaluation_state: needs_patch
worst_verdict: weak
next_aesthetic_bottleneck:
  lever_id: print_typography_authority
  dimension: typography_authority
  route: tikz_patch
  linked_evidence: [C004, quality_axes.label_annotation_semantics]
```

This is more actionable than the Issue 35/36 anchor-only behavior because the
next action is no longer generic "improve polish" prose. It is a named
typography-authority lever with a permitted route and forbidden semantic guard.

## Local Visual Check

The full render was opened in Codex and the historical VC054 Energy-label crop
was inspected. The crop still shows why this belongs under typography/label
authority: the rotated `Energy` label sits immediately against the Panel C
film-edge region and intersects the dashed leader context. The dogfood therefore
keeps `print_typography_authority` as `weak` instead of allowing a
`high_impact_candidate` claim.

## Validation Evidence

Schema and lint:

```text
figure-agent.critique.v1.11 9 solid_manuscript
OK: critique lint passed for fig1_overview_v2_pair_001_vault
```

Status:

```text
States: render=FRESH critique=FRESH export=TRACKED_GOLDEN acceptance=NOT_ACCEPTED workflow_ready=false golden_ready=false release_ready=false final_ready=false
Explanation: export_tracked_golden — tracked golden exports require deliberate roll-forward approval.
```

Loop:

```text
aesthetic_lever_summary:
  lever_count: 9
  verdict_counts: pass=7, weak=1, fail=0, needs_human=0, not_applicable=1
  evaluation_state: needs_patch
  next_aesthetic_bottleneck: print_typography_authority / typography_authority / tikz_patch
```

Driver:

```text
action: human_gate_stop
stop_boundary: human_gate_required
reason: latest /fig_loop checkpoint requires human review: human review required for P001. first blocker export_tracked_golden.
```

The driver did not let a refreshed aesthetic critique bypass existing
adjudication, export/golden, or publication gates. The status first blocker
remains `export_tracked_golden`, while the driver correctly gives priority to
the latest loop checkpoint's conservative human-review boundary.

## Review Notes

- Contract correctness: v2 intent selects critique v1.11 and requires exact
  lever accounting.
- Scope containment: `.tex`, exports, accepted state, golden state, and
  publication provenance were not edited.
- Integration readiness: status, lint, loop, adjudication scaffold, and driver
  all consume the refreshed critique without schema errors.

## Remaining Risk

This is a contract dogfood, not a fresh independent Claude host-vision art
review. It verifies that the new v2 lever grammar works end-to-end and produces
an actionable bottleneck, but it does not prove that a separate host vision pass
would identify every aesthetic issue. A future release dogfood should ask the
host LLM to re-author the critique from the v1.11 brief without reusing this
document as source material.
