# Handcrafted-finish benchmark v1

Date: 2026-08-03
Status: prospective host evidence only; named-human review pending

## Purpose

Test whether a freer redraw or a restrained editorial refinement improves three
representative Figure Agent motifs without changing their scientific meaning:

- Fig. 1: amorphous host with localized trap sites
- Fig. 2: progressive trapping in matched MIM cells
- Fig. 5: opposing-force cantilever schematic

The rendered board masks candidate roles with option ids. The same Codex host
authored and reviewed all candidates, so this is not independent preference
evidence, a ranker reward, a publication verdict, or a named-human acceptance.

## Artifacts

- Fixture: `examples/handcrafted_finish_benchmark_v1/`
- Manifest: `benchmark_manifest.yaml`
- Masked review: `review/host_masked_review.yaml`
- Render: `build/handcrafted_finish_benchmark_v1.png`
- 100/50/33 candidate crops: `build/handcrafted_finish_crops/`
- Hash-bound crop evidence: `build/handcrafted_finish_evidence.json`

Current audited render SHA-256:
`ffe2df62b9522caa81e52608970d8b231adad8ecee21d32c3001e79974ddc0b6`.

## Same-host result

The advisory preferences were Q2 for the amorphous host and R8 for matched MIM
transport. Subsequent object-level enlargement invalidated the initial V9
preference: C5 and L1 read as thick banana/ribbon silhouettes, while V9 contains
a self-crossing waist and is not one valid finite-width member. The cantilever
row was therefore first recorded as `no_viable_candidate`. This correction is
evidence that collision-free output is insufficient for silhouette quality.

V9 was then redrawn as a single narrow member with separated edges, a centered
fixed-end tangent, and a smooth free-end cap. An opt-in PDF-vector morphology
check now measures the rendered path rather than the TikZ recipe. Before redraw,
it found one self-intersection and a 2.256 width-variation ratio. The current V9
has zero self-intersections, a 0.075 width-to-length ratio, and a 1.026
width-variation ratio. It is recorded only as
`repair_candidate_pending_human`: those metrics exclude specific malformed
silhouettes, but they do not establish journal-level taste or human preference.

Across all three families, the reusable observation was narrower than “make it
less regular”:

1. Repeated geometry is beneficial when it expresses semantic invariance, such
   as the same MIM footprint or apparatus identity in a controlled comparison.
2. Visual changes should concentrate in state-bearing variables.
3. Unowned halos, textures, field curves, and asymmetric embellishments weaken
   hierarchy when they do not encode a declared scientific role.
4. Random jitter is not a substitute for editorial art direction.

These observations were promoted only into the prospective critique/audit
language. They were not written into reward memory, candidate ranking, or human
acceptance state.

## Verification

- Strict compile: green
- Print-size contract: 178.0 x 118.7 mm; minimum declared font 5.1 pt
- Semantic assertions: 2 checked, 0 issues
- Physics grounding: grounded
- Visual clash: 0 blocking, 2 report-only
- Silhouette morphology: 1 checked, 0 violations
- Text collision/boundary/label-path: 0 blocking
- Human/master gate: pending
