<!-- FIGURE_AGENT:EXECUTION_AUTHORITY -->
# Figure Agent Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:test-driven-development` for each implementation task and
> `superpowers:verification-before-completion` before any completion claim.

**Goal:** Make Figure Agent reduce the correction cost of visual errors and
complex panels while preserving or exceeding the accepted TikZ quality
benchmark, with illustration quality represented as an explicit reusable
contract rather than hidden renderer code.

**Architecture:** Keep TikZ as the production composition baseline. Preserve
the declaration-driven attribution path from rendered findings to panels,
semantic objects, and source selectors. Put a narrow scientific illustration
grammar between semantics and TikZ/SVG backends, beginning with one
`sulfur_trap_domain` motif. Machine evidence and human publication acceptance
remain separate gates.

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

- [x] Write RED tests requiring, for every detector finding, a deterministic
  overlay image, focused crop, and manifest record containing finding ID,
  attribution state, input render hash, pixel bbox, PDF bbox, and output hashes.
- [x] Render distinct, accessible styles for exact, ambiguous, and unbound
  attribution without changing the manuscript artifact.
- [x] Generate artifacts in ordinary compile mode even when findings are
  report-only. Strict mode may change the exit code but not the evidence set.
- [x] Ensure a no-finding compile creates a valid empty manifest and no fake
  crop.
- [x] Verify:

```bash
uv run pytest tests/test_visual_finding_artifacts.py tests/test_strict_mode.py -q
bash scripts/compile.sh examples/<synthetic-fixture>/<synthetic-fixture>.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/<synthetic-fixture>/<synthetic-fixture>.tex
```

- [x] Commit: `feat: emit review overlays and crops for visual findings`

## Task 5: Improve detector precision from reviewed evidence

**Files:**

- Modify: `scripts/detector_feedback_ledger.py`
- Modify: the smallest detector module responsible for the dominant reviewed
  false-positive family
- Create or modify: the matching focused detector test module
- Modify: `benchmarks/visual_attribution_suite.yaml`

- [x] Use the reviewed ledger to select one dominant false-positive family.
  Do not tune against raw finding volume.
- [x] Write a RED regression test for that family while preserving every known
  true positive in the benchmark corpus.
- [x] Make one detector-level repair. Do not add fixture-name checks, accepted
  artifact hashes, or coordinate exceptions.
- [x] Compare before/after reviewed precision, recall, and unbound attribution.
  A lower finding count alone is not success.
- [x] Verify:

```bash
uv run pytest tests/test_detector_feedback_ledger.py \
  tests/test_visual_attribution_suite.py <focused-detector-test> -q
bin/fig-agent helper detector_feedback_ledger.py --json
```

- [x] Commit: `fix: reduce reviewed visual detector false positives`

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

- [x] RED-test a general fragment manifest containing schema version, semantic
  IDs, declared relations, deterministic view box, generator path/hash, input
  hashes, SVG hash, PDF hash, toolchain versions, and TikZ ownership boundary.
- [x] Implement deterministic generation with existing dependencies. Fail with
  a clear prerequisite error when the SVG-to-PDF renderer is unavailable.
- [x] Require the SVG to expose stable IDs used by the manifest; reject orphaned
  manifest IDs and undeclared SVG IDs that claim semantic status.
- [x] Reject scripts, event handlers, external URLs, absolute paths, ambient
  fonts/CSS, and unhashed linked or embedded assets. Rendering runs with network
  access disabled and a declared asset allowlist.
- [x] Compare deterministic rasterizations of SVG and PDF at fixed dimensions;
  reject unexplained geometry, clipping, view-box, or visual-equivalence drift.
- [x] Select the target panel only after source provenance passes. Place only
  its complex geometry in the fragment. Keep global
  panel composition, text, labels, and inter-panel arrows in TikZ.
- [x] Compile from the plugin root using the mandated command:

```bash
bash scripts/compile.sh \
  examples/fig1_hybrid_complex_panel_pilot/fig1_hybrid_complex_panel_pilot.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/fig1_hybrid_complex_panel_pilot/fig1_hybrid_complex_panel_pilot.tex
```

