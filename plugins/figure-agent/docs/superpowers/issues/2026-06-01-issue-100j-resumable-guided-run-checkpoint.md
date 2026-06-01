# Issue 100J - Resumable Guided Run Checkpoint

Status: implemented on branch `codex/issue100j-run-journal-summary`

Type: operator UX, run journal safety, long-session continuation

## Problem

`/fig_run` records non-authoritative journals under `.scratch/fig-run-runs`,
but a later session had to inspect raw `run_manifest.json`, `run.json`, step
JSON, and `stop.md` to understand where the workflow stopped. That made long
sessions fragile after interruption.

The unsafe solution would be a true `--resume` command that replays a stored
`safe_command`. That is intentionally not implemented. A stored command can be
stale as soon as source, critique, adjudication, build, export, or acceptance
state changes.

## Implemented Behavior

Added:

```bash
uv run python3 scripts/fig_run_journal.py <name>
```

The command emits:

```yaml
schema: figure-agent.fig-run-journal-summary.v1
fixture: <name>
state: missing | available | stale
authoritative: false
replay_allowed: false
resume_command: null
next_live_commands:
  - /fig_status <name>
  - /fig_drive <name> --mode <mode> --goal <goal> --dry-run
run_dir: <latest valid journal>
final_action: <previous action>
final_stop_boundary: <previous stop boundary>
final_stop_reason: <previous stop reason>
required_actor: <actor from boundary_handoff>
closeout_checks: [...]
stale_against: [...]
```

Selection rules:

- only valid `figure-agent.fig-run-journal.v1` manifests are considered;
- journals for other fixtures are ignored;
- malformed journals are ignored;
- the newest valid journal by manifest/run payload mtime is selected;
- fixture evidence newer than the selected journal marks the summary `stale`;
- stored `final_safe_command` is intentionally omitted from the summary.

## Non-Goals

- Do not add an executable resume mode.
- Do not replay `safe_command` values from `.scratch`.
- Do not mutate source, critique, adjudication, build, export, accepted,
  golden, SVG, or publication state.
- Do not scan unrelated `.scratch` trees.
- Do not change `/fig_drive` routing.

## Tests

Added `tests/test_fig_run_journal.py` covering:

- missing journal root;
- newest valid journal selection while ignoring malformed and wrong-fixture
  records;
- stale summary when fixture evidence is newer than the journal;
- custom `--runs-root` support.

## Design Review

### Review 1 - Resume Safety

The summary is explicitly not a resume mechanism. It never emits the stored
`final_safe_command`; it emits only live `/fig_status` and `/fig_drive`
commands. This keeps continuation tied to current state.

### Review 2 - Staleness Boundary

The summary checks the same high-level fixture evidence classes that make a
run journal unsafe as continuation state: source, authoring docs, critique,
adjudication, and build artifacts. Newer evidence marks the summary `stale`
without hiding the prior stop context.

### Review 3 - Operator Utility

The output is compact enough for a fresh agent session: previous stop, actor,
closeout checks, and live commands are in one JSON object. Raw run JSON remains
available for forensic inspection, but is no longer the default operator path.
