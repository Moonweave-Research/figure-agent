# Safe Resume And Operator UX Closeout

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-70e-safe-resume-and-operator-ux-closeout.md`

Status: completed

## Decision

Resume is deferred.

Issue 70 shipped better guided autonomy, but not command replay:

- 70A showed that boundary clarity and patch freshness were stronger needs than
  resume.
- 70B made non-complete `/fig_run` stops self-explanatory through
  `boundary_handoff`.
- 70C hardened the source-mutating patch executor, but did not expose patch
  execution through `/fig_run`.
- 70D added non-authoritative `.scratch/fig-run-runs/` evidence.

None of that proves a `--resume` flag is safer than rerunning live status and
driver selection. A stale journal could lag source, critique, adjudication,
export, acceptance, golden, or publication state.

## Operator Contract

Automatic:

- deterministic compile, lint, freshness, export, golden, publication,
  visual/text clash, crop/accounting, package validation gates, and shared
  single-next-action summaries.

Semi-automatic:

- `/fig_run --execute` may execute only allowlisted mechanical shell actions
  selected by fresh `/fig_drive`: compile, missing adjudication scaffold,
  verify-only loop checkpoint, and non-golden draft export.
- `/fig_critique` host vision writes critique after reading prepared evidence.
- `/fig_loop` records verify-only loop evidence.
- `/fig_run --record` can persist plan-only evidence when explicitly requested.

Explicit opt-in mutation:

- `fig_loop_patch_executor.py --apply` may apply one externally prepared unified
  diff only after its own fresh loop, adjudication, closeout, and scope gates.
  It is not exposed through `/fig_run`, and no journal/resume path may replay it.

Manual:

- source drawing and semantic patch choices;
- existing adjudication repair;
- host/human gates;
- patch handoff decisions before any prepared diff exists;
- SVG/vector polish editing;
- accepted/golden/release decisions;
- force-golden and publication provenance.

Continuation after interruption:

1. Inspect `.scratch/fig-run-runs/<timestamp>-<name>/stop.md` only as context.
2. Rerun live `/fig_status <name>` or `/fig_drive <name> --mode <mode> --goal
   "<goal>" --dry-run`.
3. Use `/fig_run <name> --mode <mode> --goal "<goal>" --execute` only if the
   fresh driver still selects an allowlisted action.

## Files Updated

- `README.md`
- `skills/figure-agent/SKILL.md`
- `commands/fig_run.md`
- `commands/fig_drive.md`
- `commands/fig_loop.md`
- `commands/fig_closeout.md`
- `docs/superpowers/issues/2026-05-29-issue-70-operator-grade-guided-autonomy.md`
- `docs/superpowers/issues/2026-05-29-issue-70e-safe-resume-and-operator-ux-closeout.md`
- `docs/superpowers/specs/2026-05-29-operator-grade-guided-autonomy-design.md`

## Review Notes

- No new resume/read path was added.
- No runner allowlist expansion was added.
- No `/fig_run` patch, SVG, accepted, golden, release, or provider automation
  was added.
- The existing opt-in patch executor remains a separate, explicit prepared-diff
  path with its own freshness gates.
- Docs now state the same continuation rule: journal first as context, then
  live status/driver re-query.

Post-review fixes:

- Aligned the operator tier table with `README.md`: `/fig_run --execute` is
  semi-automatic at the command boundary, not a blanket automatic workflow.
- Reworded the parent roadmap from "stops and resumes" to
  "stops, continuation handoffs, and currentness checks" because resume/replay
  is intentionally deferred.
- Scoped the no-journal claim to `.scratch/fig-run-runs/` so it does not
  contradict `/fig_drive` reading live `.scratch/fig-loop-runs/` checkpoints.

## Verification

- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
- `uv run ruff check .` -> passed.
- `uv run pytest -q` -> 1422 passed, 1 skipped, 1 xfailed, 6 warnings.

No known Issue 70E blocker remains.
