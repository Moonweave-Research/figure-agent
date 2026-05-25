# Issue 46 - Polished-SVG Clean Dogfood

**Status:** completed
**Branch:** `codex/issue46-polished-svg-clean-dogfood`
**Date:** 2026-05-26

## Scope

This milestone proves the plugin route for polished-SVG closure. It does not
edit a real figure and does not claim aesthetic quality. The target is route
coherence:

```text
recipe -> executor -> delta pack -> handoff manifest -> status FRESH -> driver complete
```

## Initial Design Review

- Real fixture dogfood remains useful, but real examples are frequently in
  active authoring states and can make CI nondeterministic.
- A temporary clean fixture is the right guardrail for plugin correctness.
- The route should reuse existing modules; a new orchestrator would be
  premature.

## Evidence

### TDD

Initial test run:

```bash
uv run pytest -q tests/test_svg_polish_clean_dogfood.py
```

Result: failed as expected. The final-artifact state was `STALE` because the
temporary fixture lived outside the repository root while the real manifest hash
contract is repo-relative. The test was corrected with a test-local base-dir
shim; production code was not changed.

Second run:

```bash
uv run pytest -q tests/test_svg_polish_clean_dogfood.py
```

Result: `1 passed`.

### Targeted Verification

```bash
uv run pytest -q tests/test_svg_polish_clean_dogfood.py tests/test_svg_polish_recipe.py tests/test_svg_polish_executor.py tests/test_svg_polish_delta.py tests/test_svg_polish_handoff.py tests/test_status.py tests/test_fig_driver.py
```

Result: `269 passed`.

```bash
uv run ruff check scripts/svg_polish_recipe.py scripts/svg_polish_executor.py scripts/svg_polish_delta.py scripts/svg_polish_handoff.py scripts/status.py scripts/fig_driver.py tests/test_svg_polish_clean_dogfood.py
```

Result: all checks passed.

```bash
git diff --check
```

Result: clean.

### Final Verification

```bash
uv run pytest -q
```

Result: `1208 passed, 1 skipped, 1 xfailed, 6 warnings`.

```bash
uv run ruff check .
```

Result: all checks passed.

```bash
git diff --cached --check && git diff --check
```

Result: clean.

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Result: all three validations passed.

## Route Observed

The clean fixture route exercised:

- fresh generated exports;
- fresh bounded `polish/svg_polish_recipe.yaml`;
- executor write to `polish/<name>.polished.svg`;
- delta pack write to `polish/aesthetic_delta/delta_manifest.json`;
- handoff write to `polish/svg_polish_audit.md` and
  `polish/svg_polish_manifest.yaml`;
- `/fig_status` equivalent state:
  - `render_state: FRESH`
  - `export_state: FRESH`
  - `final_artifact_kind: polished_svg`
  - `final_artifact_state: FRESH`
- `/fig_driver --mode polish` equivalent summary:
  - `action: complete`
  - `safe_command: null`
  - `stop_boundary: null`

## Mutation Boundary

The test uses a temporary fixture only. No real example source, generated
exports, accepted state, golden state, or publication provenance is mutated by
Issue 46.

## Review Notes

1. Contract correctness: the route uses existing public module functions and
   does not introduce a second polish orchestrator.
2. Scope containment: only docs and test coverage changed; no real fixture
   artifacts are committed.
3. Integration readiness: the test closes the gap left by Issue 44E, where a
   real fixture validated tool behavior but not the clean final-artifact route.

No known Issue 46 plugin blocker remains.
