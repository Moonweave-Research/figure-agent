---
description: Dry-run advisory figure driver. Reads /fig_status and recommends one next action without mutating any fixture file.
---

Run the advisory driver for one figure.

**Usage**: `/fig_drive <name> --mode <mode> --goal "<goal>" --dry-run`

Run from the plugin root:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "<goal>" --dry-run
```

`--dry-run` is required in Issue 8B. The command never compiles, exports,
critiques, patches, polishes, accepts, stages, or commits. It reads
`status.infer_stage()` and emits one advisory action as JSON.

`/fig_drive` is the recommender. `/fig_loop` is the verify-only checkpoint
that records evidence after the user/outer agent acts on a recommendation.
Neither command executes the recommendation — the driver never runs any
action; `/fig_loop` only logs the resulting state.

## Modes

- `authoring` — source/build loop. Recommends `run_compile` when render is
  missing/stale; reports `complete` when render is fresh. Critique, export,
  loop, polish, and release actions are forbidden in this mode.
- `review` — close compile, critique, adjudication, and `/fig_loop` evidence,
  one patch target at a time. Hidden source editing, automatic host critique
  authoring, final SVG polish, and accepted/golden mutation are forbidden.
- `release` — accepted/golden/final-artifact readiness. Mutating `accepted`,
  forcing golden overwrite, creating polished SVG, and hiding unresolved
  findings are forbidden.
- `polish` — SVG final-artifact handoff after generated export is current.
  Editing generated `exports/`, treating polish as source repair, setting
  `accepted: true`, and bypassing semantic backport are forbidden.

## Output JSON contract

`schema: figure-agent.driver.v1` with these fields:

| Field               | Type                  | Notes                                            |
|---------------------|-----------------------|--------------------------------------------------|
| `schema`            | string                | `figure-agent.driver.v1`                         |
| `fixture`           | string                | figure name                                      |
| `mode`              | string                | `authoring \| review \| release \| polish`        |
| `goal`              | string                | passthrough of the `--goal` argument             |
| `status`            | object                | compact `/fig_status` vector                     |
| `action`            | string                | one of the 11 canonical action names             |
| `safe_command`      | string or null        | concrete shell/slash command, or `null`          |
| `stop_boundary`     | string or null        | one of the 9 canonical stop identifiers          |
| `reason`            | string                | one-line explanation                             |
| `forbidden_actions` | list of strings       | union of action-vocabulary names and mutation-namespace identifiers (see below) |
| `may_execute`       | bool                  | always `false` in Issue 8B                       |

### Schema versioning

The `schema` field is a stable contract identifier. Consumers MUST ignore any
unknown top-level field so additive changes within `v1` are backward
compatible; the `vN` suffix changes only on incompatible removal or rename of
a documented field.

### `safe_command` conventions

When `safe_command` is non-null it falls into one of two namespaces:

- **shell** (`uv run python3 ...`, `bash scripts/...`) — runnable by a generic
  shell or `subprocess.run`.
- **slash** (`/fig_critique <name>`, etc.) — requires a Claude host loop
  (e.g. `/fig_critique` invokes host vision); a non-Claude executor must
  delegate these to the host.

In both cases the goal substring is shell-quoted via `shlex.quote`, so a goal
containing spaces or single quotes is safe to copy-paste.

## Action vocabulary

Eleven canonical action names. The driver returns exactly one per call:

`create_or_fix_source`, `run_compile`, `run_critique`, `run_adjudicate`,
`run_fig_loop`, `run_export`, `patch_handoff_stop`, `human_gate_stop`,
`polish_handoff_stop`, `release_blocked`, `complete`.

### Deferred until /fig_loop output ingestion (Issue 8C+)

The Issue 8B driver does not consume `/fig_loop` output, so it does not emit
the patch-evidence-driven actions `patch_handoff_stop` and `human_gate_stop`
or the boundaries `ambiguous_patch_selection`, `patch_handoff_required`,
`human_gate_required`, `force_golden_required`, and `mode_forbidden_action`.
They are present in the contract so a later driver (and any executor) keeps a
stable vocabulary; in the current driver they are unreachable.

## Forbidden-action identifiers

`forbidden_actions` is a flat list of stable strings drawn from two
namespaces. Consumers should treat both as opaque identifiers.

**Action-vocabulary subset** (in `authoring` mode): `run_critique`,
`run_adjudicate`, `run_export`, `run_fig_loop`, `polish_handoff_stop`,
`release_blocked` — these are canonical action names the driver itself would
never recommend in that mode.

**Mutation namespace** (`review` / `release` / `polish` modes):

- `edit_source` — source `.tex` / briefing / spec edits.
- `edit_source_outside_patch_handoff` — review mode allows source edits only
  inside a `/fig_loop` `patch_handoff.allowed_edit_scope`.
- `edit_generated_export` — direct edits to `exports/`.
- `edit_polished_svg` — direct edits to `polish/<name>.polished.svg`.
- `set_accepted` — flipping `spec.yaml.accepted` to `true`.
- `force_golden` — `--force-golden` golden roll-forward.
- `bypass_semantic_backport` — promoting polished SVG when the manifest
  declares `backport_required` or `semantic_change_declared`.

## Stop-boundary identifiers

If `stop_boundary` is non-null, stop and satisfy that boundary before running
any other command. Identifiers:

- `host_llm_critique_required` — `/fig_critique` must run via host Claude.
- `reference_missing` — declared reference input is absent; fix `spec.yaml`
  path or add the file first.
- `ambiguous_patch_selection` — more than one actionable patch target.
- `patch_handoff_required` — exactly one `/fig_loop` patch target awaits.
- `human_gate_required` — adjudication/escalation needs domain review.
- `accepted_or_final_ready_required` — release readiness needs accepted /
  golden / final artifact promotion.
- `force_golden_required` — golden roll-forward needs `--force-golden`.
- `semantic_backport_required` — polish manifest declares semantic backport.
- `mode_forbidden_action` — next state-machine action is disallowed by mode.

## Examples

```bash
uv run python3 scripts/fig_driver.py fig1_overview --mode authoring --goal 'tighten layout' --dry-run
uv run python3 scripts/fig_driver.py fig3_trap --mode review --goal 'close review loop' --dry-run
uv run python3 scripts/fig_driver.py fig2_band --mode release --goal 'final release check' --dry-run
uv run python3 scripts/fig_driver.py fig4_polish --mode polish --goal 'svg polish handoff' --dry-run
```

`/fig_drive` is the driver wrapper for the docs contract in
`skills/figure-agent/SKILL.md` §"Driver rule for agents". Treat
`/fig_status <name>` as the canonical first check; use `/fig_drive` when you
need a mode-scoped, JSON-stable recommendation instead of free-form prose.

Next: follow `safe_command` if non-null and `stop_boundary` is null; otherwise
satisfy the stop boundary before re-running `/fig_drive`. Never override
`may_execute: false`.
