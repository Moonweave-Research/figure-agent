# figure-agent v0.2 Architecture Proposal

**Status**: ACCEPTED — landed across PR #7 (split) → #8a (frozen-legacy delete) → #9 (CI infra) → #8b (stage migration) → #11 (L4.5 vision critique). Released as v0.2.0 (2026-05-04).
**Date**: 2026-05-03
**Author**: session redesign after host-LLM vision insight + L3 architectural reset (2026-05-03)
**Supersedes**: `docs/architecture-overview.md` (v0.1.7.2 — 11 layers); see Layer 4.5 / 9 sections in that file for the rewritten reference.

> Living document. Edit freely. Mark resolved sections with `[RESOLVED]`,
> open questions with `[OPEN]`, deferred decisions with `[DEFERRED]`.

---

## §1. Why this redesign

Two converging signals from the past 48 hours:

1. **L3 architectural reset (2026-05-03 EOD)** — flagship macro decoupling at 65% turned out to be a minor lever; real bottlenecks are PNG semantic understanding (briefing quality) and paper-quality reach (Inkscape polish). L3 hold decided.

2. **Host-LLM vision insight (2026-05-04)** — Claude Code itself is a vision LLM. The plugin can orchestrate vision critique through the host main loop without calling external APIs, sidestepping the v0.1 "Plugin does not call vision APIs" policy without breaking it.

Combined: the v0.1.7.2 11-layer model carries dead weight (frozen orchestration) AND lacks the one capability (automated vision feedback) that would actually raise the figure-quality ceiling.

---

## §2. Honest evaluation of the current 11 layers

| Current | Real role | Verdict |
|---|---|---|
| L0 External Inputs | "user puts files somewhere" | **DROP — disclaimer, not a layer** |
| L1 Identity/Onboarding | README + SKILL + plugin.json + CLAUDE + AGENTS | **CONSOLIDATE — 5 surfaces drift** |
| L2 Authoring Intent | briefing.md + spec.yaml | **KEEP — slim spec.yaml** |
| L2.5 Reference Analysis | `reference_extract.py` 1060 lines | **REWRITE — split into modules** |
| L3 Semantic TikZ | `.tex` + `.sty` flagship macros | **KEEP — freeze macro additions** |
| L4 Compile Gates | lint + lualatex + collision/clash/drift | **KEEP AS-IS** |
| L5 Export | dvisvgm + staleness contract | **KEEP AS-IS** |
| L6 Validation Gates | golden_contract + accepted mode | **KEEP — minor cleanup** |
| L7 State Inference | status.py 382 lines (test_status.py 703 lines) | **KEEP — file size below CRITICAL threshold; no split needed** |
| L8 Reproducibility | .gitignore + LFS | **RECLASSIFY — config, not layer** |
| L9 Frozen Legacy | 4 scripts + 3 commands + 1 prompt + 2 spec fields | **DELETE most + RENAME `review_brief.py` & `fig_review.md` (reused by L4.5)** |
| L10 Documentation | docs/ + docs/historical | **RECLASSIFY — meta** |

Real functional pipeline = 6 layers (L2 → L2.5 → L3 → L4 → L5 → L6). The other 5 are organizational labels, policy, or dead code.

---

## §3. Proposed v0.2 layer model

