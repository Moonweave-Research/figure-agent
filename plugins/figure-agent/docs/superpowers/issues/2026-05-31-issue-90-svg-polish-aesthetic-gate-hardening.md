# Issue 90 - SVG Polish And Aesthetic Gate Hardening

Status: completed in commits d33f3da, 452c00f, af2b005, b4d416b

Type: SVG polish audit, aesthetic gate hardening, operator safety

Depends on:

- Issue 43 - aesthetic lever grammar
- Issue 55 - paper-wide aesthetic context
- Issue 56 - journal art-direction playbook dogfood
- Issue 63 - reference learning and aesthetic metrics
- Issue 73 - SVG polish trigger semantics
- Issue 75 - SVG polish readiness source gate clarity
- Issue 89 - v0.9 operator-grade release candidate

## Problem

The plugin now prevents many bad figure states: stale critique, missing crop
accounting, visual-clash omissions, unsafe export, accepted/golden mutation,
and ambiguous queue operation. It also has SVG polish building blocks:

- `svg_polish_recipe.py`
- `svg_polish_executor.py`
- `svg_polish_delta.py`
- `svg_polish_manifest.py`
- `/fig_driver --mode polish`
- `ready_for_svg_polish`
- `aesthetic_intent.yaml` v2 and `aesthetic_lever_audit`
- `journal_art_direction_playbook_audit`
- SVG before/after/diff input in `/fig_critique`

The remaining weakness is not that SVG can never be edited. The weakness is
that the handoff and audit boundary around SVG polish is still too easy to
misread:

1. Operators can ask "can I start SVG polish now?" and still need to interpret
   multiple fields.
2. A host critique can describe SVG before/after/diff in prose without making
   a crisp pass/regress/human-art-direction decision.
3. Aesthetic quality still leans heavily on broad LLM taste words unless the
   fixture has strong `aesthetic_intent`, paper context, or journal playbook
   anchors.
4. Positive real-fixture evidence for the complete route
   `ready_for_svg_polish -> recipe -> delta -> critique -> manifest` is still
   thinner than the safety evidence for compile/export/status/queue.

## Goal

Make SVG polish and aesthetic review a guarded, auditable loop instead of an
informal judgment layer.

The first slice should harden the **gate and audit contract**, not expand
automatic SVG editing. A user should be able to ask:

- "Can SVG polish start?"
- "Did SVG polish actually improve the figure?"
- "Did SVG polish regress scientific meaning, labels, readability, or journal
  maturity?"
- "Should the loop continue in SVG, return to TikZ semantic backport, or stop
  for human art direction?"

and receive a structured answer from the plugin state, not just prose.

## Non-Goals

- Do not add broad automatic SVG beautification.
- Do not allow hidden source, accepted, golden, or publication mutation.
- Do not let SVG polish bypass `ready_for_svg_polish`.
- Do not promote a figure to release-ready based on aesthetic scores alone.
- Do not require SVG polish for figures that are already release/golden-ready.
- Do not require external vision APIs.
- Do not change TikZ generation or source patch behavior in this issue.

## Proposed Behavior

### 1. SVG Polish Readiness Contract

`/fig_driver --mode polish` should expose a compact readiness object that is
easy to consume:

```yaml
svg_polish_gate:
  state: blocked | ready | needs_human | semantic_backport | no_current_checkpoint
  can_start_svg_polish: true | false
  source: latest_loop_checkpoint | status_blocker | driver_blocker
  reason: "<one-line>"
  required_inputs:
    - critique_fresh
    - loop_checkpoint_current
    - tikz_vs_svg_polish_trigger_ready
    - no_top_tier_blockers
    - no_crop_uncertainty
    - no_human_art_direction_gate
  next_action: start_svg_polish_recipe | rerun_fig_loop | run_fig_critique | human_art_direction | semantic_backport
```

This can be additive. Existing `svg_polish_readiness` may remain, but the gate
must remove operator ambiguity. Implementation should deepen or normalize the
existing `figure-agent.svg-polish-readiness.v1` surface rather than creating a
parallel readiness truth that can drift from `/fig_loop` and `/fig_driver`.

