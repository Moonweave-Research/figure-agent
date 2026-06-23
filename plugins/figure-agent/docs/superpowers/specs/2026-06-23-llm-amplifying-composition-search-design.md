# LLM-Amplifying Composition Search Engine Design

Status: draft for user review
Date: 2026-06-23
Owner: figure-agent
Target release: post-0.11.x

## Summary

The current figure-agent loop is good at reproducibility, stale-artifact gates,
and mechanical defects such as collisions, label overlaps, and missing evidence.
It is not good at composition. A detector-clean figure can still look awkward,
unnatural, over-annotated, or code-generated.

This spec defines the next engine layer:

```text
LLM visual proposal + fixture intent + reference/convention context
  -> semantic scene model
  -> structural composition candidates
  -> render/evaluate/rank packet
  -> human-gated selection
  -> quality-kernel verification
```

The product goal is not to replace the LLM or make figure-agent a taste oracle.
The product goal is to widen the safe creative search space for LLMs. The LLM
should be able to propose bold figure restructurings. figure-agent should render
them, check scientific invariants, measure convention-level regressions, preserve
evidence, and make human comparison cheap.

This is not a bypass around figure-agent. Every LLM proposal must still enter the
plugin as a structured candidate with source diff, sandbox render, invariant
checks, evidence hashes, comparison artifacts, and human-gated acceptance. The
plugin should reject unsafe application, not creative proposal capture.

## Triggering Dogfood Case

`fig3_resistance_mechanism` exposed the failure mode:

- The rendered figure is scientifically plausible and mostly detector-clean, but
  visually awkward.
- Panel A's carrier walk reads as a mechanical bouncing-ball diagram, not a
  natural dispersive path.
- The I(t) sparkline is visually orphaned from the cell.
- Bridge text floats without a strong anchor.
- Panel A is sparse while Panel B is busy.
- Panel B has too many competing arrows.
- `n = breadth` crosses the distributions instead of reading as a clean span.
- The blue spike is so thin that it risks reading as a glitch rather than a
  narrow trap-energy distribution.

The current quality loop cannot fix this class of problem because its candidate
family is dominated by bounded coordinate nudges. On this fixture,
`quality-map` reports candidates blocked by `stale_detector_evidence` and
`unknown_panel`, and even a working nudge engine would not restructure panel
hierarchy, object anchoring, or arrow grammar.

This is not just a bug in one figure. It is an architectural gap.

## Core Product Principle

figure-agent must not reduce LLM creative bandwidth.

The split of responsibility is:

```text
LLM:
  visual hypothesis, restructuring, metaphor choice, composition proposal,
  large layout moves, explanatory simplification

figure-agent:
  source grounding, fixture boundaries, deterministic rendering, evidence
  freshness, semantic invariant checks, composition lint, candidate comparison,
  regression prevention, human-gated acceptance
```

The system should say "show me evidence" more often than it says "no." A
freeform structural candidate should be allowed into a review sandbox unless it
breaks a hard factual, safety, or reproducibility gate.

This does not mean figure-agent becomes optional. The correct boundary is:

```text
LLM proposal without figure-agent:
  untracked source edits, no render lineage, no stale-evidence checks,
  no invariant audit, no rollback, no durable rationale

LLM proposal through figure-agent:
  structured candidate, sandbox render, invariant audit, comparison packet,
  human decision record, rollback path
```

The plugin is the lab bench, not the painter's prison.

## Goals

1. Add a creative lane where LLMs can propose structural redraws beyond the
   current safe-mechanical nudge family.
2. Preserve hard gates for source freshness, compile/export validity, scientific
   invariants, path safety, accepted/golden state, and explicit human authority.
3. Add composition lint that detects convention-level failure modes without
   claiming subjective taste judgment.
4. Generate and render multiple structural candidates per problem region.
5. Rank candidates by evidence-backed deltas, not by opaque aesthetic scoring.
6. Keep final figure direction and acceptance under human authority.
7. Record the LLM proposal, applied operations, rendered artifacts, checks, and
   rejection reasons so a session can be resumed or audited.
8. Apply first to `fig3_resistance_mechanism`, then generalize to other
   schematic figures.

## Non-Goals

- No autonomous journal-acceptance claim.
- No hidden auto-designer that silently mutates manuscript source.
- No blocking of LLM structural redraws just because they are outside an old
  candidate family.
