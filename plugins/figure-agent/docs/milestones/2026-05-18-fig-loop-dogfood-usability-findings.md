# Fig Loop Dogfood Usability Findings - 2026-05-18

## Scope Correction

`fig1_overview_v2` is a dogfood fixture, not a target manuscript figure. Its
purpose in this pass is to reveal plugin defects, loop-friction, misleading
state transitions, and unsafe handoff behavior. Do not evaluate this pass as a
figure-quality polish pass.

The useful evidence from the dogfood run is the loop behavior:

- `compile -> run_export -> status -> fig_loop` was repeated five times.
- Each run reported `render=FRESH`, `critique=FRESH`, `export=FRESH`.
- `critique_adjudication.yaml` was fresh and had no remaining `apply` target.
- `/fig_loop` stopped at `status_action_required` with
  `manual_approval_required`, not at a patch target.
- `/fig_status` still reported `workflow_ready=false` because of
  `coordinate_hints_stale`, while its `Next:` text pointed at `accepted: true`.

That last combination was the important usability defect.

## Findings

### P0 - Status next action can point to acceptance while workflow is not ready

Current observed state:

```text
States: render=FRESH critique=FRESH export=FRESH acceptance=NOT_ACCEPTED workflow_ready=false
Notes: coordinate_hints_stale
Next: golden fixture is not accepted yet ... set accepted: true in spec.yaml.
```

This is internally inconsistent. If `workflow_ready=false`, the next action
should not point at an acceptance promotion unless every non-approval blocker is
cleared. Either `coordinate_hints_stale` must not block `workflow_ready`, or
`Next:` must prioritize refreshing coordinate hints before acceptance.

Risk: agents will ask the user for a manual approval while an ordinary local
contract-refresh task remains.

Resolution in this slice:

- Treat `coordinate_hints_*` notes as non-blocking workflow notes.
- Keep surfacing them in `/fig_status` so agents can refresh `/fig_extract`
  when useful.
- Do not let them make `workflow_ready=false`.
- Keep real blockers such as stale critique, stale export, missing briefing,
  and missing reference inputs as workflow blockers.

Regression coverage:

- `tests/test_status.py::test_coordinate_hint_notes_do_not_block_workflow_ready`
  locks the state where each emitted `coordinate_hints_*` note remains visible
  but `workflow_ready` stays true when render, critique, and export are fresh.

Deferred alternative:

- If Layer 2.5 becomes a mandatory reference-analysis gate later, reverse the
  policy deliberately and add first-class next-action text for
  `/fig_extract <name>`.

### P1 - `/fig_loop` stdout is human-readable only, brittle for automation

The dogfood harness initially failed because it parsed:

```text
fig_loop.py: wrote verify-only run to <path>
```

The run itself succeeded, but machine parsing should not depend on prose.

Risk: outer agents and CI smoke scripts will repeatedly reinvent fragile regex
parsers around slash-command output.

Proposed Issue:

- Add `--json` to `scripts/fig_loop.py`.
- Emit at least `run_dir`, `manifest_path`, `iteration_path`,
  `final_stop_reason`, `escalation_level`, and `patch_handoff_present`.
- Keep existing prose output for humans.

### P1 - No first-class deterministic E2E smoke command

The useful dogfood sequence was:

```text
/fig_compile -> /fig_export -> /fig_status -> /fig_loop
```

Today this has to be hand-scripted. That makes the plugin hard to evaluate as a
loop system because every reviewer may run a different sequence.

Risk: "E2E passed" claims will be non-comparable across agents.

Proposed Issue:

- Add a deterministic smoke runner, for example `scripts/fig_e2e_smoke.py`.
- It should run compile, export gate, status, and fig_loop.
- It should not edit source, critique, acceptance, golden, or exports beyond
  normal compile/export outputs.
- It should output one JSON summary per run and support `--repeat N`.

### P1 - Adjudication authoring is raw YAML with no scaffold

The loop contract depends on `critique_adjudication.yaml`, but the user-facing
workflow still requires an outer agent to hand-create the YAML from
`critique.md`.

Risk: malformed decisions, hidden finding loss, stale hashes, and inconsistent
`apply`/`defer` semantics become normal operator errors rather than rare edge
cases.

Proposed Issue:

- Add an adjudication scaffold command or script.
- Parse `critique.md` frontmatter findings.
- Generate `critique_adjudication.yaml` with the correct
  `source_critique_hash`.
- Default undecided findings to `needs_human` or another explicit pending state
  if the schema is extended; do not silently omit them.

### P2 - Axis verdicts may imply coverage that was not actually evaluated

`/fig_loop` currently records axes such as `static_visual`, `theory`, and
`story_hierarchy`, but several are always `not_evaluated` in this verify-only
runner.

Risk: the JSON shape looks like a comprehensive loop audit while major quality
axes are placeholders.

Proposed Issue:

- Keep the axes, but add an explicit `source` or `evidence_path` field per axis.
- Distinguish `not_configured`, `not_evaluated`, `blocked`, and `passed`.
- Make docs state which axes are real gates in the current version.

### P2 - Patch handoff is clear, but closeout is still operator-heavy

The protocol correctly avoids hidden auto-editing and selects one patch target.
However, closeout requires a human/outer agent to know when to regenerate
critique, rewrite adjudication, and rerun export/status.

Risk: agents may fix a target visually, then leave stale critique/adjudication
or stale exports while claiming loop closure.

Proposed Issue:

- Add a post-patch checklist command that reports exactly which closeout steps
  are stale or missing.
- Prefer machine-readable output so outer agents can stop before overclaiming.

## Recommended Next Slice

Do not continue polishing `fig1_overview_v2` as a figure.

The P0 state/readiness fix is now implemented as an optional-note policy for
`coordinate_hints_*`.

The next implementation slice should add `fig_loop --json` and a repeatable E2E
smoke runner so future dogfood passes test the plugin instead of drifting into
figure edits.
