# Issue 62 v0.8 Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a v0.8.0 release-candidate metadata and documentation slice that accurately describes the current figure-agent plugin after Issues 57-61.

**Architecture:** Keep the release slice documentation-first and contract-tested. Update version surfaces, README current-state language, changelog, closeout status, and release contract tests without adding new audit features or touching figure sources/generated artifacts.

**Tech Stack:** Python 3.12, pytest, ruff, uv lockfile metadata, Claude plugin validation.

---

### Task 1: Release Contract Tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_release_contract.py`

- [x] **Step 1: Write failing tests**

Add assertions that v0.8 docs state:

- README current state matches plugin version.
- README mentions `style-pack catalog`, `external vision review`, and `single next action`.
- README explicitly says the plugin is not a hidden auto-designer and cannot certify Nature/Science acceptance.
- Closeout status names v0.8.0 / Issue 62 as current truth.
- CHANGELOG has a `0.8.0` section with Issues 57-61.

- [x] **Step 2: Run red test**

Run:

```bash
uv run pytest -q tests/test_release_contract.py
```

Expected: fail on missing v0.8 release docs/version language.

Actual: failed on v0.7.1 metadata, missing v0.8 README/CHANGELOG/closeout
language, and stale Issue 57 branch status.

### Task 2: Version And Release Notes

**Files:**
- Modify: `plugins/figure-agent/.claude-plugin/plugin.json`
- Modify: `plugins/figure-agent/pyproject.toml`
- Modify: `plugins/figure-agent/uv.lock`
- Modify: `plugins/figure-agent/CHANGELOG.md`

- [x] **Step 1: Bump version metadata**

Set plugin manifest and pyproject version to `0.8.0`; refresh `uv.lock` so the
local package entry also reports `0.8.0`.

- [x] **Step 2: Add v0.8.0 changelog section**

Add a top changelog entry dated `2026-05-28` covering:

- real-fixture audit adoption;
- single next-action UX;
- SVG polish promotion dogfood evidence;
- style-pack catalog;
- optional external vision review evidence;
- release claim boundary: quality/audit kernel, not hidden auto-designer.

Actual: plugin manifest, `pyproject.toml`, and `uv.lock` now report `0.8.0`.
`CHANGELOG.md` has a `0.8.0` entry dated `2026-05-28`.

### Task 3: Current-Truth Docs

**Files:**
- Modify: `plugins/figure-agent/README.md`
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md` only if command-facing current-truth gaps are found
- Modify: `plugins/figure-agent/commands/*.md` only if command docs conflict with v0.8 current truth
- Modify: `plugins/figure-agent/docs/milestones-archive/2026-05-21-plugin-development-closeout-status.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-62-v0-8-release-hardening.md`

- [x] **Step 1: Update README current state**

Change current state to v0.8.0 and document automatic, semi-automatic, opt-in,
and manual boundaries. Include style packs and external vision review as opt-in
evidence layers.

- [x] **Step 2: Update closeout status**

Make the closeout milestone current through v0.8.0 / Issue 62, include fresh
verification results, and keep the Nature/Science claim boundary explicit.

- [x] **Step 3: Update Issue 62 status**

Mark Issue 62 as implemented pending commit, then amend to final wording after
commit if needed.

Actual: README, closeout, and Issue 57-62 status lines now reflect the v0.8.0
release-candidate truth and keep the Nature/Science acceptance boundary
explicit.

### Task 4: Verification And Review

- [x] **Step 1: Run targeted release tests**

```bash
uv run pytest -q tests/test_release_contract.py tests/test_style_pack_catalog.py tests/test_external_vision_review.py
```

- [x] **Step 2: Run full verification**

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [x] **Step 3: Critical review**

Check:

- no source/export/accepted/golden/generated artifacts are staged;
- no new feature implementation leaked into the release slice;
- docs do not claim automatic Nature/Science acceptance;
- docs distinguish automatic, semi-automatic, opt-in, and manual steps;
- version surfaces agree.

- [ ] **Step 4: Commit**

Commit the release-hardening docs, metadata, lockfile, and tests only.

Actual verification:

- `uv run pytest -q tests/test_release_contract.py tests/test_style_pack_catalog.py tests/test_external_vision_review.py` -> `33 passed`.
- `uv run pytest -q` -> `1337 passed, 3 skipped, 1 xfailed`.
- `uv run ruff check .` -> all checks passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> validation passed.
- `claude plugin validate .` -> validation passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> validation passed.
