# Architecture v0.3 — LLM Figure Quality Judgment

**Status:** Historical evidence — non-authoritative.
**Superseded by:** `docs/product-spec.md` and `docs/execution-plan.md`.

**Status at the time:** REJECTED (2026-05-08) — superseded by existing primary-source evidence in `examples/golden_trap_depth_picture/critique_adjudication.yaml:280-303`. Cheap intervention (briefing §7 + reference attached) already lifted `F1_w` from 0.244 → 0.981 (4.9× the §6 threshold of 0.15). Independent Codex + Gemini review both verdicted "needs re-design before implementation plan" with 6 / 4 BLOCKING issues respectively. Reviews preserved at `docs/trials/2026-05-08-figure-quality-spec-review-{codex,gemini}.md`. Draft text below preserved as a record of the brainstorming chain that led here; do not implement.

---

**Original Status:** DRAFT (2026-05-08)
**Trigger:** N=1 dogfood on `golden_trap_depth_picture` produced `P_w=0.31, R_w=0.20, F1_w=0.24` with one BLOCKER FN missed (polymer chain reads as wave, not chemistry). v1 rubric §6 cheap-experiment branch and follow-on N=3 catalog-stability run both confirmed the failure is structural, not prompt-tunable.
**Predecessor:** `critique-evaluation-rubric-v1.md` (rubric and metrics), `architecture-v0.2-proposal.md` §7 (auto-apply gate), `architecture-v0.3-briefing-semantic-grounding.md` (parallel deferred work)
**Historical product direction:** `quality-kernel-goal.md`, `session_strategic_direction_2026_05_04` (memory)
**Methodology basis:** Industry consensus 2026 — hybrid multidimensional rubrics + iterative bootstrap (RRD), Anthropic guidance "unit tests for correctness + LLM rubrics for overall quality", AdaRubric / Autorubric / Prometheus 2 / RubricEval line.

---

## 1. Problem Statement

`/fig_critique` v1 issues a single ungrounded vision call on the panel-level PNG and asks the LLM to "find what's wrong." Two failure modes are systematic:

1. **Drift toward generic style heuristics** — without grounding, the LLM replaces author intent with best-practice priors. N=1 dogfood: 7 of 11 findings were FP that, if applied, would have reverted deliberate decisions.
2. **Panel-average masks BLOCKER FN** — semantic defects in a single sub-region (e.g., polymer chain reads as wave) are diluted by surrounding correctly-rendered regions and never surface in the finding list.

Two layers of structural problem feed these failures:

- **No closed-set rubric.** The LLM is asked to *judge* quality, not to *detect* deviations from a named cue list. Judging is calibration-bound; detecting is closed-set.
- **No reference anchor that avoids lock-in.** A single reference causes idiom collapse (`snippet_anchoring_lock_in` memory); no reference causes drift. Multi-reference ordinal comparison is the only reference formulation that survives both.

This spec replaces the single panel-level vision call with a four-layer pipeline that separates deterministic measurement from LLM judgment, applies sub-region attention, and grounds figure-level assessment via multi-reference ordinal comparison.

## 2. Architecture Overview

`/fig_critique` becomes a four-layer orchestrator. Each layer has a distinct role and failure mode; same LLM may back multiple vision layers but with different formulations to avoid copying the same failure across layers.

```
L4.5a-deterministic       — bbox/pixel arithmetic, 0 LLM call
L4.5a-l6-surface          — L6 collision report → critique finding, 0 LLM call
L4.5a-vision-subregion    — per-region single-call, closed-set binary cues, N call/fixture
L4.5b-comparator          — full PNG + 3 ref → 5 axes ordinal, 1 call/fixture (optional)
```

Separation principle:

- **Detector ≠ judge.** Sub-region detector emits binary `pass/fail` per cue from a closed catalog. The LLM is not asked "is this region good?" — it is asked "does cue X hold?".
- **Comparator ≠ scorer.** Figure-level comparator emits ordinal cluster position per axis (which of 3 references is the rendered figure closest to). The LLM is not asked "score 1-10" — it is asked "rank against named neighbors."

Reuse map:

- `spec.yaml.subregions[*]` (new field) — sub-region bbox + optional `semantic_intent`
- `spec.yaml.comparator_refs[*]` (new field) — 3 external reference PNGs with cluster labels
- `coordinate_hints.yaml.structural_regions` (existing) — secondary input for deterministic arithmetic (chain_rows etc.), **not** the source of sub-region partitioning
- `critique.md` schema v1 → v2 (this spec)
- v1 rubric §3 metrics — applied per-layer + aggregate, decision rule (§6) restricted to vision_subregion layer only

