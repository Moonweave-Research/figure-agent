# Render-Derived Detector and Dogfood Benchmark Promotion Design

Status: draft for review
Date: 2026-06-09
Owner: figure-agent
Target release: post benchmark-contract MVP

## Current State

The benchmark-contract MVP is in place:

- `smoke` has five repo-authored synthetic fixtures.
- Each smoke fixture has a `benchmark_contract.yaml`.
- Each smoke fixture has at least one detector report under
  `benchmark_reports/`.
- `quality_benchmark.py` evaluates expected detector movement and fails
  release-blocking smoke fixtures when detector reports are missing or worsen.
- `candidate_rank.py` can use detector movement as a soft prior.
- The release gate verifies smoke fixture packaging and detector report
  inclusion.

The remaining limitation is that the current smoke detector reports are static
fixture-local JSON files. They prove the benchmark contract and ranking path,
but they do not yet prove that figure-agent can derive those detector metrics
from rendered before/after artifacts.

## Problem

figure-agent is closer to becoming a useful figure-improvement tool, but its
current benchmark signal is still partly declarative:

- smoke reports are authored JSON, not generated from a render;
- dogfood figures are listed but not promoted into a measured benchmark gate;
- detector output is not yet tied to candidate render manifests;
- a candidate can be ranked using detector movement only when a report already
  exists.

This means the system can check a contract, but it cannot yet close the loop:

> candidate source change -> isolated render -> detector metrics -> benchmark
> movement -> ranking -> review packet.

The next slice must close that loop without mutating user figures, accepted
goldens, exports, or Google Drive / CloudStorage locations.

## Scope Boundary

This spec is intentionally staged. The first implementation does not pretend
that all detectors are already pixel-derived. It establishes a safe detector
generation facade and regenerates the current smoke seed reports through that
facade. The second implementation adapts existing render/checker outputs into
the same report schema. Only after those two steps should dogfood results be
used as evidence for real figure-improvement quality.

In short:

- Phase A: deterministic report-generation contract and write safety.
- Phase B: adapters from existing checker/render outputs.
- Phase C: dogfood preview promotion with warning semantics.

## Goals

- Create the detector report generation path that can move from checked-in
  seed JSON to render-derived evidence without changing benchmark contracts.
- Support the same detector report schema for static smoke fixtures and
  generated candidate renders.
- Add a read-only-by-default benchmark detector generation command. Its write
  mode, when explicitly requested, writes only under controlled local fixture
  paths.
- Promote `fig1_overview_v2_pair_001_vault` into a dogfood benchmark preview
  with warning semantics, not release-blocking semantics.
- Attach detector movement summaries to candidate render/review artifacts.
- Keep Cowork/plugin packaging deterministic and small.

## Non-Goals

- No automatic source apply.
- No automatic golden acceptance.
- No ML model training or external paper-image dataset.
- No copied paper figure as a benchmark target.
- No writes under `~/Library/CloudStorage`, Google Drive, global caches, or
  hidden machine-level state.
- No broad visual-quality claim such as "publication ready" from detector
  metrics alone.

## Public Interfaces

### CLI

Add a read-only-by-default detector generation command:

```bash
fig-agent benchmark-detectors <name> \
  [--candidate-id <id>] \
  [--suite smoke|dogfood|patterns] \
  [--write] \
  [--json]
```

Default behavior:

- resolves `plugin_root` and `workspace_root` through `runtime_paths.py`;
- reads the fixture contract;
- inspects existing baseline and candidate render artifacts when available;
- returns detector metrics as JSON;
- performs no writes unless `--write` is passed.

Explicit write behavior:

- for repo-authored smoke fixtures, writes generated reports to
  `examples/<name>/benchmark_reports/generated/`;
- for user dogfood fixtures, writes generated reports only under
  `examples/<name>/build/benchmark_reports/`;
- never writes to `exports/`, accepted/golden state, source TeX, caption files,
  or package directories.

### MCP

Add a read-only MCP facade after the CLI exists:

```text
figure_agent_benchmark_detectors_preview
```

The MCP tool must:

- expose only preview output by default;
- reject write/apply/accept/golden flags;
- return dependency diagnostics instead of attempting installs;
- return fixture-relative artifact paths;
- never create `.scratch` or `build/` unless a separate explicit write-capable
  CLI path is used outside the MCP preview.

### Release Gate

Release gate changes:

- smoke detector generation preview must pass for all five smoke fixtures;
- package audit must include checked-in smoke contracts and seed reports;
- dogfood detector preview may warn but must not block release until a
  deterministic dogfood baseline is accepted;
- if a smoke contract points to a generated report path, the package builder
  must include only repo-owned generated seed reports, not user build outputs.

## Data Contracts

### Detector Report

Use the already-supported generic metric shape:

```json
{
  "schema": "figure-agent.benchmark-detector-report.v1",
  "fixture": "smoke_label_overlap_demo",
  "detector": "text_boundary",
  "source": {
    "kind": "render_derived",
    "baseline_artifact": "build/baseline/render.png",
    "candidate_artifact": "build/candidates/CAND001/render/candidate.png"
  },
  "metrics": {
    "text_boundary.blocker_count": {
      "baseline": 2,
      "candidate": 1
    }
  },
  "diagnostics": []
}
```

The benchmark runner may continue to accept legacy minimal reports:

```json
{"metrics": {"text_boundary.blocker_count": {"baseline": 2, "candidate": 1}}}
```

but newly generated reports must use the explicit schema.

### Detector Result Envelope

`fig-agent benchmark-detectors --json` returns:

```json
{
  "schema": "figure-agent.benchmark-detectors-preview.v1",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "suite": "dogfood",
  "write_mode": false,
  "reports": [
    {
      "detector": "text_boundary",
      "state": "available",
      "report": {}
    }
  ],
  "writes": [],
  "diagnostics": []
}
```

States:

- `available`: detector metric was computed.
- `not_applicable`: contract does not require this detector.
- `artifact_missing`: required render/crop artifact is absent.
- `dependency_missing`: host tool is absent.
- `invalid_contract`: benchmark contract is malformed.
- `unsafe_path`: write target or artifact path escapes the fixture boundary.

## Detector Strategy

### Slice 1: Contract-Backed Synthetic Generator

For the first implementation, generate detector reports deterministically from
fixture-local synthetic metadata and existing checked-in smoke seed values.
The generator must not infer fake improvements from `expected_movement` alone.
It may copy or normalize repo-owned seed metrics into the explicit detector
report schema. This keeps the system honest about path safety, write policy,
schema, release-gate integration, and ranking behavior before heavier render
analysis is added.

This slice must still be useful:

- every generated report has schema, fixture, detector, source, metrics, and
  diagnostics;
- generated values must match the checked-in smoke seed reports;
- tests must prove missing reports can be regenerated under the allowed path.

### Slice 2: Existing Checker Adapter

Adapt existing checkers where they already exist:

- `check_text_boundary_clash.py` for text boundary count;
- existing visual-clash/label-path/undeclared-geometry reports where the
  fixture has compatible build outputs.

The adapter normalizes checker-specific output into the benchmark detector
report shape. It should not rewrite checker internals unless the adapter cannot
distinguish blocker counts from warnings.

### Slice 3: Render Manifest Adapter

When candidate render manifests exist, compute baseline/candidate metrics from:

- original fixture render;
- candidate sandbox render;
- panel crops when available;
- detector outputs produced inside the candidate sandbox.

The adapter should prefer actual candidate sandbox artifacts over static
fixture reports, but it must return `artifact_missing` rather than inventing
metrics.

## Dogfood Promotion

Add `fig1_overview_v2_pair_001_vault` as a dogfood preview target with this
policy:

- dogfood preview is read-only;
- detector missing state is a warning, not release failure;
- dogfood generated reports live under `build/benchmark_reports/`;
- no dogfood report is packaged into the Cowork ZIP;
- dogfood benchmark comparison is useful for local work but not a public
  release claim.

The first dogfood contract should use only detectors that can be supported by
existing build artifacts. If no stable detector applies, the dogfood preview
should report `artifact_missing` with exact required paths.

## Safety Rules

- All fixture names pass `fixture_identity.validate_fixture_name`.
- All read/write paths resolve under either `plugin_root/examples/<name>` for
  repo-owned smoke fixtures or `workspace_root/examples/<name>` for user
  fixtures.
- `benchmark-detectors --write` refuses symlinked `examples`, fixture dirs,
  `build`, `benchmark_reports`, output files, candidate dirs, and artifact
  paths.
- Writes are denied when the resolved output path contains `CloudStorage`,
  `GoogleDrive`, `Google Drive`, `~/Library/Caches`, or `~/.cache`.
