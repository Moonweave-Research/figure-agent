# Issue 42 SVG Polish UX and Semantic Backport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a deterministic SVG polish handoff scaffolder that writes the audit and manifest for an already-polished SVG while preserving the existing semantic-backport gate.

**Architecture:** Keep `svg_polish_manifest.py` as the owner of schema validation and freshness. Add `svg_polish_handoff.py` as a thin UX layer that validates operator input, writes `svg_polish_audit.md`, then writes `svg_polish_manifest.yaml` with current hashes. Existing `/fig_status` and accepted-mode gates consume the generated manifest unchanged.

**Tech Stack:** Python 3.12, PyYAML, existing figure-agent scripts, pytest, ruff.

---

### Task 1: Handoff Module and Audit Scaffold

**Files:**
- Create: `scripts/svg_polish_handoff.py`
- Test: `tests/test_svg_polish_handoff.py`

- [x] **Step 1: Write failing tests**

Add tests that build a temporary fixture with source, briefing, spec, exports,
critique, and `polish/<name>.polished.svg`. Assert that generated audit text
contains all required semantic-backport checks and that unknown edit classes
raise a controlled error before any output files are written.

- [x] **Step 2: Run tests and confirm RED**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py
```

Expected: import failure because `svg_polish_handoff.py` does not exist.

- [x] **Step 3: Implement minimal module**

Create `SvgPolishHandoffError`, `build_audit_markdown`, `build_manifest_payload`,
and `write_handoff_files`. Reuse `ALLOWED_EDIT_CLASSES`, `ALLOWED_EDITORS`,
`file_sha256`, `final_artifact_source_set_hash`, and
`write_svg_polish_manifest`.

- [x] **Step 4: Run tests and confirm GREEN**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py tests/test_svg_polish_manifest.py
```

Expected: all pass.

### Task 2: CLI Dry Run and Write Mode

**Files:**
- Modify: `scripts/svg_polish_handoff.py`
- Test: `tests/test_svg_polish_handoff.py`

- [x] **Step 1: Write failing CLI tests**

Add tests proving dry-run prints planned output paths without writing files, and
`--write` writes audit then manifest.

- [x] **Step 2: Run tests and confirm RED**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py
```

Expected: CLI entrypoint missing or assertions fail.

- [x] **Step 3: Implement CLI**

Add argparse support for `example_dir`, `--reviewer`, `--editor`,
`--toolchain`, `--edit-class`, `--reviewed-at`, `--notes`,
`--semantic-change-declared`, `--backport-required`, `--write`, and `--force`.

- [x] **Step 4: Run tests and confirm GREEN**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py tests/test_svg_polish_manifest.py
```

Expected: all pass.

### Task 3: Status Integration Regression

**Files:**
- Test: `tests/test_svg_polish_handoff.py`

- [x] **Step 1: Write failing/guard tests**

Add a test that appends `final_artifact.kind: polished_svg` to a fixture spec,
uses the handoff writer with `backport_required=True`, and asserts
`compute_final_artifact_state(...)["state"] == "BLOCKED"`.

- [x] **Step 2: Run tests**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py tests/test_status.py
```

Expected: pass after Task 1/2 because existing status logic should already
consume the generated manifest.

### Task 4: Documentation and Verification

**Files:**
- Modify: `commands/fig_loop.md`
- Modify: `commands/fig_status.md` if needed
- Modify: `docs/architecture-overview.md`

- [x] **Step 1: Update docs**

Document `scripts/svg_polish_handoff.py` as the canonical way to scaffold audit
and manifest after a human/outer-agent SVG edit. Reconcile Layer 5.5 wording so
it says the contract and loop surfacing exist, while handoff UX is the new work.

- [x] **Step 2: Run final verification**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py tests/test_svg_polish_manifest.py tests/test_status.py tests/test_golden_artifact_checks.py
uv run pytest -q
uv run ruff check scripts/svg_polish_handoff.py tests/test_svg_polish_handoff.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.