Both new layers are report-only. Auto-apply gate (architecture-v0.2-proposal §7) remains closed until N≥5 fixtures pass.

## 3. Components

### 3.1 Sub-region detector — universal cue catalog (v0)

11 cues, partitioned by execution layer:

**L4.5a-deterministic (3 cues, bbox/pixel arithmetic):**
- `aspect_extreme` — sub-region aspect outside `[1:3, 3:1]` without `semantic_intent` justification
- `whitespace_imbalance` — one side ≥3× whitespace of opposite, computed from pixel distribution
- `panel_inner_squeeze` — title/caption pixel area exceeds 30% of region pixel area

**L4.5a-l6-surface (1 cue, L6 → critique elevation):**
- `axis_tick_overlap` — L6 collision report subset (filter by collision type). Existing collision check produced 39 candidates on N=1 fixture that critique never surfaced (FN001).

**L4.5a-vision-subregion (7 cues, true vision LLM territory):**
- `text_on_line` — label/equation visually overlaps plot line / axis / arrow
- `text_clipped` — intended label cut by boundary or clip
- `size_hierarchy_violated` — child label visually larger or bolder than parent
- `baseline_drift` — same column/row labels visually misaligned in baseline
- `leader_anchor_drift` — leader arrow base not anchored to data feature
- `arrow_crosses_data` — leader/evidence arrow traverses data curve when whitespace path exists
- `redundant_encoding` — same data dimension encoded by ≥2 of (color, shape, label) without justification

The split between deterministic and vision is hard: cues that bbox/pixel arithmetic can answer go deterministic; cues requiring semantic interpretation of glyphs go vision. Putting deterministic cues in vision inflates cost and noise.

### 3.2 Briefing semantic activation (per-region, optional)

Trigger: `spec.yaml.subregions[i].semantic_intent` field present.

```yaml
subregions:
  - id: row3_polymer_chain
    bbox: [x, y, w, h]                              # build PNG pixel space
    semantic_intent: "S-rich polymer chain의 chemistry가 wave가 아닌 분자 구조로 식별 가능해야 함"
```

Activation: when present, vision_subregion layer gets one additional binary cue — "rendered region satisfies semantic_intent?". When absent: only universal cues run; explicit prohibition of fallback to "general quality judgment" (this is the N=1 dogfood drift origin).

Author burden in v0.3: subregion bbox and semantic_intent are author-written. Automated extraction (briefing → semantic_intent) is deferred to a separate spec (`architecture-v0.3-briefing-semantic-grounding.md`).

### 3.3 Comparator — axes catalog (v0)

5 ordinal axes. Each axis: "current figure is closer to ref_A / ref_B / ref_C cluster" (3-way ordinal, no absolute score).

- `typography_density` — sparse ↔ dense
- `palette_count` — monochrome ↔ multi-hue
- `whitespace_distribution` — tight ↔ airy
- `annotation_layering` — flat ↔ multi-level
- `composition_grid` — free-form ↔ strict-grid

Reference source: `spec.yaml.comparator_refs[*]` with explicit cluster labels.

```yaml
comparator_refs:
  - path: <external nature-grade PNG>
    cluster: nature_grade
  - path: <external nature-grade PNG>
    cluster: nature_grade
  - path: <external mediocre PNG>
    cluster: mediocre
```

Hard constraint: paths must point outside `examples/<this-fixture>/` to prevent self-referential lock-in. Plugin enforces (reject if same fixture tree).

When `comparator_refs` absent: L4.5b skipped entirely; aggregate output flagged as degraded.

## 4. Data Flow + Schema v2

### 4.1 Orchestration phases

```
Phase 1 — Preflight
  critique_brief.py freshness + briefing + line-numbered .tex
  load spec.yaml.subregions, spec.yaml.comparator_refs
  load L6 collision report from last /fig_compile

Phase 2 — L4.5a-deterministic (0 LLM call)
  for each subregion bbox: compute aspect_extreme, whitespace_imbalance, panel_inner_squeeze
  → deterministic_findings[]

Phase 3 — L4.5a-l6-surface (0 LLM call)
  filter L6 collision report to axis-tick subset
  → l6_surface_findings[] (each tracks L6 collision_id)

Phase 4 — L4.5a-vision-subregion (N LLM call, N = subregion count)
  for each region: crop_subregion.py → build/_crops/<region_id>.png
  host Read tool on crop → prompt = 7 cue + (optional) semantic_intent
  → vision_subregion_findings[]

Phase 5 — L4.5b-comparator (1 LLM call, optional)
  if comparator_refs present:
    host Read on full PNG + 3 ref → prompt = 5 axes ordinal
  else:
    skip
  → axis_rankings[]

Phase 6 — Merge + Write
  aggregate → critique.md schema v2 (auto_verdict + adjudicated_verdict slot)
```

