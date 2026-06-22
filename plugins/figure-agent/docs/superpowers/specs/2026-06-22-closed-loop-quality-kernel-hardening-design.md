# Closed-Loop Quality Kernel Hardening Design

Status: Draft for hardening review
Date: 2026-06-22
Owner: figure-agent
Target release: post-0.11.x quality loop hardening

## Summary

figure-agent already behaves like a conservative quality kernel: it can compile,
export, detect clashes, account for audit evidence, propose bounded candidates,
render candidate sandboxes, expose closeout checks, and summarize quality memory.
The current weakness is not that the system has no eyes. The weakness is that
the loop from evidence to action is not closed tightly enough:

```text
detector evidence -> actionable defect -> multiple safe candidates
  -> candidate render/evaluation -> candidate-specific ranking
  -> explicit apply/verification -> memory outcome -> better next proposal
```

Today the system often sees many defects but moves only one coordinate, can mark
benchmark detector movement as passed without rendering candidates, can score a
candidate without candidate-specific visual evidence, and can preserve accepted
or PASS states while closeout remains stale or blocked.

This spec hardens the whole loop. It does not replace the existing focused specs
for quality maps, candidate rendering, evidence-gated apply, memory, or benchmark
engines. It binds them into one stricter product contract and closes the gaps
observed during dogfood.

The goal is not autonomous taste. The goal is a local, measurable, evidence-bound
quality kernel that reliably converts narrow mechanical figure defects into
reviewable, rendered, ranked, explicitly accepted, verified improvements.

## Current Evidence Baseline

Observed on `fig1_overview_v2_pair_001_vault` and the smoke benchmark:

- `figure_agent_doctor` reports the source bundle, dependencies, and workspace as
  healthy.
- Dogfood status reports `accepted: true`, audit evidence present, and
  `publication_gate_state: PASS`, while also reporting `workflow_ready: false`,
  `render_state: STALE`, `critique_state: STALE`, and `export_state:
  TRACKED_GOLDEN`.
- Audit evidence reports 134 detector-linked defects, including 95
  `undeclared_geometry` candidates, 41 `visual_clash` candidates with 38 linked
  defects and 3 accepted false positives, and 1 `label_path` candidate.
- `quality-map` emits many `safe_candidate` text-overlap defects with line-range
  selectors and mechanical TikZ coordinate-adjust suggestions.
- `propose-improvements` emits only `CAND001`, targeting `QD001`, with
  `target.panel: unknown`, `target.subregion: label-a`, and one `replace_text`
  operation that changes `(3.95, 5.65)` to `(4.05, 5.65)`.
- `propose-patch` emits exactly one operation because `build_quality_patch_plan`
  stops after the first usable defect.
- `candidate_generator.build_candidate_set()` emits at most one default
  candidate because `_defect_target_line()` returns the first supported safe
  ledger defect.
- `build_family_candidates()` generally emits a single candidate per supported
  canonical/family path.
- `candidate_panel_model` can expose panel selectors. Panel A exposes 31
  selectors, but generated candidates still lose panel/subregion attribution.
- Smoke benchmark completes five fixtures and reports detector movements as
  passed, while `candidate_count`, `rendered_count`, and `ranked_count` are zero
  and `render_success_rate` is zero.
- Dogfood benchmark reports one candidate and one ranked result, but
  `render_mode: none`, `rendered_count: 0`, and `render_success_rate: 0.0`.
- `quality_benchmark._run_fixture()` does not actually render candidates. If
  render is requested, it reports `requested_not_implemented`.
- `candidate_rank.score_manifest()` can accept render evidence, memory, and
  detector inputs, but benchmark ranking currently uses synthetic manifests,
  fixture-level detector movement, and no candidate render manifests.
- `quality_memory_index` reports memory mostly under
  `unknown:unknown:unknown`; `eligible_prior_count` remains zero because useful
  panel/family/outcome metadata is missing or too sparse.
- Closeout/apply readiness can surface contradictory operator states such as
  `candidate_set_missing_candidate` and `already_applied`, while compile,
  critique, adjudication, and export remain stale or blocked.
- `quality_patch_apply` applies a patch and records required verification
  commands, but it does not run those commands itself and currently records the
  outcome as `verification_failed` immediately after apply.

These facts define the baseline. A future implementation is not allowed to claim
quality-loop improvement unless these gaps are measurably reduced.

## Product Principle

figure-agent should improve by preserving and acting on evidence, not by becoming
bolder.

Good behavior:

- "There are 12 safe text-overlap defects; 10 have source selectors, panel ids,
  and supported edit families; 10 candidates were rendered; 7 reduced the target
  detector without new blockers; 2 require human review; 1 failed compile."
- "This candidate ranks high because its own render manifest shows compile,
  export, crop, and candidate-specific detector deltas."
- "This accepted candidate cannot be applied because the source hash changed
  since render."
- "Memory has three improved label-offset outcomes for Panel C subregions and
  adds a bounded soft ranking prior; apply authority is unchanged."

Bad behavior:

- "134 defects exist, so emit one first-match coordinate nudge."
- "Detector movement passed in a benchmark that rendered no candidates."
- "This looks nicer, apply it."
- "Accepted/PASS means ready even though compile, critique, or export is stale."
- "Memory or LLM review upgrades a candidate to apply-eligible."

## Goals

1. Make detector evidence actionable by preserving panel, selector, freshness,
   defect class, severity, and safe-edit metadata through the whole loop.
2. Replace first-match candidate generation with complete bounded enumeration
   over supported safe defects.
3. Render and evaluate candidates in benchmarks when render is requested, with
   honest states when dependencies are missing.
