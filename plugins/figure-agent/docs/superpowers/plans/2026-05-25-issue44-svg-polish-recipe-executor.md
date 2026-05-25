# Issue 44 SVG Polish Recipe Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:test-driven-development for behavior changes and
> superpowers:verification-before-completion before claiming completion. Keep
> Issue 44A, 44B, 44C, 44D, and 44E as separate reviewable slices.

**Goal:** Add a conservative, recipe-based SVG polish execution path that can
apply bounded visual-only edits, produce before/after audit evidence, and keep
semantic backport as a hard release blocker.

**Architecture:** `svg_polish_recipe.py` owns recipe schema and freshness.
`svg_polish_executor.py` owns dry-run and write mode. Existing
`svg_polish_handoff.py` and `svg_polish_manifest.py` remain the final-artifact
handoff and release gate. Delta review is added only after the executor is
bounded and tested.

**Tech Stack:** Python 3.12, stdlib XML parsing where sufficient, PyYAML,
existing figure-agent hashing utilities, pytest, ruff.

---

## Issue 44A: Recipe Contract

**Files:**

- Create: `scripts/svg_polish_recipe.py`
- Create: `tests/test_svg_polish_recipe.py`
- Update: `docs/superpowers/issues/2026-05-25-issue-44-svg-polish-recipe-executor.md`

- [x] **Step 1: Write failing schema tests**

Cover:

- valid recipe loads;
- malformed YAML fails cleanly;
- wrong schema fails;
- fixture mismatch fails;
- source outside `exports/` fails;
- target outside `polish/` fails;
- duplicate operation ids fail;
- unknown operation class fails;
- unknown action fails;
- selector/action/semantic guard required fields fail;
- unknown future mapping fields are preserved on load/write.

Run:

```bash
uv run pytest -q tests/test_svg_polish_recipe.py
```

Expected: RED because the module does not exist.

- [x] **Step 2: Implement parser, validator, writer**

Implement:

- `SvgPolishRecipeError`
- `load_svg_polish_recipe(path, example_dir=...)`
- `validate_svg_polish_recipe(data, example_dir=...)`
- `write_svg_polish_recipe(path, data)`
- `svg_polish_recipe_source_paths(...)`
- `svg_polish_recipe_input_hash(...)`
- `svg_polish_recipe_is_stale(...)`

- [x] **Step 3: Verify 44A**

Run:

```bash
uv run pytest -q tests/test_svg_polish_recipe.py tests/test_svg_polish_manifest.py
uv run ruff check scripts/svg_polish_recipe.py tests/test_svg_polish_recipe.py
git diff --check
```

- [x] **Step 4: Review 44A**

Review for:

- schema correctness;
- path containment;
- freshness correctness;
- backward compatibility;
- unknown-field preservation.

Do not start 44B until 44A tests and review are clean.

---

## Issue 44B: Safe Executor MVP

**Files:**

- Create: `scripts/svg_polish_executor.py`
- Create: `tests/test_svg_polish_executor.py`
- Update: `commands/fig_loop.md` or `commands/fig_drive.md` only if UX text is
  needed.

- [x] **Step 1: Write failing executor tests**

Use small SVG fixtures. Cover:

- dry-run reports planned changes and writes nothing;
- write mode writes only `polish/<name>.polished.svg`;
- `translate` applies bounded transform to one selected element;
- `set_stroke_width` applies bounded stroke width change;
- `set_opacity`, `set_fill_opacity`, and `set_stroke_opacity` apply bounded
  numeric changes;
- selector resolving zero elements fails;
- selector resolving too many elements fails;
- excessive movement or visual change fails;
- source SVG is never modified;
- generated `exports/` files are never modified.

Run:

```bash
uv run pytest -q tests/test_svg_polish_executor.py
```

Expected: RED because the module does not exist.

- [x] **Step 2: Implement dry-run and write mode**

Implement:

- `SvgPolishExecutorError`
- `plan_svg_polish(recipe, example_dir=...)`
- `apply_svg_polish(recipe, example_dir=..., force=False)`
- CLI with default dry-run and explicit `--write`

Start with XML attribute edits only. Do not rewrite path geometry.

- [x] **Step 3: Verify 44B**

Run:

```bash
uv run pytest -q tests/test_svg_polish_executor.py tests/test_svg_polish_recipe.py tests/test_svg_polish_handoff.py tests/test_svg_polish_manifest.py
uv run ruff check scripts/svg_polish_executor.py tests/test_svg_polish_executor.py
git diff --check
```

- [x] **Step 4: Review 44B**

Review for:

- mutation containment;
- selector safety;
- deterministic output;
- failure mode clarity;
- no hidden semantic edits.

Do not start 44C until 44B tests and review are clean.

---

## Issue 44C: Aesthetic Delta Audit Pack

**Files:**

- Create: `scripts/svg_polish_delta.py`
- Create: `tests/test_svg_polish_delta.py`
- Modify: `scripts/critique_brief.py` only if the delta pack should be emitted
  in the host critique brief for this slice.
