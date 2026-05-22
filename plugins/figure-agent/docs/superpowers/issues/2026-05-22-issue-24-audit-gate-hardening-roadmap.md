# Issue 24: Audit Gate Hardening Roadmap

**Date:** 2026-05-22 KST
**Status:** 24A-B implemented; 24C-E open
**Type:** post-Issue-23 audit-system hardening

## Problem

Issue 23 made the audit system much harder to fool: visual-clash candidates now
produce local zoom crops, critiques must account for required crops, reference
packs calibrate top-tier judgments, and fixture freshness messaging is clearer.

The remaining risk is narrower but important: the plugin can still record audit
uncertainty or lose auxiliary audit inputs without always turning that into a
clear stop boundary. That means a host critique can appear structurally complete
while one of the machine-generated audit surfaces was uncertain, missing, or not
freshly bound to the exact image that the host LLM reviewed.

## Priority Order

1. **Issue 24A: Crop Uncertainty Stop Boundary**
   - Implemented in this branch.
   - Highest priority.
   - `/fig_loop` already surfaces `crop_audit_summary.evaluation_state:
     needs_action` when crop verdicts are `uncertain`.
   - Before 24A, `/fig_driver --dry-run` did not treat that state as a review
     blocker.
   - Implemented fix: latest loop checkpoints with uncertain crop audit verdicts
     must route to `human_gate_stop` / `human_gate_required`, with a reason that
     names the uncertain crop ids and asks for explicit reread or human review.

2. **Issue 24B: Required Audit Input Presence**
   - Implemented in this branch.
   - Current critique freshness includes `build/visual_clash.json` and
     `build/audit_crops/manifest.json` only when those files exist.
   - Before 24B, visual-clash accounting lint returned no accounting violation
     when `visual_clash.json` was missing.
   - Required fix: for current critique schemas, missing required audit reports
     should be a controlled lint problem rather than silently degrading to
     "zero candidates." Legacy critiques can retain compatibility fallback.

3. **Issue 24C: Crop Content Hash Integrity**
   - The crop manifest participates in critique freshness, but the crop PNG
     files themselves are not content-hashed inside the manifest.
   - Required fix: add deterministic per-crop `sha256:` hashes to the manifest
     and validate that crop files still match the manifest the critique used.

4. **Issue 24D: Historical Visual-Clash Regression Harness**
   - Host-vision dogfood proved the HV+/`V_s` regression can be caught when the
     historical shape is presented with the new visual-clash evidence.
   - Required fix: add deterministic regression coverage for the defect family
     so the plugin does not rely only on host-vision reruns to prevent relapse.

5. **Issue 24E: Structured Accept-Simplification Reasons**
   - Current lint checks visual-clash-linked `accept_simplification` with prose
     length and keyword heuristics.
   - Required fix: introduce a structured reason enum plus rationale text so
     false positives, intentional schematic conventions, outside-target items,
     and convention-acceptable cases can be validated without prose guessing.

## Dependency Graph

```text
24A crop uncertainty stop boundary
  -> 24B required audit input presence
      -> 24C crop content hash integrity

24D historical regression harness can run after 24B or 24C.
24E structured accept-simplification reasons can run independently after 24B.
```

## Non-Goals

- No figure/source drawing changes.
- No hidden auto-patching.
- No score-driven release gates.
- No external web scraping or provider integration.
- No mutation of accepted, golden, export, or publication-provenance state.

## Success Definition

Issue 24 is complete when:

- uncertain crop audits cannot silently pass through the driver;
- missing required audit reports cannot masquerade as zero audit candidates for
  current schemas;
- crop images are bound by content hash to the manifest used by critique
  freshness;
- the HV+/`V_s` defect family has deterministic regression coverage;
- accepted visual-clash simplifications use structured, reviewable reasons.
