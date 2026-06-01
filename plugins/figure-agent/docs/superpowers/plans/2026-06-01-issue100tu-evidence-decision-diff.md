# Issue 100T/U Implementation Plan

## Slice

Implement two P2 auditability hardening features without changing release gates:

1. Issue 100T: optional `inspection_trace.yaml` parser/validator.
2. Issue 100U: read-only adjudication decision diff preview.

## TDD Plan

### 100T

- Add tests for valid inspection trace loading.
- Add tests for missing trace as `not_applicable`.
- Add tests for duplicate artifact IDs, missing artifact, stale artifact hash,
  and malformed YAML.
- Implement `scripts/inspection_trace.py` with a small public API and validate
  CLI.
- Wire optional trace validation into `critique_lint.py` so present-but-stale
  traces are visible through the normal critique gate.

### 100U

- Add tests for preview preserving same-shape decisions.
- Add tests for dropped, added, and shape-changed decisions.
- Add a CLI preview test proving no file write occurs.
- Implement helper + `sync --preview`.

## Verification

Targeted:

```bash
uv run pytest -q plugins/figure-agent/tests/test_inspection_trace.py plugins/figure-agent/tests/test_sync_critique_adjudication.py plugins/figure-agent/tests/test_critique_adjudication.py plugins/figure-agent/tests/test_critique_lint.py
uv run ruff check plugins/figure-agent/scripts/inspection_trace.py plugins/figure-agent/scripts/critique_adjudication.py plugins/figure-agent/scripts/critique_lint.py plugins/figure-agent/tests/test_inspection_trace.py plugins/figure-agent/tests/test_sync_critique_adjudication.py plugins/figure-agent/tests/test_critique_lint.py
git diff --check
```

Final:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate plugins/figure-agent/.claude-plugin/plugin.json
claude plugin validate plugins/figure-agent
claude plugin validate .claude-plugin/marketplace.json
```

## Risk Review

- Keep 100T optional to avoid fake proof or new brittle gates.
- Keep 100U read-only to avoid changing human decision semantics.
- Do not touch fixture source/export/golden/accepted artifacts.
