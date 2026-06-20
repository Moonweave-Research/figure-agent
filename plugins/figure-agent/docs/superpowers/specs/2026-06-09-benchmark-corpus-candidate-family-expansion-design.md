# Benchmark Corpus and Candidate Family Expansion Design

Status: draft for review

Target: figure-agent 0.13.x after quality memory, memory-aware ranking,
lightweight benchmark run/compare, and read-only MCP benchmark previews

## Summary

The previous quality-memory work made figure-agent able to remember outcomes and
compare local benchmark runs. That is necessary but not sufficient for better
drawing. The next stage is to define what "benchmark" means for figure-agent
and to expand the candidate families that can actually improve figures.

In this project, a benchmark is not a scraped paper-figure dataset and not a
training corpus. It is a fixed, local, versioned test suite of figure fixtures
used to answer one question:

> Did this figure-agent change produce safer, measurably better figure-repair
> candidates without regressing known cases?

The benchmark suite contains input fixtures with known defect contracts,
expected measurable detector movement, and optional human-reviewed outcomes.
It is closer to a compiler regression suite than a machine-learning benchmark.

## What "Benchmark" Means Here

The benchmark is an evaluation harness, not a model-training dataset.

It answers:

- Can figure-agent find a valid candidate for this known defect?
- Does the candidate reduce the intended measurable defect?
- Does it avoid known hard regressions?
- Does a new engine change perform at least as well as the previous engine on
  the same fixed local cases?

It does not answer by itself:

- Is this figure ready for Nature/Science submission?
- Is the scientific story correct?
- Is the candidate visually preferable to a trained designer's eye?
- Has the agent learned a global style from external papers?

There are two benchmark styles:

1. Contract-based benchmark: the case has a defect contract and detector
   movement expectations. This is the default.
2. Golden-target benchmark: the case has a manually authored expected output.
   This is allowed only for repo-authored synthetic fixtures where the repo owns
   both input and target. It is not allowed for copied paper figures.

Most figure-agent benchmarks should be contract-based. A benchmark case is
"good enough" when it catches regressions and ranks safer candidates higher,
even if there is no single perfect target image.

## Benchmark Taxonomy

### 1. Synthetic Contract Fixtures

Synthetic fixtures are small figures authored inside this repo specifically to
exercise one repair behavior.

Examples:

- `smoke_label_overlap_demo`
- `smoke_leader_line_demo`
- `smoke_panel_spacing_demo`
- `smoke_contrast_demo`
- `smoke_annotation_box_demo`

These are the safest benchmark cases because the repo owns every asset and the
expected defect is explicit. They should be the first suite used for release
blocking.

Use synthetic fixtures for:

- deterministic tests;
- fast benchmark runs;
- candidate-family contract tests;
- release-gate regression blocking.

Do not use synthetic fixtures to claim publication quality. They prove that a
mechanic works, not that a manuscript figure is beautiful.

### 2. Dogfood Fixtures

Dogfood fixtures are real user-owned manuscript/workspace fixtures already
present under the active workspace `examples/`.

Examples:

- `fig1_overview_v2_pair_001_vault`

Dogfood fixtures are used to check whether the same mechanics survive real
layout complexity. They are not hidden training data. They are listed
explicitly in `benchmarks/quality_suites.yaml`, and benchmark commands must not
modify their source, captions, accepted/golden state, publication state, or
exports unless a separate explicit apply/acceptance command is run.

Use dogfood fixtures for:

- realism checks;
- candidate diversity checks;
- review-packet quality checks;
- optional release warnings.

Do not make dogfood failures silently block release until the failure criterion
is deterministic and the fixture owner accepts that gate.

### 3. Reference-Derived Pattern Fixtures

Reference-derived fixtures are locally authored mini-fixtures inspired by
defect patterns seen in external papers or user-provided reference images, but
they do not copy a copyrighted paper figure as a benchmark target.

Allowed:

- "Create a small energy-diagram fixture with shallow/deep labels and deliberate
  label-path proximity."
- "Create a generic MIM-stack fixture with a low-contrast axis label."
- "Create a schematic with leader lines crossing label text."

Not allowed:

- storing a paper's figure image as a target;
- recreating the exact composition of a copyrighted figure as a golden
  benchmark;
- using external paper images as hidden training state;
- claiming a candidate is scientifically correct because it resembles an
  external figure.

Reference-derived fixtures are useful because they turn a design pattern into a
test without making the benchmark legally or scientifically ambiguous.

## What a Benchmark Case Contains

Each benchmark fixture must declare:

