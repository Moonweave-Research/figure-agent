# /fig_context_pack

Compile a deterministic, read-only authoring context pack for one fixture.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent" context-pack <name> [--json | --format json]
```

`--json` and `--format json` are accepted. The command reads `spec.yaml`,
`briefing.md`, paper-local authoring files, the bundled style lock, and the
fig1 rule catalog. It does not write files, call a model, run a generation
executor, or revive prompt-loop orchestration.
