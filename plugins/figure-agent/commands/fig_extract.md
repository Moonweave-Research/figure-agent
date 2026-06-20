---
description: Extract OCR labels, palette clusters, and optional vtracer structural hints from a reference PNG into coordinate_hints.yaml.
---

Extract authoring hints from the fixture's reference image. Output is written
to `examples/<name>/coordinate_hints.yaml` and feeds semantic TikZ authoring in
Layer 3 plus layout drift validation in Layer 6. The output is evidence for
placement and color reconstruction; structural hints are authoring evidence, not final source.

**Usage**: `/fig_extract <name>`

Run from the workspace root:

```
fig-agent helper reference_extract.py examples/<name>
fig-agent helper reference_extract.py examples/<name> --rebuild
```

`<name>` maps to `examples/<name>/`. The fixture must declare `reference_image` in `spec.yaml`. Ordinary fixtures (no reference_image) skip cleanly with a clear message — `/fig_extract` is intended for golden-class fixtures.

## What it does

1. Resolves `spec.yaml.reference_image` to an absolute path; aborts if missing.
2. Loads the reference as RGB (RGBA / palette PNGs are converted; alpha is dropped).
3. Runs Tesseract OCR for text labels with bounding box and confidence.
4. Runs a palette PIL connected-component pass for each `polymer-paper-preamble`
   palette color, with per-group RGB-distance thresholds and a
   `min_component_pixels` filter.
5. Runs optional vtracer structural hints when the `vtracer` Python package is
   importable. If vtracer is unavailable or fails, OCR + palette clusters still remain useful and the command writes `structural_regions.status` as
   `unavailable` or `failed`.
6. Writes the joined result to `coordinate_hints.yaml` with metadata,
   reference SHA-256, extraction parameters, and available hint groups.

If `coordinate_hints.yaml` already exists and is no older than the reference, the script reports "up to date" and exits 0 without overwriting. Pass `--rebuild` to force regeneration.

## Output schema (excerpt)

```yaml
metadata:
  extraction_version: "0.3"
  created_at: "2026-04-30T..."
  reference_image_path: reference/golden_target_001.png
  reference_image_hash: sha256:...
  ocr_status: ok                # or 'skipped (tesseract not available)'
  parameters:
    min_component_pixels: 200
    ocr_confidence_floor: 30.0
    group_thresholds: { specific: 55, broad: 55, gray: 35 }
reference_image_size: [1693, 929]
text_labels:
  - text: "Discharge"
    bbox: [753, 59, 833, 80]    # [x1, y1, x2, y2]
    conf: 96.55
palette_shape_clusters:
  cTeal:
    target_rgb: [68, 170, 153]
    threshold: 55
    match_count: 1161
    components:
      - bbox: [1227, 162, 1228, 687]
        pixel_count: 525
structural_regions:
  status: ok                   # ok | unavailable | failed
  panel_arcs: []
  border_boxes: []
  chain_rows: []
  s_atoms: []
  trap_levels: []
```

## Common errors

- `tesseract not found on PATH` — install via `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Debian/Ubuntu). The script still produces shape clusters; only `text_labels` is empty and `metadata.ocr_status` reads "skipped".
- `spec.yaml does not declare reference_image` — Layer 2.5 only applies to fixtures with a fixed visual target. Add `reference_image: reference/<file>.png` to `spec.yaml` first, or skip this command.
- `reference image not found at <path>` — the path declared in `spec.yaml` does not exist on disk.
- `structural_regions.status: unavailable` — `vtracer` is not importable in the
  current Python environment. This does not block authoring: OCR + palette clusters still remain useful placement evidence. Install or enable vtracer
  only when structural hints are needed for a fixture.
- `structural_regions.status: failed` — vtracer was importable but failed while
  vectorizing or parsing the reference image. Inspect the recorded error, rerun
  with `--rebuild`, or continue from OCR + palette clusters when structural
  hints are not required.

## After running

- Inspect `coordinate_hints.yaml` and the OCR labels list for accuracy.
- Use the bbox coordinates as authoring hints when writing `<name>.tex` so labels and shape positions match the reference.
- Re-run with `--rebuild` after the reference image is updated; `/fig_status <name>` surfaces a `coordinate_hints_stale` note when the reference is newer than the hints.

Next: author or refine `examples/<name>/<name>.tex`, then `/fig_compile <name>`.
