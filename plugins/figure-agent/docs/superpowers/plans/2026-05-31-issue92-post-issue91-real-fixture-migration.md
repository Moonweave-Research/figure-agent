# Post-Issue91 Real-Fixture Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the Issue 91 contracts on the real fixture queue without mutating figure sources, exports, accepted/golden state, publication state, or SVG polish artifacts.

**Architecture:** Treat this as an operator dogfood slice, not a new feature slice. First capture non-mutating queue/status/driver evidence. Then classify each fixture and separate v1.16 contract refresh from true figure defects. Only if the dogfood finds a plugin-code defect should implementation begin, with a narrow TDD issue.

**Tech Stack:** Python CLI scripts under `scripts/`, pytest, markdown milestone evidence, existing figure-agent queue/status/driver contracts.

---

## File Structure

- Create: `docs/milestones/2026-05-31-post-issue91-real-fixture-migration.md`
  - Records commands, fixture classifications, and any follow-up issue links.
- Modify: `docs/superpowers/issues/2026-05-31-issue-92-post-issue91-real-fixture-migration.md`
  - Close status and checklist after evidence is complete.
- Modify only if a defect is reproduced:
  - `scripts/status.py`
  - `scripts/fig_driver.py`
  - `scripts/fig_queue.py`
  - `scripts/fig_loop.py`
  - matching focused tests under `tests/`

## Task 1: Capture Non-Mutating Queue Snapshot

- [x] **Step 1: Run review queue snapshot**

```bash
uv run python3 scripts/fig_queue.py --mode review --goal "post-Issue91 migration review" --json
```

Expected: JSON output; no source/export/golden/accepted files modified.

- [x] **Step 2: Run release queue snapshot**

```bash
uv run python3 scripts/fig_queue.py --mode release --goal "post-Issue91 migration release check" --json
```

Expected: accepted/golden/publication gates appear as human or release-operator
boundaries, not automatic mutation.

- [x] **Step 3: Run polish queue snapshot**

```bash
uv run python3 scripts/fig_queue.py --mode polish --goal "post-Issue91 SVG polish readiness check" --json
```

Expected: SVG polish readiness is blocked unless the latest loop checkpoint
explicitly permits polish and all final-artifact gates are fresh.

- [x] **Step 4: Confirm no protected files changed**

```bash
git status --short examples
```

Expected: no `.tex`, export, accepted/golden, publication, build, or polish
artifact mutation from the queue snapshots.

## Task 2: Classify Production Fixtures

- [x] **Step 1: For each production fixture, run status**

Use this fixture list:

```text
fig1_overview_v2_pair_001_vault
fig1_overview_v2
golden_trap_depth_picture
n3_trial_01_trap_depth
n3_trial_02_actuation_sequence
fig3_trapping_concept
smoke_trap_demo
fig5_floating_clip_mechanism
```

Run this Python loop:

```bash
uv run python3 - <<'PY'
import json
from pathlib import Path
from status import infer_stage

fixtures = [
    "fig1_overview_v2_pair_001_vault",
    "fig1_overview_v2",
    "golden_trap_depth_picture",
    "n3_trial_01_trap_depth",
    "n3_trial_02_actuation_sequence",
    "fig3_trapping_concept",
    "smoke_trap_demo",
    "fig5_floating_clip_mechanism",
]
out = Path("/tmp/figure-agent-issue92")
out.mkdir(exist_ok=True)
for fixture in fixtures:
    result = infer_stage(Path("examples") / fixture)
    (out / f"{fixture}.status.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
PY
```

Expected: each fixture has an explicit state vector and `next` action.

- [x] **Step 2: For each fixture with ambiguous next action, run driver dry-run**

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal "post-Issue91 migration" --dry-run
```

Repeat with the affected fixture name. Expected: JSON says exactly one bounded
action or a stop boundary.

- [x] **Step 3: Classify each fixture**

Use exactly one category:

```text
ready/no-op
host_critique_required
human_gate_required
release_operator_required
workflow_agent_mechanical
svg_editor
plugin_defect
```

If a fixture is stale because v1.16 now requires crop-local evidence, classify
it as `host_critique_required`, not `plugin_defect`.

## Task 3: Write Milestone Evidence

- [x] **Step 1: Create milestone**

Create `docs/milestones/2026-05-31-post-issue91-real-fixture-migration.md`
with:

```markdown
# Post-Issue91 Real-Fixture Migration

Status: draft

## Commands

- `uv run python3 scripts/fig_queue.py --mode review --goal "post-Issue91 migration review" --json`
  - Result: record exit code and output summary.

## Fixture Classification

| Fixture | Review action | Release action | Polish action | Classification | Notes |
| --- | --- | --- | --- | --- | --- |

## Protected Mutation Check

- `git status --short examples`
  - Result: record whether protected files changed.

## Findings

- Plugin defects:
- Host critique refresh queue:
- Human/release gates:
- Mechanical workflow-agent work:

## Verdict

<operator-ready / blocked by plugin defect / blocked by human fixture work>
```

- [x] **Step 2: Record exact observations**

Do not summarize away stale-contract states. If `critique_stale` appears, note
whether the cause is generator/rubric/schema migration, input hash, or real
source/render change.

## Task 4: Defect Triage Gate

- [x] **Step 1: Decide whether any row is a plugin defect**

Plugin defect examples:

- driver suggests mutation despite `may_execute: false`;
- queue hides a blocking status note;
- status says fresh while v1.16-required crop evidence is missing;
- SVG polish route bypasses semantic diff;
- release mode suggests force-golden without human stop boundary.

Not plugin defects:

- host critique is stale after schema/rubric change;
- human adjudication is required;
- accepted/golden roll-forward requires explicit human approval;
- real figure source needs aesthetic repair.

- [x] **Step 2: If a plugin defect exists, stop fixture migration and create a narrow issue**

Create a new issue doc named after the defect, for example:

```text
docs/superpowers/issues/2026-05-31-issue-93-queue-hides-v1-16-lint-blocker.md
```

Include repro command, expected behavior, actual behavior, and focused test
target. Do not patch real fixture files as part of defect triage.

## Task 5: Verification

- [x] **Step 1: Run targeted tests**

```bash
uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_queue.py tests/test_fig_loop.py
```

Expected: all pass.

- [x] **Step 2: Run ruff for touched code**

If only docs/milestone changed:

```bash
git diff --check
```

If code changed:

```bash
uv run ruff check scripts/status.py scripts/fig_driver.py scripts/fig_queue.py scripts/fig_loop.py
git diff --check
```

- [x] **Step 3: Close Issue 92**

Update `docs/superpowers/issues/2026-05-31-issue-92-post-issue91-real-fixture-migration.md`:

```markdown
Status: completed

Closeout:
- milestone: docs/milestones/2026-05-31-post-issue91-real-fixture-migration.md
- verification: <commands and results>
- protected mutation: no source/export/golden/accepted/publication/SVG mutation
```

## Self-Review Checklist

- [x] The milestone distinguishes stale-contract migration from figure defects.
- [x] Every production fixture has exactly one current classification.
- [x] No generated artifacts are staged.
- [x] Any code change has a focused failing test first.
- [x] Human/release/SVG boundaries remain explicit.
