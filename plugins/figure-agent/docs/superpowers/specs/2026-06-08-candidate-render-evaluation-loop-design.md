# Candidate Render Evaluation Loop Design

Status: Draft for user review
Date: 2026-06-08
Owner: figure-agent
Target release: post-0.9.3

## Problem

The current candidate workflow can propose and package panel-level improvement
candidates, but it still stops short of proving that a candidate renders into
usable visual evidence. This leaves the operator with metadata, a source patch
copy, and review text, but not a deterministic before/after artifact that shows
whether the proposed change actually improved the figure.

For real figure improvement, the next boundary is not automatic source apply.
The next boundary is a locked candidate sandbox that can compile, export, crop,
compare, rank, and report candidate evidence without mutating the manuscript
fixture or accepted build artifacts.

## Goals

- Render selected candidates in an isolated build sandbox under
  `examples/<name>/build/candidates/<candidate_id>/`.
- Produce before/after artifacts for the target panel from the existing fixture
  build and the candidate build.
- Attach deterministic visual evidence to candidate review packets and MCP
  resources.
- Add a small visual evaluation layer that records objective deltas and hard
  failure gates without claiming automatic acceptance.
- Preserve the current review-only authority model. Candidate rendering must not
  edit source TeX, accepted golden artifacts, fixture `build/<name>.*`, fixture
  `exports/`, or user manuscript files.
- Keep direct CLI use, Cowork plugin use, and MCP use aligned on the same
  runtime path contract.

## Non-Goals

- No automatic application of candidates to manuscript source.
- No automatic golden promotion or human acceptance bypass.
- No LLM-only judgment of visual quality.
- No broad generation of new candidate families beyond hooks needed by the
  render/evaluation loop.
- No new third-party runtime dependency.
- No writes outside the candidate sandbox except explicit JSON outputs requested
  by the operator.

## Public Interfaces

### CLI

Extend the existing candidate commands with rendering and evaluation stages:

```bash
fig-agent render-candidates <name> \
  --candidate-set <path> \
  [--candidate-id <id>] \
  [--compile] \
  [--export] \
  [--crop-panel <panel>] \
  [--evaluate] \
  [--json]
```

Required behavior:

- Without `--compile`, the command prepares sandbox source copies and
  manifests only.
- With `--compile`, the command compiles each selected candidate inside its
  candidate sandbox.
- With `--export`, the command exports candidate PDF/SVG/PNG/TIFF artifacts
  when host tools are available.
- With `--crop-panel`, the command creates original and candidate panel crops
  using the candidate's declared panel when omitted.
- With `--evaluate`, the command records deterministic visual deltas and hard
  gate statuses.
- JSON output must use fixture-relative paths and must never expose absolute
  workspace paths in stable contract fields.

Do not add a separate single-candidate command in this slice. Use
`render-candidates --candidate-id <id> --evaluate` as the single command path:

```bash
fig-agent render-candidates <name> \
  --candidate-set <path> \
  --candidate-id <id> \
  --evaluate \
  [--json]
```

### MCP

Keep MCP as a review/evidence surface, not an apply surface.

- `figure_agent_render_candidates` writes only under the locked candidate
  sandbox.
- `figure_agent_compare_candidate` must return before/after artifact
  descriptors when rendered artifacts exist.
- `figure_agent_candidate_resource` must continue to reject path traversal,
  symlinks, escaped candidate paths, and unexpected file types.
- MCP responses must distinguish `not_rendered`, `rendered`, `failed`, and
  `dependency_missing` states.

## Architecture

### `candidate_render.py`

Responsibilities:

- Resolve candidate set paths through `runtime_paths.py`.
- Validate candidate IDs and candidate set lineage.
- Create one sandbox per candidate:
  `examples/<name>/build/candidates/<candidate_id>/`.
- Copy the source TeX and required local fixture assets into the sandbox or
  reference approved read-only assets explicitly.
