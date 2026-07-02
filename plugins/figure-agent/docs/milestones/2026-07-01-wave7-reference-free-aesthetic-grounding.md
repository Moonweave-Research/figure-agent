# Wave 7 Reference-Free Aesthetic Grounding

## Result

Reference-free grounded critiques now have an enforceable lint boundary:
top-level and panel findings must carry `grounded_in_rule` when the fixture has
explicit briefing rules, deterministic audit evidence, and no figure/panel
reference image.

## Why

The brief already told the host critic to anchor every reference-free finding to
briefing rules, `panel_goals`, or detector ids, but lint did not enforce that
contract. This left a path where a report-only critique could make generic
visual or aesthetic claims without proving which local rule or audit signal
grounded the claim.

## Scope

- No source fixture, export, release, or generated artifact mutation.
- No model/API calls.
- No scoring or automatic apply authority added.
- Existing fixtures with declared figure or participating panel references keep
  their reference-grounded behavior.
- Existing fixtures without reference-free grounding context keep legacy lint
  behavior.

## Implemented

- `scripts/critique_lint.py` adds `reference_free_grounding` blocker detection.
- `scripts/critique_brief.py` states that reference-free mode does not waive
  `aesthetic_intent.yaml` anchor/accounting requirements.
- `tests/test_critique_lint.py` covers missing `grounded_in_rule` and a passing
  reference-free + aesthetic intent critique.
- `tests/test_critique_brief.py` covers combined reference-free and aesthetic
  intent briefing text.

## Validation

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_lint.py tests/test_quality_manifest.py
uv run ruff check scripts/critique_lint.py scripts/critique_brief.py tests/test_critique_brief.py tests/test_critique_lint.py
python -m compileall scripts/critique_lint.py scripts/critique_brief.py
git diff --check
```

