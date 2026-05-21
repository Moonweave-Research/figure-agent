# Issue 23: Zoom and Reference-Calibrated Audit Roadmap

**Date:** 2026-05-22 KST
**Status:** 23A-C completed; 23D-E open
**Type:** post-closeout audit-quality hardening

## Problem

Issue 22 closed the critical contract gaps around critique consumption,
export validity, visual-clash freshness, print-scale lint, and release gate
binding. The remaining audit risk is not that the plugin lacks broad rubric
categories. The remaining risk is that host-vision critique can still miss
small geometry defects or judge "top-tier" quality without enough structured
reference calibration.

Dogfood showed two practical facts:

- The host LLM does not reliably see sub-millimeter defects from full render
  or panel-level crops. It needs forced local zoom crops around suspicious
  geometry.
- "Nature/Science-level" cannot be judged only from generic prose. The critique
  needs an explicit reference class, must-match traits, must-avoid traits, and
  target-journal ambition for each fixture.

## Priority Order

1. **Issue 23A: Visual-Clash BBox-Centered Crops**
   - Completed in commit `112e766`.
   - Highest priority. Converts every `VC###` candidate into an image crop the
     host LLM must inspect.
   - Directly addresses the observed failure mode: the LLM sees defects only
     when zoomed into the exact local region.
   - Also defines the stable crop-pack manifest and freshness contract that
     later crop-accounting lint depends on.

2. **Issue 23B: Crop-Read Accountability**
   - Completed in commit `ebb1eff`.
   - Requires the critique output to account for every zoom, print-scale, and
     visual-clash crop.
   - Prevents "crop was provided but not actually reviewed" from becoming a
     silent failure.

3. **Issue 23C: Reference-Calibrated Critique Pack**
   - Completed in commit `e725c6c`.
   - Adds an optional fixture-level `critique_reference_pack.yaml`.
   - Makes target journal, reference class, exemplar traits, must-match traits,
     and must-avoid traits explicit critique inputs.

4. **Issue 23D: Reference-Calibrated Scoring Guidance**
   - Uses the reference pack to sharpen advisory scores and benchmark levels.
   - Keeps scores advisory only. Scores do not unlock export, release,
     acceptance, or human gates.

5. **Issue 23E: Fixture Freshness UX Cleanup**
   - Improves status/driver explanations for stale render, critique, export,
     tracked golden, and publication provenance states.
   - Reduces user confusion when the plugin core is healthy but the fixture
     artifacts are stale.

## Later Backlog

These are useful but should not preempt Issues 23A-E:

- SVG polish handoff expansion.
- Deterministic historical regression harness for the HV+/V_s defect family.
- External second-opinion vision model integration.
- Structured `accept_simplification_reason` enum.
- Publication provenance UX beyond the current human gate.

## Dependency Graph

```text
23A visual-clash bbox crops
  -> 23B crop-read accountability
      -> 23C reference-calibrated critique pack
          -> 23D reference-calibrated scoring

23E fixture freshness UX can run after 23A or in parallel if no shared files
conflict.
```

## Non-Goals

- No external web search or automatic journal-image scraping in this issue
  chain.
- No copyrighted figure corpus ingestion.
- No hidden auto-patching.
- No score-driven release gates.
- No claim that the plugin can certify Nature/Science acceptance without human
  scientific and provenance review.

## Success Definition

Issue 23 is complete when:

- visual-clash candidates produce local zoom crops and those crops are included
  in the critique brief;
- a deterministic crop-pack manifest exists and participates in critique
  freshness;
- critique output must account for all required crops from that manifest;
- a fixture can declare a reference-calibration pack;
- the host critique uses that pack to judge target-journal fit and top-tier
  ambition;
- advisory scores can cite the reference pack without becoming gates;
- status/driver messaging makes stale fixture state easy to understand.
