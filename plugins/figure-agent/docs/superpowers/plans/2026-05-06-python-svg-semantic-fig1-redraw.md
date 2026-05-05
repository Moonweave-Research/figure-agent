# Python SVG Semantic Fig1 Redraw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a semantic scene representation for the Fig 1 reference PNG and render it to SVG/PNG using Python.

**Architecture:** Keep the semantic data model separate from the renderer. `semantic_scene.py` defines typed objects, `fig1_scene.py` builds the target scene, and `render_semantic_fig1.py` converts semantic objects into SVG.

**Tech Stack:** Python dataclasses, drawsvg, matplotlib, numpy, pdflatex, dvisvgm, rsvg-convert.

---

### Task 1: Semantic Contract

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/verify_semantic_scene.py`
- Create: `experiments/python_svg_semantic_fig1/capability_log.md`

- [ ] Write a verifier that imports `fig1_scene.build_scene()` and checks required object ids, role names, and key assertions.
- [ ] Run it before implementation and confirm it fails because `fig1_scene` does not exist.

### Task 2: Scene Model

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/semantic_scene.py`
- Create: `experiments/python_svg_semantic_fig1/src/fig1_scene.py`

- [ ] Define dataclasses for scene, panels, semantic objects, labels, and assertions.
- [ ] Build the Fig 1 scene with all required semantic object ids.
- [ ] Run the semantic verifier and confirm it passes.

### Task 3: Renderer

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/render_semantic_fig1.py`
- Create: `experiments/python_svg_semantic_fig1/src/stack/drawsvg_helpers.py`
- Create: `experiments/python_svg_semantic_fig1/src/stack/dvisvgm_math.py`
- Create: `experiments/python_svg_semantic_fig1/semantic_fig1.svg`
- Create: `experiments/python_svg_semantic_fig1/semantic_fig1.png`

- [ ] Implement reusable drawing helpers.
- [ ] Render each semantic object into the source-like layout.
- [ ] Generate SVG and PNG.

### Task 4: Verification And Handback

**Files:**
- Create: `experiments/python_svg_semantic_fig1/feasibility_handback.md`
- Modify: `experiments/python_svg_semantic_fig1/capability_log.md`

- [ ] Verify XML parsing.
- [ ] Verify scene contract.
- [ ] Verify deterministic SVG regeneration.
- [ ] Render PNG preview.
- [ ] Commit experiment artifacts.
