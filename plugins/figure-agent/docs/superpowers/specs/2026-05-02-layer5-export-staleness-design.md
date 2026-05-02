# Layer 5 export staleness — Design Spec

**Date:** 2026-05-02
**Status:** brainstorm-complete, awaiting user review before implementation plan
**Origin:** Paired prerequisite from `2026-05-02-bell-curve-style-decoupling-design.md` §"Paired prerequisite". The original framing ("rsvg-convert mis-rasterizes SVG paths") was empirically refuted during this brainstorming session — the two export pipelines are equivalent within anti-aliasing tolerance. The actual unresolved problem is staleness, not divergence.

## Goal

Detect and resolve drift between `examples/<name>/build/` (compile output) and `examples/<name>/exports/` (export pipeline output), so that the two stay in sync without manual intervention. Protect git-tracked golden-fixture exports from automatic overwrite. Add a contract test catching future regressions in either rasterizer (pdftocairo or rsvg-convert).

## Why

`build/<name>.png` is produced by `pdftocairo` directly from the compile-output PDF; `exports/<name>.png` is produced by `dvisvgm --pdf` (PDF → SVG with `<text>` preservation) followed by `rsvg-convert` (SVG → PNG at 600 dpi). These pipelines render the same input to perceptually equivalent output (verified empirically: `_macro_smoke` 0.39% / 1864 RMSE, `dogfood_power_law_trap_pipeline` 1.49% / 3536 RMSE — both anti-aliasing-only divergence at the level of font edges and stroke endcaps).

The earlier session-2026-05-02 observation that `exports/PNG` showed mystery cBlue circles absent from `build/PNG` was traced to `exports/` having stale 15:16 timestamps after a 17:43 macro fix in `910c3bc` — the export pipeline was simply not re-run, so users were comparing a pre-fix PDF's PNG against a post-fix PDF's PNG. That falsified the "rasterizer divergence" hypothesis but exposed a real workflow bug: there is no mechanism today that detects when `exports/` has fallen behind `build/`, and `/fig_export` does not automatically refresh.

This affects reproducibility (golden-fixture promotion gates assume `exports/` reflects current source) and trust (users seeing diverged PNGs cannot tell whether the underlying source diverged or the artifacts are stale).

## Architecture

Three changes, each one self-contained:

1. `/fig_status` learns a new sub-state for `examples/<name>/exports/`: `MISSING | TRACKED_GOLDEN | STALE | FRESH`.
2. `/fig_export` reads that sub-state and either rebuilds (`STALE` or `MISSING`), skips with warning (`TRACKED_GOLDEN`), or no-ops (`FRESH`). A `--force-golden` flag overrides `TRACKED_GOLDEN`.
3. Two contract tests guard the invariants: a freshness invariant (always-on, all fixtures) and a cross-pipeline equivalence smoke (opt-in per-fixture via `spec.yaml`).

The export pipeline scripts themselves (`scripts/export_svg.sh`, `scripts/svg_to_png.sh`) are NOT modified. They remain CLI-agnostic so they can be invoked directly for debugging. The new logic lives in `scripts/status.py` and the `/fig_export` orchestration.

### Staleness definition: content hash, not mtime

A fixture's `exports/<name>.pdf` is FRESH iff its metadata-stripped content blob equals `build/<name>.pdf`'s metadata-stripped content blob.

```
hash(strip_metadata(qpdf_qdf(build/<name>.pdf)))
  == hash(strip_metadata(qpdf_qdf(exports/<name>.pdf)))
```

Reuses the metadata-stripping pipeline already established in `scripts/diff_pdf_content.py` (committed in BellCurve PR `6024545`). The strip patterns cover `/CreationDate`, `/ModDate`, `/ID`, `/Producer`, `/Trapped` — i.e., per-invocation noise that does not reflect rendering content.

Rationale vs mtime:
- **mtime is fragile.** `git checkout`, `cp`, `tar -x`, copy-on-write filesystems, and editor "touch on save" patterns all break mtime ordering. A user pulling the branch fresh would see every fixture as STALE even when the artifacts are correct.
- **content hash is robust.** It compares actual rendering instructions. A re-compile that produces the same PDF (e.g., recompiling without source changes) correctly reports FRESH and avoids unnecessary work. A real source change correctly reports STALE.
- **content hash detects work avoidance.** The freshness check itself is fast (qpdf is sub-second on a one-page fixture). It only fires if the user invokes `/fig_status` or `/fig_export`; it does not run on every file save.

