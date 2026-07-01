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
Layer 2.5: Reference Analysis          (OCR + palette clusters + optional vtracer hints)
   |
   v
Layer 3: Semantic TikZ Authoring       (<name>.tex + polymer-paper-preamble.sty)
   |
   v
Layer 3.5: Theory Guard                (authoring/acceptance review; not compile)
   |
   v
Layer 4: Compile Gates                 (compile.sh: lint -> lualatex -> checks)
   |
   v
Layer 5: Export                        (PDF / SVG via dvisvgm / TIFF / PNG)
   |
   v
Layer 5.5: Final Artifact              (polished-SVG contract;
                                        optional, opt-in, no hidden SVG editor)
   |
   v
Layer 6: Validation Gates              (check_golden_artifacts: basic / accepted)
   |
   v
Layer 7: State Inference               (status.py / fig_status)
   |
   v
Layer 7.5: Driver / Operator Routing    (fig_drive / fig_run / fig_queue;
                                        bounded execution + explicit handoffs)
   |
   v
Layer 8: Reproducibility / Asset       (.gitignore + .gitattributes + LFS policy)

Layer 4.5: Vision Critique             (host Claude reads build PNG via Read tool;
                                        critique_brief.py + /fig_critique;
                                        report-only, no external API)

Layer 9: Frozen Orchestration Legacy   (deleted in v0.2: prompt_gen, redact,
                                        llm_author_prompt, /fig_prompt,
                                        /fig_preview_select; review_brief →
                                        critique_brief, fig_review → fig_critique)

