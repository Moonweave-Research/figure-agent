# Issue 100DU - Fig-Run JSON Flag Compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, bounded runner

## Problem

`/fig_run` emits JSON by default and already accepted `--format json`, but it
rejected the explicit `--json` spelling used by adjacent JSON-first workflow
commands such as `/fig_drive`, `/fig_queue_run`, and `/fig_improve`.

That creates a needless parser trap when an operator or agent moves from
driver/queue inspection into the bounded runner while carrying the same
explicit-output flag habit.

## Scope

- Accept `--json` as a no-op output compatibility flag.
- Preserve the existing JSON-only output contract.
- Preserve `--format json`, plan-only behavior, `--execute`, journaling, and
  all mutation boundaries.
- Do not introduce alternate output formats or resume/replay behavior.

## Implemented Behavior

- `fig_run.py` now accepts `--json` through argparse and still emits the same
  `figure-agent.run.v1` JSON payload.
- `commands/fig_run.md` documents both explicit output spellings:
  `[--json | --format json]`.

## Tests

- `tests/test_fig_run.py::test_main_accepts_json_as_output_compatibility_noop`
- `tests/test_fig_run.py::test_main_accepts_format_json_as_output_compatibility_noop`
- `tests/test_command_contract_docs.py::test_fig_run_documents_explicit_json_output_spellings`

## Review Notes

- Contract: additive CLI alias only; public JSON fields and exit behavior are
  unchanged.
- Safety: `--json` does not imply `--execute`, record journals, force exports,
  mutate source, or bypass host/human/release boundaries.
- UX: bounded-runner output flags now match the surrounding workflow surface.
