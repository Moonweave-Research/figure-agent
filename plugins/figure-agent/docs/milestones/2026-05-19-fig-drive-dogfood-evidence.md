# Fig Drive Dogfood Evidence

**Date:** 2026-05-19
**Scope:** Issue 8C dry-run driver dogfood
**Status:** complete

## Purpose

This evidence matrix checks whether `/fig_drive --dry-run` gives correct
next-action guidance on real fixtures. It does not approve executor mode,
auto-patching, auto-export, auto-critique, SVG editing, or accepted/golden
mutation.

## Method

Commands were run from `plugins/figure-agent`. For each fixture and mode the
driver was invoked exactly once with the canonical shape:

```bash
uv run python3 scripts/fig_driver.py <name> --mode <mode> --goal "dogfood driver" --dry-run
```

Stdout JSON was captured per cell (20 cells: 5 fixtures × 4 modes). Every cell
exited `0`. No fixture or build/exports/polish/.scratch path was mutated; the
driver is read-only by construction (Issue 8B), and a sentinel `git status -s
examples/` taken before and after the matrix was identical.

Fixtures attempted (all present):

- `fig1_overview_v2_pair_001_vault`
- `golden_trap_depth_picture`
- `smoke_trap_demo`
- `fig3_trapping_concept`
- `fig5_floating_clip_mechanism`

## Evidence Matrix

Verdict rubric (from plan §"Apply the verdict rubric"):

- **correct** — action follows the status vector and selected mode.
- **questionable** — action is defensible but reason, safe command, or
  forbidden actions could confuse a future executor.
- **defect** — action violates Issue 8B contract, suggests a forbidden
  command, or fails to stop at a required boundary.

`workflow_ready` and `release_ready` were `false` for every cell in this
dogfood pass; the columns are omitted from the table to keep widths
manageable and noted inline where they matter for the verdict.

| Fixture | Mode | Action | Stop boundary | safe_command | Render | Critique | Export | Final artifact | Verdict | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| fig1_overview_v2_pair_001_vault | authoring | run_compile | — | `bash scripts/compile.sh examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex` | STALE | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | render STALE; authoring mode escalates to compile before any downstream gate. |
| fig1_overview_v2_pair_001_vault | review | run_compile | — | same as above | STALE | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | render gate fires first; critique gate (`STALE`) waits behind compile per spec state machine. |
| fig1_overview_v2_pair_001_vault | release | run_compile | — | same as above | STALE | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | release also blocked behind render; TRACKED_GOLDEN export is irrelevant until source/build is fresh. |
| fig1_overview_v2_pair_001_vault | polish | run_compile | — | same as above | STALE | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | polish handoff must wait for fresh render even though the fixture is a golden. |
| golden_trap_depth_picture | authoring | complete | — | `null` | FRESH | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | authoring mode terminates once render is FRESH; critique staleness is review-mode work. |
| golden_trap_depth_picture | review | run_critique | host_llm_critique_required | `/fig_critique golden_trap_depth_picture` | FRESH | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | render FRESH → critique gate fires; host LLM must refresh `critique.md`. |
| golden_trap_depth_picture | release | run_critique | host_llm_critique_required | `/fig_critique golden_trap_depth_picture` | FRESH | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | release blocked behind critique (Issue 8A run_critique allowed in release per amended table). |
| golden_trap_depth_picture | polish | run_critique | host_llm_critique_required | `/fig_critique golden_trap_depth_picture` | FRESH | STALE | TRACKED_GOLDEN | NONE/generated_export | correct | polish must close critique before promotion; driver does not skip the gate even though final_artifact_kind is `generated_export` only. |
| smoke_trap_demo | authoring | run_compile | — | `bash scripts/compile.sh examples/smoke_trap_demo/smoke_trap_demo.tex` | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | render gate fires regardless of stale export status. |
| smoke_trap_demo | review | run_compile | — | same as above | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | same. |
| smoke_trap_demo | release | run_compile | — | same as above | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | same. |
| smoke_trap_demo | polish | run_compile | — | same as above | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | same. |
| fig3_trapping_concept | authoring | run_compile | — | `bash scripts/compile.sh examples/fig3_trapping_concept/fig3_trapping_concept.tex` | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | same pattern as smoke_trap_demo; export freshness is downstream. |
| fig3_trapping_concept | review | run_compile | — | same as above | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | render gate first. |
| fig3_trapping_concept | release | run_compile | — | same as above | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | render gate first. |
| fig3_trapping_concept | polish | run_compile | — | same as above | STALE | NOT_REQUIRED | FRESH | NONE/generated_export | correct | render gate first. |
| fig5_floating_clip_mechanism | authoring | run_compile | — | `bash scripts/compile.sh examples/fig5_floating_clip_mechanism/fig5_floating_clip_mechanism.tex` | STALE | NOT_REQUIRED | MISSING | NONE/generated_export | correct | render STALE → compile gate; export MISSING is downstream of render. |
| fig5_floating_clip_mechanism | review | run_compile | — | same as above | STALE | NOT_REQUIRED | MISSING | NONE/generated_export | correct | render gate first. |
| fig5_floating_clip_mechanism | release | run_compile | — | same as above | STALE | NOT_REQUIRED | MISSING | NONE/generated_export | correct | render gate first; export MISSING gate waits behind it. |
| fig5_floating_clip_mechanism | polish | run_compile | — | same as above | STALE | NOT_REQUIRED | MISSING | NONE/generated_export | correct | render gate first; export MISSING gate waits behind it. |

