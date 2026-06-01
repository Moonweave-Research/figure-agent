# Issue 63B - Non-Model Aesthetic Metrics Pack

Status: completed; merged to main

Depends on: Issue 63A reference-learning contract

## Problem

Host vision critique can miss old-looking, generic, or reference-divergent
figures even when references are available. The plugin needs a local,
deterministic signal that can flag aesthetic-class divergence without asking the
model to judge its own output.

The metric must not ask whether the build image is a pixel copy of the
reference. The current figure is a re-implementation with different semantics,
so full-image SSIM, pixel identity, and coordinate equality would create false
positives.

## Goal

Emit a deterministic `build/reference_aesthetic_metrics.json` file that compares
the build render to declared reference anchors using aesthetic-class metrics.
The first version should be small, local, and explainable.

## Scope

In scope:

- Compute metrics only when a fixture declares compatible reference-learning
  roles.
- Start with low-cost PIL/numpy style metrics:
  - palette histogram distance;
  - dominant hue family count;
  - ink density ratio;
  - edge density ratio;
  - coarse silhouette occupancy;
  - stroke or line density proxy where feasible.
- Include enough provenance to make freshness and reproduction clear:
  - fixture;
  - build artifact path and hash;
  - reference path and hash;
  - metric version;
  - metric values;
  - threshold profile if configured.
- Keep the file deterministic and machine-readable.
- Add the metrics file to critique input context after 63C, not as hidden
  release authority.

Out of scope:

- Full-image SSIM or pixel similarity.
- Learned aesthetic models.
- Provider calls.
- Automatic source edits.
- Hard release blocking before dogfood calibration.

## Acceptance

- [x] A local script can generate `build/reference_aesthetic_metrics.json`.
- [x] Missing or incompatible references skip with a controlled explanation.
- [x] The output is deterministic for the same inputs.
- [x] Synthetic tests demonstrate palette, density, and silhouette divergence.
- [x] Tests prove full-image similarity is not used as a pass/fail contract.
- [x] Existing fixtures without reference-learning opt-in are unaffected.

## Implementation Notes

Implemented as `scripts/reference_aesthetic_metrics.py`.

The script:

- reads optional `critique_reference_pack.yaml`;
- only runs when the pack contains `reference_learning`;
- writes deterministic `build/reference_aesthetic_metrics.json`;
- records build and reference hashes;
- computes aesthetic-class deltas:
  - `palette_histogram_distance`;
  - `dominant_hue_family_count_delta`;
  - `ink_density_delta`;
  - `edge_density_delta`;
  - `coarse_silhouette_occupancy_delta`;
  - `line_density_proxy_delta`;
- records build/reference feature summaries;
- skips no-opt-in fixtures without creating a metrics file;
- writes `state: skipped` with `skip_reasons` when the learning contract exists
  but the declared local reference image cannot be measured.

The implementation intentionally does not compute SSIM, pixel identity, or
coordinate equality. It also does not surface metrics in `/fig_status` or
`/fig_loop`; that remains Issue 63C.

Verification performed:

- `uv run pytest -q tests/test_reference_aesthetic_metrics.py`
  -> 4 passed.
- `uv run ruff check scripts/reference_aesthetic_metrics.py tests/test_reference_aesthetic_metrics.py`
  -> all checks passed.

## Review Questions

1. Do the metrics measure editorial class rather than copy similarity?
2. Are the metrics explainable enough for users and agents to trust?
3. Can thresholds be calibrated fixture-by-fixture without overfitting?
4. Does the output give `/fig_loop` useful suspicion without overriding human
   or semantic gates?
