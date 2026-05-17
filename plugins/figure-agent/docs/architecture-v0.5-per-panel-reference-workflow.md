# Architecture v0.5 — Per-Panel Reference Workflow (D-2)

**Status:** DRAFT (2026-05-08) — handoff to Codex session for implementation
**Predecessor:** `architecture-v0.4.2-perception-data-only.md` (companion D-1, ships first).
**Drives from:** `feedback_perception_spec_rejected.md`, `feedback_reference_dilemma_hybrid.md`, `feedback_element_iteration_workflow.md`, `project_v0_2_critique_reference_grounding.md`.
**Scope owner:** Codex session (implementation), not this session.

---

## 1. Problem Statement

This session converged on an empirical finding: across vision tier-sense, macro swap, perception pack v0.4, and v0.4.1, every "more sophisticated AI" attempt collapsed to "user must judge". The user's actual workflow is:

1. User generates (or hand-picks) a per-panel **reference image** of how that panel should look (image-gen, mockup, paper figure crop, sketch, etc.).
2. AI reproduces the panel in TikZ as faithfully as feasible.
3. User iterates element-by-element (`feedback_element_iteration_workflow.md`).

`figure-agent` already has a figure-level `reference_image` field (`spec.yaml.reference_image`), used by Layer 2.5 (`/fig_extract`) and `/fig_critique`. But the granularity is wrong for multi-panel figures — a single full-figure reference at the top forces `/fig_critique` to compare 7 panels against 1 reference, dilutes per-panel intent, and doesn't survive when the user wants to swap one panel's reference without touching the others.

v0.5 lifts the `reference_image` field to per-panel granularity: `spec.yaml.panels[i].reference_image`. `/fig_critique` then compares each panel's build crop against its own reference.

## 2. Non-Goals

- ❌ Auto-cropping panels from the build PDF without coordinate hints.
- ❌ Image-gen orchestration (host or external image-gen tools produce the references; plugin only consumes them).
- ❌ Reference-vs-build pixel-diff metrics. v0.5 ships qualitative LLM critique only.
- ❌ Multi-reference compose (`feedback_reference_dilemma_hybrid.md` says 2-3 references compose better than 1, but v0.5 ships the 1-per-panel case first; multi-ref is a v0.5.1+ extension).

## 3. Schema additions

### 3.1 spec.yaml — panels[i].reference_image (optional)

Existing schema (e.g., `examples/golden_trap_depth_picture/spec.yaml`):

```yaml
panels:
  - id: row1
    caption: Experiment to discharge reference
```

v0.5 adds:

```yaml
panels:
  - id: row1
    caption: Experiment to discharge reference
    reference_image: reference/panel_row1_ref.png   # NEW — optional, path relative to figure folder
    bbox_pdf_cm: [x0, y0, x1, y1]                    # NEW — optional, for crop region
```

**Compatibility:**
- Per-panel critique requires both `panels[i].reference_image` and `panels[i].bbox_pdf_cm`.
- If either field is absent, `/fig_critique` skips that panel-level comparison and emits a WARN in the generated brief.
- If a participating reference is declared but the file is missing
  (`spec.yaml.reference_image`, or `panels[i].reference_image` together with
  `panels[i].bbox_pdf_cm`), treat it as configuration error; fix the path or
  add the file before critique/export.
- There is no figure-level-reference fallback for panel crops: comparing a panel crop to a full-figure reference is scale-mismatched and produces noisy findings.

