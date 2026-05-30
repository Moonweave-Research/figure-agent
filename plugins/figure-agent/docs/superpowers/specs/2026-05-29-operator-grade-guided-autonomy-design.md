# Operator-Grade Guided Autonomy Design

Date: 2026-05-29

Parent issue:
`docs/superpowers/issues/2026-05-29-issue-70-operator-grade-guided-autonomy.md`

## Current State

`figure-agent` now has three distinct layers that should stay separate:

- `/fig_status` reads canonical fixture state and exposes
  `next_action_summary`.
- `/fig_drive` selects one next action from status, loop evidence, and closeout
  state.
- `/fig_run --execute` safely executes a narrow set of driver-selected shell
  steps: compile, missing adjudication scaffold, verify-only loop checkpoint,
  and non-golden draft export.

The current risk is not simply "more autonomy is needed." Current docs and
dogfood still point to competing gaps: fixture cleanup/adoption, positive
SVG-polish promotion evidence, paper-wide context, audit UX compression, and
source-mutating patch freshness. Issue 70 must therefore start with a readiness
matrix before adding new runner behavior.

## Design Goal

Make guided autonomy evidence-driven and boundary-safe:

1. prove which real fixture states still confuse operators;
2. make boundary stops mechanically understandable when evidence justifies it;
3. harden any source-mutating path before exposing it more prominently;
4. add runner journals only as non-authoritative evidence, and add resume
   behavior only if earlier evidence proves it safer than rerunning
   `/fig_drive`.

The system should feel autonomous in low-judgment mechanical steps and
deliberately non-autonomous at host, human, source-patch, SVG-polish,
accepted/golden, and release boundaries.

## Architecture

The design preserves existing layer ownership:

- `status.py` remains the canonical state reader.
- `fig_driver.py` remains the action selector.
- `fig_run.py` remains the bounded executor.
- `fig_loop.py` remains verify-only loop evidence.
- `fig_closeout.py` remains read-only post-patch closeout.
- `fig_loop_patch_executor.py` remains an explicit, externally prepared
  patch-application path.

Issue 70 may add helper contracts around those layers, but the helpers must
derive from existing evidence. They must not create a second route selector.

## Readiness Gate

70A is mandatory before implementation. It measures current behavior across
real fixtures and decides whether the rest of Issue 70 is the right next work.

The readiness matrix should answer:

- Which `/fig_run` states are already clear enough?
- Which stop boundaries are ambiguous in practice?
- Which gaps are really fixture cleanup, audit adoption, SVG-polish evidence,
  or closeout freshness rather than runner UX?
- Which child issues should proceed, pause, or be reordered?

If the evidence shows a different bottleneck, 70B/70D/70E should be deferred.

Current 70A evidence:
`docs/milestones/2026-05-29-guided-autonomy-readiness-matrix.md` found that
review-mode `/fig_run` would execute zero steps across the eight spec-backed
fixtures because all sampled fixtures stopped at host or closeout boundaries.
It also found no live patch/pending-closeout shape and no positive SVG-polish
route. This makes 70C the strongest next implementation candidate; 70B is
limited to non-patch explanatory handoff if pursued; at that point, 70D/70E
were deferred.
Later slices kept 70D to non-authoritative evidence journals and 70E to
docs-only resume deferral rather than command replay.

Current 70C implementation:
`docs/milestones/2026-05-29-patch-executor-freshness-hardening.md` hardens the
existing opt-in patch executor so it refuses stale loop checkpoints, iteration
fixture mismatch, and pending patch closeout evidence before mutation.

Current 70B implementation:
`docs/milestones/2026-05-29-boundary-handoff-packet.md` adds an explanatory
`boundary_handoff` object to `/fig_run` non-complete results. It derives from
existing driver/runner evidence, omits executable resume commands, and defers
patch/source-mutation scope.

## Boundary Handoff Contract

If 70A justifies it, 70B adds a handoff packet to `/fig_run` non-complete stops.
The packet must be compact, additive, and mechanically derived from existing
fields:

- `action`
- `stop_boundary`
- `safe_command`
- `next_action_summary`
- loop checkpoint evidence
- closeout evidence

The handoff packet answers what a new operator needs first:

- why the workflow stopped;
- who owns the next action;
- which evidence must be read;
- what may change;
- what must not change;
- which closeout checks are required;
- which live status/driver checks should be rerun before continuing.

70B must not emit executable resume commands. Manual boundaries such as command
failure, human gate, force-golden, release approval, and existing adjudication
repair must receive explanatory continuation guidance only. The packet is not
authority to bypass the boundary.

Patch/source-mutation handoff is explicitly deferred from 70B until 70C is
complete.

