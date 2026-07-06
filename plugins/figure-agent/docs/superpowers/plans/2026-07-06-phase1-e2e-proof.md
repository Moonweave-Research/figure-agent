# Phase 1 exit check — learning-gradient E2E proof

Scripted end-to-end proof that the learning gradient is live on a real fixture
(`fig2_trap_design_space`). One run produces, in the experience log:

- ≥1 row with `outcome.quality_movement == "improved"` (defect-sourced candidate whose
  edit a re-run detector confirms resolved the defect)
- ≥1 row with `outcome.human_label == "reject"`
- 0 rows whose `state.target.subregion_key` starts with `unstable:`

The run is fully isolated: it operates on a **copy** of the fixture under a scratch
workspace (`FIGURE_AGENT_WORKSPACE`) and writes the experience log to a scratch dir
(`FIG_AGENT_EXPERIENCE_LOG_DIR`), so the tracked `docs/experience-log/` and `examples/`
trees are never touched.

## Prerequisites

- LaTeX toolchain (`lualatex`, `pdftocairo`, `rsvg-convert`) and `uv` on PATH.
- Run from the plugin root: `plugins/figure-agent`.

## Environment

```bash
PR="$PWD"                       # plugins/figure-agent (source tree = plugin root)
SC=/tmp/phase1-e2e              # any empty scratch dir
mkdir -p "$SC/ws/examples" "$SC/exp"
cp -R "$PR/examples/fig2_trap_design_space" "$SC/ws/examples/"
export FIGURE_AGENT_PLUGIN_ROOT="$PR"      # code (scripts, styles) resolves here
export FIGURE_AGENT_WORKSPACE="$SC/ws"     # examples/build/exports resolve here (the copy)
export FIG_AGENT_EXPERIENCE_LOG_DIR="$SC/exp"   # experience log lands here, not docs/
```

## Step 1 — baseline compile + generate the defect-sourced candidate set

```bash
./bin/fig-agent compile fig2_trap_design_space
./bin/fig-agent candidates fig2_trap_design_space --output build/candidates/candidate_set.json
```

`candidates` produces 6 ledger-sourced candidates (`source_defect` QD001–QD006, class
`text_overlap`, `edit_class=label_offset`). Each carries a `source_defect`, so its
post-apply recheck can score `improved` (art-direction candidates carry no `source_defect`
and can only be neutral).

## Step 2 — drive each candidate through render → accept → apply

For a candidate `<CID>` targeting panel `<P>`:

```bash
CS=build/candidates/candidate_set.json
./bin/fig-agent render-candidates fig2_trap_design_space --candidate-set "$CS" \
  --candidate-id <CID> --compile --export --crop-panel <P> --evaluate
./bin/fig-agent accept-candidate fig2_trap_design_space <CID> --candidate-set "$CS" \
  --decision accept --reviewer local-user --rationale "E2E proof: rendered evidence reviewed."
./bin/fig-agent apply-candidate fig2_trap_design_space <CID> --candidate-set "$CS" \
  --acceptance build/candidates/<CID>/acceptance.json
```

Panels: CAND001/002/003/004 → `A`, CAND005/006 → `B`.

Apply runs the post-apply pipeline (compile/export/status), the semantic recheck
(rebuilds the real `quality_defect_ledger`), and the value-preservation gate, then appends
one experience row. Observed outcomes:

- **CAND003 → `improved`**. Its bounded edit `\draw[... cGray!35] (4.95,0.45) -- (4.95,9.75)`
  → `(5.05,0.45) -- (5.05,9.75)` nudges a vertical gray rule 0.10 units right, physically
  clearing the `text_overlap` at panel A. The re-run `check_undeclared_geometry` ledger no
  longer reports QD004 → `detector_recheck.status="success"`,
  `reason="source_defect_resolved"`; `verifiers.labels_unchanged=pass`,
  `palette_locked=pass`; `apply_status="applied"`, `pipeline_ok=true`.
  The applied edit **persists** (a genuine improvement is not rolled back).
