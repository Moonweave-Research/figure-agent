# Fig1 Render Parity Gate Handback v24

## Scope

This pass adds a hard render parity gate for Fig1. It checks that the current Python source can regenerate the tracked `fig1_reference_semantic.svg` byte-for-byte.

## Implemented Boundary

- `src/verify_fig1_render_parity.py` compares `svg_text_for_scene(build_scene())` against the tracked SVG.
- `src/run_fig1_gates.py` now includes `verify_fig1_render_parity.py` before the baseline hash gate.
- `src/test_fig1_render_parity.py` covers current-source parity, stale-artifact detection, and gate-runner inclusion.
- The gate does not render or compare PNG files.
- The gate does not add subjective visual judgment rules.
- The gate does not replace `src/verify_fig1_baseline_hash.py`; render parity and baseline hash are orthogonal.

## Why This Matters

The baseline hash proves that the checked-in SVG still matches the pinned artifact hash. It does not prove that current renderer source, scene payloads, and scaffold code can reproduce that SVG.

The render parity gate closes that gap: if renderer source drifts but the tracked SVG is not regenerated, the gate fails.

## Transfer Note

For future reference figures, this pattern is reusable once that figure has:

- a source-of-truth semantic scene builder,
- a deterministic SVG text renderer,
- a tracked reference SVG artifact,
- and a figure-specific parity verifier.

The gate transfers as a workflow contract. It does not transfer Fig1 panel coordinates or Fig1-specific aesthetic decisions.