```yaml
schema: figure-agent.benchmark-contract.v1
fixture: smoke_label_overlap_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
  - visual_clash
detector_reports:
  text_boundary: benchmark_reports/text_boundary.json
  visual_clash: benchmark_reports/visual_clash.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
  visual_clash.new_blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
  - candidate_hard_gate_rejected
  - text_boundary_blocker_increase
  - semantic_anchor_removed
human_review:
  required_for_apply: true
  required_for_publication_claim: true
release:
  release_blocking: true
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
```

The contract is not a pixel-perfect golden image. It says which defect the
agent should try to improve and which measurable regressions are forbidden.

The contract loader must keep these axes separate:

- `defect_class`: what is wrong with the input fixture, such as
  `label_overlap`, `leader_line_collision`, `panel_boundary_overlap`,
  `low_contrast`, or `annotation_box_collision`.
- `candidate_families`: the generator family namespace, such as
  `label-repair`, `connector-routing`, `panel-layout`, `contrast-repair`, or
  `annotation-box-layout`.
- `candidate_edit_classes`: the concrete edit operation class emitted in
  candidate manifests, such as `label_offset`, `leader_line_reroute`,
  `panel_spacing_adjust`, `contrast_boost`, or `annotation_box_resize`.

This separation is mandatory because current candidate data already uses
`family` and `edit_class` as different fields. Memory priors and benchmark
contracts must not accidentally treat an edit class as a family id.

Detector movement is evaluated only when a required detector report exists and
can be parsed. Missing detector reports are not silently treated as success:

- for `smoke` release-blocking fixtures, missing required detector reports make
  the fixture `failed` with reason `required_detector_missing`;
- for `dogfood` fixtures, missing required detector reports make the fixture
  `warning` unless the fixture contract has `release.release_blocking: true`;
- for `patterns`, missing required detector reports block candidate-family
  promotion but not package release.

Supported movement operators for the first implementation:

- `decrease`: candidate value must be lower than baseline value.
- `decrease_or_equal`: candidate value must be lower than or equal to baseline.
- `increase`: candidate value must be higher than baseline.
- `increase_or_equal`: candidate value must be higher than or equal to baseline.
- `unchanged`: candidate value must match baseline exactly.

The benchmark runner must report both raw detector values and evaluated
movement state, for example:

```json
{
  "detector_evaluation": {
    "state": "passed",
    "movements": [
      {
        "metric": "text_boundary.blocker_count",
        "baseline": 3,
        "candidate": 1,
        "operator": "decrease_or_equal",
        "state": "passed"
      }
    ]
  }
}
```

## Benchmark Suites

Update `plugins/figure-agent/benchmarks/quality_suites.yaml` to separate suite
roles:

```yaml
schema: figure-agent.quality-benchmark-suites.v1
suites:
  smoke:
    description: Fast synthetic fixtures for release-blocking mechanics.
    fixtures:
      - smoke_label_overlap_demo
      - smoke_leader_line_demo
      - smoke_panel_spacing_demo
      - smoke_contrast_demo
      - smoke_annotation_box_demo
  dogfood:
    description: Explicit user-owned real fixtures for realism checks.
    fixtures:
      - fig1_overview_v2_pair_001_vault
  patterns:
    description: Reference-derived local pattern fixtures, no copied targets.
    fixtures:
      - pattern_energy_trap_labels_demo
      - pattern_mim_stack_labels_demo
```

Release policy:

- `smoke` hard regressions block release.
- `patterns` hard regressions block candidate-family promotion but not package
  release until the pattern fixture is stable.
- `dogfood` hard regressions warn by default. They block only when a fixture
  has an explicit `release.release_blocking: true` contract.

Packaging policy:

- every fixture listed in the installed `smoke` suite must be included in the
  Cowork ZIP with source, `spec.yaml`, briefing, and `benchmark_contract.yaml`;
- generated `build/`, `exports/`, caches, memory indexes, and accepted/golden
  artifacts must remain excluded;
- user-owned dogfood fixtures such as `fig1_overview_v2_pair_001_vault` remain
  excluded from the Cowork ZIP unless the owner explicitly creates a sanitized
  package fixture;
- `package_cowork_plugin.py` and `release_gate.py` must fail if the installed
  `quality_suites.yaml` names a `smoke` fixture that is not present in the ZIP.

## Candidate Family Roadmap

### Family 1: `label-repair`

Purpose:

- move text labels slightly while preserving semantic anchor and source
  compileability.

Primary edit classes:

- `label_offset`

Current state:

- basic candidate generation exists for simple label cases and Panel C dogfood.

Needed upgrades:

- support multi-line TikZ node selectors;
- compute direction from nearest collision/path vector when detector evidence
  exists;
- reject offsets that cross panel boundaries;
- emit detector expected movement in candidate manifest.

### Family 2: `connector-routing`

Purpose:

- move or bend leader lines so they do not cross labels, axis ticks, or
  semantic curves.

Primary edit classes:

- `leader_line_reroute`

Inputs:

- label-path proximity report;
- candidate TeX index;
- panel model;
- optional intent anchors.

Candidate operations:

- replace straight line with two-segment orthogonal route;
- adjust control points for a curved connector;
- shorten a line endpoint away from label glyph bounds.

Hard gates:

- cannot disconnect leader from target object;
- cannot change label text;
- cannot route outside panel bbox;
- must compile after patch.

### Family 3: `panel-layout`

Purpose:

- adjust row/column panel spacing or local panel anchors to reduce boundary
  overlap.

Primary edit classes:

- `panel_spacing_adjust`

Inputs:

- text-boundary clash report;
- panel bbox hints;
- TeX coordinate index.

Candidate operations:

- increase row gutter;
- shift panel group by a small bounded delta;
- update panel label position with the panel group.

Hard gates:

- cannot change panel order;
- cannot crop content outside final page;
- cannot reduce panel bbox below original content extent.

### Family 4: `contrast-repair`

Purpose:

- improve low-contrast labels, axes, or paths without changing semantic color
  roles.

Primary edit classes:

- `contrast_boost`

Inputs:

- style definitions;
- visual clash/contrast detector report;
- intent color-role declarations.

Candidate operations:

- darken a text color within allowed palette;
- increase stroke opacity or width within a bounded range;
- add a label backdrop only when the fixture contract allows it.

Hard gates:

- cannot change semantic color category;
- cannot introduce new label-backdrop overflow;
- cannot make a decorative element dominate the data mark.

### Family 5: `annotation-box-layout`

Purpose:

- resize or reposition annotation boxes so labels and internal drawings do not
  collide.

Primary edit classes:

- `annotation_box_resize`

Inputs:

- text-boundary clash report;
- visual clash report;
- box geometry selectors.

Candidate operations:

- widen an annotation box by a small bounded amount;
- move internal label anchor;
- increase internal padding while preserving outer alignment.

Hard gates:

- cannot cover neighboring panels;
- cannot hide internal drawing elements;
- cannot move semantic labels outside their box.

## Ranking Upgrade

`candidate_rank.py` must evolve from fixed soft scores to detector-aware
scoring.

Add soft score inputs:

- memory prior;
- render success;
- detector delta preview;
- risk level;
- review burden;
- candidate family reliability;
- semantic preservation evidence.

Ranking rule:

```text
rank_score =
  base_reviewable_score
  + render_bonus
  + detector_improvement_bonus
  + memory_prior
  - review_burden_penalty
  - risk_penalty
```

Hard gates remain separate:

- rejected candidates stay rejected;
- memory cannot upgrade authority;
- detector improvements cannot bypass human review;
- benchmark scores cannot apply source changes.

Detector-aware ranking must consume detector evaluations as soft evidence only
after hard gates are known. A candidate with positive detector movement but a
failed semantic or compile gate remains rejected. Missing detector reports leave
the existing score unchanged only for non-release preview commands; in a
release-blocking benchmark they are reported as benchmark failures before
ranking is used for release decisions.

The first detector-aware score fields are:

```json
{
  "scores": {
    "detector_prior": 0.15,
    "memory_prior": 0.05,
    "review_burden": 0.5
  },
  "evidence": {
    "positive": ["detector:text_boundary.blocker_count:decrease_or_equal"],
    "negative": []
  }
}
```

## Implementation Plan

### Task 1: Benchmark Contract Loader

Files:

- Create `plugins/figure-agent/scripts/benchmark_contracts.py`
- Test `plugins/figure-agent/tests/test_benchmark_contracts.py`
- Modify `plugins/figure-agent/scripts/quality_benchmark.py`

Responsibilities:

- load `examples/<name>/benchmark_contract.yaml`;
- validate fixture name, defect class, candidate families, expected movement,
  and hard regression codes;
- validate `candidate_families` separately from `candidate_edit_classes`;
- validate detector report paths are fixture-local and not symlinks;
- validate `reference_policy` and reject copied-image golden targets unless
  `kind: repo_authored_synthetic`;
- return a structured diagnostic when the contract is missing;
- never create or modify fixture files.