- No external paid vision or image-generation API as a required core dependency.
- No reference overcopying. References supply convention priors, not topology to
  clone.
- No automatic scientific meaning inference beyond declared fixture inputs.
- No WYSIWYG drag editor.
- No data plotting. Graph Hub remains responsible for real data plots.

## Architecture

Use six layers.

## Contract Hardening Required Before Build

The following contracts are prerequisites for implementation. They close the
gaps that would otherwise make the spec either unsafe or too restrictive.

### Freshness State Semantics

Freshness must not be one binary gate. Different stages need different evidence.

| Stage | Stale source allowed? | Stale detector evidence allowed? | Output |
|---|---:|---:|---|
| `proposal_capture` | yes | yes | unranked `creative_review_only` proposal record |
| `sandbox_prepare` | no | yes | candidate source copy + diff manifest |
| `sandbox_render` | no | yes | rendered candidate artifacts |
| `evaluate_rank` | no | no | ranked review packet |
| `human_accept` | no | no | acceptance record |
| `apply_to_fixture` | no | no | source mutation with rollback |
| `export_or_release` | no | no | export/release artifacts |

State names:

```text
proposed -> sandbox_prepared -> rendered -> evaluated -> review_ready
  -> human_accepted -> applied -> exported
```

Invalidation rules:

- Any change to `<name>.tex`, `spec.yaml`, `briefing.md`, scene model, reference
  pack, or composition-lint config invalidates `evaluated`, `review_ready`, and
  later states.
- Any change to detector reports invalidates ranking but not raw proposal records.
- Human acceptance is bound to candidate source hash, render hash, scene model
  hash, and evaluation hash. A hash mismatch returns to `rendered` or earlier.
- Stale evidence can be recorded as context, but it cannot support ranking,
  acceptance, apply, export, or release.

Every candidate set and review packet must include a freshness vector:

```json
{
  "schema": "figure-agent.freshness-vector.v1",
  "captured": {
    "tex_hash": "sha256:...",
    "spec_hash": "sha256:...",
    "briefing_hash": "sha256:...",
    "scene_model_hash": "sha256:...",
    "lint_config_hash": "sha256:...",
    "detector_hash": "sha256:...",
    "reference_pack_hash": "sha256:..."
  },
  "current": {
    "tex_hash": "sha256:...",
    "spec_hash": "sha256:...",
    "briefing_hash": "sha256:..."
  },
  "status": {
    "source": "fresh",
    "detectors": "stale",
    "references": "fresh"
  }
}
```

If any source hash differs at `sandbox_prepare`, the command returns
`rebase_required`. If detector/reference hashes differ at `evaluate_rank`, the
command returns `refresh_required`.

### LLM Boundary

v1 must not call model APIs from plugin code. figure-agent consumes proposals
authored by the host LLM or by a human-maintained file.

Allowed proposal inputs:

- `--proposal-json <path>` containing `composition-candidate-set.v1`;
- fixture-local `build/candidates/<id>/proposal.json` written by the host;
- MCP request payload supplied by the host session.

Forbidden in v1:

- plugin-originated external LLM calls;
- hidden image-generation calls;
- silent source mutation based on free text;
- storing only a natural-language summary without executable candidate source or
  patch payload.

Public command names must preserve this boundary. In v1, the plugin captures,
renders, ranks, and reviews candidate proposals; it does not generate them from
`--goal` text.

V1 command split:

```bash
fig-agent compose-capture <name> --proposal-json <path> [--json]
fig-agent compose-render <name> --candidate-set <path> [--candidate-id <id>] [--json]
fig-agent compose-rank <name> --candidate-set <path> [--json]
fig-agent compose-review <name> --candidate-set <path> --candidate-id <id> [--json]
```

`--goal` and `--count` are allowed only on a future host-orchestrated command
that emits a prompt/template for the host LLM. They must not imply plugin-side
model inference.

### Semantic Invariant Contract

Scientific invariants are explicit, human-authored constraints. The plugin may
check declared invariants; it must not invent scientific truth.

