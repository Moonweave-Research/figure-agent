# Issue 90 SVG Polish Aesthetic Gate Closeout

Status: implementation complete; final verification passed in this branch.

## Scope

Issue 90 hardened SVG polish readiness and aesthetic delta review. It did not
add hidden SVG mutation, automatic source patching, accepted/golden mutation,
or release promotion from aesthetic scores.

## Implemented

### 90A - SVG Polish Gate Summary

- Added `figure-agent.svg-polish-gate.v1` as a compact operator-facing view
  derived from the existing `svg_polish_readiness` contract.
- `/fig_driver --mode polish` now reports a gate even when no current loop
  checkpoint exists.
- `/fig_loop` JSON and stdout summary include the gate alongside
  `svg_polish_readiness`.

### 90B - SVG Delta Audit Schema And Lint

- Added critique schema `figure-agent.critique.v1.15` and rubric
  `figure-agent.critique-rubric.v1.15`.
- Fresh `polish/aesthetic_delta/delta_manifest.json` now requires v1.15
  critique and a structured `svg_polish_delta_audit`.
- Lint validates before/after/diff image-id accounting against the canonical
  delta manifest.
- Delta pack artifacts already participate in `critique_input_hash`; v1.15
  freshness now follows that existing hash path.

### 90C - Aesthetic Gate Closed Set

- Added v1.15 `aesthetic_gate_audit` with the closed slots:
  `maturity_restraint`, `visual_hierarchy`, `template_genericness`,
  `overdecorated_or_cartoonish`, `journal_fit`, `handcrafted_finish`,
  `semantic_preservation`, `print_scale_finish`, and `paper_wide_coherence`.
- Routes are closed-set and must be compatible with
  `editorial_art_direction.tikz_vs_svg_polish_trigger`.
- Generic aesthetic prose such as "looks polished" is rejected unless it cites
  current-artifact evidence.

## Three Review Cycles

1. Contract/schema/freshness review:
   - Fixed duplicate-readiness risk by deriving `svg_polish_gate` from the
     existing readiness contract.
   - Bumped schema/rubric only for fresh SVG delta opt-in.
   - Confirmed delta files participate in critique input hashing.

2. Backward compatibility and scope containment review:
   - Kept v1.14 and older critiques parseable when no fresh delta manifest is
     present.
   - Kept `/fig_run` and `/fig_queue_run` SVG write behavior unchanged.
   - Preserved release/accepted/golden gates.

3. Test coverage and failure-mode review:
   - Added tests for no checkpoint, ready checkpoint, human gate precedence,
     v1.15 missing delta audit, missing delta image accounting, generic
     aesthetic prose, incompatible SVG route, and brief/rubric output.
   - Verified fixture-local SVG polish dogfood through the existing
     `test_svg_polish_clean_dogfood.py` path.

## Remaining Risks

- Real-figure SVG polish dogfood is still limited because no checked-in example
  currently carries a full polished-SVG manifest flow.
- v1.15 host-vision critique quality still depends on the host actually reading
  before/after/diff images; lint now catches missing accounting but cannot
  prove visual attention beyond structured evidence.

## Verification

- `uv run pytest -q tests/test_svg_polish_clean_dogfood.py tests/test_fig_driver_editorial.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_svg_polish_delta.py`:
  441 passed
- `uv run ruff check .`: All checks passed
- `git diff --check`: clean
- `uv run pytest -q`: 1491 passed, 1 skipped, 1 xfailed, 6 legacy
  deprecation warnings
- `claude plugin validate .claude-plugin/plugin.json`: passed
- `claude plugin validate .`: passed
- `claude plugin validate ../../.claude-plugin/marketplace.json`: passed

No known Issue 90 plugin blocker remains.
