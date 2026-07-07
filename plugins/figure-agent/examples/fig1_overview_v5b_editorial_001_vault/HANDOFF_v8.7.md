# fig1_overview_v5b_editorial_001_vault — Handoff (v8.7 + 5-iter critique polish)

**Last update:** 2026-05-17 02:30 KST
**Branch state:** `main` at commit `7d41ac2` (worktree `vigorous-mcclintock-66fd4f` merged)
**Stage:** Row 2 Option α 3-column restructure + Nature Comm publication-grade apparatus zones + 5-iteration critique polish — ALL SHIPPED
**Working PNG:** `plugins/figure-agent/examples/fig1_overview_v5b_editorial_001_vault/build/fig1_overview_v5b_editorial_001_vault.png`

---

## What's done (this session)

### Big structural moves
1. **Row 2 restructured 4 panels → 3 columns** (v8.6, commit `510501c`)
   - D/E/F/G (4 panels) → Column D (kinetic) / Column E (ISPD-paired V_s+g(E_t) stacked) / Column F (mechanical, was G)
   - Each column: apparatus zone (top y=2.80..4.25) + result zone (bottom y=0.20..2.60)
   - 3 spokes from C HERO → 3 column centers (2.28 / 6.975 / 11.70)
   - Old G letter retired; panel letters now A..F continuous

2. **§8.5 LOCKED rule amendment — Maxwell baseline ALLOWED in apparatus zone, FORBIDDEN in result zone**
   - Pre-v8.6: Maxwell forbidden everywhere in Fig 1 G (preserve Coulomb-only novelty)
   - v8.6+: Maxwell light-pink dashed in Column F apparatus = "baseline before trapping"; Coulomb bold red solid in result = "wins against baseline." Color tier asymmetry IS the novelty argument.
   - New theory guard TG-G-002 enforces this (color/weight discrimination check)

3. **Apparatus zones upgraded to Nature Comm grade** (v8.7, commit `48d5104`)
   - Column D: SMU box (V/A labels) + 2 leads + MIM stack (top/bottom hatched electrodes + cAmber polymer film) + ground
   - Column E: Corona needle (+ polarity, "Corona" label) + wide sample slab (grounded, "polymer film" label) + Kelvin probe ("Probe" label) + support stem + V_s meter box
   - Column F: PSU (V_active) + 2 leads (above + below routing) + mount-spacer stipple + neutral pale polymer + cross-hatched electrode (Conrad 2016 45°+135°) + Maxwell baseline arrow + "F_Maxwell (baseline)" label

4. **5-iteration critique polish** (commit `7d41ac2`)
   - Iter 1: redundancy / panel letter realign / MIM hero / Maxwell 1-line / corona thickness / ISPD inter-arrow center
   - Iter 2: Coulomb arrow boundary / Maxwell opacity / polymer film readability / "derive" replacing redundant ISPD / V_s curve dynamic
   - Iter 3: material terminology unified / V_active vs SMU disambig / apparatus electrode x-align to result
   - Iter 4: Column F clip+polymer+q_tr+Coulomb arrow+air gap all aligned (clip is FIXED, polymer MOVES narrative) / Gaussian peak ratio 1.26×→2.0× (briefing 1.86× spec)
   - Iter 5: holistic sign-off (no regressions / storyline coherent / color binding / panel letter continuity verified)

### Reference assets gathered (commit `48d5104`)
- 18 PNG candidates in `reference/row2_apparatus/` from figure-researcher agent
- `candidates.md` with per-PNG annotation (source DOI / strengths / weaknesses / mining points / gap report)
- **TOP refs adopted into .tex:**
  - Apparatus 1 (kinetic): **Wang et al Nat Commun 2022** Fig 1e — equivalent-circuit framing (partial-mined as generic SMU+MIM synthesis since OA pool weak for transient I-t rigs)
  - Apparatus 2 (ISPD): **He et al Nat Commun 2024** Fig 1c — direct adapt for Probe/Sample/Meter layout
  - Apparatus 3 (mechanical): **Conrad et al Nat Commun 2016** Fig 1b — cross-section idiom + cross-hatched electrode + spacer stipple

