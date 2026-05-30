# Issue 74 Post-v1.14 Host Critique Refresh Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the post-v1.14 stale host-vision critique queue and prove the plugin routes each fixture to its next true gate without hidden mutation.

**Architecture:** Codex handles deterministic planning, linting, adjudication checks, loop/driver verification, documentation, and commits. Claude host vision handles `/fig_critique` because it must read render images, crops, references, and print-scale artifacts. The queue closes only when lint/adjudication/loop/driver evidence agrees.

**Tech Stack:** figure-agent slash-command contracts, Python scripts under `plugins/figure-agent/scripts/`, markdown issue/milestone docs, pytest/ruff/plugin validation.

---

## File Structure

- Modify: `plugins/figure-agent/examples/<fixture>/critique.md`
  - Host vision writes refreshed critique content.
- Modify: `plugins/figure-agent/examples/<fixture>/critique_adjudication.yaml`
  - Codex/Claude syncs or scaffolds adjudication against the refreshed critique.
- Create: `plugins/figure-agent/docs/milestones/2026-05-29-post-v1-14-host-critique-refresh-queue.md`
  - Records commands, evidence, fixture outcomes, reviews, and verification.
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-29-issue-74-post-v1-14-host-critique-refresh-queue.md`
  - Set status to completed and link the milestone after closeout.

Do not modify source `.tex`, `briefing.md`, `spec.yaml`, exports, accepted/golden state, publication provenance, polished SVGs, or generated build artifacts.

## Task 1: Confirm Queue And Protected Scope

- [ ] **Step 1: Check clean tracked state**

Run from repo root:

```bash
git status --short --branch
```

Expected: no unrelated dirty tracked files except this issue/plan if they are already staged in the current task.

- [ ] **Step 2: Confirm current status for each queued fixture**

Run from `plugins/figure-agent`:

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
uv run python3 scripts/status.py examples/golden_trap_depth_picture
uv run python3 scripts/status.py examples/fig1_overview_v2
```

Expected: each reports `critique: stale` and a `Next:` command containing `/fig_critique <fixture>`.

- [ ] **Step 3: Confirm driver boundary for each queued fixture**

Run:

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal "Issue 74 host critique refresh" --dry-run
uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "Issue 74 host critique refresh" --dry-run
uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "Issue 74 host critique refresh" --dry-run
```

Expected for each JSON:

- `action: run_critique`
- `stop_boundary: host_llm_critique_required`
- `safe_command: /fig_critique <fixture>`
- `forbidden_actions` includes accepted/golden/export/SVG mutation identifiers.

## Task 2: Host-Vision Refresh Each Critique

Repeat this task once per fixture:

- `fig1_overview_v2_pair_001_vault`
- `golden_trap_depth_picture`
- `fig1_overview_v2`

- [ ] **Step 1: Generate the critique brief**

Run from `plugins/figure-agent`:

```bash
uv run python3 scripts/critique_brief.py examples/<fixture> > /tmp/<fixture>-issue74-critique-brief.md
```

Expected: exits `0`, prints current `schema`, `rubric_version`, `generator_version`, and `critique_input_hash`.

- [ ] **Step 2: Run host `/fig_critique`**

In Claude host vision, run:

```text
/fig_critique <fixture>
```

Required host reads:

- `examples/<fixture>/build/<fixture>.png`
- every listed high-zoom crop in `build/audit_crops/manifest.json`
- every listed visual-clash crop/candidate
- every listed text-boundary and label-path candidate when present
- every listed print-scale image
- every listed figure-level or panel-level reference image

Expected: `examples/<fixture>/critique.md` is rewritten for the current brief hash.

- [ ] **Step 3: Lint the critique**

Run:

```bash
uv run python3 scripts/critique_lint.py examples/<fixture>
```

Expected: `OK: critique lint passed for <fixture>`.

- [ ] **Step 4: Preserve or refresh adjudication**

First try the conservative sync path:

```bash
uv run python3 scripts/critique_adjudication.py sync <fixture>
```

Expected: succeeds when the existing finding ids and decision shape still match
the refreshed critique. This preserves decisions and refreshes only the source
critique hash.

If the file is missing, scaffold:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <fixture>
```