- Compile with output directories inside the sandbox.
- Export rendered outputs into the sandbox.
- Write a candidate render manifest containing stage results, artifact
  descriptors, tool diagnostics, and content hashes.

Hard invariants:

- The source fixture is read-only.
- All generated files land under the candidate sandbox.
- The command rejects symlinked or escaped `build`, `build/candidates`,
  candidate directories, manifests, source copies, and artifact paths.
- Bundled styles resolve from `plugin_root/styles`.
- User figure fixtures resolve from `workspace_root/examples/<name>`.

### `candidate_visual_eval.py`

New focused module.

Responsibilities:

- Locate original rendered artifact from the fixture build.
- Locate candidate rendered artifact from the candidate sandbox.
- Produce target-panel before/after crops.
- Record deterministic image evidence:
  - crop dimensions
  - file hashes
  - simple pixel-difference summary
  - exported file availability
  - stage success and dependency diagnostics
- Run existing lightweight checkers when they apply without broadening scope:
  - text boundary clash
  - label/path proximity
  - visual clash
  - critique zoom crop generation

Evaluation semantics:

- The evaluator records one of `blocked`, `failed`, `rendered`, or
  `rendered_needs_human_review`.
- The evaluator must not mark a candidate as accepted.
- A positive score means "worth human review", not "safe to apply".
- Missing host tools produce dependency diagnostics and a non-success stage.

### `candidate_review_packet.py`

Extend review packets with:

- `render_status`
- `render_manifest_path`
- `before_artifacts`
- `after_artifacts`
- `visual_deltas`
- `hard_gates`
- `human_review_required: true`

The review packet must keep existing textual critique and candidate metadata.
Rendered artifact fields are additive.

### `candidate_rank.py`

Extend ranking to consume visual evaluation summaries.

Ranking rules:

- Candidates with compile/export failures rank below rendered candidates.
- Candidates with hard gate failures rank below rendered candidates that only
  require human review.
- Ranking never grants apply authority.
- Ranking output must explain the strongest positive and negative evidence in
  deterministic fields.

## Data Contracts

### Render Manifest

Path:

```text
examples/<name>/build/candidates/<candidate_id>/render_manifest.json
```

Required fields:

```json
{
  "schema_version": 1,
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "candidate_id": "CAND001",
  "candidate_hash": "sha256:...",
  "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
  "sandbox_path": "build/candidates/CAND001",
  "stages": {
    "prepare": {"status": "success"},
    "compile": {"status": "success"},
    "export": {"status": "success"},
    "crop": {"status": "success"},
    "evaluate": {"status": "rendered_needs_human_review"}
  },
  "artifacts": {
    "source_copy": "build/candidates/CAND001/source/candidate.tex",
    "pdf": "build/candidates/CAND001/render/candidate.pdf",
    "png": "build/candidates/CAND001/render/candidate.png",
    "before_crop": "build/candidates/CAND001/crops/original_panel_C.png",
    "after_crop": "build/candidates/CAND001/crops/candidate_panel_C.png"
  },
  "visual_deltas": {
    "pixel_diff_mean": 0.0,
    "pixel_diff_max": 0,
    "changed_bbox": null
  },
  "diagnostics": []
}
```

All path fields are fixture-relative. Absolute paths are allowed only in
ephemeral debug logs, never in stable JSON contract fields.

### Stage Status Values

Allowed values:

- `not_run`
- `success`
- `failed`
- `dependency_missing`
- `blocked`
- `rendered`
- `rendered_needs_human_review`

## Safety Boundaries

The candidate renderer must enforce all of these boundaries:

- Candidate IDs must match the existing safe identifier contract.
- Candidate set paths must resolve inside `examples/<name>/build/candidates/`
  unless explicitly provided as a safe fixture-relative path by an existing
  command contract.
