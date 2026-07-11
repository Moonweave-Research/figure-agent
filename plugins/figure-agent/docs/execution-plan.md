<!-- FIGURE_AGENT:EXECUTION_AUTHORITY -->
# Figure Agent Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:test-driven-development` for each implementation task and
> `superpowers:verification-before-completion` before any completion claim.

**Goal:** Make Figure Agent reduce the correction cost of visual errors and
complex panels while preserving or exceeding the accepted TikZ quality
benchmark.

**Architecture:** Keep TikZ as the production composition baseline. Add a
declaration-driven attribution path from rendered findings to panels, semantic
objects, and source selectors; then validate one Python-generated semantic SVG
fragment inside a forked TikZ fixture. Machine evidence and human publication
acceptance remain separate gates.

**Tech Stack:** Python 3.11+, pytest, PyYAML, existing figure-agent CLI/helpers,
TikZ/LuaLaTeX, dvisvgm, deterministic SVG/PDF/PNG artifacts. Add no dependency
without explicit approval.

---

## 0. Execution rules

This is the single active forward plan. `docs/product-spec.md` defines the
product boundary. Architecture notes, roadmaps, milestones, issue ledgers,
fixture plans, and experiments may provide evidence but do not reorder this
plan.

For every task:

1. work in a clean dedicated worktree and `codex/` branch;
2. preserve historical fixtures and accepted artifacts;
3. write the smallest failing test first;
4. implement only enough general behavior to pass it;
5. run the targeted test, then the affected suite;
6. run `git diff --check` and `uv run ruff check` on changed Python;
7. commit a small, reviewable slice with the evidence named in the message; and
8. never equate a machine gate with publication acceptance.

All commands below run from `plugins/figure-agent/` unless stated otherwise.
The plan names intended files; an implementer must inspect current code first
and reuse an existing module when it already owns the responsibility.

## Task 0: Establish the two-document authority contract

**Files:**

- Create: `docs/product-spec.md`
- Create: `docs/execution-plan.md`
- Create: `tests/test_document_authority.py`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `skills/figure-agent/SKILL.md`
- Modify: `docs/architecture-overview.md`
- Modify: repository root `README.md`
- Modify: prior product-direction and execution-plan documents listed in
  `tests/test_document_authority.py`

- [x] Write a failing test that requires exactly one product-authority marker
  and one execution-authority marker, requires every agent entry point to link
  both canonical documents, and requires superseded documents to declare
  themselves non-authoritative.
- [x] Add the canonical documents and redirect entry points.
- [x] Preserve old documents in place as evidence; add only an unambiguous
  status banner and canonical pointers.
- [x] Update any release-contract test that treats an old direction document as
  active.
- [x] Verify:

```bash
uv run pytest tests/test_document_authority.py tests/test_readme_identity.py \
  tests/test_release_contract.py tests/test_command_contract_docs.py \
  tests/test_doc_rot_architecture.py -q
uv run ruff check .
git diff --check
```

- [x] Commit: `docs: establish single product and execution authority`

## Task 1: Freeze the TikZ benchmark and defect corpus

**Files:**

- Create: `benchmarks/visual_attribution_suite.yaml`
- Create: `tests/fixtures/visual_attribution/`
- Create: `tests/test_visual_attribution_suite.py`
- Modify: `benchmarks/quality_suites.yaml`
- Modify: `scripts/quality/quality_benchmark.py`

- [x] Define a small corpus containing true collision/clash findings, accepted
  false positives, panel boundaries, semantic region declarations, and expected
  attribution states (`exact`, `ambiguous`, `unbound`). Use synthetic fixtures
  for contract edge cases and immutable copies of reviewed evidence for realism.
- [x] Record baseline metrics: finding count, reviewed true positives, reviewed
  false positives, exact attribution rate, ambiguous rate, unbound rate, and
  human correction minutes. Unknown measurements are represented as `null`, not
  invented estimates.
- [x] Add a test proving that a fixture-specific name or hard-coded coordinate
  cannot determine the expected result.
- [x] Integrate the suite as an opt-in benchmark; do not add publication claims
  to the machine output.
- [x] Verify:

```bash
uv run pytest tests/test_visual_attribution_suite.py tests/test_quality_benchmark.py -q
bin/fig-agent benchmark-run --suite visual-attribution --json
```

- [x] Commit: `test: lock visual attribution benchmark corpus`

## Task 2: Declare semantic regions and source selectors

**Files:**

- Create: `scripts/semantic_region_contract.py`
- Create: `tests/test_semantic_region_contract.py`
- Modify: `scripts/inputs.py`
- Modify: `README.md`
- Modify: `docs/architecture-overview.md`

