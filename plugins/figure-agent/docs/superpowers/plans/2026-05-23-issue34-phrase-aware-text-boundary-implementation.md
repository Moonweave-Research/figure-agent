# Issue 34 Phrase-Aware Text Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for each behavior slice and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement phrase-aware `contain_text` matching for text-boundary checks so split PDF labels such as `polymer film`, `V` + `s`, and `F` + `Maxwell` can be checked as grouped labels.

**Architecture:** Keep the change inside the existing text-boundary checker and helper. `check_text_boundary_clash.py` remains the runtime detector; `text_boundary_spec_helper.py` remains the author-facing layout-to-check generator. No critique, status, export, or source figure behavior changes are included.

**Tech Stack:** Python, pytest, YAML specs, existing PDF word extraction from `check_visual_clash.extract_pdf_words_and_page`.

---

## Source Of Truth

Read first:

- `plugins/figure-agent/docs/superpowers/specs/2026-05-23-issue34-phrase-aware-text-boundary-design.md`
- `plugins/figure-agent/docs/superpowers/issues/2026-05-23-issue-34-phrase-aware-text-boundary-containment.md`
- `plugins/figure-agent/scripts/check_text_boundary_clash.py`
- `plugins/figure-agent/scripts/text_boundary_spec_helper.py`
- `plugins/figure-agent/tests/test_text_boundary_clash.py`
- `plugins/figure-agent/tests/test_text_boundary_spec_helper.py`

## Task 1: Checker Phrase Matching

**Files:**
- Modify: `plugins/figure-agent/scripts/check_text_boundary_clash.py`
- Test: `plugins/figure-agent/tests/test_text_boundary_clash.py`

- [ ] **Step 1: Add failing tests for phrase containment**

Add tests:

```python
def test_containing_row_box_text_phrase_inside_rect_is_clean() -> None:
    checks = [
        {
            "id": "row2_box",
            "kind": "rect",
            "role": "row_box",
            "mode": "contain_text",
            "bbox_pdf_cm": [0.0, 0.0, 3.0, 2.54],
            "clearance_pt": 0.0,
            "text_phrases": [{"id": "polymer_film", "words": ["polymer", "film"]}],
        }
    ]
    words = [
        _word("polymer", 20.0, 20.0, 50.0, 30.0),
        _word("film", 54.0, 20.0, 70.0, 30.0),
        _word("caption", 140.0, 20.0, 170.0, 30.0),
    ]

    assert boundary.detect_text_boundary_clashes(words, (220.0, 220.0), checks) == []


def test_containing_row_box_text_phrase_outside_rect_emits_one_candidate() -> None:
    checks = [
        {
            "id": "row2_box",
            "kind": "rect",
            "role": "row_box",
            "mode": "contain_text",
            "bbox_pdf_cm": [0.0, 0.0, 2.54, 2.54],
            "clearance_pt": 0.0,
            "text_phrases": [{"id": "polymer_film", "words": ["polymer", "film"]}],
        }
    ]
    words = [
        _word("polymer", 90.0, 20.0, 120.0, 30.0),
        _word("film", 124.0, 20.0, 140.0, 30.0),
    ]

    candidates = boundary.detect_text_boundary_clashes(words, (220.0, 220.0), checks)

    assert len(candidates) == 1
    assert candidates[0]["kind"] == "text_outside_rect"
    assert candidates[0]["text"] == "polymer film"
    assert candidates[0]["text_source"] == "text_phrases"
    assert candidates[0]["phrase_id"] == "polymer_film"
    assert candidates[0]["words"] == ["polymer", "film"]
    assert candidates[0]["bbox_pt"] == [90.0, 20.0, 140.0, 30.0]
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q \
  tests/test_text_boundary_clash.py::test_containing_row_box_text_phrase_inside_rect_is_clean \
  tests/test_text_boundary_clash.py::test_containing_row_box_text_phrase_outside_rect_emits_one_candidate
```

Expected: fail because `text_phrases` is not implemented.

- [ ] **Step 3: Implement phrase validation and grouping**

In `check_text_boundary_clash.py` add helper functions with these responsibilities:

- `DEFAULT_MAX_PHRASE_GAP_PT = 6.0`
- `DEFAULT_MAX_PHRASE_Y_CENTER_DELTA_PT = 6.0`
- `_text_phrases(check)` validates and returns phrase declarations.
- `_phrase_tolerances(check)` validates and returns gap/y-center tolerances.
- `_word_center_y(word)` returns `(ymin + ymax) / 2.0`.
- `_same_phrase_line(left, right, max_center_delta)` returns true when y-ranges
  overlap or center-y values differ by at most `max_center_delta`.