- CAND001/002/005/006 → `regressed`. The auto-derived nudge does not resolve the target
  defect (`reason="source_defect_unresolved"`), so the value-preservation gate
  auto-rolls-back the .tex (`apply_status="rolled_back"`). This is the documented
  blind-nudge ceiling, not a failure of the run.

Because CAND003's edit persists, restore the clean baseline before Step 3 (other candidates
are keyed to the original source and would drift-mismatch):

```bash
cp "$PR/examples/fig2_trap_design_space/fig2_trap_design_space.tex" \
   "$SC/ws/examples/fig2_trap_design_space/fig2_trap_design_space.tex"
./bin/fig-agent compile fig2_trap_design_space
./bin/fig-agent candidates fig2_trap_design_space --output build/candidates/candidate_set.json
```

## Step 3 — scripted reject

```bash
CS=build/candidates/candidate_set.json
./bin/fig-agent render-candidates fig2_trap_design_space --candidate-set "$CS" \
  --candidate-id CAND001 --compile --export --crop-panel A --evaluate
./bin/fig-agent accept-candidate fig2_trap_design_space CAND001 --candidate-set "$CS" \
  --decision reject --reviewer local-user --rationale "E2E proof: rejected on visual review."
# accept-candidate writes acceptance.json{decision:"reject"}. apply-candidate blocks a
# non-accept acceptance before it can append, so the reject row is logged via the
# sanctioned append entrypoint directly (same path the unit test exercises):
PYTHONPATH="$PR/scripts:$PR/scripts/checks:$PR/scripts/candidates:$PR/scripts/quality:$PR/scripts/loop:$PR/scripts/driver" \
python3 -c "import experience_log; from pathlib import Path; \
experience_log.append_apply_record('fig2_trap_design_space','CAND001', \
  workspace_root=Path('$SC/ws'), plugin_root=Path('$PR'), \
  candidate_set_path=Path('build/candidates/candidate_set.json'))"
```

> Finding: there is no CLI/MCP command that appends the reject experience row.
> `append_apply_record` is only called by `candidate_apply.apply_candidate`, which blocks a
> non-accept acceptance (`acceptance_not_accepted`) before reaching the append. The reject
> human-label signal is wired into `build_apply_records`/`_human_review_labels`, but driving
> it end-to-end still needs the direct `append_apply_record` call above. A thin
> `fig-agent log-reject` (or an append inside `accept-candidate` on reject) would close this.

## Step 4 — verify the three exit criteria

```bash
python3 - "$SC/exp/fig2_trap_design_space.jsonl" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
imp = sum(r["outcome"]["quality_movement"] == "improved" for r in rows)
rej = sum(r["outcome"]["human_label"] == "reject" for r in rows)
uns = sum(str((r["state"]["target"] or {}).get("subregion_key") or "").startswith("unstable:")
          for r in rows)
print("improved:", imp, "| reject:", rej, "| unstable keys:", uns)
assert imp >= 1 and rej >= 1 and uns == 0
print("ALL THREE CRITERIA MET")
PY
```

## Observed result (this run)

6 rows in `fig2_trap_design_space.jsonl`:

| candidate | quality_movement | human_label | detector_recheck | subregion_key |
|-----------|------------------|-------------|------------------|---------------|
| CAND002   | regressed        | accept      | failed · source_defect_unresolved | sha256:… |
| CAND001   | regressed        | accept      | failed · source_defect_unresolved | sha256:… |
| CAND003   | **improved**     | accept      | **success · source_defect_resolved** | sha256:… |
| CAND005   | regressed        | accept      | failed · source_defect_unresolved | sha256:… |
| CAND006   | regressed        | accept      | failed · source_defect_absent_pre_apply | sha256:… |
| CAND001   | regressed        | **reject**  | failed · source_defect_unresolved | sha256:… |

improved = 1, reject = 1, unstable keys = 0 → all three criteria met.
