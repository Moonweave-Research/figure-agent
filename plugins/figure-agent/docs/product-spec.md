<!-- FIGURE_AGENT:LEGACY_EVIDENCE -->
# Figure Agent Product Specification

**Status:** Historical evidence — non-authoritative.

**Effective date:** 2026-07-14

**Superseded by:** `docs/figure-agent.md`.

**Execution warning:** Everything below this boundary is quoted historical
evidence. Historical instructions, checklists, commands, and any internal
"active", "current", or "authority" language MUST NOT be executed or treated
as current. All such language is superseded by `docs/figure-agent.md`.

**Preservation rule:** Retained in place for provenance only.

## 1. Authority contract

This is the single active product specification for Figure Agent. It defines
the product identity, durable boundaries, architecture, evidence model, and
promotion rules. The only active forward execution authority is
docs/execution-plan.md.

All other roadmaps, architecture notes, milestone records, experiments, and
fixture-local plans are operational references or historical evidence. They may
explain how the product reached the current state, but they do not set product
direction. Code, tests, manifests, and generated artifacts remain the authority
for what is implemented now.

The previous product question -- whether Figure Agent should replace TikZ with
SVG or build a complete drawing grammar -- is closed as the top-level framing.
TikZ, SVG, PDF, and PNG are representations in a larger control system. None of
them is the product identity.

## 2. Product identity

Figure Agent is not a model that competes with an LLM at drawing. It uses an LLM
and therefore must not claim an independent general drawing intelligence.

Figure Agent exists to convert unconstrained LLM-authored scientific figures
into artifacts that are:

- scientifically constrained;
- visually inspectable at whole, panel, object, and zoom scales;
- attributable from a rendered defect to a semantic object and editable source;
- locally repairable without uncontrolled regeneration;
- reproducible from declared inputs;
- provenance-complete; and
- explicitly bounded by human scientific and publication review.

The operating sentence is:

> Let the LLM propose freely. Make Figure Agent constrain, observe, localize,
> repair, reproduce, and prove.

The product succeeds when LLM plus Figure Agent produces fewer scientific and
visual defects, requires less human correction, and preserves more editability
than the same LLM working without Figure Agent. It does not succeed merely
because Figure Agent can generate a figure or pass machine checks.

## 3. Strategic premise

### 3.1 What remains with the LLM

The LLM remains the primary source of open-ended visual synthesis:

- narrative interpretation;
- analogy and metaphor;
- composition proposals;
- stylistic exploration;
- freeform TikZ or SVG authoring;
- alternative generation; and
- high-level repair hypotheses.

Figure Agent must not reproduce these general capabilities with a rigid internal
illustrator language unless repeated evidence proves that a narrow contract is
necessary.

### 3.2 What Figure Agent owns

Figure Agent owns the failure classes for which unconstrained LLM behavior is
persistently unreliable:

1. scientific object and relation preservation;
2. cross-panel and cross-iteration consistency;
3. paper-scale typography, stroke, spacing, and collision checks;
4. visual hierarchy and semantic salience constraints;
5. multi-scale defect observation and localization;
6. source attribution without invented mappings;
7. bounded repair with protected invariants and rollback;
8. deterministic reproduction and provenance;
9. evidence-backed learning from accepted and rejected repairs; and
10. an explicit boundary between machine evidence and human acceptance.

Semantic legibility is part of that ownership boundary. It includes
object-role legibility and connector endpoint and purpose legibility. It also
includes label ownership, unnecessary glyphs and false apparatus topology.
These are not minor taste defects: they determine whether a reader infers the
declared scientific apparatus and relation rather than an unintended one.

### 3.3 Durable value test

Every product change must answer at least one of these questions:

- Does it detect a recurring defect that the LLM commonly misses?
- Does it bind that defect to the correct object, relation, or source selector?
- Does it prevent a scientifically invalid or visually incoherent edit?
- Does it repair a bounded region while preserving declared invariants?
- Does it reduce human correction time on a later figure?
- Does it make the result reproducible or its uncertainty more honest?

