# Current sulfur-paper figure state and next-session handoff

**Updated:** 2026-07-26
**Status:** Fig1 development baseline is frozen for now; it is not publication-final.

This document is the session handoff for the sulfur/polymer figure work. It is
the place to recover the current state without relying on chat history. It does
not replace `docs/figure-agent.md`, which remains the product authority.

## 1. Worktree authority

Use this worktree for the current Fig1 candidate:

```text
/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig1-authority
```

Current branch:

```text
fig1-authority
```

The active standalone cantilever work is deliberately separate:

```text
worktree: /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig3-dogfood
branch: fig5-actuation-development
fixture: examples/fig5_cantilever_actuation_artifact_v2
```

That directory name is historical; the Git branch is the authoritative Fig5
identity. Its dirty WIP is preserved and must not be treated as Fig1 source.

Do not edit these paths for this work:

```text
/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]
/Users/choemun-yeong/workspace/ResearchOS/[figure-agent-py]
/tmp/figure-agent-next
```

The main checkout has user-owned WIP. `/tmp/figure-agent-next` was used for
system-only verification and must not be mistaken for the maintained figure
source.

## 2. Fig1 baseline

The maintained Fig1 source is the nested repair candidate, not the canonical
fixture-root TeX:

```text
plugins/figure-agent/examples/fig1_updated_agent_redraw_v1/review/failure-first/comparable-v3-repair-c5/repaired.tex
```

The explicit current-candidate pointer is:

```text
plugins/figure-agent/examples/fig1_updated_agent_redraw_v1/review/current-candidate.json
```

It binds the candidate source to:

```text
source_sha256: sha256:6f0a40a221da752f0fdefe34238c74f9bfe8513e5f1e026bbac774f7d3670741
promotion_state: candidate_only
human_gate: pending
```

The source of the current render is therefore:

```text
plugins/figure-agent/examples/fig1_updated_agent_redraw_v1/review/failure-first/comparable-v3-repair-c5/build/repaired.png
```

The current candidate is a usable internal development baseline. It is not a
golden artifact, accepted artifact, submission file, or publication verdict.
The canonical fixture root may report `render=STALE` while the explicit nested
candidate reports `render=FRESH`; this is intentional fail-closed provenance,
not a missing or deleted figure.

### Human-authority snapshot

The user-provided Fig1 snapshot reviewed on 2026-07-26 is the highest-authority
visual development reference for this figure. It is pixel-equivalent to the
candidate render above and therefore binds the maintained visual state to:

```text
branch: fig1-authority
head: 2bb14af8fe16ee0762340c136a2f2b65e1c32669
candidate: comparable-v3-repair-c5
source: review/failure-first/comparable-v3-repair-c5/repaired.tex
render: review/failure-first/comparable-v3-repair-c5/build/repaired.png
```

The snapshot was originally authored on `fig1-redraw-to-final`; after the
Fig1/Fig5 split, its maintained authority is the `fig1-authority` branch above.

Stale Fig1 worktrees, older visual candidates, and unrelated ORRO lanes must
not override this snapshot when recovering or extending the figure. This is a
development-authority statement only; it does not change `promotion_state`,
the pending human gate, or the publication boundary above.

### Current machine evidence

Evidence below is from the candidate build directory above:

| Evidence | State |
|---|---|
| strict compile | `passed` |
| physics grounding | `grounded` |
| text-boundary declarations | `checked=11`, `total=0` |
| label/path declarations | `checked=9`, `total=0` |
| semantic assertions | `checked=3`, `issue_count=0` |
| visual clash | `blocking_total=0`, `report_only_total=26` |
| human acceptance | not declared |
| publication acceptance | not claimed |

Machine green is only the first evidence layer. The remaining Fig1 gate is a
human visual review at full size, reduction size, and intended print size. Open
questions are the final balance of A/B, the amount of visual weight assigned to
C, and the scientific reading of the C energy landscape. Do not expand C or
reopen A/B merely to manufacture another machine diff.