```json
{
  "schema": "figure-agent.semantic-invariant.v1",
  "id": "carrier_sign_agnostic",
  "owner": "human",
  "source_evidence": ["briefing.md:31"],
  "visible_assertion": "carrier path must not imply clean electron/hole ballistic drift",
  "applies_to": [{"panel": "A", "object": "carrier_walk"}],
  "verification_method": "human_review_required",
  "blocking_level": "apply_and_release",
  "requires_human_if_changed": true,
  "allowed_uncertainty": "process path may show direction cues if it remains tortuous"
}
```

Allowed `verification_method` values:

- `declared_human_review_required`
- `geometry_relation`
- `text_presence_or_absence`
- `style_token_check`
- `rendered_artifact_check`

If no invariant contract exists, creative candidates remain review-only; they are
not blocked at proposal capture.

Before `human_accept` or `apply_to_fixture`, every target object must report one
of:

- `covered`: relevant invariants exist and passed;
- `not_truth_bearing`: object is explicitly non-truth-bearing;
- `human_waived_with_rationale`: reviewer accepted missing coverage.

Truth-bearing geometry changes additionally require
`permissions_granted: ["change_truth_bearing_geometry"]` in the acceptance
record.

### Composition Lint Check Contract

Every lint check must declare whether it is deterministic or human commentary.

```json
{
  "schema": "figure-agent.composition-lint-check.v1",
  "id": "arrow_clutter",
  "class": "deterministic_metric",
  "required_inputs": ["semantic_scene", "render_bbox_inventory"],
  "metric": "arrow_role_count_per_subregion",
  "threshold": {"review": 3, "major": 5},
  "evidence_object": "subregion_bbox + arrow_object_ids",
  "false_positive_policy": "human may mark as intentional grammar",
  "candidate_families": ["arrow_clutter_reduction"]
}
```

Checks without metric, threshold, and evidence object are allowed only as
`human_commentary`. `human_commentary` findings may guide LLM prompts, but they
must not rank, block, or accept candidates.

### Candidate Operation Contract

Every rendered candidate must contain executable content, not just a summary.

Allowed candidate payload forms:

1. `full_source_copy`: complete sandbox TeX source plus base/source hash.
2. `typed_patch`: operations with selector hash and exact replacement text.

```json
{
  "schema": "figure-agent.composition-candidate-operation.v1",
  "kind": "replace_semantic_block",
  "path": "examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex",
  "base_source_hash": "sha256:...",
  "operation_hash": "sha256:...",
  "selector": {
    "kind": "semantic_block",
    "object_id": "carrier_walk",
    "start_marker": "% fig-agent:start object=carrier_walk",
    "end_marker": "% fig-agent:end object=carrier_walk",
    "original_hash": "sha256:..."
  },
  "original_text_hash": "sha256:...",
  "replacement_text": "...exact TeX block...",
  "replacement_text_hash": "sha256:...",
  "post_hash": "sha256:...",
  "rollback": {"kind": "restore_original_text", "original_text": "..."}
}
```

Line ranges are read-only hints. They are not safe mutation selectors for
creative candidates.

`full_source_copy` candidates may render for review, but they cannot apply until
converted to either a typed patch or an explicit whole-file replacement whose
base source hash still matches.

### Acceptance Contract

Creative candidates require an explicit acceptance artifact before any fixture
source mutation.

```json
{
  "schema": "figure-agent.composition-acceptance.v1",
  "fixture": "fig3_resistance_mechanism",
  "candidate_id": "CCAND001",
  "decision": "accept",
  "reviewer": "human",
  "accepted_at": "2026-06-23T00:00:00Z",
  "accepted_hashes": {
    "candidate_manifest": "sha256:...",
    "candidate_source": "sha256:...",
    "base_source": "sha256:...",
    "operation_set": "sha256:...",
    "scene_model": "sha256:...",
    "invariant_set": "sha256:...",
    "lint_config": "sha256:...",
    "render": "sha256:...",
    "evaluation": "sha256:..."
  },
  "permissions_granted": ["apply_to_fixture_source"],
  "known_regressions_accepted": [],
  "rationale": "Chosen because it reduces arrow clutter while preserving sign-agnostic trapping.",
  "rollback_patch": "build/candidates/CCAND001/rollback.patch"
}
```

`apply_to_fixture` must rerun hard gates immediately before mutation and fail if
any accepted hash no longer matches current state.

### TeX Sandbox Policy

