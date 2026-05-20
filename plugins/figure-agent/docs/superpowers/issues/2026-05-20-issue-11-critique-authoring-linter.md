# Issue 11: Critique Authoring Linter

**Date:** 2026-05-20 KST
**Status:** implemented on main
**Type:** plugin quality / authoring preflight

## Problem

Dogfood surfaced critique-authoring footguns that are currently caught too late
or with overly indirect messages:

- duplicate finding ids across panel and top-level findings;
- v1.3 top-tier audit blockers that are not linked to a finding,
  `quality_axes.blocking_items`, or `accept_simplification`;
- malformed critique frontmatter that should fail before adjudication scaffold
  writes anything.

`critique_adjudication.py scaffold` already validates most of the contract, but
its main job is to write `critique_adjudication.yaml`. A read-only preflight is
better for `/fig_critique` closeout and dogfood review.

## Implemented Contract

- Add `scripts/critique_lint.py`.
- `lint_critique(example_dir)` returns a list of blocker violations without
  mutating the fixture.
- CLI:

```bash
uv run python3 scripts/critique_lint.py <name|examples/name|path>
```

- Exit `0` and print `OK` when critique lint passes.
- Exit `1` and print blocker diagnostics when lint fails.
- Duplicate finding ids are reported directly as `duplicate_finding_id`.
- Other critique schema/link-rule failures are reported as `critique_contract`.

## Out of Scope

- Rewriting `critique.md`.
- Calling the host LLM.
- Changing `/fig_loop`, `/fig_driver`, `/fig_export`, accepted, golden, or final
  artifact behavior.
- Scoring prose quality or comparing frontmatter against Markdown body prose.

## Verification

- `uv run pytest -q tests/test_critique_lint.py tests/test_critique_adjudication.py tests/test_critique_brief.py`
- `uv run pytest -q`
- `uv run ruff check scripts/critique_lint.py tests/test_critique_lint.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
