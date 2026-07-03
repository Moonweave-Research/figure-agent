# Element-Iteration Loop Protocol — fig1_overview_v5e_aggressive_001_vault

**Target**: Nature-grade aesthetic + complete element quality across 60 sub-regions in 7 panels (A / B / C / Row2 / D / E / F). 4-axis acceptance (이론 / 구조 / 스토리 / 미감), 10-iter cap per panel.

**Prerequisite files** (all present):
- `panel_goals.md` — 4-axis acceptance per panel
- `spec.yaml` — per-panel `reference_image` + bbox (v8.6 6-panel structure)
- `reference/audit_table.md` — 3-axis reference curation tags (transferable / do-not-transfer)
- `briefing.md` — §8 LOCKED + §9 Forbidden + §13 sub-region specs
- `subregion_iteration_log.md` — prior iter history (v5..v8.3)

---

## Trigger

User invokes with one of:
- `Panel <ID> iter <N>` — explicit (e.g., `Panel A iter 1`, `Column D iter 3`)
- `Panel <ID>` — N inferred from log (last iter for this panel + 1)
- `Continue` — resume the most recently active panel

`<ID>` ∈ {A, B, C, Row2, D, E, F}. `<N>` ∈ 1..10.

If `<N>` would exceed 10, do NOT execute — invoke **escalation diagnosis** instead.

---

## Pre-iteration setup (every iter)

Sequential reads (cache for the duration of this iter):

1. `panel_goals.md` §Panel `<ID>` — load intent / forbidden / 4-axis acceptance / known issues / sub-region checklist
2. `spec.yaml` `panels[<ID>]` — load `bbox_pdf_cm` + `reference_image` (may be absent for A/B/C)
3. `reference/audit_table.md` row for `<ID>` — load transferable + do-not-transfer + usability tag
4. **Generate per-panel crop** at 600 DPI via `pdftocairo` (D pre-step — see below), then Read the crop instead of full-figure PNG
5. `fig1_overview_v5e_aggressive_001_vault.tex` lines for sub-regions in scope (per `briefing.md` §13.`<ID>`)
6. `subregion_iteration_log.md` last 3 entries for this panel — load prior scope + 4-axis trajectory
7. `critique.md` open findings for this panel — input to scope selection

Parallel reads OK; do not skip any step.

### D pre-step: per-panel crop to overcome Read-tool downsample

Build PNG is 600 DPI / 4272×2688 — but Read tool downsamples for conversation display, making sub-pixel (≤0.15pt) changes invisible. Per-panel crop preserves DPI within a smaller file → micro-changes register.

Approximate per-panel crop coordinates (top-left origin, 600 DPI pixels):

| Panel | `pdftocairo` args | Crop dims |
|---|---|---|
| A | `-x 0 -y 0 -W 1100 -H 1300` | 1100×1300 |
| B | `-x 1080 -y 0 -W 1000 -H 1300` | 1000×1300 |
| C | `-x 2100 -y 0 -W 2180 -H 1300` | 2180×1300 |
| Row2 | `-x 0 -y 1180 -W 4272 -H 200` | 4272×200 |
| D | `-x 0 -y 1380 -W 1380 -H 1308` | 1380×1308 |
| E | `-x 1450 -y 1380 -W 1450 -H 1308` | 1450×1308 |
| F | `-x 2920 -y 1380 -W 1352 -H 1308` | 1352×1308 |

Command pattern (run after every compile):
```bash
pdftocairo -png -r 600 <x> <y> <W> <H> -singlefile build/<name>.pdf build/panel_<ID>_iter<N>
```

Then Read `build/panel_<ID>_iter<N>.png` for scoring — NOT the full figure PNG.

---

## Iteration body — 7 steps

### Step 1: Scope selection (≤2 sub-regions)

Pick 1–2 sub-regions for this iter. Priority order:

1. Sub-regions with ❌ in last iter's 4-axis trajectory (unresolved regression)
2. Sub-regions with open `critique.md` findings unaddressed
3. Sub-regions whose acceptance bullets in `panel_goals.md` are NOT yet ✅
4. Sub-regions with cross-binding (§13.9) to other panels' open issues
5. Lowest-risk aesthetic polish (only if 이론/구조/스토리 already all ✅)

Document the choice + 1-line rationale in iter log.

### Step 2: Reference scan