LLM-authored TeX is untrusted until rendered inside a sandbox.

Requirements:

- compile with shell escape disabled;
- reject symlinks in candidate source, sandbox, output, and input roots;
- allow `\input` and asset reads only from plugin styles and the selected fixture
  sandbox/input copy;
- reject absolute paths in candidate TeX;
- reject writes outside the candidate sandbox;
- record all copied assets and their hashes;
- canonicalize every input and output path before compile;
- reject symlinks again immediately before compile, after asset copy;
- run with isolated current working directory, home, and temp roots;
- set TeX file access policy to restrict open-in and open-out to permitted roots
  (for example `openin_any=p` and `openout_any=p` where supported);
- record denied read/write attempts when the runner can observe them;
- preserve fixture `build/<name>.*`, `exports/`, accepted artifacts, and golden
  artifacts until explicit apply/export commands run.

Required negative tests:

- absolute path input;
- `../` path escape;
- symlinked source or asset;
- forbidden `\input` outside copied roots;
- write attempt outside sandbox;
- shell-escape attempt.

### Freeform Structural Family

Known candidate families should not become a new cage. Add a required fallback:

```text
family: freeform_structural
authority: creative_review_only
auto_rank: limited_to_hard_gates_and_declared_lint
auto_apply: never
```

`freeform_structural` candidates are allowed to render and enter human review
when they pass hard plan-time safety checks. They do not need to map to an
existing family. They also cannot claim expected lint improvements unless those
improvements are measured after rendering.

They cannot be accepted for apply until:

- executable operations exist;
- invariant coverage is `covered`, `not_truth_bearing`, or
  `human_waived_with_rationale` for all targets;
- hard gates pass on fresh evidence;
- acceptance includes `permissions_granted: ["accept_freeform_structural"]`.

### Layer 1: Semantic Scene Model

The engine needs addressable semantic objects, not just TeX line ranges.

Inputs:

- `spec.yaml`
- `briefing.md`
- `<name>.tex`
- optional `caption.md`
- current build artifacts
- detector reports
- critique and adjudication files
- reference packs and paper-wide context when declared

Output schema:

```json
{
  "schema": "figure-agent.semantic-scene-model.v1",
  "fixture": "fig3_resistance_mechanism",
  "panels": [
    {
      "id": "A",
      "role": "mechanism",
      "objects": [
        {
          "id": "cell_stack",
          "kind": "apparatus",
          "truth_bearing": true,
          "source_selector": {"kind": "line_range", "value": "20:23"}
        },
        {
          "id": "carrier_walk",
          "kind": "process_path",
          "truth_bearing": false,
          "semantic_claim": "carrier is sign-agnostic and repeatedly trapped",
          "source_selector": {"kind": "line_range", "value": "30:36"}
        },
        {
          "id": "current_sparkline",
          "kind": "mini_plot",
          "anchor_target": "cell_stack",
          "source_selector": {"kind": "line_range", "value": "40:45"}
        }
      ]
    }
  ]
}
```

The first implementation may use explicit fixture-local annotations rather than
full TeX parsing. For example:

```yaml
composition_model:
  panels:
    A:
      objects:
        carrier_walk:
          lines: [30, 36]
          kind: process_path
          truth_bearing: false
          allowed_creative_ops: [path_morphology, arrow_simplify, density_fill]
        current_sparkline:
          lines: [40, 45]
          kind: mini_plot
          anchor_target: cell_stack
```

Missing scene annotations must not block LLM proposals. They only downgrade
automatic apply authority and require human review.

### Layer 2: Creative Candidate Lane

The existing safe-mechanical lane remains for small bounded fixes:

```text
safe-mechanical lane:
  label nudges, small offsets, clash clearing, style-token normalization
  -> eligible for deterministic ranking and narrow apply gates
```

Add a creative lane:

```text
creative lane:
  LLM-authored or LLM-planned structural redraw candidates
  -> sandbox render
  -> invariant/composition/reference checks
  -> human selection required
```

Creative candidates may include:

- replacing a segmented zigzag path with a smoother process path;
- reducing arrow count;
- converting floating text into anchored callouts;
- moving a mini-plot into an apparatus readout position;
- regrouping annotations;
- changing panel density;
- replacing internal measurement arrows with brackets or external spans;
- widening a too-thin schematic distribution;
- rebalancing panel bboxes or whitespace;
- proposing a `freeform_structural` redraw that does not fit a known family,
  provided it stays review-only until rendered and human accepted.