A fixture-specific coordinate adjustment that answers none of these questions is
figure production, not Figure Agent development. It may be useful evidence, but
it must not be promoted as a product capability.

Figure production is not Figure Agent product development.

## 4. Constraint-sandwich architecture

Figure Agent surrounds, rather than replaces, LLM authoring.

```text
references + scientific intent + declared invariants
                         |
                         v
              pre-authoring context contract
                         |
                         v
        free LLM authoring in TikZ, SVG, or hybrid form
                         |
                         v
       deterministic render + semantic observation model
                         |
                         v
 whole -> panel -> object/relation -> contact/edge/label zoom
                         |
                         v
      defect localization -> bounded repair candidates
                         |
                         v
       regression proof + reproducibility + provenance
                         |
                         v
              named human review and decision
```

The pre-authoring contract must remain smaller than the generated artifact. It
states scientific facts, protected relations, forbidden implications, panel
roles, salience roles, and output constraints. It must not prescribe every path
or coordinate and thereby suppress the LLM's useful expressive ability.

Read-only authoring context packs remain durable paper-specific knowledge
compilation. They are not LLM prompt plumbing, not prompt-loop revival, and not
automatic physics detection. They may expose declared facts to an authoring
agent, but they do not call a model, invent scientific truth, or authorize a
generation executor.

The post-authoring system must not merely produce a score. It must make failures
observable, attributable, and repairable.

## 5. Canonical model

### 5.1 Intent and authority

Each active figure declares authoritative inputs and their roles. Reference
pixels, briefing text, specification, editable source, review history, and
coordinate hints do not have interchangeable authority.

Declared scientific truth includes required objects, required relations,
forbidden objects or implications, narrative role, and uncertainty. Inferred
truth from OCR, vision, DOM grouping, or pixel similarity remains evidence until
a deterministic declaration or named human decision promotes it.

### 5.2 Semantic visual object model

Figure Agent uses a small renderer-neutral model, not a complete scene graph.
Each declared object or relation may carry:

- stable semantic ID;
- panel and narrative role;
- scientific meaning;
- relation endpoints and direction;
- visual salience role;
- layer and occlusion ownership;
- source ownership and stable selector ID;
- render geometry and coordinate-space binding;
- protected invariants;
- review state and provenance.

Line ranges are review snapshots, not durable identity. A durable selector uses
a stable selector ID plus explicit anchors and a source hash.

### 5.3 Representation roles

| Surface | Role |
| --- | --- |
| TikZ/TeX | Current strongest composition, typography, and manuscript assembly baseline |
| SVG | Inspectable vector authoring or fragment surface with stable semantic IDs |
| Python | Contracts, geometry, detectors, attribution, repair planning, manifests, and provenance |
| PDF | Deterministic vector assembly and manuscript artifact |
| PNG | Canonical raster review and vision input |
| overlays and crops | Localized diagnostic evidence |
| LLM | Open-ended proposal, authoring, and repair-hypothesis generation |
| human review | Scientific meaning and publication-quality acceptance |

TikZ/TeX is the default publication-authoring path because it is the strongest
current baseline for manuscript composition, typography, mathematical geometry,
and reproducibility. This operating default does not make TikZ the product
identity and does not prevent a bounded alternative from earning promotion with
cross-family human evidence.

SVG is a derived export, inspection, interchange, or bounded fragment surface.
It may carry stable semantic IDs when the originating renderer can prove the
mapping. It is not a co-equal default publication backend, and editability or a
passing schema does not establish visual quality. The existing TikZ-to-SVG
export remains an output path; this product direction does not reopen backend
selection or create a second SVG-polish engine.

Python is the control plane for contracts, orchestration, geometry, detectors,
attribution, bounded repair, rollback, manifests, provenance, and review
artifacts. It is not the default drawing language. In particular,
fixture-specific handcrafted SVG coordinates are figure-production evidence and
must not accumulate as reusable Python product logic.

No fragment may depend on network access, mutable external URLs, ambient fonts,
or unhashed local assets.

## 6. Failure ontology

The product organizes reviewed failures into eight non-interchangeable classes:

1. semantic -- missing, invented, or misrepresented scientific meaning;
2. relation -- incorrect attachment, direction, containment, overlap, or causal link;
3. geometry -- broken contours, crossings, clipping, malformed shapes, or alignment;
4. composition -- incorrect panel orientation, hierarchy, density, or narrative flow;
5. typography -- collision, illegibility, inconsistent scale, or unsuitable hierarchy;
6. style -- incoherent stroke, color role, curvature, corner, cap, join, or repetition;
7. finish -- dangling endpoints, incomplete outlines, awkward contacts, or optical misalignment;
8. reproducibility -- stale, unbound, nondeterministic, or provenance-incomplete artifacts.

Every finding records its observation scale, confidence, evidence source, and
attribution state. A detector that cannot distinguish these classes must not
silently collapse them into one quality score.

## 7. Multi-scale observation and actionable attribution

The canonical review ladder is:

```text
whole figure -> panel -> semantic object/relation -> zoomed finish region
```

Whole-figure review owns narrative and hierarchy. Panel review owns local
composition and density. Object/relation review owns scientific fidelity and
attachment. Zoom review owns contacts, contours, labels, stroke termination,
and micro-finish.

A machine finding becomes actionable only when this chain is preserved:

```text
rendered bbox -> panel -> declared semantic object/relation -> source selector
```

Attribution is exact, ambiguous, or unbound. Missing, duplicated, overlapping,
or stale declarations must degrade to ambiguous or unbound. Figure Agent must
never guess a source location merely to enable automation.

Every actionable finding produces a focused crop, an overlay, the relevant
semantic declaration, the selector snapshot, and a render-geometry hash.
An audit-crop hash is insufficient by itself: if its manifest predates the
current build render, the crop is stale and must degrade to unbound until the
evidence pack is regenerated.

A declarative contract does not prove rendered semantic legibility. A
deterministic gate can require every salient object to declare a role, every
visible connector to declare both endpoints, its purpose, and a render-style
family, and every label to declare one owner. Connector style must agree with
role: a mechanical attachment cannot reuse an electrical-lead style merely
because both are lines. Whether those declarations are actually legible in the
render remains pending until named human or independent visual review records
the observed reading. Machine-valid declarations therefore cannot authorize
publication acceptance.

The active renderer-neutral evidence contract is
`figure-agent.semantic-legibility-evidence.v1`. It hash-binds the full-figure
and canonical page rasters, page geometry, focused crops, semantic declaration,
authenticated source-selector snapshot, and aggregate `review_input_hash`.
Authority conflict, missing or stale binding, duplicate provenance or selector,
render-hash drift, and cross-semantic selector substitution fail closed to
review-only rather than becoming repair authority. Publishing is transactional
and versioned: a failed refresh preserves the prior packet, and successful
refresh removes only obsolete generated crops while preserving human-owned
files. An `exact` machine attribution still requires human review; it claims
neither semantic preservation nor publication acceptance.

When electrical topology is scientifically relevant, the contract also declares
electrical object states and source/return connections. An object declared
floating cannot be an endpoint of an electrical connection; a ground reference
must identify the circuit node it actually belongs to rather than merely appear
near the apparatus. When a fixture's conductivity is not established by the
authority packet, declare it `electrically_unmodeled`: omit electrical
connections without inventing either an insulating or conducting material.

## 8. Bounded repair contract

The primary execution capability is controlled local repair, not complete
regeneration. A repair candidate declares:

- target defect, object, relation, and source selector;
- preconditions and source hashes;
- allowed files, semantic blocks, and parameters;
- protected objects, relations, labels, and styles;
- expected defect movement;
- source and rendered-change budgets;
- required verification;
- rollback operation; and
- human-review requirement.

Initial reusable repair families should remain small:

- label reflow and scale correction;
- close or complete a contour;
- align or simplify a contact;
- restore a declared relation;
- reduce or increase semantic salience;
- normalize stroke and color roles;
- repair clipping or view-box ownership;
- rebalance a declared panel subregion.

The LLM may propose candidate parameters or source edits. Figure Agent validates
the repair boundary before application and proves semantic and visual regression
conditions afterward. An unbound finding is review-only and cannot trigger an
automatic edit.

