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

Final audited render SHA-256:
`076c3770ac6314874b8a8ec2938fa317bf9e4197af38720ac5506c48368db40b`.

## Same-host result

The advisory preferences were Q2 for the amorphous host and R8 for matched MIM
transport. Subsequent object-level enlargement invalidated the initial V9
preference: C5 and L1 read as thick banana/ribbon silhouettes, while V9 contains
a self-crossing waist and is not one valid finite-width member. The cantilever
row is therefore recorded as `no_viable_candidate`. This correction is also
evidence that collision-free output is insufficient for silhouette quality.

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
- Text collision/boundary/label-path: 0 blocking
- Human/master gate: pending