Sub-region cropping: new `scripts/crop_subregion.py`. Coordinates are **build PNG pixel space** (not reference image coordinate). build PNG dimensions read from PNG header; bbox validated against dimensions. Crops written to `build/_crops/<region_id>.png`, ephemeral, regenerated each critique run.

### 4.2 Schema v2

```yaml
schema: figure-agent.critique.v2
fixture: <name>
generated_at: <ISO-8601>
layers_run: [deterministic, l6_surface, vision_subregion, comparator]

auto_verdict:
  status: ready | revise | block
  rule: |
    block  if any layer has BLOCKER finding
    revise if any layer has MAJOR/MINOR finding OR comparator returns mediocre on ≥2 axes
    ready  otherwise
  layers_with_blockers: []
  axis_mediocre_count: 0

adjudicated_verdict:
  status: pass | fail | null
  rule: "BLOCKER FN=0 AND vision_subregion P_w≥0.6 AND vision_subregion R_w≥0.4"
  metrics:
    P_w: null
    R_w: null
    F1_w: null
    BLOCKER_FN_count: null
  filled_at: null

findings:
  - id: D001                          # prefix: D=deterministic, L=l6_surface, V=vision, C=comparator
    layer: deterministic
    sub_region_id: row3_polymer_chain
    cue_id: aspect_extreme            # category/severity_default/layer resolved via cue catalog
    severity: MAJOR
    observation: "..."
    suggested_fix: "..."
    evidence:
      bbox: [x, y, w, h]
      measured_ratio: 4.2
    status: open

  - id: V003
    layer: vision_subregion
    sub_region_id: row3_polymer_chain
    cue_id: size_hierarchy_violated
    severity: MINOR
    tex_lines: [42, 57]
    observation: "..."
    suggested_fix: "..."
    status: open

axis_rankings:                        # comparator output (only present if layer ran)
  - axis: typography_density
    position: ref_C                   # ref_A=nature1, ref_B=nature2, ref_C=mediocre
    evidence: "label density visibly higher than ref_A and ref_B"
```

### 4.3 Cue catalog file

`docs/critique-cue-catalog.yaml` — external lookup keyed on `cue_id`. RRD adds entries; finding schema does not change.

```yaml
schema: figure-agent.cue_catalog.v1
cues:
  - id: text_on_line
    category: label_placement
    layer: vision_subregion
    severity_default: MAJOR
    description: "..."
    added_at: 2026-05-08
    added_via_fixture: golden_trap_depth_picture
  - id: aspect_extreme
    category: proportion              # category list = v1's 6 + 'proportion'
    layer: deterministic
    severity_default: MINOR
    measurement: "bbox aspect ratio outside [1:3, 3:1] without semantic_intent"
    added_at: 2026-05-08
    added_via_fixture: <design>
```

Mapping rule: `cue_id` → `category` is 1:N (each cue in exactly one category). Severity weighting (BLOCKER=4 / MAJOR=2 / MINOR=1 / NIT=0.5) inherits from v1 rubric §1.1.

### 4.4 Backward compatibility

Spec.yaml polyfill matrix:

| spec.yaml state | layers run | result |
|---|---|---|
| `subregions` + `comparator_refs` | 4 layers | full v2 |
| `subregions` only | det / l6 / vision_subregion | comparator-less v2 |
| `comparator_refs` only | comparator + panel-level vision (1 region = full figure) | degraded |
| neither | panel-level vision only | v2 schema wrapping a single finding block, equivalent to v1 |

`critique_adjudication.yaml` v1 ↔ v2: finding ID matching is preserved (severity / category fields unchanged). Existing v1 critique.md files are not migrated in place; only new pipeline emits v2.

## 5. Testing — N=3 Trial Protocol

### 5.1 Fixture set (Q3 decision)

