# Issue 34 — Phrase-Aware Text Boundary Containment

Status: completed in commit `ab87fc4`

Design spec:
`../specs/2026-05-23-issue34-phrase-aware-text-boundary-design.md`

## Problem

Issue 33 made `rect` / `mode: contain_text` usable by adding exact
`text_allowlist` filtering. That removes the global-noise problem, but the
matching unit is still the PDF extractor's word text.

This is good enough for labels such as `SMU`, `HV+`, and `Coulomb`, but not for
labels that render as multiple PDF words or glyph fragments:

- phrase labels such as `polymer film`;
- math/subscript labels such as `F_Maxwell`, `V_s`, or `q_tr`;
- labels where the extractor splits a visual label into `F` + `Maxwell` or
  `V` + `s`.

The practical risk is false confidence: authors may add a phrase to
`text_allowlist` and believe it is checked, while the checker never sees that
exact phrase as one PDF word.

## Goal

Add a deterministic phrase/group matching layer for `contain_text` checks so
row-box containment can cover real rendered labels that are split across
adjacent PDF words.

## Scope

In scope:

- Extend `text_boundary_checks` for `rect` / `mode: contain_text` with an
  optional phrase/group field.
- Keep existing `text_allowlist` exact-word behavior backward compatible.
- Validate malformed phrase/group declarations with controlled errors.
- Group only nearby words on the same visual line; do not infer arbitrary
  semantic ownership.
- Emit candidates that still name the source check, candidate text, and word
  bounding box or grouped bounding box.
- Add focused tests for phrase inside rect, phrase outside rect, split math
  label outside rect, malformed phrase declaration, and legacy exact-word
  behavior.

Out of scope:

- OCR or raster-based text recognition.
- TikZ parsing to infer semantic labels.
- Regex matching unless a later issue proves it is needed.
- Host-vision critique changes.
- Source figure edits.

## Candidate Contract

Preferred explicit contract:

```yaml
text_phrases:
  - id: polymer_film
    words: ["polymer", "film"]
  - id: f_maxwell
    words: ["F", "Maxwell"]
```

The checker should:

- match each phrase as an ordered sequence of extracted PDF words;
- require words to be on the same visual line within a small y-overlap or
  baseline tolerance;
- require horizontal adjacency within a conservative gap threshold;
- use the union bounding box of the matched words for `contain_text`;
- preserve deterministic candidate ordering.

## Acceptance Criteria

- Exact `text_allowlist` behavior from Issue 33 remains unchanged.
- A `text_phrases` item whose grouped words are inside the rect produces no
  candidate.
- A `text_phrases` item whose grouped words are outside the rect produces one
  `text_outside_rect` candidate.
- Split labels such as `F` + `Maxwell` can be checked as one phrase.
- Malformed `text_phrases` fails with a controlled error in both the checker
  and `text_boundary_spec_helper.py`.
- `text_boundary_spec_helper.py` copies valid `row_boxes[].text_phrases` into
  generated checks.
- Tests prove the checker does not duplicate candidates for the same phrase.

## Design Decisions

- Grouped candidates expose both joined `text` and the underlying `words`.
- Default tolerances are `max_phrase_gap_pt: 6.0` and
  `max_phrase_y_center_delta_pt: 6.0`, with per-check overrides only when a real
  extraction case requires them.
- Fixture authors must provide stable phrase ids so reports can point back to
  a declared label group.
- The full implementation design lives in
  `../specs/2026-05-23-issue34-phrase-aware-text-boundary-design.md`.