```
═══════════════════════════════════════════════════════════════════
                    FIGURE-AGENT v0.2 ARCHITECTURE
═══════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────┐
  │  IDENTITY SURFACE  (single source: SKILL.md)                │
  │  README/CLAUDE/AGENTS/plugin.json — auto-derived stubs only │
  └─────────────────────────────────────────────────────────────┘
                                  ║
  ╔═══════════════════════════════╩═══════════════════════════════╗
  ║                    PIPELINE  (data flow)                      ║
  ╠═══════════════════════════════════════════════════════════════╣
  ║                                                               ║
  ║   L1 │ AUTHORING INTENT                                       ║
  ║      │ briefing.md  +  spec.yaml(slim: panels/style/golden)   ║
  ║      │       ▼                                                ║
  ║   L2 │ REFERENCE HINTS  (optional, golden fixtures only)      ║
  ║      │ ocr.py + palette.py + vtrace.py → coordinate_hints     ║
  ║      │       ▼                                                ║
  ║   L3 │ TIKZ SOURCE                                            ║
  ║      │ <name>.tex  +  styles/polymer-paper-preamble.sty       ║
  ║      │ (flagship macro library — additions FROZEN)            ║
  ║      │       ▼                                                ║
  ║   L4 │ COMPILE + WARN GATES                                   ║
  ║      │ lint_tex → lualatex → collision/clash                  ║
  ║      │       ▼                                                ║
  ║  L4.5│ ★ VISION CRITIQUE  [NEW]                               ║
  ║      │ host Claude reads build/<name>.png + briefing          ║
  ║      │ → critique.md (physics + layout + hierarchy)           ║
  ║      │ → optional spec.yaml/.tex patch suggestion             ║
  ║      │ (numbered L4.5 to preserve L5/L6 numbering downstream) ║
  ║      │       ▼                                                ║
  ║   L5 │ EXPORT                                                 ║
  ║      │ dvisvgm + rsvg + staleness contract (Layer A/B)        ║
  ║      │       ▼                                                ║
  ║   L6 │ VALIDATION GATES                                       ║
  ║      │ golden_contract: required_labels + source_inventory    ║
  ║      │ + layout_drift (anchored to L2 hints)                  ║
  ║      │                                                        ║
  ╚═══════════════════════════════════════════════════════════════╝
                                  ║
  ┌───────────────────────────────╨───────────────────────────────┐
  │  CROSS-CUTTING  (observes pipeline, not in flow)              │
  │   • status.py     — read-only stage inference (any layer)     │
  │   • .gitignore    — golden vs ordinary fixture tracking       │
  │   • CHANGELOG     — release log                               │
  └───────────────────────────────────────────────────────────────┘

  ╔═══════════════════════════════════════════════════════════════╗
  ║  REMOVED FROM v0.1 (final state after PR #8a+#8b+#9):         ║
  ║   ✗ scripts/{prompt_gen, redact, llm_author_prompt}.py        ║
  ║   ✗ commands/{fig_prompt, fig_preview_select}.md              ║
  ║   ✗ prompts/llm_author_tikz.md                                ║
  ║   ✗ spec.yaml.{selected_preview, selection_notes}             ║
  ║   ✗ Layer 0 / 8 / 10  (re-classified, not pipeline layers)    ║
  ║   ✗ docs/historical/                                          ║
  ║                                                               ║
  ║  RENAMED (not deleted):                                       ║
  ║   ↪ scripts/review_brief.py    → scripts/critique_brief.py    ║
  ║   ↪ commands/fig_review.md     → commands/fig_critique.md     ║
  ╚═══════════════════════════════════════════════════════════════╝
```

---

## §4. Key changes

### §4.1 NEW: L4.5 Vision Critique

The single largest value addition. Evolves frozen `/fig_review` into an automated host-orchestrated equivalent via **rename + extend** (not delete-and-rewrite — see §4.5).

```
/fig_critique <name>
   1. critique_brief.py emits the brief (briefing context + line-numbered .tex
      + severity/category schema + freshness checks)
   2. Slash command Reads build/<name>.png into the host main loop
   3. Host Claude (subscription, no API) inspects PNG against the brief
      and produces structured findings
   4. Host writes examples/<name>/critique.md (YAML front-matter + Markdown — §4.6)
   5. STOP. No auto-apply, no patch staging — report-only mode (see §7).
```

**Cost**: 0원 (subscription tokens only). Zero API calls. CLAUDE.md policy untouched — host orchestration is not an external API call.

**Numbering choice**: L4.5 (not L5) because Export already occupies L5 in the existing `architecture-overview.md` and is referenced by tests (`test_export_freshness.py`, `test_export_pipeline_equivalence.py`). Renumbering Export would force downstream doc/test churn for zero pipeline-semantic gain.

### §4.2 REMOVED: L9 Frozen Legacy (partial — corrected after Codex review)

**Codex finding [HIGH] #1**: blast radius is NOT zero. `selected_preview` is read by `status.py:122,286` for stage inference — Stage 2 vs Stage 3 distinction depends on it. Removal requires a stage-model migration, not a simple delete.

**Updated removal scope** (split into two sub-PRs):

