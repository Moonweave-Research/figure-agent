# Issue 100D Implementation Plan

## Slice

Add a positive-route SVG polish recipe template. Keep execution and release
gates unchanged.

## TDD Plan

- Add a test that `svg_polish_recipe_template(example_dir)` emits reloadable
  YAML with the current `recipe_input_hash`.
- Add a test that the template includes conservative operation classes:
  `label_micro_position`, `stroke_polish`, and `typography_cleanup`.
- Add CLI coverage for `--template examples/<name>`.
- Add CLI coverage for `--write-template` and overwrite refusal.
- Add controlled error coverage when the fixture's exported SVG is missing.

## Implementation

- Add `svg_polish_recipe_template(example_dir, base_dir=...)`.
- Add `--template <example-dir>` to `scripts/svg_polish_recipe.py`.
- Keep `validate_svg_polish_recipe()` unchanged.
- Update Issue 100 inventory and command docs with the starter command.

## Verification

```bash
uv run pytest -q tests/test_svg_polish_recipe.py tests/test_svg_polish_executor.py
uv run ruff check scripts/svg_polish_recipe.py scripts/svg_polish_executor.py tests/test_svg_polish_recipe.py tests/test_svg_polish_executor.py
git diff --check
uv run pytest -q
uv run ruff check .
claude plugin validate plugins/figure-agent/.claude-plugin/plugin.json
claude plugin validate plugins/figure-agent
claude plugin validate .claude-plugin/marketplace.json
```

## Review Checklist

- Template is deterministic and fixture-local.
- Template does not imply execution permission.
- Existing recipe validation and executor safety stay unchanged.
- No build/export/polish artifacts are committed.
