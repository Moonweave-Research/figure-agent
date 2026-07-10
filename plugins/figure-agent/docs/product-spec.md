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
   panels, semantic objects, and source selectors; and
2. reduce the cost of complex panels through a hybrid path in which Python can
   generate semantic SVG fragments that TikZ composes into the final figure.

## 3. Current truth and target architecture

### 3.1 Current truth

- **TikZ is the primary editable composition source and quality benchmark.**
- **Python is the implementation language** for orchestration, manifests,
  geometry, detectors, candidate generation, verification, and provenance.
- **SVG is a vector representation, not a replacement for Python.** Semantic SVG
  may serve as an inspectable fragment IR and QA surface when it carries stable
  object identities and provenance.
- **PDF, annotated SVG, PNG, overlays, and crops are evidence artifacts.** They
  serve different inspection and export purposes; no single render format is the
  whole source of truth.
- The shipped plugin has deterministic TikZ compile/export and multiple quality
  checks. A general built-in semantic-SVG authoring and polish executor is not
  yet a production capability.
- Machine gates can establish contract compliance and reproducibility. They do
  not establish publication acceptance.

### 3.2 Target flow

```text
intent + references + declared semantics
                  |
                  v
       semantic regions / object relations
                  |
          +-------+--------+
          |                |
          v                v
   TikZ composition   Python-generated semantic SVG fragment
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

### 4.3 Complex-panel hybrid authoring

Python-generated semantic SVG fragments are allowed for sub-regions where they
materially reduce complexity or improve geometry: dense molecular structures,
organic freeform shapes, repeated objects, spatial fields, and other geometry
that is awkward to maintain directly in TikZ.

Each fragment must provide:

- stable semantic object IDs and declared object relations;
- a deterministic view box and coordinate transform;
- the generator and input hash;
- an SVG source for inspection and a deterministic PDF-compatible render for
  TikZ assembly;
- a manifest tying both renders to the same fragment source; and
- a clear boundary showing which labels, arrows, and panel relationships remain
  owned by TikZ.

TikZ remains responsible for figure-wide composition unless a later promotion
gate explicitly changes that policy.

### 4.4 Reference-conditioned authoring

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
- PDF-space bounding box or deterministic transform into PDF space;
- source path and source selector;
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

Until then, semantic SVG is an experimental hybrid fragment path and TikZ is the
production baseline.

## 8. Non-goals and hard boundaries

- Replacing TikZ merely because SVG is easier to inspect.
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
- Slice 3 machine gates have evidence on their development branch, while human
  scaffold/artifact verdicts remain required; therefore the slice is not closed
  and publication acceptance is not claimed here.

The active work needed to close these gaps is defined only in
`docs/execution-plan.md`.
