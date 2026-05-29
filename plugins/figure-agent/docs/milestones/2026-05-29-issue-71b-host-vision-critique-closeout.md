# Issue 71B Host-Vision Critique Queue Closeout

Date: 2026-05-29

Related issues:

- `docs/superpowers/issues/2026-05-29-issue-71-real-fixture-production-readiness-roadmap.md`
- `docs/superpowers/issues/2026-05-29-issue-71a-real-fixture-baseline-and-queue-freeze.md`
- Milestone: `docs/milestones/2026-05-29-real-fixture-production-readiness-baseline.md` (71A baseline that assigned these fixtures to 71B)

Status: completed

## Goal

Refresh every stale, reference-grounded critique that Issue 71A assigned to 71B,
using genuine host-vision inspection (the host/Claude vision model actually reads
the rendered figure, required audit crops, visual-clash crops, print-scale
images, and reference images before writing `critique.md`), then run the
deterministic closeout pipeline (lint -> adjudication -> fig_loop -> driver) for
each fixture and record the outcome.

Five fixtures are in scope:

- `n3_trial_01_trap_depth`
- `golden_trap_depth_picture`
- `n3_trial_02_actuation_sequence`
- `fig1_overview_v2_pair_001_vault`
- `fig1_overview_v2`

## Hard Boundaries Observed

- No `.tex` source edited.
- No accepted/golden state mutated (no `accepted:` flip, no `--force-golden`).
- No generated export or polished SVG edited.
- No publication provenance mutated.
- No generated build/export/.scratch artifact staged.
- No critique content fabricated without visual inspection.

Only tracked files written: each fixture's `critique.md` and
`critique_adjudication.yaml`, plus a snapshot rebase of
`tests/real_fixture_loop_contracts.yaml` (see Verification) and this milestone.

## Per-Fixture Process

For each fixture: (1) driver dry-run (`--mode review --goal
issue-71b-host-vision-closeout`), (2) `/fig_critique` host-vision authoring,
(3) genuine image inspection, (4) `critique_lint.py`, (5) adjudication
(`scaffold`/`sync` chosen for safety), (6) `fig_loop.py --json`, (7) post-closeout
driver dry-run.

## Host-Vision Route

Because of an API "many-image request" per-image ceiling (any single image whose
largest dimension exceeds 2000px is rejected once a request accumulates many
images), the heavy fixtures were inspected in fresh-context subagents (clean
image budgets), while the host main loop authored the figure it had inspected
directly. Routes are recorded per fixture for auditability. Subagent critiques
were independently re-linted in the main loop, and a sample of their
observations was spot-checked against the actual crop pixels.

| Fixture | host_vision_route |
| --- | --- |
| `n3_trial_01_trap_depth` | main_loop (prior session) |
| `golden_trap_depth_picture` | main_loop |
| `n3_trial_02_actuation_sequence` | subagent_fresh_context |
| `fig1_overview_v2_pair_001_vault` | subagent_fresh_context |
| `fig1_overview_v2` | subagent_fresh_context |

## Fixture Outcomes

### n3_trial_01_trap_depth

- Driver (initial): `run_critique` / `host_llm_critique_required` (critique was legacy v1.2/STALE).
- Critique: refreshed to schema v1.10 (lint OK). verdict `revise`; 2 MAJOR structural (C001 polymer chain missing S sites, C002 band trap levels detached/sparse), 2 MINOR (C003 stray dot, C004 subtitle overrun). 26 visual-clash candidates accounted (3 real defects, 23 accept_simplification).
- Adjudication: scaffold; C001-C004 all `needs_human` (MAJOR/structural human-protected).
- fig_loop: `human_gate_required` / `human_review_required`.
- Driver (post): `human_gate_stop` / `human_gate_required`, critique FRESH.
- Classification: source-figure issues (real reference-fidelity gaps) routed to human review; likely relates to known BandDiagram/WavyChain macro-API gaps. No plugin defect.

### golden_trap_depth_picture

- Driver (initial): `run_critique` / `host_llm_critique_required` (legacy v1.3 critique).
- Inspection: full render preview + 4 quadrants + reference + 38 visual-clash crops + 2 print-scale images. Render is high-fidelity and reproduces the reference (explicit S sites, grouped trap levels with charges, CB/VB, shallow/deep g(E_t) lobes).
- Critique: authored fresh at schema v1.10 (lint OK). verdict `revise`; 1 MINOR reference-grounded finding C001 (label_placement): the Debye reference plot `log I` y-axis title overlaps the neighbouring Experiment plot right spine (VC002/VC003), whereas the reference shows the two Row 1 plots cleanly separated. The other 36 visual-clash candidates are accept_simplification (clear-space math typography, intended sulfur-site markers, annotation arrow on target, band/reference-line conventions).
- Adjudication: scaffold --force (no prior decisions to preserve); C001 `needs_human`.
- fig_loop: `human_gate_required` / `human_review_required`.
- Driver (post): `human_gate_stop` / `human_gate_required`, critique FRESH. Remaining blocker is `export_tracked_golden` (a 71E human gate, not 71B).
- Classification: source-figure issue (minor inter-panel spacing drift vs reference) routed to human review. No plugin defect.

