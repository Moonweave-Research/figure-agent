# L5.5 Post-Export Visual Critic — spec (v0.2.1)

## Motivation

`/fig_critique` (Layer 4.5) inspects `build/<name>.png` — the direct lualatex render.
`/fig_export` (Layer 5) regenerates the PNG via `dvisvgm → rsvg-convert`, a different
rasterisation path that can introduce colour-profile drift, font-substitution artefacts,
and DPI-rounding differences invisible at the build stage.

L5.5 closes this gap by running a vision critique on `exports/<name>.png` after export,
using the same host-Claude-Code read-and-write pattern as L4.5.

## Trigger

After `/fig_export <name>` completes successfully:

```
/fig_export <name>   →   L5.5 auto-triggered if exports/<name>.png is newer than
                         exports_critique.md (or exports_critique.md is absent)
```

L5.5 is **not** re-triggered by `/fig_compile` alone; it requires a fresh export artifact.

## Inputs

| Input | Path |
|-------|------|
| Export PNG | `examples/<name>/exports/<name>.png` |
| Briefing | `examples/<name>/briefing.md` |
| Spec | `examples/<name>/spec.yaml` |
| Reference image (if declared) | path resolved from `spec.yaml.reference_image` |
| Coordinate hints (if present) | `examples/<name>/coordinate_hints.yaml` |
| Style lock | `styles/polymer-paper-preamble.sty` |

The freshness input set matches D3 (`_critique_source_paths` / `_source_paths`) so that
`/fig_status` and L5.5 staleness rules stay in sync.

## Output

`examples/<name>/exports_critique.md` — same YAML front-matter schema as `critique.md`
(schema v1), but with `source: exports_png` added to the front-matter to distinguish it
from the build-stage critique.

```markdown
---
schema: figure-agent.critique.v1
source: exports_png
fixture: <name>
generated_at: <ISO-8601>
verdict: ready | revise | block
findings: [...]
---
```

## Gate

**Report-only** for v0.2.1 (mirrors L4.5 policy). Findings are written to
`exports_critique.md`; the pipeline does not halt on `revise` or `block` verdicts.

Gate promotion to N=5+ requires:
- Five or more distinct fixtures having both L4.5 and L5.5 critiques.
- Comparison showing L5.5 catches ≥1 finding not present in the L4.5 critique
  in at least 3 of the 5 fixtures (evidence that the export rasterisation path
  introduces distinct artefacts worth gating on).

Until N=5 is reached, L5.5 is informational only.

## Staleness detection

`exports_critique.md` is stale when any of the following is newer than it:

- `exports/<name>.png`
- `briefing.md`
- `spec.yaml`
- `reference_image` (if declared and present)
- `coordinate_hints.yaml` (if present)
- `styles/polymer-paper-preamble.sty` (if present)

`/fig_status` reports `exports_critique_stale` as a note when this condition holds.
(Implementation deferred to the L5.5 feature PR; this spec records the intended rule.)

## Implementation plan (deferred)

1. `scripts/run_export.py`: after `_regenerate()`, call `critique_brief.generate_for()`
   with `png_override=exports_dir / f"{name}.png"` and write output to
   `exports_critique.md`.
2. `scripts/critique_brief.py`: accept optional `png_override` parameter so L5.5
   can redirect the render path without duplicating brief logic.
3. `scripts/status.py`: add `exports_critique_stale` note using the freshness set above.
4. Tests: mock the host-read step; assert `exports_critique.md` is written after export.