Acceptance tests:

- valid contract loads as `figure-agent.benchmark-contract.v1`;
- missing contract returns `state=missing`, not failure;
- path escape in fixture name is rejected;
- unknown hard regression code is rejected;
- `label_offset` under `candidate_families` is rejected; it belongs under
  `candidate_edit_classes`;
- detector report paths outside the fixture are rejected;
- missing `reference_policy` is rejected for `patterns` fixtures.

### Task 2: Synthetic Smoke Fixtures

Files:

- Create `plugins/figure-agent/examples/smoke_label_overlap_demo/`
- Create `plugins/figure-agent/examples/smoke_leader_line_demo/`
- Create `plugins/figure-agent/examples/smoke_panel_spacing_demo/`
- Create `plugins/figure-agent/examples/smoke_contrast_demo/`
- Create `plugins/figure-agent/examples/smoke_annotation_box_demo/`
- Modify `plugins/figure-agent/benchmarks/quality_suites.yaml`
- Test `plugins/figure-agent/tests/test_quality_benchmark.py`

Responsibilities:

- each fixture must be small and compileable;
- each fixture must contain one explicit defect class;
- each fixture must include `benchmark_contract.yaml`;
- benchmark preview must include contract state for every fixture;
- package builder must include every installed `smoke` fixture and its contract
  in the Cowork ZIP.

Acceptance tests:

- `fig-agent benchmark-run --suite smoke --limit 5 --json` completes without
  writing;
- every smoke fixture has a contract;
- missing fixture is still reported as skipped, not created;
- generated Cowork ZIP contains all `smoke` fixtures listed in
  `quality_suites.yaml`;
- generated Cowork ZIP excludes dogfood fixtures and generated benchmark
  outputs.

### Task 3: Candidate Family Generalization

Files:

- Modify `plugins/figure-agent/scripts/candidate_families.py`
- Modify `plugins/figure-agent/scripts/candidate_generator.py`
- Test `plugins/figure-agent/tests/test_candidate_families.py`
- Test `plugins/figure-agent/tests/test_candidate_cli_contract.py`

Responsibilities:

- add deterministic candidate generation for:
  - `leader_line_reroute`;
  - `panel_spacing_adjust`;
  - `contrast_boost`;
  - `annotation_box_resize`;
- each candidate must emit family, edit_class, target, expected_delta,
  semantic_risks, blocked_if, and required_commands;
- family ids must use the canonical family namespace, while concrete operations
  use `edit_class`;
- unsupported fixture structures must produce refusal objects, not exceptions.

Acceptance tests:

- each smoke fixture produces at least one candidate for its intended family;
- candidate manifests preserve `review_only` where visual/human review is
  needed;
- invalid family names are rejected.

### Task 4: Detector-Aware Ranking

Files:

- Modify `plugins/figure-agent/scripts/candidate_rank.py`
- Modify `plugins/figure-agent/scripts/quality_benchmark.py`
- Test `plugins/figure-agent/tests/test_candidate_rank.py`
- Test `plugins/figure-agent/tests/test_quality_benchmark.py`

Responsibilities:

- read detector summaries when present;
- add `scores.detector_prior`;
- add positive/negative evidence strings for detector movement;
- include raw baseline/candidate detector values in benchmark result JSON;
- fail release-blocking benchmark cases when required detector reports are
  missing;
- include risk/review-burden penalty;
- preserve hard gate and effective apply authority.

Acceptance tests:

- detector improvement raises one reviewable candidate over another;
- detector regression lowers rank score;
- rejected candidate remains rejected with positive detector evidence;
- missing detector reports leave existing score unchanged only in non-release
  ranking preview mode.

### Task 5: Release Gate Integration

Files:

- Modify `plugins/figure-agent/scripts/release_gate.py`
- Test `plugins/figure-agent/tests/test_release_contract.py`
- Test `plugins/figure-agent/tests/test_quality_benchmark_compare.py`

Responsibilities:

- run the current `smoke` benchmark in preview mode during release gate;
- compare current smoke result to a committed baseline report when one exists;
- never use an arbitrary "latest" local `.scratch` run as release truth;
- block package release on smoke hard regression;
- report dogfood regressions as warnings unless explicitly release-blocking;
- include benchmark summary in release report JSON.

Acceptance tests:

- identical smoke benchmark comparison does not block;
- new hard gate failure in smoke blocks release;
- dogfood warning does not block unless contract says release-blocking;
- release gate does not write outside `dist/` and `.scratch/`;
- release gate reports `benchmark_baseline_missing` as a warning during the
  first rollout, not as an implicit pass;
