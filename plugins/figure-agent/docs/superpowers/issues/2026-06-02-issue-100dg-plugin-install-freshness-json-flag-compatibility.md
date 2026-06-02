# Issue 100DG - Plugin install freshness JSON flag compatibility

Status: implemented in this slice

Type: install workflow, CLI compatibility, operator UX

## Problem

`plugin_install_freshness.py` emits JSON by default and is the primary operator
check for "am I using the latest installed plugin?", but it rejected explicit
JSON-output flags:

```bash
uv run python3 scripts/plugin_install_freshness.py --json
uv run python3 scripts/plugin_install_freshness.py --format json
```

After the rest of the workflow surfaces accepted explicit JSON flags, this left
a small but real install-readiness parser trap.

## Scope

- Accept `--json` as a no-op because output is already JSON.
- Accept `--format json` as a no-op because output is already JSON.
- Preserve `figure-agent.plugin-install-freshness.v1` payload shape and exit
  status semantics.

## Non-goals

- Do not add text output.
- Do not change source/install/package/git/marketplace/example-source hygiene
  policy.
- Do not change emitted `next_action` precedence.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_plugin_install_freshness.py::test_cli_accepts_json_noop_flag tests/test_plugin_install_freshness.py::test_cli_accepts_format_json_alias`
  failed with argparse `unrecognized arguments`.
- Green:
  - `uv run pytest -q tests/test_plugin_install_freshness.py::test_cli_accepts_json_noop_flag tests/test_plugin_install_freshness.py::test_cli_accepts_format_json_alias tests/test_plugin_install_freshness.py::test_cli_returns_zero_for_fresh_clean_installed_package`

## Review Notes

1. **Compatibility** - JSON output and exit-code policy are unchanged.
2. **Scope containment** - The flags are parser aliases only.
3. **Operator reality** - Install-readiness diagnostics now accept the same
   explicit JSON spelling as the other JSON-default workflow commands.