Creative candidates must never directly mutate source. They write to candidate
sandboxes and review packets first.

### Layer 3: Composition Lint

Composition lint records checkable convention failures. It does not say "good"
or "beautiful." It says which figure-convention risks are present.

Initial checks:

| Check | Signal | Example on `fig3_resistance_mechanism` |
|---|---|---|
| `orphan_plot` | mini-plot has no declared anchor or proximity to its source object | I(t) sparkline floats beside the cell |
| `floating_annotation` | explanatory text has no target object, leader, or panel caption role | `current decays`, `broader g(E)` text |
| `arrow_clutter` | too many arrows in one subregion, or arrows with competing meanings | Panel B evolution + breadth + magnitude arrows |
| `panel_density_imbalance` | large density mismatch between adjacent panels | sparse Panel A vs busy Panel B |
| `measurement_arrow_crosses_data` | measurement span crosses the object it measures without a convention reason | `n = breadth` crossing curves |
| `thin_glitch_primitive` | truth-bearing or meaning-bearing primitive below print/legibility width | blue spike too narrow |
| `path_mechanicalness` | process path is made of repeated sharp segments and arrowheads | carrier walk reads as bouncing ball path |
| `anchor_ambiguity` | label/callout target is unclear after layout reduction | detached bridge text |

Composition lint output:

```json
{
  "schema": "figure-agent.composition-lint.v1",
  "fixture": "fig3_resistance_mechanism",
  "findings": [
    {
      "id": "CL001",
      "severity": "review",
      "check": "orphan_plot",
      "panel": "A",
      "target_object": "current_sparkline",
      "evidence": ["semantic_scene.current_sparkline.anchor_target"],
      "suggested_candidate_families": ["sparkline_anchor", "sparkline_remove_or_caption"]
    }
  ]
}
```

These findings are review signals. They do not automatically fail release unless
the fixture opts into a stricter publication gate.

### Layer 4: Structural Candidate Families

Candidate families should change composition, not just coordinates.

For `fig3_resistance_mechanism`, v1 ships these families:

1. `carrier_walk_morphology`
   - Replace many sharp segments with one or two smoother stochastic paths.
   - Reduce arrowheads to start/end or a small number of direction cues.
   - Preserve the claim: sign-agnostic repeated trapping, not ballistic drift.

2. `sparkline_anchor`
   - Attach sparkline visually to the cell as readout/evidence.
   - Optionally reduce bridge text and make the sparkline carry the message.

3. `floating_text_consolidation`
   - Convert unanchored explanatory text into one anchored callout, panel caption,
     or removed redundant label.

4. `arrow_clutter_reduction`
   - Keep only the most important arrow grammar.
   - Convert `n = breadth` from an internal crossing arrow to an external bracket
     or baseline span.

5. `distribution_shape_salience`
   - Widen the blue spike enough to read as narrow distribution rather than a
     rendering glitch.
   - Preserve the semantic contrast: S60 discrete/narrow, S80 continuous/broad.

6. `panel_density_rebalance`
   - Add or remove non-truth-bearing texture, whitespace, or grouping so adjacent
     panels carry comparable visual weight.

Every structural family declares:

- allowed target object kinds;
- protected semantic invariants;
- allowed operation classes;
- expected composition-lint improvements;
- possible regressions;
- required human decision points.

### Layer 5: Reference-Conditioned Ranking

Reference-free critique is taste-blind. The engine needs reference and convention
context, but references must amplify the LLM rather than cage it.

Ranking inputs:

- hard gates: compile, export, stale evidence, path safety;
- semantic invariants from `briefing.md`, `spec.yaml`, and optional scene model;
- composition lint deltas;
- detector deltas;
- reference-convention deltas when a reference pack exists;
- accessibility and print-scale checks;
- user-specified intent such as "slim, compact, dense, not bloated."

Ranking output must avoid unverifiable aesthetic claims:

Bad:

```text
Candidate 3 is the best-looking figure.
```

Good:

```text
Candidate 3 removes one orphan plot, reduces arrow clutter from 3 arrow roles to
1, moves the breadth marker outside the data curves, preserves all declared
physics invariants, and introduces no new detector candidates. Human review is
required for final composition choice.
```