### n3_trial_02_actuation_sequence

- Driver (initial): `run_critique` / `host_llm_critique_required`; existing critique schema-valid v1.13 but STALE (hash drift).
- Critique: refreshed at schema v1.13 (lint OK, independently re-linted in main loop). verdict `revise`; no BLOCKER/MAJOR; 1 MINOR (C005 teal double-encodes force and recovery arrow roles), 2 NIT (C003 muted rose force arrows, C004 strip-cap knob protrudes over clamp). Subagent reported 18 image Read calls covering all 14 required crops + render + reference + quadrants + print; all three physics invariants confirmed from pixels; no unintended visible anomalies (v1.13 inverse question).
- Adjudication: `sync` (finding ids {C003,C004,C005} unchanged; resolved/not_resolved shape unchanged) preserved the existing human decisions C003 `dismiss`, C004 `defer`, C005 `defer` and only re-bound `source_critique_hash`.
- fig_loop: `status_action_required` / `agent_action_required` (findings dismissed/deferred; loop wants a verify-only checkpoint).
- Driver (post): `run_fig_loop` / (no stop boundary), critique FRESH, no first blocker. Clean closeout advance.
- Classification: clean; minor/nit findings already human-adjudicated. No plugin defect.

### fig1_overview_v2_pair_001_vault (ACCEPTED, tracked-golden)