The fail-closed source-binding path uses
`figure-agent.source-selector-registry.v1`,
`figure-agent.finding-source-attribution.v1`, and
`figure-agent.repair-target-contract.v1`. Rendered text must match a declared
selector alias, and exactly one matching selector must be declared movable;
otherwise attribution remains ambiguous or unbound.
The canonical CLI is `fig-agent text-finding-attribution`; the shorter
`finding-attribution` spelling is a compatibility alias. This token-first path
does not replace geometry-first region attribution in
`visual_finding_attribution.py`.

The active authoring control plane also preserves
`figure-agent.authoring-visual-assets.v1`,
`figure-agent.layout-lanes.v1`,
`figure-agent.authoring-execution-input-audit.v1`,
`figure-agent.authoring-execution-packet.v1`,
`figure-agent.authoring-execution-preflight.v1`,
`figure-agent.authoring-execution-receipt.v1`,
`figure-agent.repair-execution-packet.v3`, and
`figure-agent.shape-profile.v1`, and
`figure-agent.composition-profile.v1` as evidence contracts. Their machine-valid
state remains subordinate to rendered and human review.

## 9. Evidence and learning loop

Each attempt records the input authority, model and tool receipt, source and
render hashes, findings before and after, applied repair family, protected
invariants, rollback state, and human outcome.

When filesystem read isolation is unavailable, a clean-room authoring claim
also binds an allowlist of repository content reads into the authoring packet
and audits the execution transcript. An undeclared repository content read
makes that run comparison-ineligible even if its output path, source hash, and
compile are otherwise valid. Transcript auditing is bounded evidence, not an
attestation that unobserved reads were impossible.

The minimum source binding is a tracked editable source plus its source commit
and tree hash. A selector snapshot records `selector_id`, `anchor_start`, and
the selected content hash; line numbers are informative only. Render evidence
binds the page hash, full-render hash, crop rectangle and coordinate space, crop
hash, and aggregate `review_input_hash`.

TikZ-to-SVG export packets remain derived evidence. They bind unchanged-source,
PDF, SVG, and sidecar-mapping hashes plus the conversion receipt; conversion may
not silently rewrite the editable TikZ source. Such a packet always records
`publication_acceptance: not_claimed`. Clean-room tasks preserve the historical
`target_crop_forbidden` boundary and remain
`blocked_pending_independent_semantic_packet` until an independently authored,
hash-bound semantic packet exists.

The learning unit is not "this image looked better." It is:

```text
figure context + failure class + repair family + measured movement + human verdict
```

Rejected and neutral attempts are retained as evidence. They prevent repeated
micro-patches, reveal false-positive detectors, and show when the system needs a
new observation or repair primitive rather than another LLM retry.

## 10. Benchmark and proof model

Figure Agent is evaluated by an ablation with fixed model, input, budget, and
starting artifact:

- A: raw LLM authoring;
- B: the same LLM plus Figure Agent contracts and verification;
- C: the same LLM plus contracts, verification, and bounded repair.

Evaluation must cover at least two materially different scientific figure
families and include complex panels. Metrics remain separate:

- scientific fidelity failures;
- verified visual defects by failure class;
- actionable attribution rate;
- repair success and regression rate;
- human correction minutes and intervention count;
- clean reproduction rate;
- editability and provenance completeness; and
- named human blinded quality verdict.

Scores cannot compensate for scientific failure. A candidate with a missing or
invented material relation fails regardless of aesthetic quality.

Historical clean-room Test A — reference reconstruction and
Test B — semantic synthesis remain useful evidence, but they no longer define
the product north star. Each uses a separately hashed input packet. A passing
product-direction claim still requires two independent cold-reproduction tasks.
Any session that observed protected implementation details remains ineligible to
author either the semantic packet or clean-room SVG artifacts for that benchmark.

## 11. Illustration grammar policy

A full drawing grammar is not the default strategy. The previous sulfur-trap
grammar demonstrated deterministic semantic lowering but did not achieve the
required artifact quality. That result is retained as evidence.

