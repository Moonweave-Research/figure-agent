# Slice 2 — Real Sub-Region Key Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `quality_defect_ledger` emit a distinct, stable sub-region key per defect — composite `(panel, selector_sha256)` when a selector exists, else `(panel, defect_class, ordinal)` — instead of collapsing every defect to `(panel, "label-a")`, so per-sub-region diagnosis and cross-run trending have a real join key.

**Architecture:** Add a pure post-build normalization pass `_assign_subregion_keys(defects)` to `scripts/quality/quality_defect_ledger.py` and call it inside `build_quality_defect_ledger` **after** `source_fingerprint` is computed (so defect identity / the fingerprint stay unchanged — Slice 2 only adds a distinct `target["subregion"]`). The selector hash is already available on `selector_hint.selector_text_hash` for undeclared-geometry defects; a per-`(panel, defect_class)` ordinal is the fallback when no selector exists.

**Tech Stack:** Python 3.12+, pytest, `uv` (all commands via `uv run`). Repo root for commands: `plugins/figure-agent` (quote the bracketed workspace path in shells). Slice-2 dogfood gate: the ledger emits **distinct** sub-regions on fig2 AND fig3.

---

## Why this is Slice 2 (the blocker)

The 2026-06-25 ceiling-loop design spec (`docs/superpowers/specs/2026-06-25-ceiling-loop-design.md`, §2 principle 7 / §8) makes this a **precondition**: the stop-point diagnoser keys everything per sub-region, but `quality_defect_ledger._explicit_target` (`scripts/quality/quality_defect_ledger.py:112-127`) hard-defaults `subregion` to the literal `"label-a"` at every path, so two distinct defects in the same panel are indistinguishable. No per-region facet can ship until distinct regions exist. This slice fixes only that.

Verified consumer surface (so the change is safe):
- `candidate_generator.py:236-238` reads `target.get("subregion") or "label-a"` — tolerant; it will simply carry the new composite key into candidates (desired propagation, no break).
- `test_candidate_generator.py` asserts `subregion == "label-a"` only on defects it constructs **inline** and feeds directly to `candidate_generator` (never through `build_quality_defect_ledger`), so the ledger change does not touch them.
- The `"label-a"` strings in `test_svg_polish_executor.py` are SVG element ids — an unrelated concept.

## File Structure

- **Modify:** `scripts/quality/quality_defect_ledger.py`
  - add `_subregion_for_defect(defect, ordinals)` + `_assign_subregion_keys(defects)` helpers (near `_explicit_target`, ~line 128);
  - call `_assign_subregion_keys(defects)` in `build_quality_defect_ledger` after the `source_fingerprint` loop (~line 641).
- **Test:** `tests/test_quality_defect_ledger.py` — add 3 tests (distinct-by-selector, distinct-by-ordinal fallback, explicit-subregion preserved) + update any existing `build_quality_defect_ledger` test that asserts the old `"label-a"` collapse.

---

### Task 1: Failing test — two near-misses get distinct sub-regions

**Files:**
- Test: `tests/test_quality_defect_ledger.py`

- [ ] **Step 1: Write the failing test**

Add at the end of `tests/test_quality_defect_ledger.py`. It mirrors the existing `test_quality_defect_ledger_ingests_undeclared_geometry_near_miss` (`tests/test_quality_defect_ledger.py:80`) — reuse `_write_fixture` (`:17`) for a valid fixture, then write an undeclared-geometry report with **two** `add_micro_defect` candidates on different source lines.

```python
def test_quality_defect_ledger_assigns_distinct_subregions(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    fixture = _write_fixture(workspace)
    name = fixture.name
    tex = fixture / f"{name}.tex"
    # Ensure the two candidate source lines exist and differ, so selector hashes differ.
    tex.write_text(
        "% Panel A\n"
        "\\draw (0,0) -- (1,0) node[right] {first label};\n"
        "\\draw (0,1) -- (1,1) node[right] {second label};\n",
        encoding="utf-8",
    )
    report = fixture / "build" / "undeclared_geometry.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "candidates": [
                    {"id": "UG001", "source_line": 2, "recommended_action": "add_micro_defect"},
                    {"id": "UG002", "source_line": 3, "recommended_action": "add_micro_defect"},
                ],
            }
        ),
        encoding="utf-8",
    )

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        name, plugin_root=_PLUGIN_ROOT, workspace_root=workspace
    )

    subregions = [
        d["target"]["subregion"]
        for d in ledger["defects"]
        if d.get("defect_class") == "text_overlap"
    ]
    assert len(subregions) == 2, ledger["defects"]
    assert subregions[0] != subregions[1], subregions
    assert "label-a" not in subregions, subregions
```

