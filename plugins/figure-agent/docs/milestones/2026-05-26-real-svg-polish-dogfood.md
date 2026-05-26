# Issue 47 - Real Fixture SVG Polish Dogfood

**Status:** evidence closed - real fixture does not route to SVG polish yet
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

Initial result before refreshing the render:

- `render_state: STALE`
- `critique_state: STALE`
- first blocker: render stale
- driver next action: compile

```bash
bash scripts/compile.sh examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
```

Result on the original preflight branch:

- compile succeeded;
- no PDF text collisions;
- no text-boundary clashes;
- `build/visual_clash.json` regenerated;
- visual clash total: `45`.

After merging latest `main` (`2595bf1`, v8.5/v8.6 aesthetic upgrade) into this
Issue 47 branch, compile was rerun.

Latest compile result:

- compile succeeded;
- no PDF text collisions;
- no text-boundary clashes;
- `build/visual_clash.json` regenerated;
- visual clash total: `46`.

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
- `visual_clash.missing_refs: [VC046]` in stale critique accounting

## Judgment

The plugin driver behaved correctly: it did not jump to recipe authoring while
the real fixture critique was stale. The next step requires host vision, not
local code execution.

## Host Critique Refresh Result

`/fig_critique fig1_overview_v2_pair_001_vault` was refreshed on
2026-05-26T20:30:00Z.

Result:

- `critique.md` schema remains `figure-agent.critique.v1.11`.
- `generator_version`: `sha256:2bf5a894...`
- `critique_input_hash`: `sha256:7848464b...`
- `M046` was added for the new `VC046` corona `+` marker as
  `accept_simplification`.
- 21 visual-clash crop ids were renamed to match the current manifest.
- `critique_lint.py` passed.
- Audit evidence passed:
  - visual clash accounting: `46/46`
  - crop accounting: `112/112`
  - uncertain crops: `0`
  - defect crops: `0`

The first local `critique_adjudication.py sync` attempt exposed a plugin bug:
the sync freshness check still compared against the legacy
`figure-agent.critique-rubric.v1.10` constant instead of the
`quality_manifest.expected_critique_rubric_version()` policy used by
`/fig_status`. The bug was fixed in this branch and covered by
`test_sync_adjudication_accepts_v1_11_rubric_for_aesthetic_intent_v2`.

After the fix, adjudication sync succeeded:

```bash
uv run python3 scripts/critique_adjudication.py sync \
  examples/fig1_overview_v2_pair_001_vault
```

## Final Routing Result

```bash
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "issue47 real svg polish dogfood" --json
```

Result:

- `audit_evidence.evaluation_state: passed`
- `visual_clash.accounted_count: 46`
- `crop_audit.required_count: 112`
- `editorial_art_direction_summary.polish_recommended_path: continue_tikz`
- `editorial_art_direction_summary.polish_trigger_verdict: pass`
- `editorial_art_direction_summary.human_art_direction_gate_verdict: pass`
- `final_stop_reason: status_action_required`
- next action: tracked golden roll-forward would require explicit
  `/fig_export --force-golden`, but this dogfood does not mutate golden state.

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode polish --goal "issue47 real svg polish dogfood" --dry-run
```

Result:

- `action: run_fig_loop`
- `stop_boundary: mode_forbidden_action`
- reason: latest `/fig_loop` editorial art-direction summary recommends
  `continue_tikz`; leave polish mode and resolve source-level illustration
  issues first.
- No polish recipe was authored.
- No source, generated export, accepted, golden, or polished-SVG state was
  mutated.

## Final Judgment

Issue 47 did not prove a real SVG polish execution path because the real
fixture's own refreshed critique does not authorize SVG polish yet. This is a
valid negative dogfood result:

- The stale critique gate worked.
- The crop/read accountability path worked after host refresh.
- The adjudication sync gap was found and fixed.
- The driver honored `continue_tikz` instead of inventing a polish recipe.

The next plugin-development step is not SVG editing on this fixture. It is to
either:

1. perform bounded TikZ/source-level illustration work until the host critique
   routes `ready_for_svg_polish`, or
2. dogfood the SVG route on another real fixture whose refreshed critique
   already routes `ready_for_svg_polish`.

Do not proceed to `polish/svg_polish_recipe.yaml` for this fixture until the
loop checkpoint explicitly changes to `ready_for_svg_polish`.
