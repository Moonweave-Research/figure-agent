# Issue 71E Release, Golden, And Publication Gate Rehearsal

**Status:** completed with upstream critique-refresh caveat

## Purpose

Rehearse release, accepted, tracked-golden, force-golden, and publication
boundaries on real fixtures without mutating accepted state, golden artifacts,
exports, publication provenance, source figures, or SVG polish artifacts.

This pass was run after Issue 73 changed `critique_brief.py`, which correctly
made several hash-fresh critiques stale by generator version. That freshness
gate takes priority over force-golden/release decisions.

## Fixtures

Primary Issue 71 release candidates:

- `fig1_overview_v2_pair_001_vault`
- `golden_trap_depth_picture`
- `fig1_overview_v2`
- `fig5_floating_clip_mechanism`

Additional non-critique release-boundary controls:

- `fig3_trapping_concept`
- `smoke_trap_demo`

## Commands

For each fixture:

```bash
uv run python3 scripts/status.py examples/<fixture>
uv run python3 scripts/fig_driver.py <fixture> --mode release --goal "Issue 71E release gate rehearsal" --dry-run
uv run python3 scripts/fig_run.py <fixture> --mode release --goal "Issue 71E release gate rehearsal" --execute --no-record
uv run python3 scripts/check_golden_artifacts.py examples/<fixture>
```

Tracked working-tree status was checked before and after the rehearsal with
`git status --short --untracked-files=no`; both were empty.

## Results

| Fixture | Status first blocker | Driver action / boundary | Runner result | Golden/publication check |
|---|---|---|---|---|
| `fig1_overview_v2_pair_001_vault` | `critique_stale`; publication `PASS`; accepted/tracked-golden candidate remains behind fresh critique | `run_critique` / `host_llm_critique_required` | `host_boundary`, `executed_count: 0`, actor `host_llm` | Fails accepted golden checks: missing required labels/inventory and stale or missing `QUALITY_AUDIT.md` |
| `golden_trap_depth_picture` | `critique_stale`; publication `HUMAN_ACCEPTANCE_REQUIRED` | `run_critique` / `host_llm_critique_required` | `host_boundary`, `executed_count: 0`, actor `host_llm` | Fails accepted/golden/publication checks: not accepted, stale/missing audit, missing theory guard/reference pack, unresolved visual clash budget |
| `fig1_overview_v2` | `critique_stale`; publication `HUMAN_ACCEPTANCE_REQUIRED` | `run_critique` / `host_llm_critique_required` | `host_boundary`, `executed_count: 0`, actor `host_llm` | Fails golden contract mode because no `golden_contract` is declared |
| `fig5_floating_clip_mechanism` | `export_missing`; publication `HUMAN_ACCEPTANCE_REQUIRED` | `release_blocked` / `accepted_or_final_ready_required` | `not_executable_action`, `executed_count: 0`, actor `release_operator` | Fails artifact-shape checks because all export artifacts are missing |
| `fig3_trapping_concept` | no publication blocker; release not ready | `release_blocked` / `accepted_or_final_ready_required` | `not_executable_action`, `executed_count: 0`, actor `release_operator` | Basic artifact-shape gate passes |
| `smoke_trap_demo` | no publication blocker; release not ready | `release_blocked` / `accepted_or_final_ready_required` | `not_executable_action`, `executed_count: 0`, actor `release_operator` | Fails basic SVG shape check: visible elements `28 < 40` |

## Human Approval Requirements

- `fig1_overview_v2_pair_001_vault`: rerun host `/fig_critique` after Issue 73,
  then a human must explicitly decide whether to roll tracked golden forward
  with `--force-golden`. The plugin must not infer this from `accepted: true`.
- `golden_trap_depth_picture`: rerun host `/fig_critique`; human acceptance,
  publication provenance, theory guard/reference-pack, visual-clash budget, and
  any future tracked-golden roll-forward remain explicit gates.
- `fig1_overview_v2`: rerun host `/fig_critique`; human acceptance and
  publication audit must be resolved before release-style use.
- `fig5_floating_clip_mechanism`: export artifacts are missing, but
  `acceptance_state: NOT_ACCEPTED` prevents `/fig_run --execute` from
  auto-exporting in release mode. A release operator must resolve acceptance or
  explicitly operate the draft/export path outside release mode.
- `fig3_trapping_concept` and `smoke_trap_demo`: not release-ready because no
  accepted/golden/final-artifact gate is satisfied. Runner stops at the release
  operator boundary instead of mutating acceptance.

## Review

### 1. Release Decision Clarity

PASS. The driver separates host-critique freshness from release approval. Where
freshness is stale, release mode stops at `host_llm_critique_required` instead
of skipping ahead to accepted/golden decisions. Where freshness is not the
blocker, release mode stops at `accepted_or_final_ready_required`.

### 2. Golden Roll-Forward Safety

PASS. No `--force-golden` command was surfaced as executable. `/fig_run
--execute --no-record` executed zero shell commands for every release rehearsal
row.

### 3. Publication Provenance Visibility

PASS. Publication failures are typed in driver status for not-accepted
publication candidates. Missing `QUALITY_AUDIT.md`, missing compliance
sections, and missing `submission-safe: true` are visible as human/agent
actions; none were fabricated.

### 4. Next Hardening Signal

The main operational caveat is now expected freshness churn: after
`critique_brief.py` changes, hash-based critiques become stale before release
rehearsal can reach force-golden decisions. This is correct for safety, but it
means a release rehearsal after critique-contract work must begin with a
host-vision refresh queue.

## Outcome

Issue 71E did not find a code defect in release/golden/publication mutation
containment. The plugin remained conservative:

- no accepted state changed;
- no golden artifact changed;
- no `--force-golden` ran;
- no export artifact was regenerated;
- no publication provenance file was written;
- no source or SVG polish file changed;
- no `.scratch` run journal was written because `--no-record` was used.

The release workflow is safe but not frictionless: current real release
candidates require host critique refresh and human publication/acceptance
decisions before any final artifact update can be considered.

## Verification

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

- `1434 passed, 1 skipped, 1 xfailed, 6 warnings`
- `ruff`: all checks passed
- `git diff --check`: clean
- plugin manifest validation: passed
- plugin directory validation: passed
- marketplace validation: passed

No known Issue 71E release-boundary blocker remains.
