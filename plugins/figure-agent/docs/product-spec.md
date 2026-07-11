<!-- FIGURE_AGENT:PRODUCT_AUTHORITY -->
# Figure Agent Product Specification

**Status:** Active product authority

**Effective date:** 2026-07-11

**Companion authority:** `docs/execution-plan.md`

## 1. Authority contract

This file is the single active product specification for Figure Agent. It
defines the product goal, system boundary, architecture, acceptance model, and
promotion rules. `docs/execution-plan.md` is the single active forward execution
plan. An agent starting product work must read these two files before any
roadmap, architecture note, milestone, experiment, or fixture-local plan.

All other documents are one of the following:

- an operational reference that explains shipped commands or code;
- historical evidence that records a past decision, experiment, or branch;
- a fixture-local contract whose authority is limited to that fixture; or
- a review artifact that supplies evidence but cannot change product direction.

Code, tests, manifests, and generated artifacts remain the authority for what is
implemented now. These two documents do not turn planned behavior into shipped
behavior. When prose and runtime disagree, report the disagreement and repair
the appropriate authority; never silently claim that the prose is operational.

## 2. Product north star

Figure Agent helps an agent and a human produce publication-quality scientific
schematics with less correction cost than a TikZ-only workflow, while retaining
or exceeding the best verified TikZ visual quality.

The product does **not** discard TikZ. TikZ is currently the strongest proven
assembly and typography path in this repository and therefore remains both the
production baseline and the benchmark to beat. Figure Agent earns a broader
authoring role only when measured evidence shows that it improves visual
quality, editability, or iteration cost without weakening scientific fidelity,
reproducibility, or human control.

The immediate product focus is:

1. make visual findings actionable by connecting rendered defects back to
   panels, semantic objects, and source selectors;
2. determine whether an LLM can directly author SVG at the accepted TikZ
   quality level before investing further in a drawing grammar;
3. locate the durable product value in direct drawing, reproducibility,
   verification, provenance, or correction-cost reduction from that evidence;
   and
4. expand a scientific illustration grammar only when the direct-authoring
   baseline exposes a repeated visual-control problem that simpler tooling does
   not solve.

## 3. Current truth and target architecture

### 3.1 Current truth

- **TikZ is the primary editable composition source and quality benchmark.**
- **Python is the implementation language** for orchestration, manifests,
  geometry, detectors, candidate generation, verification, and provenance.
- **SVG is a vector representation, not a replacement for Python.** Semantic SVG
  may serve as an inspectable fragment IR and QA surface when it carries stable
  object identities and provenance.
- **Semantic structure alone does not create illustration quality.** The Fig3
  hybrid pilot preserved object identities and relations, but its bound human
  verdict rejected the primitive SVG artifact as a production-quality
  rendering.
- **The first paired illustration grammar did not solve the quality gap.** Its
  TikZ and SVG backends shared one neutral scene and surrounding illustration
  language, yet both sulfur-trap artifacts were rejected for production and the
  grammar SVG remained worse than the historical raw SVG comparator.
- **A grammar layer is a hypothesis, not an assumed product requirement.** It
  may be needed for motifs, strokes, curvature, layering, spacing, emphasis,
  and optical correction, but Figure Agent must first measure whether an LLM
  can author a comparable SVG directly from a reference and scientific brief.
- **PDF, annotated SVG, PNG, overlays, and crops are evidence artifacts.** They
  serve different inspection and export purposes; no single render format is the
  whole source of truth.
- The shipped plugin has deterministic TikZ compile/export and multiple quality
  checks. A general built-in semantic-SVG authoring and polish executor is not
  yet a production capability.
- Machine gates can establish contract compliance and reproducibility. They do
  not establish publication acceptance.

### 3.2 Target flow

The flow below is the retained hybrid architecture when evidence justifies a
grammar. The clean-room direct-SVG baseline in Section 4.5 is a diagnostic
branch used to decide whether further grammar investment is warranted; it is
not silently inserted into the production flow.

