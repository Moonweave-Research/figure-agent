# figure-agent — Architecture Overview

**Status**: active reference. Mirrors the layer model used to organize
post-v0.1.7.2 cleanup. For the product-direction rationale behind each layer,
see `docs/quality-kernel-goal.md`. For the canonical fixture acceptance criteria,
see `docs/golden-target-trap-depth-picture.md` and `docs/golden-target-001-retrospective.md`.

## Purpose

`figure-agent` is a **paper-figure quality kernel**. Its value is not "produce
a figure for the user" but "enforce style, compile, export, and reproducibility
invariants on a figure regardless of who or what authored the source." This
document defines the layers the plugin owns, the boundaries it explicitly does
not own, and where each script / command / artifact lives in the flow.

A new contributor should read this once before touching anything beyond a
single fixture; a future contributor should be able to recover the mental
model from this file without rereading the full commit history.

## Layer model

The flow runs top-to-bottom. Each layer has a defined input, output, and
gating responsibility. Layers labeled "frozen" continue to exist for
backwards compatibility but are not the development direction.

```
Layer 0: External Inputs               (user / tool, no plugin code)
   |
   v
Layer 1: Identity / Onboarding         (README, SKILL, plugin.json, CLAUDE/AGENTS)
   |
   v
Layer 2: Authoring Intent              (briefing.md + spec.yaml + golden_contract)
   |
   v
Layer 2.5: Reference Analysis          (planned — Phase E; see end of file)
   |
   v
Layer 3: TikZ Source Authoring         (<name>.tex + polymer-paper-preamble.sty)
   |
   v
Layer 4: Compile Gates                 (compile.sh: lint -> lualatex -> checks)
   |
   v
Layer 5: Export                        (PDF / SVG via dvisvgm / TIFF / PNG)
   |
   v
Layer 6: Validation Gates              (check_golden_artifacts: basic / accepted)
   |
   v
Layer 7: State Inference               (status.py / fig_status)
   |
   v
Layer 8: Reproducibility / Asset       (.gitignore + .gitattributes + LFS policy)

Layer 9: Frozen Orchestration Legacy   (prompt_gen, redact, llm_author_prompt,
                                        review_brief, /fig_prompt,
                                        /fig_preview_select, /fig_review)

Layer 10: Documentation                (docs/ active + docs/historical/)
```

## Layer-by-layer reference

### Layer 0 — External Inputs

**Owner**: user.
**Plugin code**: none.

The plugin is gen-tool-agnostic by design (declared in `plugin.json`,
`SKILL.md`, `CLAUDE.md`, `AGENTS.md`). External inputs include:

- The user's intent, which is captured into `briefing.md` during the
  `/fig_new` interview (Layer 2).
- LLM-generated reference PNGs, saved by hand to `examples/<name>/reference/`
  (golden fixtures) or `examples/<name>/previews/` (frozen workflow).
- External vision-model critique output, when the frozen `/fig_review`
  brief is pasted into a vision LLM and the user revises the `.tex` based
  on the response.

The plugin's contact with Layer 0 is purely positional: it requires inputs
to land at known filesystem paths with known extensions. It never fetches
or generates anything in Layer 0.

### Layer 1 — Identity / Onboarding

**Files**: `README.md`, `CLAUDE.md`, `AGENTS.md`, `.claude-plugin/plugin.json`,
`skills/figure-agent/SKILL.md`, `commands/*.md`.

These are the surfaces that tell a new user (or a new agent session) what
the plugin is. They must agree on:

- The four quality-kernel responsibilities (Style Lock / compile-export /
  Visual QA / reproducibility).
- The active workflow (`/fig_compile` / `/fig_export` / `/fig_status`).
- The frozen workflow (`/fig_prompt` / `/fig_preview_select` / `/fig_review`)
  marked as legacy so users do not mistake them for the development path.
- The boundary statement that the plugin does not call image-gen APIs.

Drift between these surfaces is the most common identity-confusion source;
when adjusting one, adjust all.

### Layer 2 — Authoring Intent

**Files**: `examples/<name>/briefing.md`, `examples/<name>/spec.yaml`.

`briefing.md` is the prose record of intent (what the figure shows, in what
panels, with what physics invariants). It is structured by numbered headings
parsed by `scripts/inputs.parse_briefing`.

`spec.yaml` is a lightweight metadata record of panels, style profile, and
optional fixture-class flags:

- `selected_preview` — frozen-workflow field; chosen image from `previews/`.
- `reference_image` — golden-fixture field; the fixed visual target PNG.
- `accepted` — golden-fixture flag; manuscript-acceptance gate.
- `golden_contract` — golden-fixture spec for `check_golden_artifacts`
  (`required_labels`, `source_inventory`).

Meaning lives in `briefing.md` and `<name>.tex`; `spec.yaml` is metadata
only, never the single source of truth.

### Layer 2.5 — Reference Analysis (planned)

**Status**: not implemented; reserved for Phase E.

This layer will run between Layer 2 and Layer 3. Inputs are the user's
LLM-generated reference PNG (Layer 0) plus `briefing.md` (Layer 2). Outputs
are a per-fixture `coordinate_hints.yaml` containing extracted text-label
positions and shape clusters, used at two downstream times:

- **At Layer 3 authoring time** — supplies precise (x, y, w, h) coordinates
  to the TikZ author so first-pass coordinate accuracy is no longer limited
  by visual estimation.
- **At Layer 6 validation time** — drives reference-vs-build bbox drift
  detection.

Planned components: `scripts/reference_extract.py` (VTracer + OCR +
clustering), `scripts/check_layout_drift.py`, `commands/fig_extract.md`.
Adding this layer is Phase E in the cleanup roadmap.

### Layer 3 — TikZ Source Authoring

**Files**: `examples/<name>/<name>.tex`, `styles/polymer-paper-preamble.sty`,
`styles/tex_template.tex`.

A human or LLM authors the TikZ source. The macro library is shared:

- `\IsoBlock`, `\IsoCharge`, `\GradSlab`, `\IsoConeTip` — isometric block
  primitives (v0.1 flagship).
- `\TrapLevel` — promoted from `golden_trap_depth_picture` to the shared
  preamble in v0.2.
- `\BandBox`, `\SmallLobe` — fixture-local; promotion candidates if a
  second fixture proves reuse.

`lint_tex.py` enforces palette / font / hex / non-palette-color discipline
at BLOCKER tier; `flagship_macros_unused` is WARN-only because non-isometric
fixtures legitimately do not use the iso macros.

### Layer 4 — Compile Gates

**Files**: `scripts/compile.sh`, `scripts/lint_tex.py`,
`scripts/check_collisions.py`, `scripts/check_visual_clash.py`.

Chain (in order):

1. `lint_tex.py` — Style Lock check, BLOCKER tier (compile fails on
   non-palette colors, raw hex, font overrides, definecolor).
2. `lualatex` (or `LATEX_ENGINE` override) — produces `build/<name>.pdf`.
3. `pdftocairo -png -r 600` — produces `build/<name>.png`.
4. `check_collisions.py` — text bbox IoU collisions; report-only by default.
5. `check_visual_clash.py` — render-pixel clash detection (text_on_path,
   text_on_fill, near_miss, clipping); report-only by default.

`FIGURE_AGENT_STRICT=1 bash scripts/compile.sh ...` propagates `--strict`
to the collision and clash checkers, promoting their findings to non-zero
exit. Default mode preserves report-only ergonomics so dogfood iteration
is not interrupted.

### Layer 5 — Export

