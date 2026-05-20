# Post-Push Critique Preflight

**Date:** 2026-05-20 KST
**Fixture:** `fig1_overview_v2_pair_001_vault`
**Status:** ready for host `/fig_critique`

## Purpose

Confirm that the pushed Issue 12 audit surfaces are available in the real
fixture before asking the Claude host loop to regenerate `critique.md`.

This preflight does not replace `/fig_critique`; it only verifies that the
evidence pack and command boundary are ready.

## Driver State

Command:

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal 'post-push audit dogfood' --dry-run
```

Result:

- `action: run_critique`
- `safe_command: /fig_critique fig1_overview_v2_pair_001_vault`
- `stop_boundary: host_llm_critique_required`
- `render_state: FRESH`
- `critique_state: STALE`
- `workspace_warnings: []`

## Brief Preflight

Command:

```bash
uv run python3 scripts/critique_brief.py examples/fig1_overview_v2_pair_001_vault
```

Observed:

- Brief emitted 2004 lines.
- `## High-Zoom Visual Audit Crops` appears.
- `## Print-Scale Audit Images` appears.
- `schema: figure-agent.critique.v1.4` appears.
- `rubric_version: figure-agent.critique-rubric.v1.4` appears.
- `scale_basis=fixed_width_proxy` appears in the print-scale section.
- `micro_defects.kind: print_scale_unreadable` is requested from print-scale
  evidence.

Separation check:

- The high-zoom section does not contain `print_scale_unreadable`.
- The high-zoom section does not contain `print_178mm`.
- The high-zoom section does not contain `print_thumbnail`.

## Audit Images

Verified with `file`:

- `build/audit_crops/print_178mm.png`: `1000 x 624`
- `build/audit_crops/print_thumbnail.png`: `360 x 225`
- `build/audit_crops/full_q1.png`: `2136 x 1333`
- `build/audit_crops/panel_D_q1.png`: `671 x 632`
- `build/audit_crops/panel_E_q1.png`: `701 x 632`
- `build/audit_crops/panel_F_q1.png`: `671 x 632`

Visual spot-check:

- `print_178mm.png` renders the full figure at reduced width.
- `print_thumbnail.png` renders a compact full-figure readability proxy.
- `panel_E_q1.png`, `panel_E_q2.png`, and `panel_F_q2.png` open correctly as
  high-zoom crops.

## Next Required Host Step

Run in the Claude host session:

```text
/fig_critique fig1_overview_v2_pair_001_vault
```

The host critique must Read the main render, all listed high-zoom crops, and
both print-scale audit images before writing `critique.md`.

After the host critique:

```bash
uv run python3 scripts/critique_adjudication.py sync fig1_overview_v2_pair_001_vault
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal 'post-push audit dogfood' --json
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal 'post-push audit dogfood' --dry-run
```

## Boundary

Codex did not overwrite `critique.md` in this preflight. Doing so would blur
the plugin's host-vision contract; the official dogfood step remains the
Claude `/fig_critique` command above.
