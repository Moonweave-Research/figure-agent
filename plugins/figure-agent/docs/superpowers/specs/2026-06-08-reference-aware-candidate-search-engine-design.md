# Reference-Aware Candidate Search Engine Design

Status: reviewed draft

Target: figure-agent 0.11.x after quality-map/propose/apply-plan and MCP facade
stabilize

## Summary

The previous figure-agent upgrades made the plugin installable, diagnosable,
MCP-visible, and able to classify some safe mechanical patch opportunities. They
did not make figure-agent substantially better at drawing.

This spec defines the next engine layer:

```text
reference + spec + caption + current render
  -> panel/subregion understanding
  -> candidate improvements
  -> render each candidate
  -> score by deterministic, visual, and semantic gates
  -> choose or present the safest winner
```

The product goal is not a taste oracle. The product goal is a
reference-aware, semantics-preserving, candidate-search system that makes
scientific figures measurably better while preserving human authority over
scientific meaning, accepted/golden state, and final art direction.

MCP is part of the delivery surface, not the core improvement mechanism. The
core must work through deterministic CLI contracts first; MCP exposes those
contracts to Claude/Cowork in a structured way.

## Current Baseline

Already available:

- `fig-agent status`, `compile`, `export`, `closeout`, `quality-map`, `propose`,
  `apply-plan`, and `verify-plan` public CLI surfaces.
- Runtime separation between installed plugin resources and user workspace.
- Deterministic checks for compile freshness, exports, critique freshness,
  visual clash evidence, text-boundary evidence, label-path proximity,
  undeclared geometry, crop audit, and publication gates.
- `audit_evidence_graph.py` and `quality_defect_ledger.py` to turn evidence into
  structured defects.
- Patch policy/planning/apply infrastructure for narrow safe-mechanical edits.
- MCP facade tools for doctor/status/compile/export/closeout/quality proposal
  workflows.
- Per-panel reference workflow design history and a figure-design philosophy
  that deliberately separates checkable conventions from taste.

Observed dogfood result on `fig1_overview_v2_pair_001_vault`:

- The system can report that the fixture is fresh, accepted, critique-clean, and
  publication-gate passing.
- The quality loop refuses to patch `export_tracked_golden`, correctly treating
  it as a human approval gate.
- The system still lacks a way to create and rank alternate improvements when no
  deterministic checker has emitted a safe mechanical defect.

## Problem

For a mature manuscript figure, the important improvement opportunities are
often not binary failures. They are comparative choices:

- this label position reads better than that one;
- this panel has too little visual hierarchy;
- this reference idiom should influence line weight, but not topology;
- this caption claim is visually under-supported;
- this palette works in color but loses hierarchy in grayscale;
- this candidate improves Panel D while making Panel C worse.

The current system is strong at saying "do not proceed" or "this artifact is
stale." It is weak at exploring multiple valid visual alternatives and selecting
the best one under scientific constraints.

## Goals

1. Define a candidate-search engine that can propose multiple bounded figure
   improvements without committing them.
2. Make every candidate traceable to a target panel, subregion, evidence item,
   and allowed edit scope.
3. Score candidates with a layered fitness function:
   - hard deterministic gates;
   - visual quality deltas;
   - reference faithfulness;
   - caption/spec support;
   - semantic invariant preservation;
   - human-review burden.
4. Render and compare candidates before any source mutation is accepted.
5. Keep scientific meaning and final acceptance under explicit human authority.
6. Expose the engine through CLI first, then MCP tools that return structured
   plans and artifacts instead of free-form command strings.
7. Build a benchmark suite so "better drawing" can be measured across fixed
   fixtures, not inferred from a single visual anecdote.

## Non-Goals

- Do not add an autonomous publication-acceptance decision.
- Do not let MCP mutate source files without explicit apply semantics.
- Do not infer scientific topology from aesthetics.
- Do not call external image-generation APIs in the core engine.
- Do not rebuild paper-figure-vault, literature retrieval, or general reference
  search in this slice.
- Do not replace human art direction for final taste calls.
- Do not make fig1's frozen reference state mutable as part of this upgrade.

## Product Principle

The next figure-agent should be judged by this standard:

> It should make it cheaper to find a better candidate and safer to know when no
> automatic candidate should be applied.

That means a "no patch; human gate" result is acceptable when it is evidence
backed. A broad automatic rewrite that looks nicer but changes science is a
failure.

## Architecture

Use a five-layer architecture.

### Layer 1: Figure Intent Model

The engine needs a structured model of what the figure is trying to do before it
can improve it.

Inputs:

- `spec.yaml`
- `briefing.md`
- `caption.md` when present
- `<name>.tex`
- current build/export artifacts
- critique and adjudication files
- panel references and paper-wide style references
- coordinate hints and perception packs

Fixture-local input contract:

| Input class | Location | Required? | Missing behavior |
|---|---|---:|---|
| Figure spec | `examples/<name>/spec.yaml` | yes | stop with `source_not_scaffolded` |
| Briefing | `examples/<name>/briefing.md` | yes | record absent briefing and downgrade semantic-risk candidates to review-only |
| Source | `examples/<name>/<name>.tex` | yes for candidates | stop candidate generation until authored |
| Caption | `examples/<name>/caption.md` | no | skip caption-support scoring; do not invent caption claims |
| Panel references | fixture-relative paths declared in `spec.yaml` | no | skip reference-faithfulness scoring for that panel |
| Paper-wide style references | fixture-relative paths declared in `spec.yaml.style_references` | no | use local style-lock checks only |
| Coordinate hints | `examples/<name>/coordinate_hints.yaml` | no | use declared panel bbox only; if both are absent, panel-local candidates become review-only |
| Perception pack | `examples/<name>/build/perception/` | no | use deterministic checker outputs only |
| Semantic invariants | `examples/<name>/semantic_invariants.yaml` | no | semantic-risk candidates become review-only |

The engine must not discover references, captions, papers, or hints outside
`workspace_root/examples/<name>` unless a fixture-relative path is explicitly
declared and resolves back inside the same fixture directory. Missing optional
inputs degrade scoring or apply eligibility; they do not trigger web search,
cross-repo lookup, or implicit manuscript inference.

Output schema:

```json
{
  "schema": "figure-agent.intent-model.v1",
  "fixture": "fig1",
  "panels": [
    {
      "id": "D",
      "role": "kinetic evidence",
      "bbox_pdf_cm": [0.0, 0.0, 1.0, 1.0],
      "semantic_claims": ["high-n sulfur trace", "low-n control trace"],
      "visual_priorities": ["curve hierarchy", "axis legibility"],
      "locked_invariants": ["axis direction", "material identity", "control meaning"],
      "allowed_edit_classes": ["label_offset", "whitespace", "style_normalization"]
    }
  ]
}
```

The first implementation builds this from existing fields and conservative
defaults only. It must not invent missing scientific claims. When a panel role or
claim is absent, the model records `unknown` and marks semantic-risk candidates
for that panel as `review_only`.

### Layer 2: Candidate Generator

The generator creates small alternate edits. It must produce several candidates
for eligible issues rather than a single "best guess."

Candidate families:

- label offset variants;
- callout/leader-line routing variants;
- panel whitespace and local spacing variants;
- line-weight tier normalization;
- palette/style-token normalization;
- title/axis hierarchy variants;
- SVG polish recipe variants only when the existing SVG route allows it.

Candidate sources:

- deterministic checker evidence from `build/*.json`;
- open critique findings that are already adjudicated as safe-mechanical;
- `quality-map` defects whose `patchability.state` is `safe_candidate`;
- style drift against `styles/polymer-paper-preamble.sty`;
- panel/reference mismatch summaries from existing critique evidence;
- declared operator request scope such as `--scope label-offsets`.

Forbidden candidate sources:

- raw LLM suggestions without a linked evidence id;
- unstaged edits outside the selected fixture;
- inferred manuscript claims not present in `spec.yaml`, `briefing.md`, or
  `caption.md`;
- accepted/golden/export approval blockers;
- visual preferences without a checkable target.

Each candidate must declare:

- target fixture, panel, and subregion;
- edit class;
- affected file;
- selector or line range;
- original content hash;
- expected visual improvement;
- semantic risks;
- rollback plan;
- required verification commands.

