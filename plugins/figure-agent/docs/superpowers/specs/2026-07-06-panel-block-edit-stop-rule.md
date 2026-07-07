# Panel-block edit stop rule

Applies to the quality-search Panel-F post families (`scripts/quality/quality_search.py`).

A human-observed element iteration on an **existing** panel is a **data entry**, not
a new Python function. Add it to `scripts/quality/panel_block_edits.yaml`
(`family_id`, `template_id`, `panel`, `requires`, `applied_signature`,
`preserve_after`, `replacements`, `protected_labels`, `goal_trigger`,
`goal_hypothesis`). The generic family in `quality_search.py`
(`_panel_block_edit_replacement`) and its loader (`scripts/quality/panel_block_edits.py`)
consume it; no dispatch/goal-branch/test wiring is required.

A **new Python family** is justified only by a new *edit mechanic* — a
capability the parametric `replace_block` family cannot express (e.g. a new
operation kind, a geometry-computed edit, a non-`replace_text` transform). New
coordinates, colours, or label prose are **never** a new mechanic; they are data.

Rationale: one bespoke function per observed defect (~150-225 LOC + a mirror
test each, each used exactly once) drove `quality_search.py` toward 10.7k LOC
with the marginal cost of an iteration rising. Data entries hold the marginal
cost flat.
