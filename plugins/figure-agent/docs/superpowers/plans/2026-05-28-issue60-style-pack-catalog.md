# Issue 60 Style Pack Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small opt-in catalog of vetted journal/paper style packs that reuse the existing aesthetic contracts without introducing global defaults.

**Architecture:** Treat the catalog as data, not a new runtime layer. Add YAML packs under the existing explicit opt-in directories and test them through the existing `journal_art_direction_playbook.py` and `paper_aesthetic_context.py` parsers. Add operator documentation that explains pack selection and how fixture-local `aesthetic_intent.yaml` remains the override/grounding layer.

**Tech Stack:** Python 3.12, pytest, YAML, existing figure-agent style-pack parsers.

---

### Task 1: Add Catalog Loader Tests First

**Files:**
- Create: `plugins/figure-agent/tests/test_style_pack_catalog.py`

- [x] **Step 1: Write failing tests**

Add tests that:

- assert the four expected journal playbooks exist and validate;
- assert the four expected paper contexts exist and validate;
- assert main-text playbooks do not use `cover_like`/`graphical_abstract`
  contexts;
- assert the expressive pack is isolated from main-text by using
  `graphical_abstract` or `cover_like`;
- assert every journal playbook has both `continue_tikz` and
  `ready_for_svg_polish` route rules;
- assert every paper context includes at least one `must_avoid` anti-pattern.

- [x] **Step 2: Run tests and confirm failure**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_style_pack_catalog.py
```

Expected: fail because the catalog files do not exist yet.

Actual: failed with missing catalog playbook and paper-context files.

### Task 2: Add Journal Art-Direction Playbook Catalog

**Files:**
- Create:
  - `plugins/figure-agent/examples/_journal_art_direction_playbooks/nc-main-text.yaml`
  - `plugins/figure-agent/examples/_journal_art_direction_playbooks/nature-materials-dense.yaml`
  - `plugins/figure-agent/examples/_journal_art_direction_playbooks/science-compact.yaml`
  - `plugins/figure-agent/examples/_journal_art_direction_playbooks/graphical-abstract-expressive.yaml`

- [x] **Step 1: Add four validated playbooks**

Each pack must use schema `figure-agent.journal-art-direction-playbook.v1` and
include:

- `playbook_id` matching filename stem;
- `target_journal`;
- `venue_context`;
- `visual_maturity`;
- 3-10 `design_center` items;
- 2-10 `anti_patterns`;
- 2-10 `positive_signals`;
- 2-8 `polish_route_rules` including both `continue_tikz` and
  `ready_for_svg_polish`;
- 1-6 `human_review_triggers`.

Main-text packs must be restrained and must route semantic/aesthetic ambiguity
back to TikZ or human review. The expressive pack must not use `main_text`.

- [x] **Step 2: Run targeted playbook tests**

Run:

```bash
uv run pytest -q tests/test_journal_art_direction_playbook.py tests/test_style_pack_catalog.py
```

Expected after Task 3 is complete: pass. During this task, paper-context tests
may still fail until Task 3 adds those files.

Actual after fixup: `tests/test_style_pack_catalog.py` passed.

### Task 3: Add Paper Aesthetic Context Catalog

**Files:**
- Create:
  - `plugins/figure-agent/examples/_paper_aesthetic_contexts/nc-main-text-series.yaml`
  - `plugins/figure-agent/examples/_paper_aesthetic_contexts/nature-materials-dense-series.yaml`
  - `plugins/figure-agent/examples/_paper_aesthetic_contexts/science-compact-series.yaml`
  - `plugins/figure-agent/examples/_paper_aesthetic_contexts/graphical-abstract-expressive-series.yaml`

- [x] **Step 1: Add four validated paper contexts**

Each pack must use schema `figure-agent.paper-aesthetic-context.v1` and include:

- `paper_id` matching filename stem;
- venue-appropriate `target_journal`;
- `visual_maturity`;
- `density`;
- shared visual language anchors;
- template fixture roles;
- explicit `must_avoid` entries.

- [x] **Step 2: Run targeted paper-context tests**

Run:

```bash
uv run pytest -q tests/test_paper_aesthetic_context.py tests/test_style_pack_catalog.py
```

Expected: pass.

Actual: `tests/test_style_pack_catalog.py` passed after adding the catalog.

### Task 4: Add Operator Documentation

**Files:**
- Create: `plugins/figure-agent/docs/style-pack-catalog.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-60-style-pack-catalog.md`

- [x] **Step 1: Document usage**

Explain:

- no pack applies globally;
- a fixture opts into a journal playbook through
  `spec.yaml.journal_art_direction_playbook`;
- a fixture opts into a paper context through `spec.yaml.paper_aesthetic_context`;
- `aesthetic_intent.yaml` remains fixture-local and should refine, not replace,
  the selected pack;
- main-text packs are conservative, expressive packs are explicit opt-in only.

- [x] **Step 2: Update Issue 60 status**

Set status to implemented in branch `codex/issue60-style-pack-catalog` and list
the catalog files, tests, and docs.

### Task 5: Verification And Review

- [x] **Step 1: Run targeted tests**

```bash
uv run pytest -q tests/test_style_pack_catalog.py tests/test_journal_art_direction_playbook.py tests/test_paper_aesthetic_context.py
```

Result: `21 passed`.

- [x] **Step 2: Run full docs/data verification**

```bash
uv run ruff check tests/test_style_pack_catalog.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

- `uv run pytest -q`: `1315 passed, 3 skipped, 1 xfailed`
- `uv run ruff check .`: all checks passed
- `git diff --check`: clean
- `claude plugin validate .claude-plugin/plugin.json`: passed
- `claude plugin validate .`: passed
- `claude plugin validate ../../.claude-plugin/marketplace.json`: passed

- [x] **Step 3: Critical review**

Check:

- no global default was introduced;
- main-text packs forbid decorative/cover-like effects;
- expressive pack cannot silently leak into main-text figures;
- pack ids are short and stable;
- pack content is concrete enough to guide host-LLM critique;
- no figure source, export, accepted, golden, or generated artifact was changed.

Review result: clean. Catalog packs are opt-in data, main-text packs stay
restrained, expressive packs are isolated by venue and visual maturity, and no
real fixture `spec.yaml` was modified.

- [x] **Step 4: Commit**

Commit only catalog YAML, docs, tests, and Issue 60 status updates.