- [x] Write RED tests for a fixture-local `semantic_regions.yaml` contract with
  this minimum shape:

```yaml
schema: figure-agent.semantic-regions.v1
page_geometry:
  coordinate_space: pdf_cm
  page_index: 0
  origin: bottom_left
  media_box_pdf_cm: [0.0, 0.0, 17.8, 10.0]
  crop_box_pdf_cm: [0.0, 0.0, 17.8, 10.0]
  rotation_deg: 0
  render_geometry_hash: sha256:<hash>
regions:
  - id: target_panel.complex_region
    panel_id: TARGET
    role: potential_profile
    bbox_pdf_cm: [10.1, 0.8, 12.9, 3.2]
    source:
      path: fig1_hybrid_complex_panel_pilot.tex
      selector_id: target_panel.complex_region
      anchor_start: "% figure-agent:start target_panel.complex_region"
      anchor_end: "% figure-agent:end target_panel.complex_region"
      source_sha256: sha256:<hash>
      line_start: 210
      line_end: 248
    provenance: declared_by_author
```

- [x] Reject duplicate IDs or anchors, invalid boxes, unsafe paths, reversed
  line ranges, unknown panels, out-of-page boxes, selectors outside the named
  source, and page/render geometry that does not match the detector render.
- [x] Treat line ranges as regenerated review snapshots. Resolve identity from
  `selector_id` plus unique anchors; missing, duplicated, or stale anchors are
  `ambiguous`/`unbound` and never silently relocated by line proximity.
- [x] Normalize coordinates without fixture-specific offsets. Reuse existing
  `bbox_pdf_cm` parsing and page-geometry helpers where possible.
- [x] Emit stable normalized JSON and source/input hashes for downstream tools.
- [x] Verify:

```bash
uv run pytest tests/test_semantic_region_contract.py tests/test_inputs.py \
  tests/test_spec_bbox_helper.py -q
```

- [x] Commit: `feat: validate declared semantic regions and source selectors`

## Task 3: Attribute visual findings without guessing

**Files:**

- Create: `scripts/visual_finding_attribution.py`
- Create: `tests/test_visual_finding_attribution.py`
- Modify: the existing collision/clash result assembly module discovered by
  tracing the current output schema
- Modify: `scripts/critique_schema_validator.py` only if the public critique
  schema must carry the new attribution block

- [x] Write RED tests for bbox intersection with panel and semantic regions.
- [x] Return `exact` only when one valid region wins through an explicitly
  declared containment/priority relationship. Area, nearest-center, and DOM
  order are not implicit tie-breakers. Return `ambiguous` with every candidate
  for undeclared overlap; return `unbound` when no declaration applies.
- [x] Copy the declared source selector into the finding only after validating
  the source hash. Never synthesize `tex_lines` from spatial proximity alone.
- [x] Preserve the original detector bbox and confidence so attribution cannot
  hide detector uncertainty.
- [x] Add regression tests for top-left pixel versus bottom-left PDF origins,
  DPI changes, MediaBox/CropBox differences, page rotation, page index, fragment
  transforms, boundary-touching boxes, nested regions, missing declarations,
  stale source/render-geometry hashes, and malformed detector output.
- [x] Verify:

```bash
uv run pytest tests/test_visual_finding_attribution.py \
  tests/test_visual_attribution_suite.py tests/test_critique_schema_validator.py -q
```

- [x] Commit: `feat: map visual findings to declared source regions`

## Task 4: Always produce attribution overlays and crops

**Files:**

- Create: `scripts/visual_finding_artifacts.py`
- Create: `tests/test_visual_finding_artifacts.py`
- Modify: `scripts/compile.sh`
- Modify: the perception-pack manifest writer that currently owns
  `build/perception/`

- [ ] Write RED tests requiring, for every detector finding, a deterministic
  overlay image, focused crop, and manifest record containing finding ID,
  attribution state, input render hash, pixel bbox, PDF bbox, and output hashes.
- [ ] Render distinct, accessible styles for exact, ambiguous, and unbound
  attribution without changing the manuscript artifact.
- [ ] Generate artifacts in ordinary compile mode even when findings are
  report-only. Strict mode may change the exit code but not the evidence set.
- [ ] Ensure a no-finding compile creates a valid empty manifest and no fake
  crop.
- [ ] Verify:

```bash
uv run pytest tests/test_visual_finding_artifacts.py tests/test_strict_mode.py -q
bash scripts/compile.sh examples/<synthetic-fixture>/<synthetic-fixture>.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/<synthetic-fixture>/<synthetic-fixture>.tex
```

