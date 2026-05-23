# Issue 32 — Authoring Closeout Boundary Sync

Status: completed in branch `codex/authoring-closeout`

## Problem

Issue 29 added deterministic text-boundary clash detection, Issue 30 added a
helper to generate `text_boundary_checks`, and Issue 31 added a scoped
coordinate shift helper. The remaining authoring gap is workflow sync: after a
panel/subregion move, a fixture can declare `text_boundary_layout` but still
carry missing or stale generated `text_boundary_checks`.

If `/fig_closeout` reports compile/export/loop actions without surfacing this
sync gap, users may run compile against stale boundary checks and miss the
exact class of box/rule text overflows the plugin is meant to catch.

## Scope

Extend `scripts/fig_closeout.py`.

In scope:

- Add a read-only `text_boundary_checks` closeout step.
- When `spec.yaml.text_boundary_layout` is absent, report `not_required`.
- When layout exists and generated checks match `text_boundary_checks`, report
  `passed`.
- When layout exists but `text_boundary_checks` is missing or differs from the
  generated contract, report `needs_action` with:

```bash
uv run python3 scripts/text_boundary_spec_helper.py examples/<name> --write
```

- When layout is malformed, report `blocked` with a controlled reason.
- Keep `/fig_closeout` read-only; it must not run the helper or edit `spec.yaml`.
- Update command docs and tests.

Out of scope:

- Running compile or critique.
- Inferring boundaries from TikZ or images.
- Changing `check_text_boundary_clash.py`.
- Changing `/fig_status` gates.

## Step Ordering

`text_boundary_checks` should appear before `compile` in the closeout report.
If it needs action or is blocked, `next_action` should point to that step before
compile/export/loop advice.

## Acceptance Criteria

- Missing layout preserves current behavior via `not_required`.
- Matching generated checks produce `passed`.
- Missing or stale checks produce `needs_action` and the helper command.
- Malformed layout produces `blocked`, not an unhandled traceback.
- The step is included in `blocking_step_ids` until passed/not-required.
- Tests cover all four states and next-action ordering.
