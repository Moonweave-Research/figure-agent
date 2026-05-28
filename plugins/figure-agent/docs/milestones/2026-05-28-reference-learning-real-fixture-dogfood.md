# Issue 63 Real-Fixture Dogfood

Status: pass with host-critique follow-up pending

Fixture: `n3_trial_02_actuation_sequence`

## Purpose

Dogfood the v0.8.1 reference-learning path on a real fixture without changing
figure source, accepted/golden state, exports, or SVG polish artifacts.

This run checks whether a reference can act as a bounded style-class anchor
instead of a copy target, and whether non-model aesthetic metrics surface useful
loop evidence without bypassing normal critique gates.

## Setup

Added `examples/n3_trial_02_actuation_sequence/critique_reference_pack.yaml`.

The pack declares:

- `reference_learning.schema: figure-agent.reference-learning.v1`
- reference: `reference/codex_gen_v1.png`
- allowed transfer:
  - restrained scientific illustration tone;
  - balanced ink density across three actuation stages;
  - compact label hierarchy;
  - clear stage-to-stage visual rhythm.
- forbidden transfer:
  - copy component topology;
  - introduce unbriefed hardware or materials;
  - override the left-to-right actuation story;
  - treat pixel similarity as a quality target.

## Commands And Evidence

Pack validation:

```bash
uv run python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from critique_reference_pack import load_reference_pack
p = Path('examples/n3_trial_02_actuation_sequence/critique_reference_pack.yaml')
pack = load_reference_pack(p)
print(pack['schema'])
print(pack['reference_learning']['schema'])
print(len(pack['reference_learning']['references']))
PY
```

Result:

- `figure-agent.critique-reference-pack.v1`
- `figure-agent.reference-learning.v1`
- `1`

Compile:

```bash
bash scripts/compile.sh examples/n3_trial_02_actuation_sequence/n3_trial_02_actuation_sequence.tex
```

Result:

- Style Lock: one WARN, `flagship_macros_unused`
- collision check: OK
- text-boundary check: OK
- label-path proximity check: OK
- visual clash candidates serialized to `build/visual_clash.json`
- build PDF/PNG refreshed

Metrics:

```bash
uv run python scripts/reference_aesthetic_metrics.py examples/n3_trial_02_actuation_sequence
```

Result: `measured: wrote build/reference_aesthetic_metrics.json`

Metric summary:

```json
{
  "comparison_count": 1,
  "state": "measured",
  "metrics": {
    "coarse_silhouette_occupancy_delta": 0.0,
    "dominant_hue_family_count_delta": 4.0,
    "edge_density_delta": 0.03263,
    "ink_density_delta": 0.040027,
    "line_density_proxy_delta": 0.148538,
    "palette_histogram_distance": 0.108877
  }
}
```

`/fig_status` equivalent:

```bash
uv run python scripts/status.py n3_trial_02_actuation_sequence --json
```

Observed:

- `render_state: FRESH`
- `critique_state: STALE`
- `reference_aesthetic_metrics: warning`
- note: `reference_aesthetic_metrics_warning`
- next action remains `/fig_critique n3_trial_02_actuation_sequence`

`/fig_loop` equivalent:

```bash
uv run python scripts/fig_loop.py n3_trial_02_actuation_sequence \
  --goal 'dogfood Issue 63 reference-learning metrics after fresh compile' \
  --json
```

Observed:

- `final_stop_reason: status_action_required`
- `next_action_summary.action: run_critique`
- `reference_aesthetic_metrics_summary.evaluation_state: warning`
- `warning_metric_count: 1`
- warning metric:
  - `dominant_hue_family_count_delta`
  - value `4.0`
  - threshold `2.0`
- no severe metric, no release bypass, no hidden source edit.

Brief generation:

```bash
uv run python scripts/critique_brief.py examples/n3_trial_02_actuation_sequence \
  | rg -n "schema: figure-agent.critique|rubric_version:|Reference Learning Contract|Reference Aesthetic Metrics|unintended_visible_anomaly|critique_input_hash|Evaluation state|Severe metric count|Blocking items|Warning metrics"
```

Observed:

- `## Reference Learning Contract`
- `## Reference Aesthetic Metrics`
- `Evaluation state: warning`
- `Severe metric count: 0`
- `schema: figure-agent.critique.v1.13`
- `rubric_version: figure-agent.critique-rubric.v1.13`
- `critique_input_hash: sha256:10434ffea6b7822fcb5bee9a25ef5ae0504c0b64f727e059cf105ba97bcefac6`
- `unintended_visible_anomaly` contract present for the v1.13 brief

## Judgment

Useful.

The fixture proves the intended v0.8.1 behavior:

- The reference pack is opt-in and explicitly bounded against copy-target
  misuse.
- Metrics are generated locally from existing build/reference images.
- The non-model metric signal is visible in `/fig_status`, `/fig_loop`, and
  the critique brief.
- A warning-level aesthetic-class divergence does not bypass stale critique,
  accepted/golden, export, or release gates.
- The next action remains critique refresh, which is the correct human/host LLM
  handoff point.

## Remaining Follow-Up

Run host `/fig_critique n3_trial_02_actuation_sequence` in Claude after restart
so the v1.13 critique can inspect the reference-learning contract, the warning
metric, high-zoom crops, and unintended-visible-anomaly fields.

Do not treat the warning metric as a defect by itself. It is a suspicion signal:
the host critique should decide whether the hue-family count difference is an
intentional simplification, a style drift, or a real journal-tone mismatch.

No source `.tex`, accepted/golden state, exports, or SVG polish files were
intentionally modified by this dogfood slice.
