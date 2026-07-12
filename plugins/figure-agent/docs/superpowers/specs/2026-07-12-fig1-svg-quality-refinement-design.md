# Fig. 1 C/F SVG Quality Refinement Design

**Status:** Approved in dialogue; awaiting written-spec review before planning.
**Date:** 2026-07-12
**Authority:** This document is a bounded design input. `docs/product-spec.md`
defines product direction and `docs/execution-plan.md` remains the single active
execution authority until a follow-on plan is approved.

## 1. Context

Task 20 established that direct SVG can reconstruct the accepted Fig. 1 visual
language and can produce a more contemporary alternative, but it did not prove
that direct SVG consistently exceeds the accepted TikZ-quality baseline. Human
review found useful potential together with concrete failures:

- panel C contained abnormal trap-band geometry, overlapping forms, awkward
  deep-state geometry, and color choices whose semantic meaning was unclear;
- panel F contained label collisions, an awkward and uneven cantilever, suspect
  paper typography, and one alternative that changed the real vertical setup
  into a scientifically misleading horizontal composition;
- the more contemporary alternatives sometimes looked cleaner while losing
  mathematical or physical precision; and
- machine checks alone were insufficient to settle publication quality.

The next experiment therefore isolates a narrower question: can Figure Agent
produce a corrected SVG that is no worse than the accepted TikZ baseline, and
also produce a restrained modern redesign without changing the science?

Task 20 remains `blocked_pending_second_human_review`. This refinement does not
relabel that outcome, substitute an AI advisory for the missing human, reveal
the blinded source mapping, or overwrite any Task 20 artifact.

This is a provenance-declared bounded refinement in a session that has observed
historical Fig. 1 evidence. It is not clean-room authoring, a replacement Test B,
an independent cold authoring run, or evidence that can authorize a Task 20
product-direction outcome.

## 2. Decision

Create a new, historically separate Fig. 1 C/F refinement fixture with two
explicit variants per panel:

1. **`conservative`** — preserve the accepted composition and explanatory
   density while repairing known defects and bringing the SVG finish to at
   least the TikZ baseline.
2. **`modern-a`** — preserve the same scientific object-relation contract while
   applying a restrained publication style: low-saturation semantic color,
   consistent line hierarchy, controlled whitespace, and paper-appropriate
   typography.

The modern variant is not an unrestricted restyle. It may change placement,
grouping, spacing, geometry treatment, and visual hierarchy, but it may not add,
remove, reverse, or reinterpret a scientific object or relation.

### Alternatives considered

- **Conservative-only repair:** lowest scientific risk, but it would not test
  whether SVG provides a genuine visual-quality advantage.
- **Editorial high-contrast redesign:** visually immediate, but its heavy panel
  blocks and saturated contrast can overstate color meaning and diverge from the
  surrounding paper.
- **Ultra-minimal systems diagram:** easy to validate structurally, but likely
  to discard the material and apparatus cues that make the accepted TikZ figure
  explanatory.

The paired `conservative` plus restrained `modern-a` design is chosen because it
separates correctness recovery from aesthetic ambition instead of asking one
candidate to prove both at once.

## 3. Artifact and provenance boundary

Implementation will occur in a new clean worktree and `codex/` branch created
from the commit containing this design and its approved implementation plan.
The intended fixture root is:

```text
examples/fig1_svg_quality_refinement/
```

The fixture will contain, at minimum:

```text
authority/
  manifest.yaml
  panel-c.semantic.yaml
  panel-f.semantic.yaml
sources/
  conservative/panel-c.svg
  conservative/panel-f.svg
  modern-a/panel-c.svg
  modern-a/panel-f.svg
build/
  conservative/panel-c.png
  conservative/panel-f.png
  modern-a/panel-c.png
  modern-a/panel-f.png
review/
  manifest.yaml
  index.html
```

Exact filenames may be adjusted in the implementation plan to match an existing
validated fixture convention, but the historical boundary and variant identity
must remain explicit.

The authority manifest records source paths and SHA-256 hashes for the accepted
reference crops, relevant TikZ/reference render, the reviewed direct-SVG inputs,
the semantic packets, renderer/tool versions, and every generated SVG/PNG. It
must identify derived copies as derived; it must not present them as independent
clean-room evidence.