4. Rank candidates only from evidence bound to the same candidate, or explicitly
   mark lower-confidence fixture-level priors.
5. Make apply and closeout states unambiguous, freshness-bound, and impossible to
   confuse with stale accepted/PASS artifacts.
6. Activate memory only from attributed candidate outcomes and keep memory as a
   bounded soft prior.
7. Integrate host-mediated semantic review as a local report and blocking signal,
   not as an automatic editor or authority bypass.
8. Prove progress with smoke and dogfood metrics before expanding candidate
   families.

## Non-Goals

- Do not create an autonomous figure designer.
- Do not delete, weaken, or bypass safety gates.
- Do not use LLM prompting as the primary repair mechanism.
- Do not call external vision, embedding, search, image-generation, or cloud APIs
  from plugin code.
- Do not train a model or create hidden global learning state.
- Do not mutate source from MCP by default.
- Do not auto-apply from ranking score, detector score, memory prior, or LLM
  verdict alone.
- Do not change accepted, tracked-golden, release, or publication state without
  explicit human approval and current hashes.
- Do not perform broad semantic rewrites, claim rewrites, topology rewrites, or
  manuscript-meaning edits in the mechanical loop.
- Do not turn fig1 into a mutable training corpus. It may be a named dogfood or
  benchmark fixture only.

## System Model

The loop has five subsystems.

| Subsystem | Owns | Must not own |
|---|---|---|
| Eyes | Detector reports, defect ledger, panel/selector attribution, freshness, objective deltas | Taste, acceptance, scientific truth |
| Hands | Candidate enumeration, bounded operations, render sandboxes, explicit apply, rollback | Broad redesign, semantic rewrite, golden promotion |
| Operations | State machine, benchmark, ranking, closeout, next action, gates | Hidden mutation, stale success claims |
| Memory | Local event logs, outcome aggregation, bounded soft priors | Apply authority, hard-gate changes, cross-project training |
| Semantic Reviewer | Host-written local reports about semantic/layout risk | Direct source edits, deterministic gate overrides, external service calls |

Each subsystem emits structured evidence. Downstream subsystems may consume only
fresh, hash-bound evidence or must explicitly downgrade confidence.

## Required Shared State Vocabulary

All new JSON contracts in this hardening slice must use these state names where
they apply.

### Evidence Freshness

- `fresh`: inputs and hashes match the current source/build context.
- `stale`: an input hash, source hash, candidate hash, or artifact hash no longer
  matches.
- `missing`: an expected artifact does not exist.
- `invalid`: artifact exists but fails schema, path, hash, or parse validation.
- `not_required`: the contract does not require this artifact for the current
  fixture/candidate.

### Automation Readiness

- `pass`: deterministic gate passed.
- `needs_action`: deterministic action is required and can be run safely.
- `blocked`: progress requires human, host, missing dependency, stale repair, or
  unsupported work.
- `not_required`: gate does not apply.

### Candidate Render Mode

- `not_requested`: benchmark or command did not request render.
- `rendered`: all selected candidates reached render manifests or documented
  per-candidate failure manifests.
- `dependency_missing`: render was requested but host tools are missing.
- `blocked`: render was requested but freshness, path, symlink, or contract gates
  blocked execution before candidate manifests could be produced.
- `failed`: render ran and produced one or more hard failures.

`requested_not_implemented` is forbidden after this spec is implemented. If a
feature is not implemented, the command must fail closed with a diagnostic rather
than pretending a benchmark completed normally.

### Candidate Outcome

- `improved`: candidate-specific evidence shows target improvement and no new
  hard blocker.
- `neutral`: candidate rendered but did not materially improve or regress.
- `regressed`: candidate created a new blocker, worsened the target metric, or
  failed a hard gate after previously valid inputs.
- `blocked_by_hard_gate`: deterministic gate blocked.
- `blocked_by_human_gate`: human or host review is required.
- `rolled_back`: candidate was applied and then reverted through recorded
  rollback evidence.
- `unknown`: outcome cannot be inferred from current evidence.

`unknown` is allowed as a diagnostic state. It must not feed priors or success
metrics.

## Eyes: Perception And Defect Ledger Contract

### Problem

The system already detects many visual and geometry issues. The missing layer is
actionability. A detector candidate is not actionable until it can be linked to a
current source selector, panel/subregion, edit family, confidence, and freshness
state.

### Required Defect Schema

Every normalized defect emitted by `quality-map` or any successor ledger must
include:

```json
{
  "schema": "figure-agent.quality-defect.v1",
  "id": "QD001",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "source": "deterministic_audit",
  "defect_class": "text_overlap",
  "severity": "action",
  "owner": "tool",
  "target": {
    "panel": "A",
    "subregion": "label_cluster_top_left",
    "object_kind": "label_endpoint",
    "confidence": "exact"
  },
  "affected_files": ["examples/<name>/<name>.tex"],
  "selector_hint": {
    "kind": "line_range_with_hash",
    "value": "414:414",
    "source_hash": "sha256:...",
    "selector_text_hash": "sha256:..."
  },
  "evidence": [
    {
      "uri": "figure://<name>/audit/undeclared-geometry",
      "node_id": "UG002",
      "artifact_path": "build/undeclared_geometry.json",
      "artifact_sha256": "sha256:..."
    }
  ],
  "freshness": {
    "state": "fresh",
    "source_hashes": {"examples/<name>/<name>.tex": "sha256:..."},
    "audit_evidence_graph_hash": "sha256:...",
    "status_input_hash": "sha256:...",
    "critique_input_hash": "sha256:..."
  },
  "patchability": {
    "state": "safe_candidate",
    "edit_families": ["label_offset"],
    "blocked_codes": [],
    "reasons": ["mechanical_text_overlap"],
    "policy_version": "figure-agent.quality-patch-policy.v2"
  },
  "source_fingerprint": "sha256:..."
}
```

