# Issue 64 Loop Summary And Export Closeout UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make v1.13 critique summaries visible in `/fig_loop` and reduce routine export-induced critique freshness churn.

**Architecture:** Keep the fix narrow. `fig_loop_assessments.py` owns schema allowlists and summary extraction, `quality_manifest.py` owns critique input hashing, and `status_next_policy.py` owns operator-facing next-action copy. No state-machine, release, accepted, golden, or source-figure behavior changes are introduced.

**Tech Stack:** Python 3.12, PyYAML, pytest, existing figure-agent scripts.

---

### Task 1: Document Issue 64

**Files:**
- Create: `plugins/figure-agent/docs/superpowers/issues/2026-05-28-issue-64-loop-summary-and-export-closeout-ux.md`
- Create: `plugins/figure-agent/docs/superpowers/plans/2026-05-28-issue64-loop-summary-and-export-closeout-ux.md`

- [x] **Step 1: Capture problem, scope, acceptance, and review questions**

Document the v1.13 loop-summary gap, generated-export freshness friction, and
status next-action wording gap.

### Task 2: Add v1.13 loop-summary regression tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_fig_loop_assessments.py`

- [x] **Step 1: Write failing tests**

Add focused tests that write v1.13 critique frontmatter and assert:

- `journal_grade_assessment()` returns the assessment and
  `reference_calibration_summary`;
- `top_tier_audit_summary()`, `editorial_art_direction_summary()`, and
  `crop_audit_summary()` return summaries for v1.13;
- optional `aesthetic_lever_summary()` and
  `journal_art_direction_playbook_summary()` return summaries when their
  optional v1.13 fields are present.

- [x] **Step 2: Run red tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop_assessments.py -k "v1_13"
```

Expected before implementation: at least one test fails because v1.13 is not in
the relevant allowlists.

- [x] **Step 3: Implement minimal allowlist update**

Modify `scripts/fig_loop_assessments.py` by adding `CRITIQUE_SCHEMA_V1_13` and
including it in the quality axes, top-tier audit, editorial art direction,
crop audit, reference calibration, aesthetic lever, and optional journal
playbook paths where the validator already permits those fields for v1.13.

- [x] **Step 4: Run targeted green tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop_assessments.py
```

Expected: all tests pass.

### Task 3: Add generated-export hash policy tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_quality_manifest.py`
- Modify: `plugins/figure-agent/scripts/quality_manifest.py`

- [x] **Step 1: Write failing tests**

Add tests asserting:

- `exports/<name>.svg` is ignored by `critique_manifest_paths()` for fixtures
  without `spec.yaml.final_artifact.kind: polished_svg`;
- the same generated export SVG is included when `final_artifact.kind:
  polished_svg` is declared.

- [x] **Step 2: Run red tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_quality_manifest.py -k "generated_export_svg"
```

Expected before implementation: the non-polished fixture test fails because the
generated export SVG is currently included.

- [x] **Step 3: Implement minimal policy**

Only append `exports/<name>.svg` to critique manifest paths when
`spec.final_artifact.kind == "polished_svg"` or polish-layer inputs exist.
Leave `polish/aesthetic_delta/*`, `polish/svg_polish_recipe.yaml`, and
`polish/<name>.polished.svg` behavior unchanged.

- [x] **Step 4: Run targeted green tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_quality_manifest.py
```

Expected: all tests pass.

### Task 4: Clarify status next-action copy

**Files:**
- Modify: `plugins/figure-agent/scripts/status_next_policy.py`
- Modify: `plugins/figure-agent/tests/test_status.py` if existing tests assert exact copy

- [x] **Step 1: Inspect exact-copy tests**

Search:

```bash
cd plugins/figure-agent
rg -n "vision review|before treating exports as final|fig_critique" tests/test_status.py tests
```

- [x] **Step 2: Update wording and tests**

Clarify that pre-export critique is a reference-grounded review before export,
while post-export critique is a final snapshot review when required by
freshness.

- [x] **Step 3: Run targeted tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_status.py tests/test_quality_manifest.py tests/test_fig_loop_assessments.py
```

Expected: all tests pass.

### Task 5: Final verification and review

- [x] **Step 1: Run final verification**

```bash
cd plugins/figure-agent
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [x] **Step 2: Critical review**

Review:

- v1.13 latest-schema summaries are visible;
- generated-export hash policy does not weaken polished-SVG contracts;
- status wording changed only operator guidance, not state behavior;
- generated artifacts and unrelated fixture source files are untouched.

- [x] **Step 3: Mark Issue 64 complete**

Update Issue 64 status and verification section only after all checks pass.
