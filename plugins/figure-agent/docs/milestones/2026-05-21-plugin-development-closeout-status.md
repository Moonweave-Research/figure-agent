# Figure-Agent Plugin Development Closeout Status

**Date:** 2026-05-21 KST
**Status:** current release-smoke pass after Issue 22E

## Bottom Line

The current plugin-development chain for loop orchestration, top-tier critique
rubrics, visual-clash evidence, high-zoom audit crops, numeric advisory scoring,
SVG-polish surfacing, and publication/export gating is complete enough for
regular dogfood use on current `main`. The later post-closeout critical review
has been resolved through Issue 22E; see
`docs/superpowers/issues/2026-05-21-issue-22-post-closeout-critical-contract-hardening.md`.

This does not mean the plugin can certify final Nature/Science-level artwork by
itself. It means the plugin now exposes the right deterministic gates,
host-vision audit inputs, lint contracts, and stop boundaries so real figure
work can proceed without the previous silent-loop and visual-clash blind spots.

## Release-Smoke Result — 2026-05-21 KST

Commands run from `plugins/figure-agent` on current `main`:

```bash
uv run pytest -q
uv run ruff check .
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
uv run python3 scripts/status.py fig1_overview_v2_pair_001_vault --json
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal smoke --dry-run
uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode release --goal smoke --dry-run
uv run python3 scripts/fig_driver.py smoke_trap_demo --mode authoring --goal smoke --dry-run
```

Results:

- Full test suite: `923 passed, 1 skipped, 1 xfailed`.
- Ruff: clean.
- Claude plugin validation: manifest, plugin directory, and marketplace all
  pass.
- Driver smoke: all sampled fixtures returned valid `figure-agent.driver.v1`
  JSON with `may_execute: false` and a single safe next action.
- Current sampled fixtures are artifact-stale on `main`; this is not a plugin
  core failure. The driver correctly routes them to `/fig_compile` first.
- `fig1_overview_v2_pair_001_vault` still carries human publication provenance
  blockers and stale critique/export state. That remains a fixture closeout
  problem, not a core plugin contract blocker.

## Closed Critical Tracks

- Driver/status/loop routing: `/fig_status` is the canonical first state check,
  `/fig_drive` remains dry-run, and `/fig_loop` remains verify-only.
- Critique freshness and adjudication: hash-aware freshness, adjudication
  schema, sync helpers, and stale-state handling are implemented.
- Top-tier audit rubrics: structural completeness, label-target matching,
  physical plausibility, conceptual completeness, journal-grade assessment,
  top-tier audit, editorial art direction, and micro-defect surfaces are present.
- Visual-clash evidence pipeline: compile emits `build/visual_clash.json`, the
  critique brief ingests the candidates, schema v1.7 assigns stable `VC###`
  ids, and lint requires exact candidate accounting.
- Historical visual-clash regression: host-vision dogfood caught the historical
  `HV+` backdrop overflow and `$V_s$` same-box glyph/internal-drawing failure.
- Accept-simplification loophole: visual-clash-linked `accept_simplification`
  now requires a concrete candidate-specific rationale instead of vague prose.
- CI guardrail: full-render CI compiles fixtures and runs
  `check_visual_clash_budget.py`; ordinary PR CI stays fast and non-rendering.
- Final artifact/polish routing: polished SVG is surfaced as a final-artifact
  state, but SVG editing remains explicit human/external-tool work.
- Release gate binding: release mode now consumes the latest current
  `/fig_loop` checkpoint and will not close release while adjudication, patch
  handoff, or human-gated loop blockers remain unresolved.

## Not A Remaining Blocker

- Existing completed issue files may still contain unchecked historical
  checklist bullets from earlier planning templates. Those are stale checklist
  artifacts, not live blockers, when the issue status says completed and later
  tests/PRs prove the behavior.
- `full-render` is intentionally skipped on normal PRs unless labeled; it runs
  on `main` and label-triggered PRs because the render dependency stack is slow.
- Host-vision critique is still semi-automatic by design. The plugin prepares
  crops, candidate ids, schemas, and lint gates; it does not replace the host
  LLM or human art-direction judgment.

## Residual Optional Hardening

These are useful future improvements, but they are not required before using
the plugin for real figure work:

1. Deterministic historical regression harness:
   generate a disposable fixture that recreates the `HV+`/`V_s` geometry and
   proves the structured lint path rejects weak or missing critique accounting.
2. Structured `accept_simplification_reason` field:
   replace the current natural-language rationale heuristic with an enum plus
   explanation in a future schema version if host prose becomes inconsistent.
3. CI ergonomics:
   periodically run full-render on pull requests with a label or scheduled
   workflow, while keeping normal PR feedback fast.
4. Documentation cleanup:
   normalize stale unchecked bullets in old completed issues if they become
   confusing during handoff.

## Practical Use Guidance

For new real figure work, start with:

1. `/fig_status <name>`
2. `/fig_drive <name> --mode authoring --dry-run`
3. Execute only the returned safe next command.
4. Use `/fig_critique` when the driver reaches a host-vision critique boundary.
5. Run `/fig_loop` after critique/adjudication to record the next loop state.
6. Use `/fig_export` only after render and critique state are fresh enough for
   release/export work.

At this point, core plugin development can pause unless a new dogfood run finds
a concrete contract failure. The next live work should be fixture-specific:
refresh stale renders/critiques/exports, then resolve the human publication
provenance gate for the target figure.