Historical Task 20 artifacts are read-only evidence. New files never replace,
rename, or mutate them. The private blinded mapping stays private and unrevealed.
No refinement review page may correlate old blinded option letters with source
families.

The conservative sources may begin from a provenance-declared copy of an
existing direct-SVG source because their purpose is bounded correction. The
`modern-a` sources may share the semantic packets and generic reusable drawing
primitives, but may not import conservative panel geometry or panel-specific
coordinates. This keeps the modern result a real composition test rather than a
palette swap.

Both editable SVG sources must satisfy the existing direct-SVG safety boundary:
no scripts, network access, external URLs, unbound local assets, or embedded
raster panels. Fonts must be license-recorded and hash-pinned through the
isolated render configuration; ambient font substitution invalidates the render.

## 4. Shared semantic and object-relation contract

Both variants consume the same declared panel contract. A variant is invalid if
it satisfies visual checks but violates a declared object, relationship, label,
direction, or scientific state.

### Panel C: localized trap model

Required objects include the real-space polymer film, localized shallow and deep
states, the energy-axis frame, conduction and valence references, mobility edge,
shallow and deep trap distributions/levels, correspondence leaders, and trap
depth annotation.

Required relations include:

- every real-space localized-state class maps to the corresponding energy class;
- shallow and deep classes use consistent color and identity across both spaces;
- `E_C`, mobility edge, trap states, and `E_V` retain their declared order;
- the trap-depth arrow has declared endpoints and direction;
- a density-of-states shape does not collide with or visually swallow its
  discrete levels; and
- mathematical labels retain proper subscripts, symbols, and italic/roman roles.

Color is semantic only for shallow/deep identity and their correspondence. It
must not introduce a third unexplained state.

### Panel F: electromechanical apparatus

Required objects include the support, cantilever, trapped charges, electrode,
air gap, active-bias source/connection, ground, and Coulomb-repulsion annotation.

Required relations include:

- the apparatus remains vertically oriented;
- support, cantilever, air gap, and electrode preserve their physical adjacency;
- the electrical connectivity graph distinguishes active bias from ground and
  contains no contradictory same-node connection;
- trapped charges remain associated with the cantilever;
- the repulsion direction is consistent with the illustrated charge/electrode
  configuration; and
- the cantilever is a continuous, plausible strip with controlled width and
  curvature rather than a sequence of unrelated shapes.

## 5. Visual language

### Conservative variant

- retain the current left/right organization in C and vertical apparatus in F;
- remove collisions, awkward joins, inconsistent widths, and accidental visual
  tangencies;
- use a consistent paper-scale type system and math rendering;
- preserve useful material cues and explanatory density from the accepted TikZ
  baseline; and
- avoid decorative changes that cannot be tied to readability or hierarchy.

### Modern A variant

- use a restrained, low-saturation palette with one shallow accent, one deep or
  force accent, and neutral structure colors;
- use line weight to distinguish primary structure, secondary construction,
  leaders, and annotations;
- increase whitespace and grouping clarity without shrinking labels below the
  target paper scale;
- prefer controlled flat or filter-free vector shading over glossy effects;
- align typography with conventional scientific-journal usage; and
- preserve the scientific figure grammar rather than adopting an infographic or
  presentation-slide aesthetic.

## 6. Implementation pipeline

The implementation follows a lock-first, test-first sequence:

1. freeze the authority manifest and semantic packets;
2. write focused failing tests for each declared invariant and known defect;
3. implement and verify `conservative` C and F;
4. permit `modern-a` work only after the conservative machine gates pass;
5. implement `modern-a` from the shared semantic contract without importing
   conservative panel geometry;
6. render SVG to PNG at the declared output size and create deterministic zoom
   crops for review;
7. reproduce the deterministic build from a clean environment using one
   documented command;
8. generate a new blinded human-review package; and
9. record the human verdict without upgrading it into a publication claim.

No new dependency or public API is introduced without explicit approval. The
implementation must reuse existing validators and rendering helpers when they
already own the required behavior.

The clean-environment step proves build/render reproducibility only. It is not
one of the independent cold authoring runs defined by the product spec.

## 7. Machine gates

