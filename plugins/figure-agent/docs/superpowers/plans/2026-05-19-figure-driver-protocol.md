# Figure Driver Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one canonical driver protocol tell agents when to compile, critique, export, loop, polish, release, or stop.

**Architecture:** Start docs-first and keep the first code slice advisory-only. `/fig_status` remains the source of truth for stage/state; the driver layer reads status, selects exactly one next action, and stops at host/human/polish/promotion boundaries instead of mutating hidden state.

**Tech Stack:** Python 3.12, pytest, existing `scripts/status.py`, existing command markdown, local plugin docs.

---

## Source Of Truth

Read first:

- `docs/superpowers/specs/2026-05-19-figure-driver-orchestration-design.md`
- `docs/superpowers/issues/2026-05-19-issue-8a-figure-driver-protocol.md`
- `skills/figure-agent/SKILL.md`
- `commands/fig_status.md`
- `commands/fig_loop.md`
- `commands/fig_export.md`
- `scripts/status.py`
- `scripts/fig_loop.py`
- `scripts/run_export.py`

## File Structure

Required docs-only slice:

- Modify `skills/figure-agent/SKILL.md`
  - Add the canonical driver rule: start with `/fig_status <name>` unless the
    user explicitly requested a lower-level command.
  - Explain that `/fig_loop` is verify-only and not a full executor.
  - Explain the mode split: authoring, review, release, polish.

- Modify `commands/fig_loop.md`
  - Strengthen wording that `/fig_loop` does not compile/export/critique/patch.
  - Add a short "When to use" section.

- Modify `commands/fig_status.md`
  - Add "Traffic controller" wording.
  - Clarify that `Next:` is the canonical next action for agents.

- Modify `commands/fig_export.md`
  - Clarify that export is the gate where critique freshness is enforced before
    export regeneration.

Optional dry-run command slice:

- Create `scripts/fig_driver.py`
  - Read `infer_stage()`.
  - Select one advisory next action.
  - Print JSON.
  - Do not mutate fixtures.

- Create `commands/fig_drive.md`
  - Document dry-run advisory behavior.

- Create `tests/test_fig_driver.py`
  - Cover mode routing, stop boundaries, and no mutation.

Do not implement mutating automation in Issue 8A.

### Task 1: Docs-First Driver Contract

**Files:**
- Modify: `skills/figure-agent/SKILL.md`
- Modify: `commands/fig_status.md`
- Modify: `commands/fig_loop.md`
- Modify: `commands/fig_export.md`

- [ ] **Step 1: Update `skills/figure-agent/SKILL.md` with the driver rule**

Add a short section near "Workflow shape":

```markdown
### Driver rule for agents

Unless the user explicitly asks for a specific low-level command, start every
figure workflow by running `/fig_status <name>` and follow its `Next:` hint.
Do not choose between compile, critique, export, loop, polish, or release from
memory. `/fig_status` is the traffic controller.

Use modes mentally:

- authoring: stay in `/fig_compile` until render is fresh enough for review.
- review: close compile, critique, adjudication, and `/fig_loop` evidence.
- release: check accepted/golden/final artifact readiness.
- polish: start only after generated export is current and the remaining work
  is visual-only SVG finalization.

`/fig_loop` is a verify-only checkpoint. It records state and patch handoff
evidence; it does not compile, export, critique, patch, polish, accept, or
commit.
```

- [ ] **Step 2: Update `commands/fig_status.md`**

Add this paragraph after the usage block:

```markdown
## Traffic Controller Contract

Agents should treat `/fig_status <name>` as the canonical first check unless
the user explicitly requested a lower-level command. The printed `Next:` hint is
the workflow's current next action. Do not jump from build to export, critique,
loop, polish, or release by intuition when `Next:` points somewhere else.
```

- [ ] **Step 3: Update `commands/fig_loop.md`**

Add this paragraph near the opening:

```markdown
## When To Use

Use `/fig_loop` after `/fig_status` says the normal compile/export/critique
prerequisites are ready enough to record loop evidence, or when you need a
verify-only patch handoff decision. Do not use `/fig_loop` as the full
end-to-end runner. It will not run compile, critique, export, adjudication,
SVG polish, accepted checks, or git operations for you.
```

- [ ] **Step 4: Update `commands/fig_export.md`**

Add this paragraph after the command steps:

```markdown
`/fig_export` is the export gate, not the whole loop. It is the point where
reference-grounded critique freshness is enforced before export regeneration.
If this command reports `critique_missing` or `critique_stale`, return to
`/fig_critique <name>` instead of repeatedly compiling.
```

- [ ] **Step 5: Verify docs-only changes**

Run:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:

```text
no git diff --check output
Validation passed
Validation passed
Validation passed
```

- [ ] **Step 6: Commit docs slice**

Run:

```bash
git add skills/figure-agent/SKILL.md commands/fig_status.md commands/fig_loop.md commands/fig_export.md
git commit -m "Document figure driver protocol"
```

### Task 2: Decide Whether To Add Dry-Run Driver Command

**Files:**
- Read: `scripts/status.py`
- Read: `tests/test_status.py`
- Optional Create: `scripts/fig_driver.py`
- Optional Create: `commands/fig_drive.md`
- Optional Create: `tests/test_fig_driver.py`

- [ ] **Step 1: Make the scope decision**

Choose docs-only completion if the docs fix is enough to stop agent confusion
for now.

Choose dry-run command implementation only if the command can stay read-only
and tested without adding hidden execution.

Record the decision in the issue file under:

```markdown
## Implementation Decision

- Decision: docs-only | dry-run command
- Reason:
- Deferred:
```

- [ ] **Step 2A: If docs-only, verify and stop**

Run:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 2B: If dry-run command, write failing tests first**

Create `tests/test_fig_driver.py` with tests for:

```python
from __future__ import annotations

from pathlib import Path

import pytest


def _write_fixture(root: Path, name: str, *, with_tex: bool = True) -> Path:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: demo\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    if with_tex:
        (fixture / f"{name}.tex").write_text("% source\n", encoding="utf-8")
    return fixture


def test_driver_authoring_mode_recommends_compile_when_render_stale(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    summary = run_driver("demo", mode="authoring", goal="tighten layout", repo_root=tmp_path)
    assert summary["action"] == "run_compile"
    assert summary["safe_command"] == "uv run python3 scripts/compile.py examples/demo/demo.tex"
    assert summary["stop_boundary"] is None

def test_driver_review_mode_stops_for_critique_when_missing(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    (fixture / "reference" / "ref.png").parent.mkdir()
    (fixture / "reference" / "ref.png").write_bytes(b"png")
    (fixture / "spec.yaml").write_text(
        "name: demo\nreference_image: reference/ref.png\npanels: []\n",
        encoding="utf-8",
    )
    make_fresh_build_and_exports(fixture, "demo")
    summary = run_driver("demo", mode="review", goal="review figure", repo_root=tmp_path)
    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "host_llm_critique_required"
    assert "fig_critique" in summary["safe_command"]

def test_driver_review_mode_recommends_adjudicate_when_critique_fresh(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    make_fresh_build_and_exports(fixture, "demo")
    write_fresh_critique(fixture, "demo")
    summary = run_driver("demo", mode="review", goal="close findings", repo_root=tmp_path)
    assert summary["action"] == "run_adjudicate"
    assert summary["stop_boundary"] is None

def test_driver_review_mode_runs_loop_only_after_status_prerequisites(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    make_fresh_build_and_exports(fixture, "demo")
    write_fresh_critique(fixture, "demo")
    write_fresh_adjudication(fixture, "demo")
    summary = run_driver("demo", mode="review", goal="record loop", repo_root=tmp_path)
    assert summary["action"] == "run_fig_loop"
    assert "--goal" in summary["safe_command"]

def test_driver_polish_mode_stops_until_export_is_current(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    summary = run_driver("demo", mode="polish", goal="final SVG polish", repo_root=tmp_path)
    assert summary["action"] == "run_compile"
    assert summary["mode"] == "polish"
    assert "polish" in summary["forbidden_actions"]

def test_driver_release_mode_reports_final_ready_blocker(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    make_fresh_build_and_exports(fixture, "demo")
    summary = run_driver("demo", mode="release", goal="release check", repo_root=tmp_path)
    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"

def test_driver_dry_run_does_not_mutate_fixture_files(tmp_path):
    fixture = _write_fixture(tmp_path, "demo")
    before = {path.relative_to(fixture): path.read_bytes() for path in fixture.rglob("*") if path.is_file()}
    run_driver("demo", mode="review", goal="dry run", repo_root=tmp_path)
    after = {path.relative_to(fixture): path.read_bytes() for path in fixture.rglob("*") if path.is_file()}
    assert after == before
```

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
```

Expected: fail because `scripts/fig_driver.py` does not exist yet.

### Task 3: Optional Dry-Run Driver Implementation

Only do this if Task 2 chooses dry-run command.

**Files:**
- Create: `scripts/fig_driver.py`
- Create: `commands/fig_drive.md`
- Test: `tests/test_fig_driver.py`

- [ ] **Step 1: Implement read-only action selection**

`fig_driver.py` should:

- parse `<name>`, `--mode`, `--goal`, and `--dry-run`
- require `--dry-run` in Issue 8A
- call `infer_stage(example_dir)`
- select exactly one action or stop boundary
- print JSON
- return exit code `0` for advisory output
- never write fixture files

Action names:

- `create_or_fix_source`
- `run_compile`
- `run_critique`
- `run_export`
- `run_adjudicate`
- `run_fig_loop`
- `patch_handoff_stop`
- `human_gate_stop`
- `polish_handoff_stop`
- `release_blocked`
- `complete`

- [ ] **Step 2: Add command docs**

Create `commands/fig_drive.md` explaining:

- dry-run only
- status-first
- modes
- no mutation
- stop boundaries
- examples

- [ ] **Step 3: Run targeted tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_status.py tests/test_fig_loop.py tests/test_run_export.py
uv run ruff check scripts/fig_driver.py tests/test_fig_driver.py
git diff --check
```

Expected: all pass.

- [ ] **Step 4: Validate plugin**

Run:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 5: Commit dry-run command**

Run:

```bash
git add scripts/fig_driver.py commands/fig_drive.md tests/test_fig_driver.py
git commit -m "Add dry-run figure driver"
```

## Review Checklist

Before claiming Issue 8A complete:

- [ ] The docs make `/fig_status` the canonical first check.
- [ ] The docs do not imply `/fig_loop` executes the full workflow.
- [ ] The docs say `/fig_export` is where critique-before-export is enforced.
- [ ] The docs say SVG polish starts after generated export is current.
- [ ] If code was added, all behavior is dry-run/read-only.
- [ ] If code was added, tests prove no fixture mutation.
- [ ] No accepted/golden/polish/source mutation was introduced.

## Completion Report Template

Use this in the final Claude report:

```markdown
Issue 8A completion report

Files changed:
- `skills/figure-agent/SKILL.md`
- `commands/fig_status.md`
- `commands/fig_loop.md`
- `commands/fig_export.md`
- optional: `scripts/fig_driver.py`, `commands/fig_drive.md`, `tests/test_fig_driver.py`

Decision:
- docs-only | dry-run command

Implemented contract:
- status-first driver rule
- explicit mode boundaries
- verify-only `/fig_loop` wording
- export critique-freshness boundary
- polish-after-export boundary

Verification:
- command -> result

Review result:
- clean | findings fixed

Remaining risks:
- list concrete risks, or state: No known Issue 8A blocker remains.
```