Output schema:

```json
{
  "schema": "figure-agent.candidate-set.v1",
  "fixture": "fig1",
  "base": {
    "tex_hash": "sha256:...",
    "status_hash": "sha256:...",
    "intent_model_hash": "sha256:..."
  },
  "candidates": [
    {
      "id": "CAND001",
      "target": {"panel": "D", "subregion": "axis_label"},
      "edit_class": "label_offset",
      "affected_files": [
        "examples/fig1/fig1.tex"
      ],
      "selector": {
        "kind": "line_range_with_hash",
        "path": "examples/fig1/fig1.tex",
        "start_line": 120,
        "end_line": 120,
        "original_hash": "sha256:..."
      },
      "operations": [
        {
          "kind": "replace_text",
          "path": "examples/fig1/fig1.tex",
          "original": "\\node at (1.0, 2.0) {label};",
          "replacement": "\\node at (1.0, 2.2) {label};"
        }
      ],
      "risk": "low",
      "expected_delta": ["improve label clearance"],
      "semantic_risks": [],
      "rollback": {
        "strategy": "reverse_operations"
      },
      "verification": {
        "required_commands": [
          "fig-agent compile fig1 --strict",
          "fig-agent status fig1 --json"
        ]
      },
      "apply_authority": "apply_eligible",
      "blocked_if": ["semantic_invariant_failed", "render_failed"]
    }
  ]
}
```

Candidate-set `apply_authority` is the pre-render authority ceiling. Rendering
and ranking may only preserve or downgrade it; they must never upgrade it.

Allowed `apply_authority` values:

- `apply_eligible`: candidate may be passed to `fig-agent apply-candidate
  <name> <candidate-id> --apply` after render/rank gates pass.
- `review_only`: candidate may be rendered and reviewed but must not be applied
  by the engine until a human rewrites or approves the edit scope.
- `rejected`: candidate is retained only as diagnostic evidence and cannot be
  applied.

### Layer 3: Render Sandbox

Candidates must render in isolation. The engine must not overwrite accepted
exports or user source while testing alternatives.

Sandbox output location:

```text
examples/<name>/build/candidates/<candidate_id>/
```

Allowed files:

- candidate source copy;
- compiled PDF/SVG/PNG;
- checker outputs;
- candidate manifest;
- score report.

The sandbox must record the source commit/hash, base artifact hashes, tool
versions, and candidate operations. Candidate artifacts are generated evidence,
not final exports.

### Layer 4: Fitness Scoring

A candidate is scored by hard gates first and soft scores second.

Hard gates:

- source selector still matches;
- compile succeeds;
- status does not regress freshness;
- deterministic checkers do not introduce new blockers;
- declared semantic invariants still pass;
- reference-locked structures are not changed;
- caption/spec claims remain supported;
- generated artifacts stay under the candidate sandbox;
- no accepted/golden/final-artifact state is changed.

Soft scores:

- text legibility;
- overlap/clearance improvement;
- panel balance;
- visual hierarchy;
- grayscale and colorblind robustness;
- reference faithfulness;
- cross-panel style consistency;
- human-review burden;
- before/after visual delta locality.

Score schema:

```json
{
  "schema": "figure-agent.candidate-score.v1",
  "candidate_id": "CAND001",
  "hard_gate_state": "pass",
  "hard_gate_failures": [],
  "scores": {
    "legibility": 0.82,
    "reference_faithfulness": 0.71,
    "semantic_preservation": 1.0,
    "review_burden": 0.18
  },
  "rank_score": 0.74,
  "verdict": "reviewable"
}
```

Allowed `hard_gate_state` values:

- `pass`: candidate may continue to soft scoring.
- `human_required`: candidate may be reviewed but cannot be marked
  `apply_eligible`.
- `rejected`: candidate cannot be applied and should not be ranked above
  reviewable candidates.

The first version may use deterministic approximations for many soft scores. It
should not pretend those approximations are human taste.

### Layer 5: Selection and Human Review

The engine may mark a candidate as `recommended` only when all are true:

- hard gates pass;
- edit class is safe-mechanical;
- visual delta is local;
- no semantic invariant is touched;
- improvement beats baseline by a configured margin;
- review burden is low.