Existing ledger fields may be preserved, but missing `target.panel`,
`target.subregion`, `selector_hint.source_hash`, or `freshness.state` must be
counted as an actionability gap.

### Perception Metrics

Every `quality-map` result must expose a `metrics` object:

```json
{
  "defect_count": 134,
  "safe_candidate_defect_count": 12,
  "candidate_supported_defect_count": 10,
  "unsupported_safe_defect_count": 2,
  "unknown_panel_defect_count": 0,
  "unknown_subregion_defect_count": 1,
  "missing_selector_hash_count": 0,
  "stale_detector_evidence_count": 0,
  "detector_missing_evidence_count": 0,
  "accepted_false_positive_count": 3
}
```

Acceptance thresholds for the first hardening release:

- `unknown_panel_defect_count == 0` for any defect emitted as
  `safe_candidate`.
- `missing_selector_hash_count == 0` for any defect emitted as
  `safe_candidate`.
- `stale_detector_evidence_count == 0` before candidate generation proceeds.
- `candidate_supported_defect_count + unsupported_safe_defect_count ==
  safe_candidate_defect_count`.

### Eyes Failure Modes

The perception layer must fail closed or downgrade actionability for:

- detector report missing;
- detector report stale against source, build, crop, or critique input;
- malformed detector report;
- selector outside current source;
- source hash mismatch;
- path escape or symlink in any evidence path;
- detector identifies a taste/style preference with no safe mechanical edit;
- conflicting detector evidence for the same source object;
- unknown panel or subregion on an otherwise safe defect;
- detector candidate accepted as false positive.

No downstream candidate may be generated from a defect in one of these failure
modes unless the candidate records a refusal rather than an operation.

## Hands: Candidate, Patch, Render, And Apply Contract

### Problem

The current default hands are first-match. This loses most detector evidence and
makes ranking, memory, and benchmarks meaningless. A closed-loop system must
enumerate bounded safe work, not select the first offsettable line.

### Candidate Enumeration Rule

For every fresh `safe_candidate` defect:

1. If at least one supported edit family can produce a bounded operation, emit at
   least one candidate.
2. If no supported edit family can produce a bounded operation, emit a refusal
   with a stable reason code.
3. Never silently skip a fresh `safe_candidate` defect.

Default candidate generation must no longer return after the first target. Stable
candidate ids are assigned after sorting by:

1. severity rank;
2. panel id;
3. source file path;
4. selector start line;
5. source fingerprint;
6. edit family;
7. variant id.

Example ids:

```text
CAND001
CAND002
CAND003
```

Candidate ids are stable within the same source and ledger hashes. If the ledger
or source changes, stale candidate sets must be blocked rather than reusing old
ids as if they still describe the same patch.

### Candidate Set Metrics

`fig-agent candidates <name> --json` must expose:

```json
{
  "metrics": {
    "safe_candidate_defect_count": 12,
    "candidate_count": 18,
    "candidate_defect_coverage": 1.0,
    "refusal_count": 2,
    "candidate_with_panel_count": 18,
    "candidate_with_family_count": 18,
    "candidate_with_source_hash_count": 18,
    "variant_count": 6
  }
}
```

First release thresholds:

- `candidate_defect_coverage == 1.0` for supported synthetic fixtures.
- `candidate_with_panel_count == candidate_count`.
- `candidate_with_family_count == candidate_count`.
- `candidate_with_source_hash_count == candidate_count`.
- Existing real fixtures may have refusals, but every refusal must have a reason.

Metric definitions:

- `candidate_defect_coverage =
  distinct_supported_safe_defects_with_at_least_one_candidate /
  candidate_supported_defect_count`.
- `refusal_coverage =
  distinct_unsupported_safe_defects_with_refusal /
  unsupported_safe_defect_count`.
- `candidate_supported_defect_count` excludes stale, missing-evidence,
  false-positive, unknown-panel, and unsupported-family defects.
- Refused, stale, blocked, or unsupported defects must be reported in explicit
  denominators and must not silently disappear from rates.

### Required Candidate Fields

Every candidate must include:

```json
{
  "id": "CAND001",
  "candidate_hash": "sha256:...",
  "source_defect": {
    "id": "QD001",
    "source_fingerprint": "sha256:...",
    "defect_class": "text_overlap"
  },
  "target": {
    "panel": "A",
    "subregion": "label_cluster_top_left",
    "object_kind": "label_endpoint"
  },
  "edit_family": "label_offset",
  "edit_class": "label_offset",
  "variant": {
    "id": "dx_plus_0_10cm",
    "parameters": {"dx_cm": 0.10, "dy_cm": 0.0}
  },
  "apply_authority": "review_only",
  "risk": "low",
  "selectors": [
    {
      "kind": "tex_selector.v1",
      "path": "examples/<name>/<name>.tex",
      "line_start": 414,
      "line_end": 414,
      "source_hash": "sha256:...",
      "selector_text_hash": "sha256:...",
      "panel": "A"
    }
  ],
  "operations": [
    {
      "kind": "replace_text",
      "path": "examples/<name>/<name>.tex",
      "source_sha256": "sha256:...",
      "original": "  (3.95, 5.65) -- (6.60, 5.65);",
      "replacement": "  (4.05, 5.65) -- (6.60, 5.65);"
    }
  ],
  "blocked_if": [
    "source_hash_mismatch",
    "render_failed",
    "semantic_invariant_failed"
  ],
  "rollback": {"strategy": "reverse_operations"},
  "verification": {
    "required_commands": [
      "fig-agent compile <name> --strict",
      "fig-agent status <name> --json"
    ]
  }
}
```