```text
intent + references + declared semantics
                  |
                  v
       semantic regions / object relations
                  |
                  v
      scientific illustration grammar
                  |
          +-------+--------+
          |                |
          v                v
   TikZ backend       optional SVG backend
          |                |
          +-------+--------+
                  |
                  v
       deterministic TikZ assembly
                  |
                  v
 PDF + annotated SVG + PNG + overlay/crops + manifests
                  |
                  v
       quality kernel and human review
                  |
                  v
 bbox -> panel -> semantic object -> source selector
                  |
                  v
        bounded edit candidates and decision
```

The default remains TikZ-only when it is the cheaper and higher-quality path.
The hybrid path is selected at a panel or object boundary, never by rewriting an
entire accepted figure merely to change technology.

### 3.3 Representation roles

| Surface | Product role | Must not be treated as |
| --- | --- | --- |
| TikZ/TeX | Primary composition, typography, labels, arrows, panel assembly, editable benchmark | A technology that must be removed |
| Python | Orchestration, deterministic geometry, detectors, contracts, manifests, source attribution | A final visual format |
| Scientific illustration grammar | Renderer-neutral motif, stroke, layer, spacing, and optical-correction contract | A full Illustrator clone, arbitrary style generator, or renderer |
| Semantic SVG | Optional complex-fragment IR with stable IDs, relations, and inspectable geometry | Semantic merely because it has an `.svg` suffix |
| PDF | Deterministic vector assembly and manuscript artifact | Sufficient proof of semantic correctness |
| PNG | Raster review and vision input | Editable source |
| Overlay/crops | Localized visual-error evidence | Publication output |
| Human scaffold/review | Scientific and publication acceptance boundary | A machine gate that can be inferred from exit code |

## 4. Product capabilities

### 4.1 Quality kernel

The durable kernel owns:

- style-lock enforcement;
- deterministic compile and export;
- stale-artifact and provenance detection;
- visual and semantic QA evidence;
- status and next-action routing; and
- explicit acceptance boundaries.

The kernel may evaluate artifacts authored by a human, an agent, TikZ, Python,
or another tool. It must report uncertainty and unbound findings honestly.

### 4.2 Actionable visual-error detection

A detector finding is actionable only when the system can preserve this chain:

```text
rendered bbox -> panel -> declared semantic object/relation -> source selector
```

The attribution result is one of `exact`, `ambiguous`, or `unbound`. The system
must not invent a source location when declarations are missing or regions
overlap. Every actionable finding produces a review overlay and focused crop so
the human can verify the attribution before accepting an edit.

A durable source selector has a stable selector ID and explicit structural or
author-provided anchors. Line ranges are review snapshots, not durable identity:
they may be emitted for a human, but they cannot remain authoritative after the
source hash or anchor resolution changes. Missing, duplicated, or stale anchors
degrade attribution to `ambiguous` or `unbound` rather than triggering a guessed
edit.

### 4.3 Scientific illustration grammar

The grammar is the narrow contract between declared scientific semantics and a
rendering backend. It makes the visual decisions that raw circles, paths, and
coordinates do not express. TikZ and SVG may implement the contract, but
neither backend owns the grammar.

A versioned motif definition contains only:

- a motif-family ID and the semantic object/relation slots it must preserve;
- stroke, fill, color-role, curvature, corner, cap, and join families;
- layer and occlusion order, including foreground/background ownership;
- spacing, repetition, controlled-variation, and optical-alignment rules;
- label and composition ownership boundaries retained by TikZ;
- deterministic backend parameters and provenance; and
- review assertions that can be inspected in a paired TikZ/backend crop.

The first implemented motif family is `sulfur_trap_domain`: polymer backbone,
sulfur-rich region, sulfur sites, localized trap levels, and trapped carriers.
Its paired TikZ/SVG experiment preserved the neutral scene and shared visual
roles, but the bound human review rejected both artifacts and found the grammar
SVG worse than the raw Fig3 SVG comparator. The implementation remains
experimental infrastructure and does not justify another motif family.
Matching schemas, hashes, or semantic relations was necessary but insufficient.

