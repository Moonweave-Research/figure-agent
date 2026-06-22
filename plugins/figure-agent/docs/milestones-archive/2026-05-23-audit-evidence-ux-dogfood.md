# Audit Evidence UX Dogfood

**Date:** 2026-05-23 KST
**Branch:** `codex/audit-ux-dogfood`
**Status:** evidence captured; follow-up recommended

## Scope

Dogfood the Issue 25 audit-evidence UX after PR #36 and PR #37 merged:

- `/fig_status` single-fixture output
- `/fig_drive --dry-run` JSON
- `/fig_loop --json` stdout and `decision.md`

This pass did not edit figure source, critique files, adjudication files,
exports, accepted state, or golden state.

## Verification Baseline

```bash
uv run pytest -q tests/test_audit_evidence_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py -q
```

Result: targeted suite passed.

## Fixture Scan

```bash
uv run python3 scripts/status.py | head -80
find examples -path '*/build/visual_clash.json' -o -path '*/build/audit_crops/manifest.json'
```

Observed:

- No tracked `examples/*/build/visual_clash.json`.
- No tracked `examples/*/build/audit_crops/manifest.json`.
- Existing tracked critiques are legacy for current audit-evidence accounting:
  - `fig1_overview_v2_pair_001_vault`: `figure-agent.critique.v1.5`
  - `golden_trap_depth_picture`: `figure-agent.critique.v1.3`
  - `fig1_overview_v2`: `figure-agent.critique.v1.3`

## Runs

### Run 1: `fig1_overview_v2_pair_001_vault`

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode review --goal "audit evidence UX dogfood" --dry-run
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "audit evidence UX dogfood" \
  --runs-root /tmp/figure-agent-audit-ux-dogfood-runs.2qYlS1 --json
```

Evidence:

- `/fig_status` printed:
  - `Audit evidence: legacy`
  - `reason: critique schema predates current audit evidence accounting`
  - `next=/fig_critique fig1_overview_v2_pair_001_vault`
- `/fig_drive` JSON included top-level `audit_evidence` with:
  - `evaluation_state: legacy`
  - `critique_schema: figure-agent.critique.v1.5`
  - `next_action: /fig_critique fig1_overview_v2_pair_001_vault`
- `/fig_loop --json` included top-level `audit_evidence`.
- `decision.md` printed:
  - `audit_evidence_state: legacy`
  - `audit_evidence_blocking: (none)`
  - `audit_evidence_next: /fig_critique fig1_overview_v2_pair_001_vault`

Judgment: useful for identifying that the fixture is not yet on the current
audit-evidence contract. It does not exercise VC/crop blocker surfacing because
the fixture has no current audit report artifacts on disk.

### Run 2: `golden_trap_depth_picture`

```bash
uv run python3 scripts/status.py examples/golden_trap_depth_picture
uv run python3 scripts/fig_driver.py golden_trap_depth_picture \
  --mode review --goal "audit evidence UX dogfood" --dry-run
```

Evidence:

- `/fig_status` printed `Audit evidence: legacy`.
- `/fig_drive` copied top-level `audit_evidence`.
- First blocker remained `render_missing`, which is correct: audit UX did not
  override the canonical status/driver gate.

Judgment: useful for showing additive UX without action-selection regression.

### Run 3: `fig1_overview_v2`

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2
uv run python3 scripts/fig_driver.py fig1_overview_v2 \
  --mode review --goal "audit evidence UX dogfood" --dry-run
```

Evidence:

- `/fig_status` printed `Audit evidence: legacy`.
- `/fig_drive` copied top-level `audit_evidence`.
- First blocker remained `render_missing`.

Judgment: useful for legacy-contract visibility only.

## Findings

### Clean

- `/fig_status`, `/fig_drive`, and `/fig_loop` all surface the shared
  `audit_evidence` object.
- The surfacing is additive: render/critique/export/publication gates remain
  canonical.
- `/fig_loop` decision markdown now gives enough audit-evidence context without
  opening raw JSON.
- No source, export, accepted, golden, critique, or adjudication file was
  mutated.

### Gap

No real tracked fixture on current `main` exercises the full current
audit-evidence path (`visual_clash.json` + audit-crop manifest + current
critique schema). The current dogfood can prove UX propagation, but not the
operator experience for actual `needs_action`, `missing_input`, or
`stale_or_mismatched` VC/crop blockers on a real fixture.

## Recommended Follow-Up

Create a narrow Issue 26: **Audit Evidence Dogfood Fixture Coverage**.

The goal should be to add or generate one deterministic, non-publication fixture
that exercises:

- current critique schema with `micro_defects[].visual_clash_ref`;
- `build/visual_clash.json` candidate accounting;
- `build/audit_crops/manifest.json` hash/freshness behavior;
- one `missing_input`, one `needs_action`, and one `passed` audit-evidence
  scenario through `/fig_status`, `/fig_drive`, and `/fig_loop`.

This should be a plugin QA fixture, not a real manuscript figure.