Machine validation is necessary but not sufficient. At minimum it covers:

- authority/provenance schema, path containment, hashes, and exact output
  inventory;
- editable SVG structure with stable semantic IDs and no unintended embedded
  raster panels;
- required object and relation presence;
- C energy ordering, mapping endpoints, trap-shape/level clearance, and math
  text identity;
- F connectivity graph, orientation, cantilever continuity/width bounds, and
  force-direction declaration;
- rendered text and object bounding-box collisions, boundary escape, and
  clipping using the actual rendering font path;
- minimum paper-scale font size and line width;
- deterministic whole-panel plus focused-crop rendering;
- clean-environment reproduction and generated-artifact hashes; and
- `git diff --check`, targeted tests, affected tests, and Ruff for changed
  Python.

Visual checks run on the whole panel and focused crops at declared inspection
scales. A crop passing cannot hide a composition failure in the whole panel, and
a whole-panel pass cannot hide a small collision visible at publication zoom.

## 8. Human review and stop rules

The new review package compares the accepted baseline, `conservative`, and
`modern-a` for C and F through fresh opaque option labels, randomized order,
equal dimensions/background/rasterization, and stripped format metadata. The
private refinement mapping is distinct from the Task 20 key and remains hidden
until the scores are fixed. The package binds the exact render, semantic
contract, authority manifest, and toolchain under one aggregate review-input
hash. It does not reuse Task 20 blinded option letters.

The reviewer records separate answers for:

1. scientific correctness and completeness;
2. obvious collisions, malformed geometry, and typography defects;
3. no-worse-than-baseline finish;
4. modern variant visual improvement; and
5. any remaining uncertain or preference-only concern.

Definite errors block the affected variant. Preference-only feedback is recorded
without being converted into a correctness failure.

For each scientifically passing panel, the reviewer records `better`,
`equivalent`, or `worse` separately for composition, illustration quality, and
typography/scale readability. `No worse` means all three dimensions are at least
`equivalent`; `better` means at least one is `better` and none is `worse`. A
borderline or disputed result requires a distinct second named human before it
can support the slice verdict.

The slice may close successfully when:

- `conservative` has no declared machine failure and a named human judges it no
  worse than the accepted baseline with no definite visible defect; and
- `modern-a` has no semantic/machine failure and a named human judges it a
  meaningful visual improvement without scientific loss.

If `modern-a` fails, the verified conservative result and the evidence about
the modern failure remain valid separate outcomes. If only machine gates pass,
the state is `awaiting_human_review`, not `publication_ready`. Publication
acceptance remains a separate human decision outside this slice. No result from
this refinement changes Task 20 product direction or replaces the two cold
authoring runs required for a product-direction claim.

## 9. Non-goals

- replacing TikZ as the only supported production backend;
- changing the science, apparatus topology, or mathematical model;
- repairing or completing the blocked Task 20 second-human review;
- revealing Task 20 blinded keys or source mappings;
- overwriting historical Fig. 1 sources, renders, reviews, or manifests;
- building a WYSIWYG editor;
- generalizing panel-specific coordinates into the shared library before the
  small fixture proves the behavior; or
- claiming journal or publication acceptance from automated evidence.

## 10. Principal risks and controls

- **A polished scientific error:** prevent with shared declared semantics and
  relation gates before aesthetic evaluation.
- **A palette swap presented as redesign:** prohibit modern imports of
  conservative panel geometry; require separate provenance.
- **Machine-perfect but visibly weak output:** require named human whole-panel
  and zoom-crop review.
- **Font measurements that differ from the final render:** measure from the
  actual rendered artifact and record the renderer/font receipt.
- **Hidden review leakage:** keep Task 20 mappings unrevealed and avoid old
  option labels in the new package.
- **Scope expansion into a general renderer rewrite:** keep the first slice to
  panels C/F and generalize only behavior proven by focused tests.

## 11. Planning handoff

After written-spec approval, create a task-by-task implementation plan using
`superpowers:writing-plans`. The plan must name the clean worktree/branch,
precise files after repo inspection, RED tests before implementation, rendering
commands, clean-build reproduction command, review package, and human-gated stop
state.
Implementation must not begin before that plan is reviewed.