## Patch Executor Currentness Contract

70C hardens `fig_loop_patch_executor.py` before any future patch-related UX is
made more visible. This is independent of whether non-patch runner handoff
ships.

The patch executor writes source, so it must be at least as freshness-safe as
read-only driver checkpoint routing:

- reject loop runs older than relevant fixture evidence;
- require fixture identity to match;
- reject malformed or missing iteration records;
- refuse a new patch when a previous patch apply in the selected run still has
  pending closeout;
- name the blocking evidence path in refusal messages.

70C does not add patch execution to `/fig_run` and does not generate patches.

## Runner Journal Contract

70D is now implemented. 70B dogfood showed that boundary handoff packets are
useful in live fixture states, but they are still ephemeral stdout unless a
session records them. `/fig_run --execute` therefore writes a gitignored runner
journal by default while preserving the public stdout JSON. Plan-only runs stay
no-write by default and require explicit `--record` if a dogfood note should be
persisted.

The journal lives under `.scratch/fig-run-runs/<timestamp>-<fixture>/` and
persists the public run payload plus boundary handoff. The journal is evidence,
not authority:

- fresh `/fig_drive` state still decides next action;
- old journals cannot replay commands;
- recorded `safe_command` fields are preserved as evidence only;
- generated journals remain untracked;
- tests can redirect the runs root.

No `--resume` behavior should be implemented in 70D.

## Safe Resume And UX Closeout

70E is implemented as a docs-only closeout with resume deferred. A
`.scratch/fig-run-runs/` journal can explain what happened, but it is stale
evidence the moment source, critique, adjudication, export, accepted/golden, or
publication state changes. No shipped command reads a fig-run journal to decide
the next action. This does not ban other live evidence readers such as
`/fig_drive` reading fresh `.scratch/fig-loop-runs/` checkpoints.

Manual continuation path:

1. Read the last `stop.md` or stdout payload only as context.
2. Rerun live `/fig_status <name>` or `/fig_drive <name> --mode <mode> --goal
   "<goal>" --dry-run`.
3. Run `/fig_run <name> --mode <mode> --goal "<goal>" --execute` only if the
   fresh driver selects an allowlisted shell action.

This keeps automatic, semi-automatic, and manual boundaries explicit.

## Vertical Slices

### 70A: Guided Autonomy Readiness Matrix

Evidence-only real-fixture matrix. This is the go/no-go gate for further guided
autonomy work.

### 70B: Mechanical Boundary Handoff Packet

Add an additive stop packet only if 70A shows stop ambiguity. It must mirror
existing driver/status/loop/closeout fields, avoid executable resume commands,
and exclude patch/source-mutation handoff until 70C is complete.

### 70C: Patch Executor Freshness And Pending-Closeout Hardening

Harden the existing source-mutating patch executor before any patch path is
surfaced more prominently.

### 70D: Fig Run Journal Contract

Persist runner evidence under `.scratch/` only if 70A/70B prove multi-session
continuity needs it. No replay or resume behavior.

### 70E: Safe Resume And Operator UX Closeout

Make the resume go/no-go decision and close docs against actual behavior.
Implemented as docs-only: resume is deferred.

## Safety Boundaries

Issue 70 must not automate:

- host-vision critique writing;
- source editing through `/fig_run`;
- patch generation;
- existing adjudication overwrite/repair;
- accepted/golden roll-forward;
- `--force-golden`;
- release approval;
- SVG/vector polish editing;
- provider API calls;
- git staging, commit, push, or branch switching.

## Test Strategy

Implementation slices should use TDD:

- 70A: docs/milestone evidence only; no pytest unless code changes.
- 70B: `tests/test_fig_run.py` boundary cases for host critique, human gate,
  existing adjudication, force-golden, command failure, max steps, and additive
  JSON compatibility.
- 70C: `tests/test_fig_loop_patch_executor.py` and
  `tests/test_fig_driver_checkpoint.py` for stale loop run, newer evidence,
  malformed records, pending closeout, and clean current run.
- 70D: `tests/test_fig_run.py` journal path, `--runs-root`, optional
  `--no-record`, and journal non-authority.
- 70E: full verification and plugin validation.

## Success Criteria

- The roadmap does not assume guided autonomy is the next implementation until
  70A proves it.
- `/fig_run` stop handoffs, if added, are self-explanatory without becoming a
  second router.
- Source-mutating patch execution is blocked on stale or pending-closeout
  evidence.
- Any journal or resume behavior is explicitly non-authoritative until live
  status and driver state are revalidated.
- Existing safe runner allowlist remains narrow.
- No hidden mutation boundary is crossed.
- Docs and command behavior agree.
