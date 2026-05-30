# Issue 70A: Guided Autonomy Readiness Matrix

Status: completed in `docs/milestones/2026-05-29-guided-autonomy-readiness-matrix.md`

Depends on: Issue 70 operator-grade guided autonomy roadmap

Type: AFK

## Problem

The plugin has enough machinery to tempt broader autonomy, but current docs
still identify real-fixture cleanup, fixture audit adoption, paper-wide context,
positive SVG-polish evidence, and audit UX compression as important open
evidence gaps. Issue 70 must not assume stop/resume ambiguity is the dominant
problem until real fixtures prove it.

## What To Build

Run a current-truth, real-fixture guided-autonomy matrix. The goal is not to
add features. The goal is to decide whether 70B/70D/70E are justified, and to
identify any higher-priority plugin gap that should preempt them.

The matrix should record:

- `/fig_status` state vector;
- `/fig_drive --dry-run` selected action;
- `/fig_run` plan-mode output;
- `/fig_run --execute` output only where the current allowlist permits it;
- final boundary and whether it is understandable from existing output;
- whether the fixture instead exposes a fixture cleanup, SVG-polish evidence,
  audit adoption, or closeout freshness gap.

## Suggested Coverage

Include fixtures that exercise at least these shapes:

- stale render -> compile;
- stale/missing critique -> host boundary;
- missing adjudication -> scaffold;
- non-golden missing/stale export -> draft export;
- tracked golden export -> force-golden stop;
- human gate from adjudication -> human stop;
- patch handoff or pending patch closeout;
- SVG polish readiness, semantic backport, or stale-polish gate.

If no fixture can exercise patch/pending-closeout or SVG-polish behavior, the
matrix must record that absence as a blocking evidence gap for proceeding to
runner handoff or resume work. It must not silently treat missing coverage as a
clean pass.

## Go/No-Go Output

The milestone must explicitly decide:

- proceed to 70B mechanical boundary handoff;
- pause autonomy work and prioritize fixture cleanup/adoption;
- prioritize positive SVG-polish promotion evidence;
- prioritize patch-executor freshness hardening before any patch-related UX;
- split the roadmap because multiple independent gaps are found.

## Acceptance

- At least five real fixtures are inspected.
- The matrix includes at least four distinct stop/action shapes or explains why
  the current fixture set cannot produce them.
- Patch/pending-closeout and SVG-polish-related shapes are covered, or their
  absence is recorded as a no-go/defer signal for dependent Issue 70 slices.
- Generated build/export artifacts are not committed.
- Unsafe, unclear, or misleading runner behavior is filed as a concrete
  follow-up before 70B starts.
- The milestone states whether 70B is justified.

## Verification

- `git status --short --untracked-files=all` before and after the pass.
- `git diff --check`.
- If source code is unchanged, no pytest is required.

## Review Questions

1. Does the evidence actually show stop/resume UX is the next bottleneck?
2. Did the pass expose higher-priority real-fixture or SVG-polish gaps?
3. Did `--execute` run only current allowlisted actions?
4. Are generated artifacts excluded from the diff?