- [x] Store compile logs, manifests, overlays, crops, and hashes as new pilot
  artifacts. Do not overwrite historical Fig1 outputs.
- [ ] Commit: `feat: pilot semantic SVG fragment in forked TikZ fixture`

## Task 7: Compare TikZ-only and hybrid correction cost

**Files:**

- Create: `docs/trials/<date>-hybrid-complex-panel-comparison.md`
- Create inside the pilot fixture: `review/human_scaffold_verdict.yaml`
- Modify: `benchmarks/visual_attribution_suite.yaml`

- [x] Render both variants in one clean environment and record source hashes,
  tool versions, compile commands, output hashes, and failures.
- [x] Write a predeclared comparison protocol with identical starting inputs and
  task boundaries. Count preparation, failed attempts, detector diagnosis,
  rendering, and repair time; do not compare selectively trimmed successful
  runs.
- [x] Compare visual quality, scientific fidelity, source edit size, correction
  minutes, detector findings, actionable attribution rate, and artifact
  reproducibility. Report missing measurements explicitly.
- [x] Require a human scaffold verdict for object relations and a separate
  human artifact verdict for publication quality. Each verdict records a
  `review_input_hash` aggregating the exact artifact, semantic manifest,
  reference-authority manifest, briefing/spec, relations, and toolchain.
- [x] Mark the verdict stale when any bound input changes, even if output bytes
  happen to remain identical.
- [x] Keep the task open when either verdict is absent. Machine gates may mark
  the package `review-ready`, never `publication-accepted`.
- [x] Verify the comparison report against a schema test added beside the
  existing trial/report contract tests.
- [ ] Commit: `docs: record human-reviewed TikZ versus hybrid pilot`

## Task 8: Cross-figure generalization on sulfur-polymer Fig3

**Status:** Machine-complete at clean archive commit `95e29908`; scaffold and
artifact verdicts remain pending, so Slice 3 is open and no publication
acceptance is claimed.

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

- [x] Declare which facts are authoritative in the reference, briefing, spec,
  coordinate hints, editable source, and review history.
- [x] Exercise the same region, attribution, overlay/crop, and fragment contracts
  against the six-panel narrative without importing Fig1-specific coordinates,
  panel names, templates, or private helpers.
- [x] Add one cross-figure test that runs the contract on both Fig1 and Fig3.
- [x] Reproduce from a clean tracked checkout using only declared inputs.
- [x] Preserve the distinction between machine-valid, review-ready, and
  human-accepted. Slice 3 closes only when both human verdicts exist.
- [x] Compile from `plugins/figure-agent/`:

```bash
bash scripts/compile.sh examples/<slice3-name>/<slice3-name>.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/<slice3-name>/<slice3-name>.tex
```

- [x] Commit: `feat: prove semantic attribution across Fig1 and Fig3 families`

## Task 9: Bind the raw semantic-SVG non-promotion decision

The current human observation is that the Fig3 primitive SVG artifact has lower
basic illustration quality than the TikZ benchmark. Record that artifact
rejection against the already-bound review inputs. Do not infer a scaffold
verdict, close Slice 3, or claim that all SVG backends are rejected.

**Files:**

- Modify: `examples/fig3_trap_schematic_slice3_semantic/review/human_scaffold_verdict.yaml`
- Create: `docs/decision-records/2026-07-11-raw-semantic-svg-non-promotion.md`
- Modify: `tests/test_hybrid_comparison_report.py`

- [ ] **Step 1: Write the failing bound-verdict test**

```python
def test_fig3_records_artifact_rejection_without_inventing_scaffold_acceptance() -> None:
    fixture = PLUGIN_ROOT / "examples" / "fig3_trap_schematic_slice3_semantic"
    verdict_path = fixture / "review" / "human_scaffold_verdict.yaml"
    verdict = yaml.safe_load(verdict_path.read_text(encoding="utf-8"))
    binding = validate_human_verdict_bindings(verdict_path, fixture)

    assert binding["stale"] is False
    assert verdict["scaffold_verdict"]["status"] == "pending"
    assert verdict["artifact_verdict"]["status"] == "rejected"
    assert verdict["publication_acceptance"] == "not_claimed"
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
uv run pytest \
  tests/test_hybrid_comparison_report.py::test_fig3_records_artifact_rejection_without_inventing_scaffold_acceptance -q
```

