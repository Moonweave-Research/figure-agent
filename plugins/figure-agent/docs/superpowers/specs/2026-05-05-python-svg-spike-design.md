# Python→SVG Figure Engine Spike — Design

**Date**: 2026-05-05
**Branch (planned)**: `experiment/python-svg-spike`
**Worktree (planned)**: `[figure-agent-py]/`
**Owner**: Codex (handoff brief)
**Status**: pre-implementation, brainstorming gate passed (advisor reviewed)

---

## 1. Goal

Empirically measure whether a Python+SVG-first figure engine (drawsvg + matplotlib + dvisvgm) reaches paper-grade quality faster and with less friction than the current TikZ pipeline, on a *drawing-heavy* + *math-typography* test set. The output of the spike is **decision data** — three numerical gates that cleanly route to one of three follow-up paths: (γ) full Python build, (β) hybrid (Python where it wins, TikZ elsewhere), or kill (TikZ remains canonical).

## 2. Non-goals

- Not a build of a v0.3 figure engine. The spike is a **6–12h falsification experiment**, not the start of a 6–10 PR effort.
- Not a chemistry-skeletal port. `chemfig` has no Python equivalent in scope; chemistry-bearing figures stay TikZ regardless of spike outcome (see §10).
- Not an isometric / 3D test. Isometric is queued as separate spike-2 *only if* spike-1 passes (§10).
- Not a Hub interaction redesign. `[Graph_making_hub]/` import count must remain 0 throughout the spike (§10).

## 3. Background

Project memory established two findings prior to this spike:

1. *"Engine is not the ceiling"* (`session_strategic_fork_2026_05_05.md`): TikZ-as-opaque-generator partially closed G4. Element-iteration was named the next lever, not engine replacement.
2. *"Snippet = read-only documentation"* (`feedback_snippet_role_reframe.md`): Abstractions hiding internals became reference material, not modules.

Both findings argue against new engine layers. However, the user has now identified a concrete reference image (`examples/fig1_overview/reference/variant_aesthetic_ref.png`) that they could not reproduce in TikZ to manuscript quality despite full snippet/macro coverage, plus a desire for isometric capability that TikZ's `3d` library does not serve well. This spike exists to test whether those two observations override the prior findings, with a numerical gate so the answer is empirical, not vibes-based.

## 4. Scope — what Codex builds

Two panels from `examples/fig1_overview/reference/variant_aesthetic_ref.png`:

### Panel A — BR "Macroscopic probe" (drawing-heavy)

Reproduce in Python+SVG:
- Vertical cantilever beam clamped at top, curving left under repulsion (current TikZ at `examples/fig1_overview/fig1_overview.tex` lines 321–379, panel `[P5]`)
- Negative-charge ⊖ markers along the beam
- Hatched/clamped fixed end at top, "Cantilever" tiny callout
- `+V` electrode plate (right-side hatched rectangle)
- Red "Repulsion (dominant)" force arrow pointing left
- Blue "Maxwell attraction (suppressed)" small arrow pointing right
- Dashed field lines between beam and electrode
- Small probe icon (top-left of panel)
- Bottom callout: "Charge-trapping-induced repulsion / dominates over Maxwell attraction"

**Math content in panel A**: minimal (italic body text only). No equations.

### Panel B — Center "Converged deep charge trapping" (math + drawing mix)

Reproduce in Python+SVG:
- Title "Converged deep charge trapping" in card with rounded border
- Energy-axis vertical arrow on left
- LUMO label (top box), HOMO label (bottom box)
- Multiple shallow-state horizontal lines (blue, between LUMO and midgap)
- Multiple deep-state horizontal lines (red, dense near midgap)
- DOS gaussian fills (right side): shallow (light blue), deep (dense red)
- E_t ≈ 0.5–1.0 eV vertical extent annotation with bracketed arrow
- Math labels: `g(E_t)`, `E_t`, axis `Energy`, axis `g(E_t)`
- Bottom italic callout: "Deep states dominate the trap landscape near midgap, driving the long-lived repulsive response."

**Math content in panel B**: real — `E_t`, `g(E_t)`, subscripts, italic math styling.

### 4.1 Fixed sub-region tags (frozen pre-spike)

Codex MUST use exactly these tags in commits and friction log. No additions, renames, or merges. 20 slots total.

**Panel A — BR cantilever (9 tags):**
- `A.cantilever_beam` — vertical → leftward-curving beam path
- `A.clamp` — hatched fixed end at top
- `A.charges` — ⊖ markers along the beam
- `A.electrode` — `+V` hatched plate (right side)
- `A.repulsion_arrow` — red leftward force arrow + label
- `A.maxwell_arrow` — small blue rightward arrow + label
- `A.field_lines` — dashed lines between beam and electrode
- `A.probe_icon` — small probe icon (top-left)
- `A.callout` — bottom italic 2-line callout

