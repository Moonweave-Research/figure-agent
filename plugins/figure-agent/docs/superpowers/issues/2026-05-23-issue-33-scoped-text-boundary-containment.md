# Issue 33 — Scoped Text Boundary Containment

Status: implemented on branch `codex/scoped-text-boundary-containment`; pending final review/merge

## Problem

Issue 29 added `rect` / `mode: contain_text`, and Issue 30 exposed it through
`text_boundary_layout.row_boxes`. In real fixture adoption, raw row-box
containment is too noisy because the checker applies it to every PDF word. A
single Row 2 box therefore flags normal Row 1 text, legends, captions, or
inter-row labels that were never meant to be contained by that row.

This made `row_boxes` unusable for `fig1_overview_v2_pair_001_vault`; the
fixture could only adopt column-rule and forbidden-rectangle checks.

## Goal

Make row-box containment usable without guessing semantic ownership from TikZ
source. The contract should let fixture authors explicitly scope which rendered
text strings are expected inside a containing rectangle.

## Scope

In scope:

- Extend `text_boundary_checks` for `rect` / `mode: contain_text` with optional
  text filters.
- Extend `text_boundary_layout.row_boxes[]` so the helper can emit those
  filters.
- Keep filter matching deterministic and simple.
- Preserve current behavior when no filter is supplied.
- Add focused tests.
- Dogfood the contract on `fig1_overview_v2_pair_001_vault` only if it remains
  low-noise.

Out of scope:

- TikZ source parsing to infer which labels belong to a row.
- Raster OCR ownership inference.
- Hidden auto-editing of source `.tex`.
- Changing visual-clash, critique, export, accepted, or golden behavior.

## Contract

`rect` checks with `mode: contain_text` may declare:

```yaml
text_allowlist:
  - "SMU"
  - "Coulomb"
```

When present, the checker evaluates only words whose extracted PDF text exactly
matches an allowlisted entry. All other words are ignored for that containment
check. Matching is string-exact after the PDF extractor's own word segmentation;
multi-word semantic phrase grouping is not inferred in this issue.

`text_boundary_layout.row_boxes[]` may declare the same field. The helper copies
it into the generated `text_boundary_checks` entry.

## Acceptance Criteria

- A `contain_text` rect with `text_allowlist` ignores non-allowlisted words
  outside the rect.
- The same check still flags an allowlisted word outside the rect.
- Without `text_allowlist`, existing global containment behavior is unchanged.
- `text_boundary_spec_helper.py` copies valid allowlists from row boxes into
  generated checks.
- Malformed allowlists fail with controlled errors.
- Existing tests pass.

## Review Questions

- Is explicit allowlisting narrow enough to avoid false confidence?
- Does it solve the real usability gap without adding brittle geometry
  inference?
- Should a future issue add phrase grouping or regex matching, or is exact
  extracted-word matching enough for the first usable contract?

## Implementation Notes

- `scripts/check_text_boundary_clash.py` now honors optional
  `text_allowlist` for `rect` / `mode: contain_text` checks.
- `scripts/text_boundary_spec_helper.py` validates and copies
  `row_boxes[].text_allowlist` into generated checks.
- Missing `text_allowlist` preserves the original global containment behavior.
- `fig1_overview_v2_pair_001_vault` adopts scoped Row 2 containment for exact
  Row 2-only words and keeps compile output at
  `text_boundary_clash.json.total: 0`.