Expected: FAIL because the artifact verdict is still `pending`.

- [ ] **Step 3: Record only the supplied human artifact judgment**

Set `artifact_verdict.status: rejected`, `reviewer: choemun-yeong`, and an
execution-time ISO-8601 `reviewed_at` timestamp. Record that the primitive
geometry, visual density, and cross-panel illustration language fall below the
TikZ comparator.
Leave every scaffold field unchanged and pending. The decision record must say:

```yaml
outcome: retain_experimental
applies_to: raw_semantic_svg_pilot
does_not_reject:
  - semantic SVG as a QA surface
  - grammar-driven SVG backends not yet tested
  - TikZ production composition
publication_acceptance: not_claimed
```

- [ ] **Step 4: Re-run binding and comparison tests**

Run:

```bash
uv run pytest tests/test_hybrid_comparison_report.py -q
```

Expected: PASS with the exact review-input hash still fresh.

- [ ] **Step 5: Commit the bounded decision**

```bash
git add examples/fig3_trap_schematic_slice3_semantic/review/human_scaffold_verdict.yaml \
  docs/decision-records/2026-07-11-raw-semantic-svg-non-promotion.md \
  tests/test_hybrid_comparison_report.py
git commit -m "docs: retain raw semantic SVG as experimental"
```

## Task 10: Add the renderer-neutral illustration grammar contract

This is a rendering contract, not the existing `aesthetic_intent.yaml` review
grammar. The existing aesthetic levers may identify `line_weight_rhythm`,
`hand_craft`, or `cross_panel_grammar` failures, but they must not contain path
geometry or mutate a backend.

**Files:**

- Create: `scripts/illustration_grammar.py`
- Create: `tests/test_illustration_grammar.py`
- Create: `styles/illustration-grammar/sulfur_trap_domain.v1.yaml`

- [ ] **Step 1: Write failing contract tests**

```python
def test_loads_sulfur_trap_domain_with_closed_visual_contract() -> None:
    grammar = load_illustration_grammar(
        PLUGIN_ROOT / "styles/illustration-grammar/sulfur_trap_domain.v1.yaml"
    )
    assert grammar["schema"] == "figure-agent.illustration-grammar.v1"
    assert grammar["motif_family"] == "sulfur_trap_domain"
    assert set(grammar["semantic_slots"]) == {
        "chain.backbones", "sulfur.regions", "sulfur.sites",
        "trap.levels", "trapped.carriers",
    }
    assert grammar["layer_order"] == [
        "sulfur.regions", "chain.backbones", "sulfur.sites",
        "trap.levels", "trapped.carriers",
    ]

@pytest.mark.parametrize("mutation,error", [
    (("schema", "figure-agent.illustration-grammar.v2"), "schema_unsupported"),
    (("motif_family", ""), "motif_family_invalid"),
    (("layer_order", ["chain.backbones"]), "layer_order_incomplete"),
])
def test_grammar_fails_closed(
    tmp_path: Path,
    mutation: tuple[str, object],
    error: str,
) -> None:
    payload = yaml.safe_load(GRAMMAR_PATH.read_text(encoding="utf-8"))
    payload[mutation[0]] = mutation[1]
    candidate = tmp_path / "grammar.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(IllustrationGrammarError, match=error):
        load_illustration_grammar(candidate)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/test_illustration_grammar.py -q`

Expected: FAIL because the loader and grammar file do not exist.

- [ ] **Step 3: Implement the minimal loader and closed motif file**

`scripts/illustration_grammar.py` defines
`IllustrationGrammarError(ValueError)` and
`load_illustration_grammar(path: Path) -> dict[str, Any]`. The loader returns a
normalized mapping only after validating every required slot, relation, visual
token group, layer entry, optical rule, and ownership field.