> If `_PLUGIN_ROOT` / `json` / `Path` are not already imported in this test module, reuse the exact imports the existing tests use (read the file head and the `plugin_root=` argument passed in `test_quality_defect_ledger_ingests_undeclared_geometry_near_miss` at `:109`). Do not invent a new constant name.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd 'plugins/figure-agent' && NO_COLOR=1 uv run pytest tests/test_quality_defect_ledger.py::test_quality_defect_ledger_assigns_distinct_subregions -q`
Expected: FAIL — both subregions are `"label-a"`, so `subregions[0] != subregions[1]` is False.

---

### Task 2: Implement the composite sub-region key

**Files:**
- Modify: `scripts/quality/quality_defect_ledger.py`

- [ ] **Step 1: Add the two helpers** (insert immediately after `_explicit_target`, i.e. after `scripts/quality/quality_defect_ledger.py:127`)

```python
def _subregion_for_defect(
    defect: dict[str, Any], ordinals: dict[tuple[str, str], int]
) -> str:
    target = defect.get("target")
    panel = (
        target.get("panel", "unknown")
        if isinstance(target, dict)
        else "unknown"
    )
    # 1. Preserve an already-explicit, non-default subregion.
    if isinstance(target, dict):
        existing = target.get("subregion")
        if isinstance(existing, str) and existing.strip() and existing.strip() != "label-a":
            return existing.strip()
    # 2. Selector hash when available (stable across runs).
    selector_hint = defect.get("selector_hint")
    if isinstance(selector_hint, dict):
        sel_hash = selector_hint.get("selector_text_hash")
        if isinstance(sel_hash, str) and sel_hash:
            return f"sel:{sel_hash[:12]}"
        value = selector_hint.get("value")
        if isinstance(value, str) and value.strip():
            return f"sel:{_canonical_hash(value.strip())[:12]}"
    # 3. Per-(panel, defect_class) ordinal fallback.
    defect_class = str(defect.get("defect_class") or "defect")
    key = (panel, defect_class)
    index = ordinals.get(key, 0)
    ordinals[key] = index + 1
    return f"{defect_class}#{index}"


def _assign_subregion_keys(defects: list[dict[str, Any]]) -> None:
    ordinals: dict[tuple[str, str], int] = {}
    for defect in defects:
        if not isinstance(defect, dict):
            continue
        target = defect.get("target")
        if not isinstance(target, dict):
            target = {"panel": "unknown", "subregion": "label-a"}
            defect["target"] = target
        target["subregion"] = _subregion_for_defect(defect, ordinals)
```

- [ ] **Step 2: Call it in `build_quality_defect_ledger`** — after the `source_fingerprint` loop (`scripts/quality/quality_defect_ledger.py:638-640`), before `_annotate_actionability` (`:641`).

Change:

```python
    for defect in defects:
        if isinstance(defect, dict):
            defect["source_fingerprint"] = _source_fingerprint(defect)
    actionability_metrics = _annotate_actionability(defects, _declared_panels(example_dir))
```

to:

```python
    for defect in defects:
        if isinstance(defect, dict):
            defect["source_fingerprint"] = _source_fingerprint(defect)
    # Slice 2: stamp a distinct, stable sub-region key AFTER the fingerprint so
    # defect identity is unchanged; only target["subregion"] gains a real value.
    _assign_subregion_keys(defects)
    actionability_metrics = _annotate_actionability(defects, _declared_panels(example_dir))
