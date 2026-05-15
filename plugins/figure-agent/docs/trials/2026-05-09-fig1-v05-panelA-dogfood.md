# 2026-05-09 Fig1 v0.5 Panel A Dogfood

## Setup

- Fixture: `examples/fig1_overview_v2`
- Source commit before this trial: `c01edaf` (`wip(fig1): Panel A rewrite -- DIB rings connected via explicit bridge chains`)
- Goal: test the smallest v0.5 per-panel reference path before expanding to N=3.

This trial adds one panel reference only:

```yaml
panels:
  - id: A
    caption: Sulfur-rich network
    reference_image: reference/sulfur_polymer_panelA_ref.png
    bbox_pdf_cm: [0.141, 0.141, 4.591, 5.227]
```

The bbox came from:

```bash
uv run python scripts/spec_bbox_helper.py fig1_overview_v2 \
  --panel id=A x=0,3.5 y=5,9
```

## Verification

Commands run from `plugins/figure-agent`:

```bash
bash scripts/compile.sh examples/fig1_overview_v2/fig1_overview_v2.tex
uv run python scripts/critique_brief.py examples/fig1_overview_v2
uv run python scripts/status.py examples/fig1_overview_v2
```

Observed:

- Compile succeeded and regenerated `build/fig1_overview_v2.{pdf,png}`.
- Compile reported 1 collision and 43 visual clash candidates; these are existing report-only QA warnings, not compile blockers.
- `critique_brief.py` emitted `## Per-panel reference contexts` with:
  - build crop: `examples/fig1_overview_v2/build/panel_crops/A.png`
  - panel reference: `examples/fig1_overview_v2/reference/sulfur_polymer_panelA_ref.png`
  - bbox: `[0.141, 0.141, 4.591, 5.227]`
- `/fig_status` equivalent reports stage `3/4`, `not accepted`, exports `MISSING`, and `coordinate_hints_stale`.

## Result

The N=1 panel path is useful. The existing figure-level critique (`examples/fig1_overview_v2/critique.md`, generated 2026-05-08) did not include a Panel A finding. With the Panel A crop next to the panel-specific reference, several issues become visually obvious:

1. The S8 inset is clipped by the Panel A crop at the upper-right edge; the reference keeps the S8 inset fully inside the panel.
2. The "Sulfur-rich polymer" / "DIB-linked polysulfide network" caption overlaps the lower network geometry; the reference keeps the caption below the chemical network.
3. The rendered panel uses a compact triangular 3-DIB fragment, while the reference shows a more open network with a central DIB, two lower DIBs, and extended outgoing chains. If the new triangular topology is intentional, the briefing/reference should be updated; otherwise this is a structural mismatch.
4. Several S labels in the S8 inset render with visible white label boxes over bonds, making the inset look patched rather than chemically integrated.

## Decision

This supports the modified Claude review decision:

- Do N=1 first, not N=3.
- Per-panel reference grounding is a real lever, because it surfaces panel-local issues that full-figure critique can miss.
- Do not add a connectivity metric or new rubric enum from this result. The finding can stay under `structural` prose.
- Do not add macro coverage ratio WARN from this result. This trial says reference grounding helped; it does not establish an editability threshold.

## Follow-up Patch

The follow-up edit corrected Panel A toward the reference rather than changing
the reference:

- lifted the DIB network upward to clear the caption,
- attached the previously floating edge chains to DIB rings,
- moved and shrank the S8 inset so it stays inside the Panel A crop,
- removed the white label boxes from S8 sulfur labels,
- moved the caption below the chemical network.

Post-patch compile regenerated the figure and the Panel A crop. The crop no
longer clips the S8 inset, and the caption no longer overlaps the lower DIB
network.
