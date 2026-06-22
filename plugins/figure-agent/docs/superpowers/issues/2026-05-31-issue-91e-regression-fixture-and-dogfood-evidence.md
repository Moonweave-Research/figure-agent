# Issue 91E - Regression Fixture And Dogfood Evidence

Status: completed

Type: regression proof, dogfood evidence, release safety

Depends on:

- Issue 91A - SVG delta artifact hash and renderer provenance
- Issue 91B - SVG semantic diff checker
- Issue 91C - TikZ boundary and near-miss auto-discovery
- Issue 91D - crop and delta observation grounding

## What To Build

Create a regression evidence pass that proves Issue 91 catches the edge cases
it was designed to catch.

This is not a new feature gate. It is the closeout proof for the full Issue 91
slice set.

## Required Evidence Cases

1. SVG delta artifact drift:
   - Generate a valid SVG delta pack.
   - Mutate one delta PNG without changing source SVG, polished SVG, or recipe.
   - Verify stale/invalid state is detected.
2. SVG semantic drift:
   - Use a small polished SVG fixture that removes or outlines a text label.
   - Verify semantic diff reports `text_identity_loss`.
3. SVG group-transform overreach:
   - Use a fixture where a parent group transform moves multiple semantic
     children.
   - Verify semantic diff reports `group_transform_risk`.
4. TikZ undeclared boundary:
   - Use a fixture with a drawn box or rule that is not represented in
     `spec.yaml`.
   - Verify `build/undeclared_geometry.json` reports the candidate.
5. TikZ near-miss:
   - Use a fixture where a label is visually too close to a line/path but does
     not bbox-overlap.
   - Verify the near-miss report is generated and critique accounting is
     required.
6. Shallow crop evidence:
   - Use a critique fixture that names all crop ids but uses generic evidence.
   - Verify lint rejects it under the new schema and legacy schema remains
     parseable.

## Acceptance Criteria

- [x] Evidence is recorded in a milestone document under
      `docs/milestones/`.
- [x] Each required evidence case has a command, expected failure/pass state,
      and observed result.
- [x] No accepted, golden, export, publication, or real paper figure source is
      mutated by the dogfood pass.
- [x] Synthetic fixtures or temporary test fixtures are used where real fixture
      mutation would be unsafe.
- [x] Full test suite, ruff, diff check, and plugin validation pass after the
      evidence pass.

## Evidence

- Milestone:
  `docs/milestones-archive/2026-05-31-issue-91-regression-fixture-and-dogfood-evidence.md`
- Targeted command:
  `uv run pytest -q tests/test_svg_polish_delta.py tests/test_svg_semantic_diff.py tests/test_undeclared_geometry.py tests/test_critique_schema_validator.py tests/test_critique_lint.py`
- Result: 216 passed.

Final verification:

- `uv run pytest -q`
  - Result: 1529 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Edge Cases

- Dogfood fixtures must not depend on local-only absolute paths.
- Evidence should distinguish plugin defects from intentional human gates.
- If a real fixture is used, the run must be report-only unless the user
  explicitly approves source or golden mutation.
- A false positive should be recorded as a calibration issue, not hidden.

## Verification

- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