Grammar loading fails closed on an unknown schema version, motif family,
semantic slot, relation, or required visual token. A backend must report an
unsupported capability explicitly; it may not silently omit a layer, substitute
a default motif, or change semantic roles. Contract tests verify schema and slot
preservation, backend tests verify deterministic structural output, and paired
render tests produce crops for human comparison. Raster similarity may detect
drift but cannot decide publication quality.

The grammar is not a general-purpose scene graph or complete vector-design
application. It does not include arbitrary brushes, freeform effects, filters,
page layout, typography engines, or unconstrained style synthesis. New motif
families are added one at a time only after a real figure exposes a repeated
need and a human accepts the resulting paired review.

### 4.4 Complex-panel hybrid authoring

Python-generated semantic SVG fragments are allowed for sub-regions where they
materially reduce complexity or improve geometry: dense molecular structures,
organic freeform shapes, repeated objects, spatial fields, and other geometry
that is awkward to maintain directly in TikZ.

SVG is not allowed merely because a region is complex. A new fragment must
either implement an approved illustration motif or remain an experimental QA
or direct-authoring artifact with an explicit non-promotion verdict. Raw
backend-specific polish rules may be prototyped to discover grammar
requirements, but they cannot become the product contract.

Each fragment must provide:

- stable semantic object IDs and declared object relations;
- a deterministic view box and coordinate transform;
- the generator and input hash;
- an SVG source for inspection and a deterministic PDF-compatible render for
  TikZ assembly;
- a manifest tying both renders to the same fragment source; and
- a clear boundary showing which labels, arrows, and panel relationships remain
  owned by TikZ.

No fragment may depend on network access, mutable external URLs, ambient fonts,
or unhashed local assets. Scripts are forbidden. Embedded raster assets, when a
scientifically necessary exception is declared, carry content hashes and an
explicit license/provenance record. SVG and its PDF-compatible render must pass
a deterministic geometry and visual-equivalence check, including view-box and
clipping checks.

TikZ remains responsible for figure-wide composition unless a later promotion
gate explicitly changes that policy.

### 4.5 Clean-room direct-SVG capability baseline

Before expanding the rejected illustration grammar, Figure Agent measures the
quality ceiling of direct LLM-authored SVG. This is a diagnostic experiment,
not a production-path promotion. It asks whether an LLM can match or exceed the
accepted Fig1 TikZ benchmark without reading its editable source, generated SVG
export, experience log, candidate patches, or Figure Agent illustration
grammar.

The first challenge uses two demanding and materially different regions of the
six-panel Fig1 benchmark:

- Panel C: thin-film real-space trap structure plus the related energy diagram;
- Panel F: biased apparatus, bent polymer cantilever, trapped charges,
  electrode separation, and Coulomb-repulsion direction.

The allowed clean-room inputs are immutable equal-boundary PNG crops, a
sanitized scientific briefing/specification, panel dimensions, and explicit
palette and typography constraints. The briefing preserves scientific meaning
and required object relations but contains no source coordinates, drawing
commands, or backend-specific implementation hints. The task may not read any
existing `.tex`, whole-figure SVG export, candidate patch, experience log, or
illustration-grammar artifact. A provenance receipt binds the exact allowed
inputs and records the denied source families.

The experiment has two sequential stages:

1. **Direct gold:** one clean LLM invocation writes editable `panel_c.svg` and
   `panel_f.svg`, then performs at most three render-inspect-revise iterations.
   Every iteration, prompt/input receipt, SVG, raster, elapsed time, and stated
   correction reason is retained.
2. **Cold reproduction:** only if direct gold passes human review, a separate
   clean invocation receives the same allowed input contract without the gold
   SVG or its iteration history. This distinguishes a one-off drawing success
   from reproducible authoring behavior.

