# Issue 70: Operator-Grade Guided Autonomy Readiness Roadmap

Status: completed

Depends on: Issue 69 safe draft export runner expansion

## Problem

The plugin now has a strong audit kernel and a bounded runner. `/fig_run
--execute` can already close safe mechanical work: compile, missing
adjudication scaffold, verify-only loop checkpoints, and non-golden draft
export.

The next risk is not simply "add more autonomy." Current repo docs still point
to real-fixture cleanup, fixture audit adoption, positive SVG-polish evidence,
paper-wide context, and UX compression as important evidence gaps. Issue 70
therefore starts with a readiness gate: prove where guided autonomy is actually
needed before adding more kernel behavior.

If the readiness pass confirms stop/continuation ambiguity as a recurring
bottleneck, the next day-to-day friction is "what exactly should the operator
or host LLM do when the runner stops?"

Today a boundary stop preserves safety, but the next handoff can still be
ambiguous:

- host-vision critique stops do not produce a compact packet of images,
  evidence, freshness reason, and expected closeout;
- human gates expose safety, but not always the smallest decision the human
  needs to make;
- patch and polish handoffs can require reading multiple JSON/Markdown
  artifacts to know what is allowed;
- a new session can lose track of what `/fig_run` already executed and why it
  stopped;
- dogfood evidence is spread across milestones instead of a current real-fixture
  runner matrix.

If the plugin keeps adding automatic actions without this evidence and boundary
layer, it risks becoming less trustworthy: automation would advance through
more states while humans lose visibility into the remaining high-judgment
boundary.

## Goal

Make the plugin feel operator-grade without widening hidden mutation. `/fig_run`
should either execute safe mechanical work or stop with a precise handoff that
tells the next agent or human what to inspect, what not to mutate, how to close
the boundary, and why fresh status/driver checks are required before continuing.

This roadmap does not make the plugin a hidden auto-designer. It improves the
contract around stops, continuation, and evidence. Resume/replay is explicitly
deferred until a future design proves it safer than rerunning live state.

## Design Principles

- The driver remains the canonical next-action selector.
- The runner remains a bounded executor over driver-selected actions.
- Boundary handoff is explanatory, not authority to bypass the boundary.
- Generated run journals, if implemented, belong under `.scratch/` and are not
  committed.
- Host, human, accepted, golden, release, source-patch, and SVG-polish editing
  boundaries stay explicit.
- New JSON contracts must be additive and backward-compatible.
- Real-fixture evidence should precede any further allowlist expansion.

## Child Issues

1. Issue 70A - Guided Autonomy Readiness Matrix
2. Issue 70B - Mechanical Boundary Handoff Packet
3. Issue 70C - Patch Executor Freshness And Pending-Closeout Hardening
4. Issue 70D - Fig Run Journal Contract
5. Issue 70E - Safe Resume And Operator UX Closeout

## Recommended Order

Run 70A first. It is a go/no-go gate for further guided-autonomy work and may
redirect effort toward fixture cleanup or positive SVG-polish evidence instead.
Run 70C before any future patch-executor exposure, because source mutation must
be at least as freshness-safe as read-only driver routing. 70B may proceed
before 70C only for non-source-mutation stops; patch/source-mutation handoff
must remain deferred until 70C is complete. Defer 70D/70E until 70A/70B show
that persisted runner journals would reduce continuity friction and any resume
behavior can be proven safer than live status/driver reruns.

```text
70A readiness matrix
  -> 70B mechanical boundary handoff, if 70A justifies it
     (excluding patch/source-mutation boundaries until 70C)
  -> 70C patch-executor freshness hardening, before any patch exposure
  -> 70D fig_run journal contract, conditional on continuity evidence
  -> 70E safe resume and operator UX closeout, only after currentness rules exist
```

70A result:
`docs/milestones-archive/2026-05-29-guided-autonomy-readiness-matrix.md` found no
current `/fig_run --execute` opportunity in review mode, no live patch/pending
closeout coverage, and no positive SVG-polish route. The strongest next
implementation candidate is 70C patch freshness hardening. 70B remains allowed
only as a small non-patch explanatory handoff slice. It did not justify command
replay/resume; later slices therefore kept 70D to non-authoritative evidence
journals and 70E to docs-only resume deferral.

70C result:
`docs/milestones-archive/2026-05-29-patch-executor-freshness-hardening.md` implements
stale loop checkpoint refusal, iteration fixture mismatch refusal, and pending
patch closeout refusal for the existing opt-in patch executor. This still does
not expose patch execution through `/fig_run`.

70B result:
`docs/milestones-archive/2026-05-29-boundary-handoff-packet.md` implements an additive
`boundary_handoff` object for `/fig_run` non-complete stops. The packet is
explanatory only: no executable resume command, no patch edit scope leakage,
and no expansion of the runner allowlist.

70D result:
`docs/milestones-archive/2026-05-29-fig-run-journal-contract.md` implements a
gitignored `.scratch/fig-run-runs/` journal for `/fig_run` stdout payloads. The
journal is non-authoritative evidence only: it records what happened, but never
allows command replay or resume without fresh status/driver checks.

70E result:
`docs/milestones-archive/2026-05-29-safe-resume-operator-ux-closeout.md` closes the
roadmap with resume deferred. Current behavior is guided autonomy, not replay:
read the last journal if helpful, then rerun live `/fig_status` or
`/fig_drive`, and use `/fig_run --execute` only for freshly selected
allowlisted mechanical actions.

## Out Of Scope For Issue 70

- Hidden source editing.
- Automatic host-vision critique authoring.
- Automatic accepted/golden roll-forward.
- Automatic `--force-golden`.
- Automatic release approval.
- Automatic SVG/vector polish editing.
- Treating aesthetic score, reference metrics, or basin detection as release
  authority.
- Provider API calls or web scraping.

## Acceptance

- The roadmap is decomposed into independently implementable issues.
- Each child issue has clear AFK/HITL classification and dependency order.
- The first child issue is an evidence gate, not an implementation commitment.
- The roadmap explains which boundaries remain manual and why.
- The next implementation slice can start with tests without re-litigating the
  whole architecture.
- Documentation states that guided autonomy is about better stops,
  continuation handoffs, and currentness checks, not resume/replay or broader
  hidden mutation.

## Review Questions

1. Does this prioritize real operator friction over speculative automation?
2. Does it preserve the current safety model around host, human, accepted,
   golden, release, patch, and polish boundaries?
3. Are the child issues vertical enough to be implemented and verified
   independently?
4. Does the roadmap avoid expanding auto-patch before stop/continuation UX is
   trustworthy?