- Modify: `tests/test_critique_brief.py` if brief output changes.

- [x] **Step 1: Write failing delta tests**

Cover:

- before/after/diff pack is generated deterministically;
- delta manifest includes source SVG hash, polished SVG hash, recipe hash, and
  operation ids;
- stale recipe or missing polished SVG fails cleanly;
- missing delta pack preserves current behavior unless a later schema requires
  it.

- [x] **Step 2: Implement delta pack generation**

Use existing local rendering tools where already available in the plugin. Keep
all generated images ignored/untracked.

- [x] **Step 3: Wire critique brief if scoped**

If implemented in this slice, add a `## SVG Polish Aesthetic Delta` section
that tells the host LLM to compare before/after and detect regressions or
semantic changes.

- [x] **Step 4: Verify 44C**

Run:

```bash
uv run pytest -q tests/test_svg_polish_delta.py tests/test_critique_brief.py
uv run ruff check scripts/svg_polish_delta.py tests/test_svg_polish_delta.py
git diff --check
```

- [x] **Step 5: Review 44C**

Review for:

- deterministic artifacts;
- no stale delta leakage;
- no forced critique schema change unless required;
- host prompt clarity.

---

## Issue 44D: Semantic Backport Guard Hardening

**Files:**

- Modify: `scripts/svg_polish_handoff.py` if recipe metadata is included in the
  audit.
- Modify: `scripts/svg_polish_manifest.py` only if additive optional recipe
  fields are necessary.
- Modify: `scripts/status.py`, `scripts/fig_loop.py`, or `scripts/fig_driver.py`
  only to surface existing blocked states more clearly.
- Add focused tests in existing status/driver/loop test files.

- [x] **Step 1: Write failing guard tests**

Cover:

- recipe operation with `semantic_guard.allowed: false` cannot be promoted;
- manifest with recipe-driven `backport_required: true` reports final artifact
  `BLOCKED`;
- `/fig_drive --mode polish` routes blocked final artifact to
  `semantic_backport_required`;
- no accepted/golden state is mutated.

- [x] **Step 2: Implement minimal guard wiring**

Prefer reusing existing `semantic_change_declared` and `backport_required`
fields. Avoid a manifest v2 unless the additive fields cannot express the
contract.

- [x] **Step 3: Verify 44D**

Run:

```bash
uv run pytest -q tests/test_svg_polish_handoff.py tests/test_svg_polish_manifest.py tests/test_status.py tests/test_fig_driver.py
uv run ruff check scripts/svg_polish_handoff.py scripts/svg_polish_manifest.py scripts/status.py scripts/fig_driver.py
git diff --check
```

- [x] **Step 4: Review 44D**

Review for:

- no release shortcut;
- no advisory-only semantic blocker;
- compatibility with Issue 42 manifests;
- clear operator recovery path.

---

## Issue 44E: Real Fixture Dogfood

**Files:**

- Create: `docs/milestones/2026-05-25-svg-polish-recipe-dogfood.md`
- Do not commit generated build/export/delta artifacts unless repo policy
  explicitly requires a golden artifact update.

- [x] **Step 1: Select one fixture**

Use a fixture whose current loop checkpoint can legitimately route to
`ready_for_svg_polish`. Do not use a fixture with unresolved semantic or human
art-direction blockers.

- [x] **Step 2: Run end-to-end dogfood**

Sequence:

```bash
uv run python3 scripts/status.py examples/<name>
uv run python3 scripts/fig_loop.py <name> --goal "svg polish recipe dogfood" --json
uv run python3 scripts/fig_driver.py <name> --mode polish --goal "svg polish recipe dogfood" --dry-run
uv run python3 scripts/svg_polish_executor.py examples/<name> --dry-run
uv run python3 scripts/svg_polish_executor.py examples/<name> --write
uv run python3 scripts/svg_polish_handoff.py examples/<name> ... --write
uv run python3 scripts/status.py examples/<name>
```

Record:

- recipe operations;
- before/after evidence paths;
- whether polish improved, regressed, or was neutral;
- whether semantic backport stayed false;
- final `/fig_status` result.

- [x] **Step 3: Verify dogfood**

Run:

```bash
uv run pytest -q tests/test_svg_polish_recipe.py tests/test_svg_polish_executor.py tests/test_svg_polish_delta.py tests/test_svg_polish_handoff.py tests/test_status.py tests/test_fig_driver.py
git diff --check
```

- [x] **Step 4: Review 44E**

Review for:

- dogfood honesty;
- no source/export/accepted/golden mutation;
- recipe usefulness;
- failure modes found during real usage.

---

## Final Verification

After 44A-44E are complete, run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Final Review Checklist

- Can a recipe silently edit generated exports?
- Can a broad selector modify an entire panel unexpectedly?
- Can a semantic edit pass as visual-only?
- Can stale recipe or delta artifacts affect critique freshness?
- Can old Issue 42 manifests remain valid?
- Can generated-export fixtures remain unaffected?
- Is the first executor conservative enough for real SVG output?
- Is there a clear stop path when SVG selectors are unstable?