- Candidate output directories must not pre-exist as symlinks.
- Any symlink encountered on a candidate artifact path is rejected.
- The renderer must not follow ancestor symlinks out of the fixture.
- The compile command must run with output directories inside the sandbox.
- The renderer must not overwrite fixture `build/<name>.pdf`,
  `build/<name>.svg`, `exports/`, accepted artifacts, or golden artifacts.
- Candidate artifacts must not include manuscript-only dirty fixtures in
  package outputs.

## Dogfood Scenario

Primary scenario:

```bash
fig-agent candidates fig1_overview_v2_pair_001_vault \
  --panel C \
  --family energy-trap-alignment \
  --json \
  --output ./build/candidates/panel_C_candidate_set.json

fig-agent render-candidates fig1_overview_v2_pair_001_vault \
  --candidate-set ./build/candidates/panel_C_candidate_set.json \
  --candidate-id CAND001 \
  --compile \
  --export \
  --crop-panel C \
  --evaluate \
  --json

fig-agent compare-candidate fig1_overview_v2_pair_001_vault CAND001 \
  --candidate-set ./build/candidates/panel_C_candidate_set.json \
  --json
```

Pass condition:

- `CAND001` produces a render manifest.
- The manifest references before/after Panel C crops.
- The review packet exposes those artifacts.
- The original fixture build and source remain unchanged.
- The command exits with a dependency diagnostic instead of a false success when
  TeX, Poppler, `rsvg-convert`, or image conversion tools are unavailable.

## Test Plan

### Contract Tests

- CLI help exposes the render/evaluate flags.
- Public docs and safe commands use `fig-agent ...`.
- JSON schema validates required render manifest fields.
- Stable JSON fields contain fixture-relative paths only.
- Stage status values are limited to the documented enum.

### Sandbox Tests

- Reject candidate IDs with traversal characters.
- Reject candidate set paths outside the fixture.
- Reject symlinked `build/candidates`.
- Reject symlinked candidate directories.
- Reject symlinked source copies and rendered artifacts.
- Verify compile/export outputs cannot overwrite fixture build artifacts.

### Runtime Tests

- Use a temporary workspace with a smoke fixture.
- Run render preparation without host TeX and verify a precise dependency
  diagnostic when compile is requested.
- Mock compile/export subprocesses for deterministic unit coverage.
- Verify rendered manifest paths stay fixture-relative.
- Verify review packets include artifact descriptors only after render
  manifests exist.

### MCP Tests

- `figure_agent_render_candidates` writes only under the candidate sandbox.
- `figure_agent_compare_candidate` returns render evidence when present.
- Candidate resource reads reject path escape and symlink escape attempts.
- Missing render manifests return `not_rendered`, not an exception disguised as
  a successful comparison.

### Dogfood Verification

Run the primary scenario against
`fig1_overview_v2_pair_001_vault` and inspect:

- candidate render manifest
- original Panel C crop
- candidate Panel C crop
- compare packet JSON
- git status showing no source mutation

## Risks

- TeX builds can depend on relative assets that are not copied into the
  sandbox. Mitigation: start with explicit asset discovery from the source
  compile inputs and fail closed when assets are ambiguous.
- Existing checker scripts can assume fixture build paths. Mitigation: adapt
  them through parameters rather than changing their global defaults.
- Pixel diff is not a semantic quality metric. Mitigation: report it as
  objective evidence only and require human review.
- Candidate rendering can create large artifacts. Mitigation: keep artifacts
  under `build/candidates`, exclude them from packages, and audit size in tests.

## Acceptance Criteria

- A real Panel C candidate can be rendered in a sandbox without touching source
  files or accepted build outputs.
- The operator can inspect before/after crops through CLI JSON and MCP resource
  paths.
- Hard failures and missing dependencies are explicit in JSON.
- The candidate ranking surface accounts for render/evaluation evidence without
  granting apply authority.
- The release gate includes focused tests for CLI contract, sandbox safety,
  review packet enrichment, and MCP evidence exposure.