| Role | Fixture | Archetype | Rationale |
|---|---|---|---|
| Anchor | `golden_trap_depth_picture` | band/trap-depth | v1 rubric §6 baseline (`F1_w=0.244` panel-level vision) — only fixture with complete v1 adjudication YAML |
| Diversity 1 | `n3_trial_02_actuation_sequence` | process / temporal flow | independent archetype, surfaces flow-related FNs |
| Diversity 2 | `dogfood_power_law_trap_pipeline` | quantitative plot | independent archetype, surfaces proportion / tick FNs |

Normative constraint: future N=k expansion must satisfy §6 baseline anchor (1 fixture with v1 adjudication) **and** §4.2 archetype diversity (≥2 distinct archetypes) simultaneously. Single-archetype expansion is rejected even if k grows.

`fig3_trapping_concept` is excluded — `dogfood_fixture_quality_concern` (memory 2026-05-02) flags figure source defects independent of pipeline. Quality audit must precede any use as measurement instrument.

### 5.2 Per-fixture flow

```
1. /fig_compile <name>             # L6 collision report fresh
2. /fig_critique <name>            # v2 pipeline → critique.md v2 + auto_verdict
3. Author adjudicates              # TP/FP/AMB per finding, FN enumeration
                                    # → critique_adjudication.yaml v2 (per-layer breakdown)
4. score_critique.py               # per-layer + aggregate metrics
                                    # → critique_score.yaml
5. Author fills adjudicated_verdict # post-hoc, writes back into critique.md
```

### 5.3 Per-layer success thresholds

| Layer | Primary metric | Threshold | Failure interpretation |
|---|---|---|---|
| L4.5a-deterministic | Precision (closed set, no FN) | ≥0.90 | Arithmetic bug → algorithm fix |
| L4.5a-l6-surface | Recall vs L6 collision report | ≥0.95 | L6 → critique elevation broken → orchestration fix |
| L4.5a-vision-subregion | `P_w`, `R_w` | `P_w≥0.6` AND `R_w≥0.4` | cue catalog gap → RRD pass |
| L4.5b-comparator | per-axis match count (LLM ordinal == author ordinal) | ≥10 of 15 (5 axes × 3 fixture) | axis definition or ref selection inadequate |

### 5.4 §6 decision rule (vision_subregion layer only)

```
Baseline (v0.2 ungrounded panel-level vision): F1_w = 0.244
Trial (v0.3 vision_subregion layer only):       F1_w = ?

ΔF1_w ≥ 0.15 absolute   → v0.3 hypothesis confirmed. RRD 1 pass sufficient.
ΔF1_w 0.05 – 0.15        → partial improvement. RRD continues to next fixture batch.
ΔF1_w < 0.05             → structural failure. Sub-region / comparator hypothesis re-examined.
BLOCKER FN > 0           → automatic fail regardless of ΔF1_w.
```

Decision rule input is intentionally restricted to `vision_subregion` layer F1_w. Aggregate F1_w across all 4 layers would be inflated by deterministic + L6 free-precision and is informational only. Same population (vision LLM judgment) is preserved against v1 baseline for honest comparison.

### 5.5 Stability gate (§4.2 variance)

Across 3 fixtures, vision_subregion layer `Var(F1_w) < 0.15`. Violation → identify which fixture is over/under-performing; isolate cue catalog overfit (anchor-specific cue) from fixture idiosyncrasy.

### 5.6 Cost & latency (priori, trial corrects)

- vision call/fixture: ~5 region × 1 call (per-region cue bundle) + 1 comparator = ~6 call/fixture
- N=3 → ~18 vision call total; deterministic + L6 are 0 call
- subscription token (no external API), latency target: 5–10 min wall time / fixture
- Author burden split: anchor 2-3h (warm, prior adjudication exists) / each diversity 4-6h (cold start) → **2-3 day distributed**

Cost / time targets are priori and revised post-trial in `critique_score.yaml`.

## 6. Open Issues & Flag Triage

### 6.1 Decision flags carried from brainstorming

| Flag | Origin | Resolution timing | Plan |
|---|---|---|---|
| **A** | §3.2 polyfall ban vs RRD conflict | post-trial | semantic FN triage step in plan: (1) generalizable as universal cue → catalog add / (2) region-local meaning → spec.yaml.semantic_intent. Author decides per FN |
| **B** | §3.3 comparator_refs author burden | spec authoring | hard constraint: refs must be external (path outside fixture tree); plugin rejects self-referential. cluster label required |
| **C** | §5.3 comparator Spearman ρ at N=3 | trial | N=3 uses per-axis match count (15 binary). ρ gate activates at N≥10. score_critique.py implements both, default = count |
| **D** | §5.6 author burden time budget | plan | per-fixture split (anchor 2-3h, diversity 4-6h each). 1-day gate removed |