- [ ] Commit: `feat: emit review overlays and crops for visual findings`

## Task 5: Improve detector precision from reviewed evidence

**Files:**

- Modify: `scripts/detector_feedback_ledger.py`
- Modify: the smallest detector module responsible for the dominant reviewed
  false-positive family
- Create or modify: the matching focused detector test module
- Modify: `benchmarks/visual_attribution_suite.yaml`

- [ ] Use the reviewed ledger to select one dominant false-positive family.
  Do not tune against raw finding volume.
- [ ] Write a RED regression test for that family while preserving every known
  true positive in the benchmark corpus.
- [ ] Make one detector-level repair. Do not add fixture-name checks, accepted
  artifact hashes, or coordinate exceptions.
- [ ] Compare before/after reviewed precision, recall, and unbound attribution.
  A lower finding count alone is not success.
- [ ] Verify:

```bash
uv run pytest tests/test_detector_feedback_ledger.py \
  tests/test_visual_attribution_suite.py <focused-detector-test> -q
bin/fig-agent helper detector_feedback_ledger.py --json
```

- [ ] Commit: `fix: reduce reviewed visual detector false positives`

## Task 6: Build one semantic SVG fragment pilot

**Source authority gate:** The locally observed
`fig1_overview_v5f_v013_dogfood_001_vault` directory contains generated
`build/` and `exports/` evidence but no tracked editable source in this branch or
its visible Git history. It is a visual comparison artifact, not a fork source.
Do not import it from a user worktree or reconstruct source from its PDF/SVG.

Before implementation, select a tracked Fig1-family editable source and record
its source commit and tree hash in `benchmarks/hybrid_pilot_source.yaml`. The source
package must contain TeX, briefing, spec, declared reference inputs, and a
reproducible baseline render. If no candidate satisfies this provenance gate,
Task 6 is blocked and the pilot fixture must not be created. Fork the verified
source into `examples/fig1_hybrid_complex_panel_pilot`; never edit the
benchmark in place.

**Files:**

- Create: `scripts/hybrid/fragment_contract.py`
- Create: `scripts/hybrid/render_fragment.py`
- Create: `tests/test_hybrid_fragment_contract.py`
- Create: `tests/test_hybrid_fragment_render.py`
- Create: `benchmarks/hybrid_pilot_source.yaml`
- Create inside the forked fixture: `fragments/complex_panel_fragment.py`
- Create inside the forked fixture: `fragments/complex_panel_fragment.svg`
- Create inside the forked fixture: `fragments/complex_panel_fragment.pdf`
- Create inside the forked fixture: `fragments/fragment_manifest.json`
- Modify only inside the forked fixture: its `.tex`, `spec.yaml`, briefing,
  authoring plan, and review artifacts

- [ ] RED-test a general fragment manifest containing schema version, semantic
  IDs, declared relations, deterministic view box, generator path/hash, input
  hashes, SVG hash, PDF hash, toolchain versions, and TikZ ownership boundary.
- [ ] Implement deterministic generation with existing dependencies. Fail with
  a clear prerequisite error when the SVG-to-PDF renderer is unavailable.
- [ ] Require the SVG to expose stable IDs used by the manifest; reject orphaned
  manifest IDs and undeclared SVG IDs that claim semantic status.
- [ ] Reject scripts, event handlers, external URLs, absolute paths, ambient
  fonts/CSS, and unhashed linked or embedded assets. Rendering runs with network
  access disabled and a declared asset allowlist.
- [ ] Compare deterministic rasterizations of SVG and PDF at fixed dimensions;
  reject unexplained geometry, clipping, view-box, or visual-equivalence drift.
- [ ] Select the target panel only after source provenance passes. Place only
  its complex geometry in the fragment. Keep global
  panel composition, text, labels, and inter-panel arrows in TikZ.
- [ ] Compile from the plugin root using the mandated command:

```bash
bash scripts/compile.sh \
  examples/fig1_hybrid_complex_panel_pilot/fig1_hybrid_complex_panel_pilot.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/fig1_hybrid_complex_panel_pilot/fig1_hybrid_complex_panel_pilot.tex
```

- [ ] Store compile logs, manifests, overlays, crops, and hashes as new pilot
  artifacts. Do not overwrite historical Fig1 outputs.
- [ ] Commit: `feat: pilot semantic SVG fragment in forked TikZ fixture`

## Task 7: Compare TikZ-only and hybrid correction cost

**Files:**

