# Issue 100Q - Critique Entity Consistency Lint

Status: completed

Type: critique trust, semantic drift, operator safety

## Problem

A critique can be hash-fresh and still contain stale semantic prose. The
freshness hash proves the critique was generated from the current input set; it
does not prove every named entity the host LLM says is visible still exists in
the active figure source.

The concrete risk is a label-target audit entry such as `F_Maxwell` marked as
matched/visible after that label has been removed from active TikZ and survives
only in comments or old diagnostic context. That confuses operators because the
plugin appears fresh while the critique discusses a phantom visual entity.

## Scope

Add a conservative lint check for code-like or physics-like entity names in
`audit_enumeration.label_target_matching` entries that claim `matches: true`.

The check is intentionally narrow:

- inspect only the current fixture's active `.tex` source;
- ignore TeX comments when deciding whether an entity is active;
- flag entities that exist only in comments as `comment-only`;
- flag entities absent from both active source and comments as `absent`;
- skip prose-only labels that do not contain source-like symbolic tokens;
- skip fixtures without a matching `.tex` file to preserve legacy tests and
  parser-only use cases.

## Non-Goals

- No image OCR or visual entity detector.
- No automatic source edits.
- No mutation of `critique.md`, `critique_adjudication.yaml`, accepted/golden,
  export, SVG, or publication state.
- No attempt to prove every natural-language object exists in the render.

## Contract

`critique_lint.py` emits a blocker:

```text
BLOCKER: critique_entity_consistency: label_target_matching entity F_Maxwell is comment-only in active TeX source
```

when a matched label-target audit entry cites a symbolic entity that is not
present in active TeX.

## Tests

- comment-only `F_Maxwell` in `.tex` fails lint;
- active `F_{\mathrm{Maxwell}}` in `.tex` passes lint.

## Review Notes

Review 1 - scope:

- The detector is source-text based and only checks matched symbolic labels,
  avoiding broad natural-language hallucination detection.

Review 2 - false positives:

- The check normalizes simple TeX symbol forms such as `F_Maxwell`,
  `F_{Maxwell}`, and `F_{\mathrm{Maxwell}}`.
- Prose labels like `polymer film` are skipped because source spelling may be
  macro-driven or intentionally abstract.

Review 3 - integration:

- `status.py` already surfaces `critique_lint` blockers for fresh critiques, so
  no new status contract is required.