### Supported Edit Families In The First Hardening Release

The first release may support only these families:

- `label_offset`: move a label anchor or endpoint by a bounded distance.
- `text_overlap_clearance`: move a text-bearing node or endpoint away from a
  detector-proven clash by a bounded distance.
- `leader_line_adjustment`: reroute or shorten a connector when the source line
  has an exact selector and the edit is bounded.

Any new edit family requires:

- at least one synthetic fixture;
- one positive and one refusal test;
- render/evaluate coverage;
- rollback coverage;
- refusal behavior on stale source;
- documentation in this spec or a successor spec.

### First Release Variant Bounds

The first hardening release must use a fixed variant catalog. Implementations may
not synthesize arbitrary offsets, arbitrary reroutes, or detector-dependent
unbounded moves.

Allowed first-release variants:

- `label_offset`:
  - candidate deltas: `dx_cm,dy_cm` in `{-0.10, 0.00, +0.10}` excluding
    `(0.00, 0.00)`;
  - maximum absolute move per operation: `0.15cm`;
  - may move only the selected label anchor, label endpoint, or text node
    coordinate selected by the source defect.
- `text_overlap_clearance`:
  - move only along the detector-provided separation axis;
  - candidate deltas: `0.05cm`, `0.10cm`, `0.15cm`;
  - maximum absolute move per operation: `0.15cm`;
  - if the detector cannot provide a separation axis, emit a refusal rather than
    guessing a direction.
- `leader_line_adjustment`:
  - endpoint-only adjustment;
  - maximum endpoint move: `0.15cm`;
  - no change to connected semantic target, arrow direction, or graph topology;
  - no insertion of new connector segments in the first release.

Candidate budget:

- Default materialization may cap rendering work through `--max-candidates`, but
  a capped result must report `truncated: true` and the truncation reason.
- Truncated candidate sets may be used for interactive preview.
- Truncated candidate sets cannot satisfy coverage, benchmark, release, or
  dogfood acceptance gates.
- Candidate generation must remain deterministic under the same source hashes,
  ledger hashes, family catalog, and cap.

### Automatic Edit Invariants

Every automatic operation must satisfy all conditions:

- The target path is fixture-local and not a symlink.
- The operation changes at most one fixture source file in MVP.
- The source hash matches at operation time.
- The original text appears exactly once for `replace_text` operations.
- The edit is bounded by family-specific numeric limits.
- The edit does not change scientific text, labels, claims, units, topology,
  reaction meaning, axis meaning, or manuscript assertions.
- The edit does not write generated exports, accepted/golden artifacts, or files
  outside the allowed sandbox/apply surfaces.
- The candidate has rollback instructions before apply.
- Compile/status verification is required after apply.
- Human acceptance is required before source mutation.

If any invariant fails, the candidate is `blocked` or `human_required`. The
system must not add fallback code that attempts a broader edit.

### Patch Plan Behavior

`fig-agent propose <name> --json` may remain a single-operation patch planner
only if it is explicitly documented as a narrow convenience command. The closed
loop must not depend on `propose` for coverage. The coverage path is:

```text
quality-map -> candidates -> render-candidates -> rank-candidates
```

If `propose` is upgraded, it must either:

- produce one plan per selected defect, with explicit selection arguments; or
- produce a batch plan with per-operation gates and rollback.

It must not silently choose the first safe defect without reporting skipped safe
defects.

### Render Sandbox Contract

Candidate rendering must reuse the existing sandbox contract:

```text
examples/<name>/build/candidates/<candidate_id>/
```

Allowed writes:

- `candidate_manifest.json`
- `render_manifest.json`
- sandbox source copies
- sandbox compile/export/crop/evaluation artifacts

Forbidden writes:

- fixture source during render;
- fixture `exports/` during render;
- accepted/golden artifacts;
- files outside the fixture or workspace `.scratch` allowlist.

## Operations: Benchmark, Ranking, Status, And Closeout

### Benchmark Render Requirement

`fig-agent benchmark-run --suite <suite> --render --json` must execute the
candidate render path or fail with a precise state. It may not report a completed
render benchmark with `rendered_count: 0` when candidates exist and dependencies
are available.

Required behavior:

1. Load benchmark contract.
2. Build quality map and candidate set.
3. If render is not requested, report `render_mode: not_requested`.
4. If render is requested, call the same candidate rendering implementation used
   by `fig-agent render-candidates`.
5. For each candidate, write or collect a candidate manifest and, when requested,
   a render manifest.
6. Compute ranking from candidate-specific manifests and render evidence.
7. Report dependency failures as `dependency_missing`, not as success.
8. Never mutate fixture source or exports during benchmark render.

### Benchmark Metrics

Every benchmark result must include:

```json
{
  "candidate_count": 10,
  "safe_candidate_defect_count": 8,
  "safe_candidate_coverage": 1.0,
  "refusal_count": 2,
  "render_mode": "rendered",
  "rendered_count": 10,
  "render_success_rate": 0.9,
  "ranked_count": 10,
  "candidate_specific_rank_rate": 1.0,
  "new_blocker_count": 0,
  "stale_evidence_block_count": 0,
  "mean_rank_score": 0.72,
  "regression_count": 0
}
```

Smoke acceptance thresholds:

- `candidate_count > 0` for each smoke fixture designed to exercise a supported
  edit family.
- `rendered_count == candidate_count` when dependencies exist and `--render` is
  requested.
- `candidate_specific_rank_rate == 1.0` for rendered candidates.
- `new_blocker_count == 0`.
- `regression_count == 0`.