```

- [ ] **Step 3: Run the Task-1 test to verify it passes**

Run: `cd 'plugins/figure-agent' && NO_COLOR=1 uv run pytest tests/test_quality_defect_ledger.py::test_quality_defect_ledger_assigns_distinct_subregions -q`
Expected: PASS (2 distinct `sel:...` subregions).

- [ ] **Step 4: Lint**

Run: `cd 'plugins/figure-agent' && uv run ruff check scripts/quality/quality_defect_ledger.py`
Expected: `All checks passed!`

---

### Task 3: Ordinal-fallback test (no selector hash → distinct ordinals)

**Files:**
- Test: `tests/test_quality_defect_ledger.py`

- [ ] **Step 1: Write the test** (append to the test module)

```python
def test_subregion_ordinal_fallback_is_distinct() -> None:
    defects = [
        {"defect_class": "text_overlap", "target": {"panel": "A", "subregion": "label-a"}},
        {"defect_class": "text_overlap", "target": {"panel": "A", "subregion": "label-a"}},
        {"defect_class": "text_overlap", "target": {"panel": "B", "subregion": "label-a"}},
    ]
    quality_defect_ledger._assign_subregion_keys(defects)
    subs = [d["target"]["subregion"] for d in defects]
    assert subs == ["text_overlap#0", "text_overlap#1", "text_overlap#0"], subs
```

- [ ] **Step 2: Run it**

Run: `cd 'plugins/figure-agent' && NO_COLOR=1 uv run pytest tests/test_quality_defect_ledger.py::test_subregion_ordinal_fallback_is_distinct -q`
Expected: PASS (ordinals reset per panel; same-panel same-class get `#0`, `#1`).

---

### Task 4: Explicit-subregion-preserved test

**Files:**
- Test: `tests/test_quality_defect_ledger.py`

- [ ] **Step 1: Write the test** (append)

```python
def test_subregion_preserves_explicit_value() -> None:
    defects = [
        {"defect_class": "text_overlap", "target": {"panel": "A", "subregion": "hero"}},
        {
            "defect_class": "text_overlap",
            "target": {"panel": "A", "subregion": "label-a"},
            "selector_hint": {"kind": "line_range", "selector_text_hash": "abcdef0123456789"},
        },
    ]
    quality_defect_ledger._assign_subregion_keys(defects)
    assert defects[0]["target"]["subregion"] == "hero"
    assert defects[1]["target"]["subregion"] == "sel:abcdef012345"
```

- [ ] **Step 2: Run it**

Run: `cd 'plugins/figure-agent' && NO_COLOR=1 uv run pytest tests/test_quality_defect_ledger.py::test_subregion_preserves_explicit_value -q`
Expected: PASS (an explicit non-default subregion is kept; a selector hash yields `sel:` + first 12 chars).

---

### Task 5: Regression sweep for the old `"label-a"` collapse

**Files:**
- Test: `tests/test_quality_defect_ledger.py` (update only if needed)

- [ ] **Step 1: Find any test that asserts the old collapse through the real ledger**

Run: `cd 'plugins/figure-agent' && grep -n "subregion" tests/test_quality_defect_ledger.py`
Inspect each hit. Only assertions that call `build_quality_defect_ledger(...)` AND expect `subregion == "label-a"` are now stale (a single real defect now gets `sel:...` or `<class>#0`). Tests that construct a defect inline and assert their own input echoes are unaffected.

- [ ] **Step 2: Update any stale assertion to the new key**

For each stale assertion, replace the expected `"label-a"` with the now-correct value: `sel:<first-12-of-selector_text_hash>` when the defect carries a selector hash, else `<defect_class>#0`. Show the corrected expected value explicitly (do not leave it computed-in-the-head).

- [ ] **Step 3: Run the full ledger test module**

Run: `cd 'plugins/figure-agent' && NO_COLOR=1 uv run pytest tests/test_quality_defect_ledger.py -q`
Expected: all pass.

---

### Task 6: Slice-2 dogfood gate — distinct sub-regions on fig2 AND fig3

**Files:** none (verification gate).

- [ ] **Step 1: Make the detector reports fresh** for both cohort fixtures (non-strict compile regenerates `build/undeclared_geometry.json`).

