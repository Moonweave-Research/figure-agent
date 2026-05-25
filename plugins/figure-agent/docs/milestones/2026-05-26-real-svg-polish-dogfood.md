# Issue 47 - Real Fixture SVG Polish Dogfood

**Status:** blocked on host critique refresh
**Branch:** `codex/issue47-real-svg-polish-dogfood`
**Date:** 2026-05-26
**Candidate fixture:** `fig1_overview_v2_pair_001_vault`

## Why This Fixture

`fig1_overview_v2_pair_001_vault` is the only current real fixture with
`aesthetic_intent.yaml` explicitly routing `svg_micro_polish` to
`ready_for_svg_polish`. That makes it the best real candidate after Issue 46's
temporary clean fixture proof.

## Preflight Commands

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
```

Initial result:

- `render_state: STALE`
- `critique_state: STALE`
- first blocker: render stale
- driver next action: compile

```bash
bash scripts/compile.sh examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
```

Result:

- compile succeeded;
- no PDF text collisions;
- no text-boundary clashes;
- `build/visual_clash.json` regenerated;
- visual clash total: `45`.

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
```

Post-compile result:

- `render_state: FRESH`
- `critique_state: STALE`
- `export_state: TRACKED_GOLDEN`
- `final_artifact_kind: generated_export`
- `final_artifact_state: NONE`
- audit evidence: needs action because `crop_audit_log` is missing required
  crop ids in the current stale critique.

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode polish --goal "issue47 real svg polish dogfood" --dry-run
```

Result:

- `action: run_critique`
- `safe_command: /fig_critique fig1_overview_v2_pair_001_vault`
- `stop_boundary: host_llm_critique_required`

## Judgment

The plugin driver behaved correctly: it did not jump to recipe authoring while
the real fixture critique was stale. The next step requires host vision, not
local code execution.

## Next Required Step

Run:

```bash
/fig_critique fig1_overview_v2_pair_001_vault
```

Then rerun:

```bash
uv run python3 scripts/critique_lint.py examples/fig1_overview_v2_pair_001_vault
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "issue47 real svg polish dogfood" --json
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode polish --goal "issue47 real svg polish dogfood" --dry-run
```

Only proceed to `polish/svg_polish_recipe.yaml` if the loop checkpoint routes to
`ready_for_svg_polish` with no human/top-tier/crop blockers.
