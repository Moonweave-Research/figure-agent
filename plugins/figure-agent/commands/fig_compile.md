---
description: Compile human/LLM-authored TikZ. Style Lock + clash + (optional) layout drift checks.
---

Compile the final TikZ source.

**Usage**: `/fig_compile <name>`

Run from the user workspace:

`fig-agent compile <name>`

Cowork path preflight:

Do not infer that the installed plugin bundle is missing just because the user
workspace has no `scripts/` or `styles/` directory. `fig-agent` reads bundled
tools/styles from `FIGURE_AGENT_PLUGIN_ROOT` or `CLAUDE_PLUGIN_ROOT`, and reads
figure work from `FIGURE_AGENT_WORKSPACE` or `CLAUDE_PROJECT_DIR`.

Strict opt-in:

`fig-agent compile <name> --strict`

`<name>` maps to `examples/<name>/`.

Check target: `examples/<name>/build/<name>.pdf`

Steps:
1. Verify `examples/<name>/<name>.tex` exists. If missing, instruct the user to author it
   from `briefing.md` (cp `styles/tex_template.tex` to start) before compiling.
2. Pre-compile lint: `scripts/compile.sh` runs `scripts/lint_tex.py` first. BLOCKER-tier
   Style Lock checks (`\definecolor`, `\setmainfont`/`\setsansfont`/`\setmonofont`, raw hex,
   non-palette TikZ colors). On any violation, abort before lualatex; `build/` is untouched.
   WARN-tier lints are report-only and include thin strokes, missing flagship macros,
   filled labels that may be overpainted by later draw/path commands, and short
   double-headed arrows whose tips may fuse at manuscript scale.
   If the last edit was a fixed panel/subregion move, run
   `fig-agent helper tex_coordinate_shift.py examples/<name>/<name>.tex --line START:END --dx <cm> --dy <cm>`
   first and inspect the dry-run diff before applying `--write`.
3. If the fixture declares `spec.yaml.text_boundary_layout`, refresh the
   generated checker contract before compiling:
   `fig-agent text-boundary <name> --write`.
   The helper only rewrites `spec.yaml.text_boundary_checks`; `compile.sh`
   consumes `text_boundary_checks`, not the author-facing layout block.
4. Run `fig-agent compile <name>` (lualatex via shared chain).
5. Run `fig-agent helper check_collisions.py` on `examples/<name>/build/<name>.pdf`.
6. Run `fig-agent helper check_visual_clash.py` and
   `fig-agent helper check_text_boundary_clash.py` on
   `examples/<name>/build/<name>.pdf`.
   - Default mode is report-only: collision/clash findings print WARN output
     and the checker exits 0.
   - Strict mode is opt-in: with `FIGURE_AGENT_STRICT=1`, `compile.sh`
     propagates `--strict` to all checkers and any finding exits non-zero.
   - Golden/ship acceptance is not decided by the edit-loop compile command.
     Fixtures declaring `golden_contract` are gated by
     `fig-agent helper check_golden_artifacts.py --require-accepted`, which enforces
     unresolved collision/clash budgets and rejects `accepted: false`.
7. (Optional) Run `fig-agent helper check_layout_drift.py examples/<name>` —
   only when `examples/<name>/coordinate_hints.yaml` exists. Reports per-label
   drift between the reference PNG OCR positions and the build PDF text
   positions, anchored on `spec.yaml.golden_contract.required_labels`.
   Report-only by default; `--strict` (or `FIGURE_AGENT_STRICT=1`) makes
   matched-but-drifted labels exit non-zero.
8. `scripts/compile.sh` always runs `scripts/perception_pack.py <name>` after
   successful render and checks. It writes:
   - `examples/<name>/build/perception/extract.yaml`
   - `examples/<name>/build/perception/overlay.png`

   This step requires `pdfplumber` and fails hard if the dependency is missing.
   The pack is descriptive only: raw PDF primitives plus endpoint overlay, not
   a topology judgment or automatic critique.
9. Report:
   - Compile success/fail
   - Collision report (count, severity)
   - Visual clash report (WARN list, NOT blocking)
   - Text boundary clash report when `spec.yaml.text_boundary_checks` exists
     (`build/text_boundary_clash.json`, WARN list, NOT blocking)
   - Layout drift report when emitted (per-label drift / uncovered counts,
     aspect-ratio header)
   - Perception pack paths when generated
   After review of compile + clash reports, run `/fig_critique <name>` for the
   host-orchestrated vision critique before exporting.
10. Style Lock: confirm `\usepackage{polymer-paper-preamble}` is loaded in .tex.
   If missing, warn user but do not auto-inject.

Human-gated by default. Reports inform during iteration; do not block on WARN
unless strict mode is explicitly enabled for manuscript/CI or the fixture is
being checked through the accepted-artifact gate.

Lint is a /fig_compile sub-routine; no persistent state, re-runs every compile. Aligned with /fig_status freshness model.

Next: /fig_critique <name> or /fig_export <name> (if WARN > 0, revise <name>.tex and re-run /fig_compile <name>)
