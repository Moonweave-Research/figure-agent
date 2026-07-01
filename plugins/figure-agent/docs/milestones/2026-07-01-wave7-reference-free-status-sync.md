# Wave 7 Reference-Free Status Sync

## Result

`critique_adjudication.py sync` now follows the same reference-free critique
requirement as `/fig_status`: a fixture with explicit briefing rules and
deterministic audit evidence is not treated as `critique_state=NOT_REQUIRED`
just because it has no reference image.

## Why

`status.compute_critique_state` already distinguished:

- no reference and no reference-free grounding context -> `NOT_REQUIRED`
- no reference but explicit briefing/audit grounding and no critique -> `BRIEFING_REQUIRED`
- no reference but fresh grounded critique -> `FRESH`

The adjudication sync preflight still used the older shortcut:

- no figure/panel reference -> `NOT_REQUIRED`

That could make direct scripts reject or skip a valid reference-free critique
path even while status surfaces expected a grounded critique.

## Implemented

- `scripts/critique_adjudication.py` imports
  `has_reference_free_grounding_context`.
- Its metadata preflight now returns `BRIEFING_REQUIRED` for missing
  reference-free grounded critiques instead of `NOT_REQUIRED`.
- Fresh reference-free briefing critiques continue into adjudication sync.
- `tests/test_critique_adjudication.py` covers both missing and fresh
  reference-free briefing critique cases.

## Validation

```bash
uv run pytest -q tests/test_status.py tests/test_critique_adjudication.py tests/test_fig_closeout.py tests/test_fig_queue.py
uv run pytest -q tests/test_critique_adjudication.py tests/test_status.py
uv run ruff check scripts tests
python -m compileall -q scripts
git diff --check
```

