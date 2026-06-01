# Issue 99 - Auto-Detected Label-Frame Boundary Clash

Status: implemented

## Problem

`figure-agent` can currently miss a label whose rendered glyph bbox is crossed
by a panel frame, horizontal rule, or column rule when that boundary was not
declared in `spec.yaml.text_boundary_checks`.

The concrete dogfood failure was a Row-2 frame border crossing the lower part
of axis/category labels in `fig1_overview_v2_pair_001_vault`. The existing
allowlist-based text-boundary checker did not run because no explicit
`text_boundary_check` described that border. The undeclared-geometry checker
already discovers the frame/rule geometry, but it does not emit a distinct
candidate when the discovered geometry crosses text.

## Root Cause

The pipeline has two separate signals:

- PDF text bboxes from `check_visual_clash.extract_pdf_words_and_page()`;
- TeX-derived rectangles and line segments from `check_undeclared_geometry.py`.

No checker currently performs the cross-product:

```text
auto-discovered frame/rule geometry x rendered text bbox
```

`check_undeclared_geometry.py` also intentionally filters near-miss candidates
with `0 < distance <= near_miss_pt`, so a true intersection with distance `0`
does not become a label-near-boundary candidate.

## Decision

Use the existing `UG###` undeclared-geometry report rather than adding a new
`LF###` report.

Add new `check_undeclared_geometry.py` candidate kinds:

- `label_crosses_rect_boundary`
- `label_crosses_horizontal_rule`
- `label_crosses_column_rule`

The candidates must:

- be generated from rendered PDF frame/rule geometry plus PDF text bboxes;
- require a real line/bbox intersection, not merely an aesthetic near miss;
- carry the existing `undeclared_geometry_ref` path through `/fig_critique`;
- preserve current `undeclared_rect_boundary`, `undeclared_horizontal_rule`,
  `undeclared_column_rule`, and near-miss behavior.

Implementation note: source-derived TikZ coordinates do not include the final
PDF x/y placement offsets, so exact crossing candidates are emitted from
`pdfplumber` rendered path coordinates. Source-derived geometry still supplies
the existing `undeclared_*` and near-miss candidates.

## Scope

In scope:

- `scripts/check_undeclared_geometry.py`;
- focused unit tests for the geometric detection;
- brief/test adjustments only if the existing undeclared-geometry brief section
  does not surface the new candidate kinds clearly enough.

Out of scope:

- editing fixture TeX, critique, adjudication, spec, exports, accepted, or
  golden state;
- adding a new report namespace;
- making undeclared-geometry accounting mandatory in `audit_evidence_summary.py`
  in this slice;
- weakening existing visual/text/label-path checks.

## Acceptance

- A synthetic horizontal frame/rule crossing a text bbox emits exactly one
  `label_crosses_horizontal_rule` candidate.
- A synthetic label that clears the border emits no crossing candidate.
- Rect frame borders are decomposed into sides and can emit a
  `label_crosses_rect_boundary` candidate.
- Current fixed `fig1_overview_v2_pair_001_vault` emits no new
  `label_crosses_*` candidates.
- Strict mode continues to fail on any undeclared-geometry candidate because
  this remains part of `check_undeclared_geometry.py`.

## Verification

- `uv run pytest -q tests/test_undeclared_geometry.py tests/test_critique_brief.py::test_critique_brief_includes_undeclared_geometry_candidates`
- `uv run python3 scripts/check_undeclared_geometry.py examples/fig1_overview_v2_pair_001_vault/build/fig1_overview_v2_pair_001_vault.pdf --tex examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex --spec examples/fig1_overview_v2_pair_001_vault/spec.yaml --json-output /tmp/fig1_issue99_undeclared_geometry.json`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