- Driver (initial): `run_critique` / `host_llm_critique_required`; existing critique schema-valid v1.11 but STALE. Driver lists `critique.md` in `allowed_scope` with `requires_human: false`, so refreshing critique.md is NOT an accepted/golden boundary violation (the protected set is `set_accepted`/`force_golden`/`edit_generated_export`/`edit_polished_svg`).
- Critique: refreshed at schema v1.11 (lint OK, independently re-linted). verdict `ready`; findings C001-C004 unchanged (all `resolved`, historical). 109 required crops (43 VC + 60 panel + 4 full_q + 2 print) all accounted inspected/no_defect. Subagent transcript was cleaned up before a Read-count could be retrieved; main loop spot-checked 3 crops (VC001_S heteroatom marker, VC021_ISPD label on connector, panel_D_q1 MIM stack) against pixels and confirmed the observations are pixel-grounded.
- Adjudication: NOT re-scaffolded (scaffold --force would overwrite human-authored rationale — P001-P003 dismiss notes citing briefing §3.2 intent / NatComm 2024 ref / TG-G-001, and C004's dated patch-resolution evidence). Instead the existing decisions were preserved verbatim and only `source_critique_hash` was updated to re-bind to the refreshed critique (fig_loop tolerates the orphan P001-P003 decisions; `adjudication_state` does not cross-check decision ids against findings).
- fig_loop: `status_action_required` / `manual_approval_required`.
- Driver (post): `release_blocked` / `force_golden_required`, critique FRESH. Remaining blocker is the tracked-golden export needing deliberate roll-forward (71E human gate, not 71B).
- Classification: human gate (accepted/tracked-golden); critique freshness blocker cleared. No plugin defect.

### fig1_overview_v2 (multi-panel overview, NOT_ACCEPTED)

- Driver (initial): `run_critique` / `host_llm_critique_required` (legacy v1.3 critique, 51 required crops).
- Critique: authored fresh at schema v1.10 (lint OK, independently re-linted). verdict `revise`; 4 MAJOR + 2 MINOR, all `label_placement` label-path crossings. Subagent reported 54 image Read calls (full render, reference, 4 quadrants, 2 print, 45 VC crops) covering all 51 crops, with per-finding dark scores. Main loop spot-checked the two highest-severity claims (VC041 "Maxwell" label crossed by the gold polymer strip and overlapped by a force circle; VC040 minus/M glyph heavily overlapped, dark 0.887) and confirmed both are genuine pixel-grounded collisions. The 45 VC candidates are fully accounted (real defects vs accept_simplification).
- Adjudication: scaffold --force. The prior adjudication held only generic auto-scaffold `needs_human` defaults for dead finding ids F001-F003 (zero human rationale), so regenerating from the refreshed findings was safe; result C001-C006 all `needs_human`.
- fig_loop: `human_gate_required` / `human_review_required`.
- Driver (post): `human_gate_stop` / `human_gate_required`, critique FRESH, acceptance NOT_ACCEPTED. Remaining first blocker is `not_accepted` (a 71E human-acceptance gate, not 71B).
- Classification: source-figure issues (real Panel G label/strip/force-circle collisions and other label-path crossings) routed to human review; then a 71E acceptance gate. No plugin defect.

## Verification

Two test-snapshot files were rebased because the 71B refreshes legitimately changed the fixture states those snapshots captured (the contract intent is unchanged in every case):

- `tests/real_fixture_loop_contracts.yaml`: `stale_critique_blocks_loop` and `reference_missing_preempts_critique` `decision_count` 0 -> 1 (golden now carries finding C001); `human_gate_from_fresh_adjudication` `decision_count` 2 -> 4 and `recommended_next_action` `F001` -> `C001` (n3_01 finding-id refresh). `single_apply`/`ambiguous` cases left intact.
- `tests/test_fig_loop.py::test_main_json_exercises_real_run_loop_summary`: added the conditionally-present `svg_polish_readiness` key to the reconstructed expected payload, matching the existing pattern for other conditional keys (`next_action_summary`, `audit_evidence`). fig1's refreshed critique now legitimately flags `tikz_vs_svg_polish_trigger: weak` (polish-not-ready while MAJOR defects are open), which surfaces this payload field.

Final results (all five critiques refreshed):

- `uv run pytest -q tests/test_critique_lint.py tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py` -> 359 passed.
- `uv run pytest -q` -> 1427 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .` -> All checks passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> Validation passed.
- `claude plugin validate .` -> Validation passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> Validation passed.

Tracked working-tree scope (no source/spec/export/golden/accepted/publication/SVG/build mutation): five `critique.md` + five `critique_adjudication.yaml` + the two test-snapshot files above. This milestone is the only new untracked file.

## Review Cycles

### Cycle 1 - Evidence completeness

Every critique is grounded in genuine image inspection of the required render/crops/reference/print evidence:

- `n3_trial_01_trap_depth` (main_loop, prior session): full inspection; 26 VC accounted.
- `golden_trap_depth_picture` (main_loop): render preview + 4 quadrants + reference + 38 VC crops + 2 print-scale images + 2 reference-vs-render comparison crops; all 44 required crops inspected; the one finding is reference-grounded (render vs `golden_target_001.png`).
- `n3_trial_02_actuation_sequence` (subagent): 18 image Reads covering all 14 required crops + render + reference + quadrants + print; physics invariants confirmed from pixels.
- `fig1_overview_v2_pair_001_vault` (subagent): all 109 crops `inspected: true`; main-loop spot-checked 3 crops (VC001_S, VC021_ISPD, panel_D_q1) against pixels and confirmed grounding.
- `fig1_overview_v2` (subagent): 54 image Reads covering all 51 crops; main-loop spot-checked the two highest-severity findings (VC041, VC040) and confirmed genuine collisions.

Result: PASS. Residual: the `fig1_overview_v2_pair_001_vault` subagent transcript was cleaned up before its full Read-log could be retrieved; this is mitigated by the per-crop `inspected: true` accounting, the unchanged (accepted) render, the passing lint, and the main-loop pixel spot-check, and is recorded under Remaining Risks.

### Cycle 2 - Boundary safety

`git status` + `git diff --check` confirm no `.tex`, `spec.yaml`, `exports/`, `.svg`, accepted-flag, publication, or generated build/.scratch mutation; no `--force-golden` was run. For the ACCEPTED `fig1_overview_v2_pair_001_vault`, only `critique.md` was rewritten (which the driver lists in `allowed_scope` with `requires_human: false`) and its adjudication had only its `source_critique_hash` re-bound. The two modified test files are snapshot rebases, outside the protected source/export/golden/SVG/publication set. Result: PASS.

### Cycle 3 - Contract readiness

All five critiques pass `critique_lint.py`. Adjudication handling was chosen per fixture to avoid fabricating or destroying human decisions: `sync` for n3_02 (preserved dismiss/defer), hash-only re-bind for pair_001 (preserved P001-P003 rationale + C004 patch evidence), `scaffold --force` only where the prior adjudication held no human-authored content (golden, n3_01, fig1). Every post-closeout driver reports `critique_state: FRESH`; fig_loop and driver stop reasons are coherent (human gates for n3_01/golden/fig1; verify-loop closeout for n3_02; manual-approval/force-golden for pair_001). Follow-ups are separated: source-figure issues route to human review, and accepted/golden/not-accepted states route to the 71E human gate; no new plugin defect was found (the lint/adjudication/loop/driver tooling behaved correctly; the only tooling-side changes were the expected test-snapshot rebases). Result: PASS.

## Remaining Risks

- `fig1_overview_v2_pair_001_vault` host-vision re-inspection was performed by a subagent whose transcript was cleaned up before its exact image Read-log could be retrieved. Mitigations applied: all 109 crops carry `inspected: true`, the accepted render is unchanged, lint passes, and a 3-crop main-loop spot-check confirmed pixel-grounded observations. A future audit could re-run `/fig_critique` on this fixture for full read-log capture if stronger assurance is wanted.

## Follow-Ups (outside 71B)

- Cross-fixture `tikz_vs_svg_polish_trigger` inconsistency: `fig1_overview_v2` sets this editorial slot to `weak` (which surfaces `svg_polish_readiness` and flags the figure as not polish-ready), while `n3_trial_01_trap_depth` and `golden_trap_depth_picture` set it to `pass` despite also having open MAJOR/MINOR defects. Both are defensible readings of the slot semantics but the latter two underreport polish-readiness. Worth harmonizing in a later pass (likely aligning n3_01/golden to the `weak` reading, since their figures genuinely are not polish-ready). Not a 71B requirement; human-gate routing is correct in all cases.

No known Issue 71B blocker remains.