The motif YAML must declare the five semantic slots, the five-item layer order
above, and these four relations already used by the Fig3 fragment manifest:

```yaml
relations:
  - [sulfur.sites, attached_to, chain.backbones]
  - [sulfur.sites, located_in, sulfur.regions]
  - [trap.levels, co_located_with, sulfur.regions]
  - [trapped.carriers, sits_on, trap.levels]
```

It must also declare these closed token groups:

```yaml
visual_tokens:
  stroke_families: [support, primary, focal]
  color_roles: [polymer, sulfur, carrier, neutral]
  curvature: [organic_backbone]
  joins: [round]
  caps: [round]
  emphasis: [background, structure, focal]
optical_rules:
  minimum_clearance_em: 0.35
  carrier_centering: optical
  repeated_site_variation: controlled
ownership:
  grammar: [motif_geometry, layer_order, visual_tokens]
  tikz: [global_panel_composition, typography, labels, inter_panel_arrows]
```

Reject `aesthetic_levers`, route fields, freeform effects, filters, arbitrary
fonts, and unknown required token groups.

- [ ] **Step 4: Run contract tests and Ruff**

```bash
uv run pytest tests/test_illustration_grammar.py -q
uv run ruff check scripts/illustration_grammar.py tests/test_illustration_grammar.py
```

Expected: PASS.

- [ ] **Step 5: Commit the grammar contract**

```bash
git add scripts/illustration_grammar.py tests/test_illustration_grammar.py \
  styles/illustration-grammar/sulfur_trap_domain.v1.yaml
git commit -m "feat: define sulfur trap illustration grammar"
```

## Task 11: Compile a backend-neutral motif scene

The grammar owns appearance rules; a fixture-local instance owns normalized
geometry and semantic membership. The compiled scene must contain neither SVG
tags nor TikZ commands.

**Files:**

- Create: `scripts/illustration_scene.py`
- Create: `tests/test_illustration_scene.py`
- Create: `examples/fig3_trap_schematic_slice4_illustration_grammar/motif_instance.yaml`
- Create: `examples/fig3_trap_schematic_slice4_illustration_grammar/provenance.yaml`

- [ ] **Step 1: Write the failing neutral-scene test**

```python
def test_scene_preserves_slots_layers_and_has_no_backend_syntax() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    serialized = json.dumps(scene, sort_keys=True)

    assert scene["motif_family"] == "sulfur_trap_domain"
    assert [layer["semantic_id"] for layer in scene["layers"]] == [
        "sulfur.regions", "chain.backbones", "sulfur.sites",
        "trap.levels", "trapped.carriers",
    ]
    assert "<svg" not in serialized
    assert "\\draw" not in serialized
    assert "fig3_trap_schematic" not in serialized
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/test_illustration_scene.py -q`

Expected: FAIL because `compile_illustration_scene` does not exist.

- [ ] **Step 3: Implement normalized scene compilation**

`scripts/illustration_scene.py` defines
`IllustrationSceneError(ValueError)` and
`compile_illustration_scene(grammar_path: Path, instance_path: Path) ->
dict[str, Any]`. The compiler returns normalized `semantic_ids`, `relations`,
`layers`, and `resolved_tokens` fields without backend syntax.

The instance uses a unit-square coordinate system, contains four non-crossing
backbone splines and three sulfur-rich domains, and binds every visible site,
trap level, and carrier to one declared relation. Reject an unknown slot,
crossing relation, point outside `[0, 1]`, missing domain membership, or carrier
without a trap level. Do not import Fig1 coordinates, panel names, templates, or
helpers.

- [ ] **Step 4: Run scene and cross-figure regression tests**

```bash
uv run pytest tests/test_illustration_scene.py \
  tests/test_hybrid_fragment_contract.py -q
uv run ruff check scripts/illustration_scene.py tests/test_illustration_scene.py
```

Expected: PASS.

- [ ] **Step 5: Commit the neutral scene**

