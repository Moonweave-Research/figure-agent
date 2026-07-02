# Publication Gate Regression Hardening

Date: 2026-07-02

Status: active OMX team execution plan

Branch: `work/review-auto-fixes-2026-06-25`

Primary objective: repair the regressions found after the human-attestation,
SVG-polish retirement, rollback, empty-extraction, and plan-check changes so
release readiness is again a trustworthy operator signal.

## Success Criteria

- Accepted publication candidates cannot pass the golden or status gate without
  a valid human attestation.
- Status/read-only verification never creates files in `HOME` and never
  traceback-crashes on missing keys or malformed attestation content.
- Attestation is bound to the full render-relevant source set, not only the
  top-level `.tex` file.
- Final-artifact fields are either consistently non-blocking generated-export
  compatibility output or are enforced consistently. No dead polished-SVG
  blocker plumbing remains.
- Candidate rollback leaves source, build, and exports consistent with the
  restored source, or clearly reports that manual cleanup is required.
- Text-free PDFs do not crash compile by default; extraction failures remain
  loud only when extraction itself failed or expected text is missing.
- `fig-agent plan-check` works from repo root and plugin root; strict mode is
  documented and testable without pinning live transient fixture state.
- Tests cover the failure modes from the review and avoid pinning live fixture
  transients.

## Team Lanes

### Lane 1: Human Attestation And Publication Gate

Owner: executor worker

Files:

- `scripts/human_attestation.py`
- `scripts/publication_gate.py`
- `scripts/checks/check_golden_artifacts.py`
- `scripts/status.py`
- `tests/test_human_attestation.py`
- `tests/test_publication_gate.py`
- `tests/test_golden_artifact_checks.py`
- `tests/test_status.py`

Tasks:

1. Split key loading from key creation. Verification must read an existing key
   only and return `(False, reason)` for missing/unreadable keys.
2. Make signature validation ASCII/hex-shape checked before
   `hmac.compare_digest`, returning `bad_hmac` instead of raising.
3. Replace `.tex`-only attestation binding with a source-set digest covering the
   render-relevant files used by status freshness where practical. Include
   `briefing.md`, `spec.yaml`, style-lock inputs, and the top-level `.tex`.
4. Wire human attestation into `check_golden_artifacts.py --require-accepted`,
   not only `publication_gate_summary()`.
5. Add regression tests for missing attestation, missing key, read-only HOME,
   non-ASCII signature, and source-set staleness.

Stop condition:

- Targeted human attestation, publication gate, golden artifact, and status
  tests pass.

### Lane 2: Final Artifact, SVG-Polish Retirement, And Candidate Rollback

Owner: executor worker

Files:

- `scripts/status.py`
- `scripts/status_readiness_policy.py`
- `scripts/status_next_policy.py`
- `scripts/candidates/candidate_apply.py`
- `mcp/_legacy_server.py`
- `commands/fig_status.md`
- `commands/fig_loop.md`
- `tests/test_status_readiness_policy.py`
- `tests/test_status.py`
- `tests/test_candidate_apply.py`
- `tests/test_mcp_facade.py`

Tasks:

1. Resolve final-artifact contract after SVG-polish retirement. Prefer deleting
   or downgrading dead polished-SVG blockers over leaving fields that imply
   enforcement that no longer exists.
2. Ensure `release_ready` cannot silently ignore a declared unsupported final
   artifact. Either fail closed with an explicit unsupported-final-artifact
   reason or reject the declaration at status/spec-validation level.
3. Make candidate rollback restore generated exports touched by post-apply
   export checks, or remove them if a clean restore is unavailable.
4. Correct MCP/user-facing messages so `rolled_back` does not claim the working
   tree is unchanged unless exports/build state was actually restored.
5. Fix the self-contradictory MCP facade assertion around `rolled_back`.

Stop condition:

- Candidate apply and status/readiness tests pass with rollback and
  final-artifact regressions covered.

### Lane 3: Extraction, Plan-Check Portability, And Test Hygiene

Owner: executor worker

Files:

- `scripts/checks/check_collisions.py`
- `scripts/checks/check_visual_clash.py`
- `scripts/checks/check_plan_consistency.py`
- `bin/fig-agent`
- `tests/test_poppler_nonutf8_robust.py`
- `tests/test_plan_consistency.py`
- `commands/fig_compile.md`

Tasks:

1. Change empty word extraction from hard RuntimeError to a safe empty result for
   valid graphics-only PDFs. Keep real `pdftotext` failures loud.
2. Add a regression fixture/test proving a non-trivial graphics-only PDF does
   not fail collision or visual-clash extraction.
3. Resolve `fig-agent plan-check` paths against plugin root by default while
   still allowing explicit `--examples-dir` and `--map`.
4. Make `--strict` useful by either filtering advisory known non-main findings
   or documenting/renaming it as "no findings allowed" and keeping it out of CI.
   Tests should use tmp maps, not live fixture drift.
5. Replace live-tree transient pinning in `test_plan_consistency.py` with stable
   tmp-tree or schema-shape assertions.

Stop condition:

- Plan-check tests pass from repo root and plugin root; extraction tests pass.

## Integration Plan

1. Launch `omx team 3:executor` with this plan and the context snapshot.
2. Monitor team status until all worker tasks are terminal.
3. Integrate worker commits from worktrees into the leader branch.
4. Run focused verification:

   ```bash
   cd plugins/figure-agent
   uv run pytest -q tests/test_human_attestation.py tests/test_publication_gate.py tests/test_golden_artifact_checks.py tests/test_status.py tests/test_status_readiness_policy.py tests/test_candidate_apply.py tests/test_mcp_facade.py tests/test_poppler_nonutf8_robust.py tests/test_plan_consistency.py -m "not render"
   uv run ruff check scripts tests bin/fig-agent
   ```

5. If focused verification is green, run:

   ```bash
   uv run pytest -q tests -m "not render"
   ```

## Stop Rules

- Stop and report if workers disagree on the final-artifact contract and the
  codebase does not make one interpretation clearly safer.
- Stop and report if a fix requires a new dependency or a public CLI-breaking
  change outside this plan.
- Do not push. Final output must include changed files, verification evidence,
  and any residual release risk.