- release gate fails if a release-blocking smoke fixture lacks required detector
  reports.

### Task 6: MCP Next Experiment Preview

Files:

- Modify `plugins/figure-agent/mcp/figure_agent_server.py`
- Create `plugins/figure-agent/scripts/quality_next_experiment.py`
- Test `plugins/figure-agent/tests/test_mcp_facade.py`
- Test `plugins/figure-agent/tests/test_quality_next_experiment.py`

Responsibilities:

- expose `figure_agent_quality_next_experiment`;
- return read-only recommendation for which candidate family to try next;
- base recommendation on benchmark failures, memory index, and available
  fixture contracts;
- do not expose write/apply/accept flags;
- return only safe preview commands from an allowlist.

Allowed recommendation commands:

- `fig-agent benchmark-run --suite <suite> --json`
- `fig-agent benchmark-compare <baseline-run> <candidate-run> --json`
- `fig-agent candidates <name> --json`
- `fig-agent rank-candidates <name> --candidate-set <path> --json`
- `fig-agent memory-index --fixture <name> --json`

Forbidden recommendation commands:

- any command containing `--write`, `--apply`, `--accept`, `--overwrite`, or
  `--force`;
- `fig-agent apply-candidate`;
- `fig-agent apply-candidate-ready`;
- `fig-agent accept-candidate`;
- `fig-agent export --force-golden`;
- arbitrary shell commands or paths.

Acceptance tests:

- MCP schema has no `write`, `apply`, `accept`, `overwrite`, or arbitrary path;
- preview call does not create `.scratch`;
- recommendation includes reason codes and next public CLI command;
- recommendation command is rejected if it is not in the preview allowlist.

## Source Policy

Benchmark fixtures may use:

- repo-authored synthetic diagrams;
- user-owned fixtures already in the workspace;
- reference-derived patterns described in original local text;
- generated minimal assets owned by this repo.

Benchmark fixtures must not use:

- copied paper figure images as golden targets;
- downloaded datasets without an explicit license file;
- hidden Google Drive or CloudStorage paths;
- user manuscript fixtures not listed in `quality_suites.yaml`;
- dirty fixture source files as implicit training state.

Every benchmark contract must include a `reference_policy` block. Accepted
values:

- `repo_authored_synthetic`: fixture and optional golden target are authored in
  this repo.
- `user_owned_dogfood`: fixture is user-owned and explicitly listed in
  `quality_suites.yaml`; no package inclusion by default.
- `reference_derived_pattern`: fixture is an original local mini-figure derived
  from a written pattern description; external image files are forbidden.

The contract loader must reject `reference_derived_pattern` fixtures that
declare `golden_target_allowed: true` or include external image assets.

## Success Criteria

The next upgrade is complete when:

1. `smoke` has at least five synthetic fixtures with benchmark contracts.
2. At least four candidate families produce candidates on their intended smoke
   fixture.
3. `benchmark-run --suite smoke --json` reports candidate and ranking metrics
   plus contract state and detector evaluation without writing by default.
4. `benchmark-compare` detects a seeded hard regression.
5. `rank-candidates --use-memory` and detector-aware ranking preserve hard
   gates.
6. MCP exposes only read-only benchmark/memory/next-experiment tools.
7. Dogfood on `fig1_overview_v2_pair_001_vault` still runs without modifying
   `caption.md`, source TeX, exports, golden acceptance, or publication state.
8. Cowork ZIP includes all installed smoke benchmark fixtures and excludes
   dogfood/generated artifacts.
9. Release gate does not rely on arbitrary local latest benchmark runs.

## Review Checklist

- Does every benchmark fixture declare what it is testing?
- Are `defect_class`, `candidate_families`, and `candidate_edit_classes`
  separated correctly?
- Are required detector report paths fixture-local and symlink-safe?
- Does missing detector evidence fail or warn according to suite policy instead
  of silently passing?
- Is every external visual influence transformed into a local original pattern,
  not copied as a target?
- Does every fixture declare a `reference_policy`?
- Does the package builder include installed smoke fixtures but exclude dogfood?
- Can benchmark writes escape through symlinks?
- Can memory or detector evidence upgrade hard gates?
- Can MCP trigger write/apply/accept paths?
- Are MCP recommended commands restricted to the preview allowlist?
- Does release gate use a deterministic smoke run/baseline policy instead of
  arbitrary local latest reports?
- Does release blocking apply only to deterministic smoke hard regressions?
- Does dogfood remain explicit, local, and owner-controlled?