Readiness can only become `ready` from a current `/fig_loop` checkpoint that
records `ready_for_svg_polish`. `status_blocker` and `driver_blocker` may
explain why readiness is blocked, but they must not promote a figure to SVG
polish by themselves. In particular, accepted/golden/export freshness is not
proof that SVG polish is allowed.

Readiness precedence is conservative:

1. human art-direction gate or high-impact blocker;
2. semantic backport requirement;
3. unresolved crop uncertainty or stale/missing critique;
4. stale/missing SVG recipe, polished SVG, or delta pack;
5. ready only when the current checkpoint is clean and explicitly says
   `ready_for_svg_polish`.

### 2. SVG Delta Audit Contract

When `polish/aesthetic_delta/manifest.json` exists and is fresh, the critique
must fill a structured SVG delta verdict:

```yaml
svg_polish_delta_audit:
  evaluation_state: improved | no_meaningful_change | regressed | needs_human_art_direction | invalid
  read_all_delta_images: true
  delta_image_audit_log:
    - image_id: before
      path: polish/aesthetic_delta/before.png
      verdict: inspected
      observation: "<current-artifact evidence>"
    - image_id: after
      path: polish/aesthetic_delta/after.png
      verdict: inspected
      observation: "<current-artifact evidence>"
    - image_id: diff
      path: polish/aesthetic_delta/diff.png
      verdict: inspected
      observation: "<current-artifact evidence>"
  compared_inputs:
    - before
    - after
    - diff
  improvements:
    - "<specific improvement>"
  regressions:
    - category: semantic_drift | label_readability | crop_regression | print_scale_regression | overdecorated | journal_mismatch
      evidence: "<crop/diff/reference>"
      severity: BLOCKER | MAJOR | MINOR | NIT
      linked_finding_id: "<id or null>"
  route_after_delta: continue_svg_polish | accept_svg_polish | semantic_backport_required | needs_human_art_direction
  rationale: "<why this route is chosen>"
```

`critique_lint.py` should reject a vNext critique that has a fresh SVG delta
manifest but omits this block, does not account for all required delta image
ids from the manifest, names unknown image ids, or reports a regression without
a visible finding / human route. `read_all_delta_images: true` is not
sufficient by itself; the image-id log is the audit contract.

`accept_svg_polish` is a delta-local verdict only. It must not mark release
ready by itself. It means the delta audit saw no blocking regression and the
workflow may proceed to the existing `svg_polish_manifest.py` / final-artifact
freshness contract, then through normal status/export/publication gates.

The delta manifest and each listed delta image hash must participate in
`critique_input_hash`. Otherwise a critique could remain fresh after a polished
SVG, recipe, or before/after/diff image changes.

### 3. Aesthetic Gate Closed Set

The aesthetic gate should stop using only generic language such as "polished",
"pretty", or "professional". It should require a closed-set assessment:

- `maturity_restraint`
- `visual_hierarchy`
- `template_genericness`
- `overdecorated_or_cartoonish`
- `journal_fit`
- `handcrafted_finish`
- `semantic_preservation`
- `print_scale_finish`
- `paper_wide_coherence`

Each item should route to exactly one of:

- `pass`
- `tikz_patch`
- `svg_polish`
- `semantic_backport`
- `needs_human_art_direction`
- `accept_simplification`

The route must be compatible with existing gates. For example, `svg_polish`
cannot appear unless `tikz_vs_svg_polish_trigger.recommended_path` is
`ready_for_svg_polish`.

### 4. Driver And Loop Surfacing

`fig_loop.py` and `fig_driver.py` should surface:

- whether SVG polish can start;
- whether the latest SVG delta was audited;
- whether the latest delta improved, regressed, or needs human art direction;
- the next bounded command, if any;
- the stop boundary if human/SVG/release action is required.

The driver must remain non-mutating unless it is invoking the existing bounded
SVG polish executor in a separate, explicitly approved issue. This issue is
about gates and audit visibility.

For Issue 90A-C, the runner allowlists stay unchanged. `/fig_run` and
`/fig_queue_run` must not execute SVG write commands in this issue.

## Edge Cases To Cover

### Readiness Edge Cases

1. No current `/fig_loop` checkpoint exists.
   - Expected: `state: no_current_checkpoint`, `can_start_svg_polish: false`.
2. Critique is stale.
   - Expected: block on critique refresh, not SVG.
