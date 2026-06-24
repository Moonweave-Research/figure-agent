# Post-v1.14 Host Critique Refresh Queue

Date: 2026-05-29

Related:

- Issue: `docs/superpowers/issues/2026-05-29-issue-74-post-v1-14-host-critique-refresh-queue.md`
- Plan: `docs/superpowers/plans/2026-05-29-issue-74-post-v1-14-host-critique-refresh-queue.md`
- Predecessor: `docs/milestones-archive/2026-05-29-issue-71b-host-vision-critique-closeout.md` (the v1.10/v1.11 critiques refreshed here were authored in commit `42e70cf`)
- Cause: `docs/milestones-archive/2026-05-29-svg-polish-trigger-semantics.md` / commit `4a3e73b` "Harden SVG polish trigger semantics" (Issue 73 / v1.14)

Status: completed

## Why This Queue Exists

Issue 73 (commit `4a3e73b`) changed `critique_brief.py`, bumping
`generator_version` from `sha256:f7b71b47…` to `sha256:46e53b4c…` and adding a
v1.14 critique contract (editorial route-detail + crop-anomaly accounting for
fixtures on the advanced schema). Hash-based freshness therefore re-marked the
three release/golden/publication candidates stale even though no rendered figure
changed, and each stopped first on `critique_stale` before its true gate.

## Key Discriminator: Inputs Are Byte-Identical

`compute_critique_input_hash` does not depend on `generator_version`; it hashes
the example dir, spec, reference, and style lock. For all three fixtures the
current computed `critique_input_hash` exactly matches the committed critique's
value, proving the critique inputs (render PNG, audit crops, reference) are
bit-for-bit unchanged from the commit-`42e70cf` host-vision inspection:

| Fixture | critique_input_hash (unchanged) |
| --- | --- |
| `golden_trap_depth_picture` | `sha256:af28fe39…` |
| `fig1_overview_v2` | `sha256:814b42a6…` |
| `fig1_overview_v2_pair_001_vault` | `sha256:2deed846…` |

Because the inputs are identical, the v1.10 fixtures need only a
`generator_version` re-stamp (re-running `/fig_critique` would read identical
pixels and produce identical observations), and the v1.11 fixture needs a
schema migration that carries the same observations forward into the v1.14
contract. As an honest current-build attestation the host still read each
fixture's render this session and confirmed it matches the carried-forward
observations.

## Per-Fixture Refresh

Schema/contract decision is feature-driven: `uses_v1_14_contract = reference_learning
or journal_playbook or aesthetic_lever`. Only `fig1_overview_v2_pair_001_vault`
(aesthetic_lever schema) takes v1.14; the other two stay on the v1.10 base.

### golden_trap_depth_picture

- Schema after refresh: `figure-agent.critique.v1.10`, rubric `…v1.10`, generator `sha256:46e53b4c…`, input_hash `sha256:af28fe39…`. verdict `revise` (1 MINOR C001, reference-grounded Debye y-title spacing drift — unchanged from `42e70cf`).
- Change: `generator_version` + `generated_at` re-stamp only; all v1.10 content carried forward.
- Adjudication: `sync` rebound `source_critique_hash`, preserving `C001: needs_human`.
- Render review: `critique_state: FRESH`, `action: human_gate_stop`, first blocker `export_tracked_golden`.
- Release review: `human_gate_stop` / `human_gate_required`, first blocker `export_tracked_golden`.

### fig1_overview_v2

- Schema after refresh: `figure-agent.critique.v1.10`, rubric `…v1.10`, generator `sha256:46e53b4c…`, input_hash `sha256:814b42a6…`. verdict `revise` (4 MAJOR + 2 MINOR label-path crossings — unchanged from `42e70cf`).
- Change: `generator_version` + `generated_at` re-stamp only.
- Adjudication: `sync` rebound hash, preserving `C001..C006: needs_human`.
- Render review: `critique_state: FRESH`, `action: human_gate_stop`, first blocker `not_accepted`.
- Release review: `human_gate_stop` / `human_gate_required`, first blocker `not_accepted`.

### fig1_overview_v2_pair_001_vault (ACCEPTED, tracked-golden)