Run:
```bash
cd 'plugins/figure-agent'
uv run python bin/fig-agent compile fig2_trap_design_space
uv run python bin/fig-agent compile fig3_resistance_mechanism
```
Expected: both rc=0 (Output written … bytes). If a fixture lacks undeclared-geometry candidates, the gate still holds via the ordinal fallback as long as ≥2 defects exist.

- [ ] **Step 2: Assert distinct sub-regions per fixture**

Run:
```bash
cd 'plugins/figure-agent'
uv run python3 -c "
import sys; sys.path.insert(0, 'scripts'); sys.path.insert(0, 'scripts/quality')
import quality_defect_ledger as q
from pathlib import Path
for name in ('fig2_trap_design_space', 'fig3_resistance_mechanism'):
    led = q.build_quality_defect_ledger(name, workspace_root=Path('.'))
    subs = [d['target']['subregion'] for d in led['defects'] if isinstance(d, dict)]
    print(name, 'defects=%d' % len(subs), 'distinct=%d' % len(set(subs)), subs)
    assert len(subs) < 2 or len(set(subs)) > 1, (name, subs)
print('SLICE-2 GATE PASS')
"
```
Expected: prints `SLICE-2 GATE PASS`; each fixture with ≥2 defects shows `distinct > 1` (no `label-a` collapse). If a fixture has <2 defects, the gate is vacuously satisfied for it — note that in the run report and confirm the other fixture has ≥2 distinct.

> The exact `build_quality_defect_ledger` invocation (plugin_root/workspace_root) must match how the test calls it at `tests/test_quality_defect_ledger.py:109`; if `plugin_root` is required, pass it the same way the test does.

---

### Task 7: Full suite, lint, commit

- [ ] **Step 1: Full suite**

Run: `cd 'plugins/figure-agent' && NO_COLOR=1 uv run pytest -q`
Expected: `0 failed` (baseline 2582 passed + the 3 new tests). `NO_COLOR=1` avoids the pre-existing `FORCE_COLOR` argparse artifact in `test_cowork_runtime_contract.py`.

- [ ] **Step 2: Lint**

Run: `cd 'plugins/figure-agent' && uv run ruff check scripts/quality/quality_defect_ledger.py tests/test_quality_defect_ledger.py`
Expected: `All checks passed!`

- [ ] **Step 3: Commit**

```bash
git add plugins/figure-agent/scripts/quality/quality_defect_ledger.py plugins/figure-agent/tests/test_quality_defect_ledger.py
git commit -m "feat(ledger): Slice 2 — distinct per-sub-region key

Stamp target[subregion] with a composite (panel, selector_sha256) or
(panel, defect_class, ordinal) key after the source_fingerprint loop, so two
defects in one panel are distinguishable (was collapsed to label-a). Selector
hash reuses selector_hint.selector_text_hash; ordinal is the per-(panel,class)
fallback. Fingerprint/identity unchanged. Gate: distinct sub-regions on fig2/fig3.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage:** implements design §2 principle 7 + §8 Slice 2 (`(panel, selector_sha256)` / `(panel, defect_class, ordinal)`, distinct on fig2/fig3). Fingerprint left unchanged per §6 (no perturbation of the identity the recheck uses) — Slice 4 separately replaces the gameable recheck.
- **Placeholder scan:** no TBD/TODO; every code step shows complete code; the only "read the existing import/helper" notes point at exact cited lines (`:17`, `:80`, `:109`) for harness conventions, not for logic.
- **Type consistency:** `_subregion_for_defect(defect, ordinals) -> str` and `_assign_subregion_keys(defects) -> None` are used with those exact signatures in Tasks 2-4; `ordinals: dict[tuple[str,str], int]`; subregion strings `sel:<12>` / `<class>#<n>` are consistent across tasks.
- **Scope:** one module + its test; no consumer break (verified: `candidate_generator` is tolerant; candidate_generator/svg_polish tests unaffected). Slices 3+ are separate, evidence-gated plans (Slice 3 = diagnoser/harness, planned only after this gate passes and reveals the dominant stop-cause).
