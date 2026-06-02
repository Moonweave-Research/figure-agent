# Issue 100DH - JSON evidence-helper flag compatibility

Status: implemented in this slice

Type: CLI compatibility, operator UX, evidence helpers

## Problem

Three documented evidence-helper CLIs emit JSON by default, but rejected the
same explicit JSON-output flags accepted by the primary workflow commands:

```bash
uv run python3 scripts/fig_run_journal.py <name> --json
uv run python3 scripts/detector_feedback_ledger.py --format json
uv run python3 scripts/diagnostic_artifact_provenance.py <name> <path> --json
```

This was a small but real parser trap on paths operators use after interrupted
runs, detector-tuning reviews, and scratch-artifact provenance checks.

## Scope

- Accept `--json` as a no-op because output is already JSON.
- Accept `--format json` as a no-op because output is already JSON.
- Apply the compatibility to:
  - `fig_run_journal.py`;
  - `detector_feedback_ledger.py`;
  - `diagnostic_artifact_provenance.py`.

## Non-goals

- Do not add text output.
- Do not change schema payloads, exit codes, freshness rules, detector
  aggregation, or artifact provenance classification.
- Do not change mutation boundaries. All three helpers remain read-only.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_run_journal.py::test_cli_accepts_json_noop_flag tests/test_fig_run_journal.py::test_cli_accepts_format_json_alias tests/test_detector_feedback_ledger.py::test_cli_accepts_json_noop_flag tests/test_detector_feedback_ledger.py::test_cli_accepts_format_json_alias tests/test_diagnostic_artifact_provenance.py::test_cli_accepts_json_noop_flag tests/test_diagnostic_artifact_provenance.py::test_cli_accepts_format_json_alias`
  failed with argparse `unrecognized arguments`.
- Green:
  - same command passed after adding parser aliases.

## Review Notes

1. **Contract preservation** - JSON schemas and return-code policy are
   unchanged.
2. **Scope containment** - The change is parser-only and does not affect
   figure source, critique, export, accepted, golden, or SVG-polish state.
3. **Operator consistency** - Evidence helpers now accept the same explicit
   JSON-output spelling as the hardened driver, queue, run, loop, closeout,
   status, improve, and install-readiness surfaces.