### Briefing additions this session
- **§3.2** Setup-context rule (mini-icon discipline, now SUPERSEDED by v8.7 full apparatus zones but kept as constraint)
- **§3.3** Row 2 size hierarchy verification gate (ARCHIVED post-v8.6 — asymmetry dissolved structurally)
- **§8.5** Maxwell amendment (apparatus allowed, result forbidden, color-tier convention)
- **§15** Export-time specs (Nat Comm 89/178mm, PDF+SVG+TIFF+PNG, font embedding)
- **§17** Dashed-line semantics consolidation (4 locked semantics with discrimination rules)
- **§18** Cross-figure consistency (8 paper-wide anchors locked by Fig 1 for Fig 2..6 inheritance)
- **§13.5–§13.7** completely rewritten for 3-column structure (22 sub-regions → 25)
- **§13.4** spoke endpoints + modality label positions updated
- **§13.3 C-L6** thin-film thickness anchor spec
- **§13.2 B-4** sample boundary divider spec

---

## What's pending (next session candidates)

### 1. Fresh `/fig_critique` re-run (HIGH priority — submission gate)
.tex changed massively across v8.2→v8.7. `critique.md` carries notes through v8.5 but post-v8.6/v8.7 reconciliation flag only. Reference-grounded critique pass needed before any `accepted: true` claim.
- Run: `cd plugins/figure-agent && uv run python scripts/critique_brief.py examples/fig1_overview_v5b_editorial_001_vault` then host-write fresh `critique.md`
- TG-G-002 specifically pending (Maxwell-vs-Coulomb color/weight discrimination verification)

### 2. Caption.md update (HIGH priority — submission gate)
Current `caption.md` predates v8.6 restructure. Must update:
- Apparatus zone narrative (SMU+MIM / Corona+Probe+meter / PSU+fixture+Maxwell)
- "Coulomb wins against baseline Maxwell attraction" claim in Column F
- ISPD first-use expansion still applies (per briefing §13.6 E-4 Q12)
- 6-panel A..F caption pieces (was 7 panels A..G pre-v8.6)

### 3. Audit doc reconciliation (MEDIUM)
- `critique.md`: v8.6 + v8.7 changes not reflected
- `QUALITY_AUDIT.md`: only v8.6 note added; v8.7 critique-iter1-5 fixes need entry
- `subregion_iteration_log.md`: v8.6 + v8.7 iter rows not added
- `theory_guard.md`: TG-G-002 added but status still "pending v8.6 .tex implementation" — should escalate to "pending verification post-v8.7"

### 4. briefing §14 (caption template) + §16 (provenance) — DEFERRED earlier (LOWER)
Both deferred by user in earlier turns. Submission-readiness needs both eventually.
- §14: figure caption skeleton + ISPD expansion responsibility
- §16: AI-image policy + author provenance statement format (TG-PUB-001 close)

### 5. Possible polish items (LOW, defer unless critique flags)
- Column F apparatus zone PSU pulse trace very thin (0.20pt) — may not register at print scale
- Column D MIM hatching dense at small render — may look noisy on 300dpi raster
- Column E V_s meter readout indicator (horizontal line inside box) — barely visible
- "F_Maxwell (baseline)" label sits across apparatus polymer + Maxwell arrow gap — slight visual crowding
- Visual clash count 56 (mostly false-positive text-on-fill / near-miss / intentional embedded glyphs)

### 6. Cross-figure work (NEW — out of fig1 scope)
- Fig 5 mechanism schematic (already v4 commit `6be2559`) — may need further polish if becomes hero supporting Fig 1 Column F
- Fig 3 trapping concept — pending separate work
- All other figures should follow §18 cross-figure consistency anchors set by Fig 1

---

## Key file paths

```
plugins/figure-agent/examples/fig1_overview_v5b_editorial_001_vault/
├── briefing.md                    # ~770 lines, v8.6 + v8.7 specs locked
├── fig1_overview_v5b_editorial_001_vault.tex   # ~770 lines, v8.7 critique-polished
├── caption.md                     # STALE — v8.5-era, needs v8.7 rewrite
├── critique.md                    # v8.5-era + v8.6 reconciliation flag
├── QUALITY_AUDIT.md               # v8.5 + v8.6 note, missing v8.7 critique entries
├── theory_guard.md                # TG-G-001..ROW2-001 + TG-G-002 (NEW v8.6)
├── subregion_iteration_log.md     # v7 entries, missing v8.4-v8.7
├── design.md                      # 26k baseline design
├── authoring_contract.md
├── authoring_plan.md
├── spec.yaml
├── reference/
│   ├── row2_apparatus/            # 18 PNG + candidates.md (v8.7 references)
│   ├── sulfur_polymer_panelA_ref.png    # anti-reference (topology forbidden)
│   ├── codex_gen_overview_v1.png        # style anchor
│   └── reference_pack.md
├── build/                         # gitignored compile artifacts
└── exports/                       # PDF/SVG/TIFF/PNG (TRACKED_GOLDEN)
```

