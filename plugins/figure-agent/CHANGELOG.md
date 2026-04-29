# Changelog

All notable changes to figure-agent are documented here.

## [Unreleased]

### Added

- /fig_status <name> — read-only stage inference from filesystem + spec.yaml; prints stage N/6 + Next: hint. No arg = summary of all examples.

### Fixed

- `/fig_status` freshness source set now matches `/fig_review`: `<name>.tex`, `briefing.md`,
  and `styles/polymer-paper-preamble.sty`. Editing the briefing or style lock no longer leaves
  the build pdf or exports falsely reported as fresh.
- `/fig_status` adds a `stale_export` note when any source is newer than an export artifact;
  the `Next:` hint becomes "re-run /fig_compile then /fig_export" instead of "done" so the
  primary action agrees with the diagnostic.
- `/fig_status` adds a `selected_preview_missing` note when `spec.yaml` names a preview that
  is not present in `previews/`.
- `/fig_status` no longer crashes when `examples/<name>/previews` exists as a file rather
  than a directory; reports stage 1 with a `previews_not_directory` note.

### Changed

- All six command docs now end with a single-line Next: footer for consistent affordance.
- `prompt_gen.py` module docstring updated to reflect post-input-extraction responsibility
  (prompt composition and normalization via `inputs` + `redact`, not parsing).
- `SKILL.md` trimmed (145→84 lines) by removing command-level details kept in `commands/*.md`
  ("What the prompt must contain", "What the compile must guarantee") and historical rationale
  (design context documented in `docs/design-v0.1.md`).

Runtime-output Next: footer in command scripts deferred to v0.2 (touches 6 scripts).

### Deprecated

- `prompt_gen` re-exports of `parse_briefing` and `parse_spec` (backwards-compat shim for 0.1.x)
  will be removed in v0.2. Migration: when importing from `scripts/`, use `from inputs import parse_briefing, parse_spec`.
  (v0.2 will make `scripts/` a proper package with package-relative imports.)
- `redact.py` module will be renamed to `normalize.py` in v0.2; the function name and
  behavior do not change.

## [0.1.5] - 2026-04-28

### Fixed

- Force white background in PNG raster export so figures without explicit
  panel-background fills render correctly in PNG viewers that treat transparency
  as black.

## [0.1.4] - 2026-04-28

### Fixed

- Preserve negated forbidden prompt lines such as `not allowed`, keep in-section
  blockquotes, and warn when literal details are kept inside physics invariants.
- Make `/fig_review` use repo-relative render paths, reject stale renders, and
  include line-numbered TikZ source for critic citations.
- Align design docs, release-gate docs, and local package metadata with shipped
  `/fig_review` behavior.

## [0.1.3] - 2026-04-28

### Added

- Add `/fig_review`, a halt-stage slash command that emits a self-contained
  Reviewer brief for external physics and aesthetic critique.

### Changed

- Update the documented workflow to include `/fig_review` between compile and export.

## [0.1.2] - 2026-04-28

### Added

- Surface `briefing.md` §6 Physics invariants near the top of generated prompts
  and preserve them verbatim so conceptual constraints remain hard constraints.
- Report literal details inside §6 as kept physics-invariant audit items.
- Document `/fig_review` as a v0.2 Claude-assisted critique direction.

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