Render dependency gate:

- Render-capable smoke and dogfood gates must run in a declared render-enabled
  environment.
- The benchmark suite must expose `render_dependency_probe` with tool names,
  versions when available, and pass/fail state.
- In render-enabled CI, `dependency_missing` is a gate failure.
- Outside render-enabled CI, `dependency_missing` is an honest blocked diagnostic
  and must not be reported as benchmark PASS.
- A benchmark that did not render because of missing dependencies must not update
  memory priors, candidate success counts, or release confidence metrics.

Dogfood acceptance thresholds:

- `candidate_count >= 5` or explicit refusals explain every unsupported safe
  defect group.
- `unknown panel` candidates are zero for safe candidates.
- `render_success_rate >= 0.8` when dependencies exist.
- The best-ranked candidate has render evidence bound to the same `candidate_id`.

Metric definitions:

- `safe_candidate_coverage =
  distinct_supported_safe_defects_with_at_least_one_candidate /
  candidate_supported_defect_count`.
- `render_success_rate =
  candidates_with_render_manifest_status_success_or_reviewable /
  render_requested_candidate_count`.
- `candidate_specific_rank_rate =
  ranked_candidates_with_rank_basis_candidate_specific_render /
  ranked_rendered_candidates`.
- `new_blocker_count` counts blockers introduced by the candidate render/evaluate
  stage, not pre-existing baseline blockers.
- `stale_evidence_block_count` counts candidates blocked because their source,
  candidate set, candidate manifest, render manifest, detector report, or
  acceptance artifact is stale.
- Blocked, stale, refused, dependency-missing, and render-failed candidates must
  be reported in separate denominators and must not be hidden by success rates.

### Candidate-Specific Ranking

Ranking must bind every score to evidence for the same candidate:

```json
{
  "candidate_id": "CAND001",
  "candidate_hash": "sha256:...",
  "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
  "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
  "rank_basis": "candidate_specific_render",
  "evidence": {
    "positive": ["rendered_before_after_available"],
    "negative": []
  },
  "scores": {
    "legibility": 0.7,
    "reference_faithfulness": 0.0,
    "semantic_preservation": 1.0,
    "review_burden": 0.4,
    "memory_prior": 0.0,
    "detector_delta": 0.15
  },
  "rank_score": 0.65
}
```

Ranking rules:

- A rendered candidate may receive positive render evidence.
- An unrendered candidate may not receive positive render evidence.
- Fixture-level detector movement must be marked `rank_basis:
  fixture_level_prior` and capped at a small soft contribution.
- Memory may adjust only a bounded soft score.
- Ranking cannot change `hard_gate_state`, `apply_authority`, or
  `effective_apply_authority`.
- A candidate with stale manifest, stale render, or source hash mismatch must not
  rank above a fresh rendered candidate.

### Status And Closeout Hardening

Status must distinguish:

- accepted historical state;
- current workflow readiness;
- current release readiness;
- current golden readiness;
- current final artifact readiness;
- stale accepted/golden/export evidence.

Rules:

- `accepted: true` means a human previously accepted a fixture state. It does not
  imply current render, critique, export, candidate apply, or closeout freshness.
- `publication_gate_state: PASS` means no publication-gate failures were reported
  for the evaluated inputs. It does not imply `workflow_ready` or
  `release_ready` when inputs are stale.
- `workflow_ready` must be false if render, critique, adjudication, or required
  candidate apply evidence is stale.
- `release_ready` must be false if tracked golden export requires current
  acceptance or if final artifacts are stale.
- Closeout readiness must return one primary next action and a full blocker list.
  It must not surface contradictory blockers without explaining precedence.

Preferred stale accepted message:

```text
accepted_but_stale: fixture has an accepted historical state, but current source,
render, critique, or export evidence is stale. Re-run compile/critique/export and
refresh acceptance before closeout.
```

### Acceptance Artifact Contract

Source mutation requires a validated human acceptance artifact. Ranking, memory,
benchmark results, semantic review, and MCP review packets may recommend review,
but none of them may create or substitute for acceptance.

Required acceptance artifact:

```json
{
  "schema": "figure-agent.candidate-acceptance.v1",
  "fixture": "<name>",
  "candidate_id": "CAND001",
  "candidate_hash": "sha256:...",
  "candidate_set_hash": "sha256:...",
  "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
  "candidate_manifest_sha256": "sha256:...",
  "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
  "render_manifest_sha256": "sha256:...",
  "accepted_by": "human",
  "accepted_at": "2026-06-22T00:00:00Z",
  "accepted_artifacts": [
    {"path": "build/candidates/CAND001/render_manifest.json", "sha256": "sha256:..."}
  ],
  "decision": "accept",
  "rationale": "short human-readable reason"
}
```

Apply must block if any of these do not match current evidence:

- fixture name;
- candidate id;
- candidate hash;
- candidate set hash;
- candidate manifest hash;
- render manifest hash;
- source hashes for all target operations;
- accepted artifact hashes.

Acceptance artifacts may not be generated by ranking, memory, benchmark,
semantic review, or MCP source-apply code. Candidate-declared acceptance fields
are ignored unless they appear in the validated acceptance artifact.

### Apply Verification

Any apply path must choose one of two explicit semantics:

1. Run verification commands and record real command results.
2. Mark the result `applied_unverified` and list required commands.

It must not apply a patch and immediately record `verification_failed` without
actually running verification. `verification_failed` is reserved for executed
verification commands that returned failure or produced failing status.

Allowed apply result states:

- `blocked`
- `dry_run_passed`
- `applied_unverified`
- `applied`
- `applied_with_failed_verification`
- `rolled_back`