Cost: one qpdf invocation per fixture when checked. Negligible relative to the lualatex compile that precedes it.

### Golden fixture protection

`.gitignore` exclusions like `!plugins/figure-agent/examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.pdf` mark a fixture's `exports/<file>` as a curated, hand-accepted reference snapshot. Auto-rebuild MUST NOT clobber these.

Detection rule: an exports artifact is `TRACKED_GOLDEN` iff `git ls-files <abs_path>` returns the path. The check uses `git ls-files` (not the gitignore exclusion list directly) so the rule generalizes to any future golden fixtures without spec changes.

Behavior matrix:

| `git ls-files`          | content hash                  | sub-state          | `/fig_export` action                      |
|-------------------------|-------------------------------|---------------------|-------------------------------------------|
| no exports/<file>       | n/a                           | `MISSING`          | regenerate                                 |
| not tracked             | matches build/PDF             | `FRESH`            | no-op                                      |
| not tracked             | differs from build/PDF        | `STALE`            | regenerate                                 |
| tracked                 | n/a                           | `TRACKED_GOLDEN`   | skip with warning; `--force-golden` to override |

The `TRACKED_GOLDEN` sub-state takes precedence over content-hash comparison: a tracked file is reported as `TRACKED_GOLDEN` whether or not its content matches the current build. This is intentional — golden fixtures may legitimately diverge from the current source as the source evolves; the golden is the reference snapshot, not the current truth.

### Contract tests

Two layers, answering different questions.

**Layer A — Per-fixture freshness invariant** (always on, no opt-in):

After `/fig_export` runs on a non-golden fixture and reports success, the freshness check MUST pass:

```
hash(strip_metadata(qpdf(build/<name>.pdf))) == hash(strip_metadata(qpdf(exports/<name>.pdf)))
```

A test fixture exercises this end-to-end: `tests/test_export_freshness.py` compiles a minimal one-figure fixture, runs `/fig_export`, asserts the equality. Catches operational failure modes: pipeline error swallowed, `dvisvgm` truncated output, copy-script silently no-op.

**Layer B — Cross-pipeline equivalence smoke** (opt-in per-fixture):

Fixtures that declare `export_pipeline_equivalence` in `spec.yaml` are subject to a pixel-level equivalence assertion between `build/PNG` and `exports/PNG`. Schema:

```yaml
# spec.yaml
export_pipeline_equivalence:
  ae_max: 0.02      # required if section present; absolute-error fraction in [0, 1]
  fuzz_pct: 5       # optional, default 5; passes through to magick compare -fuzz
```

The test calls `magick compare -metric AE -fuzz <fuzz_pct>% build/PNG exports/PNG` and asserts `AE / (width × height) ≤ ae_max`. Default for fixtures that omit the section is "no equivalence smoke required."

This catches future regressions in `pdftocairo` (Cairo version bumps), `dvisvgm` (Ghostscript / mutool / TeX Live changes), and `rsvg-convert` (libRSVG releases). It is opt-in because (a) `_macro_smoke` is too small to set a stable threshold (AA-pixel count varies disproportionately with content size), (b) future flagship-pilot fixtures may have more text/finer paths and legitimately exceed a global 2% threshold, and (c) the freshness invariant alone solves the operational pain — equivalence is forward-looking insurance, not the bug fix.

Recommended initial declarations (added in implementation):
- `dogfood_power_law_trap_pipeline/spec.yaml`: `ae_max: 0.02` (measured 1.49% + 0.5% headroom).
- `_macro_smoke/spec.yaml`: omit (smoke fixture; not under contract).
- `golden_trap_depth_picture/spec.yaml`: omit (already gated by `golden_artifact_checks` separate contract).

### Files modified / created

**Modified:**
- `scripts/status.py` — add exports sub-state computation. Use the new `_strip_metadata` import (see footnote) plus `git ls-files` shellout.
- `/fig_export` orchestrator (likely `.claude/commands/fig_export.md` or `scripts/<export-script>`, to be confirmed at plan time) — apply behavior matrix above; honor `--force-golden`.
- `scripts/diff_pdf_content.py` — refactor to expose `strip_metadata(pdf_path: Path) -> bytes` as importable. CLI `main()` and exit codes 0/1/2 unchanged. The BellCurve PR's usage of the script must continue working.

**Created:**
- `tests/test_export_freshness.py` — Layer A invariant.
- `tests/test_export_pipeline_equivalence.py` — Layer B opt-in smoke (skips fixtures without the spec.yaml section).

