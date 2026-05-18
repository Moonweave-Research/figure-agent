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

Resolution in this slice:

- Add `--json` to `scripts/fig_loop.py`.
- Emit at least `run_dir`, `manifest_path`, `iteration_path`,
  `final_stop_reason`, `escalation_level`, and `patch_handoff_present`.
- Keep existing prose output for humans.
- Keep preflight failures on the legacy prose stderr contract.

### P1 - No first-class deterministic E2E smoke command

The useful dogfood sequence was:

```text
/fig_compile -> /fig_export -> /fig_status -> /fig_loop
```

Today this has to be hand-scripted. That makes the plugin hard to evaluate as a
loop system because every reviewer may run a different sequence.

Risk: "E2E passed" claims will be non-comparable across agents.

Resolution in this slice:

- Add a deterministic smoke runner, for example `scripts/fig_e2e_smoke.py`.
- It runs compile, export gate, status, and fig_loop.
- It does not edit source, critique, acceptance, golden, or exports beyond
  normal compile/export outputs.
- It outputs one aggregate JSON summary with per-run command evidence and
  supports `--repeat N`.
- It compares stable status/loop outcomes across repeats so command success
  alone cannot hide drift in stop reason, escalation, readiness, notes, or
  patch-handoff presence.

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

## Implemented Follow-up

Do not continue polishing `fig1_overview_v2` as a figure.

The P0 state/readiness fix is now implemented as an optional-note policy for
`coordinate_hints_*`.

The P1 adjudication scaffold is now implemented as `/fig_adjudicate <name>` via
`scripts/critique_adjudication.py scaffold <name>`, so future dogfood passes do
not require hand-written `critique_adjudication.yaml`.

The P2 axis-evidence gap is now addressed in `/fig_loop` JSON by adding
`source`, `evidence_path`, and `evaluation_state` to every axis verdict while
preserving legacy `state` and `verdict`.

The P2 post-patch closeout checklist is now implemented as `/fig_closeout
<name>` via `scripts/fig_closeout.py`. It reports compile, critique,
adjudication, export, and loop-rerun closeout state without mutating the figure
or scratch run state. It blocks the final loop-rerun recommendation until prior
closeout prerequisites are closed and treats tracked golden roll-forward as
manual approval evidence rather than an auto-executable command.

## Issue 5A Dogfood: Auto-Patch Readiness Gate

Issue 5A deliberately remains read-only. The goal is not to patch figures
automatically, but to classify whether a single patch handoff is a future
auto-patch candidate.

Verification on `fig1_overview_v2`:

```bash
uv run python3 scripts/fig_loop.py fig1_overview_v2 \
  --goal "Dogfood Issue 5A readiness gate on existing fixture" --json
```

Observed result:

- `final_stop_reason: status_action_required`
- `escalation_level: agent_action_required`
- `patch_handoff_present: false`
- `auto_patch_eligibility: null`
- `recommended_next_action: run /fig_compile fig1_overview_v2 to compile the
  TikZ source.`

This confirms the gate does not invent an auto-patch candidate when no single
patch handoff exists.

Repeat smoke:

```bash
uv run python3 scripts/fig_e2e_smoke.py fig1_overview_v2 --repeat 2 \
  --goal "Dogfood Issue 5A readiness gate smoke"
```

Observed result:

- `success: true`
- both repeats reached stable `manual_approval_required`
- both repeats reported `patch_handoff_present: false`
- render, critique, and export remained fresh after the first compile/export
  refresh

Synthetic eligibility scenarios were also run in a temporary repo root so no
fixture source or artifacts were modified:

- label/overlap finding -> `auto_patch_candidate`, `may_edit: false`
- mechanism/causal-arrow finding -> `human_review_required`,
  `may_edit: false`
- publication-safety/accepted-golden finding -> `human_review_required`,
  `may_edit: false`

Current judgment:

- Issue 5A is useful as a conservative classifier.
- It is not sufficient evidence to build Issue 5B auto-editing yet.
- Generic label wording changes must stay `patch_assisted_only`; only concrete
  geometry findings such as overlap, clipping, offset, crowding, or collision
  should enter `auto_patch_candidate`.
- Before Issue 5B, collect more real `apply` handoff examples and check whether
  keyword classification is too broad or too narrow.
- Keep `may_edit: false` until before/after evidence capture, rollback, and
  patch-closeout verification are first-class runner outputs.
