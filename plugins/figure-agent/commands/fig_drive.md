---
description: Dry-run advisory figure driver. Reads /fig_status and recommends one next action without mutating any fixture file.
---

Run the advisory driver for one figure.

**Usage**: `/fig_drive <name> --mode <mode> --goal "<goal>" --dry-run`

Run from the plugin root:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "<goal>" --dry-run
uv run python3 scripts/fig_driver.py <name> --mode final --goal "final readiness" --dry-run
```

`--dry-run` is required. The command never compiles, exports,
critiques, patches, polishes, accepts, stages, or commits. It reads
`status.infer_stage()`, optionally ingests the latest valid `/fig_loop`
checkpoint under `.scratch/fig-loop-runs/`, and emits one advisory action as
JSON.

`/fig_drive` does not read `.scratch/fig-run-runs/` journals. Those records are
operator evidence only; the driver always recomputes from live status, closeout,
and current loop evidence.

`/fig_drive` is the recommender. `/fig_loop` is the verify-only checkpoint
that records evidence after the user/outer agent acts on a recommendation.
Neither command executes the recommendation — the driver never runs any
action; `/fig_loop` only logs the resulting state.

## Canonical Workflow Order

Use `/fig_status <name>` or `/fig_drive <name> --mode review --goal "<goal>"
--dry-run` as the first check. Follow this order unless the user explicitly
asks for a lower-level command:

1. `render_state: MISSING | STALE` -> `/fig_compile <name>`.
2. `render_state: FRESH` and `critique_state: MISSING | STALE |
   REFERENCE_MISSING` -> `/fig_critique <name>` or fix declared references.
3. `critique_state: FRESH` and stale/missing adjudication -> `/fig_adjudicate
   <name>` or repair `critique_adjudication.yaml`.
4. Closed compile/critique/adjudication prerequisites -> `/fig_loop <name>
   --goal "<goal>"`.
5. Export, release, or polish only when the driver selects that action.

This ordering is intentional: host vision critique must inspect the current
render, so stale render wins over stale critique.

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
- `final` — non-mutating final-readiness preset. It reuses the release
  readiness gates, surfaces a strict-compile final check, and emits explicit
  operator guidance for the next required actor. It does not force golden,
  set accepted state, edit SVG, export, or mutate publication evidence.

## Output JSON contract

`schema: figure-agent.driver.v1` with these fields:

| Field               | Type                  | Notes                                            |
|---------------------|-----------------------|--------------------------------------------------|
| `schema`            | string                | `figure-agent.driver.v1`                         |
| `fixture`           | string                | figure name                                      |
| `mode`              | string                | `authoring \| review \| release \| polish \| final` |
| `goal`              | string                | passthrough of the `--goal` argument             |
| `status`            | object                | compact `/fig_status` vector                     |
| `action`            | string                | one of the 11 canonical action names             |
| `safe_command`      | string or null        | concrete shell/slash command, or `null`          |
| `stop_boundary`     | string or null        | one of the 10 canonical stop identifiers         |
| `reason`            | string                | one-line explanation                             |
| `forbidden_actions` | list of strings       | union of action-vocabulary names and mutation-namespace identifiers (see below) |
| `workspace_warnings` | list of strings      | read-only git/workspace warnings; never blocks or mutates |
| `status_explanation` | object or absent     | shared `/fig_status` explanation of first blocker and state buckets |
| `audit_evidence`    | object or absent      | shared `/fig_status` audit-evidence summary with compact blockers and next action |
| `next_action_summary` | object              | compact read-only UX summary of the selected action, blocker source, scope, and evidence refs |
| `may_execute`       | bool                  | always `false`                                   |
| `loop_checkpoint`   | object or absent      | compact latest `/fig_loop` evidence when it drives the recommendation |
| `closeout`          | object or absent      | compact `/fig_closeout` evidence when incomplete closeout drives the recommendation |
| `operator_guidance` | object                | plain next-step UX: state, required actor, and one operator instruction |
| `final_readiness_profile` | object or absent | final-mode checklist for strict compile, critique, loop, export, publication, and release gates |

The compact `status` object includes publication-gate fields when available:
`publication_gate_state` and `publication_gate_failures`. In release mode,
`HUMAN_ACCEPTANCE_REQUIRED` or `PROVENANCE_REQUIRED` produces
`action: release_blocked` with `stop_boundary:
accepted_or_final_ready_required`; the `reason` names the first blocker code
and required action. The driver remains dry-run and never sets `accepted`,
writes `QUALITY_AUDIT.md`, forces golden state, or mutates provenance.

For missing or stale generated exports, the driver only surfaces a runnable
`run_export` command when the state also matches `/fig_run`'s draft-export
execution policy: `acceptance_state: NOT_DECLARED`, `critique_state: FRESH |
NOT_REQUIRED`, and `export_state: MISSING | STALE`. If acceptance is already
declared as not accepted, release/polish mode returns a stop boundary instead
of a command that the runner would later refuse.

When present, `status_explanation` is copied from `/fig_status` without
recomputing state. Its `first_blocker.code` is appended to `reason` so a
caller can distinguish fixture freshness blockers (`render_stale`,
`critique_stale`, `export_missing`) from human-only blockers
(`export_tracked_golden`, `publication_gate_required`, `not_accepted`) without
guessing from the raw state vector. This is explanatory only; it does not make
`safe_command` executable and does not change the selected action.

When present, `audit_evidence` is also copied from `/fig_status` without
recomputing state. Actionable states (`missing_input`, `stale_or_mismatched`,
`needs_action`) are appended to `reason` with the summary's compact blocker
context. This keeps visual-clash, text-boundary, label-path,
undeclared-geometry, and crop-accounting blockers visible to an outer executor
without changing the driver's action vocabulary, dry-run guarantee, or selected
command.

`next_action_summary` is additive compression of the already selected driver
action. It must match top-level `action` and `safe_command`; it does not
reinterpret state, authorize mutation, or introduce a second selector. Use it
for compact UI/handoff displays, then inspect `status_explanation`,
`audit_evidence`, `loop_checkpoint`, or `closeout` for detailed evidence. Its
`decision_boundary` sub-object names the authority behind the next step:
`deterministic_plugin_gate`, `host_vision_gate`, `human_decision`,
`release_decision`, `polish_handoff`, `advisory_only`, or `none`. Use this to
distinguish "must resolve before continuing" from "safe but optionally
improvable"; advisory-only aesthetic candidates do not block release.

`operator_guidance` is the user-facing answer to "what do I do next?" It names
one required actor (`workflow_agent`, `host_llm`, `human`, `release_operator`,
`svg_editor`, or `none`) and one next-step instruction. In `complete` states it
explains that no required plugin action remains for the selected mode; in
human/release states it does not surface hidden mutation commands. It copies
`next_action_summary.decision_boundary` when available so shell users can see
the same blocking/advisory distinction without reading lower-level evidence
objects.

In `--mode final`, `final_readiness_profile` is added. It is a non-mutating
checklist, not a second router. The strict compile row always includes:

```bash
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/<name>/<name>.tex
```

If render is stale, that strict compile command becomes the selected
`safe_command`. If render is already fresh, the command remains visible as the
manual final render check, while release/golden/publication decisions stay
human-only. Final mode also requires a current verify-only `/fig_loop`
checkpoint before it can report `complete`, so final release guidance is based
on the same loop evidence used by review, release, and polish routing.

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

### `/fig_loop` output ingestion

In review mode, after render/critique/adjudication prerequisites are closed,
`/fig_drive` first checks read-only `/fig_closeout` evidence. If closeout is
incomplete, the driver returns the closeout boundary before recommending a new
loop checkpoint. For example, stale export closeout maps to `run_export`, stale
loop-rerun closeout maps to `run_fig_loop`, and tracked golden roll-forward
stays blocked behind manual approval. The driver never runs closeout or its
next action.

When closeout does not block, `/fig_drive` reads the latest valid verify-only
`/fig_loop` run for the same fixture. Malformed runs, wrong-fixture runs, and
runs older than the current source, authoring context, critique, adjudication,
publication audit, theory guard, subregion log, or build evidence are ignored.

The driver translates loop evidence as follows:

- `patch_target_recommended` or `active_subregion_recommended` with a
  `patch_handoff` -> `patch_handoff_stop` /
  `patch_handoff_required`.
- `ambiguous_patch_selection` -> `patch_handoff_stop` /
  `ambiguous_patch_selection`.
- `human_gate_required` or `escalation_level: human_review_required` ->
  `human_gate_stop` / `human_gate_required`.
- `basin_detected` with `basin_summary` ->
  `human_gate_stop` / `human_gate_required`, with the repeated signal and
  history count named in `reason`. This is a step-out boundary, not a request
  for another blind local patch.
- `top_tier_audit_summary` with any `fail`, `needs_human`, or positive
  `blocking_high_impact_count` -> `human_gate_stop` /
  `human_gate_required`. This takes priority over export or golden
  roll-forward recommendations; weak-only summaries do not block.
- `editorial_art_direction_summary` with `fail`, `needs_human`,
  `needs_human_art_direction`, or positive `blocking_high_impact_count` ->
  `human_gate_stop` / `human_gate_required`. This keeps target-journal
  art-direction choices visible before export, polish, or release.
- `status_action_required` with `--force-golden` in the recommendation ->
  `release_blocked` / `force_golden_required`.
- `no_actionable_findings` or `verify_only_complete` -> `complete`.

Other loop states stay conservative and return `run_fig_loop`.

In `--mode polish`, the driver also reads the latest current `/fig_loop`
checkpoint after compile, critique, export, and final-artifact hard gates are
closed. If that checkpoint includes `editorial_art_direction_summary`, the
driver routes `polish_recommended_path` as follows:

| `polish_recommended_path` | Driver action | Stop boundary |
|---|---|---|
| `continue_tikz` | `run_fig_loop` | `mode_forbidden_action` |
| `ready_for_svg_polish` | `polish_handoff_stop` | `null` |
| `needs_human_art_direction` | `human_gate_stop` | `human_gate_required` |
| `semantic_backport_required` | `polish_handoff_stop` | `semantic_backport_required` |

The driver still never edits source, exports, polished SVGs, accepted state, or
golden state. `continue_tikz` means polish mode is the wrong next executor; run
the review loop and patch source through the normal `/fig_loop` handoff
boundary. For schema `figure-agent.critique.v1.14` and newer schemas that
inherit the route-detail contract, the loop summary can carry route detail
(`remaining_tikz_lever`, `svg_polish_candidate_reason`,
`semantic_backport_reason`, or `human_art_direction_reason`); the driver copies
that detail into its explanatory readiness output. If the summary says
`ready_for_svg_polish` but another editorial slot still reports `fail`,
`needs_human`, or a high-impact blocker, the human gate wins over polish
handoff.

If no current loop checkpoint can prove `ready_for_svg_polish`, polish mode
returns `run_fig_loop` / `mode_forbidden_action` instead of falling back to SVG
handoff from export freshness alone. This keeps SVG polish subordinate to the
same critique, adjudication, audit, and human-gate evidence used by review and
release.

When a current loop checkpoint is available, polish mode also emits
`svg_polish_readiness` as an additive top-level JSON field. This is the compact
answer to "can SVG polish start yet?":

```json
{
  "schema": "figure-agent.svg-polish-readiness.v1",
  "can_start_svg_polish": false,
  "recommended_path": "continue_tikz",
  "next_action": "run_fig_loop",
  "blocking_reason": "editorial polish trigger recommends continue_tikz: move Panel F recovery label in source",
  "blocking_items": [
    {
      "source": "editorial_art_direction_summary",
      "id": "tikz_vs_svg_polish_trigger",
      "recommended_path": "continue_tikz",
      "verdict": "weak",
      "route_detail": "move Panel F recovery label in source"
    }
  ]
}
```

The readiness object is explanatory only. It never grants mutation authority.
`ready_for_svg_polish` is necessary for the recipe route, but human, top-tier,
crop, aesthetic, semantic-backport, freshness, export, accepted, golden, and
publication gates still take precedence.

If `/fig_driver --mode polish` reaches SVG polish, follow the first command it
surfaces. The canonical recipe path is:

1. If `polish/svg_polish_recipe.yaml` is missing, author a bounded recipe first.
2. If the recipe exists, inspect the executor plan:

```bash
uv run python3 scripts/svg_polish_executor.py examples/<name> --dry-run
```

3. After reviewing the dry-run plan, write the polished SVG only for
   visual-only edits:

```bash
uv run python3 scripts/svg_polish_executor.py examples/<name> --write
```

4. Generate before/after/diff evidence for critique:

```bash
PYTHONPATH=scripts uv run python3 -c "from pathlib import Path; from svg_polish_delta import build_svg_polish_delta_pack; build_svg_polish_delta_pack(Path('examples/<name>'), base_dir=Path('.'))"
```

5. Use `scripts/svg_polish_handoff.py` after the delta pack exists to scaffold
   audit and manifest metadata.

## Workspace Warnings

`workspace_warnings` is an additive advisory field. The driver reads
`git status --porcelain --untracked-files=no` and reports tracked dirty paths
as `tracked_worktree_dirty: ...`. This is a conflict-mediation hint for
parallel Codex/Claude work: it tells the next executor to inspect existing
tracked edits before patching the same files. It does not include ignored build
artifacts, does not block recommendations, and does not stage, revert, or edit
anything.

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
- `closeout_required` — post-patch compile/critique/adjudication/export/loop
  closeout is incomplete; inspect the `closeout` object before proceeding.

## Examples

```bash
uv run python3 scripts/fig_driver.py fig1_overview --mode authoring --goal 'tighten layout' --dry-run
uv run python3 scripts/fig_driver.py fig3_trap --mode review --goal 'close review loop' --dry-run
uv run python3 scripts/fig_driver.py fig2_band --mode release --goal 'final release check' --dry-run
uv run python3 scripts/fig_driver.py fig4_polish --mode polish --goal 'svg polish handoff' --dry-run
uv run python3 scripts/fig_driver.py fig1_overview --mode final --goal 'final readiness' --dry-run
```

`/fig_drive` is the driver wrapper for the docs contract in
`skills/figure-agent/SKILL.md` §"Driver rule for agents". Treat
`/fig_status <name>` as the canonical first check; use `/fig_drive` when you
need a mode-scoped, JSON-stable recommendation instead of free-form prose.

Next: follow `safe_command` if non-null and `stop_boundary` is null; otherwise
satisfy the stop boundary before re-running `/fig_drive`. Never override
`may_execute: false`.