New grammar work is allowed only when the failure corpus proves that:

1. the same visual-control failure recurs across materially different figures;
2. prompting, bounded repair, and simpler style constraints do not solve it;
3. a narrow renderer-neutral contract can express the missing control;
4. at least two backends preserve the same semantic and visual roles; and
5. human review shows an actual quality or correction-cost improvement.

Grammar should encode reusable invariants such as semantic salience, layer
ownership, stroke roles, curvature families, controlled repetition, and optical
alignment. It must not become an Illustrator clone or prescribe arbitrary page
geometry.

## 12. Acceptance model

Figure Agent separates three states:

1. Machine-valid: schemas, compilation, hashes, manifests, safety, and declared checks pass.
2. Review-ready: overlays, crops, attribution, provenance, and comparisons exist.
3. Human-accepted: a named human accepts scientific meaning and publication quality.

Machine-valid is not publication-accepted. Review-ready is not publication-
accepted. Missing human review is pending, not success.

A verdict binds an aggregate review-input hash covering the exact rendered
artifact, semantic declarations, reference authority, briefing/specification,
object relations, source state, and toolchain. Any bound-input change makes the
verdict stale.

## 13. Promotion rules

A detector, repair family, representation, or grammar becomes a general product
capability only when:

- it addresses a named recurring failure class;
- it passes cross-fixture tests without fixture-name or coordinate special cases;
- it improves the A/B/C benchmark on at least two materially different families;
- it does not hide real defects or weaken scientific fidelity;
- it preserves editability, provenance, and clean reproduction;
- its uncertainty and review boundary are explicit; and
- a named human accepts the relevant scientific and visual evidence.

Passing tests or generating files is insufficient. One successful figure is
evidence, not generalization.

## 14. Non-goals

- Building a frontier drawing model inside Figure Agent.
- Replacing TikZ or forcing SVG as the universal authoring source.
- Building a full vector editor, arbitrary style language, or hidden taste oracle.
- Treating semantic IDs, schemas, or pixel similarity as illustration quality.
- Automatically mutating unbound findings.
- Using fixture-specific coordinates as reusable product logic.
- Letting a numerical score claim publication acceptance.
- Overwriting accepted or historical artifacts during an experiment.
- Conflating data plotting with scientific schematic authoring.

## 15. Current evidence and gaps

Current repository evidence supports these conclusions:

- deterministic compile, export, provenance, candidate isolation, and human-gate
  infrastructure are substantial product assets;
- visual findings can be produced in volume, but not all are semantically bound
  or actionable;
- raw semantic SVG and the first paired illustration grammar preserved useful
  structure but did not meet the human visual-quality bar;
- direct LLM SVG authoring demonstrated useful expressive potential, but the
  bound Fig3 artifact was rejected for primitive geometry, visual density, and
  cross-panel illustration quality; this does not reject SVG as a derived QA
  surface;
- recent Panel F refinement exposed reusable concepts such as semantic salience,
  contact simplification, and forbidden implications, but much of the final
  geometry was still manually tuned; and
- the first renderable bound Fig3 control/treatment authoring pair removed the
  prior palette, local-font-size, and thin-stroke blockers by moving Style Lock
  rules into the pre-authoring contract, but both outputs still fail strict
  collision checks; the treatment run is also comparison-ineligible because
  its transcript contains undeclared reads of the product specification and
  execution plan; and
- repeated Fig3 repair failures have produced reusable blocker-identity,
  multi-neighbor layout, source-direction, rendered-path, and path-metric
  machinery, but an adversarial QA pass found fail-open gaps in named-style
  arrow resolution, option-token matching, branch scope, and evidence validation;
- a detached clean-worktree run at commit `09cd206a` produced `3740 passed, 4
  failed, 29 skipped, 5 xfailed`; the failures expose ignored-build dependencies,
  one stale historical attribution, and an overgrown execution authority rather
  than publication-quality success;
- the active Fig3 source now has a fresh passing strict compile and meets its
  declared geometry-coverage floor (21/25 operations typed; four remain outside
  typed parsing). This supports a bounded machine clean claim only: the
  hash-bound current-render scaffold still awaits a named human verdict, and it
  does not decide physical band-energy shape or publication quality; and