The SVGs remain self-contained and editable. They use stable semantic group
IDs, explicit view boxes, vector paths/shapes, and live text. They may use
declared gradients when they improve material readability, but may not use
scripts, network access, external URLs or fonts, embedded raster images, or
unbound local assets. Direct SVG may discover backend-specific visual
techniques; those techniques do not become a product contract unless later
evidence justifies a general rule.

Each iteration automatically produces an equal-boundary TikZ comparator crop,
SVG crop, side-by-side image, difference/flicker evidence, SVG safety report,
semantic-object inventory, deterministic render receipt, and correction-cost
ledger. Machine gates establish safety, structure, and reproducibility only. A
named human records `better`, `equivalent`, or `worse` for scientific fidelity,
composition, illustration quality, typography/scale readability, and
editability/correction cost.

The direct-SVG quality hypothesis passes only when Panels C and F are both no
worse than the TikZ benchmark and at least one is clearly better. The result
changes product direction as follows:

- direct gold fails: a richer illustrator language or grammar has stronger
  justification;
- direct gold passes but cold reproduction fails: Figure Agent should focus on
  control, reproducibility, and bounded correction;
- both stages pass: a dedicated drawing grammar has weak justification, so
  Figure Agent should concentrate on verification, provenance, visual-error
  detection, and review automation.

The accepted TikZ figure, historical exports, and prior experiments remain
immutable. Because the current design session observed historical Panel F TikZ
implementation details while inspecting the repository, it is not eligible to
author the clean-room SVG artifacts. It may prepare the sanitized input packet,
automation, and review harness; the drawing run must occur in a fresh task that
has access only to the declared inputs.

### 4.6 Reference-conditioned authoring

The active reference workflow remains:

```text
reference PNG -> OCR + palette clusters + optional vtracer structural hints
coordinate_hints.yaml -> semantic TikZ authoring
```

Structural extraction is authoring evidence, not final source. SVG-to-TikZ path
conversion is not the active workflow. A reference authority manifest must say
which visual facts come from the reference, briefing, spec, coordinate hints,
editable source, and review history.

Read-only authoring context packs are durable paper-specific knowledge
compilation. They are not LLM prompt plumbing, prompt-loop revival, generation
execution, or automatic physics detection.

## 5. Declared semantic boundary

Semantics used for editing or acceptance must be declared in versioned,
machine-readable fixture artifacts. At minimum, a declaration identifies:

- panel ID;
- semantic object or relation ID;
- role and scientific meaning;
- page index, named coordinate space, origin/axis convention, crop/media box,
  page rotation, and PDF-space bounding box or deterministic transform;
- render-geometry hash tying detector pixels, DPI, page geometry, and fragment
  transforms to the reviewed render;
- source path, stable selector ID, anchors, source hash, and optional line-range
  snapshot;
- provenance of the declaration; and
- ambiguity when a one-to-one mapping is not possible.

Pixel similarity, DOM grouping, OCR, or vision inference may propose a mapping,
but cannot silently become declared semantic truth. Inference stays evidence
until a deterministic contract or a human verdict promotes it.

## 6. Acceptance model

Figure Agent separates three states:

1. **Machine-valid:** schemas, hashes, compilation, manifests, and deterministic
   checks pass.
2. **Review-ready:** required overlays, crops, semantic evidence, source
   attribution, and comparison artifacts exist.
3. **Human-accepted:** a named human scaffold/review verdict accepts scientific
   meaning and publication quality.

Machine-valid is not publication-accepted. A slice, fixture, or release that
requires human review stays open until the verdict artifact exists and names the
reviewed artifact hashes. Absence of a human verdict is `pending`, not success.
The verdict binds an aggregate review-input hash covering the rendered artifact,
semantic and reference-authority manifests, briefing/spec, object relations, and
toolchain. Any bound-input change makes the verdict stale even when the final
render bytes happen to remain unchanged.