Even then, applying the winner requires an explicit command. `recommended` means
"best review candidate," not "safe to mutate without operator action." Otherwise
the engine produces a human review packet.

Review packet contents:

- baseline render;
- candidate render;
- visual diff;
- changed source lines;
- score report;
- semantic invariant report;
- rollback command;
- recommended next action.

## Public Interfaces

CLI-first public interfaces:

```text
fig-agent intent <name> --json
fig-agent candidates <name> --json [--scope safe-mechanics]
fig-agent render-candidates <name> --candidate-set build/candidates/candidate_set.json
fig-agent rank-candidates <name> --candidate-set build/candidates/candidate_set.json --json
fig-agent review-candidate <name> <candidate-id> --json
fig-agent apply-candidate <name> <candidate-id> --apply
```

MCP tools mirror the same engine without becoming a separate workflow:

- `figure_agent_analyze_figure`
- `figure_agent_propose_improvements`
- `figure_agent_render_candidates`
- `figure_agent_rank_candidates`
- `figure_agent_prepare_human_review`
- `figure_agent_apply_candidate`

MCP mutation rules:

- analysis/proposal/ranking tools are read-only except sandbox artifacts;
- apply requires explicit apply semantics and returns verification evidence;
- MCP apply is disabled by default in packaged Cowork mode until the CLI apply
  path has benchmark evidence and an explicit operator opt-in flag;
- no MCP tool accepts arbitrary workspace paths;
- all fixture names resolve under `workspace_root/examples/<name>`.

## Data Contracts

### `candidate_manifest.json`

Every candidate sandbox writes:

```json
{
  "schema": "figure-agent.candidate-manifest.v1",
  "candidate_id": "CAND001",
  "fixture": "fig1",
  "base": {
    "source_commit": "sha1-or-unavailable",
    "tex_hash": "sha256:...",
    "status_hash": "sha256:...",
    "render_hash": "sha256:..."
  },
  "tool_versions": {
    "fig_agent": "0.11.x",
    "python": "3.x",
    "tex_engine": "lualatex ..."
  },
  "operations": [],
  "artifacts": {
    "pdf": "build/candidates/CAND001/render.pdf",
    "svg": "build/candidates/CAND001/render.svg",
    "png": "build/candidates/CAND001/render.png"
  },
  "verification": {
    "commands": [],
    "hard_gate_state": "pass"
  },
  "apply_authority": "apply_eligible",
  "effective_apply_authority": "apply_eligible"
}
```

Allowed manifest `verification.hard_gate_state` values are `pass`,
`human_required`, and `rejected`. The manifest must include both the candidate
set's pre-render `apply_authority` ceiling and the post-render
`effective_apply_authority`.

`effective_apply_authority` is the only mutation authority consumed by
`review-candidate`, `rank-candidates`, CLI apply, and MCP apply. It is computed
after render and hard gates:

- if `hard_gate_state == "pass"`, it may equal the candidate-set
  `apply_authority`;
- if `hard_gate_state == "human_required"`, it must be `review_only`;
- if `hard_gate_state == "rejected"`, it must be `rejected`.

An implementation must fail validation if a manifest claims
`effective_apply_authority: apply_eligible` while `hard_gate_state` is not
`pass`.

### `semantic_invariants.yaml`

Each fixture may declare invariants. Missing invariants reduce apply authority,
not analysis authority.

```yaml
schema: figure-agent.semantic-invariants.v1
fixture: fig1
invariants:
  - id: INV-D-AXIS-DIRECTION
    panel: D
    statement: Current axis increases upward and time increases rightward.
    protected_elements:
      - axis:d:x
      - axis:d:y
    allowed_edits:
      - label_offset
      - stroke_weight
  - id: INV-F-FORCE-DIRECTION
    panel: F
    statement: Coulomb repulsion arrow points away from the biased electrode.
    protected_elements:
      - arrow:f:coulomb
    allowed_edits:
      - label_offset
```

### `benchmark_case.yaml`

Benchmarks must include both positive and negative cases.

