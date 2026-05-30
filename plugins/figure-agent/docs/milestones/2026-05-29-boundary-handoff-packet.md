# Boundary Handoff Packet

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-70b-mechanical-boundary-handoff-packet.md`

Status: implemented

Dogfood evidence:
`docs/milestones/2026-05-29-boundary-handoff-dogfood.md`

## Goal

Make `/fig_run` non-complete stops easier for a new operator or host agent to
understand without widening the runner's execution allowlist or introducing a
second router.

## Implemented Behavior

`scripts/fig_run.py` now emits a top-level `boundary_handoff` object for every
non-`complete` result payload.

Contract:

- `schema: figure-agent.boundary-handoff.v1`
- `action`: copied from the final driver action
- `stop_boundary`: copied from the final driver stop boundary
- `required_actor`: `host_llm`, `human`, `svg_editor`, `release_operator`, or
  `workflow_agent`
- `blocking_reason`: compact driver/runner reason, with command failure
  `stderr_tail` included
- `evidence_refs`: copied from `next_action_summary` or fallback driver/runner
  evidence
- `allowed_scope` / `forbidden_scope`: copied from `next_action_summary`
- `closeout_checks`: post-boundary checks for the required actor
- `continuation_guidance`: live status/driver revalidation guidance

`continuation_guidance` intentionally does not include an executable resume
command.

Patch/source-mutation boundaries remain deferred. For `patch_handoff_stop`, the
handoff reports:

- `deferred_boundary: patch_source_mutation_deferred_until_70c`
- `allowed_scope: ["read-only"]`
- `forbidden_scope: ["source mutation before patch executor currentness is verified"]`

This keeps 70B explanatory-only and prevents patch edit scope from leaking into
runner output.

## Tests Added

`tests/test_fig_run.py` now covers:

- host-LLM critique stop -> `required_actor: host_llm`
- missing reference stop -> `required_actor: workflow_agent`
- human gate stop -> `required_actor: human`
- semantic backport stop -> `required_actor: workflow_agent`
- release/golden stop -> `required_actor: release_operator`
- existing adjudication repair stop -> `required_actor: workflow_agent`
- successful complete run -> no `boundary_handoff`
- command failure -> workflow handoff with stderr evidence
- max-step stop -> workflow handoff with repeated-action checks
- patch handoff stop -> deferred marker with no patch scope guidance

Existing runner tests still cover allowlisted execution and refusal behavior.

## Verification

- Red test first:
  `uv run pytest -q tests/test_fig_run.py -k "host_critique or boundary or command_failure or max_steps or release_blocked_handoff or patch_handoff_boundary"`
  failed with six expected `KeyError: 'boundary_handoff'` failures before
  implementation.
- Targeted green:
  same command -> 10 passed.
- Review fix tests:
  `uv run pytest -q tests/test_fig_run.py -k "reference_missing_handoff or semantic_backport_handoff or existing_adjudication_file_blocks_auto_scaffold or draft_export_then_requeries"`
  -> 4 passed.
- Regression target:
  `uv run pytest -q tests/test_fig_run.py`
  -> 28 passed.
- Broader target:
  `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_status.py`
  -> 235 passed.
- Lint:
  `uv run ruff check scripts/fig_run.py tests/test_fig_run.py`
  -> passed.

## Review Notes

- `/fig_run` still executes only the existing allowlist:
  `run_adjudicate`, `run_compile`, `run_export`, `run_fig_loop`.
- The new packet does not change `schema: figure-agent.run.v1` fields.
- No host critique, patch, SVG, accepted/golden, release, or resume automation
  was added.
