# Fig5 composition studies

These are deliberately separate, non-canonical TikZ studies.  They preserve
the fixture's scientific sequence and do not change the reviewed Fig5 source,
semantic contract, acceptance state, or print-size contract.

| Study | Reading order | Intended editorial effect | Measured natural height |
| --- | --- | --- | --- |
| `timeline-spine.tex` | A -> B -> C across the top, then D across the bottom | Makes the isolation state and its consequence read as one causal timeline. | 84.52 mm |
| `mechanism-focus.tex` | A -> B, then C and D as paired outcomes | Makes the force-balance condition the visual pivot while preserving the response trace as its outcome. | 81.51 mm |

The canonical Fig5 contract is 53.50 mm high at 180 mm width.  Each study
therefore declares a sibling, source-specific `.authority.yaml` sidecar for
its own physical measurement.  The sidecar allows the regular Figure Agent
compile to check the alternative page geometry without changing the canonical
source, acceptance, or promotion state.  These renders remain for human
art-direction comparison only; neither is a candidate for automatic promotion,
human acceptance, or publication use without a deliberate figure-height/layout
decision.

The parent fixture's strict boundary, process-stage, and semantic text anchors
describe the canonical one-row geometry, so strict compilation of these studies
correctly stops at inherited-coordinate mismatches.  A future selection would
need its own full candidate contract and checks; a source-specific print sidecar
does not weaken or replace those higher-level guards.

The original four-panel causal row remains the only current, fully validated
source.  These studies answer a narrower question: whether the manuscript's
story benefits enough from a two-row hierarchy to justify changing the final
figure allocation.
