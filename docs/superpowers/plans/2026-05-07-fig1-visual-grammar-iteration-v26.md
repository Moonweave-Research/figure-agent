# Fig1 Visual Grammar Iteration v26 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current Fig1 visual-polish spike from ad hoc coordinate edits into bounded panel-level visual grammar iterations, then commit only accepted visual changes with regenerated artifacts, report, docs, and hash.

**Architecture:** Keep Python semantic payloads and scaffold contracts as the source of truth. Do not add a new gate or open-ended vision layer. For each panel, first define local visual grammar anchors, then make narrow renderer/scene edits, render crops, accept or reject visually, and only then update baseline/report/docs.

**Tech Stack:** Python semantic scene, `drawsvg`, `matplotlib`, `numpy`, `shapely`, `svgelements`, `svgpathtools`, ImageMagick `magick`, `rsvg-convert`, existing Fig1 verifiers.

---

## Pre-Flight State

Current branch: `experiment/python-svg-semantic-fig1`

Protected dirty legacy files. Do not stage, revert, commit, or edit:

- `experiments/python_svg_semantic_fig1/src/fig1_scene.py`
- `experiments/python_svg_semantic_fig1/src/semantic_scene.py`

Known untracked non-scope path:

- `.claude/`

Current accepted baseline before v26 probe iteration:

- v25 commit: `01da12b SEMANTIC.fig1: expose origin payload labels`
- expected baseline hash in `src/verify_fig1_baseline_hash.py`: `76c7976517daf457f7f996945c69d8fd75314113b3125076c41527b04b2ec946`

Current uncommitted visual-iteration hash:

- `aa0dd6f8c84c331517964cfde463eb3db31f42018cd1ddae8c92e69d79ca5507`

Current verification snapshot:

- `run_fig1_gates.py`: 7/8 PASS; baseline hash fails because v26 visual changes are not accepted/hash-pinned yet.
- `test_fig1_*.py`: 37 tests OK under `uv`.
- `verify_fig1_physics_sanity.py`: PASS.
- `verify_fig1_semantics.py`: PASS.
- `verify_fig1_scaffold_contract.py`: PASS.
- `verify_fig1_render_parity.py`: PASS.

Blocking design risk before commit:

- Maxwell cue was changed from historical leftward reference cue to rightward toward-electrode stress cue. This is visually aligned with “Coulomb repulsion wins over Maxwell attraction,” but it conflicts with old v20 documentation text unless v26 docs explicitly supersede it.

---

## File Map

Modify only accepted v26-scope files:

- `experiments/python_svg_semantic_fig1/src/fig1_l1_scene.py`
  - Probe/electrical/hero/interpretation/origin payload coordinates and object positions.
- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
  - Panel-local renderer geometry and visual grammar.
- `experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py`
  - Only if an accepted semantic visual contract changes, such as Maxwell cue direction.
- `experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py`
  - Only if an accepted physics sanity contract changes, such as Maxwell cue direction.
- `experiments/python_svg_semantic_fig1/src/test_fig1_physics_sanity.py`
  - Only if direction mutation tests need clearer expected wording.
- `experiments/python_svg_semantic_fig1/README.md`
  - Add v26 visual grammar status and verification command updates.
- `experiments/python_svg_semantic_fig1/physics_sanity_inventory_v20.md`
  - Add a supersession note for Maxwell direction if rightward cue is retained.
- `experiments/python_svg_semantic_fig1/physics_sanity_contract_v20.md`
  - Add a supersession note for Maxwell direction if rightward cue is retained.
- `experiments/python_svg_semantic_fig1/probe_visual_grammar_handback_v26.md`
  - Create when probe visual grammar is accepted.
- `experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py`
  - Add v26 handback tokens if a v26 handback is tracked.
- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`
  - Regenerated artifact.
- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
  - Regenerated artifact.
- `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`
  - Regenerated comparison artifact.
- `experiments/python_svg_semantic_fig1/fig1_visual_judgment_report.md`
  - Regenerated report artifact.
- `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py`
  - Update only after user accepts the visual checkpoint.

Do not modify:

- `experiments/python_svg_semantic_fig1/src/fig1_scene.py`
- `experiments/python_svg_semantic_fig1/src/semantic_scene.py`

---

## Visual Acceptance Rules

Use these for every panel cycle:

- One cycle changes one panel or one clear cross-panel grammar decision.
- No new gate.
- No new report category.
- No min-font-size rule.
- No pixel tracing.
- No TikZ prototype in this repo.
- No baseline hash update until the user visually accepts the checkpoint.
- If a panel still feels wrong after 3 focused cycles, stop that panel and move to the next panel instead of overfitting.
- If total v26 panel cycles exceed 10 without whole-figure improvement, freeze the spike and write a handoff rather than continuing.

---

### Task 1: Probe Contract Reconciliation

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py`
- Modify: `experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py`
- Modify: `experiments/python_svg_semantic_fig1/physics_sanity_inventory_v20.md`
- Modify: `experiments/python_svg_semantic_fig1/physics_sanity_contract_v20.md`
- Create: `experiments/python_svg_semantic_fig1/probe_visual_grammar_handback_v26.md`
- Modify later if accepted: `experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py`
- Modify later if accepted: `experiments/python_svg_semantic_fig1/README.md`

- [ ] **Step 1: Decide Maxwell direction for v26**

Keep the current rightward Maxwell cue only if the visual story is:

```text
red Coulomb force on cantilever: leftward, away from +V
blue Maxwell attraction cue: rightward, toward +V, secondary
```

Reject and revert if the intended story is only a reference-style Maxwell cue without physical direction contrast.

- [ ] **Step 2: If keeping rightward Maxwell, document supersession**

Add this exact note near the Maxwell rows in `physics_sanity_inventory_v20.md` and `physics_sanity_contract_v20.md`:

```markdown
> v26 supersession note: v20 documented the reference-style Maxwell cue as leftward. v26 changes the rendered secondary Maxwell cue to rightward, toward the +V electrode, so it visually contrasts with the leftward Coulomb force on the cantilever. The cue remains secondary and report/visual-review territory; it is not a force-balance claim.
```

- [ ] **Step 3: Add v26 handback**

Create `experiments/python_svg_semantic_fig1/probe_visual_grammar_handback_v26.md`:

```markdown
# Fig1 Probe Visual Grammar Handback v26

## Scope

This pass is a panel-local visual grammar pass for the macroscopic probe panel. It improves force ownership, cantilever bend direction, support/contact depiction, material roles, and secondary Maxwell cue hierarchy without adding a new scaffold, new scientific content, or publication-grade approval.

## Implemented Boundary

- The red `ForceArrow` remains `force_target="cantilever"` and leftward.
- The blue `MaxwellAttractionCue` remains `secondary_reference_cue` and is rendered rightward toward the `+ V` electrode to contrast with the Coulomb repulsion story.
- The cantilever bends away from the `+ V` electrode.
- The ground/probe label clutter is removed.
- The clamp/support is softened into a support/contact depiction rather than a mechanical hinge.
- The trapped charges use one red charge-marker role.

## Not Claimed

- No new scaffold.
- No new semantic content.
- No force-balance claim.
- No new strict visual gate.
- No pixel tracing.
- Human visual review remains required before publication-grade approval.

## Review Prompts

- Inspect whether the support/contact reads as a cantilever support rather than a hinge or clamp.
- Inspect whether the red force vector has clear ownership without competing with charge markers.
- Inspect whether the blue Maxwell cue reads as secondary and does not imply the dominant force.
```

- [ ] **Step 4: Run targeted contract checks**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python -m unittest discover -s experiments/python_svg_semantic_fig1/src -p 'test_fig1_physics_sanity.py' -v
```

Expected:

```text
fig1 semantic contract passed
fig1 physics sanity passed
Ran 19 tests ... OK
```

Do not update baseline hash in this task.

---

### Task 2: Probe Layout Stabilization

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/fig1_l1_scene.py:245-323`
- Modify: `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py:1173-1334`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
- Generated: `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`

- [ ] **Step 1: Define probe grammar anchors before editing**

