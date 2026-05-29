# Issue 75 - SVG Polish Readiness Source-Gate Clarity

Status: completed

Depends on:

- Issue 73 - SVG Polish Trigger Semantics
- Issue 74 - Post-v1.14 Host Critique Refresh Queue

Type: small contract hardening

## Problem

Issue 73 clarified that SVG polish can start only when
`editorial_art_direction.tikz_vs_svg_polish_trigger.recommended_path` is
`ready_for_svg_polish`. Issue 74 then exposed a remaining operator-facing
ambiguity in legacy critiques: several fixtures with open source-level or human
review findings still report `tikz_vs_svg_polish_trigger.verdict: pass` with
`recommended_path: continue_tikz`.

The driver remains safe because `continue_tikz` never authorizes SVG polish.
The gap is explanatory: `svg_polish_readiness` may cite only the editorial
trigger, making a blocked polish handoff look like a clean stylistic routing
choice instead of a source/human gate.

## Goal

Make `svg_polish_readiness` explain source and human loop blockers before
falling back to editorial trigger wording. A fixture with unresolved findings,
human review, patch handoff, or status-action loop stop must not look
"editorially pass-clean" just because the legacy trigger says `pass`.

## Non-Goals

- Do not auto-start SVG polish.
- Do not reinterpret or rewrite existing `critique.md` content.
- Do not make legacy v1.10/v1.13 critiques lint-fail solely because their
  trigger verdict is `pass`.
- Do not change accepted, golden, export, publication, or source mutation rules.
- Do not require host-vision refresh for fixtures that are otherwise fresh.

## Contract

`svg_polish_readiness_from_checkpoint()` should prefer blockers in this order:

1. Existing hard audit blockers already implemented: crop uncertainty, aesthetic
   lever human review, and top-tier high-impact/human blockers.
2. New loop-source blockers:
   - `final_stop_reason: human_gate_required`
   - `final_stop_reason: patch_target_recommended`
   - `final_stop_reason: ambiguous_patch_selection`
   - `final_stop_reason: status_action_required`
   - any other non-`verify_only_complete` stop that represents unresolved loop
     work and is not already handled by a more specific blocker.
3. Existing stored `svg_polish_readiness`, if present.
4. Editorial trigger summary fallback.

The new blocker should return schema `figure-agent.svg-polish-readiness.v1`,
`can_start_svg_polish: false`, `source: latest_loop_checkpoint`,
`next_action` derived from the stop reason, and a blocking item that names the
loop stop instead of only `tikz_vs_svg_polish_trigger`.

## Acceptance

- A checkpoint with `final_stop_reason: human_gate_required` and a legacy
  `pass`/`continue_tikz` editorial summary yields `can_start_svg_polish: false`
  with a human-review source blocker.
- A checkpoint with `final_stop_reason: patch_target_recommended` yields a
  source patch blocker.
- A checkpoint with `final_stop_reason: status_action_required` yields a status
  action blocker.
- A clean checkpoint with `final_stop_reason: verify_only_complete` preserves
  the existing editorial readiness behavior.
- Existing crop/top-tier/aesthetic blocker precedence remains unchanged.
- Driver polish-mode output includes the improved readiness explanation when a
  latest loop checkpoint is present.

## Verification

- TDD red test:
  `uv run pytest -q tests/test_fig_driver_editorial.py::test_svg_polish_readiness_from_checkpoint_prefers_human_gate_over_legacy_pass_trigger tests/test_fig_driver_editorial.py::test_svg_polish_readiness_prefers_patch_target_over_legacy_pass_trigger tests/test_fig_driver_editorial.py::test_svg_polish_readiness_from_checkpoint_preserves_clean_loop_editorial_fallback`
  -> failed before implementation because readiness fell back to the editorial
  trigger (`run_fig_loop`) instead of loop-source blockers.
- Targeted tests:
  `uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_driver.py`
  -> 85 passed.
- Integration tests:
  `uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_driver.py tests/test_fig_loop.py`
  -> 167 passed.
- Full test suite:
  `uv run pytest -q`
  -> 1439 passed, 1 skipped, 1 xfailed.
- Targeted ruff:
  `uv run ruff check scripts/fig_driver_editorial.py tests/test_fig_driver_editorial.py tests/test_fig_driver.py`
  -> All checks passed.
- Full ruff:
  `uv run ruff check .`
  -> All checks passed.
- Plugin validation:
  `claude plugin validate .claude-plugin/plugin.json`, `claude plugin validate .`,
  and `claude plugin validate ../../.claude-plugin/marketplace.json`
  -> all Validation passed.
- Diff check:
  `git diff --check`
  -> clean.
- Real fixture spot-check:
  `uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode polish --goal "Issue 75 source gate clarity" --dry-run`
  -> `svg_polish_readiness.next_action: human_review`,
  `blocking_items[0].id: human_gate_required`.

## Review

1. **Contract correctness** - PASS. The hard rule did not change: SVG polish
   still starts only when the editorial route is `ready_for_svg_polish`.
   Issue 75 only changes the explanation order for non-clean loop checkpoints.
2. **Backward compatibility** - PASS. Legacy critiques remain lint-parseable;
   no `critique.md` content was rewritten, and no schema/rubric version was
   bumped.
3. **Integration readiness** - PASS. Driver polish mode now surfaces the same
   source/human blocker that already controls action routing, so operators see
   the true blocker before editorial fallback wording.

No known Issue 75 blocker remains.
