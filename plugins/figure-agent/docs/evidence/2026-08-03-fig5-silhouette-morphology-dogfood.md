# Fig. 5 repeated-member silhouette dogfood

Date: 2026-08-03
Status: machine-valid development evidence; human/master gate remains open

## Scope

The current Fig. 5 authoring baseline is
`examples/fig5_cantilever_actuation_artifact_v2/`. Its A-C cantilevers are not
closed filled paths: each film is rendered from a thick amber centerline with a
thinner light inner stroke. The earlier filled-boundary morphology check could
therefore validate the benchmark V9 but did not cover this canonical figure.

This dogfood slice added a `stroked_centerline` representation to the rendered
PDF checker and grouped the three state-bearing members. It did not change the
Fig. 5 TikZ artwork.

## Current rendered measurements

Strict compile selected the outer film stroke in each declared panel region:

| State | Centerline length (pt) | Stroke width (pt) | Tip x displacement (pt) |
| --- | ---: | ---: | ---: |
| A, drive-on | 72.836 | 6.779 | +29.713 |
| B, residual | 70.824 | 6.779 | +11.828 |
| C, reverse | 73.001 | 6.779 | -21.636 |

The cross-panel centerline-length ratio is 1.031 and the stroke-width ratio is
1.000. Absolute bend magnitude orders B < C < A, while C alone bends in the
opposite direction. All three local checks and the comparison group pass with
zero violations.

## Proven and unproven

The new evidence can fail strict compile on a missing or ambiguous target,
self-intersection, excessive stroke width, member-length drift, width drift,
collapsed bend ordering, or a wrong declared bend direction. It reads rendered
PDF vectors and does not prescribe a TikZ primitive or Bezier control points.

It does not score curvature taste, determine whether a silhouette feels too
cartoon-like, optimize force-label placement, validate the experimental model,
or establish publication readiness. Those remain current-render host review and
named-human decisions.

## Verification

- Canonical render SHA-256:
  `3b3639f607ceb2c5a57047c7c8cca30f671125a0cd35e8a5869c89f2c207b591`
- Strict compile: green
- Silhouette morphology: 3 members + 1 group checked, 0 violations
- Semantic assertions: 2 checked, 0 issues
- TeX geometry assertions: 5 checked, 0 issues
- Physics grounding: grounded
- Critique and adjudication: fresh after current-input synchronization
- Human/master gate: pending