`applied_unverified` is a non-success terminal state for apply recording. It
must keep `workflow_ready`, `release_ready`, `golden_ready`, and closeout `ready`
false until required verification commands execute successfully and the result is
upgraded to `applied`. It must not count as `improved` in benchmark, ranking, or
memory success metrics.

## Memory: Learning Contract

### Problem

Memory currently receives too many `unknown` family/panel/outcome events to be
useful. It must become an evidence index over real candidate outcomes, not a bag
of unbound attempts.

### Required Memory Events

Memory events must be derived from existing artifacts. They must not be invented
from prose or hidden state.

Allowed event types:

- `candidate_generated`
- `candidate_rendered`
- `candidate_ranked`
- `candidate_accepted`
- `candidate_applied`
- `candidate_rejected`
- `candidate_rolled_back`
- `closeout_ready`
- `closeout_accepted`

Every candidate attempt event must include:

```json
{
  "candidate_id": "CAND001",
  "candidate_hash": "sha256:...",
  "edit_family": "label_offset",
  "target": {"panel": "A", "subregion": "label_cluster_top_left"},
  "source_defect": {"id": "QD001", "source_fingerprint": "sha256:..."},
  "outcome": {"state": "improved", "reason": "target detector count decreased"},
  "evidence_paths": [
    "build/candidates/CAND001/candidate_manifest.json",
    "build/candidates/CAND001/render_manifest.json"
  ],
  "metrics": {
    "candidate_rank_score": 0.65,
    "target_detector_delta": -1,
    "new_blocker_count": 0
  }
}
```

### Memory Safety Rules

- Events with unknown `candidate_id`, `edit_family`, `target.panel`,
  `target.subregion`, or `outcome.state` may be logged but must not contribute to
  priors.
- Priors remain zero until at least three eligible outcomes exist for the same
  family or panel pattern.
- Eligible outcomes are `improved`, `neutral`, and `regressed`.
- Blocked and unknown outcomes do not count as positive evidence.
- Memory prior is clamped to `[-0.25, 0.25]` unless a successor spec changes the
  bound with benchmark proof.
- Memory cannot alter hard gates, apply authority, effective apply authority,
  acceptance, golden state, or release state.

### Memory Metrics

Every memory index must expose:

```json
{
  "event_count": 24,
  "eligible_prior_count": 8,
  "unknown_event_rate": 0.05,
  "family_prior_coverage": 0.6,
  "panel_pattern_prior_coverage": 0.4,
  "regression_memory_count": 1,
  "memory_prior_used_rate": 0.3
}
```

Smoke acceptance thresholds:

- `unknown_event_rate <= 0.10` for generated synthetic attempt events.
- Memory prior never changes authority fields in any test.
- A regressed family lowers or zeroes soft priority but does not block unrelated
  fresh candidates.

## Semantic Reviewer Contract

### Role

The semantic reviewer is host-mediated and report-only. Plugin code prepares
local evidence packs; a host LLM or human may inspect them and write a structured
review artifact; plugin code validates the artifact. Plugin code does not call an
external model or service.

### Inputs

Semantic review may consume only local, declared artifacts:

- candidate manifest;
- render manifest;
- before/after crops;
- source defect evidence;
- briefing/spec;
- authoring context pack;
- semantic claims and locked invariants when explicitly enabled;
- reference images or crops declared by the fixture.

### Output Schema

```json
{
  "schema": "figure-agent.semantic-candidate-review.v1",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "candidate_id": "CAND001",
  "candidate_hash": "sha256:...",
  "reviewed_artifacts": [
    {"path": "build/candidates/CAND001/render_manifest.json", "sha256": "sha256:..."},
    {"path": "build/candidates/CAND001/crops/after_panel_A.png", "sha256": "sha256:..."}
  ],
  "semantic_invariants": [
    {"id": "SI001", "state": "pass", "evidence": "label moved, claim text unchanged"}
  ],
  "findings": [],
  "conflicts": [],
  "verdict": "pass",
  "human_required": false,
  "reviewed_at": "2026-06-22T00:00:00Z",
  "reviewer": "host"
}
```

Allowed verdicts:

- `pass`
- `needs_human`
- `semantic_risk`
- `invalid_or_stale`

Rules:

- Missing semantic review blocks only candidates that declare semantic risk,
  touch locked invariants, or are configured to require semantic review.
- Semantic review requirement is computed conservatively by plugin code, not by
  candidate self-declaration alone.
- A candidate requires semantic review when any operation touches a source range
  associated with `semantic_claims` or `locked_invariants`, the edit family is not
  in the pure mechanical allowlist, the fixture config sets
  `semantic_review_required: true`, or deterministic classification cannot prove
  the edit is coordinate-only and mechanically bounded.
- Candidate-declared risk may only increase review requirements, never decrease
  them.
- Stale reviewed artifact hashes produce `invalid_or_stale`.
- A semantic reviewer may block or require human review.
- A semantic reviewer may not generate accepted operations, change source, or
  override deterministic gates.
- Broad taste findings without local evidence must be advisory only.

## Failure Mode Matrix

