# Python SVG Style Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify one Python-generated SVG stress figure that proves or falsifies the style/texture/pseudo-3D capability claim.

**Architecture:** Keep this as a standalone experiment under `experiments/python_svg_style_capability/`. Reuse the previous spike's dvisvgm and nested-SVG cleanup patterns, but add SVG-native primitives for gradients, filters, patterns, masks, and pseudo-3D geometry.

**Tech Stack:** Python, drawsvg, matplotlib, numpy, pdflatex, dvisvgm, rsvg-convert.

---

### Task 1: Capability Contract

**Files:**
- Create: `experiments/python_svg_style_capability/capability_matrix.md`
- Create: `experiments/python_svg_style_capability/friction_log.md`
- Create: `experiments/python_svg_style_capability/time_log.md`

- [ ] **Step 1: Write the expected capability rows**

Record rows for gradients, filters, patterns, masks/clips, pseudo-3D geometry, matplotlib SVG nesting, and dvisvgm math labels.

- [ ] **Step 2: Record setup start**

Add a UTC timestamp and the branch name to `time_log.md`.

### Task 2: Helper Layer

**Files:**
- Create: `experiments/python_svg_style_capability/src/stack/drawsvg_helpers.py`
- Create: `experiments/python_svg_style_capability/src/stack/dvisvgm_math.py`

- [ ] **Step 1: Copy the deterministic helper responsibilities**

Include text helpers, nested SVG cleanup, id prefixing, SVG save, and dvisvgm math embedding.

- [ ] **Step 2: Add style primitives**

Add small helpers for rounded cards, arrows, shaded isometric boxes, hatching, and procedural dot/line textures.

### Task 3: Stress Figure

**Files:**
- Create: `experiments/python_svg_style_capability/src/style_capability.py`
- Create: `experiments/python_svg_style_capability/style_capability.svg`
- Create: `experiments/python_svg_style_capability/style_capability.png`

- [ ] **Step 1: Build the Python figure**

Create a six-panel figure covering material beam texture, isometric device stack, trap-energy surface, plot/schematic fusion, texture swatches, and print-readiness checks.

- [ ] **Step 2: Generate SVG**

Run `uv run --with drawsvg --with matplotlib --with numpy python experiments/python_svg_style_capability/src/style_capability.py`.

- [ ] **Step 3: Render PNG**

Run `rsvg-convert -w 1780 -h 1000 experiments/python_svg_style_capability/style_capability.svg -o experiments/python_svg_style_capability/style_capability.png`.

### Task 4: Verification And Handback

**Files:**
- Create: `experiments/python_svg_style_capability/feasibility_handback.md`
- Modify: `experiments/python_svg_style_capability/capability_matrix.md`
- Modify: `experiments/python_svg_style_capability/friction_log.md`
- Modify: `experiments/python_svg_style_capability/time_log.md`

- [ ] **Step 1: Verify XML parse**

Run `python -m xml.etree.ElementTree experiments/python_svg_style_capability/style_capability.svg`.

- [ ] **Step 2: Verify capability evidence**

Search the SVG for `linearGradient`, `radialGradient`, `filter`, `clipPath`, `mask`, `pattern`, nested `svg`, and dvisvgm path content.

- [ ] **Step 3: Write handback**

Summarize pass/fail evidence and state whether Python-first is viable as the main visual design layer.

- [ ] **Step 4: Commit**

Commit the spec, plan, experiment sources, generated SVG/PNG, and logs on `experiment/python-svg-style-capability`.