**If `reference_image` present** (Panels D / E / F):
- Read the reference PNG path from `spec.yaml`
- Identify aspects in the reference matching this iter's sub-regions
- Cross-check against `audit_table.md` transferable list — DO NOT mine do-not-transfer aspects
- Cite the specific reference aspect in patch source line

**If no `reference_image`** (Panels A / B / C / Row2 — gap):
- Proceed reference-free using `briefing.md` + `§10` polish constraints + Nature chemistry/physics convention judgment
- Mark this in iter log as `reference: briefing-only`
- Higher drift risk acknowledged

### Step 3: Patch proposal — delta-size guideline (Panel A pilot lesson)

**Perceptibility tiers** (apply each patch consciously):

| Change type | Delta | PNG-visible? | When to use |
|---|---|---|---|
| Weight tweak | ±0.05–0.15pt | sub-pixel at 178mm display, ⚠️ marginal even on crop | only when print-scale tuning is the goal (not initial Nature-grade push); flag honestly as ⚠️ |
| Weight jump | ±0.20pt+ | visible on crop | aesthetic axis genuine improvement |
| Tone shift | ±20%+ saturation | visible on crop | palette / wash / fill perceivable change |
| Font size | +20%+ pt | clearly visible | typography rebalance |
| Position / coord | ±0.10cm+ | clearly visible | layout fix |
| Structural (new node, removed node, shape change) | — | always visible | major polish or correction |

**Default for Nature-grade iteration**: prefer **≥+30% delta** OR multi-category mix (weight + tone + position) over micro-tweaks. Reserve micro-tweaks for print-scale-only tuning, marked explicitly.

**Panel A pilot lesson** (iter 1+2 vs iter 3): 0.10pt weight changes are *technically correct* but sub-pixel — both author and user perceived "no change". A axis stayed ⚠️ for 2 iters. iter 3's +36% font + +50% tone moved A axis to ✅ in one pass. Trust this signal — bigger jumps faster.

For each sub-region in scope, draft 1 patch:

```
Sub-region: <ID, e.g., A-3>
Source: reference/<path> (aspect: <e.g., layered cross-section convention>) OR briefing-only
Visibility gate:
  intended visible at print scale? [yes/no/marginal]
  unintended visible (rogue stroke, ghost label, overlap)? [yes/no — describe]
Patch (1-line preferred):
  before: <exact .tex line>
  after:  <exact .tex line>
Expected 4-axis impact: T <delta> | S <delta> | L <delta> | A <delta>
```

Hard limits:
- ≤2 sub-regions per iter
- ≤3 lines of .tex change per patch
- ≤1 briefing.md edit per iter (Type A only — see Step 4)

### Step 4: Briefing edit classification

If patch implies briefing change, classify:

**Type A — apply autonomously in same iter commit**
- Stale spec mismatched to .tex (factual sync — e.g., 'ISPD' label spec → 'derive' rename)
- Typo / broken cross-reference / enumeration mismatch (e.g., "§13.3 says 11 sub-regions but lists 13")
- Briefing internally inconsistent

**Type B — PAUSE loop, escalate to user**
- §8 LOCKED rule change (any invariant)
- §9 Forbidden addition or loosening
- Sub-region add / remove (structural commitment change)
- Intent / acceptance criterion change in panel_goals.md
- New cross-panel binding §13.9

Default: if uncertain, treat as Type B. Loop pauses, returns to user with proposed change + rationale. No autonomous Type B edits.

### Step 5: Apply patches

In order:
1. `.tex` Edit for each patch
2. `briefing.md` Edit (only if Type A)
3. `panel_goals.md` Edit (only if Type A — e.g., acceptance bullet now passed, update score)
4. `bash scripts/compile.sh examples/fig1_overview_v5e_aggressive_001_vault/fig1_overview_v5e_aggressive_001_vault.tex`

If compile fails: do NOT proceed to scoring. Diagnose error, revert problematic patch, log failure, exit iter early with ❌ on all touched axes.

### Step 6: 4-axis scoring

Read the new PNG. Score against `panel_goals.md` 4-axis acceptance:

