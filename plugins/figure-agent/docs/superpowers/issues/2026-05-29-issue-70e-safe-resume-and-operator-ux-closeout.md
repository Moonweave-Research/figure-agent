# Issue 70E: Safe Resume And Operator UX Closeout

Status: proposed

Depends on: Issue 70A and whichever of Issues 70B, 70C, and 70D actually ship

Type: HITL/AFK mixed

## Problem

Safe resume is attractive, but unsafe resume is worse than no resume. It should
exist only after stop evidence, patch-executor freshness, and any shipped
handoff or runner-journal contracts are proven. If 70A redirects the roadmap
away from handoff/resume work, 70E becomes a docs-only closeout that records the
manual continuation path and the reason resume was deferred.

## What To Decide Or Build

If 70D lands and real dogfood shows resume is useful, decide whether to add
explicit resume behavior such as:

- `--resume <run_dir>`;
- `--resume-latest`;
- or a decision to keep resume as documentation only.

Any resume command must re-run live status and driver selection. It must never
replay old commands blindly. If this cannot be made safer than rerunning
`/fig_drive` and `/fig_run` manually, resume should remain deferred.

Then close the operator UX:

- README;
- `skills/figure-agent/SKILL.md`;
- `/fig_run`, `/fig_drive`, `/fig_loop`, and `/fig_closeout` docs;
- issue status lines;
- automatic / semi-automatic / manual table.

## Scope

In scope:

- A resume go/no-go decision.
- Resume implementation only if freshness/currentness constraints are explicit.
- Docs-only closeout if 70A or later evidence rejects resume/handoff work.
- Current-truth docs closeout.
- Full verification.

Out of scope:

- Host critique automation.
- Source patch automation.
- Accepted/golden/release automation.
- SVG/vector edit automation.
- Provider API calls.

## Acceptance

- If resume is implemented, stale journals cannot cause command replay.
- If resume is deferred, docs explain why and how to continue manually.
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