**Panel B — center "Converged deep charge trapping" (11 tags):**
- `B.title` — heading + rounded card border
- `B.energy_axis` — vertical Energy axis arrow
- `B.LUMO_box` — top label box
- `B.HOMO_box` — bottom label box
- `B.shallow_lines` — multiple blue shallow-state horizontal lines
- `B.deep_lines` — multiple red deep-state horizontal lines
- `B.DOS_shallow` — light-blue gaussian fill (right side)
- `B.DOS_deep` — dense-red gaussian fill (right side)
- `B.Et_annotation` — bracketed E_t ≈ 0.5–1.0 eV annotation
- `B.math_labels` — `g(E_t)`, `E_t`, `Energy` axis labels (math typography)
- `B.callout` — bottom italic summary

### Out of spike-1
- Panel TL (Sulfur polymer / chemistry skeletal): excluded. chemfig→drawsvg ecosystem is absent; spike-1 must not contaminate the measurement with chemistry-stack instability.
- Panel BL (Interpretation): excluded. Plot-dominant; matplotlib SVG-export is well-known; no new information from the panel.
- Panel TR (Electrical evidence): excluded. Same reason as BL.
- Inter-panel curved gradient arrows (between corners and center): excluded. Layout glue, not a stack stress test.
- Isometric variants of any panel: excluded. Queued as spike-2 (§10).

## 5. Stack decisions (locked, no Codex deviation)

| Layer | Tool | Rationale |
| --- | --- | --- |
| Schematic primitives (lines, paths, arrows, hatching, rectangles, beziers) | `drawsvg` | Mature Python SVG emitter; layout glue role only. |
| Plot SVG (DOS gaussians, any axes) | `matplotlib` (SVG backend) | Already in workspace, paper-grade. Used only for *plot-class* sub-regions. |
| Math typography (`E_t`, `g(E_t)`, `\tau`, etc.) | `dvisvgm` (LaTeX → SVG) | Paper-grade kerning. mathtext rejected (1-tier quality gap). LaTeX dep is *math-typography only*; not a TikZ regression. |
| Layout / panel composition | `drawsvg` (group + transform) | Single composition primitive. |

`svgwrite` is **not** in stack — drawsvg covers the same role with better ergonomics.
`rdkit`, `chemfig`, `mhchem→SVG` are **not** in stack — out of spike-1 scope.

## 6. TikZ control (free baseline)

Both panels have existing TikZ controls in `examples/fig1_overview/fig1_overview.tex`:

- Panel A (BR cantilever) → lines 321–379, panel `[P5]`
- Panel B (center "Converged deep charge trapping") → lines 159–250, panel `[P3]` (LUMO/HOMO bands, shallow/deep state lines, DOS gaussians, E_t annotation, midgap callout)

Codex does NOT re-author either TikZ version. Both controls already exist, so the friction log + comparison are 2-sided for both panels.

## 7. Decision gates (numerical, locked pre-spike)

All three gates are evaluated *after* the spike is complete. No gate may be tuned post-hoc.

| Gate | Threshold |
| --- | --- |
| **G1 — Hours** | Panel A ≤ 6h **and** Panel B ≤ 4h. 12h hard stop applies regardless of completion. **Definition**: panel-implementation time only. One-time stack setup (drawsvg install verify, dvisvgm `\documentclass{standalone}` smoke, helper bootstrap) is logged separately in `setup_time_log.md` and is **excluded** from G1. Timer starts after the dvisvgm pre-flight in §12 passes. |
| **G2 — Reference-grounded match** | ≥ 80% per panel, evaluated under the existing `docs/critique-evaluation-rubric-v1.md` reference-grounded protocol (same N=3 §7 gate as host critique). **Evaluator**: G2 is scored by the user (host) running `/fig_critique` against the reference image *after spike handback*. Codex does NOT self-score G2 or include G2 numbers in deliverables. (Memory `project_v0_2_critique_reference_grounding.md` documents ~50% drift of LLM self-evaluation without reference grounding; this guard prevents that path.) |
| **G3 — P0 friction count** | < 2 P0 (blocking) frictions across both panels combined. To suppress self-grading bias, every friction log row also carries a binary `scales-to-remaining-panels-without-new-P0: yes/no` field (§8). A row marked `no` is *automatically promoted* to P0 regardless of the severity Codex initially assigned. |

**Routing**:
- 3/3 pass → (γ) candidate. Promote to full design proposal.
- 2/3 pass → (β) hybrid. Identify which axis won (drawing vs math) from friction log, restrict (β) to the winning axis only.
- ≤ 1/3 pass → kill. Record outcome in KB; engine direction frozen until new evidence.

## 8. Friction log (structured, mandatory)

For every sub-region tag in either panel, Codex records exactly one row:

```
sub-region: <tag from §4.1>
hours: <float>
category: drawing | math | typography | layout
severity: P0 | P1 | P2
missing-from-stack: <one-line description, or "none">
scales-to-remaining-panels-without-new-P0: yes | no
notes: <≤ 240 chars, optional>
```

