# Figure Style Guide — Nature / Nature Communications

**Target journal class**: Nature & Nature Communications.

**Source policy**: every rule below is verbatim or near-verbatim from official
Nature / Nature Portfolio author guidelines (URLs at end). No AI-generated
"general best practice." When a category has no official rule, it is left
empty by design — those slots fill from `work_log_*.md` evidence over time.

**Citation key** (inline `[N1]`, `[N2]`, `[N3]`, `[N4]`, `[N5]` map to URLs at end).

## How to grow this file

1. After finishing a figure, add a "Lessons for next figure" section to its `work_log_vN.md`.
2. Promote a lesson here only if (a) it generalizes across figures AND (b) it is consistent with the Nature rules. If a personal preference contradicts a Nature rule, the Nature rule wins for submitted manuscripts.
3. Mark personal/lab additions with `[lab]` so they are distinguishable from publisher rules.
4. Wrong rules: strike through with a note, do not delete.

## Who reads this

- **figure-researcher** — uses these as comment vocabulary when scoring candidate references.
- **fig_critique** — should reference this rubric when judging compiled figures (today uses `critique-evaluation-rubric-v1.md`; reconcile when content stabilizes).
- **You, when drawing manually** — open at the start of each new figure.
- **(future) figure-builder** — reads before generating TikZ.

---

## 1. Dimensions & Layout

- Single column width: **89 mm** [N1].
- Double column width: **183 mm** [N1].
- Full page depth: **170 mm** [N1].
- For prep, fit to PDF page size **210 × 276 mm** [N2].
- Multi-panel figures must be supplied as a **single image file** containing all sub-parts (a, b, c, …) [N2].
- Arrange panels neatly and space-efficiently, minimizing white space; alphabetical order where feasible [N3].
- Avoid disproportionately large panels — size by legibility need [N3].
- Nature Communications: max **10 display items** (figures + tables combined) [N2].

## 2. Labels & Typography

- Font family: **Helvetica or Arial** (sans-serif). Same font throughout all figures in the paper [N1].
- Greek characters / glyphs: **Symbol** font [N3].
- Amino acid sequences: **Courier** (or other monospaced) [N3].
- Panel labels (a, b, c …): **8 pt bold, upright (not italic), lowercase** [N1][N3].
- All other text: **min 5 pt, max 7 pt** [N1][N3].
- Optimum text size when laid out at print size: **8 pt** [N2].
- Embed all fonts as **TrueType 2 or 42** (NOT TrueType 3) [N3].
- Do NOT outline / convert text to paths / rasterize text — must remain editable [N1][N3].

## 3. Color & Palette

- Submit in **RGB**; printer auto-converts to CMYK [N3].
- Avoid red/green color combinations (colorblind accessibility) [N1].
- Use **solid colors**, not patterns, to differentiate elements [N3].
- Do NOT use coloured text in legends — use **coloured boxes + black text** instead [N3].
- Black or white text on backgrounds: maintain **contrast ratio > 4.5** [N3].

## 4. Lines, Arrows & Connections

_(empty — Nature does not specify minimum stroke weight. Fill from work_logs.)_

## 5. Resolution & File Format

### Main figures (Nature)
- Photographic: **min 300 dpi**, recommended max **450 dpi** for online proofs [N1][N3].
- Combination images: **600 dpi** [N1].
- Line art: **1200 dpi** [N1].
- Preferred formats: **.ai, .eps, .pdf** (editable vector) [N3].
- Acceptable: layered .psd, .ppt (convert to .pdf first), .svg, Excel, .ps [N3].
- NOT accepted as main figures: .jpeg, .tiff, .png, Canvas, DeltaGraph, TeX, ChemDraw, SigmaPlot, CorelDraw [N3].
- Max file size: **50 MB** per figure [N3].

### Extended Data figures
- Format: **.jpeg (preferred), .tiff, or .eps only** [N3].
- Color mode: **RGB** (not CMYK) [N3].
- Resolution: **max 300 dpi** [N3].
- File size: **≤ 10 MB** [N3].
- Must fit on single page [N3].

### Nature Communications specifics
- Initial submission may be a single PDF / Word / TeX file up to **30 MB** [N2].
- For publication, supply each figure as an individual high-quality file [N2].

## 6. Scale Bars

- Use **scale bars** rather than magnification factors [N3].
- Keep scale bar and any text on a **separate, editable layer** [N3].

## 7. Captions / Legends

- Nature Communications figure legend limit: **≤ 350 words each** [N2].
- Avoid coloured text in legends — black text only [N3].
- If pseudo-coloring or nonlinear adjustment (e.g. gamma changes) is used, this **must be disclosed** in the legend [N4][N5].
- If juxtaposing images, borders **must be clearly demarcated, labelled, and described in the legend** [N4][N5].

## 8. Image Integrity (Nature Portfolio policy — applies to all submissions)

### Allowed
- Brightness / contrast adjustments — only when applied **equally across the entire image AND equally to controls** [N4][N5].
- Contrast must NOT be adjusted such that data disappears [N4].

### Prohibited
- Cloning / healing tools (Photoshop Spot Healing Brush, Remove Tool, Healing Brush, Patch Tool, Content-Aware Move, Clone Stamp, **Generative Fill**) [N4].
- Eraser tools (Eraser, Background Eraser, Magic Eraser) [N4].
- **Use of any generative AI in figures is not permitted** [N4].
- Adjusting contrast on individual bands of a gel/blot in a way that alters their relative intensity [N4].
- Combining images gathered at different times or from different samples into a single image (unless time-lapse / time-averaged AND clearly demarcated AND described in legend) [N4][N5].
- Image duplication within figures (intentional duplication must be clearly labelled) [N4].

### Gels / Blots specifically
- Provide original **uncropped** raw data for all gels [N4].
- Raw uncropped gels must accurately represent intensity and contrast of bands [N4].
- Vertical splicing of lanes: **must be clearly marked with separation or a line** [N4].
- Avoid horizontal splicing within single panels [N4].

### Enforcement
- Nature Portfolio is **spot-checking images** from randomly chosen papers [N5].

## 9. Anti-patterns (do NOT)

From Nature guidelines:
- Background gridlines [N3].
- Drop shadows, decorative patterns [N3].
- Text on busy backgrounds [N3].
- Overlapping text [N3].
- Coloured text in legends [N3].
- Outlined / non-editable text [N1][N3].
- Patterns instead of solid colors [N3].

_(Lab additions go below as `[lab]`. Empty by default.)_

---

## Sources

- **[N1]** Nature — Formatting guide. https://www.nature.com/nature/for-authors/formatting-guide *(authenticated; specs verified via search summary)*
- **[N2]** Nature Communications — How to submit / Guide to authors. https://www.nature.com/ncomms/submit/how-to-submit · https://www.nature.com/ncomms/submit/guide-to-authors
- **[N3]** Nature Research Figure Guide — Preparing figures & Building/exporting panels. https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/ · https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/
- **[N4]** Nature Research Figure Guide — Image Integrity. https://research-figure-guide.nature.com/figures/image-integrity/
- **[N5]** Nature Portfolio — Editorial policy on Image integrity and standards. https://www.nature.com/nature-portfolio/editorial-policies/image-integrity

Last verified: 2026-05-16

## Related plugin documents

- `critique-evaluation-rubric-v1.md` — fig_critique rubric (overlaps with this guide; reconcile when stable)
- `golden-target-trap-depth-picture.md` — concrete golden-target example
- `briefing-semantic-schema-v1.md` — briefing input format (separate concern)