3. Critique is fresh but `crop_audit_log` has uncertain crops.
   - Expected: block SVG start until uncertainty is resolved.
4. `tikz_vs_svg_polish_trigger` says `continue_tikz`.
   - Expected: route to remaining TikZ lever.
5. `tikz_vs_svg_polish_trigger` says `semantic_backport_required`.
   - Expected: no SVG start; route to source/spec/briefing backport.
6. `tikz_vs_svg_polish_trigger` says `ready_for_svg_polish`, but
   `human_art_direction_gate` says `needs_human`.
   - Expected: human gate wins.
7. Top-tier audit has a high-impact blocker.
   - Expected: block SVG start; require visible blocker resolution.
8. The fixture is accepted/tracked-golden but no loop checkpoint proves SVG
   readiness.
   - Expected: do not infer readiness from accepted/golden/export state.

### Delta Manifest Edge Cases

9. Delta manifest missing.
   - Expected: no delta audit required; readiness may ask for recipe/delta.
10. Delta manifest stale against polished SVG, generated SVG, or recipe.
    - Expected: invalidate delta audit input and route to regenerate delta.
11. SVG polish recipe exists but no delta manifest exists.
    - Expected: readiness can point to delta generation; critique does not
      pretend before/after evidence exists.
12. Delta manifest exists but fixture name/path does not match the current
    fixture.
    - Expected: reject as controlled validation error.
13. Delta manifest exists but before/after/diff image is missing.
    - Expected: controlled lint/brief error.
14. Delta manifest includes duplicate image ids.
    - Expected: reject; each required image id must be unique.
15. Delta manifest includes extra unknown image ids.
    - Expected: reject or warn explicitly; unknown images cannot silently pass.
16. Multiple delta manifests or stale backup manifests exist under
    `polish/aesthetic_delta/`.
    - Expected: use the canonical manifest path only; ignore or warn on backups
      without letting them satisfy freshness.
17. Host critique does not read all delta images.
    - Expected: lint rejects `read_all_delta_images: false`, missing
      `delta_image_audit_log` entries, or entries whose ids do not match the
      canonical manifest artifacts.
18. Host critique says "improved" but lists a MAJOR regression.
    - Expected: invalid unless route is `semantic_backport_required` or
      `needs_human_art_direction`.
19. Host critique says "accept_svg_polish" while there is crop uncertainty.
    - Expected: invalid.
20. Host critique says "accept_svg_polish" but `svg_polish_manifest.yaml` is
    missing, invalid, or stale.
    - Expected: route cannot be accepted; final artifact freshness must be
      proven by the manifest contract.
21. Delta audit says `accept_svg_polish`, but there is no current final-artifact
    manifest binding the polished SVG to source/export/critique/audit hashes.
    - Expected: keep release/final readiness blocked; run or repair the
      polished-SVG manifest flow.

### Aesthetic Judgment Edge Cases

22. The SVG polish adds decorative texture that makes the figure look more
    "handmade" but violates journal restraint.
    - Expected: route to human art direction or regression, not automatic pass.
23. The SVG polish improves label spacing but shifts a scientific arrow.
    - Expected: semantic drift blocks acceptance.
24. The SVG polish changes color/opacity in a way that breaks palette
    semantics.
    - Expected: semantic or journal-fit regression.
25. The SVG polish makes the full figure prettier but worsens print-scale
    readability.
    - Expected: print-scale regression blocks.
26. The SVG polish improves one panel but hurts paper-wide coherence.
    - Expected: require paper-wide coherence accounting when context exists.
27. The aesthetic issue is truly subjective.
    - Expected: `needs_human_art_direction`, not forced patching.
28. The figure is already release/golden-ready without SVG polish.
    - Expected: do not require SVG polish; preserve release route.
29. The host says "more premium" or "more beautiful" without naming the closed
    aesthetic slot and current artifact evidence.
    - Expected: invalid generic prose.
30. The host says "handcrafted_finish fail" but the journal playbook asks for
    restrained schematic clarity.
    - Expected: route to `accept_simplification` or human art direction; do not
      force decorative texture.

### Backward Compatibility Edge Cases

31. Legacy critiques without SVG delta remain parseable.
    - Expected: no new required block unless a fresh delta manifest exists or
      schema vNext opts in.
