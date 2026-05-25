# Issue 47 - Real Fixture SVG Polish Dogfood

**Status:** blocked on host critique refresh after latest-main preflight
**Builds on:** Issue 46 polished-SVG clean dogfood

## Problem

Issue 46 proves the polished-SVG route with a deterministic temporary fixture.
The remaining product question is whether a real figure fixture can traverse the
same route without confusing the operator or mutating protected source,
accepted, golden, or generated-export state.

The first real candidate is `fig1_overview_v2_pair_001_vault` because it is the
only current fixture with explicit `aesthetic_intent.yaml` triggers routing to
`ready_for_svg_polish`.

## Goal

Run a real-fixture dogfood of the SVG polish route:

```text
/fig_status -> /fig_driver --mode polish -> /fig_critique if required ->
/fig_loop -> recipe -> executor -> delta pack -> handoff -> final artifact state
```

## Scope

In scope:

- Use `fig1_overview_v2_pair_001_vault` as the first real candidate.
- Follow `/fig_driver --mode polish` exactly.
- Record the blocker chain and every command result.
- Avoid source drawing edits during this plugin dogfood.
- Avoid committing generated build/export/polish artifacts unless explicitly
  accepted as fixture evidence.

Out of scope:

- New drawing changes.
- Hidden auto-polish.
- Accepted/golden roll-forward.
- Changing release policy.

## Current Preflight Result

On branch `codex/issue47-real-svg-polish-dogfood`, the real candidate does not
yet reach the SVG polish route.

After merging latest `main` and running compile, the state is:

- `render_state: FRESH`
- `critique_state: STALE`
- `export_state: TRACKED_GOLDEN`
- `final_artifact_kind: generated_export`
- `final_artifact_state: NONE`
- `build/visual_clash.json total: 46`
- `/fig_driver --mode polish` action: `run_critique`
- stop boundary: `host_llm_critique_required`

The next required step is a host vision critique refresh:

```bash
/fig_critique fig1_overview_v2_pair_001_vault
```

Do not author a polish recipe until the refreshed critique and loop checkpoint
actually route to `ready_for_svg_polish`.

## Host Critique Handoff

Run the canonical host vision command:

```bash
/fig_critique fig1_overview_v2_pair_001_vault
```

The refreshed critique must account for current audit evidence, including
`build/visual_clash.json` candidate `VC046` and the current audit-crop manifest.
After writing `critique.md`, run:

```bash
uv run python3 scripts/critique_lint.py examples/fig1_overview_v2_pair_001_vault
uv run python3 scripts/critique_adjudication.py scaffold \
  examples/fig1_overview_v2_pair_001_vault --force
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "issue47 real svg polish dogfood" --json
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode polish --goal "issue47 real svg polish dogfood" --dry-run
```

## Acceptance Criteria

- Preflight evidence is recorded.
- Host critique is refreshed and lint-clean.
- `/fig_loop` records a checkpoint with no human/top-tier/crop blocker and
  `polish_recommended_path: ready_for_svg_polish`.
- A bounded recipe is authored and dry-run first.
- Executor writes only `polish/<name>.polished.svg`.
- Delta pack is generated and reviewed.
- Handoff manifest is written.
- Final artifact status is `FRESH` in an isolated dogfood path or explicitly
  documented as blocked by fixture policy.