**PR #8a (clean delete — no stage migration needed):** see §6 for full file list. Drops the 3 frozen scripts, 2 frozen commands, 1 prompt template, and `spec.yaml.selection_notes` field — plus the 4 supporting test/scaffold/doc references confirmed by grep (see §7 RESOLVED entry).

**PR #8b (stage-model migration — separate, sequenced after #8a):**
- Refactor `status.py` Stage 2/3 logic to drop `selected_preview` dependency
- Update `commands/{fig_compile,fig_status,fig_new}.md` references
- Update `tests/test_inputs.py` and `tests/test_status.py`
- Update `README.md`
- Then drop `spec.yaml.selected_preview`

**PR #9 (rename, do not delete — see §4.5):**
- `scripts/review_brief.py` → `scripts/critique_brief.py` (rename + extend)
- `commands/fig_review.md` → `commands/fig_critique.md` (rename + rewrite body)

**Removal rationale**: `quality-kernel-goal.md` declares these frozen but the code is still wired into stage logic. Cleanup is real value but the migration is non-trivial — sequencing matters.

### §4.3 SLIMMED: spec.yaml

Current accumulated fields:
- `panels`, `style_profile` ← core (keep)
- `reference_image`, `accepted`, `golden_contract` ← golden fixture (keep)
- `export_pipeline_equivalence` ← Layer 5 contract (keep)
- `selected_preview`, `selection_notes` ← **delete** (with L9)

### §4.5 RENAME (not rewrite): review_brief.py → critique_brief.py

**Codex finding [HIGH] #2**: `scripts/review_brief.py` (154 lines) already implements the building blocks the new L4.5 needs:

| Capability | Existing function | Line |
|---|---|---|
| Fresh PNG check | `_require_fresh_png` | 40-47 |
| Style-lock freshness | `_review_source_paths` (includes STYLE_LOCK_PATH) | 50-54 |
| Repo-relative render path | `_example_relative_path` | 36-37 |
| Line-numbered TeX | `_line_numbered` | 57-62 |
| Severity / category schema | output template | 122-127 (BLOCKER/MAJOR/MINOR/NIT × physics/label_placement/whitespace/hierarchy/palette/style) |

Strategy: **rename + extend** instead of delete + rewrite.

```
review_brief.py (current)         critique_brief.py (v0.2)
   generate_for() returns brief   generate_for() returns brief
   prints to stdout (HALT)        + writes critique.md (YAML+MD)
                                  + caller is host Claude main loop
                                    (slash command Read tool loads PNG)
```

The HALT-then-paste behavior is removed (the slash command becomes the orchestrator). Severity/category schema stays. Tests stay (just renamed).

### §4.6 critique.md schema

**Codex finding [MEDIUM] #4**: pure Markdown table is too weak for a future critique → spec.yaml feedback hook. Use **YAML front-matter + Markdown body** so the file is both human-readable and machine-parsable.

```markdown
---
schema: figure-agent.critique.v1
fixture: trap_depth_picture
generated_at: 2026-05-03T15:42:00+09:00
verdict: revise        # one of: ready | revise | block
findings:
  - id: C001
    severity: MAJOR    # BLOCKER | MAJOR | MINOR | NIT
    category: physics  # physics | label_placement | whitespace | hierarchy | palette | style
    tex_lines: [42, 57]
    observation: "trap depth arrow direction contradicts briefing §6"
    suggested_fix: "reverse arrow and relabel Et axis"
    status: open       # open | accepted | dismissed | applied
---

# Vision Critique — trap_depth_picture

(Human-readable Markdown summary written by host Claude under the front matter.
The YAML block above is the parseable surface; this prose is for the author.)
```

Reading `findings[*].severity == BLOCKER|MAJOR` later becomes the gate for the optional spec.yaml/.tex auto-patch.

### §4.4 REWRITE: L2 reference_extract.py module split

```
reference_extract.py (1060 lines, monolith)
   ↓ split
ocr.py            (~250 lines)  Tesseract OCR
palette.py        (~300 lines)  K-means + connected components
vtrace.py         (~250 lines)  vtracer SVG → structural_regions
hints_writer.py   (~150 lines)  coordinate_hints.yaml serialization
```

Resolves rot CRITICAL (single file >1000 lines).

---