Use these anchors:

```text
support/contact lane: x ~= clamp.center.x
cantilever root: centered on support/contact lane
cantilever free end: left of root, not touching panel edge
red force vector lane: left of charge markers, not crossing the beam
blue Maxwell cue lane: between beam and electrode, smaller and lighter than red force
electrode: right-side vertical plate, not flush with card edge
callout: below device, not intersecting electrode
```

- [ ] **Step 2: Generate current probe crop**

Run:

```bash
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 519x470+1054+464 /tmp/fig1_panel_probe_current.png
open -a Preview /tmp/fig1_panel_probe_current.png
```

Expected: Preview opens the current probe crop.

- [ ] **Step 3: Fix only one of these if still visible**

Allowed single-pass fixes:

```text
if root is off-center: set root_x = clamp.center.x and align first beam control point to root_x
if support is too heavy: reduce back_plate opacity to 0.55 and clamp width to 22
if force label competes with charges: move label 10px left or 8px up, not both
if electrode is isolated: move field-line end points 15px closer to beam, not the electrode itself
```

- [ ] **Step 4: Render and inspect**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 519x470+1054+464 /tmp/fig1_panel_probe_after.png
open -a Preview /tmp/fig1_panel_probe_after.png
```

Expected: Preview opens updated probe crop.

- [ ] **Step 5: User checkpoint**

Ask:

```text
Probe OK for now, or one more probe-only adjustment?
```

If OK, proceed to Task 3. If not OK, allow one more probe-only adjustment. Stop probe after one more adjustment even if imperfect.

---

### Task 3: Electrical Evidence Mini-Plot Grammar

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
- Generated: `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`

- [ ] **Step 1: Define electrical grammar anchors before editing**

Use these anchors:

```text
two equal plot cells: P-E left, current decay right
P-E axis: compact cross-axis, loop centered, label P near y-axis, E near x-axis
P-E loop: red curve not touching panel title or conclusion
decay axis: x axis lower, y axis left, curve descends cleanly left-to-right
decay labels: one model label and one slope cue only
plot labels: above each cell, not competing with curve labels
bottom conclusion: one quiet sentence
```

- [ ] **Step 2: Generate electrical crop**

Run:

```bash
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 497x394+1076+30 /tmp/fig1_panel_electrical_current.png
open -a Preview /tmp/fig1_panel_electrical_current.png
```

- [ ] **Step 3: Identify the first electrical defect**

Pick exactly one:

```text
P-E loop too synthetic
current decay diagonal/axis awkward
label clutter
plot cells misbalanced
conclusion line too weak
```

- [ ] **Step 4: Patch one defect**

Patch only the renderer function for that mini-plot. Do not edit scene payload unless the visual grammar requires payload-owned coordinates.

- [ ] **Step 5: Render, crop, verify**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 497x394+1076+30 /tmp/fig1_panel_electrical_after.png
open -a Preview /tmp/fig1_panel_electrical_after.png
```

Expected:

```text
fig1 semantic contract passed
```

- [ ] **Step 6: User checkpoint**

Ask:

```text
Electrical OK for now, or one more electrical-only adjustment?
```

Allow at most two electrical cycles before moving on.

---

### Task 4: Hero Density and Caption Hierarchy

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
- Generated artifacts same as Task 3.

- [ ] **Step 1: Generate hero crop**

Run:

```bash
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 468x613+548+173 /tmp/fig1_panel_hero_current.png
open -a Preview /tmp/fig1_panel_hero_current.png
```

- [ ] **Step 2: Apply one hero adjustment only**

Choose one:

```text
quiet bottom caption by reducing box opacity and text size
move Et annotation away from DOS lobe if it competes
tighten shallow/deep state label ownership
reduce title/caption dominance if center model feels weak
```