Layer 10: Documentation                (docs/ active + docs/historical/)
```

## Layer-by-layer reference

### Layer 0 — External Inputs

**Owner**: user.
**Plugin code**: none.

The plugin is gen-tool-agnostic by design (declared in `plugin.json`,
`SKILL.md`, and `AGENTS.md`). External inputs include:

- The user's intent, which is captured into `briefing.md` during the
  `/fig_new` interview (Layer 2).
- LLM-generated reference PNGs, saved by hand to `examples/<name>/reference/`
  (golden fixtures) or `examples/<name>/previews/` (informal storage).
- L4.5 critique findings, written by the host Claude Code main loop into
  `examples/<name>/critique.md` after `/fig_critique <name>`. The user
  or an outer agent records decisions in `critique_adjudication.yaml`, then
  uses verify-only `/fig_loop` and `/fig_drive` to choose the next bounded
  action.

The plugin's contact with Layer 0 is purely positional: it requires inputs
to land at known filesystem paths with known extensions. It never fetches
or generates anything in Layer 0.

### Layer 1 — Identity / Onboarding

**Files**: `README.md`, `AGENTS.md`, `.claude-plugin/plugin.json`,
`skills/figure-agent/SKILL.md`, `commands/*.md`.

These are the surfaces that tell a new user (or a new agent session) what
the plugin is. They must agree on:

- The four quality-kernel responsibilities (Style Lock / compile-export /
  Visual QA / reproducibility) plus L4.5 vision critique.
- The active workflow (`/fig_compile` / `/fig_critique` / `/fig_export` /
  `/fig_status`).
- The operator workflow (`/fig_drive` for one fixture, `/fig_run` for bounded
  mechanical single-fixture execution, `/fig_queue` and `/fig_queue_run` for
  multi-fixture triage).
- The boundary statement that the plugin does not call **external**
  image-gen or vision APIs; L4.5 vision critique is delegated to the
  host Claude Code main loop, not an external HTTP call.

Drift between these surfaces is the most common identity-confusion source;
when adjusting one, adjust all.

### Layer 2 — Authoring Intent

**Files**: `examples/<name>/briefing.md`, `examples/<name>/spec.yaml`.

`briefing.md` is the prose record of intent (what the figure shows, in what
panels, with what physics invariants). It is structured by numbered headings
parsed by `scripts/inputs.parse_briefing`.

`spec.yaml` is a lightweight metadata record of panels, style profile, and
optional fixture-class flags:

- `reference_image` — golden-fixture field; the fixed visual target PNG.
- `accepted` — golden-fixture flag; manuscript-acceptance gate.
- `golden_contract` — golden-fixture spec for `check_golden_artifacts`
  (`required_labels`, `source_inventory`).

Meaning lives in `briefing.md` and `<name>.tex`; `spec.yaml` is metadata
only, never the single source of truth.

### Layer 2.5 — Reference Analysis

**Files**: `scripts/reference_extract.py`, `commands/fig_extract.md`,
`tests/test_reference_extract.py`, `examples/<name>/coordinate_hints.yaml`.

This layer runs between Layer 2 (Authoring Intent) and Layer 3 (Semantic
TikZ Authoring). The active workflow is:

```
reference PNG -> OCR + palette clusters + optional vtracer structural hints
-> coordinate_hints.yaml -> semantic TikZ authoring
```

`coordinate_hints.yaml` is an authoring-evidence file, not generated final
source. It can contain:

- `text_labels[]` — OCR-detected labels with pixel bounding boxes and
  confidence scores.
- `palette_shape_clusters{}` — connected components matching the Style Lock
  palette colors.
- `structural_regions{}` — optional vtracer-derived regions such as panel
  arcs, border boxes, chain rows, atom positions, trap levels, plot boxes,
  plot curves, and lobe-like regions.

`structural_regions.status` may be `ok`, `unavailable`, or `failed`.
Unavailable vtracer does not invalidate the workflow: OCR + palette clusters
still remain useful authoring hints, and Layer 3 must continue from the
available evidence.

Layer 2.5 must not be treated as an SVG-to-TikZ conversion layer. VTracer and
SVG-derived paths are allowed only as evidence for approximate placement,
color grouping, and coarse geometry. SVG-to-TikZ path conversion is not the active workflow because it produces
low-level path code without the semantic macro structure needed for manuscript
editing.

### Layer 3 — Semantic TikZ Authoring

**Files**: `examples/<name>/<name>.tex`, `styles/polymer-paper-preamble.sty`,
`styles/tex_template.tex`.

A human or LLM authors semantic TikZ source from `briefing.md`, `spec.yaml`,
the reference PNG, and any available `coordinate_hints.yaml`. The output is a
maintainable `.tex` file built from named macros, scoped styles, and readable
TikZ constructs. Raw SVG path dumps, auto-traced path clouds, and direct
SVG-to-TikZ conversion are not acceptable as the final source for the active
workflow.

Use coordinate hints as placement evidence:

- OCR labels guide text content and label positions.
- Palette clusters guide color family and coarse shape placement.
- Optional vtracer structural hints guide panel boxes, chain rows, trap
  levels, and major geometry.

The authoring target is semantic reconstruction, not pixel-for-pixel path
transcription.

The macro library is shared and should be preferred when it matches the figure
semantics. `lint_tex.py` enforces palette / font / hex / non-palette-color
discipline at BLOCKER tier; `flagship_macros_unused` is WARN-only because some
fixtures legitimately do not use the flagship macros.

Three flagship macros currently follow the style-decoupled/safe-authoring
pattern: `\BellCurve` (primitive single-key, PR #1), `\BandDiagram` (composite
single-key α path, this pilot), and `\PlotCallout` (annotation-safety primitive
for plot labels). Per-sub-element fan-out (β) for composite macros remains an
open question; see
`docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md`
§"Out of scope". Per-macro reference docs:
`docs/macros/bell-curve.md`, `docs/macros/band-diagram.md`,
`docs/macros/plot-callout.md`.

### Layer 3.7 — Composition (structural-block rewrite)

**Files**: `scripts/composition_families.py`,
`scripts/composition_family_templates.py`, `scripts/composition_apply.py`,
`scripts/composition_cli.py`, `scripts/composition_post_apply_verify.py`.

This layer is a per-figure premium scaffold for hand-authored scene rewrites,
distinct from the bounded candidate/apply nudge path. Where candidate/apply
emits small offset patches, composition emits whole structural-block rewrites:
each family variant is a `replace_semantic_block` op that swaps a
marker-delimited TikZ region for a premium hand-authored alternative scene.

It does not generalize across figures yet. `FAMILY_DATA` in
`composition_family_templates.py` is hardcoded to the
`fig3_resistance_mechanism` scene objects `carrier_walk`,
`current_sparkline`, and `n_breadth`; `compose-generate-families` on any other
fixture (e.g. fig2) fails with `selector_missing` because no marker block
matches. This is a single-fixture-bound premium scaffold, **not** a reusable
component bank.

Every generated op is stamped `apply_authority: 'human_required'`, so the
composition path never auto-applies a scene rewrite. The flow is wired through
the `bin/fig-agent compose-*` subcommands (`compose-capture`,
`compose-generate-families`, `compose-render`, `compose-rank`,
`compose-review`, `compose-apply-ready`, `compose-accept`, ...), with
`composition_post_apply_verify.py` checking the rewrite after a human applies
it.

### Layer 3.5 — Theory Guard

**Files**: optional `examples/<name>/authoring_contract.md`,
`examples/<name>/reference/reference_pack.md`,
`examples/<name>/authoring_plan.md`, `examples/<name>/theory_guard.md`,
`examples/<name>/subregion_iteration_log.md`, `scripts/subregion_active_set.py`,
`scripts/reference_pack.py`.

This layer sits between semantic authoring and compile/export acceptance. It is
not a lualatex, collision, or visual-clash gate. Its job is to record the
scientific invariants that the rendered figure must not violate: topology,
mechanistic causality, color/label semantics, and publication-policy risks that
compile artifacts cannot prove.

For reference-conditioned pilots, `theory_guard.md` lists BLOCKER and MAJOR
claims with check methods and evidence. Any BLOCKER failure keeps the figure at
`accepted: false`. `accepted: true` requires a passing theory guard plus visual,
export, critique, provenance, and publication-compliance evidence. The theory
guard may block acceptance, but it does not replace Layer 4 compile gates or
Layer 6 artifact validation.

When `subregion_iteration_log.md` exists, `scripts/subregion_active_set.py`
parses the Markdown Active Target Set and Iteration Log tables so `/fig_critique`
can focus the host review on currently active sub-regions.
`scripts/subregion_iteration_log.py` can scaffold the canonical log and append
one iteration row after each patch. This remains text-form evidence plumbing
only; it is not a sub-region schema, bbox cropper, or auto-segmentation layer.

When `reference/reference_pack.md` exists, `scripts/reference_pack.py` parses the
Reference Roles table so accepted-mode validation can require role and
Do-Not-Transfer boundaries for every reference row. The parser does not decide
scientific truth; it only prevents boundary-free references from passing as
publication-ready evidence.

### Layer 4 — Compile Gates

**Files**: `scripts/compile.sh`, `scripts/lint_tex.py`,
`scripts/checks/check_collisions.py`, `scripts/checks/check_visual_clash.py`.

Chain (in order):

1. `lint_tex.py` — Style Lock check, BLOCKER tier (compile fails on
   non-palette colors, raw hex, font overrides, definecolor).
2. `lualatex` (or `LATEX_ENGINE` override) — produces `build/<name>.pdf`.
3. `pdftocairo -png -r 600` — produces `build/<name>.png`.
4. `check_collisions.py` — text bbox IoU collisions; report-only by default.
5. `check_visual_clash.py` — render-pixel clash detection (text_on_path,
   text_on_fill, near_miss, clipping); report-only by default.

`FIGURE_AGENT_STRICT=1 bash scripts/compile.sh ...` propagates `--strict`
to the collision and clash checkers, promoting their findings to
non-zero exit. Default mode preserves report-only ergonomics so dogfood
iteration is not interrupted and a reviewable PNG/PDF is still emitted.
Golden/ship decisions are made at Layer 6: fixtures with `golden_contract`
must pass `check_golden_artifacts.py --require-accepted`, including the
accepted flag and unresolved collision/clash budgets.

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

#### Export staleness contract (Layer 5)

`/fig_export` reads the `examples/<name>/exports/` sub-state — `MISSING`, `TRACKED_GOLDEN`, `STALE`, or `FRESH` — and dispatches:

- `MISSING` / `STALE` → regenerate PDF / SVG / TIFF / PNG from the current `build/<name>.pdf`.
- `FRESH` → no-op.
- `TRACKED_GOLDEN` → skip with warning. Use `--force-golden` to override (rare; intended for intentionally rolling forward the reference snapshot).

Sub-state is computed via content hash of the metadata-stripped qpdf-expansion (see `scripts/diff_pdf_content.py`'s `strip_metadata`). mtime is **not** used: it would be fragile to `git checkout`, `cp`, and `tar -x`.

Two contract layers guard the invariants:

- **Layer A (always on):** after `/fig_export` succeeds on a non-golden fixture, `build/<name>.pdf` and `exports/<name>.pdf` must hash-equal. Tested by `tests/test_export_freshness.py::test_freshness_invariant_after_run_export`.
- **Layer B (opt-in per-fixture):** fixtures declaring `export_pipeline_equivalence: { ae_max: <float> }` in `spec.yaml` are subject to a `magick compare`-based pixel equivalence assertion between `build/<name>.png` (pdftocairo direct) and `exports/<name>.png` (dvisvgm + rsvg-convert). Defaults to `fuzz_pct: 5`. Tested by `tests/test_export_pipeline_equivalence.py`.

Adding a new fixture to Layer B: edit its `spec.yaml`, set `ae_max` based on a measured baseline (run the test once, observe the printed AE fraction, add ~30% margin).

### Layer 5.5 — Final Artifact Contract

**Status**: implemented opt-in handoff contract. Manifest schema, `/fig_status`
state, accepted-gate validation, verify-only `/fig_loop` surfacing,
`/fig_drive --mode polish` routing, `scripts/svg_polish/svg_polish_recipe.py`,
`scripts/svg_polish/svg_polish_delta.py`, and
final-artifact blocking are live. The inert automated half — `svg_polish_executor.py`,
`svg_polish_handoff.py`, the positive harness, `add_volume_shading.py`, and the
synthetic `_volume_shading_demo` fixture — was deleted on 2026-07-02. The plugin
still does not invent hidden SVG geometry edits; a human or outer agent authors
the already-polished SVG plus its audit and manifest files directly.

**Vacuity caveat (quarantined)**: the remaining SVG-polish recipe/delta/semantic-diff/
ship-gate machinery is inert on real figures — only the synthetic `_volume_shading_demo`
fixture ever fired (deleted with the executor), because `dvisvgm` emits zero geometry IDs
for real TikZ exports, so there is no addressable geometry for these ops to mutate. The
covering tests are tagged `@pytest.mark.quarantine` so their green count does not imply
a live guarantee on real figures.

**Design**:
`docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`.

Layer 5 exports reproducible generated artifacts. Layer 5.5 is the place for
declaring a final manuscript artifact when the generated SVG needs
manual or outer-agent polish that is not realistic to finish in raw TikZ.

The contract is intentionally narrow:

- TikZ remains the semantic source of truth.
- `/fig_export` must continue to generate `exports/<name>.svg` and must not
  overwrite `polish/<name>.polished.svg`.
- Polished SVG is release-relevant only when `spec.yaml` explicitly opts in:

```yaml
final_artifact:
  kind: polished_svg
  manifest: polish/svg_polish_manifest.yaml
```

- `polish/svg_polish_manifest.yaml` records generated-export hashes, a
  repo-relative source-set hash, critique hash, polished SVG hash, audit hash,
  edit class, toolchain, semantic-change declaration, and reviewer provenance.
- SVG-only edits are limited to optical presentation changes such as label
  nudges, stroke polish, spacing balance, and icon cleanup that preserves
  scientific meaning.
- Any change to component identity, label meaning, mechanism arrows,
  material semantics, panel role, storyline, or reference interpretation must
  be backported to TikZ, briefing, or spec and rerun through compile/export,
  critique, adjudication, and final-artifact validation.
- `/fig_status` reports `final_artifact_state`, `final_artifact_kind`, and
  `final_artifact_path`. Polished artifacts can be `MISSING`, `INVALID`,
  `STALE`, `BLOCKED`, or `FRESH`.
- In accepted mode, `scripts/checks/check_golden_artifacts.py` requires a fresh,
  provenance-backed polished SVG only for fixtures that explicitly opt in.
- `/fig_loop` remains verify-only. It blocks completion when status reports
  `workflow_ready=true` but `final_ready=false`, and it surfaces the current
  final-artifact state in its decision output.
- `polish/svg_polish_audit.md` and `polish/svg_polish_manifest.yaml` are written
  directly by the human or outer agent after creating `polish/<name>.polished.svg`
  (the `svg_polish_handoff.py` scaffolding helper was deleted on 2026-07-02).

### Layer 6 — Validation Gates

**Files**: `scripts/checks/check_golden_artifacts.py`,
`tests/test_golden_artifact_checks.py`.

Two `check_golden_artifacts` modes:

- **basic mode** — artifact-shape only: SVG visible-element floor, PNG
  width floor, opaque-white PNG corners. Always runs. Malformed `spec.yaml`
  still fails before mode-specific checks because the gate cannot safely decide
  accepted/final-artifact policy from an invalid spec.
- **`--require-accepted` mode** — driven by `spec.yaml.golden_contract`:
  requires the contract block, validates `accepted: true`, runs
  `required_labels` against pdftotext output, runs `source_inventory`
  regex counts against `<name>.tex`, asserts `QUALITY_AUDIT.md` freshness,
  requires a passing `theory_guard.md` BLOCKER table, requires
  `QUALITY_AUDIT.md` to contain provenance/publication-compliance evidence
  with `submission-safe: true`, requires `disclosure-needed` for polished-SVG
  final artifacts, validates `reference/reference_pack.md` when
  reference inputs are declared, and applies collision/clash budget thresholds.
  This is the hard gate for ship-blessed fixtures; it is intentionally
  stricter than the Layer 4 compile loop.

If `--require-accepted` / `--no-require-accepted` is omitted, the checker
auto-escalates to accepted mode whenever `spec.yaml` declares the `accepted`
key, whether true or false. `--no-require-accepted` is only for ad-hoc artifact
inspection.

A second golden fixture only needs a `golden_contract` block in its
`spec.yaml`; no script edits.

### Layer 7 — State Inference

**Files**: `scripts/status.py`, `commands/fig_status.md`,
`tests/test_status.py`.

`infer_stage(example_dir)` returns `{stage: 0..4, accepted: True/False/None,
checks, notes, next, final_artifact_state, final_artifact_kind,
final_artifact_path, workflow_ready, golden_ready, release_ready, final_ready}`
from filesystem + `spec.yaml` only — no side effects. Stage line includes
`(accepted)` or `(not accepted)` marker for fixtures that declare the
`accepted` key. Notes surface stale / missing / replayability hazards
(`stale_export`, `reference_image_missing`, `partial_export`,
`previews_not_directory`, `missing_briefing`, `spec_parse_error`, and
`final_artifact_*`).

`workflow_ready` means the local render/critique/export loop is closed.
`golden_ready` additionally requires `accepted: true`. `release_ready` requires
a content-fresh export state and, for polished-SVG fixtures, a fresh
final-artifact manifest with no semantic-backport blocker. `final_ready` is kept
as a compatibility alias for `release_ready`.

`status.py` is read-only; it never modifies any file.

### Layer 7.5 — Driver / Operator Routing

**Files**: `scripts/fig_driver.py`, `scripts/fig_run.py`,
`scripts/fig_improve.py`,
`scripts/fig_queue.py`, `scripts/fig_queue_run.py`,
`scripts/fig_closeout.py`, `commands/fig_drive.md`, `commands/fig_run.md`,
`commands/fig_improve.md`,
`commands/fig_queue.md`, `commands/fig_queue_run.md`,
`commands/fig_closeout.md`.

This layer turns read-only state into an operator-grade next action without
making high-judgment decisions automatic.

`/fig_drive` is the single-fixture recommender. It reads live status and
closeout/loop evidence, emits one action, and never mutates fixture files.

`/fig_run` is the bounded single-fixture executor. It delegates action
selection to `/fig_drive`, executes only allowlisted deterministic shell work,
then re-queries the driver. It may run compile, initial adjudication scaffold,
verify-only loop checkpoints, and safe non-golden draft export. It stops at
host-vision critique, existing adjudication repair, source patch, SVG polish,
human, accepted, tracked-golden, force-golden, and release boundaries.

`/fig_improve` is the loop-centered single-fixture entry point for "keep
improving this figure" requests. It wraps `/fig_run`, summarizes the final
actor boundary, exposes optional ready-improvement candidates, and requires the
operator to rerun it after host/human/patch/SVG/release work is completed.

`/fig_queue` is the multi-fixture operator dashboard. It scans fixtures through
`/fig_drive`, groups work by actor/action/blocker, and adds blocked-row
`operator_handoff` packets. `/fig_queue_run` is plan-only by default and
delegates only the workflow-agent executable subset to `/fig_run`; it does not
execute host, human, release, SVG, patch, or closeout rows directly.

Run journals under `.scratch/fig-run-runs/` and loop journals under
`.scratch/fig-loop-runs/` are non-authoritative evidence. They explain what
happened, but they are never replay commands; operators must rerun live
`/fig_status` or `/fig_drive` before continuing.

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

### Layer 4.5 — Vision Critique (host-orchestrated)

**Files**: `scripts/critique_brief.py`, `commands/fig_critique.md`,
`tests/test_critique_brief.py`, `examples/<name>/critique.md` (output).

`/fig_critique <name>` runs the brief generator (severity/category rubric,
freshness check, line-numbered TikZ source), then the host Claude Code
main loop reads `examples/<name>/build/<name>.png` via the Read tool and
writes structured findings to `examples/<name>/critique.md` (YAML
front-matter + Markdown body, schema v1). No external API call originates
from plugin code; the host operates on subscription tokens.

The critique file is generated by the host, but the plugin never auto-edits
`<name>.tex`. Findings are adjudicated through `critique_adjudication.yaml`;
verify-only `/fig_loop` records the current state, and `/fig_drive` may
recommend exactly one next command or stop boundary without mutating source,
exports, accepted state, or golden state.

### Layer 9 — Frozen Orchestration Legacy (deleted in v0.2 cleanup)

All v0.1 frozen helpers are now removed or transformed. PR #8a deleted
`scripts/{redact,prompt_gen,llm_author_prompt}.py`, `commands/fig_prompt.md`,
`commands/fig_preview_select.md`, `prompts/llm_author_tikz.md`, the
prompt-template / redaction / selection-notes pipeline, and the
`spec.yaml.selection_notes` consumer. PR #8b dropped the
`spec.yaml.selected_preview` stage gate from `status.py`. PR #9 renamed
the surviving `review_brief.py` / `fig_review.md` to
`critique_brief.py` / `fig_critique.md` and rewired them as Layer 4.5
(see above). Existing fixture spec.yaml files keep the
`selection_notes` and `selected_preview` fields as a historical record
(yaml ignores unknown keys for surviving consumers).

See `docs/architecture-v0.2-proposal.md` for the full layer redesign.

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
| Add a per-fixture validation rule | `spec.yaml.golden_contract` (new fixture) or `scripts/checks/check_golden_artifacts.py` (new contract field) |
| Add a flagship macro | `styles/polymer-paper-preamble.sty` + update `lint_tex.py` flagship list |
| Promote a fixture to golden | three changes in one commit: `spec.yaml`, repo-root `.gitignore`, `.gitattributes` |
| Make `/fig_compile` strict in CI | `FIGURE_AGENT_STRICT=1 bash scripts/compile.sh ...` |
| Generate coordinate hints from a reference PNG | `/fig_extract <name>` → `examples/<name>/coordinate_hints.yaml` |
| Tune palette detection for a noisy reference | `--min-component-pixels` flag on `scripts/reference_extract.py` |
| Diagnose a fixture's stage | `uv run python3 scripts/status.py examples/<name>` |
| Replay a golden fixture from clean checkout | `bash scripts/compile.sh examples/<name>/<name>.tex && bash scripts/export_svg.sh ...` |

## Roadmap notes

**Phase F (open).** Per-color threshold overrides exposed via a fixture's
`spec.yaml`, so a fixture whose LLM render has unusually desaturated palette
colors can loosen the per-call detection without editing
`reference_extract.py`. Currently the script accepts a single
`--min-component-pixels` flag; finer per-color tuning is a future enhancement
gated on real dogfooding evidence.