| Axis | ❌ | ⚠️ | ✅ |
|---|---|---|---|
| 이론 (T) | LOCKED invariant violated this iter (e.g., crosslink topology appears in A, deep-shallow color swap) | Acceptance bullet not yet PASS but no violation introduced | All T bullets pass; no Forbidden triggered |
| 구조 (S) | coords/geometry/sub-region alignment broken; spec drift | Partial match (some bullets ❌, some ✅) | All S bullets pass |
| 스토리 (L) | reading order broken; intent not readable in 2s; cross-binding §13.9 broken | Partial — intent slowed but recoverable | All L bullets pass; intent readable in N-second budget |
| 미감 (A) | Nature-grade visually deficient vs reference (or vs §10 if no ref); regression from prior iter | Improved but reference-gap remains | Nature-grade match against reference (or §10 + judgment if no ref) |

Compare against previous iter scores — monotonic improvement expected. Any regression (e.g., `A ✅ → A ⚠️` next iter) requires explicit rationale in iter log.

### Step 7: Log + commit

**Append to `subregion_iteration_log.md`** under section `## Element-Iteration Loop (Nature-grade, 4-axis)` (create section if not exists):

```
### Panel <ID> iter <N>/10 — 2026-XX-XX

- **Scope**: <sub-region IDs>
- **Rationale**: <1 line — why these sub-regions>
- **Reference source**: <path + aspect> OR briefing-only
- **Patches**:
  - <sub-ID>: <1-line description> (.tex L<line>: <before> → <after>)
- **Briefing edits**: <Type A list with paths and line numbers> OR none
- **4-axis scores**: T <icon> | S <icon> | L <icon> | A <icon>
- **Score delta** (vs prior iter): <axis>: ⚠️→✅, <axis>: unchanged, ...
- **Notes**: <what improved / what remaining gap>
- **Visibility gate**: intended <yes/no> | anomaly <none/describe>
- **Commit**: <commit hash, populated after auto-commit>
```

**Auto-commit** with message format:

```
fig1 panel-<ID> iter <N>/10: <2-3 word patch summary>

- T <icon> | S <icon> | L <icon> | A <icon>
- subregions: <list>
- ref: <reference path aspect | briefing-only>
- iter log: subregion_iteration_log.md
```

Per-iter commit (NOT batched) — enables `git revert <iter-hash>` rollback.

**Commit hash policy**: do NOT backfill commit hash into the iter log entry. Hash is retrievable via `git log --oneline | grep "panel-<ID> iter <N>"` anytime. Backfilling creates a second small commit per iter, doubling history noise. Panel A iter 1 has a backfilled hash as a relic; iter 2+ pattern is preferred.

Do NOT push to remote autonomously. Push happens at panel-closure (all 4 axes ✅ for 2 consecutive iters) with user confirmation.

---

## Termination conditions

Loop terminates when ANY of:

1. **Panel closure**: All 4 axes ✅ for 2 consecutive iters with no new sub-regions touched
2. **Iter cap**: N = 10 reached → **escalation diagnosis** mandatory (do not silently stop)
3. **User STOP**: Freeze state, log reason, no further patches

### Escalation diagnosis (mandatory at N=10 or stuck)

Pick the most-likely cause based on which axis is ❌ at N=10:

- **(a) TikZ engine ceiling** — sub-region can't reach Nature-grade in TikZ at current implementation depth. Trigger: A axis ❌ persistent despite multiple weight/opacity/proportion iterations. Action: defer to SVG handoff (per §12.1 pattern), document in panel known-issues, mark panel as "partial-closure" not full closure.
- **(b) Briefing ambiguity** — spec genuinely doesn't constrain the right thing. Trigger: T or L axis ❌ with patch attempts diverging. Action: Type B escalation — propose briefing edit to user, pause loop.
- **(c) Reference insufficient** — reference doesn't cover the panel's specific needs. Trigger: A axis ❌ for Panel A/B/C (no reference) OR L axis ❌ for panels with reference but storyline-divergent. Action: trigger `/figure-research` for panel-targeted reference collection, resume loop after curation.

LLM picks the diagnosis + writes 3-line escalation message to user. Loop does not advance to iter 11.

---

## Anti-patterns to avoid