---

## Bootstrap commands for next session

```bash
# 1. Sanity-check working state
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
git log --oneline -5 main
ls -la examples/fig1_overview_v5b_editorial_001_vault/build/

# 2. Fresh compile (should match committed PNG)
bash scripts/compile.sh examples/fig1_overview_v5b_editorial_001_vault/fig1_overview_v5b_editorial_001_vault.tex

# 3. View current PNG
# /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview_v5b_editorial_001_vault/build/fig1_overview_v5b_editorial_001_vault.png

# 4. Fresh critique (next gate)
uv run python scripts/critique_brief.py examples/fig1_overview_v5b_editorial_001_vault

# 5. Re-export when ready
uv run python scripts/run_export.py fig1_overview_v5b_editorial_001_vault --skip-critique --force-golden
```

---

## Critical decisions log (so they don't get re-litigated)

1. **Row 2 went 4 panels → 3 columns** (Option α from brainstorming menu). Other options
   considered: ζ (apparatus strip above Row 2), η (minimal result icons + caption-only apparatus),
   θ (hub-and-spoke radial). Rejected θ for non-standard layout + physical inaccuracy
   ("1 sample 3 measurements" false because mechanical uses cantilever, not film).

2. **Maxwell stress allowed in apparatus zone, forbidden in result zone** (§8.5 amendment).
   User's physics framing: "Maxwell attraction baseline + Coulomb wins" is the paper's actual
   novelty claim. Pre-v8.6 hid Maxwell — Coulomb arrow read as "just an arrow." Color tier
   (Maxwell light pink dashed / Coulomb bold red solid) signals winner narratively.

3. **G shouldn't be hero** (Option D rejected). User: "G가 메인 피겨가 아니라 evidence 중
   하나." Paper framing v9.7 LOCKED = charge-trap-centered (NOT actuation showcase). Making
   G a hero would tilt paper narrative toward actuation.

4. **Generic SMU+MIM synthesis for Column D** (Apparatus 1). OA Nature pool weak for transient
   I-t rigs. Decided synthesize from standard EE convention rather than expand to paywall /
   pre-2015 / OFET adjacent. Acceptable tradeoff per user directive (a) in reference-decision turn.

5. **"polymer film" terminology unified** across all 3 columns (was "sample" in E, implicit
   in F). Same material (poly(S-r-DIB)) → consistent reader experience.

6. **Clip is FIXED, polymer MOVES** narrative locked. Apparatus + result zone clip/polymer
   x-aligned in Column F so reader perceives temporal evolution of same setup, not two
   different fixtures.

---

## Open questions for user

1. Should `/fig_critique` re-run trigger before or after caption.md update?
   - If before: critique might flag caption-related issues
   - If after: clean run with both gates aligned
   - **Recommend: caption.md first, then critique**

2. Submission target journal? Affects:
   - Column width spec (Nat Comm 89/178mm assumed for now)
   - AI-image provenance statement format (§16 still pending)
   - TIFF DPI target (600 currently)

3. Should Fig 5 mechanism schematic (already v4) get cross-consistency check against
   Fig 1 v8.7 (per §18)? Especially Maxwell-vs-Coulomb color tier rule (TG-G-002) and
   the 7-phase waveform / Phase D snapshot.

4. v8.4 mini-icon discipline (§3.2) is now SUPERSEDED by v8.7 full apparatus zones.
   Should §3.2 be archived / merged into §18 cross-figure rule, or kept as fallback
   for sister figures with less space?

---

## Known limitations (accept or escalate)

- `critique.md` post-v8.6/v8.7 reconciliation is partial (note only, no per-finding update)
- `subregion_iteration_log.md` missing v8.4–v8.7 rows
- §14 (caption template) + §16 (provenance) still deferred — needed for `accepted: true` but
  not for working / iteration
- Visual clash count 56 is mostly false positives — not addressing unless critique flags
- Cross-hatching density on Column D MIM electrodes may render coarse on 300dpi raster
- Column F PSU pulse trace barely visible at standard print scale — could be enhanced

EOF