```yaml
schema: figure-agent.benchmark-case.v1
fixture: smoke_label_overlap
expected:
  candidate_count_min: 1
  hard_gate_failures: []
  improvement:
    overlap_count_delta_max: -1
  forbidden:
    - semantic_invariant_change
    - accepted_state_change
```

## Workflow

Recommended operator flow:

```text
fig-agent status <name> --json
fig-agent intent <name> --json
fig-agent candidates <name> --json
fig-agent render-candidates <name> --candidate-set build/candidates/candidate_set.json
fig-agent rank-candidates <name> --candidate-set build/candidates/candidate_set.json --json
fig-agent review-candidate <name> CAND001 --json
fig-agent apply-candidate <name> CAND001 --apply
fig-agent compile <name> --strict
fig-agent status <name> --json
fig-agent closeout <name> --json
```

The engine must stop early when:

- source is stale;
- critique/adjudication is stale and required;
- accepted/golden approval is the first blocker;
- semantic invariants are missing for a semantic-risk edit;
- no candidate beats baseline by the minimum margin.

## Improvement Fitness

The initial fitness function should be explicit and conservative.

Hard gate state has priority:

```text
failed hard gate -> rejected
human-required hard gate -> review only
all hard gates pass -> score soft metrics
```

Suggested first score:

```text
rank_score =
  0.25 * legibility_delta
  + 0.20 * overlap_clearance_delta
  + 0.15 * panel_balance_delta
  + 0.15 * reference_faithfulness_delta
  + 0.15 * style_consistency_delta
  + 0.10 * grayscale_colorblind_delta
  - 0.20 * review_burden
```

Rules:

- Do not use the score to override a hard gate.
- Do not compare unrelated fixtures by score until benchmark calibration exists.
- Do not treat rank score as publication readiness.
- Report confidence as `low`, `medium`, or `high`; do not expose fake precision.

## Safety Policy

Non-explicit mutation is forbidden. The engine must never mutate source during
intent, candidate generation, rendering, ranking, or review. The only
source-mutating surface is:

```text
fig-agent apply-candidate <name> <candidate-id> --apply
```

That command may proceed only when the selected rendered manifest has
`effective_apply_authority: apply_eligible`, the candidate is fresh against
current source hashes, and render/rank gates have passed.

Apply eligibility is forbidden for:

- scientific topology changes;
- arrow direction changes;
- material identity changes;
- axis semantics changes;
- data curve shape changes unless generated from declared data;
- caption claim changes;
- accepted/golden/final artifact state changes;
- any edit whose visual diff is non-local.

Apply eligibility is limited to:

- moving a label within a declared panel bbox;
- increasing clearance between label and line;
- replacing ad hoc color/stroke literals with existing style macros;
- small whitespace normalization inside a panel;
- local SVG polish recipe application with semantic backport unchanged.

When in doubt, produce a review packet and stop.

## Benchmark Suite

The engine needs a benchmark suite before claims of "draws better" are allowed.

Minimum benchmark set:

- 5 synthetic fixtures with known mechanical defects;
- 5 negative fixtures where the correct answer is no patch;
- 3 real non-fig1 manuscript fixtures;
- 1 frozen fig1 regression fixture where only review packets are allowed;
- 1 colorblind/grayscale stress fixture;
- 1 caption/spec mismatch fixture.

Benchmark metrics:

- candidate generation recall on known safe defects;
- false-positive rate on semantic-risk fixtures;
- compile success after apply;
- deterministic blocker delta;
- human review packet completeness;
- sandbox containment;
- runtime budget.

Release claim threshold for first version:

- at least 80% recall on synthetic safe defects;
- 0 `apply_eligible` candidates on semantic-risk negative fixtures;
- 100% sandbox containment;
- no accepted/golden mutation without explicit human action;
- at least one real fixture produces a reviewable candidate that a human can
  accept or reject from evidence.

## Implementation Phases

### Phase 1: Intent and Invariant Model

Deliver:

- `scripts/figure_intent_model.py`
- `fig-agent intent`
- schema tests for panel roles, allowed edit classes, and missing-invariant
  authority downgrade.

Exit criteria:

- read-only;
- deterministic JSON;
- no generated files;
- works when `caption.md` is absent;
- refuses workspace-escaping paths.