**Schema additions:**
- `spec.yaml.export_pipeline_equivalence` (optional dict). Documented in `docs/spec-yaml-schema.md` if that doc exists, otherwise inline near `spec.yaml.golden_artifact_checks`.

## Validation

- `uv run pytest -q` reports all green including the two new test files.
- `/fig_status` on a fresh checkout (where mtime is irrelevant) correctly reports per-fixture exports sub-state via content hash.
- Manual: edit `examples/_macro_smoke/_macro_smoke.tex`, run `/fig_compile`, run `/fig_status` — exports/ should report STALE. Run `/fig_export` — should regenerate and report FRESH. Run `/fig_export` again — should no-op (already FRESH).
- Manual: `git ls-files examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.pdf` returns the path → `/fig_status` reports TRACKED_GOLDEN even after `/fig_compile` regenerates `build/`. `/fig_export` skips with a warning. `/fig_export --force-golden` regenerates and overwrites the tracked file.

## Out of scope

- **Figure-source quality** ("허점 많다" comment from session 2026-05-02). Recorded in memory `project_dogfood_fixture_quality_concern.md` as parking-lot finding for the next flagship-pilot's pre-work; not addressed by this spec.
- **Anti-aliasing minimization.** The 0.4–1.5% AE divergence between pdftocairo and rsvg-convert at 600 dpi is intrinsic to the two libraries' rendering choices and is accepted. Tuning fuzz_pct or rasterizer flags to drive AE toward 0 is not a goal.
- **Replacing one pipeline with the other.** Both pipelines have distinct user-facing roles (build/ for fast iteration, exports/ for SVG-preserving handoff to external editors). Neither is dropped.
- **PDF → TIFF freshness.** TIFF is part of the export set per `/fig_export` but is not exercised in the build/ pipeline. Equivalence is undefined; freshness applies (TIFF mtime/hash ≥ build/PDF hash) but is treated identically to PNG in the contract; no special handling needed.
- **Watcher/daemon auto-rebuild.** No filesystem watcher; staleness is checked on demand at `/fig_status` or `/fig_export` invocation. Out of scope.

## Implementation order (for downstream writing-plans)

1. Refactor `scripts/diff_pdf_content.py` to expose `strip_metadata` importable. Verify BellCurve PR's CLI usage still works (existing tests must remain green).
2. Add the `git ls-files` tracked-check helper. Unit-test on a known tracked path and a known untracked path.
3. Add the content-hash freshness helper. Unit-test on identical PDFs (FRESH) and a synthetic divergence (STALE).
4. Wire the sub-state into `scripts/status.py` and `/fig_status` output.
5. Wire the auto-rebuild + golden protection into `/fig_export`. Implement `--force-golden`.
6. Write `tests/test_export_freshness.py` (Layer A invariant).
7. Add `export_pipeline_equivalence` schema parsing; declare in `dogfood_power_law_trap_pipeline/spec.yaml`.
8. Write `tests/test_export_pipeline_equivalence.py` (Layer B opt-in smoke).
9. Update `docs/macros/` or workflow docs as needed (likely `docs/architecture-overview.md` or `SKILL.md` if they describe the pipeline contract).
10. Single feature commit; PR linking this spec and the BellCurve paired prerequisite resolution.

## Self-review

- **Placeholder scan:** No TBD or TODO. Every section is concrete. The single open detail (exact path of `/fig_export` orchestrator file) is flagged "to be confirmed at plan time" — appropriate for a spec.
- **Internal consistency:** `TRACKED_GOLDEN` precedes content-hash comparison consistently in both `/fig_status` reporting and `/fig_export` behavior. Layer A always on, Layer B opt-in: contract layers don't conflict.
- **Scope check:** Single fixture-folder contract surface; ≤ 4 production files modified, 2 new test files, 1 schema addition. Single implementation plan is appropriate.
- **Ambiguity check:** "Tracked" is precisely defined as `git ls-files <path>` returning the path. "Stale" is precisely defined via the content-hash equality. "Golden" is not separately defined — it is whatever git-tracking marks; this collapses three concepts (golden, tracked, hand-curated) into one and is intentional to avoid metadata drift.
- **Decision provenance:** D1 (content hash over mtime), D2 (TRACKED_GOLDEN as explicit sub-state), D3 (AE-only, per-fixture tunable, opt-in) all came from advisor sharpening rounds documented in the brainstorming session log. SSIM was considered and rejected (adds dependency without benefit at this threshold range).
