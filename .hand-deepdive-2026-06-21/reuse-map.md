I now have a complete picture. Here is the reuse map.

---

# REUSE MAP — figure-agent SVG/critique/style/polish → new Illustrator's Hand (piece #3)

## (1) What the current SVG pipeline actually does

The pipeline is **TikZ-as-truth**: an LLM authors `.tex`, compiles to PDF, exports to SVG. SVG is treated as a frozen, late-stage *export* — never the source. Five subsystems wrap it:

**A. SVG polish recipe + executor** (`svg_polish_recipe.py`, `svg_polish_executor.py`). A declarative YAML recipe lists `operations`, each with a `selector` (`element_id` / `css_class` / `text_exact`), an `action`, a `rationale`, and a `semantic_guard{allowed,reason}`. Only **5 action types** exist: `translate`, `set_stroke_width`, `set_opacity`, `set_fill_opacity`, `set_stroke_opacity`. The executor enforces hard bounds: translate ≤ **10px** per component, stroke-width ratio in **[0.5, 2.0]**, opacity in [0,1], `element_id`/`text_exact` must match exactly one node, `css_class` ≤ 5. This is deliberately a *nudge* engine, not a draw engine — it cannot create geometry, only micro-adjust existing nodes. Output goes to `polish/<name>.polished.svg` (source under `exports/` is immutable).

**B. 8 edit classes** (`svg_polish_manifest.py`, `ALLOWED_EDIT_CLASSES`): `label_micro_position`, `leader_line_micro_position`, `stroke_polish`, `icon_detail`, `spacing_balance`, `color_opacity_polish`, `typography_cleanup`, `export_cleanup`. The manifest is a freshness/provenance ledger (input hashes, editor ∈ {human, external_tool, agent_assisted}, toolchain, reviewer) gating promotion to `final_artifact`.

**C. Semantic diff guard** (`svg_semantic_diff.py`) — the structural truth-lock. Builds an XML *inventory* (texts, ids, classes, frame/viewBox, path/marker counts, per-id color+opacity, transforms) of source vs. polished and emits findings: `text_identity_loss` (BLOCKER), `frame_change`, `unsupported_svg_feature` (filter/mask/clipPath/foreignObject/image), `group_transform_risk`, `marker_or_path_change`, `element_inventory_change`, `semantic_color_remap`. Any BLOCKER/MAJOR → `semantic_backport_required` (blocks promotion). Mirrors the executor's 10px translate bound so sanctioned nudges pass while rotate/scale/matrix/oversized translates fail.

**D. Critique loop** (`critique_*.py`, ~85k-line lint). Vision critique runs *in the host Claude session* (no API keys), writing structured `critique.md` frontmatter with findings, quality-axis verdicts, journal-grade scoring, micro-defect inventory, and aesthetic/editorial audits. This is the eye.

**E. Collision/geometry** (`check_collisions.py`, `check_undeclared_geometry.py`, `check_label_path_proximity.py`). Operate on **PDF/TikZ coordinates** via `pdftotext -bbox` IoU and TikZ command parsing — detect label overlaps and undeclared rects/rules crossing labels (`label_crosses_rect_boundary`, `label_endpoint_near_miss`, etc.).

**Style Lock** = `styles/polymer-paper-preamble.sty`: a frozen LaTeX preamble (Arial, Paul Tol Muted palette, pgfplots tick density). It is **TikZ-only** — a `.sty` file consumed by lualatex.

## (2) Reusable vs. TikZ-era dead end

**REUSE (port directly):**
- **Whole critique loop (E5)** — schema, signal vocabulary, host-session vision review, micro-defect/aesthetic audits. This *is* piece #5; the Hand consumes its routes. Reuse verbatim.
- **`svg_semantic_diff.py` inventory+finding engine** — already pure-SVG, already the "structural truth-lock." This is the seed of piece #6 (accuracy lock). The Hand's invariant: text identity, frame, element inventory, color-by-id must survive every edit.
- **Recipe pattern**: declarative op = `{selector, action, rationale, semantic_guard}` with dry-run plan + bounded execution. Reuse the *contract shape*; the Hand widens the action set.
- **Manifest provenance/freshness ledger** — becomes the version-controlled decision log (reproducibility = SVG + log, not pixel-lock). Reuse.
- **8 edit classes + severity/route vocabulary** — reuse as the Hand's edit taxonomy, extended.

