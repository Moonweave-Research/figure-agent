# Issue 91 - TikZ And SVG Semantic Near-Miss Audit Hardening

Status: completed

Type: cross-layer audit hardening, TikZ deterministic checks, SVG semantic
preservation, crop evidence integrity

Depends on:

- Issue 23 - zoom and reference-calibrated audit roadmap
- Issue 29 - text-boundary clash detection
- Issue 31 - label-path proximity audit
- Issue 43 - aesthetic lever grammar
- Issue 63 - reference learning and aesthetic metrics
- Issue 73 - SVG polish trigger semantics
- Issue 90 - SVG polish and aesthetic gate hardening

## Problem

The plugin has become strong at preventing stale state, missing audit evidence,
unaccounted crops, unsafe export, and unapproved golden/final-artifact
mutation. It is now hard for a visibly broken figure to pass accidentally when
the defect is represented in existing deterministic inputs.

The remaining failure class is more specific:

1. An LLM can draw a TikZ figure that is formally fresh, linted, and
   crop-accounted, but still has a near-miss visual defect that is not declared
   in `spec.yaml` as a boundary/path check.
2. An LLM or external tool can polish SVG in a bounded-looking way while
   changing semantic structure through group transforms, label identity loss,
   renderer differences, or untracked delta artifacts.
3. A host vision critique can claim that all crops or SVG delta images were
   inspected, but current lint can only verify accounting fields and generic
   evidence markers, not that the observation is locally grounded.

Issue 90 made SVG polish gateable. Issue 91 makes the gate harder to fool.

## Goal

Make the TikZ and SVG audit layers resilient against the edge cases that arise
when an LLM authors or polishes a figure:

- undeclared box/rule geometry created by TikZ edits;
- label/path/boundary near misses that are visually bad but not hard overlaps;
- SVG delta images that drift independently of their manifest;
- SVG edits that preserve file freshness but alter scientific or label
  semantics;
- crop and delta-image audit entries that are syntactically complete but
  visually ungrounded.

The target behavior is not perfect computer vision. The target behavior is a
conservative audit contract: when deterministic evidence cannot prove safety,
the loop must surface the uncertainty and route to TikZ repair, SVG semantic
backport, or human art-direction review.

## Non-Goals

- Do not add broad automatic figure generation.
- Do not add hidden auto-patching or hidden SVG editing.
- Do not require SVG polish for figures that are already release-ready.
- Do not turn aesthetic score into an independent release gate.
- Do not require external vision APIs.
- Do not use full-image SSIM as a blocking similarity metric against
  references; references are style and semantic anchors, not pixel targets.
- Do not mutate accepted, golden, export, or publication state.

## Proposed Issue Slices

### Issue 91A - SVG Delta Artifact Hash And Renderer Provenance

Make `polish/aesthetic_delta/delta_manifest.json` freshness include
`before.png`, `after.png`, `diff.png`, and the renderer/toolchain identity used
to produce them.

This prevents a critique from staying fresh after the visible delta images
change or after a different renderer changes anti-aliasing, font fallback, or
stroke rasterization.

### Issue 91B - SVG Semantic Diff Checker

Add a deterministic semantic diff report for generated SVG versus polished SVG.

The report should detect label text loss, label-to-path conversion when text
identity is expected, arrow/path count changes, large group transforms,
unexpected color-class remaps, target selector overreach, and changed element
ids/classes. It should not decide aesthetic quality. It should decide whether a
polish is still visual-only or must route to semantic backport/human review.

### Issue 91C - TikZ Boundary And Near-Miss Auto-Discovery

Add deterministic pre-critique checks for undeclared boundary/path risks:

- likely rectangles or column rules introduced in TikZ but missing from
  `spec.yaml` boundary checks;
- label-to-line/path distance bands that are not hard overlaps but are close
  enough to create print-scale visual stacking;
- endpoint-to-label clearance around dashed lines, arrows, and S-curves;
- warning budget for undeclared geometry that should be either added to
  `spec.yaml` or explicitly dismissed.

### Issue 91D - Crop And Delta Observation Grounding

Harden critique evidence so a host LLM cannot pass by saying "all crops look
fine" without crop-local evidence.

For each required crop and each SVG delta image, critique entries should cite
local object names, relative position, candidate ids, and the exact observed
relationship. Generic prose remains invalid.

### Issue 91E - Regression Fixture And Dogfood Evidence

Prove the hardening on real and synthetic fixtures before calling Issue 91
complete.

This slice should include small synthetic fixtures for deterministic edge
cases and at least one real fixture replay for historical failures:

- an SVG delta PNG changed after manifest generation;
- SVG text identity loss or group-transform overreach;
- a TikZ box/rule near-miss with no declared boundary check;
- a critique that accounts for a crop id with generic evidence.

The dogfood must not mutate accepted/golden/publication state.

## Cross-Layer Edge Cases To Cover

### TikZ Source And Render Edge Cases

1. A new instrument box is drawn in TikZ but not represented in
   `spec.yaml.text_boundary_checks`.
   - Expected: warning or blocker identifying an undeclared boundary candidate.
2. A new column rule is drawn in TikZ but not represented in boundary checks.
   - Expected: warning or blocker identifying undeclared rule geometry.
3. A label sits just outside a box by less than one glyph descender.
   - Expected: text-boundary or near-miss candidate, not silent pass.
4. A label is technically inside a box but visually touches the border at print
   scale.
   - Expected: low-clearance candidate.
5. A dashed line ends close to a label but does not intersect its bbox.
   - Expected: endpoint/label clearance candidate.