### Layer 6: Human-Gated Acceptance

Human gates are required for:

- accepting a creative candidate;
- changing scientific metaphor;
- changing panel topology;
- changing any truth-bearing path geometry;
- accepting reference-conditioned style transfer;
- promoting to accepted/golden/final-ready state.

The human review packet should show:

- baseline render;
- candidate renders;
- panel crops;
- semantic invariant pass/fail;
- composition lint before/after;
- detector before/after;
- reference-convention notes;
- exact source diff;
- rollback path.

The human should choose among rendered options, not manually reconstruct the
figure from scratch.

## Hard Gates vs Soft Gates

Hard gates block apply/export/acceptance:

- source, render, critique, or export freshness mismatch;
- compile failure;
- path traversal or sandbox escape;
- undeclared accepted/golden mutation;
- semantic invariant violation;
- truth-bearing geometry rewrite without explicit permission;
- missing candidate render for a creative candidate;
- stale detector evidence used as if fresh.

Soft gates require review but do not block candidate generation:

- outside current candidate family;
- large layout move;
- alternate visual metaphor;
- reduced or increased annotation count;
- reference-style divergence;
- composition lint warnings.

This distinction is load-bearing. If figure-agent blocks creative exploration at
soft gates, it becomes worse than a raw LLM.

## Public Interfaces

### CLI

Add composition-search entry points that match the v1 LLM boundary:

```bash
fig-agent compose-capture <name> \
  --proposal-json examples/<name>/build/candidates/proposal.json \
  --json

fig-agent compose-render <name> \
  --candidate-set examples/<name>/build/candidates/composition_candidate_set.json \
  --json

fig-agent compose-rank <name> \
  --candidate-set examples/<name>/build/candidates/composition_candidate_set.json \
  --json

fig-agent compose-review <name> \
  --candidate-set examples/<name>/build/candidates/composition_candidate_set.json \
  --candidate-id CCAND001 \
  --json
```

Required behavior:

- Capture proposal JSON even when detector evidence is stale, but mark it
  `proposed_unranked` until refresh completes.
- Validate source freshness before sandbox preparation and rendering.
- Validate detector/reference/critique freshness before evaluation, ranking,
  acceptance, apply, export, or release.
- If freshness is insufficient for the requested stage, return a
  `refresh_required` packet with the exact safe command sequence.
- Create candidate sandboxes only under `examples/<name>/build/candidates/`.
- Store the LLM prompt/proposal, executable candidate payload, and deterministic
  transform metadata.
- Render all candidates that pass plan-time safety checks.
- Rank candidates by hard gates and composition/reference evidence.
- Never mutate fixture source unless a separate accepted apply command is run.

P5 safe first slice, implemented before real TeX rendering, narrows this surface:
`compose-render` prepares only a fixture-local candidate source copy and manifest;
`compose-rank` ranks only by hard gates plus metric-backed deterministic
composition-lint deltas declared in the host-authored candidate set; and
`compose-review` assembles a read-only before/after source packet. In this slice,
compile/export/crop/evaluate stay `not_run`, `human_commentary` is copied for
review but cannot rank or block, `freeform_structural` remains review-only, and
no acceptance/apply path or source mutation is available.

### MCP

Add MCP tools after CLI stabilizes:

- `figure_agent_analyze_composition(name)`
- `figure_agent_capture_composition_candidates(name, proposal)`
- `figure_agent_render_composition_candidates(name, candidate_set)`
- `figure_agent_rank_composition_candidates(name, candidate_set)`
- `figure_agent_prepare_composition_review(name, candidate_id)`

MCP remains an evidence and review surface. It must not silently apply creative
candidates or call model APIs from plugin code.

## Data Contracts

### Composition Candidate Set