- Schema migrated `v1.11 -> figure-agent.critique.v1.14`, rubric `…v1.11 -> …v1.14`, generator `sha256:46e53b4c…`, input_hash `sha256:2deed846…` (unchanged). verdict `ready`.
- Changes (schema migration, observations carried forward):
  - Added editorial route-detail: `editorial_art_direction.tikz_vs_svg_polish_trigger.remaining_tikz_lever` (the existing `recommended_path: continue_tikz` was kept; the lever text states the remaining TikZ-source levers — Panel B S-chain tick spacing and Panel C HERO line-weight/label micro-position — so the route stays continue_tikz rather than ready_for_svg_polish).
  - Added crop-anomaly accounting to all 109 `crop_audit_log` entries (`unintended_visible_anomaly: none` + per-crop `anomaly_rationale` + empty `anomaly_link`), reflecting the accepted golden render which carries no unintended artifacts.
  - Kept `aesthetic_lever_audit`, all observations, micro_defects, and the 7 findings (P001-P003 + C001-C004).
- Adjudication: `sync` succeeded and preserved every human decision (P001-P003 `dismiss` with briefing §3.2 / NatComm-2024 / TG-G-001 rationale; C001-C004 `resolved` incl. C004's dated patch-resolution evidence), rebinding only `source_critique_hash`. (`_findings_from_critique` aggregates 7 finding ids, matching the 7 existing decisions, so sync's id/shape check passed — no `--force` and no hand edit needed.)
- Render review: `critique_state: FRESH`, `action: release_blocked`, first blocker `export_tracked_golden`.
- Release review: `release_blocked` / `accepted_or_final_ready_required`, first blocker `export_tracked_golden`.

## Lint / Adjudication / Loop / Driver Table

| Fixture | lint | adjudication | fig_loop | driver review | driver release |
| --- | --- | --- | --- | --- | --- |
| `golden_trap_depth_picture` | OK | sync (C001 needs_human preserved) | human_gate_required | human_gate_stop (export_tracked_golden) | human_gate_stop (export_tracked_golden) |
| `fig1_overview_v2` | OK | sync (C001-C006 needs_human preserved) | human_gate_required | human_gate_stop (not_accepted) | human_gate_stop (not_accepted) |
| `fig1_overview_v2_pair_001_vault` | OK | sync (P001-P003 dismiss + C001-C004 resolved preserved) | status_action_required / manual_approval_required | release_blocked (export_tracked_golden) | release_blocked (accepted_or_final_ready) |

All three report `critique_state: FRESH`; none stops first on `critique_stale`.

## Protected-Scope Confirmation

`git status` / `git diff --check` show only the expected Issue 74 files: the
three `critique.md` files, three `critique_adjudication.yaml` files, this
milestone, and the issue doc. No `.tex`, `briefing.md`, `spec.yaml`, export,
build artifact, polished
SVG, `QUALITY_AUDIT.md`, accepted-flag, or publication-provenance file was
mutated; no `--force-golden` was run; no critique finding was auto-applied.

## Review Cycles

1. **Evidence completeness** — PASS. `critique_input_hash` is byte-identical to commit `42e70cf` for all three fixtures (documented above), so the carried-forward observations remain pixel-grounded; the host additionally re-read each current build render this session to attest. The pair_001 migration added only contract-required structure (route-detail, crop-anomaly) without changing any observation.
2. **Boundary safety** — PASS. Only the six critique/adjudication files changed; `git diff --check` clean; no protected file touched; no force-golden.
3. **Contract readiness** — PASS. All three lint clean; all three adjudications fresh against their critiques with human decisions preserved via `sync`; loop/driver coherent; every fixture advanced past `critique_stale` to a true human/release/golden/acceptance gate.

## Verification Results

- `critique_lint.py` examples/fig1_overview_v2_pair_001_vault | golden_trap_depth_picture | fig1_overview_v2 -> all `OK: critique lint passed`.
- `pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_critique_lint.py tests/test_sync_critique_adjudication.py` -> 401 passed.
- `pytest -q` -> 1434 passed, 1 skipped, 1 xfailed.
- `ruff check .` -> All checks passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` / `.` / `../../.claude-plugin/marketplace.json` -> all Validation passed.

## Remaining Risks / Next True Gates

- `golden_trap_depth_picture`: next gate is the tracked-golden export roll-forward (`export_tracked_golden`, human `--force-golden` decision) and publication provenance, then 71E.
- `fig1_overview_v2`: next gate is human acceptance (`not_accepted`); publication audit still missing.
- `fig1_overview_v2_pair_001_vault`: next gate is the tracked-golden export / accepted-or-final-ready release decision (human-gated); publication gate currently PASS.
- Open follow-up (out of Issue 74 scope, carried from the 71B milestone): `tikz_vs_svg_polish_trigger` reads `weak` on `fig1_overview_v2` but `pass` on `golden`/`n3_01`; v1.14 only enforces route-detail on the advanced-schema fixture (pair_001), so the v1.10 fixtures were not harmonized here.

No known Issue 74 blocker remains.
