# Issue 100BW - Visual-Clash Warning Budget CLI Target Boundary

Status: completed on main in merge commit `e54bc56`
Type: CI guardrail, release readiness, fixture path boundary
Priority: P1

## Problem

`scripts/check_visual_clash_budget.py` is a CI/final-mode guardrail for
compiled visual-clash WARN candidates. Its Python API intentionally accepts
arbitrary fixture-like directories for tests and local composition, but the CLI
also accepted raw relative target paths.

Before this issue, an operator could run:

```bash
python3 scripts/check_visual_clash_budget.py examples/../outside
python3 scripts/check_visual_clash_budget.py outside
```

and receive a normal `OK outside: visual_clash total ... <= cap ...` result if
that sibling directory happened to contain `spec.yaml` and
`build/visual_clash.json`.

That is the wrong boundary for a release-adjacent guardrail. The CLI should
certify only the repo's `examples/` tree or a fixture under it. It should not
turn traversal-like paths or existing sibling directories into normal fixture
targets.

## Contract

The command-line interface accepts:

- `examples`
- `examples/<fixture-name>`
- `<fixture-name>` when `examples/<fixture-name>` exists
- absolute paths only when they resolve to `examples` or a direct fixture
  directory under `examples`

The command-line interface rejects:

- traversal-like paths such as `examples/../outside`;
- existing single-component relative directories outside `examples/`;
- nested relative paths outside the supported fixture forms;
- unsafe fixture names rejected by `fixture_identity`.

The lower-level `check_targets()` and `check_fixture()` APIs remain unchanged so
tests and callers can still pass explicit temporary directories when they are
not acting as the public CLI.

## Out Of Scope

- Changing visual-clash candidate scoring.
- Changing `visual_clash_cap` semantics.
- Blocking report-only detector WARNs outside the final/CI budget path.
- Restricting detector scripts that intentionally accept arbitrary PDF paths
  and explicit `--json-output` destinations.

## Acceptance

- A CLI invocation with `examples/../outside` fails before checking the outside
  directory's budget.
- A CLI invocation with an existing `outside` sibling directory fails instead of
  treating it as a fixture target.
- Existing `check_fixture()` and `check_targets()` tests still pass.
- The CI workflow command `scripts/check_visual_clash_budget.py examples`
  remains supported.

## Verification

- `uv run pytest -q tests/test_visual_clash_budget.py`
- `uv run pytest -q tests/test_visual_clash_budget.py tests/test_fig_driver.py tests/test_ci_workflows.py`
- `uv run ruff check scripts/check_visual_clash_budget.py tests/test_visual_clash_budget.py`
- `git diff --check`
- Final full-suite and plugin validation before merge.