- `_group_phrase_words(words, phrase, max_gap, max_center_delta)` returns
  deterministic word spans for one phrase declaration.
- `_phrase_candidate(check, phrase, span, rect, clearance)` builds the same
  `text_outside_rect` candidate shape used by exact-word containment, plus
  `text_source`, `phrase_id`, and `words`.

Implementation rules:

- validate `text_phrases` only when present;
- each phrase item must have non-empty `id` and at least two non-empty `words`;
- phrase ids must be unique per check;
- `max_phrase_gap_pt` and `max_phrase_y_center_delta_pt` must be non-negative numbers when present;
- phrase matching scans sorted words deterministically;
- a next token must be to the right of the previous token, within gap tolerance, and same-line by y-overlap or center-y tolerance;
- phrase candidate uses union bbox and existing containment logic.

- [ ] **Step 4: Verify GREEN**

Run the same focused test command. Expected: pass.

## Task 2: Subscript And Deduplication Behavior

**Files:**
- Modify: `plugins/figure-agent/scripts/check_text_boundary_clash.py`
- Test: `plugins/figure-agent/tests/test_text_boundary_clash.py`

- [ ] **Step 1: Add failing tests for shifted y-ranges, malformed declarations, and no duplicates**

Add tests:

```python
def test_containing_row_box_text_phrase_matches_shifted_subscript_words() -> None:
    checks = [
        {
            "id": "row2_box",
            "kind": "rect",
            "role": "row_box",
            "mode": "contain_text",
            "bbox_pdf_cm": [0.0, 0.0, 2.54, 2.54],
            "clearance_pt": 0.0,
            "text_phrases": [{"id": "f_maxwell", "words": ["F", "Maxwell"]}],
        }
    ]
    words = [
        _word("F", 90.0, 20.0, 96.0, 27.0),
        _word("Maxwell", 96.5, 23.0, 126.0, 31.0),
    ]

    candidates = boundary.detect_text_boundary_clashes(words, (220.0, 220.0), checks)

    assert [candidate["phrase_id"] for candidate in candidates] == ["f_maxwell"]


def test_containing_row_box_text_phrase_rejects_large_gap() -> None:
    checks = [
        {
            "id": "row2_box",
            "kind": "rect",
            "role": "row_box",
            "mode": "contain_text",
            "bbox_pdf_cm": [0.0, 0.0, 2.54, 2.54],
            "clearance_pt": 0.0,
            "text_phrases": [{"id": "polymer_film", "words": ["polymer", "film"]}],
        }
    ]
    words = [
        _word("polymer", 90.0, 20.0, 120.0, 30.0),
        _word("film", 160.0, 20.0, 180.0, 30.0),
    ]

    assert boundary.detect_text_boundary_clashes(words, (220.0, 220.0), checks) == []


def test_containing_row_box_text_phrase_rejects_duplicate_phrase_id() -> None:
    checks = [
        {
            "id": "row2_box",
            "kind": "rect",
            "role": "row_box",
            "mode": "contain_text",
            "bbox_pdf_cm": [0.0, 0.0, 2.54, 2.54],
            "clearance_pt": 0.0,
            "text_phrases": [
                {"id": "polymer_film", "words": ["polymer", "film"]},
                {"id": "polymer_film", "words": ["polymer", "film"]},
            ],
        }
    ]

    with pytest.raises(boundary.TextBoundaryClashError, match="duplicate"):
        boundary.detect_text_boundary_clashes([], (220.0, 220.0), checks)
```

- [ ] **Step 2: Verify RED**

Run the new tests and confirm they fail for missing behavior.

- [ ] **Step 3: Complete validation and deduplication**

Update checker implementation so:

- malformed `text_phrases` raises `TextBoundaryClashError`;
- large gaps do not match;
- shifted y-ranges match within default center tolerance;
- duplicate phrase ids are rejected;
- duplicate word spans are not emitted twice.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_text_boundary_clash.py
```

Expected: all text-boundary clash tests pass.

## Task 3: Helper Contract Support

**Files:**
- Modify: `plugins/figure-agent/scripts/text_boundary_spec_helper.py`
- Test: `plugins/figure-agent/tests/test_text_boundary_spec_helper.py`

- [ ] **Step 1: Add failing helper tests**

Add tests:

```python
def test_build_text_boundary_checks_copies_text_phrases() -> None:
    layout = {
        "row_boxes": [
            {
                "id": "row2",
                "bbox_pdf_cm": [0.0, 0.0, 13.8, 4.5],
                "text_phrases": [
                    {"id": "polymer_film", "words": ["polymer", "film"]},
                    {"id": "f_maxwell", "words": ["F", "Maxwell"]},
                ],
            }
        ]
    }

    checks = helper.build_text_boundary_checks(layout)

    assert checks[0]["text_phrases"] == [
        {"id": "polymer_film", "words": ["polymer", "film"]},
        {"id": "f_maxwell", "words": ["F", "Maxwell"]},
    ]


def test_build_text_boundary_checks_rejects_malformed_text_phrases() -> None:
    layout = {
        "row_boxes": [
            {
                "id": "row2",
                "bbox_pdf_cm": [0.0, 0.0, 13.8, 4.5],
                "text_phrases": [{"id": "bad", "words": ["polymer"]}],
            }
        ]
    }

    with pytest.raises(helper.TextBoundarySpecHelperError, match="text_phrases"):
        helper.build_text_boundary_checks(layout)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q \
  tests/test_text_boundary_spec_helper.py::test_build_text_boundary_checks_copies_text_phrases \
  tests/test_text_boundary_spec_helper.py::test_build_text_boundary_checks_rejects_malformed_text_phrases
```

Expected: fail because helper does not copy or validate `text_phrases`.

- [ ] **Step 3: Implement helper validation/copy**

Add `_optional_text_phrases(item, label)` next to `_optional_text_allowlist`.

Rules:

- absent -> `None`;
- present must be a non-empty list;
- each item must be mapping;
- `id` must be non-empty string;
- `words` must contain at least two non-empty strings;
- phrase ids must be unique;
- preserve input order;
- copy into generated check as `text_phrases`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_text_boundary_spec_helper.py
```

Expected: all helper tests pass.

## Task 4: Documentation Status And Verification

**Files:**
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-23-issue-34-phrase-aware-text-boundary-containment.md`
- Optional modify: `plugins/figure-agent/docs/superpowers/specs/2026-05-23-issue34-phrase-aware-text-boundary-design.md` only if implementation changes the design.

- [ ] **Step 1: Update Issue 34 status**

After code and tests pass, change status from:

```markdown
Status: designed; implementation pending
```

to:

```markdown
Status: implemented in branch `codex/issue34-phrase-aware-text-boundary`
```

- [ ] **Step 2: Run focused verification**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_text_boundary_clash.py tests/test_text_boundary_spec_helper.py tests/test_fig_closeout.py
uv run ruff check scripts/check_text_boundary_clash.py scripts/text_boundary_spec_helper.py tests/test_text_boundary_clash.py tests/test_text_boundary_spec_helper.py
git diff --check
```

Expected:

- all targeted tests pass;
- ruff reports `All checks passed!`;
- `git diff --check` emits no output and exits 0.

- [ ] **Step 3: Run plugin validation**

Run:

```bash
cd plugins/figure-agent
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all three validations pass.

- [ ] **Step 4: Optional full suite**

Run before PR or merge:

```bash
cd plugins/figure-agent
uv run pytest -q
```

Expected: full suite passes with the repository's known skip/xfail counts.

## Review Checklist

Before committing implementation, verify:

- `text_allowlist` exact-word behavior is unchanged.
- `text_phrases` only affects `rect` / `mode: contain_text`.
- Phrase matching cannot join words across distant columns because gap and y-line rules are enforced.
- Candidate JSON remains backward compatible for existing exact-word candidates.
- Malformed phrase declarations fail with controlled errors.
- No fixture `.tex`, export, accepted, or golden artifact is modified.

## Commit Guidance

Preferred commit:

```bash
git add \
  plugins/figure-agent/scripts/check_text_boundary_clash.py \
  plugins/figure-agent/scripts/text_boundary_spec_helper.py \
  plugins/figure-agent/tests/test_text_boundary_clash.py \
  plugins/figure-agent/tests/test_text_boundary_spec_helper.py \
  plugins/figure-agent/docs/superpowers/issues/2026-05-23-issue-34-phrase-aware-text-boundary-containment.md
git commit -m "Implement phrase-aware text-boundary containment"
```

Open a PR after local verification passes. Normal PR CI should run `test`; `full-render` may skip unless label/main-triggered.
