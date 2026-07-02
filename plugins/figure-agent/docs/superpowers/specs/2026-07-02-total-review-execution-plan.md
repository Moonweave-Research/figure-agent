# 2026-07-02 Total-Review Execution Plan (Waves B1–B3)

Status: ACTIVE — agent-team execution contract
Branch: `work/review-auto-fixes-2026-06-25` (continue on this branch; do NOT create new branches; do NOT push — the session lead pushes after final verification)
Baseline SHA: `517a4652`. All `file:line` references below were verified at this SHA — **re-grep before editing; line numbers drift as tasks land.**

Origin: 5-axis total review 2026-07-02 (aesthetics-vision / authoring-vocab / schema-deadweight / robustness / paper-fit), building on the 2026-07-01 full audit + P0 fail-closed wave. This plan covers machine-executable Track B only. Track A (author intent: Fig2 ε_r+P–E content, Fig3 S60/bimodal decision, Fig5 story, cohort typography/color decision) is human-only and out of scope here.

## Global invariants — MUST hold after EVERY task

1. Full non-render suite green: `uv run pytest tests/ -m "not render" -q` → 0 failures (baseline has ZERO pre-existing failures; any failure is yours).
2. `uv run ruff check <touched files>` clean.
3. One commit per task (T1b may use two). Message: imperative summary + why-body. End with:
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
4. **Count-sync rule**: `tests/test_release_contract.py` pins the sentence
   `Current inventory is {S} scripts, {T} tests, and {C} command docs.` in
   `docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md`.
   S = `ls scripts/*.py | wc -l` (TOP-LEVEL only; subdirs like scripts/checks/, scripts/svg_polish/ do NOT count), T = `ls tests/test_*.py | wc -l`, C = `ls commands/fig_*.md | wc -l`. If your task changes S/T/C, recompute and update that sentence IN THE SAME COMMIT.
