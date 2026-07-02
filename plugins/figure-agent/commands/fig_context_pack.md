# /fig_context_pack

Compile a deterministic, read-only authoring context pack for one fixture.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent" context-pack <name> [--json | --format json]
```

`--json` and `--format json` are accepted. The command reads `spec.yaml`,
`briefing.md`, paper-local authoring files, the bundled style lock, the
project rule catalog, and any paper/series rule catalog explicitly selected by
`spec.yaml` (`paper_id`, `series_id`, or
`authoring_context_pack.rule_catalog`). It also includes `narrative_context`, a read-only
human-perspective compiler that records source-anchored reader path, panel-story
inputs, and human review questions. It does not write files, call a model, run a
generation executor, score candidates, mutate source, or revive prompt-loop
orchestration.