- Create: `docs/trials/<date>-hybrid-complex-panel-comparison.md`
- Create inside the pilot fixture: `review/human_scaffold_verdict.yaml`
- Modify: `benchmarks/visual_attribution_suite.yaml`

- [ ] Render both variants in one clean environment and record source hashes,
  tool versions, compile commands, output hashes, and failures.
- [ ] Write a predeclared comparison protocol with identical starting inputs and
  task boundaries. Count preparation, failed attempts, detector diagnosis,
  rendering, and repair time; do not compare selectively trimmed successful
  runs.
- [ ] Compare visual quality, scientific fidelity, source edit size, correction
  minutes, detector findings, actionable attribution rate, and artifact
  reproducibility. Report missing measurements explicitly.
- [ ] Require a human scaffold verdict for object relations and a separate
  human artifact verdict for publication quality. Each verdict records a
  `review_input_hash` aggregating the exact artifact, semantic manifest,
  reference-authority manifest, briefing/spec, relations, and toolchain.
- [ ] Mark the verdict stale when any bound input changes, even if output bytes
  happen to remain identical.
- [ ] Keep the task open when either verdict is absent. Machine gates may mark
  the package `review-ready`, never `publication-accepted`.
- [ ] Verify the comparison report against a schema test added beside the
  existing trial/report contract tests.
- [ ] Commit: `docs: record human-reviewed TikZ versus hybrid pilot`

## Task 8: Cross-figure generalization on sulfur-polymer Fig3

**Fixture:** Recover `examples/fig3_trap_schematic_v97` from source commit
`eaed8fb165e801e13cea3078f832496a011fa2f9`, fixture tree
`6966d9cf193a34debc1ecfcd5d2a1d1aff1845e5`, into a new Slice 3 output
fixture. Record that commit, tree, and every imported file hash before
implementation. Preserve the reference, briefing, spec, coordinate hints,
editable TeX, and review history as immutable inputs. Do not modify or
overwrite the historical Fig3 artifact.

**Files:**

- Create: a new Slice 3 fixture directory with an explicit source-fixture link
- Create: `reference_authority_manifest.yaml`
- Create: `semantic_regions.yaml`
- Create: Slice 3 provenance, clean-reproduction, and human-verdict artifacts
- Modify: general contracts only when a failing cross-figure test proves a real
  abstraction gap

- [ ] Declare which facts are authoritative in the reference, briefing, spec,
  coordinate hints, editable source, and review history.
- [ ] Exercise the same region, attribution, overlay/crop, and fragment contracts
  against the six-panel narrative without importing Fig1-specific coordinates,
  panel names, templates, or private helpers.
- [ ] Add one cross-figure test that runs the contract on both Fig1 and Fig3.
- [ ] Reproduce from a clean tracked checkout using only declared inputs.
- [ ] Preserve the distinction between machine-valid, review-ready, and
  human-accepted. Slice 3 closes only when both human verdicts exist.
- [ ] Compile from `plugins/figure-agent/`:

```bash
bash scripts/compile.sh examples/<slice3-name>/<slice3-name>.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/<slice3-name>/<slice3-name>.tex
```

- [ ] Commit: `feat: prove semantic attribution across Fig1 and Fig3 families`

## Task 9: Decide production promotion

**Files:**

- Modify: `docs/product-spec.md` only if the evidence satisfies its promotion
  rules
- Modify: `docs/execution-plan.md` to record the next measured bottleneck
- Modify: operator docs and status schemas only after a production decision

- [ ] Assemble a decision packet containing benchmark deltas, clean-reproduction
  receipts, provenance manifests, unresolved defects, and both families' human
  verdicts.
- [ ] Choose exactly one outcome: retain experimental hybrid, promote hybrid for
  declared panel classes, or reject the approach.
- [ ] Do not promote when evidence covers only one figure family, review is
  pending, or gains depend on fixture-specific code.
- [ ] If promoted, add an end-to-end release contract before changing the
  default workflow. If retained or rejected, preserve evidence and remove no
  production path merely to make the decision look cleaner.
- [ ] Commit the decision and update this plan so the next agent has one
  unambiguous active task sequence.

## Completion boundary

The plan is complete only when:

- visual findings are reviewable and source-actionable without guessed mapping;
- one hybrid complex-panel pilot is reproducible;
- the contracts generalize across Fig1 and sulfur-polymer Fig3;
- human scaffold and artifact verdicts exist for both evaluated families; and
- the production-promotion decision is recorded with evidence.

Passing tests, strict compile, or machine gates alone cannot satisfy this
completion boundary.
