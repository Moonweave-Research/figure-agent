# Wave 8 source-boundary handoff

## `_volume_shading_demo`

Wave 8 treats `examples/_volume_shading_demo` as a source-authoring or removal decision, not as an export or host-critique lane.

Observed files:

- `examples/_volume_shading_demo/briefing.md`
- `examples/_volume_shading_demo/spec.yaml`
- `examples/_volume_shading_demo/exports/_volume_shading_demo.svg`
- `examples/_volume_shading_demo/polish/_volume_shading_demo.polished.svg`

Missing file:

- `examples/_volume_shading_demo/_volume_shading_demo.tex`

Fresh status evidence:

- `fig-agent status _volume_shading_demo --json` reports `render_state=NOT_AUTHORED`.
- `next_action_summary.action=create_or_fix_source`.
- `next_action_summary.blocking_source=source_not_authored`.
- `next_action_summary.safe_command=null`.
- The queue row has `first_blocker=source_not_authored` and no safe command.

Boundary decision:

- Do not run compile/export/critique for this fixture until source exists.
- Do not synthesize or author the missing source in Wave 8.
- A future owner must either author `examples/_volume_shading_demo/_volume_shading_demo.tex` from the spec/briefing or remove/retire the fixture from the active queue.
