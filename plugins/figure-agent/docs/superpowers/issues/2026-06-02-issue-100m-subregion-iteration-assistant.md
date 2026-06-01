# Issue 100M - Subregion Iteration Assistant

Status: implemented

Type: operator workflow, long-loop evidence, sub-region iteration

## Problem

Sub-region iteration is one of the most useful real workflows for improving a
figure: patch one small visual/semantic unit, compile, inspect, record the
result, then repeat. The plugin already parses `subregion_iteration_log.md` when
it exists and can route `/fig_loop` to an active sub-region target.

The remaining gap was startability and consistency. Operators had to hand-author
the Markdown log shape, and long sessions could omit iteration rows or drift into
inconsistent table formats.

## Decision

Keep the existing text-form contract. Do not add a spec.yaml sub-region schema,
auto-segmentation, sub-region bbox cropper, or hidden source patcher.

Add a small local helper that scaffolds the canonical Markdown log and appends
one iteration row at a time while preserving compatibility with
`scripts/subregion_active_set.py`.

## Implemented Contract

Added:

```bash
uv run python3 scripts/subregion_iteration_log.py --template examples/<name> --write-template
uv run python3 scripts/subregion_iteration_log.py --append examples/<name> \
  --iteration iter-001 \
  --subregion-id D-1 \
  --problem "label hierarchy too flat" \
  --patch-summary "raised label and tightened arrow" \
  --result improved \
  --follow-up "recheck print crop"
```

The helper:

- writes `examples/<name>/subregion_iteration_log.md`;
- refuses to overwrite an existing log unless `--force` is passed;
- emits the existing `## Active Target Set` and `## Iteration Log` tables;
- appends exactly one iteration row per call;
- escapes Markdown table pipes in user-provided text;
- never edits `.tex`, critique, adjudication, build, export, accepted, golden,
  SVG polish, or publication files.

## Non-Goals

- Do not infer sub-region boundaries from images.
- Do not create a schema-level sub-region model.
- Do not generate sub-region crops.
- Do not synthesize patches.
- Do not replay old iteration rows as commands.

## Tests

Covered in `tests/test_subregion_iteration_log.py`:

- starter template is parseable by the existing active-set parser;
- template write refuses overwrite without `--force`;
- append preserves parseable iteration patch ids;
- CLI write-template plus append is reloadable.

## Review Notes

### Review 1 - Scope Containment

The helper only creates or appends the evidence log. It does not broaden
automation or touch figure source.

### Review 2 - Contract Compatibility

The emitted Markdown uses the exact section/table names already consumed by
`subregion_active_set.py`, `critique_brief.py`, and `fig_loop`.

### Review 3 - Operator Utility

The command removes a manual setup step from the loop while preserving the
author's role in naming the active sub-region and assessing the result.
