# Authoring Boundary Closeout Dogfood

**Date:** 2026-05-23 KST
**Status:** evidence captured; design chain complete for Issues 29-32

## Scope

This milestone reviews the authoring-boundary hardening chain added after the
real-use box-boundary overflow failures:

- Issue 29: deterministic text-boundary clash gate
- Issue 30: `text_boundary_layout` -> `text_boundary_checks` helper
- Issue 31: scoped TeX coordinate-shift helper
- Issue 32: `/fig_closeout` text-boundary sync step

The goal is plugin workflow validation only. This milestone does not change any
figure source, generated build artifact, export artifact, golden state, or
accepted state.

## Fixture Coverage At Closeout

At the time this closeout evidence was captured, no tracked example declared
`spec.yaml.text_boundary_layout` or `spec.yaml.text_boundary_checks`.

Command:

```bash
find examples -maxdepth 2 -name spec.yaml -print | \
  xargs rg -n "text_boundary_layout|text_boundary_checks"
```

Result at closeout time: no matches.

Interpretation: the plugin contract and tests are implemented, but real-fixture
adoption remains a fixture-authoring step. This is not a code blocker; it is the
next time-to-use step for figures that contain row boxes, column rules, panel
boundaries, or internal instrument rectangles.

## Real Fixture Smoke

Command:

```bash
uv run python3 scripts/fig_closeout.py smoke_trap_demo --json
```

Observed:

- schema: `figure-agent.closeout.v1`
- `text_boundary_checks`: `not_required`
- reason: `spec.yaml.text_boundary_layout is absent`
- next action: `/fig_compile smoke_trap_demo`

Command:

```bash
uv run python3 scripts/fig_closeout.py fig1_overview_v2_pair_001_vault --json
```

Observed:

- schema: `figure-agent.closeout.v1`
- `text_boundary_checks`: `not_required`
- reason: `spec.yaml.text_boundary_layout is absent`
- next action: `/fig_compile fig1_overview_v2_pair_001_vault`
- critique/export/adjudication states remain fixture closeout work, not a
  text-boundary sync blocker.

Interpretation: adding the new closeout step did not break existing fixtures.
The step is backward-compatible when no author-facing boundary layout has been
declared.

## Contract Test Evidence

Command:

```bash
uv run pytest -q \
  tests/test_fig_closeout.py \
  tests/test_text_boundary_spec_helper.py \
  tests/test_text_boundary_clash.py
```

Result:

```text
31 passed
```

Covered states:

- layout absent -> `text_boundary_checks: not_required`
- layout present + generated checks match -> `passed`
- layout present + checks missing -> `needs_action`
- layout present + checks stale -> `needs_action`
- malformed layout -> `blocked`
- next-action ordering prefers boundary sync before compile

## Design Review

### What Is Now Closed

The specific failure class "text crosses a declared box/rule boundary but the
plugin does not notice" has a complete plugin-side chain:

1. Authors can declare explicit boundaries in `spec.yaml`.
2. The helper generates the verbose checker contract.
3. Compile emits deterministic `text_boundary_clash.json` candidates.
4. Critique/lint require `TB###` accounting.
5. Closeout surfaces stale/missing boundary checks before compile/loop closure.

### What Is Intentionally Not Solved

- The plugin still does not infer row boxes or instrument boxes from arbitrary
  TikZ source. This is deliberate; inferred geometry would be unreliable and
  would weaken the explicit contract.
- Existing fixtures are not auto-migrated. A human/agent must add
  `text_boundary_layout` for fixtures that need this gate.
- `/fig_closeout` remains read-only. It tells the operator to run
  `text_boundary_spec_helper.py`; it does not mutate `spec.yaml` itself.

### Remaining Practical Gap

The remaining work was adoption on real fixtures that contain boundary risks.
`fig1_overview_v2_pair_001_vault` is the natural first adoption target because
its apparatus row has D/E and E/F column rules plus instrument display
rectangles. That adoption is fixture-specific authoring metadata, not core
plugin code. See `2026-05-23-fig1-text-boundary-adoption.md` for the follow-up
dogfood pass.

## Conclusion

No known core plugin design blocker remains for the authoring-boundary chain.
The next work is fixture adoption/dogfood, not another generic plugin feature.