### 6.2 v1 carry-over limitations

- Single-rater adjudication: v0.3 trial is author self-adjudication. Inter-rater κ unmeasured. Output explicitly labeled "directional honesty, not statistical defensibility."
- Correct Skip not enumerated: P_w upward-biased; trial caveat documented.
- Severity subjectivity: BLOCKER vs MAJOR is judgment. adjudication YAML `note` field reasoning is mandatory.

### 6.3 v2-new limitations

- subregion bbox author burden: automated extraction deferred to `/fig_extract` panel-level extension (separate spec).
- cue catalog version control: catalog is git-tracked; each addition records `added_at` and `added_via_fixture`. Catalog schema bumps maintain v1↔v2 compatibility matrix.
- reference image staleness: `comparator_refs` are external PNGs; nature-grade visual standard drifts. Refs older than 1 year reviewed at trial re-execution.
- cost / latency unmeasured: §5.6 figures are priori; trial corrects.

### 6.4 Future scope (separate specs)

| Item | Trigger | Scope |
|---|---|---|
| `/fig_extract` panel-level bbox auto-extraction | post N=3 trial pass | vtracer + heuristic → spec.yaml.subregions auto-fill |
| Auto-apply gate | N≥5 fixtures, P_w≥0.8 (architecture-v0.2-proposal §7) | findings → .tex auto-patch; report-only lifted |
| Multi-rater calibration | end of dogfood phase | ≥2 raters / fixture, weighted κ ≥0.75 |
| Comparator axis expansion | post-trial axis match distribution | add axes (data-ink ratio, narrative flow); axis lifecycle separate from cue RRD |
| Briefing semantic automation | v0.3 separate spec | briefing.md → spec.yaml.semantic_intent extraction (Flag A's (1) branch automation) |

### 6.5 Out of scope (intentional)

- Absolute quality score (1-10): comparator emits ordinal only, by design.
- LLM auto-apply: blocked until §7 gate.
- Non-vision modalities (audio, 3D): outside figure-agent.
- Cross-author critique: single-author dogfood only.

## 7. Decision History (this brainstorming session)

| Decision | Choice | Reason |
|---|---|---|
| Q1 scope | Hybrid (sub-region detector + figure-level comparator + final critique) | User intuition + N=1 panel-average mask BLOCKER FN |
| Q2 grounding strategy | Hybrid (universal + briefing semantic, RRD-iterative) | `/decide` industry consensus 2026 — universal-only diverges 20-30% from human, pure semantic premature without calibration |
| Q3 fixture set | golden_trap_depth_picture + n3_trial_02 + dogfood_power_law | §6 baseline anchor + §4.2 archetype diversity dual constraint |
| §2 cropping | per-region single-call (β) | sub-region attention enforcement is the design's core lever |
| §2 cue partition | 3 deterministic + 1 L6-surface + 7 vision | offload to deterministic where bbox/pixel arithmetic suffices |
| §3 cue catalog | external file `docs/critique-cue-catalog.yaml` | finding schema does not shake under RRD additions |
| §3 verdict | split `auto_verdict` (output time) + `adjudicated_verdict` (post-adjudication) | v1 single verdict masked BLOCKER FN; P_w/R_w only available post-adjudication |
| §4 decision rule input | vision_subregion layer F1_w only | aggregate F1_w inflated by free-precision layers; population mismatch with v1 baseline |

## 8. Sources (industry calibration)

- Adnan Masood, _Rubric-Based Evaluations & LLM-as-a-Judge — Methodologies, Biases, and Empirical Validation in Domain-Specific Contexts_ (Apr 2026): https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80
- _Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks_ (RRD), arXiv 2602.05125: https://arxiv.org/html/2602.05125
- _Autorubric: A Unified Framework for Rubric-Based LLM Evaluation_, arXiv 2603.00077: https://arxiv.org/html/2603.00077v1
- _AdaRubric: Task-Adaptive Rubrics for LLM Agent Evaluation_, arXiv 2603.21362: https://arxiv.org/html/2603.21362v1
- Monte Carlo Data, _LLM-As-Judge: 7 Best Practices_: https://www.montecarlodata.com/blog-llm-as-judge/

---

_v0.3 spec authored 2026-05-08 from session brainstorming chain (Q1 → Q3, §1 → §5). Each section presented to user, advisor-verified, revised inline. Trial fixtures and per-layer thresholds are v0.3-only; v0.4+ tightens once N≥5 calibration data exists._
