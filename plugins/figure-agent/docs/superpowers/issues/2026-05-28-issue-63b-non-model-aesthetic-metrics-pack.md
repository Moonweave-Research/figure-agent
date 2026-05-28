# Issue 63B - Non-Model Aesthetic Metrics Pack

Status: proposed

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

- A local script can generate `build/reference_aesthetic_metrics.json`.
- Missing or incompatible references skip with a controlled explanation.
- The output is deterministic for the same inputs.
- Synthetic tests demonstrate palette, density, and silhouette divergence.
- Tests prove full-image similarity is not used as a pass/fail contract.
- Existing fixtures without reference-learning opt-in are unaffected.

## Review Questions

1. Do the metrics measure editorial class rather than copy similarity?
2. Are the metrics explainable enough for users and agents to trust?
3. Can thresholds be calibrated fixture-by-fixture without overfitting?
4. Does the output give `/fig_loop` useful suspicion without overriding human
   or semantic gates?