### Phase 2: Candidate Generation

Deliver:

- `scripts/candidate_generator.py`
- `fig-agent candidates`
- candidate schemas for label offset, style-token normalization, and whitespace
  balancing.

Exit criteria:

- candidates contain selectors and original hashes;
- no source mutation;
- no candidate for accepted/golden gate blockers;
- no semantic-risk edit is marked `apply_eligible`.

### Phase 3: Render Sandbox

Deliver:

- `scripts/candidate_render.py`
- `fig-agent render-candidates`
- build sandbox under `build/candidates/`.

Exit criteria:

- candidate renders do not overwrite `build/<name>.pdf` or `exports/`;
- failed renders produce structured errors;
- manifests include base hashes and tool versions.

### Phase 4: Ranking and Review Packets

Deliver:

- `scripts/candidate_rank.py`
- `scripts/candidate_review_packet.py`
- `fig-agent rank-candidates`
- `fig-agent review-candidate`

Exit criteria:

- hard gates dominate soft scores;
- review packet includes before/after/diff/source/risk/rollback;
- no unsupported metric is presented as taste truth.

### Phase 5: Explicit Apply

Deliver:

- `fig-agent apply-candidate`
- integration with existing `quality_patch_apply.py` for operation validation,
  stale-plan checks, rollback materialization, and verification result shape;
- rollback and stale-candidate checks.

Exit criteria:

- explicit `--apply` required;
- post-apply compile/status commands are required;
- stale candidate cannot apply;
- semantic invariant failure blocks apply.

### Phase 6: MCP Facade

Deliver:

- MCP tools listed in Public Interfaces;
- resource descriptors for candidate renders and review packets;
- no raw binary streaming by default.

Exit criteria:

- MCP startup remains side-effect-free;
- tools use the same runtime path contract as CLI;
- MCP tool responses include schema, success, error, artifacts, and duration.

### Phase 7: Benchmark and Dogfood

Deliver:

- benchmark fixtures;
- benchmark runner;
- dogfood report on one non-fig1 real fixture;
- no fig1 source mutation unless explicitly requested.

Exit criteria:

- benchmark thresholds pass;
- dogfood evidence records at least one useful reviewable candidate or a precise
  reason no candidate is safe.

## Testing Strategy

Focused tests:

- intent model path safety and absent-caption behavior;
- semantic invariant parsing and authority downgrade;
- candidate selector exact-match behavior;
- stale candidate refusal;
- render sandbox containment;
- rank hard-gate precedence;
- read/rank/review commands never mutate source;
- packaged Cowork MCP apply refuses unless explicit operator opt-in is enabled;
- candidate schemas include affected file, selector, original hash, semantic
  risk, rollback, and verification fields;
- manifest schemas include source commit, base hashes, tool versions,
  pre-render `apply_authority`, and post-render `effective_apply_authority`;
- hard-gate tests prove `human_required` downgrades
  `effective_apply_authority` to `review_only`;
- missing reference, coordinate hint, or perception pack degrades to local-only
  analysis or review-only without leaving the fixture root;
- MCP envelope schema;
- benchmark negative cases.

Integration tests:

```text
fig-agent intent smoke_candidate_demo --json
fig-agent candidates smoke_candidate_demo --json
fig-agent render-candidates smoke_candidate_demo --candidate-set build/candidates/candidate_set.json
fig-agent rank-candidates smoke_candidate_demo --candidate-set build/candidates/candidate_set.json --json
fig-agent review-candidate smoke_candidate_demo CAND001 --json
fig-agent apply-candidate smoke_candidate_demo CAND001 --apply
fig-agent compile smoke_candidate_demo --strict
fig-agent status smoke_candidate_demo --json
```

Release checks:

```text
uv run pytest -q
uv run ruff check .
python3 scripts/release_gate.py --output dist/cowork --json
```

If the active Python test environment cannot see host dependencies such as
PyYAML or Pillow, tests must either run with the documented host dependency path
or be refactored so dependency-light contract tests do not import heavy modules.
Do not hide dependency failures by weakening production code.

## Open Design Decisions

These are intentionally decided for the first implementation:

- Candidate search starts with deterministic local variants, not LLM-generated
  free-form rewrites.
- Image-generation remains outside the core.
- The first benchmark uses fixed local fixtures, not web reference discovery.
- MCP tools do not accept workspace paths.
- Missing semantic invariants downgrade apply authority to review-only.
- Ranking scores are fixture-local and not publication-grade.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Candidate search creates too many variants | cap candidates per defect and per fixture |
| Scoring becomes fake taste | label soft metrics as approximations; keep human gate |
| Semantic drift | invariant registry, caption/spec checks, hard gate precedence |
| Sandbox leaks into exports | allowlist generated paths and test containment |
| MCP becomes a second engine | MCP only calls CLI/module contracts |
| Benchmarks overfit synthetic cases | include real non-fig1 fixtures and negative cases |
| Review burden increases | rank by review burden and stop when margin is weak |

## Definition of Done

The feature is done when:

- CLI surfaces exist and are documented.
- MCP tools expose the same workflow without extra mutation authority.
- At least one candidate family can improve a known visual defect end to end.
- Negative semantic-risk fixtures are never marked `apply_eligible`.
- Candidate artifacts are sandboxed and reproducible.
- Review packets are sufficient for a human to accept or reject without reading
  the whole codebase.
- Benchmarks pass the first-version thresholds.
- A real fixture dogfood run records whether the system found a useful candidate
  or correctly stopped.

## Review Log

This section records the spec review passes performed before implementation
planning.

### Review Pass 1: Scope and Product Boundary

Finding: The initial idea could sprawl into image generation, literature
retrieval, and autonomous art direction.

Resolution: The spec explicitly keeps image generation and reference search out
of core scope, defines candidate search as local deterministic variants first,
and keeps human authority over final taste and accepted/golden state.

### Review Pass 2: Safety and Semantic Drift

Finding: A system that optimizes visual quality can silently change scientific
meaning.

Resolution: The spec adds semantic invariants, hard-gate precedence, forbidden
apply-eligible classes, caption/spec support checks, and review-only downgrade
when invariants are missing.

### Review Pass 3: Measurability

Finding: "Draws better" is too vague without a benchmark.

Resolution: The spec adds benchmark fixtures, concrete threshold targets, and
fitness components that separate hard deterministic gates from soft visual
scores.

### Review Pass 4: MCP Boundary

Finding: MCP could accidentally become a second workflow engine or gain broader
mutation authority than CLI.

Resolution: The spec makes CLI the source of truth, defines MCP as a facade,
forbids workspace path arguments, and requires MCP tools to follow the same
schema and mutation rules.

### Review Pass 5: Implementation Slicing

Finding: Building all layers at once would be too large and hard to verify.

Resolution: The spec splits work into seven phases with explicit exit criteria,
starting with read-only intent modeling and ending with benchmark dogfood.

### Review Pass 6: External Reviewer Contract Audit

Finding: A read-only reviewer found four implementation-safety gaps:
`auto-apply` terminology conflicted with explicit apply semantics; the candidate
schema omitted provenance fields required for stale checks and rollback; hard
gate schemas lacked a `human_required` state; fixture-local reference inputs were
underspecified.

Resolution: The spec now uses `apply_eligible`, `review_only`, and `rejected`
instead of `auto-apply`; candidate sets include base hashes, affected files,
selectors, original hashes, semantic risks, rollback, verification, and
`apply_authority`; score and manifest contracts define `pass`,
`human_required`, and `rejected`; input contracts require all optional
references and hints to be fixture-local and to degrade capability rather than
trigger outside discovery.

### Review Pass 7: Follow-Up Authority and Provenance Review

Finding: The second reviewer pass found that manifest provenance still omitted
source/tool version metadata and that candidate-set `apply_authority` could drift
from post-render hard-gate results.

Resolution: The manifest schema now includes `source_commit`, base hashes, and
`tool_versions`. The spec separates pre-render `apply_authority` from post-render
`effective_apply_authority`; only the latter can be consumed by review, ranking,
CLI apply, or MCP apply. `human_required` hard gates must downgrade effective
authority to `review_only`, and `rejected` hard gates must downgrade it to
`rejected`.