- [ ] **Step 3: Render and inspect**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 468x613+548+173 /tmp/fig1_panel_hero_after.png
open -a Preview /tmp/fig1_panel_hero_after.png
```

Stop after one hero cycle unless the user calls out a concrete defect.

---

### Task 5: Interpretation Pipeline Cohesion

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
- Generated artifacts same as Task 3.

- [ ] **Step 1: Generate interpretation crop**

Run:

```bash
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 475x470+22+464 /tmp/fig1_panel_interpretation_current.png
open -a Preview /tmp/fig1_panel_interpretation_current.png
```

- [ ] **Step 2: Pick one pipeline defect**

Choose one:

```text
top causal boxes read like UI widgets
bottom plot and DOS feel detached
Debye bridge ownership unclear
tau_d label too isolated
conclusion card too heavy
```

- [ ] **Step 3: Patch one defect**

Do not change the causal payload sequence. Only adjust placement, line weight, or supporting visual connection.

- [ ] **Step 4: Render and inspect**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 475x470+22+464 /tmp/fig1_panel_interpretation_after.png
open -a Preview /tmp/fig1_panel_interpretation_after.png
```

Stop after one interpretation cycle unless the user calls out a concrete defect.

---

### Task 6: Origin Simplification

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
- Generated artifacts same as Task 3.

- [ ] **Step 1: Generate origin crop**

Run:

```bash
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 455x394+22+30 /tmp/fig1_panel_origin_current.png
open -a Preview /tmp/fig1_panel_origin_current.png
```

- [ ] **Step 2: Pick one origin defect**

Choose one:

```text
tiny S labels are noisy
bottom relation strip too cramped
heat/chain labels compete with chemistry glyphs
composition ramp dominates the card
```

- [ ] **Step 3: Patch one defect**

Do not remove `Heat 160 C` or `-Sx- chain` payload visibility. These are protected by `test_fig1_origin_payload_visibility.py`.

- [ ] **Step 4: Render and inspect**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 455x394+22+30 /tmp/fig1_panel_origin_after.png
open -a Preview /tmp/fig1_panel_origin_after.png
```

Stop after one origin cycle unless the user calls out a concrete defect.

---

### Task 7: Whole-Figure Visual Grammar Review

**Files:**

- Generated: `/tmp/fig1_panels_current_montage.png`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`

- [ ] **Step 1: Build crop montage**

Run:

```bash
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 455x394+22+30 /tmp/fig1_panel_origin.png
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 497x394+1076+30 /tmp/fig1_panel_electrical.png
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 468x613+548+173 /tmp/fig1_panel_hero.png
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 475x470+22+464 /tmp/fig1_panel_interpretation.png
magick experiments/python_svg_semantic_fig1/fig1_reference_semantic.png -crop 519x470+1054+464 /tmp/fig1_panel_probe.png
magick /tmp/fig1_panel_origin.png -background white -gravity north -extent 540x640 /tmp/fig1_panel_origin_ext.png
magick /tmp/fig1_panel_electrical.png -background white -gravity north -extent 540x640 /tmp/fig1_panel_electrical_ext.png
magick /tmp/fig1_panel_hero.png -background white -gravity north -extent 540x640 /tmp/fig1_panel_hero_ext.png
magick /tmp/fig1_panel_interpretation.png -background white -gravity north -extent 540x540 /tmp/fig1_panel_interpretation_ext.png
magick /tmp/fig1_panel_probe.png -background white -gravity north -extent 540x540 /tmp/fig1_panel_probe_ext.png
magick -size 540x540 xc:white /tmp/fig1_panel_blank_ext.png
magick /tmp/fig1_panel_origin_ext.png /tmp/fig1_panel_electrical_ext.png /tmp/fig1_panel_hero_ext.png +append /tmp/fig1_panels_row1.png
magick /tmp/fig1_panel_interpretation_ext.png /tmp/fig1_panel_probe_ext.png /tmp/fig1_panel_blank_ext.png +append /tmp/fig1_panels_row2.png
magick /tmp/fig1_panels_row1.png /tmp/fig1_panels_row2.png -append /tmp/fig1_panels_current_montage.png
open -a Preview /tmp/fig1_panels_current_montage.png
```

- [ ] **Step 2: Whole-figure checklist**

Inspect and mark each as YES/NO:

```text
Probe force story reads without explanation.
Electrical plots look like credible scientific schematics.
Hero is still the dominant semantic center.
Interpretation reads as one causal pipeline.
Origin supports the chemistry story without excessive tiny-label noise.
Red/blue/yellow/gray roles are consistent across panels.
No panel feels empty relative to the others.
No panel feels crowded relative to the others.
```

- [ ] **Step 3: Stop rule**

If two or more items are NO, do not commit as final visual polish. Either run one more targeted cycle on the worst panel or freeze the spike with a handback.

---

### Task 8: Accepted Checkpoint Finalization

**Files:**

- Modify: `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py`
- Modify: `experiments/python_svg_semantic_fig1/README.md`
- Modify: `experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`
- Generated: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
- Generated: `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`
- Generated: `experiments/python_svg_semantic_fig1/fig1_visual_judgment_report.md`

- [ ] **Step 1: Regenerate SVG/PNG/report**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/report_fig1_visual_judgment.py
```

- [ ] **Step 2: Compute new hash**

Run:

```bash
python - <<'PY'
from pathlib import Path
import hashlib
p = Path("experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg")
print(hashlib.sha256(p.read_bytes()).hexdigest())
PY
```

Patch `EXPECTED_HASH` in `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py` to that value.

- [ ] **Step 3: Update docs manifest if v26 handback is tracked**

Add `probe_visual_grammar_handback_v26.md` to `REQUIRED_MANIFEST_TOKENS` and add a concise `REQUIRED_V26_PROBE_VISUAL_GRAMMAR_TOKENS` tuple covering:

```text
ForceArrow
force_target="cantilever"
MaxwellAttractionCue
secondary_reference_cue
rightward toward the +V electrode
No new scaffold
No new semantic content
Human visual review remains required
```

- [ ] **Step 4: Run full verification**

Run:

```bash
python experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python -m unittest discover -s experiments/python_svg_semantic_fig1/src -p 'test_fig1_*.py' -v
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
python -m py_compile experiments/python_svg_semantic_fig1/src/fig1_l1_scene.py experiments/python_svg_semantic_fig1/src/render_fig1_l1.py experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
git status --short --branch
```

Expected:

```text
fig1 docs manifest passed
fig1 gates passed: 8/8
Ran 37 tests ... OK
```

- [ ] **Step 5: Stage only accepted files**

Run:

```bash
git add \
  experiments/python_svg_semantic_fig1/README.md \
  experiments/python_svg_semantic_fig1/probe_visual_grammar_handback_v26.md \
  experiments/python_svg_semantic_fig1/physics_sanity_inventory_v20.md \
  experiments/python_svg_semantic_fig1/physics_sanity_contract_v20.md \
  experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg \
  experiments/python_svg_semantic_fig1/fig1_reference_semantic.png \
  experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png \
  experiments/python_svg_semantic_fig1/fig1_visual_judgment_report.md \
  experiments/python_svg_semantic_fig1/src/fig1_l1_scene.py \
  experiments/python_svg_semantic_fig1/src/render_fig1_l1.py \
  experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py \
  experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py \
  experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py \
  experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py
```

Never stage:

```bash
experiments/python_svg_semantic_fig1/src/fig1_scene.py
experiments/python_svg_semantic_fig1/src/semantic_scene.py
.claude/
```

- [ ] **Step 6: Secret scan staged diff**

Run:

```bash
git diff --cached | rg -n "(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|password\\s*=|api[_-]?key\\s*=|secret\\s*=)" || true
```

Expected: no output.

- [ ] **Step 7: Commit**

Run:

```bash
git commit -m "SEMANTIC.fig1: refine probe visual grammar"
```

---

## Self-Review Checklist

- [ ] This plan does not add a new gate.
- [ ] This plan does not add a new vision critique layer.
- [ ] This plan does not start a TikZ prototype.
- [ ] This plan keeps user visual review as the subjective approval gate.
- [ ] This plan explicitly protects the two legacy dirty files.
- [ ] This plan reconciles Maxwell cue direction before any final commit.
- [ ] This plan delays baseline hash update until visual acceptance.
- [ ] This plan stops each panel after bounded cycles.