- the repository does not yet prove that Figure Agent reduces correction cost
  relative to the same LLM without the system.

The existing direct-SVG review path owns the active schema
figure-agent.three-way-review-unblinding.v1. This is retained implementation
evidence, not a reason to keep direct SVG as the product north star.

Legacy experiment runtime remains parseable under
`figure-agent.direct-svg-crop-authority.v1`,
`figure-agent.direct-svg-packet.v1`,
`figure-agent.illustration-backend-profile.v1`,
`figure-agent.illustration-grammar.v1`, and
`figure-agent.illustration-instance.v1`. These schema names preserve existing
artifact ownership only. They do not reopen direct-SVG or illustration-grammar
development in the active plan.

### 15.1 Constraint diet

The repository is substantially broader than the earned product surface. As of
2026-07-15 it contains 235 Python scripts, 82 callable top-level CLI names, and 599
Markdown documents. Code volume and command availability are not capabilities.
Until the two-family ablation proves otherwise, Figure Agent applies the
following diet.

| Disposition | Surface | Reason |
| --- | --- | --- |
| Keep and deepen | authoring context, packet, preflight, input audit, execution receipt | They expose declared truth and make model runs comparable without drawing for the model. |
| Keep and deepen | deterministic compile, export, status, hashes, and provenance | They are renderer-neutral reproducibility infrastructure. |
| Keep and deepen | semantic and relation contracts, electrical topology, Style Lock, collision, clipping, label/path, vector-clearance, and geometry-coverage checks | They target recurring failures that the LLM misses, provided coverage is reported honestly. |
| Keep and deepen | exact/ambiguous/unbound attribution, bounded repair, regression proof, rollback, and named human review | They turn observations into safe local action while preserving the acceptance boundary. |
| Consolidate | `loop`, `run`, `drive`, `improve`, `quality-search`, queue, and benchmark orchestration | These overlap as workflow shells. No new behavior belongs in them until one canonical execution path is selected. |
| Consolidate | proposal, candidate, render, rank, compare, accept, apply, and closeout command families | Candidate lifecycle remains useful internally, but the public surface is too fragmented. |
| Freeze as compatibility evidence | direct-SVG generation and SVG-polish runtimes | SVG remains an export and inspection surface; existing schemas stay parseable, but no new backend features are authorized. |
| Freeze as compatibility evidence | deterministic composition-family templates and the broad composition candidate stack | The implementation is inert on committed real figures and is explicitly Fig3-marker-bound; it has not met the cross-family promotion rule. |
| Freeze as advisory evidence | numeric aesthetic ranking and autonomous quality search | They may organize evidence but cannot substitute for semantic validity or human visual judgment. |
| Remove from the active path | fixture-specific coordinates, motif-specific repair logic, duplicated active plans, and unbound auto-repair | They either suppress LLM freedom, create false generalization, or bypass the product's evidence boundary. |

Freeze means no new features, fixtures, or default workflow dependencies. It
does not mean deleting historical artifacts or breaking their schema readers.
Deletion requires a separate compatibility audit proving that active commands,
tests, fixtures, and receipts no longer depend on the surface. The smallest
stable core should remain capable of accepting free LLM TikZ, observing it,
qualifying semantic coverage, localizing defects, applying one protected repair,
reproducing the artifact, and presenting exact evidence to a human.

The first Fig1 composition-profile pilot reinforces this diet. It produced a
larger explanatory scene, but the assisted arm clipped content, collided labels,
and omitted the required ISPD probe. The run is retained as invalid
failure-first evidence, not as a composition-assistance result. The next attempt
must add comparison eligibility and non-coordinate containment controls; it must
not revive a complete composition grammar.

The failure corpus and first A/B/C baseline now exist. The active execution plan
therefore closes QA integrity and coverage gaps first, then closes the incomplete
Fig1 and Fig3 human-review boundaries, and only then makes a two-family
capability decision. It must not add another renderer, motif family, or
fixture-specific polish rule.