6. A curve passes just below a label baseline.
   - Expected: label-path proximity candidate when path is declared, and
   undeclared-path warning when it is not.
7. A label is converted to outlines or rendered as a path.
   - Expected: text extraction coverage warning if expected text disappears.
8. Math subscripts or superscripts split into separate PDF words.
   - Expected: phrase-aware checks remain usable; missing phrase grouping is
   reported rather than silently skipped.
9. TikZ `scope`, `shift`, `scale`, `rotate`, `foreach`, or macro expansion
   hides the source coordinate from simple regex.
   - Expected: render-level checks still run; source-line attribution may be
   best-effort but must not suppress the finding.
10. A crop manifest contains stale crop ids from a previous render.
    - Expected: lint rejects hash/path mismatch through existing crop manifest
    checks.

### SVG Polish Edge Cases

1. Delta images change without source SVG, polished SVG, or recipe changing.
   - Expected: delta manifest becomes stale.
2. The renderer changes and produces different anti-aliasing or font metrics.
   - Expected: renderer/toolchain mismatch or delta manifest stale state.
3. A bounded `translate` on a parent group moves multiple semantic elements.
   - Expected: semantic diff or executor plan flags group-transform risk.
4. A text label is converted to paths by an editor.
   - Expected: semantic diff reports label identity loss.
5. An arrowhead or path is simplified away.
   - Expected: semantic diff reports path/marker count or id loss.
6. A color is visually polished but changes a semantic role, such as active
   force versus passive recovery.
   - Expected: semantic diff reports color-class remap or routes to human
   semantic review when the class is unknown.
7. Polished SVG introduces filters, masks, clips, foreignObject, raster images,
   or external references.
   - Expected: semantic diff reports unsupported SVG features unless explicitly
   allowed by manifest and review.
8. SVG `viewBox`, width, height, or transform changes alter framing.
   - Expected: semantic diff reports geometry-frame change.
9. SVG diff shows no meaningful pixel change although a recipe claims
   improvement.
   - Expected: delta audit routes `no_meaningful_change` or
   `continue_svg_polish`.
10. SVG diff shows major visual change but no semantic change is declared.
    - Expected: route to `semantic_backport_required` or
    `needs_human_art_direction`.

### Host Vision Audit Edge Cases

1. The critique accounts for a crop id but uses generic evidence.
   - Expected: lint rejects or routes to uncertain crop audit.
2. The critique says all crops are clear but omits the local candidate object.
   - Expected: crop observation grounding violation.
3. The critique cites the wrong crop path or wrong visual-clash id.
   - Expected: existing crop/ref accounting rejects unknown ids.
4. The critique accepts SVG polish while crop uncertainty remains.
   - Expected: driver blocks polish acceptance and routes to human/re-read.
5. The critique marks `accept_svg_polish` while the final artifact manifest is
   missing, invalid, stale, or blocked.
   - Expected: status/driver still requires manifest/final-artifact gate.

## Acceptance Criteria

- [x] Issue 91A makes SVG delta artifacts hash-bound and renderer-bound.
- [x] Issue 91B produces a deterministic SVG semantic diff report and routes
      semantic risk to backport or human review.
- [x] Issue 91C surfaces undeclared TikZ boundary/path risks before host vision
      critique.
- [x] Issue 91D rejects crop/SVG-delta observations that are syntactically
      complete but not locally grounded.
- [x] Issue 91E demonstrates the new gates on regression fixtures and records
      evidence without source/golden/accepted/publication mutation.
- [x] Legacy critiques and fixtures remain parseable through existing legacy
      paths.
- [x] `/fig_run`, `/fig_queue_run`, `/fig_driver`, `/fig_loop`,
      `/fig_status`, and `/fig_export` remain non-mutating outside their
      existing explicit mutation contracts.
- [x] Full verification passes after all slices:
      `uv run pytest -q`, `uv run ruff check .`, `git diff --check`, and the
      three `claude plugin validate` commands.

## Review Log

### Review 1 - Contract Completeness

Finding: the initial design could have focused only on SVG delta artifacts and
missed TikZ undeclared geometry.

Fix: split Issue 91 into four slices and made TikZ auto-discovery a first-class
slice, not a footnote.

### Review 2 - False-Positive Control

Finding: a naive "reference similarity" or full-image SSIM gate would punish
intentional redraws and conflict with the plugin's reference policy.

Fix: explicitly excluded full-image SSIM and scoped deterministic checks to
semantic/geometry/aesthetic-class evidence, not pixel identity.

### Review 3 - Operator Safety

Finding: SVG polish acceptance could be misread as release approval.

Fix: repeated the Issue 90 rule that `accept_svg_polish` is delta-local and
that status/export/publication/final-artifact gates remain authoritative.

### Review 4 - LLM Attention Failure

Finding: crop-read accounting alone does not prove the host LLM inspected the
relevant local object.

Fix: added Issue 91D for local object/position/candidate evidence rather than
only crop id accounting.

### Review 5 - Evidence Sufficiency

Finding: unit tests alone would not prove the new contracts catch the
historical workflow failures that motivated the issue.

Fix: added Issue 91E as a mandatory regression and dogfood evidence slice.

### Review 6 - Schema Migration Safety

Finding: crop and delta observation grounding changes the current critique
shape and could silently tighten legacy v1.15 critiques if applied in place.

Fix: child issues now require an explicit vNext schema/rubric bump whenever
they add required critique fields, while legacy v1.15 and older critiques
remain parseable through legacy paths.
