# F1·F2·F4 스키메틱 일관성 패치 — 2026-09-08

canonical: `/Volumes/LabShare/ResearchOS-data/02_Surfur_Polymer/docs/figure_set/FIGURE_REGISTRY.yaml`
consumers_updated: F2 full PDF/PNG, F2 builder/vector compositor, layout PPTX slide 2, F4 source/render/caption/contracts, control_tower.md, schematic_registry.md, figure_submission_checklist.md, PAPER_STATUS.md, figure_set README, Figure Agent source mirrors, scoped Cowork handoff ZIP.
superseded: `docs/figure_set/_history/20260908__f124-consistency-patch/` — pre-patch canonical files, affected documents and earlier Figure Agent source/critique bytes. No original source was deleted.
checks: F2(a)/F4 strict compile; current-hash critique lint and adjudication; SVG/PDF/PNG/TIFF/editable-source export; verify-only loop; typography extraction; quantitative-region and PPTX-entry preservation; registry and ResearchOS closeout reports stored alongside this report.
visual_review: pass — 49 required detail/seam/print/grayscale crops plus full renders, full F2 and rendered layout slide 2 were inspected. The comparison PDF is inspected separately at closeout.
unresolved: human manuscript/publication acceptance; F4 full-assembly panel namespace; F4 cohort-specific instrument morphology and caption acceptance; existing quantitative F4 limitations.

## Applied changes

- **F1:** no defensible new source defect was found in this patch scope. The registered M1 remains the visual baseline and its source/PDF/PNG hashes are unchanged.
- **F2(a):** app/mob below-script type was raised from about 4.18 to **5.20 pt** at 180 mm; headers now use regular Arial with a common hierarchy. `early fit` became `early-time extrapolation`; the long explanatory line became `under constant applied field`. Unspecified trap states, field and response use neutral black/gray to avoid stealing the blue/red shallow/deep meaning from F1/F4. Existing sparse, hand-positioned state glyphs and qualitative curves remain.
- **Full F2:** panel a is now a PDF vector object with searchable text. The original lower quantitative region (y ≥ 60 mm at 300 dpi) is byte-identical; measured data, fitting and b–d curves were not regenerated. The compositor rejects an ambiguous multiple-image input and is wired into the existing builder so regeneration retains vector placement.
- **F4:** sentence-case stage titles and concise captions; `cross-section`; shallow circles/deep squares with comparable area; d moved off the specimen edge; signed V_s at readout and magnitude |V_s| on the positive decay curve. The isometric material stack, sensing-area shading, charge positions and hand-authored line rhythm were retained.
- **F4 topology:** two-terminal HV return at charging, explicit manual transfer, and earth ground only at measurement follow the later user-confirmed project rules. The all-stage-grounding argument in the former README was an agent inference and is archived. The faded source is a previous-state ghost, not an automated withdrawal mechanism. Negative charge is an illustrative polarity in the caption.
- **PPTX:** only `ppt/media/image2.png` and `ppt/slides/slide2.xml` changed; every other ZIP entry is byte-identical. The slide-2 caption qualifies the microscopic picture as a schematic working model. The final slide was rendered without repair and inspected.

## Typography and visual reading

| Figure | Minimum PDF type at 180 mm | Embedded/extracted families | Source SHA-256 |
|---|---:|---|---|
| F1 M1 | 5.03 pt | Arial-BoldMT, Arial-ItalicMT, ArialMT, ArialUnicodeMS | `64be82b40c9cb8f5475cffd5c2e793b05ce4f76493a938f61c3e2d39ca635025` |
| F2(a) | 5.20 pt | Arial-BoldMT, Arial-ItalicMT, ArialMT | `49eb7635cde9075a6a575a1bef858730138f63d2c4cc5256321a7a8cfd8a74e3` |
| F4 schematic | 5.48 pt | Arial-BoldMT, Arial-ItalicMT, ArialMT | `f173012c079b3277728ae9a053227b365136fd46f55ab6a8f648269554eb5d3a` |

F1 uses Arial Unicode MS for the proportionality glyph; it is an explicit symbol fallback, not a hidden Computer Modern/Helvetica text substitution. These figures use a shared hierarchy rather than forcing every semantic role to the same point size. Circle/square categories in F4 remain legible in grayscale. The 360 px thumbnail tests reading order only; it does not establish fine-text readability. No visual evidence warrants regenerating the illustrations with an image model.

## Evidence and boundaries

`examples/*/critique.md` and `inspection_trace.yaml` bind current crop hashes to recorded host image inspection. These files establish inspected evidence integrity, not independent proof of scientific truth. F4 has four report-only visual-clash flags for its HV box and mathematical glyphs; local inspection found no obscured text. The schematic geometry profile reports apparatus/axis edges as informational rather than table boundaries; actual collision and label checks remain active.

The broad F4 sensor head preserves the selected component's artwork but is not demonstrated to match the project's Keyence SK bar-head rule or the actual external temperature-series apparatus. That discrepancy is explicitly `needs_human` under component fidelity; do not call it an experimentally validated instrument drawing. The F4 quantitative assembly still has a–d while this component has a–e. The registry retains `canonical_not_yet_composed` and all quantitative blockers. Human accepted/golden/release fields were not changed.

Exact paths and hashes: `FIGURE_REGISTRY.yaml`, `final_font_measurements.json`, `protected_integrity.json`, `quantitative_preservation.json`, `deck_preservation.json`, `closeout_manifest.json`. Earlier 2026-09-08 review passes are superseded for the altered source bytes. This patch changes figure assets and their validation mirrors; it does not claim a new Figure Agent runtime installation.

Canonical detailed evidence: /Volumes/LabShare/ResearchOS-data/02_Surfur_Polymer/docs/figure_set/reviews/F124_consistency_20260908