**Coordinate convention:** PDF cm, top-left origin, y-down. Computed correctly: `cm_per_source = (\resizebox width in cm) / (source canvas width in cm)`; `origin_offset = border_pt × 2.54 / 72`. **Do NOT make the user compute these manually** (Gemini v0.4.1 review #4 was right). Provide a helper:

### 3.2 Helper: bbox author tool

New script: `scripts/spec_bbox_helper.py` (or skill).

Usage:
```
uv run python -m figure_agent.scripts.spec_bbox_helper <name>
```

Behavior:
1. Reads `examples/<name>/<name>.tex` and parses `\resizebox{<W>}{!}{...}`, document `border=<X>pt`, and `tikzpicture` canvas dimensions.
2. Prompts the user (or accepts a flag) to pick panel boundaries in **source-cm coordinates** (e.g., "Panel A: x=[0,4.5] y=[5,9]").
3. Converts to PDF cm and prints the `bbox_pdf_cm` line ready to paste.

This addresses Gemini v0.4.1 #4: shifting cm-conversion math to the user is unreasonable. The plugin owns the math; the user only declares panels in their own working coordinates.

## 4. /fig_critique changes

`/fig_critique` already loads `reference_image` for figure-level comparison. v0.5 extends:

1. For each panel `p` in `spec.yaml.panels`:
   - If `p.reference_image` exists: load it.
   - If `p.bbox_pdf_cm` exists: crop `build/<name>.png` using the bbox (PIL crop after pixel scaling from the page cm).
   - If both: pass both `(panel_crop, panel_reference)` pair to host LLM with prompt: "Compare panel `<id>`'s build crop to its reference. Note structural/topological deviations. Style is locked elsewhere."
2. After all panel-level comparisons: a final figure-level pass (existing behavior) for cross-panel consistency.

`critique.md` schema gains a `panels:` section:
```yaml
panels:
  - id: row1
    findings:
      - severity: major
        category: structural
        message: "Reference shows 4 chains attached to ring; build shows 6 dangling."
        ...
findings:                       # figure-level (existing)
  - ...
```

## 5. /fig_extract changes (Layer 2.5)

Existing `/fig_extract` runs OCR + palette clustering on `spec.yaml.reference_image` (figure-level). v0.5 extends:
- If panel-level `reference_image` is present, run `/fig_extract` per-panel as well, writing `coordinate_hints.yaml` entries scoped to each panel.
- Backward compatible: figure-level reference still processed if present and no panel-level overrides.

This step is **optional** — v0.5 MVP can ship without `/fig_extract` per-panel and add it later. The bbox helper (§3.2) and `/fig_critique` per-panel comparison are the minimum viable surface.

## 6. Acceptance criteria

1. `uv run pytest` continues to pass.
2. Adding `panels[i].reference_image` + `panels[i].bbox_pdf_cm` to a fixture's spec.yaml triggers per-panel critique.
3. Absence of either field emits a WARN and skips that panel-level comparison; a declared-but-missing participating reference file fails closed.
4. `scripts/spec_bbox_helper.py` correctly converts source-cm to pdf-cm using the .tex's actual resizebox + border (sanity check: fig1_overview_v2 should give `cm_per_source ≈ 1.271` and `origin ≈ [0.141, 0.141]`).
5. critique.md gains a `panels:` array with at least one finding per panel that has reference_image+bbox.
6. Documentation updated:
   - `skills/figure-agent/SKILL.md` — note panel-level reference workflow.
   - `commands/fig_new.md` — interview optionally collects panel-level references.

## 7. Workflow integration

User flow with v0.5:

```
1. /fig_new <name>           # scaffold
2. (user generates panel-level reference images via image-gen or hand-picks)
3. (user adds panels[i].reference_image to spec.yaml)
4. uv run python -m figure_agent.scripts.spec_bbox_helper <name>   # get bbox lines
5. (user pastes bbox_pdf_cm lines)
6. (user authors / iterates .tex)
7. /fig_compile <name>       # produces PDF + perception pack (v0.4.2)
8. /fig_critique <name>      # per-panel reference grounding (this spec)
9. (iterate: read critique.md panel findings, edit one element, recompile)
```

## 8. Codex session implementation notes

- Schema migration: add fields to spec.yaml with defaults that preserve current behavior. Update any spec validation in `scripts/parse_spec.py` (or wherever).
- `scripts/critique_brief.py` already passes the figure-level reference to host LLM; extend to pass per-panel pairs as separate context blocks.
- `scripts/spec_bbox_helper.py` new. Tex parsing can use a simple regex on `\resizebox` and `geometry{... border=...pt}`; if those macros are abstracted, fall back to a YAML override (`spec.yaml.coordinate_space:` block).
- Tests: extend `tests/test_critique_brief.py` to assert per-panel context appears when `panels[i].reference_image` is set; add `tests/test_spec_bbox_helper.py` for the cm-conversion math.
- `examples/fig1_overview_v2/` is a natural test fixture — already has multi-panel structure that needs reference grounding.

## 9. Out-of-scope follow-ups

- v0.5.1: multi-reference per panel (compose 2-3 refs as style anchors per `feedback_reference_dilemma_hybrid.md`).
- v0.5.2: integrate v0.4.2 perception pack data into per-panel critique prompt (e.g., "this panel has 12 line endpoints and 8 curves; reference shows ~6 endpoints expected").
- v0.6+: image-gen orchestration as a separate optional skill (`/fig_gen_panel_ref` invokes external image-gen via host).

## 10. Lessons folded in

- `feedback_element_iteration_workflow.md` — element-iteration is the real cycle; per-panel reference makes element scope visible.
- `feedback_reference_dilemma_hybrid.md` — single-ref locks in copy; v0.5 ships single-ref but v0.5.1 path is acknowledged.
- `feedback_subregion_iteration_unit.md` — sub-regions (5-8 per panel) are the real unit; v0.5 panels are intermediate granularity, sub-region-level handling deferred.
- `project_v0_2_critique_reference_grounding.md` — N=3 dogfood already showed reference grounding is the lever for `/fig_critique` accuracy.
- `feedback_perception_spec_rejected.md` — auto-detection without reference is taste-blind; v0.5 makes the user's reference the ground truth.