32. Existing v1.14 critiques remain valid unless the fixture has fresh delta
    inputs that require the new contract.
33. Fixtures with no `aesthetic_intent.yaml`, no paper context, and no journal
    playbook still work.
    - Expected: use generic closed-set gate, but do not require missing packs.
34. Fixtures with `aesthetic_intent.yaml` v1 continue using legacy behavior.
35. Existing SVG polish recipe tests continue to pass.
36. Existing queue/run/export/release gates remain unchanged.
37. Accepted tracked-golden fixtures do not become release-blocked merely
    because they lack SVG polish evidence.

### Operator Safety Edge Cases

38. `/fig_driver --mode polish` must not expose a write command when readiness
    is blocked.
39. `/fig_queue` must classify SVG polish rows as `svg_editor` or a blocked
    operator handoff, not workflow-agent execution.
40. `/fig_run` must not execute SVG polish writes unless a later issue
    explicitly expands its allowlist.
41. `safe_command` strings remain evidence, not permission to replay stale
    state.
42. Accepted/golden state must never be mutated by SVG polish gate checks.
43. Plan-only queue output may list SVG handoff commands, but those commands
    must remain blocked unless the required actor is `svg_editor` and the
    readiness gate is `ready`.
44. A queue row with both `release_blocked` and SVG-polish hints must preserve
    the release/human blocker as the first blocker; SVG polish evidence cannot
    mask accepted/golden/publication gates.

## Candidate Slices

### Issue 90A - SVG Polish Gate Summary

- Add/normalize `svg_polish_gate` in `fig_driver_editorial.py`,
  `fig_loop.py`, and `/fig_driver --mode polish`.
- Reuse and extend the existing `svg_polish_readiness` contract; do not create
  a second readiness truth.
- No critique schema bump required if additive.
- Tests: readiness states, blocker precedence, current-checkpoint requirement.

### Issue 90B - SVG Delta Audit Schema And Lint

- Add `svg_polish_delta_audit` to the next applicable critique schema when a
  fresh delta manifest exists.
- Enforce via `critique_schema_validator.py` and `critique_lint.py`.
- Include delta image-id accounting and critique freshness/hash participation.
- Tests: missing block, stale delta, missing image id, unknown image id,
  regression without linked finding, accept-without-final-manifest guard,
  legacy compatibility.

### Issue 90C - Aesthetic Gate Closed-Set Grammar

- Add closed-set aesthetic gate slots to the brief and lint.
- Ensure routes are compatible with `tikz_vs_svg_polish_trigger`.
- Tests: generic prose rejected, incompatible route rejected, subjective issue
  routes to human.

### Issue 90D - Real Fixture Dogfood

- Run a real or fixture-local SVG polish dry-run path.
- Generate delta pack.
- Author or refresh critique using delta images.
- Confirm driver/loop route is one of:
  `accept_svg_polish`, `continue_svg_polish`, `semantic_backport_required`, or
  `needs_human_art_direction`.
- No accepted/golden mutation.

## Acceptance Criteria

- The plugin can answer "can SVG polish start?" through a compact JSON field.
- A fresh SVG delta cannot be silently ignored by critique/lint.
- SVG polish regressions cannot be hidden in prose.
- Aesthetic gate decisions use closed-set slots and explicit routes.
- Legacy critiques and non-SVG fixtures remain compatible.
- `/fig_run` and `/fig_queue_run` do not gain hidden SVG write behavior.
- Full targeted tests pass:

```bash
uv run pytest -q \
  tests/test_fig_driver_editorial.py \
  tests/test_fig_driver.py \
  tests/test_fig_loop.py \
  tests/test_critique_schema_validator.py \
  tests/test_critique_lint.py \
  tests/test_critique_brief.py \
  tests/test_svg_polish_delta.py \
  tests/test_svg_polish_recipe.py \
  tests/test_svg_polish_manifest.py
```

- Full suite, ruff, diff check, and plugin validation pass before claiming
  completion.

## Design Review

### Contract Review

The issue is intentionally gate-first. It does not add automatic SVG polish
editing and does not widen `/fig_run` execution. The new contracts should be
additive unless a fixture has fresh SVG delta inputs or explicitly opts into a
new critique schema.