If sync refuses because ids or decision shape changed, inspect
`examples/<fixture>/critique_adjudication.yaml` before using `--force`. Use:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <fixture> --force
```

only when the prior adjudication contains no human-authored decision value to
preserve. If it does contain human-authored decisions, record a human
adjudication blocker in the milestone instead of overwriting.

Expected: adjudication is schema-valid and fresh against the refreshed critique.

- [ ] **Step 5: Run loop/driver closeout**

Run:

```bash
uv run python3 scripts/fig_loop.py <fixture> --goal "Issue 74 host critique refresh closeout" --json
uv run python3 scripts/fig_driver.py <fixture> --mode review --goal "Issue 74 host critique refresh closeout" --dry-run
uv run python3 scripts/fig_driver.py <fixture> --mode release --goal "Issue 74 release-gate recheck" --dry-run
```

Expected: no command stops first on `critique_stale`. Any remaining stop is a real human/release/publication/golden/source-figure gate.

## Task 3: Document The Queue Closeout

- [ ] **Step 1: Create the milestone**

Create:

```text
plugins/figure-agent/docs/milestones/2026-05-29-post-v1-14-host-critique-refresh-queue.md
```

Required sections:

- fixture queue and why it exists;
- per-fixture commands and results;
- critique schema/rubric/hash after refresh;
- lint/adjudication/loop/driver result table;
- preserved human decisions or scaffold rationale;
- protected-scope confirmation;
- review cycles;
- verification results;
- remaining risks.

- [ ] **Step 2: Close the issue doc**

Modify:

```text
plugins/figure-agent/docs/superpowers/issues/2026-05-29-issue-74-post-v1-14-host-critique-refresh-queue.md
```

Set:

```text
Status: completed
```

Add closeout link to the milestone and summarize the next true gates.

## Task 4: Final Verification

- [ ] **Step 1: Confirm no protected mutations**

Run:

```bash
git status --short --branch
git diff --name-only
```

Expected changed files are only:

- the three `critique.md` files;
- the three `critique_adjudication.yaml` files;
- the Issue 74 milestone;
- the Issue 74 issue doc;
- test snapshots only if a real fixture contract legitimately changed.

- [ ] **Step 2: Run targeted checks**

Run from `plugins/figure-agent`:

```bash
uv run python3 scripts/critique_lint.py examples/fig1_overview_v2_pair_001_vault
uv run python3 scripts/critique_lint.py examples/golden_trap_depth_picture
uv run python3 scripts/critique_lint.py examples/fig1_overview_v2
uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_critique_lint.py tests/test_sync_critique_adjudication.py
```

Expected: lint passes and pytest passes.

- [ ] **Step 3: Run final checks**

Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:

- full pytest passes;
- ruff passes;
- diff check is clean;
- all three plugin validations pass.

- [ ] **Step 4: Commit**

Run from repo root:

```bash
git add plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/critique.md \
  plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/critique_adjudication.yaml \
  plugins/figure-agent/examples/golden_trap_depth_picture/critique.md \
  plugins/figure-agent/examples/golden_trap_depth_picture/critique_adjudication.yaml \
  plugins/figure-agent/examples/fig1_overview_v2/critique.md \
  plugins/figure-agent/examples/fig1_overview_v2/critique_adjudication.yaml \
  plugins/figure-agent/docs/milestones/2026-05-29-post-v1-14-host-critique-refresh-queue.md \
  plugins/figure-agent/docs/superpowers/issues/2026-05-29-issue-74-post-v1-14-host-critique-refresh-queue.md
git commit -m "Refresh post-v1.14 host critique queue"
```

## Self-Review

- Spec coverage: the plan covers the current queue, host vision requirement,
  lint, adjudication, loop/driver, milestone, protected-scope, and verification.
- Placeholder scan: no placeholder markers are present.
- Type/contract consistency: commands use existing script names and the
  `host_llm_critique_required` boundary recorded by `/fig_driver`.