**Files**: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`.

- PDF — copied or re-emitted from `build/`.
- SVG — `dvisvgm --pdf --font-format=woff2`; preserves top-level
  non-italic non-math text as `<text>` nodes (italic / math / macro-internal
  labels still outline because lualatex with fontspec/Arial embeds them as
  CID fonts that dvisvgm rasterizes — known partial-preservation limit).
- TIFF — `pdftocairo -tiff -r 600 -singlefile`.
- PNG — `rsvg-convert` from the SVG.

`tests/test_export_svg.py` regresses against text-node count and canonical
label survival on the golden fixture.

### Layer 6 — Validation Gates

**Files**: `scripts/check_golden_artifacts.py`,
`tests/test_golden_artifact_checks.py`.

Two modes:

- **basic mode** — artifact-shape only: SVG visible-element floor, PNG
  width floor, opaque-white PNG corners. Always runs.
- **`--require-accepted` mode** — driven by `spec.yaml.golden_contract`:
  requires the contract block, validates `accepted: true`, runs
  `required_labels` against pdftotext output, runs `source_inventory`
  regex counts against `<name>.tex`, asserts `QUALITY_AUDIT.md` freshness,
  and applies collision/clash budget thresholds.

A second golden fixture only needs a `golden_contract` block in its
`spec.yaml`; no script edits.

### Layer 7 — State Inference

**Files**: `scripts/status.py`, `commands/fig_status.md`,
`tests/test_status.py`.

`infer_stage(example_dir)` returns `{stage: 0..6, accepted: True/False/None,
checks, notes, next}` from filesystem + `spec.yaml` only — no side effects.
Stage line includes `(accepted)` or `(not accepted)` marker for fixtures
that declare the `accepted` key. Notes surface stale / missing /
replayability hazards (`stale_export`, `selected_preview_missing`,
`reference_image_missing`, `partial_export`, `previews_not_directory`,
`missing_briefing`).

`status.py` is read-only; it never modifies any file.

### Layer 8 — Reproducibility / Asset

**Files**: repo-root `.gitignore`, `.gitattributes`,
`docs/quality-kernel-goal.md` ("Export Tracking Policy" section).

Per-figure folders use the .gitignore default of treating `build/`,
`exports/`, and `previews/` as untracked. Two fixture classes:

- **Ordinary fixtures** — exports regenerated on demand, not tracked.
- **Golden fixtures** — PDF / SVG / TIFF / PNG exports force-tracked via
  explicit `.gitignore` negation entries; TIFF routes through Git LFS via
  `.gitattributes`. Promoting a fixture to golden requires three changes
  in one commit: spec.yaml (`reference_image:` + `accepted:` keys),
  `.gitignore` negation block, optional `.gitattributes` LFS line.

Detailed rationale and the promotion checklist live in
`docs/quality-kernel-goal.md`.

### Layer 9 — Frozen Orchestration Legacy

**Files**: `scripts/redact.py`, `scripts/prompt_gen.py`,
`scripts/llm_author_prompt.py`, `scripts/review_brief.py`,
`prompts/llm_author_tikz.md`, `commands/fig_prompt.md`,
`commands/fig_preview_select.md`, `commands/fig_review.md`.

Preserved from v0.1 because removing them would break in-flight users.
The slash commands carry `[frozen legacy]` markers in their `description`
metadata and a status block in their body pointing at the active workflow.
Code remains tested (47 functions) so the frozen path does not bit-rot,
but no new orchestration features are added unless dogfooding proves a
durable non-transient need.

### Layer 10 — Documentation

**Files**: `docs/` (active) + `docs/historical/` (frozen).

Active:
- `docs/quality-kernel-goal.md` — product-direction spec.
- `docs/golden-target-trap-depth-picture.md` — Golden Target 001
  acceptance criteria.
- `docs/golden-target-001-retrospective.md` — N=1 evidence retrospective.
- `docs/architecture-overview.md` — this file.

Historical (pinned for context, not maintained):
- `docs/historical/design-v0.1.md`
- `docs/historical/roadmap-v0.1.7-selection-notes.md`
- `docs/historical/superpowers-plan-2026-04-29-golden-target-001.md`

CHANGELOG.md retains references to historical doc paths because they are
historical events; do not rewrite them.

## What lives where (quick lookup)

| You want to... | Look at |
|---|---|
| Understand product direction | `docs/quality-kernel-goal.md` |
| Add a new fixture | `commands/fig_new.md` + `examples/<name>/` |
| Add a new gate to `/fig_compile` | `scripts/compile.sh` + `scripts/check_*.py` |
| Add a per-fixture validation rule | `spec.yaml.golden_contract` (new fixture) or `scripts/check_golden_artifacts.py` (new contract field) |
| Add a flagship macro | `styles/polymer-paper-preamble.sty` + update `lint_tex.py` flagship list |
| Promote a fixture to golden | three changes in one commit: `spec.yaml`, repo-root `.gitignore`, `.gitattributes` |
| Make `/fig_compile` strict in CI | `FIGURE_AGENT_STRICT=1 bash scripts/compile.sh ...` |
| Diagnose a fixture's stage | `uv run python3 scripts/status.py examples/<name>` |
| Replay a golden fixture from clean checkout | `bash scripts/compile.sh examples/<name>/<name>.tex && bash scripts/export_svg.sh ...` |

## Phase E — planned next layer

Layer 2.5 (Reference Analysis) is the next infrastructure layer. It adds
VTracer-based bbox extraction plus OCR text detection on the reference
PNG, producing a per-fixture `coordinate_hints.yaml`. The same engine is
reused at Layer 6 to detect reference-vs-build layout drift.

Phase E is deferred until either a second golden fixture lands or visual
refit on the existing fixture demonstrates real friction; making the layer
ahead of evidence risks over-engineering. When implemented, this document
should be updated to remove the "(planned)" tag from Layer 2.5 and to
add the new files / commands to Layer 6.