```bash
git add scripts/illustration_scene.py tests/test_illustration_scene.py \
  examples/fig3_trap_schematic_slice4_illustration_grammar/motif_instance.yaml \
  examples/fig3_trap_schematic_slice4_illustration_grammar/provenance.yaml
git commit -m "feat: compile backend-neutral sulfur trap scenes"
```

## Task 12: Lower one scene into TikZ and SVG backends

**Files:**

- Create: `scripts/illustration_backend_tikz.py`
- Create: `scripts/illustration_backend_svg.py`
- Create: `scripts/illustration_backend.py`
- Create: `scripts/render_illustration_motif.py`
- Create: `tests/test_illustration_backends.py`
- Create: `styles/illustration-grammar/backends/polymer-tikz.v1.yaml`
- Create: `styles/illustration-grammar/backends/polymer-svg.v1.yaml`

- [ ] **Step 1: Write failing paired-backend tests**

```python
def test_backends_preserve_the_same_semantic_slots() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    tikz = render_tikz(scene, TIKZ_PROFILE_PATH)
    svg = render_svg(scene, SVG_PROFILE_PATH)
    for semantic_id in scene["semantic_ids"]:
        assert f"figure-agent:start {semantic_id}" in tikz
        assert f'id="{semantic_id}"' in svg

def test_unsupported_token_fails_instead_of_falling_back() -> None:
    scene = copy.deepcopy(compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH))
    scene["resolved_tokens"]["curvature"] = "airbrush_blob"
    with pytest.raises(IllustrationBackendError, match="token_unsupported"):
        render_svg(scene, SVG_PROFILE_PATH)

def test_backend_profiles_cover_identical_visual_roles() -> None:
    tikz_profile = load_backend_profile(TIKZ_PROFILE_PATH, backend="tikz")
    svg_profile = load_backend_profile(SVG_PROFILE_PATH, backend="svg")
    assert set(tikz_profile["color_roles"]) == set(svg_profile["color_roles"])
    assert set(tikz_profile["stroke_families"]) == set(svg_profile["stroke_families"])
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/test_illustration_backends.py -q`

Expected: FAIL because neither backend exists.

- [ ] **Step 3: Implement deterministic backend lowering**

`scripts/illustration_backend.py` defines
`IllustrationBackendError(ValueError)` and
`load_backend_profile(path: Path, backend: str) -> dict[str, Any]`.
`illustration_backend_tikz.py` exposes
`render_tikz(scene: dict[str, Any], profile_path: Path) -> str`;
`illustration_backend_svg.py` exposes
`render_svg(scene: dict[str, Any], profile_path: Path) -> str`; and
`render_illustration_motif.py` exposes
`render_pair(grammar: Path, instance: Path, tikz_profile: Path,
svg_profile: Path, output_dir: Path) -> dict[str, Any]`.

The two backend profile files map the same grammar roles to existing TikZ style
tokens and canonical SVG values; a renderer may not invent an undeclared role.
The TikZ output contains geometry only and uses the existing polymer style
palette through its profile. The SVG output contains geometry only, stable semantic group IDs, no
text, scripts, ambient CSS/fonts, external URLs, filters, or raster assets.
`render_pair` runs twice, requires byte-identical TikZ/SVG outputs, writes a
manifest with grammar/instance/source/toolchain hashes, and sets
`publication_acceptance: not_claimed`.

- [ ] **Step 4: Run backend, fragment-security, and lint tests**

```bash
uv run pytest tests/test_illustration_backends.py \
  tests/test_hybrid_fragment_contract.py \
  tests/test_hybrid_fragment_render.py -q
uv run ruff check scripts/illustration_backend_tikz.py \
  scripts/illustration_backend_svg.py scripts/illustration_backend.py \
  scripts/render_illustration_motif.py \
  tests/test_illustration_backends.py
```

Expected: PASS.

- [ ] **Step 5: Commit both backends**