P0 = blocked, no completion path inside stack.
P1 = completed but with workaround that would not survive a real paper figure.
P2 = minor friction, completed cleanly.

`scales-to-remaining-panels-without-new-P0`: forces a hard binary on every workaround. If `no` (i.e., the workaround does not generalize to remaining panels in a hypothetical full build without introducing a new blocker), the row is **automatically promoted to P0** for G3 counting, regardless of the severity Codex initially assigned. This prevents progress-pressure-driven P0→P1 downgrade.

Freeform diary entries are not acceptable as friction log. Decision-gate routing depends on counting P0s; freeform makes G3 unverifiable. Tag must be one of the 20 fixed tags in §4.1; new tags require spec amendment, not unilateral expansion.

## 9. Time-box, commits, deliverable

- **Time-box**: 12h hard stop. Half-done is data; do not extend.
- **Commits**: per sub-region tag, not big-bang. (Per `feedback_subregion_iteration_unit.md` — sub-region is the iteration unit.)
- **Deliverable in worktree**:
  1. `panel_A_BR.svg` and `panel_B_center.svg` (whatever was completed)
  2. `friction_log.md` (structured per §8)
  3. `time_log.md` (per-sub-region hours, summed)
  4. `comparison_BR.md` — TikZ control vs Python spike side-by-side, paper-quality assessment under the reference rubric
  5. Optional `comparison_center.md` if TikZ control existed; otherwise note one-sided in friction_log.md

## 10. Guardrails (Codex must NOT silently expand scope)

1. **Chemistry corollary**: spike success ≠ (γ) authorization for chemistry-bearing figures. `chemfig` has no Python equivalent in stack. Chemistry-bearing figures stay TikZ regardless of spike outcome. Codex must not propose chemfig→drawsvg port as in-scope of this spike or follow-up.
2. **Isometric**: not in spike-1. Cantilever-in-isometric (curved beam + depth-shaded charges + 3D arrow) is the real c-γ test and is queued as spike-2 (separate spec, time-box 6–8h) if and only if spike-1 passes G1+G2+G3. A "single isometric box" placeholder is rejected as unfalsifiable per advisor.
3. **Hub boundary**: `[Graph_making_hub]/` import count = 0 throughout spike. Promote-decision will revisit Hub-vs-fig-agent responsibility split as a separate question, not inside spike code.
4. **Engine creep**: even if 3/3 gates pass, the result authorizes a *design proposal* for (γ), not a build. The proposal goes through standard brainstorming → spec → plan flow.

## 11. Worktree & branch setup

Create from main HEAD:

```bash
git worktree add ../[figure-agent-py] -b experiment/python-svg-spike
```

```
worktree path:   [figure-agent-py]/
branch:          experiment/python-svg-spike
parent commit:   main @ HEAD (8b2bf34 or later)
reference image: examples/fig1_overview/reference/variant_aesthetic_ref.png
TikZ controls:   examples/fig1_overview/fig1_overview.tex
                 - panel [P3] center: lines 159–250
                 - panel [P5] BR:     lines 321–379
spike output:    [figure-agent-py]/experiments/python_svg_spike/
                  ├── panel_A_BR.svg
                  ├── panel_B_center.svg
                  ├── src/
                  │     ├── panel_a_br.py
                  │     ├── panel_b_center.py
                  │     ├── stack/drawsvg_helpers.py
                  │     └── stack/dvisvgm_math.py
                  ├── friction_log.md
                  ├── time_log.md
                  ├── comparison_BR.md
                  └── (optional) comparison_center.md
```

## 12. Codex handoff checklist

Codex acknowledges before starting:
- [ ] Read `examples/fig1_overview/reference/variant_aesthetic_ref.png` (vision-load)
- [ ] Read `examples/fig1_overview/fig1_overview.tex` lines 159–250 (P3, center) and 321–379 (P5, BR) — TikZ controls
- [ ] Read `docs/critique-evaluation-rubric-v1.md` (G2 evaluation protocol — for context only; Codex does NOT score G2)
- [ ] Verify stack pre-flight passes BEFORE timer starts:
      - `drawsvg` import succeeds in target python env
      - `dvisvgm` available on PATH; `pdflatex` + `\documentclass{standalone}` round-trip produces a valid SVG for a trivial `$E_t$` test string
      - `matplotlib` SVG backend produces a valid SVG for a trivial gaussian fill test
      - Setup time logged in `setup_time_log.md` and excluded from G1
- [ ] Confirm stack decisions §5 will not be deviated from
- [ ] Confirm guardrails §10 understood (chemistry, isometric, Hub, engine creep)
- [ ] Confirm friction log §8 structured format will be used; tag list §4.1 frozen
- [ ] Confirm G2 is NOT self-scored; deliverables exclude G2 numbers
- [ ] Confirm 12h hard stop and per-sub-region commit cadence

After spike: do NOT promote, propose, or otherwise act on results. Hand back the four/five deliverables and stop. Promote-decision (and G2 scoring by host) is a separate session.