```json
{
  "schema": "figure-agent.composition-candidate-set.v1",
  "fixture": "fig3_resistance_mechanism",
  "base": {
    "tex_hash": "sha256:...",
    "render_hash": "sha256:...",
    "scene_model_hash": "sha256:...",
    "composition_lint_hash": "sha256:...",
    "freshness_vector_hash": "sha256:..."
  },
  "authority": "creative_review_only",
  "goal": "make trapping mechanism read naturally",
  "candidates": [
    {
      "id": "CCAND001",
      "family": "carrier_walk_morphology",
      "target": {"panel": "A", "object": "carrier_walk"},
      "proposal_source": "llm",
      "expected_improvements": ["path_mechanicalness", "arrow_clutter"],
      "protected_invariants": [
        "carrier_sign_agnostic",
        "repeated_trapping",
        "no_ballistic_drift"
      ],
      "operations": [
        {
          "schema": "figure-agent.composition-candidate-operation.v1",
          "kind": "replace_semantic_block",
          "path": "examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex",
          "base_source_hash": "sha256:...",
          "operation_hash": "sha256:...",
          "selector": {
            "kind": "semantic_block",
            "object_id": "carrier_walk",
            "start_marker": "% fig-agent:start object=carrier_walk",
            "end_marker": "% fig-agent:end object=carrier_walk",
            "original_hash": "sha256:..."
          },
          "original_text_hash": "sha256:...",
          "replacement_text": "% fig-agent:start object=carrier_walk\n...exact TeX block...\n% fig-agent:end object=carrier_walk",
          "replacement_text_hash": "sha256:...",
          "post_hash": "sha256:...",
          "replacement_summary": "replace segmented walk with smoother stochastic path and fewer arrowheads",
          "rollback": {"kind": "restore_original_text", "original_text": "..."}
        }
      ],
      "apply_authority": "human_required"
    }
  ]
}
```

### Composition Review Packet

```json
{
  "schema": "figure-agent.composition-review-packet.v1",
  "fixture": "fig3_resistance_mechanism",
  "candidate_id": "CCAND001",
  "render_status": "prepared_needs_human_review",
  "hard_gates": {
    "prepare": "success",
    "compile": "not_run",
    "export": "not_run",
    "crop": "not_run",
    "evaluate": "not_run"
  },
  "before_artifacts": [{"kind": "base_source", "path": "fig3_resistance_mechanism.tex"}],
  "after_artifacts": [{"kind": "candidate_source_copy", "path": "build/candidates/CCAND001/source/candidate.tex"}],
  "composition_lint_delta": {
    "path_mechanicalness": {
      "check_id": "CL003",
      "status": "human_commentary",
      "before": null,
      "after": null,
      "evidence_hash": "sha256:..."
    },
    "arrow_clutter": {
      "check_id": "CL002",
      "status": "improved",
      "before": {"arrow_role_count": 3},
      "after": {"arrow_role_count": 1},
      "threshold": {"review": 3, "major": 5},
      "evidence_hash": "sha256:..."
    },
    "orphan_plot": {
      "check_id": "CL001",
      "status": "unchanged",
      "before": {"orphan_plot_count": 1},
      "after": {"orphan_plot_count": 1},
      "evidence_hash": "sha256:..."
    }
  },
  "acceptance_required": "composition-acceptance.v1",
  "human_question": "Does this path read more like dispersive trapping without implying ballistic drift?"
}
```

## Implementation Slices

### Slice 0: State Hygiene and Panel Mapping

Fix the current blockers that prevent trustworthy generation:

- `stale_detector_evidence` must route to a first-class refresh plan.
- `unknown_panel` must be reduced by native panel bbox mapping for detector nodes.
- detector-backed ranking, acceptance, and apply must refuse stale evidence while
  proposal capture stays allowed as `proposed_unranked`.
- critique/accounting references such as missing `VC016` must be lint-blocking.

Exit criteria:

- `fig3_resistance_mechanism` can reach a fresh render/critique/export baseline.
- `quality-map` defects include stable panel IDs where possible.
- stale evidence cannot produce accepted-looking candidate records.

### Slice 1: Composition Lint v1

Implement the first eight composition checks listed above.

Exit criteria:

- `fig3_resistance_mechanism` emits review findings for orphan sparkline,
  floating annotations, arrow clutter, and path mechanicalness.
- The lint output is deterministic and JSON-stable.
- Findings suggest candidate families but do not claim automatic taste judgment.

### Slice 2: Creative Candidate Sandbox

Add the creative lane data contract and sandbox renderer.

Exit criteria:

- An LLM-authored candidate can be stored as `creative_review_only`.
- A `freeform_structural` candidate can be captured and rendered without a known
  family, but cannot auto-rank beyond hard gates or auto-apply.