Review fix: readiness is now explicitly sourced from a current loop checkpoint
only. `status_blocker` and `driver_blocker` can explain blocks, but they cannot
promote readiness.

Second review fix: `svg_polish_gate` must be implemented as a normalization or
extension of the existing `svg_polish_readiness` contract. A parallel readiness
truth would be a design defect.

### Safety Review

The highest-risk failure mode is mistaking "SVG polish available" for "safe to
mutate final artifacts". This issue avoids that by requiring current loop
evidence, fresh critique, no unresolved crop uncertainty, and explicit route
compatibility before surfacing any polish path.

Review fix: `/fig_run` and `/fig_queue_run` are explicitly out of scope for SVG
write execution in 90A-C.

Second review fix: `accept_svg_polish` is explicitly delta-local. It cannot
promote release readiness or bypass `svg_polish_manifest.py`, final-artifact
freshness, accepted/golden, or publication gates.

### Backward Compatibility Review

Existing accepted/golden/release behavior must remain unchanged. Existing
v1.14 critiques should not become invalid merely because the plugin is newer.
The stricter audit applies when the fixture has fresh SVG delta artifacts or
the next schema explicitly requires it.

### Edge-Case Review

The edge cases above cover stale inputs, missing images, incomplete host
inspection, subjective art direction, semantic drift, print-scale regressions,
paper-wide coherence, and operator-safety failures. The first implementation
slice should convert these into focused tests before any production code
changes.

Review fix: added fixture mismatch, duplicate image id, stale backup manifest,
missing final-artifact manifest, generic-prose, and accepted/golden compatibility
cases.

Second review fix: delta audit now requires per-image-id accounting, not just a
boolean `read_all_delta_images`. Added final-artifact manifest and queue
blocker-precedence edge cases.

### Three-Pass Review Notes

1. Readiness/pass-through review found a possible duplicate-source problem:
   the proposed `svg_polish_gate` could drift from the existing
   `svg_polish_readiness`. The issue now requires extending the existing
   contract instead.
2. Delta/manifest review found a weak audit primitive: a boolean
   `read_all_delta_images` is easier to fake than crop-level accounting. The
   issue now requires a `delta_image_audit_log` whose ids match the canonical
   manifest artifacts.
3. Operator-flow review found route ambiguity around `accept_svg_polish` and
   queue rows that also have release blockers. The issue now says
   `accept_svg_polish` is delta-local and release/golden/publication blockers
   keep precedence.

## Recommendation

Start with **Issue 90A**. It is the smallest useful slice: make the driver and
loop answer "can SVG polish start?" without changing critique schema or SVG
write behavior. Then implement 90B and 90C only after the gate summary is
stable.

## Implementation Closeout

Implemented slices:

- 90A: `svg_polish_gate` is now surfaced from the existing
  `svg_polish_readiness` contract. `/fig_driver --mode polish` reports
  `no_current_checkpoint`, `ready`, `needs_human`, `semantic_backport`, or
  `blocked` without executing SVG writes.
- 90B: v1.15 critique contract adds `svg_polish_delta_audit`. Fresh
  `polish/aesthetic_delta/delta_manifest.json` requires v1.15 critique,
  before/after/diff image-id accounting, and delta-local routing.
- 90C: v1.15 critique contract adds closed-set `aesthetic_gate_audit`.
  Generic "looks polished" evidence is rejected by lint; routes must stay
  compatible with `tikz_vs_svg_polish_trigger`.

Safety outcome:

- No `/fig_run` or `/fig_queue_run` SVG write allowlist expansion.
- `accept_svg_polish` remains a delta-local verdict and does not bypass
  `svg_polish_manifest.py`, final-artifact freshness, accepted/golden, or
  publication gates.
- Existing v1.14 and older critiques remain parseable unless a fresh SVG delta
  manifest opts the fixture into v1.15.

Verification record:

- TDD red tests were added before each production-code slice.
- Targeted tests passed for driver/loop readiness, critique schema/lint/brief,
  quality manifest, and SVG polish delta.
- Full verification and plugin validation are recorded in
  `docs/milestones-archive/2026-05-31-issue-90-svg-polish-aesthetic-gate-closeout.md`.