## 7. Promotion rules

A new authoring representation becomes a production default only after all of
the following are demonstrated on at least two materially different figure
families:

- visual quality matches or exceeds the strongest accepted TikZ benchmark;
- measured correction or iteration cost is lower;
- semantic and source attribution survives clean-environment reproduction;
- artifacts remain editable and provenance-complete;
- detector precision does not improve by hiding or suppressing real defects;
- a human review accepts both scientific meaning and publication quality; and
- the path does not depend on fixture-name-specific patches.

An illustration grammar or backend has an additional promotion requirement:
the same motif contract must lower into at least two backends without changing
its semantic slots or visual-role definitions. Backend outputs need not be
pixel-identical, but both must pass the same declared relation checks and a
paired human quality review. A lower-quality SVG implementation does not weaken
the TikZ baseline and cannot be promoted by averaging machine scores.

Correction-cost evidence follows a predeclared comparison protocol with the
same starting contract, task boundary, and timing rules. Preparation, failed
attempts, rendering, diagnosis, and repair time are included; missing or
non-comparable measurements cannot support promotion.

Until then, semantic SVG is an experimental hybrid fragment path and TikZ is the
production baseline.

## 8. Non-goals and hard boundaries

- Replacing TikZ merely because SVG is easier to inspect.
- Recreating Adobe Illustrator, a general vector editor, or an unrestricted
  style language inside Figure Agent.
- Hiding illustration decisions in SVG-only helpers when they belong to a
  renderer-neutral motif contract.
- Treating arbitrary SVG groups as semantic objects without a declaration.
- Building a hidden autonomous taste judge or claiming that a numerical score
  proves publication quality.
- Generating fixture-specific dictionaries, coordinates, or patch templates as
  a substitute for general contracts.
- Modifying or overwriting historical accepted artifacts during experiments.
- Conflating quantitative data plotting with schematic authoring; measured data
  plots remain outside the core Figure Agent authoring scope.
- Importing Fig1-specific implementation into another fixture without an
  explicit general contract and a cross-fixture test.

## 9. Artifact and provenance policy

- Historical references, sources, reviews, and accepted outputs are immutable
  evidence. New work uses a forked fixture or a new slice output directory.
- Generated artifacts name their source hashes, tool versions, and relevant
  environment details.
- Clean-environment reproduction must begin from a clean tracked checkout and
  may not depend on user untracked files or another worktree's build products.
- Worktrees and branches isolate slices. Destructive Git cleanup is not part of
  the product workflow.
- Exported artifact success does not overwrite the acceptance state.

## 10. Evidence snapshot and known gaps

This section records orientation evidence, not evergreen runtime claims. Verify
it against the named branch or artifact before relying on exact counts.

- The accepted Fig1 TikZ dogfood remains the current visual-quality benchmark.
- The latest inspected Fig1 visual-clash evidence emitted many bbox candidates
  without usable panel/source binding, demonstrating that detection volume alone
  is not actionable quality improvement.
- Slice 3 selected the six-panel sulfur-polymer Fig3 family because it applies a
  different composition and semantic pressure than Fig1 and carries reference,
  briefing, spec, coordinate hints, editable TeX, and review history.
- The Fig3 semantic-SVG pilot is reproducible and source-attributable. The
  bound human verdict rejects its basic illustration quality for production.
- The paired sulfur-trap grammar proved deterministic neutral-scene lowering
  into TikZ and SVG, but the named review rejected both artifacts and found its
  SVG worse than the raw SVG comparator. The infrastructure remains
  experimental; the current grammar implementation does not advance.
- The next unresolved question is whether a clean LLM can directly author
  Panels C and F at the accepted TikZ level. Until the clean-room baseline and,
  if eligible, cold reproduction are reviewed, the repository lacks evidence
  that another drawing grammar is the right next product investment.

The active work needed to close these gaps is defined only in
`docs/execution-plan.md`.
