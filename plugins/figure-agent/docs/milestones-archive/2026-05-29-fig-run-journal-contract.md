# Fig Run Journal Contract

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-70d-fig-run-journal-contract.md`

Status: implemented

## Goal

Persist `/fig_run` evidence so a later operator can inspect what the runner saw
and why it stopped, without turning old runner output into workflow authority.

## Implemented Behavior

`scripts/fig_run.py` now records a journal by default in `--execute` mode. A
plan-only run records only when `--record` is passed:

```text
.scratch/fig-run-runs/<timestamp>-<name>/
├── run_manifest.json
├── run.json
├── steps/
│   └── step_001.json
└── stop.md
```

The stdout JSON remains the public payload. When recording is enabled, the
payload also includes:

```yaml
journal:
  schema: figure-agent.fig-run-journal-ref.v1
  run_dir: <path>
  manifest_path: <path>
  run_path: <path>
  stop_path: <path>
  authoritative: false
  replay_allowed: false
  commands_are_evidence_only: true
  rerun_live_status_first: true
  rerun_live_driver_first: true
```

The manifest schema is `figure-agent.fig-run-journal.v1`.

## Safety Contract

- Journals are evidence, not authority.
- Journals do not contain executable resume commands.
- Journals preserve public `safe_command` fields as evidence only.
- `replay_allowed` is always false.
- `commands_are_evidence_only` is always true.
- Future resume UX must rerun live `/fig_status` and `/fig_drive`.
- `run_workflow()` remains pure and does not write journals directly.
- Plan-only mode remains no-write by default.
- `--record` opts a plan-only run into recording.
- `--no-record` preserves stdout-only behavior for execute mode.
- `--runs-root <path>` allows tests and dogfood runs to redirect records.

## Tests Added

`tests/test_fig_run.py` now covers:

- plan-only CLI journal writing through explicit `--record` and redirected
  `--runs-root`;
- no default plan-only journal writes;
- default execute-mode journal writes;
- default execute-mode records under `.scratch/fig-run-runs/` when `--runs-root`
  is omitted;
- manifest, full `run.json`, per-step JSON, and `stop.md` shape;
- multi-step runs write one `steps/step_###.json` file per public step;
- sanitized fixture names for journal directories;
- manifest `started_at`, `completed_at`, `branch`, and `commit` fields;
- manifest `started_at` / `completed_at` bracket the actual runner call, not
  only journal serialization time;
- command-failure journals remain non-authoritative and non-replayable;
- journal write failures emit `journal_error` while preserving the public run
  payload;
- journal reference fields in stdout JSON;
- `--execute --no-record` disabling writes;
- `run_workflow()` not writing journals directly.

## Verification

- Red test first:
  `uv run pytest -q tests/test_fig_run.py -k "journal or no_record"`
  failed with expected missing `--runs-root` / `--no-record` parser errors.
- Targeted green:
  same command -> 9 passed.
- Regression target:
  `uv run pytest -q tests/test_fig_run.py`
  -> 39 passed.
- Lint:
  `uv run ruff check scripts/fig_run.py scripts/fig_run_records.py tests/test_fig_run.py`
  -> passed.
- CLI smoke:
  `uv run python3 scripts/fig_run.py smoke_trap_demo --mode review --goal "70D journal smoke" --max-steps 2 --record --runs-root <tmpdir>`
  -> wrote journal ref, manifest, `run.json`, one step JSON, and `stop.md`;
  `authoritative: false`, `replay_allowed: false`.
- Expanded target:
  `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_status.py`
  -> 246 passed.
- Full suite:
  `uv run pytest -q`
  -> 1422 passed, 1 skipped, 1 xfailed, 6 warnings.
- Full lint:
  `uv run ruff check .`
  -> passed.
- Plugin validation:
  `claude plugin validate .claude-plugin/plugin.json`,
  `claude plugin validate .`, and
  `claude plugin validate ../../.claude-plugin/marketplace.json`
  -> passed.

## Review Notes

The journal deliberately does not alter driver selection or runner execution.
It is a persistence layer around the already-built public payload. This keeps
70D separate from 70E resume behavior.

Review fixups:

- Plan-only default recording was removed because it weakened the no-mutation
  dry-run contract. Plan-only recording now requires explicit `--record`.
- Fixture names are sanitized before journal directory creation.
- Manifest currentness metadata now includes timestamps, branch, and commit.
- Journal-write failure no longer causes the CLI to drop the public run result.
- Recorded command strings are explicitly marked evidence-only rather than
  replayable.
- Manifest timing now records the runner start/end window before journal write.