```bash
git add scripts/illustration_backend_tikz.py \
  scripts/illustration_backend_svg.py scripts/illustration_backend.py \
  scripts/render_illustration_motif.py tests/test_illustration_backends.py \
  styles/illustration-grammar/backends/polymer-tikz.v1.yaml \
  styles/illustration-grammar/backends/polymer-svg.v1.yaml
git commit -m "feat: render illustration grammar through TikZ and SVG"
```

## Task 13: Build the paired Fig3 grammar review fixture

Fork the tracked Slice 3 derivative into
`examples/fig3_trap_schematic_slice4_illustration_grammar`. Preserve the source
commit/tree and raw SVG review artifact as immutable comparison inputs. Do not
modify the Slice 3 fixture.

**Files:**

- Create: `examples/fig3_trap_schematic_slice4_illustration_grammar/fig3_trap_schematic_slice4_tikz.tex`
- Create: `examples/fig3_trap_schematic_slice4_illustration_grammar/fig3_trap_schematic_slice4_svg.tex`
- Create: generated `fragments/sulfur_trap_domain.tikz.tex`
- Create: generated `fragments/sulfur_trap_domain.svg`
- Create: generated `fragments/render_manifest.yaml`
- Create: immutable `comparators/raw_svg_slice3/` snapshot plus source receipt
- Create: fixture-local reference, briefing, spec, authority manifest, and semantic boundary files
- Create: `review/comparison_manifest.yaml`
- Create: `review/human_illustration_verdict.yaml`
- Create: review renders, equal-boundary crops, difference image, compile logs, and clean-reproduction receipts
- Modify: `tests/test_illustration_backends.py`

- [ ] **Step 1: Write the failing fixture-boundary test**

```python
def test_slice4_fixture_binds_three_comparable_artifacts() -> None:
    comparison = yaml.safe_load(COMPARISON_MANIFEST.read_text(encoding="utf-8"))
    assert set(comparison["variants"]) == {
        "raw_svg_slice3", "grammar_tikz", "grammar_svg"
    }
    assert comparison["grammar_pair_same_scene"] is True
    assert comparison["raw_svg_comparator_basis"] == "same_semantic_boundary"
    assert comparison["slice3_source_immutable"] is True
    assert comparison["publication_acceptance"] == "not_claimed"

def test_slice4_pending_verdict_is_fresh_and_does_not_claim_acceptance() -> None:
    fixture = PLUGIN_ROOT / "examples" / SLICE4_NAME
    verdict_path = fixture / "review" / "human_illustration_verdict.yaml"
    verdict = yaml.safe_load(verdict_path.read_text(encoding="utf-8"))
    binding = validate_human_verdict_bindings(verdict_path, fixture)

    assert binding["stale"] is False
    assert verdict["raw_svg_vs_grammar_svg"] == "pending"
    assert verdict["grammar_svg_vs_tikz_language"] == "pending"
    assert verdict["publication_acceptance"] == "not_claimed"
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
uv run pytest \
  tests/test_illustration_backends.py::test_slice4_fixture_binds_three_comparable_artifacts -q
```

Expected: FAIL because the paired fixture and manifest do not exist.

- [ ] **Step 3: Generate and compile both grammar variants**

Run from `plugins/figure-agent/`:

```bash
uv run python scripts/render_illustration_motif.py \
  --grammar styles/illustration-grammar/sulfur_trap_domain.v1.yaml \
  --instance examples/fig3_trap_schematic_slice4_illustration_grammar/motif_instance.yaml \
  --tikz-profile styles/illustration-grammar/backends/polymer-tikz.v1.yaml \
  --svg-profile styles/illustration-grammar/backends/polymer-svg.v1.yaml \
  --output-dir examples/fig3_trap_schematic_slice4_illustration_grammar/fragments

bash scripts/compile.sh \
  examples/fig3_trap_schematic_slice4_illustration_grammar/fig3_trap_schematic_slice4_tikz.tex
bash scripts/compile.sh \
  examples/fig3_trap_schematic_slice4_illustration_grammar/fig3_trap_schematic_slice4_svg.tex
```

Expected: both ordinary compiles exit 0. Run strict for both and record its
actual exit and findings without treating strict success as publication
acceptance.

