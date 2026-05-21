# Bounded Auto-Patch Executor Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in, single-target patch executor that can apply one externally prepared unified diff only when the latest `/fig_loop` checkpoint proves the target is a safe `auto_patch_candidate`.

**Architecture:** Keep `/fig_loop` verify-only and keep `fig_loop_auto_patch.py` as eligibility classification. Add a focused `scripts/fig_loop_patch_executor.py` module plus CLI that reads the latest loop record, validates the `patch_handoff`, checks the patch touches only allowed files, applies the diff, writes an evidence record, and tells the user to run `/fig_closeout`. The executor never generates edits itself and never mutates accepted, golden, export, build, final-artifact, or critique files.

**Tech Stack:** Python stdlib, existing loop run JSON records, existing patch evidence hash conventions, pytest, ruff, plugin validation.

---

## File Structure

- Create `scripts/fig_loop_patch_executor.py`
  - Owns patch-file parsing, eligibility validation, path-scope validation, diff application, and post-apply evidence writing.
- Create `tests/test_fig_loop_patch_executor.py`
  - Covers one success path and a larger refusal matrix.
- Modify `commands/fig_loop.md`
  - Document that `/fig_loop` remains verify-only and that any executor use is explicit, diff-driven, and closeout-gated.
- Modify `docs/superpowers/issues/2026-05-21-issue-15c-bounded-auto-patch-executor-pilot.md`
  - Mark implementation status after verification.

Do not modify `fig_driver.py`, `status.py`, accepted/golden/export artifacts, or example fixtures.

---

## Task 1: Patch Executor Contract Tests

**Files:**
- Create: `tests/test_fig_loop_patch_executor.py`
- Create: `scripts/fig_loop_patch_executor.py`

- [ ] **Step 1: Write failing tests first**

Add tests that create a temporary repo with:

- `examples/loop_demo/loop_demo.tex`
- `.scratch/fig-loop-runs/20260521T000000Z-loop_demo/iteration_001.json`
- `run_manifest.json`
- a patch file changing only `examples/loop_demo/loop_demo.tex`

Required tests:

- valid single-target unified diff applies and writes `patch_apply_001.json`;
- missing `--apply`/opt-in path does not mutate;
- missing `patch_handoff` is refused;
- `auto_patch_eligibility.level != auto_patch_candidate` is refused;
- `auto_patch_eligibility.may_edit == true` is not trusted as permission;
- multiple changed files are refused;
- path outside `allowed_edit_scope` is refused;
- accepted/golden/export/build/critique/final-artifact paths are refused;
- malformed patch is refused without partial mutation;
- refusal count remains greater than success count.

- [ ] **Step 2: Run RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop_patch_executor.py
```

Expected: import or missing-function failures because the executor does not exist.

---

## Task 2: Minimal Executor Implementation

**Files:**
- Create: `scripts/fig_loop_patch_executor.py`
- Test: `tests/test_fig_loop_patch_executor.py`

- [ ] **Step 1: Add public API**

Implement:

```python
class PatchExecutorError(Exception): ...

def apply_patch_file(
    name: str,
    *,
    repo_root: Path,
    runs_root: Path,
    patch_path: Path,
    apply: bool,
) -> dict[str, Any]:
    ...
```

The returned report schema is `figure-agent.patch-apply.v1`.

- [ ] **Step 2: Validate latest loop state**

The executor must require:

- latest run manifest fixture matches `name`;
- `iteration_001.json.patch_handoff` is a dict;
- `auto_patch_eligibility.level == "auto_patch_candidate"`;
- `auto_patch_eligibility.target_id == patch_handoff.target_id`;
- exactly one target id is present;
- explicit `apply=True`.

It must not treat `auto_patch_eligibility.may_edit` as permission.

- [ ] **Step 3: Validate patch file scope before mutation**

Parse unified diff file headers and compute the set of changed repo-relative paths. Refuse when:

- no changed path exists;
- more than one changed path exists;
- changed path is not exactly inside `patch_handoff.allowed_edit_scope`;
- changed path includes accepted/golden/export/build/critique/final-artifact semantics.

- [ ] **Step 4: Apply only after all validation passes**

Apply the patch by invoking `/usr/bin/patch` from `repo_root` with `--forward --batch --strip=0 --input <patch>`. Before applying, hash all allowed-scope files; after applying, hash again.

- [ ] **Step 5: Write evidence**

Write `.scratch/fig-loop-runs/<latest-run-dir>/patch_apply_001.json` containing:

- `schema: figure-agent.patch-apply.v1`
- `fixture`, `target_id`, `target_type`
- `changed_paths`
- `pre_patch` and `post_patch` hashes
- `rollback_reference` using the pre-patch hashes
- `closeout_required: true`
- `next_action: /fig_closeout <name>`

---

## Task 3: CLI and Documentation

**Files:**
- Modify: `scripts/fig_loop_patch_executor.py`
- Modify: `commands/fig_loop.md`
- Modify: `docs/superpowers/issues/2026-05-21-issue-15c-bounded-auto-patch-executor-pilot.md`

- [ ] **Step 1: Add CLI**

Support:

```bash
uv run python3 scripts/fig_loop_patch_executor.py <name> --patch-file <path> --apply
```

Without `--apply`, the command must exit non-zero and print a controlled refusal.

- [ ] **Step 2: Document usage**

Document that:

- `/fig_loop` remains verify-only;
- the executor is explicit and patch-file driven;
- it applies exactly one safe target only;
- it never writes accepted/golden/export/build/critique/final-artifact files;
- `/fig_closeout <name>` is mandatory after any mutation.

- [ ] **Step 3: Update issue status**

Mark Issue 15C implemented only after all verification commands pass.

---

## Verification

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop_patch_executor.py tests/test_fig_loop_auto_patch.py tests/test_fig_loop_handoff.py tests/test_fig_closeout.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check scripts/fig_loop_patch_executor.py tests/test_fig_loop_patch_executor.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Review Checklist

- Refusal paths outnumber success paths.
- No mutation happens before every validation passes.
- Executor cannot infer edits from prose.
- Executor cannot write outside `patch_handoff.allowed_edit_scope`.
- Executor cannot touch accepted/golden/export/build/critique/final-artifact state.
- Executor always leaves the loop in a closeout-required state after mutation.