`forbidden_actions` was inspected per cell against `_FORBIDDEN_BY_MODE`; no
cell returned an action that simultaneously appeared in the same response's
`forbidden_actions` list (the regression covered by
`test_release_mode_recommends_critique_without_self_contradicting_forbidden_list`
held across the matrix).

## Findings

**Coverage:** 5/5 listed fixtures present; 20/20 matrix cells executed; every
cell exited `0` with a stable `figure-agent.driver.v1` JSON envelope. No
`missing_fixture` rows were required.

**Verdict distribution:** 20 `correct`, 0 `questionable`, 0 `defect`.

**Decision-tree behaviour observed:**

- The render gate is the dominant stop in this dogfood snapshot — four of five
  fixtures had `render_state: STALE` or worse, so 16 of 20 cells terminated
  at `run_compile`. This is a real-state observation (the working tree's
  build PDFs were older than current sources), not a driver bias.
- `golden_trap_depth_picture` is the only fixture with `render_state: FRESH`,
  and it cleanly exercised four distinct mode outcomes: `complete` for
  authoring, three `run_critique` recommendations with
  `host_llm_critique_required` for review/release/polish. This is the
  per-mode differentiation the driver was built for, and the cross-mode
  consistency confirms the round-2 fixup that removed the
  release-mode/run_critique self-contradiction.
- The export gate, final-artifact gate, polish-handoff branch, and
  `release_blocked` branch were not exercised on real fixtures during this
  dogfood pass because no fixture met the prerequisites
  (`render_state: FRESH` ∧ `critique_state: FRESH | NOT_REQUIRED` ∧
  `export_state: MISSING | STALE | FRESH`). Coverage of those branches is
  preserved by the `tests/test_fig_driver.py` synthetic-status tests
  (`test_release_mode_reports_release_blocked_without_mutation`,
  `test_polish_mode_stops_for_polish_handoff_when_export_current`,
  `test_polish_mode_reports_semantic_backport_required_for_blocked_final_artifact`,
  `test_polish_mode_completes_when_polished_svg_is_fresh`, etc.).

**No real defects found.** No driver patch required; no regression test
added by this milestone.

**Mutation-containment audit:** A `git status -s` snapshot of `examples/`
taken immediately before and immediately after the 20-cell run was
identical. `mtime` of the fixture spec/tex/briefing files was unchanged.
`.scratch/`, `build/`, `exports/`, `polish/` were not touched by any
driver call. No git index mutation was observed.

## Readiness Judgment

Issue 8B's Issue 8A contract (action vocabulary, stop-boundary identifiers,
per-mode allowed/forbidden lists, schema-versioning policy) survives real
fixture exposure without exposing a regression. The driver gives consistent
mode-scoped recommendations, never recommends an action it simultaneously
declares forbidden, and never mutates fixtures.

The dogfood is therefore sufficient evidence to **mark Issue 8B as
shipped without an unfixed blocker** and to leave executor-mode design as
a future issue (8D+ or 7E-related work) rather than an open 8B follow-up.

## Follow-Ups

1. Future executor mode (Issue 8D+) should re-run this matrix after any
   `--execute-safe` work to confirm `may_execute: false` is still the only
   shipped state on read-only invocations.
2. When a fixture reaches `render_state: FRESH` ∧ `critique_state: FRESH`
   simultaneously, rerun the matrix to capture real-world `run_adjudicate`,
   `run_fig_loop`, `run_export`, `release_blocked`, and `polish_handoff_stop`
   evidence on actual data instead of synthetic status. This is a natural
   product of doing real review/release work on any of the listed fixtures;
   no scheduling required.
3. The dominance of `run_compile` in this snapshot signals that fixtures
   were last touched before the latest style-lock / source edits, not a
   driver bias. No mitigation required at the driver layer; user workflow
   simply needs to `/fig_compile` before mode-specific work.

**No known Issue 8C blocker remains.**
