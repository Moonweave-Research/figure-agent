# Issue 99 Label-Frame Boundary Clash Plan

## Goal

Add an auto-discovered text-label vs frame/rule crossing detector to the
existing undeclared-geometry checker.

## Implementation Plan

1. Add failing tests in `tests/test_undeclared_geometry.py`.
   - horizontal rule crossing text bbox -> `label_crosses_horizontal_rule`;
   - horizontal rule clear of text bbox -> no label crossing;
   - rectangle bottom/top/side border crossing text bbox ->
     `label_crosses_rect_boundary`.

2. Implement minimal geometry helpers in `check_undeclared_geometry.py`.
   - Convert rects to four border line descriptors.
   - Detect horizontal/vertical line intersection with word bbox.
   - Emit crossing candidates only for true intersections.
   - Keep deterministic sorting and `UG###` numbering.
   - Use rendered PDF path coordinates for CLI crossing candidates; source
     coordinates are kept only for existing `undeclared_*` and near-miss
     behavior because they do not include final PDF placement offsets.

3. Confirm existing brief surface.
   - The existing undeclared-geometry brief section should list new kinds because
     it prints candidate kind/evidence/id generically.
   - Add a brief regression only if needed.

4. Run fixture no-false-positive check on fixed fig1.
   - Write report to `/tmp`, not fixture build state.
   - Confirm no candidate of the new crossing kinds references `log t`, `E_t`,
     `Shallow`, or `Deep`.

5. Run verification.
   - targeted pytest;
   - full pytest;
   - ruff;
   - diff check;
   - plugin validate.

## Review Checklist

- Does this reuse the existing `UG###` report rather than creating a competing
  namespace?
- Does it avoid false positives for normal label clearance?
- Does it preserve strict-mode behavior?
- Does it avoid fixture/source/golden/export mutation?
- Does the host LLM see the candidate through the existing critique brief?