| Failure | Detection point | Required state | Recovery |
|---|---|---|---|
| Detector report missing | Eyes | `missing` and candidate generation blocked for dependent defects | Run compile/checker or mark detector not required |
| Detector report stale | Eyes | `stale` and no candidate from stale defect | Refresh compile/audit evidence |
| Unknown panel on safe defect | Eyes/Hands | refusal or blocked actionability | Improve panel attribution or make assisted-only |
| First-match-only generation | Hands | test failure | Enumerate all supported safe defects |
| Source hash mismatch | Hands/Apply | `blocked` | Regenerate candidate set from current source |
| Render requested but unavailable | Operations | `dependency_missing` | Install dependency or run non-render benchmark honestly |
| Render requested but not implemented | Operations | command failure | Implement render path before claiming benchmark support |
| Candidate rank lacks candidate evidence | Ranking | `rank_basis: fixture_level_prior` with capped score | Render candidate and rerank |
| Apply verification not run | Apply | `applied_unverified` | Run required verification commands |
| Verification command failed | Apply | `applied_with_failed_verification` | Inspect, rollback, or fix |
| Accepted state stale | Status/Closeout | `accepted_but_stale`, `workflow_ready: false` | Refresh compile/critique/export/acceptance |
| Memory event unknown | Memory | logged but no prior contribution | Add metadata or outcome artifact |
| Semantic review stale | Semantic reviewer | `invalid_or_stale` | Re-run host review on current artifacts |

## Phased Implementation Plan

### Phase 0: Spec And Baseline Lock

Deliverables:

- This spec lands with no code behavior changes.
- A baseline dogfood/smoke report records current candidate/render/rank/memory
  gaps.

Gate:

- Spec names all required subsystems, safety invariants, metrics, and non-goals.

### Phase 1: Eyes Actionability Metrics

Deliverables:

- `quality-map` exposes defect actionability metrics.
- Safe defects require panel, selector hash, source hash, and freshness state.
- Unsupported safe defects are counted separately.

Tests:

- Multi-defect synthetic ledger with known panel attribution.
- Stale detector report blocks actionability.
- Unknown panel safe defect increments actionability gap and cannot produce an
  operation.

Gate:

- `unknown_panel_defect_count == 0` for supported synthetic fixtures.

### Phase 2: Multi-Candidate Generation

Deliverables:

- Default `fig-agent candidates` enumerates all supported fresh safe defects.
- Candidate/refusal metrics are emitted.
- Candidate manifests include panel, subregion, edit family, source defect,
  source hash, and variant metadata.

Tests:

- Two supported defects produce two or more candidates.
- Unsupported safe defect produces refusal with reason.
- Stable ids remain stable under identical source and ledger hashes.
- Source hash mismatch blocks operation.
- Path escape and symlink targets are rejected.

Gate:

- Synthetic `candidate_defect_coverage == 1.0`.

### Phase 3: Benchmark Render And Candidate-Specific Ranking

Deliverables:

- `benchmark-run --render` calls candidate rendering.
- Benchmark result uses honest render modes.
- Ranking binds scores to candidate and render manifests.
- Unrendered candidates cannot receive positive render evidence.

Tests:

- Render requested with dependencies produces `render_mode: rendered`.
- Render dependency missing produces `dependency_missing`.
- `requested_not_implemented` never appears.
- Candidate-specific rank rate is one for rendered candidates.

Gate:

- In render-enabled CI, smoke benchmark with render has
  `rendered_count == candidate_count` and `render_dependency_probe.state: pass`.

### Phase 4: Apply Verification And Closeout State Clarity

Deliverables:

- Apply distinguishes `applied_unverified`, `applied`, and
  `applied_with_failed_verification`.
- Closeout explains stale accepted/PASS states without contradictory blockers.
- Status exposes `accepted_but_stale` or equivalent precise reason.

Tests:

- Apply without verification records `applied_unverified`.
- Failed executed verification records `applied_with_failed_verification`.
- Stale accepted fixture is blocked, not ready.
- Candidate set mismatch and already-applied precedence are deterministic.

Gate:

- No stale accepted fixture reports closeout `ready`.

### Phase 5: Memory Outcome Activation

Deliverables:

- Memory log captures attributed candidate events.
- Unknown metadata is measured and excluded from priors.
- Priors activate only after enough eligible outcomes.

Tests:

- Three improved family outcomes produce bounded positive prior.
- Unknown family/panel/outcome produces no prior.
- Regressed event lowers or zeroes prior.
- Memory cannot change authority fields.

Gate:

- Smoke synthetic memory has `unknown_event_rate <= 0.10`.

### Phase 6: Semantic Reviewer Gate

Deliverables:

- Local semantic review artifact schema and validator.
- Candidate review packet can include semantic review state.
- Stale semantic review blocks only candidates that require it.

Tests:

- Stale artifact hash produces `invalid_or_stale`.
- Unknown candidate id is invalid.
- Semantic risk requires human review.
- Missing review is non-blocking for pure mechanical candidates with no locked
  invariants.

Gate:

- Semantic review never overrides deterministic gates or grants apply authority.

### Phase 7: Dogfood Release Gate

Deliverables:

- Smoke and dogfood suites include render-aware metrics.
- Release gate fails on new hard regressions.
- Documentation and operator playbook describe new states.

Tests:

- Benchmark comparison detects regression.
- Dogfood fixture produces multiple attributed candidates or explicit refusals.
- Best-ranked candidate has candidate-specific render evidence.

Gate:

- Dogfood passes with no new hard blockers and documented residual refusals.

## Test Strategy

Write failing tests before implementation in each phase.

Required test groups:

- `test_quality_defect_ledger_actionability.py`
- `test_candidate_generator_multi_defect.py`
- `test_candidate_refusal_accounting.py`
- `test_quality_benchmark_render_mode.py`
- `test_candidate_rank_candidate_specific.py`
- `test_quality_patch_apply_verification_states.py`
- `test_closeout_stale_accepted_state.py`
- `test_quality_memory_outcomes.py`
- `test_semantic_candidate_review.py`

Minimum assertions:

- no path escape;
- no symlink traversal;
- no source mutation during read-only or render commands;
- source hash mismatch blocks apply;
- stale evidence blocks readiness;
- no first-match-only candidate generation;
- no positive render evidence without render manifest;
- no memory authority upgrade;
- no LLM/semantic review gate override.

## Public Interface Changes

The preferred command surface remains additive.

Potential CLI additions or changes:

```text
fig-agent quality-map <name> --json
fig-agent candidates <name> --json [--max-candidates N] [--family <family>] [--panel <panel>]
fig-agent render-candidates <name> --candidate-set <path> --compile --export --crop-panel <panel> --evaluate --json
fig-agent rank-candidates <name> --candidate-set <path> [--require-render] --json
fig-agent benchmark-run --suite <suite> [--limit N] [--render] [--write] --json
fig-agent apply-candidate-ready <name> <candidate_id> --candidate-set <path> --json
fig-agent apply-candidate <name> <candidate_id> --candidate-set <path> --acceptance <path> --json
fig-agent memory-index --fixture <name> --json
fig-agent semantic-review-validate <name> <candidate_id> --review <path> --json
```

MCP remains conservative:

- read-only quality map, context pack, memory summary, benchmark preview;
- candidate materialization and rendering only inside fixture-local sandbox;
- readiness and review packet surfaces;
- no MCP source apply in this hardening slice.

## File Ownership Guidance

Expected code touch areas by phase:

| Phase | Primary files | Notes |
|---|---|---|
| Eyes | `scripts/quality/quality_defect_ledger.py`, detector adapters, tests | Preserve existing detector reports |
| Hands | `scripts/candidates/candidate_generator.py`, `candidate_families.py`, candidate tests | Remove first-match semantics |
| Render/Rank | `scripts/quality/quality_benchmark.py`, `scripts/candidates/candidate_render.py`, `candidate_rank.py` | Reuse existing sandbox path |
| Apply/Closeout | `scripts/candidates/candidate_apply.py`, `scripts/quality/quality_patch_apply.py`, `scripts/fig_closeout.py`, `scripts/status.py` | Clarify states, do not weaken gates |
| Memory | `scripts/quality/quality_memory_events.py`, `quality_memory_index.py` | Events from artifacts only |
| Semantic | new validator module, review packet integration | Host-mediated local artifact only |
| MCP/CLI | `bin/fig-agent`, MCP wrappers | Integrate serially to avoid command drift |

Do not let parallel agents edit `bin/fig-agent`, MCP legacy server wrappers, or
status/closeout command surfaces at the same time. Integrate those files
serially after lower-level tests pass.

## Acceptance Metrics For The Whole Hardening Slice

The hardening slice is successful only when all are true:

1. Smoke fixtures that declare supported edit families produce nonzero
   candidates.
2. Supported synthetic multi-defect fixtures have
   `candidate_defect_coverage == 1.0`.
3. Dogfood fixture produces multiple attributed candidates or explicit refusals
   for every unsupported safe defect group.
4. `benchmark-run --render` reports real render modes and never emits
   `requested_not_implemented`.
5. Rendered candidates have `candidate_specific_rank_rate == 1.0`.
6. Unrendered candidates do not receive positive render evidence.
7. Memory unknown event rate is at most 10 percent in synthetic smoke attempt
   events.
8. Memory prior never changes hard gate or apply authority fields.
9. Stale accepted/PASS fixture states cannot report closeout `ready`.
10. Apply results distinguish unverified, verified success, and verified failure.
11. Semantic review is local, hash-bound, report-only, and cannot override
    deterministic gates.
12. All automatic writes stay under fixture `build/candidates`, fixture
    `build/memory`, fixture-local verified apply paths, or workspace `.scratch`
    benchmark outputs.

## Release And Rollout Rules

- Land this spec first, with no behavior changes.
- Implement in phases. Do not skip to semantic review or memory before candidate
  enumeration and benchmark render are trustworthy.
- Every phase starts with failing tests.
- Every phase preserves current safety boundaries unless this spec explicitly
  makes them stricter.
- Real dogfood may expose additional refusals. Add refusals and metrics before
  adding broader automatic edits.
- A single useful vertical path with strict evidence is preferred over many broad
  candidate families with weak verification.

## Atomic Commit Strategy

Implementation should be split as follows:

1. Spec only.
2. Failing tests for defect actionability metrics.
3. Implement actionability metrics.
4. Failing tests for multi-candidate generation and refusals.
5. Implement multi-candidate generation.
6. Failing tests for benchmark render mode and candidate-specific rank.
7. Implement benchmark render and rank binding.
8. Failing tests for apply verification states and stale closeout.
9. Implement apply/status/closeout hardening.
10. Failing tests for memory outcomes and bounded priors.
11. Implement memory activation.
12. Failing tests for semantic review validation.
13. Implement semantic review validator.
14. Dogfood benchmark metrics and docs update.

Each commit must keep generated artifacts out of source unless the artifact is a
deliberate fixture or golden contract file.

## Review Checklist

Before implementation starts, reviewers must confirm:

- This spec addresses Eyes, Hands, Operations, Memory, and Semantic Reviewer.
- It does not make LLM prompting the primary fix.
- It requires no external/cloud service calls from plugin code.
- It preserves or strengthens all safety gates.
- It forbids first-match-only generation in the closed loop.
- It makes benchmark render evidence real when render is requested.
- It makes ranking candidate-specific or explicitly lower-confidence.
- It prevents stale accepted/PASS state from masquerading as ready.
- It keeps memory as a bounded soft prior.
- It defines measurable acceptance criteria and failure states.

## Open Questions

None blocking for the spec. Implementation may discover individual detector
families that need assisted-only refusals before they can become automatic edit
families.
