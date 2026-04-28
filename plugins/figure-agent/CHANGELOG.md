# Changelog

All notable changes to figure-agent are documented here.

## [0.1.1] - 2026-04-28

### Fixed

- Print `/fig_prompt` output in copy-friendly order: normalized prompt first,
  then normalization audit, then next steps, all on stdout.
- Drop author-facing bare label headers from generated prompt bullets while
  preserving real content bullets with text after a colon.

### Added

- Add `styles/tex_template.tex`, a single-panel TikZ starter that compiles
  out-of-the-box and uses `polymer-paper-preamble` Style Lock.
- Document the starter copy command in `README.md` and `/fig_preview_select`.
- Add regression tests for prompt output ordering and meta-label filtering.

## [0.1.0] - 2026-04-28

### Added

- Define figure-agent v0.1 as prompt intent control plus human/LLM-authored
  TikZ compile, checks, and export.
- Normalize literal-heavy prompt details while preserving schematic intent and
  domain terms.
- Use `examples/<name>/build/<name>.pdf` as the canonical compile/check/export
  artifact.
- Export PDF, SVG, TIFF, and PNG, with TIFF/PNG raster output at 600 dpi.

### Not In v0.1

- No image-generation API calls.
- No automatic preview-to-vector reconstruction.
- Selected previews are inspiration only; final TikZ remains editable source.