| Anti-pattern | Reason |
|---|---|
| Touching >2 sub-regions in one iter | Dilutes element-iteration; LLM rationalizes away discipline |
| Skipping reference audit when reference_image present | Lock-in risk — every patch must cite source |
| Applying do-not-transfer aspect "because it looks better" | Lock-in (memory `feedback_snippet_anchoring_lock_in`) |
| Type B briefing edit without user pause | Silent spec drift |
| 4-axis ❌ marked without naming specific violation | Loss of diagnostic precision |
| Score regression (e.g., A ✅ → A ⚠️) without rationale | Hides oscillation; loop won't converge |
| Bundle multiple iter changes in one commit | Anti-rollback — single revert can't isolate bad patch |
| Compile failure → continue scoring | Bad data; revert and exit iter |
| Skipping log entry "because it was minor" | Loop opacity; next session can't bootstrap |
| **Micro-tweak (≤0.15pt) at iter 1–2 of Nature-grade push** | Sub-pixel = invisible to author + user; A axis stays ⚠️; wastes iter budget. Use only for print-scale tuning. (Panel A pilot lesson) |
| **Reading full-figure PNG for scoring** | Read-tool downsamples; micro/medium changes invisible. ALWAYS generate per-panel crop (`pdftocairo -W <px> -H <px>`) and Read the crop. (Panel A pilot lesson) |
| **Skipping D pre-step on iter 1** | Establishing high-zoom baseline first iter avoids 2-iter false-⚠️ before discovering downsample issue. |

---

## Workflow shortcuts

After **Step 1 (scope selection)**, if scope is identical to prior iter and no new critique finding triggered it: **STOP** and ask user — likely loop oscillation, escalation diagnosis needed.

After **Step 6 (scoring)**, if all 4 axes were already ✅ in prior iter AND this iter scope was preventive polish (not addressing ❌/⚠️): **CONFIRM panel closure** — 2-consecutive ✅ rule satisfied.

If user invokes `Continue` and most recent log shows panel closure: **DO NOT silently continue** — ask user "Panel <last> closed at iter <N>. Which panel next?" Don't auto-pick next panel.

---

## File update conventions

- `subregion_iteration_log.md`: append-only for new iter entries. Past entries (v5..v8.3) untouched.
- `panel_goals.md`: 4-axis acceptance bullets get strikethrough or status icon when ✅ in 2 consecutive iters. Format: `~~T1. ...~~ ✅ (Panel A iter N)`.
- `critique.md`: status field updated when iter resolves a finding (`status: resolved`).
- `briefing.md`: Type A edits only, with iter cross-ref in comment.
- `spec.yaml`: only `accepted: false → true` at full panel closure (user confirms).

---

## Reference quick-look

| File | Authority | When to consult |
|---|---|---|
| `panel_goals.md` §Panel `<ID>` | 4-axis acceptance source | Every iter |
| `briefing.md` §8 / §9 | Theoretical invariants (LOCKED) + Forbidden | Step 1 scope + Step 4 type-A/B + Step 6 T-axis score |
| `briefing.md` §13.<ID> | Sub-region geometry specs | Step 1 + Step 3 patch + Step 6 S-axis |
| `briefing.md` §13.9 | Cross-panel bindings | Step 1 cross-binding priority + Step 6 L-axis |
| `spec.yaml` `panels[<ID>]` | bbox + reference_image | Step 2 reference scan |
| `reference/audit_table.md` row | Transferable / do-not-transfer | Step 2 + Step 3 source citation |
| `critique.md` | Last critique findings | Step 1 scope priority #2 |
| `subregion_iteration_log.md` | Prior iter trajectory | Step 1 priority #1 + Step 6 monotonic check |
| HANDOFF_v8.7.md §1, §5 | Known issues + decisions log | Step 1 priority context |

---

## Pilot recommendation

**Start with Panel A**:
- 8 sub-regions (smallest panel)
- No positive reference → reference-free pilot validates the loop without reference-grounding complication
- Acceptance bullets already 4-axis structured
- No HERO pressure — workflow validation first
- Cross-binding to B/C/F is limited (cAmber identity to Row 2 background chains is loose)

After Panel A closure (or escalation at N=10), promote learnings to template, then iterate Panel C (HERO) with figure-research-augmented reference, then Row 2 columns.

---

## Out-of-scope (this template)

- Caption.md updates (figure caption text) — separate workflow at submission gate
- Multi-figure cross-consistency (Fig 1 ↔ Fig 2..6) — separate workflow per `briefing.md` §18
- SVG handoff for C-L1 polymer sheet — Inkscape workflow, not TikZ iteration
- Export pipeline (TIFF / PDF / SVG for submission) — `fig_export` skill, not iteration loop
