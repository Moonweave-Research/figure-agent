# Checker Report to Benchmark Detector Adapter Design

Status: draft for implementation
Date: 2026-06-09
Owner: figure-agent
Parent spec: `2026-06-09-render-derived-detector-dogfood-promotion-design.md`

## Summary

The benchmark detector preview workflow exists, but dogfood currently reports
`metric_missing` for `fig1_overview_v2_pair_001_vault` because its detector
input is an existing checker report:

```text
examples/fig1_overview_v2_pair_001_vault/build/text_boundary_clash.json
```

That report has checker-native fields:

```json
{
  "schema": "figure-agent.text-boundary-clash.v1",
  "candidates": [],
  "total": 0
}
```

It does not have the benchmark metric shape:

```json
{
  "metrics": {
    "text_boundary.blocker_count": {
      "baseline": 0,
      "candidate": 0
    }
  }
}
```

This slice adds a read-only adapter from checker-native reports to benchmark
detector reports.

## Goals

- Convert existing checker `total` counts into explicit benchmark metrics.
- Make dogfood benchmark detector preview return `available` for supported
  existing checker reports.
- Preserve the current seed-report path for smoke fixtures.
- Avoid inventing improvement: when no candidate artifact is present, set
  `baseline == candidate == total`.
- Keep write behavior unchanged and fixture-local.

## Non-Goals

- No candidate sandbox rendering.
- No before/after image analysis.
- No source, caption, export, accepted, or golden edits.
- No release-blocking dogfood gate.
- No new third-party dependency.

## Supported Mappings

### Text Boundary

Input:

```json
{
  "schema": "figure-agent.text-boundary-clash.v1",
  "total": 0,
  "candidates": []
}
```

Output metric:

```json
{
  "text_boundary.blocker_count": {
    "baseline": 0,
    "candidate": 0
  }
}
```

### Future Checker Families

The adapter may use the same pattern for checker reports that expose `total`:

- `visual_clash.total` -> `visual_clash.blocker_count`
- `label_path.total` -> `label_path.near_miss_count`
- `undeclared_geometry.total` -> `undeclared_geometry.candidate_count`

This implementation only needs to prove the generic `total` adapter and dogfood
text-boundary path.

## Data Semantics

When adapting a single current checker report:

- `baseline` is the current checker `total`.
- `candidate` is the same current checker `total`.
- The movement does not prove improvement.
- It proves the detector metric is available and can participate in future
  before/after comparison.

The generated report must include:

```json
{
  "schema": "figure-agent.benchmark-detector-report.v1",
  "source": {
    "kind": "checker_report",
    "checker_schema": "figure-agent.text-boundary-clash.v1",
    "checker_report": "build/text_boundary_clash.json"
  }
}
```

## Safety

- Reads must remain fixture-local.
- Symlinked checker reports are treated as `artifact_missing`.
- Malformed checker reports are treated as `artifact_missing` with diagnostics.
- Preview writes nothing.
- Explicit `--write` continues to write only normalized benchmark detector
  reports under the already approved output path.

## Tests

- Dogfood preview for `fig1_overview_v2_pair_001_vault` returns
  `text_boundary: available`.
- The adapted report has `source.kind == checker_report`.
- The adapted metric has `baseline == candidate == total`.
- A tmp fixture with checker-native `total` but no `metrics` is converted.
- Existing smoke seed report behavior remains unchanged.
- Focused pytest, ruff, smoke benchmark, dogfood preview, and release gate
  dry-run pass.

## Acceptance Criteria

- `fig-agent benchmark-detectors fig1_overview_v2_pair_001_vault --suite dogfood --json`
  returns `text_boundary` state `available`.
- The command writes no files in preview mode.
- `fig-agent benchmark-run --suite dogfood --limit 1 --json` does not fail due
  to `metric_missing`.
- `caption.md` remains untouched by this slice.