## 3. Fig1 scientific contract now in force

These are the paper-local decisions already encoded in the active Fig1
briefing/semantic contract:

- Panel E charging is a gridless two-terminal high-voltage state. Do not add a
  protective-ground symbol or a grid electrode to the charging stage.
- The specimen is manually moved from charging to the adjacent measurement
  station. Do not depict a motion stage, conveyor, or automated scan.
- The measurement state has a grounded conductive substrate.
- The sensing method is an induction-type electrostatic surface voltmeter
  (ESVM, SK-family level only). It is not a Kelvin probe/KPFM schematic.
- Panel E maps the measured surface-potential decay `V_s(t)` to a qualitative
  derived `g(E_t)` distribution; it is not a fitted data plot.
- Panel F keeps the sample/cantilever electrically floating while the grounded
  return belongs to the driven-electrode source circuit.
- Panel F currently contains a thin Maxwell-attraction baseline and a stronger
  Coulomb-repulsion result. This is part of the current candidate's visible
  composition and remains a human scientific interpretation gate for any
  future standalone cantilever figure; do not silently strengthen, remove, or
  reinterpret it in the next figure.

The active source and contracts are the authority for the current Fig1 render:

```text
examples/fig1_updated_agent_redraw_v1/briefing.md
examples/fig1_updated_agent_redraw_v1/spec.yaml
examples/fig1_updated_agent_redraw_v1/semantic_contract.yaml
examples/fig1_updated_agent_redraw_v1/authority.yaml
```

## 4. Existing cantilever fixtures are not current authority

Two existing fixtures are useful historical evidence but must not be extended
blindly:

### `examples/fig5_actuation_mechanism`

This is a v0.10 convention-validation sandbox. Its source tests a vertical
cantilever, clip-on-top convention and a side-electrode force arrow. Its
`+V/-V` actuation story is not the current experimental protocol. Keep it as a
regression artifact; do not treat its TeX as the next publication figure.

### `examples/fig3_floating_clip_protocol`

This is an SI/methods validation fixture whose briefing assumes grounded poling,
clip disconnection, and a four-phase polarity-reversal sequence. Those are
historical test assumptions, not the current charge/transfer/measurement setup.
Do not copy its `grounded poling` or automatic phase story into a new figure
without a new paper-local authority decision.

## 5. Standalone cantilever candidate

The active standalone cantilever development is in a separate Fig5 fixture:

```text
fig5_cantilever_actuation_artifact_v2
```

Source:

```text
plugins/figure-agent/examples/fig5_cantilever_actuation_artifact_v2/fig5_cantilever_actuation_artifact_v2.tex
```

The corresponding worktree is
`/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig3-dogfood`
on branch `fig5-actuation-development`. Its current clean HEAD is
`a662bb42` (`Keep the repeated cantilever scale consistent`). This is an
exploratory Figure Agent artifact, not a publication-final figure or an
accepted artifact.

The current Fig5 machine state is:

| Evidence | State |
|---|---|
| strict compile | `passed` |
| conventions | `present` (`17`) |
| physics grounding | `grounded` |
| render/export | `FRESH` |
| acceptance | `NOT_DECLARED` |
| final-ready | `false` |

Current render and export paths:

```text
examples/fig5_cantilever_actuation_artifact_v2/build/fig5_cantilever_actuation_artifact_v2.png
examples/fig5_cantilever_actuation_artifact_v2/exports/fig5_cantilever_actuation_artifact_v2.png
```

The latest Fig5 authoring contract is the four-stage causal story:

```text
two-terminal HV charge → source-off isolation → reversed-drive force balance → continuous bend response
```

Its current plan/caption/source are co-located in the Fig5 fixture:

```text
examples/fig5_cantilever_actuation_artifact_v2/authoring_plan.md
examples/fig5_cantilever_actuation_artifact_v2/caption.md
examples/fig5_cantilever_actuation_artifact_v2/fig5_cantilever_actuation_artifact_v2.tex
```

Do not import the old `fig5_cantilever_mechanism_v1` machine evidence into this
new artifact. The old fixture remains historical evidence only.

The last validated evidence for the former v1 sandbox was:

| Evidence | State |
|---|---|
| strict compile | `passed` |
| physics grounding | `grounded` |
| text-boundary declarations | `checked=5`, `total=0` |
| label/path declarations | `checked=3`, `total=0` |
| TeX force-direction assertion | `checked=1`, `issue_count=0` |
| visual clash | `blocking_total=0`, `report_only_total=6` |
| Figure Agent status | `render=FRESH`, `acceptance=NOT_DECLARED` |
| host critique/export | required/not created |

The first strict render exposed label/path defects in the ESVM and transfer
lanes; those were corrected before the current green render. The remaining
`report_only` visual candidates and the host critique are deliberately left as
human review gates rather than silently promoted or suppressed.

The current authoring slice is a low-detail, experiment-grounded process
schematic:

```text
two-terminal HV charge → manual specimen transfer → grounded measurement state → cantilever response
```

The current fixture already has its authoring plan and caption. Further edits
must preserve only the apparatus topology and claim-bearing arrows until the
force direction, grounding ownership, manual transfer agency, and air gap
survive 100%, 50%, and 33% review. Material texture, gradients, and editorial
polish remain downstream work.

### Future cantilever invariants

- Cantilever is vertical, with the clip/clamp above and polymer hanging down.
- The cantilever is mechanically clamped but electrically isolated during the
  response scene.
- The driven electrode and its grounded source return are separate from the
  cantilever and trapped-charge path.
- The air gap is visibly non-contact and has a clear named referent.
- `q_{tr}` markers are embedded in the polymer body, not floating beside it.
- The primary force arrow touches its source and points to its declared result;
  no direction is invented when polarity is not declared.
- No Kelvin-probe fork, vibration arc, grid electrode, automatic motion stage,
  or unverified model-specific instrument detail.
- No quantitative force, angle, voltage, or fitted displacement is added to a
  qualitative mechanism schematic unless a paper-local source declares it.

If the next paper-local authority confirms polarity-reversed actuation, make it
a separate declared sequence. Do not infer bidirectionality merely from the
existence of a nearby electrode.

## 6. Reproduce the current state

From a fresh session:

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig1-authority/plugins/figure-agent"
./bin/fig-agent status fig1_updated_agent_redraw_v1
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/fig1_updated_agent_redraw_v1/review/failure-first/comparable-v3-repair-c5/repaired.tex
```

Then inspect the candidate render, not the canonical-root export:

```text
examples/fig1_updated_agent_redraw_v1/review/failure-first/comparable-v3-repair-c5/build/repaired.png
```

For any new fixture, follow the repository workflow in this order:

```text
fig-agent status → fig_new → briefing/spec/caption → author source → fig_compile → rendered review → fig_critique/fig_ground as applicable
```

For the active standalone cantilever candidate:

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig3-dogfood/plugins/figure-agent"
./bin/fig-agent status fig5_cantilever_actuation_artifact_v2
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/fig5_cantilever_actuation_artifact_v2/fig5_cantilever_actuation_artifact_v2.tex
```

Inspect the generated PNG at 100%, 50%, and 33% before any critique or export.

Do not promote a nested candidate to canonical, set `accepted: true`, force a
golden artifact, or claim publication acceptance from this handoff.

## 7. Stop boundary

The next action is documentation-complete and figure-authoring-ready, not
publication-final. The first new-figure decision that truly requires the paper
authority is whether the standalone cantilever should show only the current
single-force response or a polarity-reversed sequence. Until that is declared,
keep the new figure qualitative and one-directional.