**TikZ-era DEAD END (do not carry):**
- **Style Lock as `.sty`** — replace with an SVG style token system (piece #4 asset library). The *concept* (locked palette/typography/weights) survives; the LaTeX mechanism dies.
- **`check_collisions.py` / `check_undeclared_geometry.py`** operating on PDF bboxes + TikZ command strings — must be **rewritten native-SVG** (bbox from SVG geometry, not `pdftotext`). The IoU/proximity *logic* reuses; the PDF/TikZ I/O is dead.
- **The 10px / [0.5,2.0] nudge ceilings** — these exist because TikZ owns geometry and SVG may only micro-correct export drift. For SVG-native, the Hand *is* the illustrator: it needs real Bezier/path authoring, gradients, organic curves. Keep bounds **only** on accuracy-locked structural nodes; lift them for aesthetic-freedom layers (decoration, fills, freeform strokes drawn *on top of* truth).
- **`compile.sh` / lualatex / PDF export chain** — entirely dead; SVG is now the source.

## (3) Critique signal vocabulary — VERBATIM (from `critique_schema_vocab.py`)

Map new Hand signals onto these. Sources gaps A (aesthetic finish), B (organic curves), D (composition):

- `FINDING_SEVERITIES = {BLOCKER, MAJOR, MINOR, NIT}`
- `QUALITY_AXIS_NAMES = (message_storyline, panel_role_coherence, subregion_integration, component_fidelity, scientific_plausibility, composition_layout, label_annotation_semantics, journal_polish, reference_fidelity, publication_readiness)`
- `QUALITY_VERDICTS = {pass, needs_patch, needs_human, block, not_applicable}`; `QUALITY_ACTIONS = {none, patch, human_review, revise_briefing, block_release}`
- `PANEL_ROLES = {setup, mechanism, result, comparison, control, zoom, model, workflow, context}`; `PANEL_ROLE_QUALITIES = {clear, weak, missing, redundant}`
- `AESTHETIC_GATE_SLOTS = (maturity_restraint, visual_hierarchy, template_genericness, overdecorated_or_cartoonish, journal_fit, handcrafted_finish, semantic_preservation, print_scale_finish, paper_wide_coherence)`
- `AESTHETIC_ANTIPATTERN_IDS = (childish_shape_language, poster_gradient_decoration, generic_template_look, dead_flat_vector_finish, uniform_line_weight_monotony, weak_hero_anchor, cramped_or_dead_whitespace, low_authority_typography, annotation_noise_competes_with_science, panel_style_mismatch, reference_overcopying, reference_underlearning, decorative_detail_without_explanatory_value)`
- `AESTHETIC_LEVER_DIMENSIONS = {maturity, hero_hierarchy, whitespace_breathing, typography_authority, color_harmony, line_weight_rhythm, component_fidelity, hand_craft, cross_panel_grammar, polish_route}`
- `AESTHETIC_GATE_ROUTES = {pass, tikz_patch, svg_polish, semantic_backport, needs_human_art_direction, accept_simplification}`
- `EDITORIAL_POLISH_PATHS = {continue_tikz, ready_for_svg_polish, needs_human_art_direction, semantic_backport_required}`
- `SVG_DELTA_EVALUATION_STATES = {improved, no_meaningful_change, regressed, needs_human_art_direction, invalid}`; `SVG_DELTA_REGRESSION_CATEGORIES = {semantic_drift, label_readability, crop_regression, print_scale_regression, overdecorated, journal_mismatch}`; `SVG_DELTA_ROUTES = {continue_svg_polish, accept_svg_polish, semantic_backport_required, needs_human_art_direction}`
- `MICRO_DEFECT_KINDS = {line_crosses_label, wire_crosses_label, arrow_tip_fused, label_target_detached, floating_semantic_cue, drawing_order_suspect, print_scale_unreadable, label_backdrop_overflows_outline, label_glyph_overlaps_internal_drawing, label_crosses_panel_boundary, label_crosses_column_rule, label_overflows_row_box, label_stacked_on_reference_line, label_curve_near_label, label_path_near_miss}`
- Semantic-diff finding kinds: `{text_identity_loss, element_inventory_change, frame_change, unsupported_svg_feature, group_transform_risk, marker_or_path_change, semantic_color_remap}`

## Hand-engine design implications

The new routes `tikz_patch` / `continue_tikz` become **dead enum members** — the Hand replaces them with native-SVG draw ops. The aesthetic vocabulary (gate slots, antipatterns, lever dimensions) is exactly the A/B/D gap map: `handcrafted_finish` + `dead_flat_vector_finish` + `uniform_line_weight_monotony` → gap A; `childish_shape_language` (organic-curve quality) → gap B; `visual_hierarchy` + `weak_hero_anchor` + `whitespace_breathing` + `cross_panel_grammar` → gap D. The Hand should emit edits keyed to these signals and route each through `svg_semantic_diff` (the immutable structural guard) before write. The two-layer split is the core architecture: **accuracy-locked structural nodes** (10px-style bounds, full inventory invariance) vs. **aesthetic-freedom layers drawn on top** (unbounded Bezier/gradient/organic authoring). `C=WYSIWYG-drag` has no footprint here — nothing in the existing pipeline is an editing UI, so excluding it costs nothing.

**Key file paths (all under `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/`):** `scripts/svg_polish_recipe.py`, `scripts/svg_polish_executor.py`, `scripts/svg_polish_manifest.py`, `scripts/svg_semantic_diff.py`, `scripts/critique_schema_vocab.py`, `scripts/critique_contract.py`, `scripts/check_collisions.py`, `scripts/check_undeclared_geometry.py`, `scripts/check_label_path_proximity.py`, `styles/polymer-paper-preamble.sty`.