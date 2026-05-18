# Fig Loop Quality Axes Ingestion Plan

**Goal:** Make `/fig_loop` consume v1.2 critique `quality_axes` in its existing
axis verdict slots without widening the public loop contract.

**Architecture:** Keep `/fig_loop` verify-only. Read `critique.md`
frontmatter with the existing tolerant YAML-frontmatter helper. If the critique
is schema v1.2 and `quality_axes` is a mapping, derive compact quality summaries
for existing loop slots. If anything is legacy or malformed, preserve the
current fallback behavior.

## Mapping

| Loop axis | v1.2 source axes |
|---|---|
| `story_hierarchy` | `message_storyline`, `panel_role_coherence`, `composition_layout` |
| `reference_fidelity` | `reference_fidelity` |
| `publication_safety` | `publication_readiness` |

Grouped axes use conservative severity order:

```text
pass < needs_patch < needs_human < block
```

`not_applicable` is treated as `not_configured` when it is the only available
signal. A missing quality axis falls back to the old loop behavior rather than
causing a runtime failure; full schema rejection remains owned by
`critique_adjudication.py`.

## Test Plan

1. Add a helper v1.2 critique writer in `tests/test_fig_loop.py`.
2. Add RED tests for:
   - story hierarchy mapped from v1.2 axes,
   - reference fidelity mapped from v1.2 axis,
   - publication safety mapped from v1.2 axis,
   - malformed or legacy critique fallback without crash.
3. Implement the smallest parser and mapping helpers in `scripts/fig_loop.py`.
4. Update `/fig_loop` command docs to state that v1.2 quality-axis evidence can
   populate those existing slots.
5. Verify with targeted and full tests.

## Verification

```bash
uv run pytest -q tests/test_fig_loop.py
uv run pytest
uv run ruff check plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