## §5. What stays untouched (proven, do not modify)

- **L4 Compile/WARN loop** — collision 0 achievement validated, WARN-driven iteration proven across 3 N=3 trial fixtures.
- **L5 Export staleness contract** (Layer A/B) — content-hash based, mtime-free.
- **golden_contract + accepted mode** — gate pattern works.
- **flagship macro library** (BellCurve, BandDiagram, IsoBlock, IsoCharge, GradSlab, IsoConeTip) — **6 macros frozen at current count**; no additions.
- **status.py** read-only pattern (file may be split, behavior unchanged).

---

## §6. Execution plan (4 PRs — corrected after Codex review)

```
PR #7 — Cleanup (rot 해소 + N=3 trial 기록)
   ├─ commit currently untracked items (10 dirs / 25 files via --untracked-files=all)
   ├─ N=3 docs section append
   ├─ split reference_extract.py → ocr/palette/vtrace/hints_writer
   └─ this doc as docs/architecture-v0.2-proposal.md (rev 2)

PR #8a — Frozen-legacy clean delete (no stage migration; 2-3 hrs)
   ├─ rm scripts/{prompt_gen,redact,llm_author_prompt}.py
   ├─ rm commands/{fig_prompt,fig_preview_select}.md
   ├─ rm prompts/llm_author_tikz.md
   ├─ rm tests/test_llm_author_prompt.py
   ├─ tests/test_inputs.py — drop selection_notes parser tests (5 cases)
   ├─ tests/test_release_contract.py — drop {{selection_notes}} template assertion
   ├─ commands/fig_new.md — drop scaffold line for selection_notes/selected_preview
   ├─ README.md:103 — drop historical roadmap reference
   ├─ leave existing fixture spec.yaml files alone (yaml ignores unknown keys;
   │   preserves historical record across 5 fixtures)
   └─ CLAUDE.md / SKILL.md / README.md frozen-section trim

PR #8b — Stage-model migration (selected_preview removal)
   ├─ refactor scripts/status.py Stage 2/3 logic to drop selected_preview dependency
   ├─ update commands/{fig_compile,fig_status,fig_new}.md
   ├─ update tests/{test_inputs,test_status}.py
   ├─ README.md update
   └─ THEN drop spec.yaml.selected_preview field

PR #9 — L4.5 Vision Critique (rename + extend, NOT new file)
   ├─ git mv scripts/review_brief.py scripts/critique_brief.py
   ├─ git mv commands/fig_review.md commands/fig_critique.md
   ├─ extend critique_brief.py:
   │    - keep _require_fresh_png, _line_numbered, severity schema
   │    - add YAML front-matter writer for examples/<name>/critique.md
   │    - rewrite top-level main(): write file (not stdout HALT)
   ├─ rewrite commands/fig_critique.md body for host-loop orchestration
   │  (slash command Reads PNG, calls critique_brief.py for prompt context,
   │   host Claude writes the critique inline → file)
   ├─ examples/<name>/critique.md schema doc (see §4.6)
   └─ CLAUDE.md policy clarification:
       "delegates vision tasks to host Claude Code main loop;
        never calls external vision API directly"
```

PR ordering rationale: #7 → #8a → #8b → #9. #8b depends on #8a (smaller blast radius first). #9 reuses `review_brief.py` so MUST run after the legacy cleanup but does NOT depend on stage migration.

---

## §7. Open questions / decisions

