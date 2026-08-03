# Dogfood: Fig. 1 Charge-Trap Overview

Fixture: `examples/fig1_charge_trap_overview`

This is the scientific Fig. 1-style dogfood fixture. It is a qualitative
charge-trap electret actuator overview with three panels:

- layered electret stack and charge injection
- qualitative trap-depth landscape
- long-retention and electrostatic bending actuation

## Verified Path

```bash
rsvg-convert -b white -d 600 -p 600 -f png \
  -o examples/fig1_charge_trap_overview/reference/fig1_charge_trap_overview_draft.png \
  examples/fig1_charge_trap_overview/reference/fig1_charge_trap_overview_draft.svg

uv run --with vtracer python scripts/svg_underlay.py \
  --from-spec examples/fig1_charge_trap_overview

uv run python scripts/svg_contract.py \
  examples/fig1_charge_trap_overview/source/fig1_charge_trap_overview.svg \
  --spec examples/fig1_charge_trap_overview/spec.yaml

uv run python scripts/svg_export.py fig1_charge_trap_overview

uv run python scripts/svg_qa.py \
  examples/fig1_charge_trap_overview/source/fig1_charge_trap_overview.svg \
  --spec examples/fig1_charge_trap_overview/spec.yaml \
  --pdf examples/fig1_charge_trap_overview/exports/fig1_charge_trap_overview.pdf \
  --png examples/fig1_charge_trap_overview/exports/fig1_charge_trap_overview.png \
  --reference-png examples/fig1_charge_trap_overview/reference/fig1_charge_trap_overview_draft.png \
  --max-diff 0.62

uv run python scripts/svg_status.py fig1_charge_trap_overview
```

Observed evidence:

- real vtracer underlay generation passed through `--from-spec`
- semantic SVG contract passed
- SVG QA passed, including PDF font/text checks
- status reported `EXPORT_FRESH`
- visual diff vs independent draft PNG: `0.062981`
- PNG/TIFF raster size: `4323 x 1938`
- TIFF DPI: `600 x 600`
- vtracer underlay size: about 112 KB

## Readiness Judgment

This fixture is the first credible scientific end-to-end pass for the
SVG-first layer. It shows that the layer can carry a manuscript-style schematic
from rough draft reference through locked vtracer evidence, semantic SVG source,
export, and QA without treating traced paths as final source.

This still does not prove universal paper-final readiness. It proves the layer
is ready for the next real manuscript figure trial, where the visual judgment
must come from the author rather than from automated checks alone.