```bash
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/fig3_trap_schematic_slice4_illustration_grammar/fig3_trap_schematic_slice4_tikz.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/fig3_trap_schematic_slice4_illustration_grammar/fig3_trap_schematic_slice4_svg.tex
```

- [ ] **Step 4: Produce equal-boundary review evidence**

First copy the already-bound Slice 3 raw SVG render and Panel e crop into
`comparators/raw_svg_slice3/`; record their original paths, source commit, and
SHA-256 values, and assert the copied bytes match those receipts. Never write
back to the Slice 3 fixture. Then create full renders, identical Panel e crops,
fixed-size grammar-fragment rasters, a grammar-TikZ/grammar-SVG difference
image, source hashes, toolchain versions, compile logs, and clean-archive
two-run receipts. The human verdict begins with:

```yaml
raw_svg_vs_grammar_svg: pending
grammar_svg_vs_tikz_language: pending
grammar_tikz_artifact: pending
grammar_svg_artifact: pending
publication_acceptance: not_claimed
```

Bind all three artifacts, the grammar, instance, compiled grammar scene,
historical raw-SVG comparator receipt, reference, briefing/spec, comparison
manifest, and toolchain under one aggregate review input hash. Reuse the
existing review-binding validator contract so any changed input makes the
verdict stale. The manifest must distinguish the identical neutral scene shared
by grammar TikZ/SVG from the raw SVG's same-semantic-boundary comparison basis.

- [ ] **Step 5: Re-run tests, compile, Ruff, and diff checks**

```bash
uv run pytest tests/test_illustration_grammar.py \
  tests/test_illustration_scene.py tests/test_illustration_backends.py \
  tests/test_hybrid_fragment_contract.py tests/test_hybrid_fragment_render.py -q
uv run ruff check scripts/illustration_*.py \
  scripts/render_illustration_motif.py tests/test_illustration_*.py
git diff --check
```

Expected: machine tests pass and the review packet remains explicitly pending.

- [ ] **Step 6: Commit the review-ready fixture**

```bash
git add examples/fig3_trap_schematic_slice4_illustration_grammar \
  tests/test_illustration_backends.py
git commit -m "feat: prepare paired sulfur trap grammar review"
```

## Task 14: Decide whether the grammar improves the product

- [ ] Require a named human to compare all three bound Panel e crops and record
  whether grammar-SVG improves on raw SVG and whether both grammar outputs share
  the surrounding TikZ illustration language.
- [ ] Reject the grammar implementation if it merely adds schema complexity,
  if TikZ and SVG require different semantic/visual-role definitions, or if the
  SVG result remains visibly inferior to raw or TikZ comparators.
- [ ] Retain the grammar experimentally when it improves raw SVG but does not
  yet match TikZ. When both backends pass the paired human review and clean
  reproduction, advance the motif only to a second materially different figure
  family; one-family evidence cannot promote a production default.
- [ ] Record the decision in `docs/decision-records/`, update this single plan,
  run `tests/test_document_authority.py`, and commit with a message that names
  the actual outcome rather than assuming promotion.
- [ ] Commit the decision record, verdict, and plan update together. Allowed
  messages are `docs: reject sulfur trap illustration grammar`,
  `docs: retain sulfur trap illustration grammar experiment`, or
  `docs: advance sulfur trap grammar to second-family review`.

## Completion boundary

The plan is complete only when:

- visual findings are reviewable and source-actionable without guessed mapping;
- one hybrid complex-panel pilot is reproducible;
- the contracts generalize across Fig1 and sulfur-polymer Fig3;
- the raw SVG non-promotion judgment is bound without inventing a scaffold
  verdict;
- one `sulfur_trap_domain` grammar lowers through TikZ and SVG from the same
  neutral scene;
- the three-way raw-SVG/grammar-TikZ/grammar-SVG human verdict is recorded; and
- the grammar decision is recorded with clean-reproduction evidence.

Passing tests, strict compile, or machine gates alone cannot satisfy this
completion boundary.