- **[RESOLVED] L9 removal blast radius** — Codex finding [HIGH] #1 verified. `selected_preview` is wired into `status.py:122,286` Stage 2/3 logic. Plan split into PR #8a (clean delete) + PR #8b (stage migration).
- **[RESOLVED] review_brief.py reuse** — Codex finding [HIGH] #2 verified. PR #9 changed from delete+rewrite to rename+extend. Reuses existing `_require_fresh_png`, `_line_numbered`, severity schema.
- **[RESOLVED] critique.md schema** — Codex finding [MEDIUM] #4 accepted. YAML front-matter + Markdown body (see §4.6).
- **[RESOLVED] L5 numbering collision** — Codex finding [MEDIUM] #3 fixed. Vision Critique = L4.5; Export keeps L5; Validation keeps L6.
- **[RESOLVED] status.py size** — Codex finding [LOW] #5 corrected. status.py is 382 lines (not 703 — that was test_status.py). Below SUSPICIOUS threshold; no split needed.
- **[RESOLVED] vision critique patch automation** — **report-only mode for v0.2** (option A). Critique writes `critique.md` with structured findings; no auto-apply, no patch staging. Rationale: vision LLM accuracy unknown (N=0 in this codebase); iteration's slow step is *judgment* not *typing*; spec.yaml/.tex are source-of-truth and auto-revert leaves git noise. Escalation path: after N=5+ dogfood runs, if accuracy ≥ 80%, consider category-tiered auto-apply for `palette`/`style` only (lint_tex.py BLOCKER tier validates mechanically).
- **[RESOLVED] selection_notes blast radius** — grep verified. Active callers outside `llm_author_prompt.py`: `tests/test_inputs.py` (5 spec-parser tests), `tests/test_release_contract.py` (1 template assertion), `commands/fig_new.md` (scaffold line), `README.md` (1 historical doc reference). 5 fixture spec.yaml files retain `selection_notes:` field — leave in place (yaml ignores unknown keys; preserves historical record). PR #8a effort revised: 2-3 hrs.
- **[DEFERRED] Inkscape post-process** — useful but separate concern. Add as L7 Polish later if needed (deadline ≥ 3 months gives room).
- **[DEFERRED] critique → spec.yaml feedback hook (true learning loop)** — defer until L4.5 vision critique proves useful in real iterations.

---

## §8. Honest cost/benefit summary (rev 2)

| Change | PR | Effort | Value | Risk |
|---|---|---|---|---|
| Commit untracked + N=3 docs | #7 | 30 min | data preservation | none |
| Split reference_extract.py | #7 | 2-3 hrs | rot CRITICAL → SAFE | tests need re-pointing |
| Frozen-legacy clean delete | #8a | 2-3 hrs | -files, mental load drop | low (selection_notes scope verified — §7) |
| Stage-model migration | #8b | 3-4 hrs | drop selected_preview cleanly | MEDIUM (status.py logic + tests touched) |
| L4.5 Vision Critique (rename+extend) | #9 | 3-4 hrs | THE quality lever | low (reuses tested code; new file = critique.md only) |
| Identity consolidation | (later) | 1 hr | drift prevention | low |

**Total**: ~11-15 hours of focused work spread across 4 PRs. Not a months-long refactor. Risk is concentrated in PR #8b (stage migration) — handle that one with extra test coverage.

---

## §9. Decision log

- 2026-05-03 — initial draft written from session redesign (rev 1)
- 2026-05-03 — rev 2 after Codex review: 5 findings all accepted
  - [HIGH] L9 blast radius → split into PR #8a + #8b (stage migration)
  - [HIGH] review_brief.py → rename+extend (not delete+rewrite) in PR #9
  - [MEDIUM] L5 numbering → Vision Critique = L4.5; Export keeps L5
  - [MEDIUM] critique.md schema → YAML front-matter + Markdown body
  - [LOW] doc inconsistencies → status.py 382 (not 703); date 2026-05-03; untracked = 25 files
- 2026-05-03 — rev 2.1 selection_notes scope verified + critique automation level fixed
  - selection_notes: active callers in test_inputs / test_release_contract / fig_new / README beyond llm_author_prompt.py; PR #8a effort 2-3 hrs (was 1-2)
  - critique automation: option A (report-only) chosen for v0.2; escalation gated on N=5+ dogfood accuracy ≥ 80%
- 2026-05-04 — proposal ACCEPTED; v0.2.0 release
  - PR #7 (reference_extract split), PR #8 (frozen-legacy delete), PR #9 (CI infra fix — qpdf + Arial + qdf encoding + smoke pre-build), PR #10 (selected_preview stage gate removal), PR #11 (review_brief → critique_brief rename + L4.5 host orchestration) all merged.
  - Final test count 188 pass (was 242; -54 from deleted frozen + selected_preview tests).
  - All Python files <1000 lines (max: vtrace.py 622). Rot SAFE.
  - plugin.json / pyproject.toml / uv.lock bumped 0.1.14 → 0.2.0.
  - CHANGELOG.md `[0.2.0]` entry written.
