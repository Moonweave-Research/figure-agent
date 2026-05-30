# Issue 70E: Safe Resume And Operator UX Closeout

Status: implemented

Depends on: Issue 70A and whichever of Issues 70B, 70C, and 70D actually ship

Type: HITL/AFK mixed

## Problem

Safe resume is attractive, but unsafe resume is worse than no resume. It should
exist only after stop evidence, patch-executor freshness, and any shipped
handoff or runner-journal contracts are proven. If 70A redirects the roadmap
away from handoff/resume work, 70E becomes a docs-only closeout that records the
manual continuation path and the reason resume was deferred.

## What To Decide Or Build

70E decision: keep resume deferred. 70B/70D make stops inspectable and
journaled, but they do not prove that a `--resume` flag is safer than rerunning
live `/fig_status`, `/fig_drive`, and `/fig_run`. Explicit resume behavior such
as:

- `--resume <run_dir>`;
- `--resume-latest`;

is therefore out of scope for shipped Issue 70 behavior.

Continuation path:

1. Inspect the previous `.scratch/fig-run-runs/<timestamp>-<name>/stop.md` or
   stdout JSON if useful.
2. Rerun `/fig_status <name>` or `/fig_drive <name> --mode <mode> --goal
   "<goal>" --dry-run`.
3. Run `/fig_run <name> --mode <mode> --goal "<goal>" --execute` only if the
   fresh driver still selects an allowlisted mechanical action.

Then close the operator UX:

- README;
- `skills/figure-agent/SKILL.md`;
- `/fig_run`, `/fig_drive`, `/fig_loop`, and `/fig_closeout` docs;
- issue status lines;
- automatic / semi-automatic / manual table.

## Scope

In scope:

- A resume go/no-go decision.
- Docs-only closeout because current evidence rejects resume/replay work.
- Current-truth docs closeout.
- Full verification.

Out of scope:

- Host critique automation.
- New source patch automation or exposing the existing explicit patch executor
  through `/fig_run`.
- Accepted/golden/release automation.
- SVG/vector edit automation.
- Provider API calls.

## Acceptance

- Resume is deferred.
- Docs explain why and how to continue manually.
- Docs and command behavior agree.
- New users can tell what `/fig_run` may execute and where it must stop.
- Full verification passes.

## Verification

- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`

## Review Questions

1. Is resume genuinely safer than rerunning `/fig_drive` + `/fig_run` manually?
2. Are stale journal and pending-closeout cases blocked?
3. Can an agent distinguish automatic, semi-automatic, and manual steps?
4. Are future directions separated from implemented behavior?
