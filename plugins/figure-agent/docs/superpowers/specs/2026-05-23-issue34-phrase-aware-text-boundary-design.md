# Issue 34 Phrase-Aware Text Boundary Design

## Goal

Make text-boundary row-box containment work for visual labels that PDF text
extraction splits into adjacent words or glyph fragments, without adding OCR,
TikZ parsing, regex matching, or semantic guessing.

## Current Constraint

Issue 33 added `text_allowlist` to `rect` / `mode: contain_text`. That filter is
exact PDF-word matching. It works for single extracted words such as `SMU`,
`HV+`, and `Coulomb`, but not for labels that appear as multiple extracted
words:

- `polymer film` -> `polymer` + `film`
- `V_s` -> `V` + `s`
- `F_Maxwell` -> `F` + `Maxwell`
- `q_tr` -> `q` + `tr`

Dogfood on `fig1_overview_v2_pair_001_vault` confirms that subscripted labels
often have slightly shifted y-ranges, so phrase matching cannot require exact
baseline equality.

## Recommended Design

Add optional `text_phrases` to `rect` / `mode: contain_text` checks.

```yaml
text_boundary_layout:
  row_boxes:
    - id: row2
      bbox_pdf_cm: [0.205, 5.863, 17.750, 11.457]
      text_allowlist:
        - SMU
        - Coulomb
      text_phrases:
        - id: polymer_film
          words: ["polymer", "film"]
        - id: v_s
          words: ["V", "s"]
        - id: f_maxwell
          words: ["F", "Maxwell"]
```

`text_boundary_spec_helper.py` copies `row_boxes[].text_phrases` into the
generated `text_boundary_checks` entry after validation.

## Matching Semantics

The checker treats exact words and phrases as two independent text sources for a
single contain check:

- `text_allowlist` continues to match one extracted PDF word exactly.
- `text_phrases` matches an ordered sequence of extracted PDF words.

For each phrase:

1. Sort PDF words by the existing deterministic word sort key.
2. For each word matching the first phrase token, try to extend rightward with
   the next token.
3. A next word is eligible when:
   - text exactly equals the expected token after `strip()`;
   - it is to the right of the previous token;
   - the horizontal gap is not more than `max_phrase_gap_pt`;
   - the two words are visually on the same line.
4. "Same line" means either the y-ranges overlap, or their center-y values
   differ by no more than `max_phrase_y_center_delta_pt`.
5. The phrase candidate uses the union bbox of all matched words.
6. Containment is evaluated against the union bbox using the existing
   `clearance_pt` rule.

Default tolerances:

- `max_phrase_gap_pt: 6.0`
- `max_phrase_y_center_delta_pt: 6.0`

These defaults cover the observed `V` + `s`, `F` + `Maxwell`, and `q` + `tr`
splits in fig1 without allowing arbitrary cross-panel joins. Fixture authors may
override the thresholds per check only if a real PDF extraction case requires
it.

## Candidate Shape

Phrase candidates should preserve the existing text-boundary JSON schema and
extend candidate payloads minimally:

```json
{
  "id": "TB001",
  "kind": "text_outside_rect",
  "text": "F Maxwell",
  "text_source": "text_phrases",
  "phrase_id": "f_maxwell",
  "words": ["F", "Maxwell"],
  "boundary_id": "row2_contain_text",
  "boundary_role": "row_box",
  "bbox_pt": [436.18, 283.85, 462.81, 291.82],
  "boundary_pt": {"bbox": [5.81, 166.20, 503.15, 324.77], "mode": "contain_text"},
  "clearance_pt": 0.0
}
```

Exact word candidates may omit `text_source`, `phrase_id`, and `words` to remain
backward compatible.

## Validation Rules

`text_phrases` is optional. When present:

- it must be a non-empty list;
- each item must be a mapping;
- `id` must be a non-empty string;
- `words` must be a list of at least two non-empty strings;
- phrase ids must be unique within the check;
- `max_phrase_gap_pt`, if present, must be a non-negative number;
- `max_phrase_y_center_delta_pt`, if present, must be a non-negative number.

Malformed declarations must raise `TextBoundaryClashError` in the checker and
`TextBoundarySpecHelperError` in the helper. The CLI should return the existing
controlled exit code 2.

## De-Duplication

The matcher should not emit duplicate candidates for the same phrase id and word
span. If multiple starts produce the same span, keep the first deterministic
match. Exact word candidates and phrase candidates are independent; a fixture
author should avoid putting the same single-word label in both `text_allowlist`
and `text_phrases`.

## Files To Change

- `scripts/check_text_boundary_clash.py`
  - Add phrase validation.
  - Add phrase grouping helpers.
  - Evaluate phrase matches only for `rect` / `mode: contain_text`.
  - Preserve current exact-word behavior when `text_phrases` is absent.
- `scripts/text_boundary_spec_helper.py`
  - Validate and copy `row_boxes[].text_phrases`.
  - Preserve deterministic YAML order.
- `tests/test_text_boundary_clash.py`
  - Add phrase inside/outside tests.
  - Add shifted-subscript tests.
  - Add malformed phrase tests.
  - Add no-duplicate tests.
- `tests/test_text_boundary_spec_helper.py`
  - Add helper copy and malformed phrase tests.
- `docs/superpowers/issues/2026-05-23-issue-34-phrase-aware-text-boundary-containment.md`
  - Update status after implementation.

## TDD Plan

1. Add a failing checker test where `["polymer", "film"]` is inside the rect
   and emits no candidate.
2. Add a failing checker test where the same phrase is outside the rect and
   emits one `text_outside_rect` candidate with `phrase_id`.
3. Add a failing checker test for shifted y-ranges such as `["F", "Maxwell"]`.
4. Add malformed phrase tests for the checker.
5. Implement phrase validation and matching.
6. Add helper tests for copying and validating `text_phrases`.
7. Implement helper support.
8. Run targeted tests, ruff, diff check, and plugin validation.

## Explicit Non-Goals

- No OCR.
- No regex matching.
- No automatic TikZ label extraction.
- No critique schema bump.
- No compile/export/status behavior changes beyond the checker output when
  `text_phrases` is explicitly declared.
- No fixture source edits.

## Review Conclusions

This design is intentionally conservative. It solves the concrete PDF word-split
gap while preserving the local-first deterministic contract. It does not try to
infer visual semantics; fixture authors still declare the labels that matter.
The implementation should be small enough to fit inside the existing
`check_text_boundary_clash.py` and `text_boundary_spec_helper.py` boundaries
without creating another policy layer.
