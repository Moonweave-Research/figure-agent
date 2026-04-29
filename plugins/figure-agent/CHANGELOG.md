# Changelog

All notable changes to figure-agent are documented here.

## [0.1.7.1] - 2026-04-29

Hardening release driven by the 4-agent mid-review of v0.1.7 before its
first remote push. Findings: non-string YAML scalars crashed the strip
with TypeError, all-HTML-comment input silently fell back without a
warning, the fallback string was prose an LLM might mis-read, and the
priority-order paragraph was placed after the user-supplied content.

### Fixed

- `scripts/llm_author_prompt.py` `_coerce_selection_notes` helper:
  warns to stderr (naming the example dir and encountered type) and
  coerces to str when `selection_notes` is non-string (int, list, dict,
  bare YAML date such as `2026-04-29`). Prevents TypeError from
  `_HTML_COMMENT.sub` reaching the user as an unhelpful traceback.
- `scripts/llm_author_prompt.py`: warn to stderr when `selection_notes`
  is non-empty before HTML-comment stripping but reduces to empty
  afterward — surfaces the silent-content-loss case the original
  v0.1.7 risk register anticipated.
- `scripts/llm_author_prompt.py`: shorten the missing-key fallback from
  the prose `"(none — only preview filename selected)"` to `"(none)"`
  for parity with the existing `selected_preview` fallback and the
  briefing `_section_body` `(empty)` sentinel.

### Changed

- `prompts/llm_author_tikz.md`: priority-order paragraph is now placed
  **before** the `{{selection_notes}}` placeholder so the LLM absorbs the
  precedence rule before reading user content.
- `prompts/llm_author_tikz.md`: priority paragraph extended to cover the
  extension pattern (selection notes adding visual detail consistent
  with §6) — the dogfood `fig3_trap_schematic_v97/spec.yaml` shows this
  is the real common pattern, not contradiction.

### Tests

- Three regression tests in `tests/test_llm_author_prompt.py`:
  `test_selection_notes_non_string_warns_and_coerces`,
  `test_selection_notes_empty_after_html_strip_warns_and_falls_back`,
  `test_priority_order_paragraph_present_in_output`.
- Updated existing absent-case test to lock the new structural
  relationship (priority paragraph immediately followed by the
  substituted placeholder).

108 pytest pass (105 → 108), ruff clean.

## [0.1.7] - 2026-04-29

### Added

- `prompts/llm_author_tikz.md` `### Selection notes` section with
  preview-grounded authoring guide. Priority order text directs the LLM
  to honor `briefing.md` §6 invariants over selection notes when they
  conflict (`§6 invariants > §3 composition intent > selection notes`).
- `commands/fig_preview_select.md` step 6: recommended 4-heading
  template for `selection_notes` (Visual motifs to preserve / Preview
  errors to fix in TikZ / Labels to lift / Style overrides). Free-form
  remains accepted; HTML-comment author-only notes are stripped.
- `commands/fig_new.md` scaffolds `spec.yaml` with an empty
  `selection_notes: ""` key so new examples have the field present.
- `docs/design-v0.1.md` per-figure folder contract lists
  `selection_notes` as a recognized `spec.yaml` key.
- `docs/roadmap-v0.1.7-selection-notes.md` records the audit-driven
  rationale for plumbing this orphan field instead of adding a
  `/fig_decompose` slash command, and defines the v0.1.x empirical
  validation window plus three trigger-based v0.2 branches.
- `tests/test_llm_author_prompt.py` four new tests covering plumbing,
  HTML-comment stripping (parity with `parse_briefing`), missing-key
  fallback, and backslash preservation through `str.replace`.
- `examples/fig3_trap_schematic_v97/` activated as a tracked dogfood
  fixture demonstrating the 4-heading `selection_notes` convention end
  to end.

### Changed

- `scripts/llm_author_prompt.py` reads `spec.yaml.selection_notes`,
  strips HTML comments using `inputs._HTML_COMMENT` (parity with the
  briefing parser), and substitutes the result into `{{selection_notes}}`
  with a fallback string when the field is missing or whitespace-only.
  Until v0.1.7 the field was declared in `spec.yaml`, parsed by
  `parse_spec`, and never read by any production script — users who
  wrote preview-grounded element-inventory content into it (see
  `examples/fig3_trap_schematic_v97/spec.yaml`) had no way for it to
  reach the LLM authoring prompt.

## [0.1.6] - 2026-04-29

### Added

- `scripts/lint_tex.py` — BLOCKER-tier Style Lock check (`\definecolor`, font override, raw hex,
  non-palette TikZ colors). Integrated into /fig_compile as pre-compile gate: lualatex only runs
  if lint passes; `build/` untouched on lint failure.
- /fig_status <name> — read-only stage inference from filesystem + spec.yaml; prints stage N/6 + Next: hint. No arg = summary of all examples.
- `lint_tex.py` WARN tier: `flagship_macros_unused` (fires once per file when no flagship macro is called) and `thin_stroke` (fires per occurrence when `line width` < 0.25pt). WARN-only exits 0; only BLOCKERs exit 1.
- `prompts/llm_author_tikz.md` — parameterised template for generating a
  filled LLM TikZ authoring prompt from a figure-agent example. §3 is the
  single source of the scaffolding contract; the LLM emits a complete
  standalone `.tex` (`compile.sh` runs `lualatex` on the file directly with
  no wrapper).
- `scripts/llm_author_prompt.py` — CLI and `build_prompt()` helper that
  fills `llm_author_tikz.md` with spec, briefing, palette, and flagship
  macro signatures parsed from preamble comments of the form
  `% \Name{args}: description` (single source of truth for arg semantics,
  no hardcoded signature drift).
- `styles/polymer-paper-preamble.sty` — `% \IsoBlock{w}{d}{h}{color}{hook}`
  signature comment so all four flagship macros expose a structured
  signature line for `llm_author_prompt.py` to read.

### Fixed

- `lint_tex.py` plugged three Style Lock bypasses caught by external review:
  (1) implicit positional colors in TikZ option blocks (`\node[red] {};`,
  `\draw[thick, blue]`) are now rejected via a hardcoded
  `KNOWN_NON_PALETTE_COLORS` set scanned inside `\[...\]` blocks;
  (2) brace-enclosed values (`\node[fill={red}]`) are now matched by an
  optional `\{?...\}?` in the key-value regex; (3) `strip_tex_comment` now
  consumes both characters on every backslash escape so `\\%` (LaTeX newline
  followed by a real comment) correctly truncates and no longer false-flags
  commented-out diagnostics.
- `lint_tex.py` `parse_palette` returns an empty set when
  `polymer-paper-preamble.sty` is missing instead of raising; the CLI now
  exits with code 2 and a clear stderr message in that case (distinct from
  exit 1 for actual lint violations).
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
- `Violation` NamedTuple gains `severity` field (`"blocker"` | `"warn"`); all existing violations set `severity="blocker"`.
- Dogfood regression tests refactored to filter on `severity="blocker"` and positively assert `flagship_macros_unused` WARN exists.
- `/fig_preview_select` Next: footer now points at `llm_author_prompt.py` as the authoring entry point.

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
