# Issue 100L - Paper-Wide Context Template

Status: implemented

Type: paper-wide aesthetic context, operator workflow, starter template

## Problem

The plugin already supports explicit paper-wide aesthetic context through
`examples/_paper_aesthetic_contexts/<paper_id>.yaml` and
`spec.yaml.paper_aesthetic_context`, but starting a new paper context required
manual copying from catalog examples. That made the paper-wide coherence route
feel less first-class than reference packs, SVG polish recipes, external review,
and sub-region logs.

## Decision

Add a provider-free local starter template to the existing
`paper_aesthetic_context.py` validator. The command creates only the paper-wide
pack. It does not modify fixture `spec.yaml`, source, critique, export, accepted,
golden, SVG, or publication state.

## Implemented Contract

Added:

```bash
uv run python3 scripts/paper_aesthetic_context.py \
  --template <paper_id> \
  --fixture <fixture_name> \
  --write-template
```

The helper:

- writes `examples/_paper_aesthetic_contexts/<paper_id>.yaml`;
- validates the emitted YAML through the existing v1 pack loader;
- includes one `figure_roles[]` entry for the named fixture;
- refuses overwrite unless `--force` is passed;
- prints reloadable YAML when `--write-template` is omitted;
- keeps fixture opt-in explicit: the operator still chooses when to add
  `spec.yaml.paper_aesthetic_context`.

## Non-Goals

- Do not infer paper-wide style from existing figures.
- Do not auto-edit `spec.yaml`.
- Do not make paper-wide context mandatory.
- Do not turn paper-wide taste into a release gate.
- Do not copy a reference image or catalog pack into a fixture silently.

## Tests

Covered in `tests/test_paper_aesthetic_context.py`:

- generated template loads through the existing validator;
- generated `figure_roles[]` matches the requested fixture;
- overwrite is refused without `--force`;
- CLI `--write-template` writes a reloadable pack.

## Review Notes

### Review 1 - Contract Safety

The starter is pack-only and opt-in. It does not make old critiques stale until
the user explicitly wires the pack into a fixture spec.

### Review 2 - Architecture Fit

The template uses the existing v1 schema and validator. No new schema version is
needed because semantics are unchanged.

### Review 3 - Operator Utility

The paper-wide route now has the same starter ergonomics as reference-learning
packs, SVG polish recipes, external review evidence, and sub-region logs.