- It renders in a sandbox without mutating the fixture source.
- The review packet contains before/after artifacts and exact source diff.

### Slice 2.5: Local Human Acceptance Readiness

Add a local-only acceptance gate before any future apply path.

Exit criteria:

- `compose-apply-ready` reports whether a prepared candidate is ready for local
  human acceptance.
- Readiness is hash-bound to the candidate set, render manifest, sandbox source
  copy, current base source, and operation set.
- Acceptance writes only
  `build/candidates/<candidate-id>/composition_acceptance.json`.
- `source_mutation_allowed` remains `false`; compile, export, crop, and
  evaluate stay `not_run` and explain why fixture source mutation is disabled.
- `freeform_structural` acceptance requires explicit
  `accept_freeform_structural` permission.
- Truth-bearing geometry changes require explicit
  `change_truth_bearing_geometry` permission only when candidate metadata
  declares that change.

### Slice 3: Fig3 Structural Families

Implement `carrier_walk_morphology`, `sparkline_anchor`, and
`arrow_clutter_reduction` for `fig3_resistance_mechanism`.

Exit criteria:

- Generate at least six rendered candidates.
- At least three candidates make structural changes beyond 10 px nudges.
- Ranking explains measurable convention deltas.
- Human can select one candidate without manually redrawing from scratch.

### Slice 4: Reference-Conditioned Ranking

Add optional reference-pack scoring.

Exit criteria:

- With no reference pack, candidates still render and lint, but ranking says
  reference scoring is skipped.
- With a reference pack, ranking cites convention axes such as arrow economy,
  label anchoring, line-weight hierarchy, and panel density.
- The system flags overcopying risk separately from underlearning risk.

### Slice 5: Generalization

Lift fig3-specific families into reusable schematic families.

Exit criteria:

- At least three fixtures can run composition lint.
- At least two fixtures can generate rendered creative candidates.
- Benchmark records manual edit rounds saved and reviewer preference rate.

## Validation Metrics

Per fixture:

- number of composition-lint findings before/after;
- orphan annotation count;
- arrow-role count per subregion;
- panel density ratio;
- measurement-arrow/data-curve crossings;
- minimum meaning-bearing primitive width at print scale;
- detector candidate count before/after;
- semantic invariant failures;
- candidate compile/render success rate;
- human preference over baseline;
- manual edit rounds to accepted candidate.

Cross-fixture:

- percent of creative candidates rejected by hard factual gates;
- percent rejected by human taste after passing gates;
- rate of reference-overcopy warnings;
- stale-evidence blocks caught before review;
- median time from awkward baseline to accepted candidate.

## Safety Notes

- Creative candidates are always review-only until human accepted.
- The LLM may propose broad changes, but figure-agent must preserve exact source
  diffs, render evidence, and rollback paths.
- Hard scientific invariants should be minimal and explicit. Over-constraining
  them will suppress useful LLM creativity.
- Composition lint must remain falsifiable. If a finding cannot point to an
  object, geometry relation, count, or reference convention, it belongs in human
  commentary, not a machine gate.
- References are priors, not templates. The engine should learn convention axes,
  not copy figure topology.

## Open Risks

1. LLM patches can be large and hard to merge if the source TeX remains a flat
   hand-authored file. Semantic annotations or macro boundaries may be required.
2. Composition lint can become pseudo-taste if checks are not grounded in visible
   relations.
3. Reference-conditioned ranking can overfit to a small or wrong reference set.
4. Human review packets can become too verbose; the UI must show a compact
   before/after board first, details second.
5. If hard gates are too aggressive, figure-agent will again block the LLM rather
   than amplify it.
6. If hard gates are too weak, creative candidates can become scientifically
   plausible-looking falsehoods.

## Decision

Adopt this as the next figure-agent direction after state-hygiene fixes:

> figure-agent should become a bounded composition search assistant. It should
> amplify LLM visual reasoning by accepting broad structural proposals into a
> safe rendered candidate workflow, then use deterministic evidence, semantic
> invariants, reference-conditioned convention checks, and human-gated selection
> to decide what survives.

This preserves the quality-kernel identity while adding the missing capability:
not just proving a figure is mechanically clean, but helping find a composition
that a human would actually want to use.