5. **Schema-map rule**: if you delete/add a script defining `SCHEMA`/`*_SCHEMA` constants starting `figure-agent.`, update `docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md` (remove/add the row) in the same commit.
6. Old tests that encode the removed behavior are CORRECTED to the new contract, never deleted wholesale (M6-pattern: if a test's subject is unrelated to the changed contract, monkeypatch/no-op the gate; if its subject IS the old contract, rewrite it to assert the new one).

## Global gotchas (each has burned a prior session)

- Repo path contains literal brackets: `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent` — ALWAYS quote in shell.
- Bare `python3` is blocked by a global hook → always `uv run python3` / `uv run pytest` from the repo dir.
- The edit-hook runs ruff autofix: an import added BEFORE its usage exists gets stripped as F401 → add imports in the SAME edit as the first usage, or after.
- `rm -rf` is blocked by guard_destructive → use `git rm` per path (`git rm -r` for directories is fine).
- Render tests auto-background → always `-m "not render"` for sweeps.
- The pytest `quarantine` marker is registered in `pyproject.toml:26`; its rationale text mentions SVG — T3 rewords it, do not remove the marker registration.
- Do NOT touch `scripts/critique_brief.py` schema-emit branches (`:1612-1650`) in any task except as T2 explicitly bounds. Forcing v1.17 on a fixture without grounded-observation inputs breaks real critique generation.

## Verified import graph (do not re-derive; re-verify only if an import fails)

SVG-polish ENGINE modules with **live core importers** (NOT freely deletable):
- `svg_polish_manifest` ← `status.py:36`, `status_readiness_policy.py:9`, `checks/check_golden_artifacts.py:54`, `svg_ship_gate.py:18`
- `svg_polish_delta` ← `fig_driver.py:44`, `critique_lint.py:66`, `critique_brief.py:62`
- `svg_ship_gate` ← `checks/check_golden_artifacts.py:64`
- `svg_semantic_diff` ← `svg_ship_gate.py:19`; `svg_path_geometry` ← `svg_semantic_diff.py:30`, `add_volume_shading.py:7`

SVG-polish LEAF modules with **zero importers outside the stack** (freely deletable): `svg_polish/svg_polish_executor.py`, `svg_polish/svg_polish_handoff.py`, `svg_polish/svg_polish_recipe.py`, `svg_polish/svg_polish_positive_harness.py`, `add_volume_shading.py` (~1,708 LOC).

CLI wiring: `bin/fig-agent:32` (sys.path `svg_polish`), `:277-280` (allowlist entries), `:321-338` `_svg_polish_exec`, `:340-348` `_svg_polish_delta`, dispatch `:1393`,`:1395`. `run_export.py:31` also adds `svg_polish` to sys.path. Composition dispatch: `bin/fig-agent:1424` (`compose-*`), `composition_cli.py:384-397`.

Route-name STRINGS like `ready_for_svg_polish` across driver/status/critique are handoff LABELS (schema v1.6+ semantics), not engine imports — they SURVIVE T1a/T1b.

---

## WAVE 1 — Cleanup

### T4 — Delete 4 orphan MCP shims  [S]
Goal: remove `mcp/_runtime.py`, `mcp/_protocol.py`, `mcp/_validation.py`, `mcp/_resources.py` — 100% `globals().update(...)` re-export shims with ZERO importers (verified; same anti-pattern removed once at `8d58d10d` for `_handlers_*.py`).
Boundary: `mcp/_legacy_server.py` and `mcp/figure_agent_server.py` are LIVE — do not touch.
Steps: re-verify zero importers (`grep -rn "_runtime\|_protocol\|_validation\|_resources" mcp/ scripts/ tests/ bin/ --include="*.py"` — matches must be only the shims themselves); `git rm` the 4 files; sweep `uv run pytest tests/ -k "mcp" -m "not render"`.
Acceptance: suite green; no references remain.

### T5 — Archive dead fixture stub  [S]
Goal: `git rm -r examples/ispd_measurement_setup/` (Python stub only: no spec.yaml/briefing/.tex/build; its concept belongs to Fig4's DATA half, owned by the external pipeline).
Evidence: only reference in tree = `docs/milestones-archive/2026-05-29-...baseline.md` (archive doc — leave it).
Boundary: do NOT touch `fig3_trapping_concept`, `fig2_trap_design_space`, `fig3_floating_clip_protocol` — their re-scope needs author decisions (Track A).
Acceptance: suite green (`test_real_fixture_audit_adoption` iterates `examples/*/spec.yaml` — the stub has none, so no contract change expected; verify).

### T9 — Delete the never-running layout-drift checker  [S]
Goal: `scripts/checks/check_layout_drift.py` (541 LOC) self-skips without `examples/*/coordinate_hints.yaml` (`:479-480`) and without `golden_contract.required_labels` (`:476-477`); NO fixture has coordinate_hints.yaml; no automated caller (only `bin/fig-agent:258` passthrough + optional manual step in `commands/fig_compile.md:58`). Advertised-but-never-running verification = theater. DECISION: delete.
Steps: `git rm` module + its test file(s) (`grep -l "layout_drift" tests/`); remove the `bin/fig-agent` passthrough entry + the `commands/fig_compile.md` step 7 mention; grep docs for `layout_drift`/`coordinate_hints` and prune stale mentions. Count-sync (test count changes; script is in checks/ subdir → S unchanged). Schema-map rule if it defines a schema constant.
Acceptance: `grep -rn "layout_drift" scripts/ tests/ bin/ commands/` → empty; suite green.

### T10 — vtrace: honor the `status:"failed"` contract  [S]
Goal: `vtrace.py` try/except at `:99-119` covers only conversion+parse; post-processing `:121-621` runs unguarded, and caller `reference_extract.py:190` doesn't wrap → an exception crashes `/fig_extract` instead of degrading to `structural_regions.status:"failed"` (contract: `commands/fig_extract.md:80`).
Steps (TDD): RED test — monkeypatch a post-processing helper to raise (or feed `img_w==0` → ZeroDivision at `:97`-adjacent), assert the function returns `{"status":"failed", ...}` instead of raising. GREEN: widen the existing `try:` to cover post-processing through return.
Acceptance: RED→GREEN; existing vtrace tests pass unchanged.

### T1a — Delete SVG-polish LEAF modules + CLI + fixture  [M]
Goal: remove the inert authoring engine (recipes target dvisvgm `element_id`s that real output never has — `svg_polish_recipe.py:1` inert header; reach=0 since 2026-05-26 milestone "real fixture does not route to SVG polish yet").
Delete set: `scripts/svg_polish/svg_polish_executor.py`, `svg_polish_handoff.py`, `svg_polish_recipe.py`, `svg_polish_positive_harness.py`; `scripts/add_volume_shading.py`; tests `test_svg_polish_executor.py`, `test_svg_polish_handoff.py`, `test_svg_polish_recipe.py`, `test_svg_polish_positive_harness.py`, `test_svg_polish_clean_dogfood.py`, `test_svg_polish_gate_completeness.py`, `test_add_volume_shading.py`; fixture `examples/_volume_shading_demo/` (git rm -r).
CLI: remove `bin/fig-agent` `_svg_polish_exec` (`:321-338`) + dispatch `:1393`; remove allowlist entries for executor/handoff/recipe (`:277-279`).
KEEP (live importers — see graph): `svg_polish_manifest.py`, `svg_polish_delta.py`, `svg_ship_gate.py`, `svg_semantic_diff.py`, `svg_path_geometry.py`, `svg_polish/__init__.py` (prune its exports of deleted names), `_svg_polish_delta` CLI (imports svg_polish_delta — dies in T1b).
Known coupling: `tests/test_fig_queue.py` references `_volume_shading_demo` — correct that test to another fixture or drop the specific case per invariant 6. `pyproject.toml:26` marker rationale mentions `_volume_shading_demo` — reword in T3 (not here).
Acceptance: suite green; count-sync (S −1: add_volume_shading; T −7); schema-map rule for any deleted schema constants.

### T1b — De-polish the core (status/critique/driver/golden)  [L — the one semantic refactor]
Goal: remove polish-awareness from live core so the remaining engine (`manifest`/`delta`/`ship_gate`/`semantic_diff`/`path_geometry`) loses its last importers, then delete it. End state: `scripts/svg_polish/` gone, zero `svg_polish_*`/`svg_semantic_diff`/`svg_ship_gate`/`svg_path_geometry` modules.
Per-site instructions (re-grep first):
- `status.py:36` + `status_readiness_policy.py:9` (svg_polish_manifest): drop polished-SVG branches from final-artifact/readiness state; exports-based state stays.
- `checks/check_golden_artifacts.py:54,64`: golden gate stops consulting `FINAL_ARTIFACT_POLISHED_SVG` / `render_ship_gate_failures`; plain exports contract remains.
- `fig_driver.py:44` (svg_polish_delta staleness): remove the staleness consult; the `ready_for_svg_polish` ROUTE LABEL stays (handoff semantics — external tool, not this engine).
- `critique_brief.py:62` + `critique_lint.py:66` (svg_polish_delta): remove svg-delta pack reading/validation. In the validator, remove the OPTIONAL `svg_polish_delta_audit` hooks (v1.17 branch `critique_schema_validator.py:1647-1649`-region `if "svg_polish_delta_audit" in frontmatter:` block and the v1.15/v1.16-specific helpers if they become orphaned) + `SVG_POLISH_DELTA_AUDIT_SCHEMAS` in critique_lint. No real fixture sets this key (verified) → no artifact migration.
- `critique_brief.py` v1.17-selection predicate (`:1613` region): remove the svg-delta-section disjunct; grounded-crop/undeclared-geometry disjuncts stay.
Then: `git rm -r scripts/svg_polish/`; `git rm scripts/svg_semantic_diff.py scripts/svg_ship_gate.py scripts/svg_path_geometry.py`; tests `test_svg_polish_manifest.py`, `test_svg_polish_delta.py`, `test_svg_semantic_diff.py`, `test_svg_ship_gate.py`, `test_svg_path_geometry.py` — delete engine-only ones; consumer tests (status/golden/driver/lint) are CORRECTED to the de-polished contract. Remove `bin/fig-agent:32`/`run_export.py:31` sys.path lines, `_svg_polish_delta` (`:340-348`) + dispatch `:1395`, allowlist `:280` (svg_semantic_diff).
Boundary: do NOT remove route-label strings or v1.6+ schema route vocabulary; do NOT touch composition.
Acceptance: `grep -rn "svg_polish\|svg_semantic_diff\|svg_ship_gate\|svg_path_geometry" scripts/ bin/ --include="*.py"` → only route-label strings remain (no imports); suite green; count-sync (S −3, T −5 approx — recompute); schema-map rows for svg-polish-delta/ship-gate schemas removed. Two commits allowed: (1) de-import core, (2) delete engine.

### T2 — Critique-schema floor: retire non-emittable versions  [L]
Goal: supported set = **{v1.10, v1.14, v1.17}** (exactly the three `critique_brief.py` can emit — `:1647`, `:1630`, `:1613`). Versions v1.1–v1.9, v1.11–v1.13, v1.15–v1.16 (14 elif shims): 0 real artifacts (all 6 `examples/*/critique.md` are v1.17 — verified), not emittable → RETIRE, mirroring the M6 v1-reject pattern (`f9e7bbcc`).
Steps (TDD):
1. RED: parametrized test — each retired version string → `CritiqueContractError` matching "retired".
2. Vocab: add `RETIRED_CRITIQUE_SCHEMAS` frozenset to `critique_schema_vocab.py`; keep constants `V1_10`, `V1_14`, `V1_17` (+ retired constants may be deleted once no live reference remains — follow invariant 6 for `tests/test_critique_schema_vocab.py`).
3. Validator (`critique_schema_validator.py:1390-1664`): membership check → raise `CritiqueContractError(f"{schema} is retired: ... Re-run /fig_critique")`; delete the 14 elif shims. **Keep ALL `_validate_v1_*` helpers** — the v1.17 branch calls every one (verified: no helper is unreachable from v1.17); v1.10/v1.14 branches stay.
4. Accepted-sets: collapse to the 3 live versions in `fig_loop_assessments.py` (6 frozensets), `critique_lint.py`, `critique_evidence_lint.py`, `quality/quality_manifest.py`.
5. Test migration (~25 files reference sub-v1.17 tags): per invariant 6 — tests whose SUBJECT is version-specific validation (e.g., `test_critique_lint.py` uses v1.3/v1.4/v1.5 fixtures) migrate their frontmatter to the nearest live version (usually v1.10; add required blocks — the test files already carry `_complete_*_yaml` helpers); tests whose subject is unrelated sync/plumbing use the autouse-no-op pattern from `tests/test_sync_critique_adjudication.py` (top of file).
Boundary (⚠ only risky edit in this wave): do NOT collapse the producer's v1.10/v1.14 emit branches; v1.17-only emission requires guaranteeing grounded-observation inputs on every fixture — explicitly deferred.
Acceptance: RED→GREEN; suite green; schema-map updated (mark retired rows); `docs/` grep for stale "v1.2–v1.16 supported" claims.

### T3 — Quarantine the composition stack  [S]
Goal: 3,423 LOC / 17 `composition_*.py` modules reach `accept` only on gitignored local dogfood; 5/6 committed fixtures lack `% fig-agent:start` markers; `FAMILY_DATA` hardcodes fig3 objects and raises `selector_missing:current_sparkline` at HEAD (`composition_families.py:78`, templates `:5-113`) — CI-invisible because all 75 tests build synthetic tmp fixtures. Do NOT delete (newest stack, one real E2E accept); mark honestly.
Steps: add `pytestmark = pytest.mark.quarantine` to the 16 composition test files; reword `pyproject.toml:26` marker rationale to cover both retired-SVG history and composition ("inert on committed real figures"); add a 3-line INERT header to `composition_families.py` + `composition_cli.py` stating the selector_missing regression + revisit condition (N≥3 real figures); note in `docs/architecture-overview.md` composition section.
Boundary: zero behavior change; code stays.
Acceptance: `uv run pytest tests/ -m "quarantine" -q` collects the composition tests; suite green.

## WAVE 2 — Gate hardening (fail-loud on the human-decision layer)

### T6 — Human attestation for the publication gate (F5, HIGH)  [M]
Problem (repro'd E2E): the release chain is satisfiable by agent-written plaintext — `publication_gate.py:101` regex-matches `submission-safe: true` in QUALITY_AUDIT.md; `accepted` = literal bool in spec.yaml (`status.py:227-233,662-667`); `human_decision_record.validate_decision_record` (`:142-235`) is structural-only; `fig_driver.py:977` unblocks release on PASS.
Design (implement as specified):
- New `scripts/human_attestation.py`:
  - CLI `create <fixture>`: hard-fail unless `sys.stdin.isatty()` ("human attestation requires an interactive terminal"); interactive confirm (retype fixture name); payload `{schema:"figure-agent.human-attestation.v1", fixture, tex_sha256, created_at}`; signature = HMAC-SHA256 over `fixture|tex_sha256` keyed by `~/.figure-agent/attest.key` (auto-create 0600 on first use; NEVER inside the repo); write `examples/<fixture>/human_attestation.json`.
  - Library `verify_attestation(example_dir) -> (bool, reason)`: fail-closed — missing file / schema mismatch / bad HMAC / tex_sha256 ≠ current tex hash (stale) → `(False, reason)`.
- `publication_gate.py`: `accepted:true` / `submission-safe:true` additionally require `verify_attestation` PASS; failure reason surfaces in the gate output.
- `bin/fig-agent` subcommand `attest` → the CLI. Driver/queue guidance strings point to `fig-agent attest <fixture>`.
Threat model note (put in module docstring): boundary is "cannot pass by accident or by well-formed text alone"; a deliberate local key-read forge is out of scope, consistent with the executor-allowlist philosophy.
TDD: forged JSON w/o valid HMAC → fail; stale tex hash → fail; valid attestation (key in tmp HOME via monkeypatched env) → pass; non-TTY create → hard error. Existing publication-gate tests: correct to the new contract (invariant 6).
Acceptance: E2E repro from the robustness report now FAILS (agent-writable files alone cannot PASS); suite green; count-sync (+1 script, +1 test file); schema-map row added.

### T7 — Silent-empty guard on word extraction (F2, MED)  [S]
Problem: rc==0 with 0 extracted words = "clean" in `check_collisions.py` (`extract_word_bboxes`, loud only on rc≠0 at `:29`) and `check_visual_clash.py` (`extract_pdf_words_and_page`, `:50,:60`) → detector chain (collisions/visual-clash/undeclared-geometry/hyphenation/text-boundary/label-path) fail-quiet on a text-empty PDF. Asymmetric with M3's fail-closed value gate.
Fix: in both extractors — rc==0 AND 0 words AND PDF non-trivial (>1KB or ≥1 page) → raise `RuntimeError("empty_extraction: pdftotext returned 0 words for non-trivial PDF ...")`. No allow-flag (every real fixture has text; a legit 0-word PDF should fail loud and be triaged).
TDD: RED — monkeypatch subprocess to return rc=0/empty output with a real-size PDF path → assert raise; existing behavior tests for populated PDFs unchanged.
Acceptance: RED→GREEN; downstream detector tests green (they monkeypatch extractors with words — verify none feed empty-and-expect-clean; correct such tests per invariant 6).

### T8 — Rollback must not burn the candidate or leave stale state (F1, MED)  [M]
Problem: `candidate_apply.py` rollback (`:871-874`) restores `.tex` but leaves the mutated build PDF (compiled at `:851`) AND records `result_status="applied_with_failed_verification"` (`:877-881`) which is in `TERMINAL_APPLY_STATUSES` (`:23-27`) → re-apply blocked forever at `:771` ("already_applied") for a net-unapplied candidate.
Fix contract:
- After restoring source: recompile via the existing `_compile_current_source` path; if recompile fails, DELETE `build/<name>.pdf` (never leave a PDF that doesn't match source).
- New status `"rolled_back"`: written to apply_result, NOT terminal — `:771` guard must allow re-apply. Keep the old constant recognized as terminal for pre-existing artifacts (back-compat parse), but never write it for rollbacks again.
TDD: RED (1) apply→verifier-fail→rollback then re-apply → currently "already_applied", must become allowed; RED (2) after rollback, build PDF content matches restored source (or is absent). Consumer greps: `grep -rn "applied_with_failed_verification\|TERMINAL_APPLY_STATUSES" scripts/ tests/` — correct consumers to the new status per invariant 6.
Acceptance: RED→GREEN; candidate/apply suite + MCP apply tests green.

## WAVE 3 — Plan-consistency check

### T11 — fixture ↔ canonical-plan consistency check (report-only)  [M]
Problem: 3/5 planned figures carried plan-drift detectable only by a human cross-reading `docs/superpowers/specs/2026-06-22-sulfur-paper-figure-plan-design.md` (fig2_trap_design_space over-claims vs plan `:53-55`; fig5 fixture is a sandbox; three fig3_* for one slot). #1 per-figure time-sink per production dogfood.
Design:
- New `docs/paper_figure_map.yaml` (machine-readable mapping; the plan doc stays prose-canonical):
  ```yaml
  schema: figure-agent.paper-figure-map.v1
  plan_doc: docs/superpowers/specs/2026-06-22-sulfur-paper-figure-plan-design.md
  figures:
    fig1: {fixtures: [fig1_overview_v2_pair_001_vault], role: "concept/structure overview schematic"}
    fig2: {fixtures: [], role: "dielectric polarization: eps_r vs composition + P-E loops", status: missing}
    fig3: {fixtures: [fig3_resistance_mechanism], role: "cell -> current -> trapping -> R(t) rise mechanism schematic"}
    fig4: {fixtures: [fig4_trap_energy_diagram], role: "trap energy landscape: shallow vs deep, retention"}
    fig5: {fixtures: [], role: "cantilever actuation 3-step: injection -> repulsion -> relaxation", sandbox: [fig5_actuation_mechanism]}
  non_main: {si: [fig3_floating_clip_protocol], superseded: [fig3_trapping_concept], rescope_pending: [fig2_trap_design_space]}
  ```
  (Adjust wording against the plan doc while writing; every committed non-underscore fixture must appear somewhere.)
- New `scripts/checks/check_plan_consistency.py` (report-only, exit 0 unless `--strict`): (a) every `examples/*/spec.yaml` fixture (non-`_`/non-`smoke_`) appears in the map; (b) mapped fixtures exist; (c) fixture `briefing.md` first 5 lines contain the mapped role's key tokens (case-insensitive word match on 2+ content words) — else `role_drift` finding; (d) fixtures under `sandbox:`/`superseded:`/`rescope_pending:` reported as such. JSON output `figure-agent.plan-consistency.v1`.
- `bin/fig-agent` passthrough `plan-check`. No status/loop wiring in this task (follow-up candidate).
TDD: RED with tmp fixture tree — unmapped fixture, missing-role-token briefing, sandbox flag each produce the right finding; then run against the REAL tree and assert it reports (at minimum) fig2 missing + fig5 sandbox + fig3_trapping_concept superseded.
Acceptance: real-tree run reproduces the 3 known drifts; suite green; count-sync (+1 test file; script in checks/ → S unchanged); schema-map rows for the 2 new schemas.

---

## Execution order (serial; stop the wave on a blocked task, later waves may still run if independent)

W1: T4 → T5 → T9 → T10 → T1a → T1b → T2 → T3
W2: T7 → T8 → T6
W3: T11
Dependencies: T1a before T1b before T2 (T1b removes the v1.15/16 svg-delta validator hooks T2 would otherwise have to reason about). T4/T5/T9/T10 independent warm-ups. W2 independent of W1 except T8 touches `candidate_apply.py` (no W1 task touches it).

## Completion checklist (final verifier)

1. `uv run pytest tests/ -m "not render" -q` → 0 failed.
2. `uv run ruff check scripts/ tests/ bin/fig-agent` → clean.
3. Count-sync + schema-map consistent (release-contract tests green — they enforce this).
4. `grep -rn "svg_polish\|svg_semantic_diff\|svg_ship_gate" scripts/ bin/ --include="*.py"` → route-label strings only.
5. Retired schema tag (e.g. v1.5) in a critique.md → validator raises "retired".
6. Robustness F5 repro (agent-writable `accepted:true` + `submission-safe:true`, NO attestation) → gate FAILS.
7. `fig-agent plan-check` on real tree reports fig2-missing + fig5-sandbox + fig3_trapping_concept-superseded.
8. Do NOT push; report commit list to the session lead.
