# Fig1 Overview v4 Candidate Review

## Scope

Non-golden candidate lane for Panel C label/path readability. This fixture does
not mutate accepted v2, v3 baseline, exports, release state, or golden artifacts.
Its `reference` entry intentionally symlinks to the v3 reference pack so the
candidate remains small and does not duplicate binary reference assets.

## Baseline Finding

The v3 render reproduced the human-reported Panel C problem: `mobility edge`,
`shallow`, the blue/red escape arrows, and the Delta-E_t caliper occupied the
same top-right visual lane. The automatic gate did not surface this exact
semantic crowding class in `visual_clash.json`; the relevant protection was the
separate label-path-proximity check, plus manual crop review.

## Candidate Changes

- `mobility edge`: smaller, right-aligned reference label with a white
  backplate, so the text no longer extends toward the Delta-E_t caliper.
- `shallow`: moved into the clean right-side whitespace while staying above the
  deep-escape polyline bbox.
- Deep escape curve: terminus pulled left/down to reduce optical competition
  with the shallow label.
- `spec.yaml`: label-path-proximity polyline updated to match the moved deep
  escape curve.

## Verification

Run from `plugins/figure-agent`:

```bash
./bin/fig-agent compile fig1_overview_v4_pair_001_vault
./bin/fig-agent status fig1_overview_v4_pair_001_vault --json
```

Observed:

- compile exit: 0
- render state: fresh
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- output PNG SHA-256:
  `e20fa765e75e9e4fd51e6ec19a0fb9f683f9e5f04c89432a67bda22d1a030c69`
- `build/label_path_proximity.json` SHA-256:
  `b2f8cf76204f7e150efa2179100c4915bba97b26d1de1c1e0c35ca9b0fad405f`

## Current Judgment

The specific top-right Panel C overlap/crowding defect is improved enough for a
candidate comparison pass. The figure is not accepted or golden. A formal
critique/adjudication pass is still needed before any export, publication, or
golden roll-forward decision.