- Generated JSON is deterministic: sorted keys, stable metric ordering, no
  absolute paths in stable fields.
- MCP preview has no write mode.

## Implementation Plan

1. Add tests for `benchmark_detector_reports.py`:
   - loads contract-required detector names;
   - returns preview envelope without writes;
   - rejects path escape and symlinked report destinations;
   - emits explicit schema for generated reports.

2. Add `scripts/benchmark_detector_reports.py`:
   - contract loader integration;
   - report generation envelope;
   - safe write helper;
   - minimal adapters for current smoke detector seed metrics;
   - no metric invention from contract operators alone.

3. Add CLI command:
   - `fig-agent benchmark-detectors <name> [--suite ...] [--write] --json`;
   - no writes without `--write`;
   - fixture-relative paths in output.

4. Integrate with `quality_benchmark.py`:
   - optional generated-report preview path;
   - no behavior change for existing static report contracts unless explicitly
     requested;
   - release-blocking failure semantics stay unchanged.

5. Add dogfood preview contract:
   - add or validate `benchmark_contract.yaml` for
     `fig1_overview_v2_pair_001_vault`;
   - dogfood suite remains non-blocking;
   - do not edit `caption.md` or manuscript source as part of this spec;
   - never package dogfood build reports.

6. Add MCP preview tool:
   - `figure_agent_benchmark_detectors_preview`;
   - read-only only;
   - no scratch/build creation.

7. Extend release gate:
   - preview smoke detector generation;
   - verify package excludes dogfood generated build reports;
   - keep `claude validate` behavior unchanged.

## Tests

Focused tests:

```bash
uv run pytest -q \
  plugins/figure-agent/tests/test_benchmark_detector_reports.py \
  plugins/figure-agent/tests/test_quality_benchmark.py \
  plugins/figure-agent/tests/test_mcp_facade.py \
  plugins/figure-agent/tests/test_release_gate.py
```

CLI smoke:

```bash
FIGURE_AGENT_WORKSPACE=plugins/figure-agent \
uv run --project plugins/figure-agent python plugins/figure-agent/bin/fig-agent \
  benchmark-detectors smoke_label_overlap_demo --suite smoke --json
```

Read-only proof:

- compare workspace tree before/after preview;
- assert no `.scratch`, `build/benchmark_reports`, or package output appears
  during preview;
- assert write mode creates only the allowed fixture-local report path.

Release gate:

```bash
python3 scripts/release_gate.py \
  --output /tmp/figure-agent-release-check-detector-generation \
  --skip-claude-validate \
  --json
```

## Review Checklist

- Does this spec improve actual drawing quality? Yes, indirectly: it turns
  candidate ranking toward generated and then render-derived evidence. Phase A
  is plumbing; Phase B is the first actual render-derived quality signal.
- Does it overclaim? No. Detector movement remains a review signal, not
  publication acceptance.
- Does it contaminate user files? The write policy forbids source/caption/export
  writes and keeps dogfood generated reports under `build/`.
- Does it create Google Drive risk? The path denylist explicitly rejects
  CloudStorage and GoogleDrive outputs.
- Does it add dependencies? No new third-party runtime dependency is required
  for the first implementation.
- Is dogfood release-blocking? No. Dogfood starts as preview/warning only.
- Is Phase A allowed to claim visual improvement? No. It may prove detector
  report plumbing and safety only.

## Acceptance Criteria

- `fig-agent benchmark-detectors <smoke-fixture> --suite smoke --json` returns
  explicit detector report envelopes for all five smoke fixtures without
  writing files.
- `fig-agent benchmark-detectors <smoke-fixture> --suite smoke --write --json`
  writes only under `examples/<name>/benchmark_reports/generated/`.
- A dogfood preview for `fig1_overview_v2_pair_001_vault` returns either
  `available` detector reports or exact `artifact_missing` diagnostics, without
  changing source, captions, exports, accepted state, or package outputs.
- MCP preview creates no files.
- Release gate verifies smoke detector generation preview and keeps dogfood as
  warning-only.
- Focused pytest and ruff pass.

## Open Decisions

- Whether dogfood generated reports should be committed is out of scope for
  this slice; default is no.
- Whether render-derived contrast metrics should use pixel luminance or existing
  checker outputs first is deferred until candidate render manifests are
  available.
- Whether MCP should ever expose write mode remains no for this slice.
