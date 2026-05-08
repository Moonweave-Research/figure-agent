# Critique Evaluation Rubric v1

**Status:** DRAFT (2026-05-04)
**Purpose:** define how findings produced by L4.5 `/fig_critique` are scored, so that "is this critique loop useful" becomes a quantitative question with a defensible answer.
**Trigger:** N=1 dogfood on `golden_trap_depth_picture` initially scored at "18% accuracy" using reference-match. Advisor flagged this as the wrong measurement: reference can be wrong, missed findings aren't counted, and ambiguous author-intent cases get binarized to FP. This rubric replaces reference-match with a precision/recall framing aligned with 2026 LLM-as-judge industry consensus.
**Industry calibration target:** 75–90% human-judge agreement against a golden adjudicated dataset before scaling (Evidently AI / Monte Carlo / Anthropic 2026 guidance).

---

## 1. Categories

Every finding produced by `/fig_critique`, plus every reader-observed issue that critique *did not* produce, is sorted into one of five buckets.

| Bucket | When applies | Counted in |
|---|---|---|
| **TP** True Positive | Finding identifies a real issue. Applying the suggested fix improves the figure (or at minimum doesn't harm). | Precision numerator |
| **FP** False Positive | Finding flags a non-issue. Applying the suggested fix harms the figure or replaces author intent with generic style heuristic. | Precision denominator (only) |
| **AMB** Ambiguous | Finding identifies something whose correctness depends on author intent that isn't documented. Applying or rejecting both defensible. | Reported separately; default-weighted 0.5 in both numerator and denominator |
| **FN** False Negative | A real issue exists in the rendered figure that critique did *not* flag. Identified by author / reader review. | Recall denominator |
| **CS** Correct Skip | A non-issue that critique correctly did not flag. Implicit, not enumerated; tracked only for completeness in calibration analysis. | Excluded from primary metrics |

### 1.1 Severity weighting

Each finding (TP/FP/AMB) and each missed issue (FN) carries a severity inherited from the critique schema (BLOCKER / MAJOR / MINOR / NIT). Severity-weighted variants of the metrics multiply each item by:

```
BLOCKER = 4
MAJOR   = 2
MINOR   = 1
NIT     = 0.5
```

Unweighted metrics are reported alongside severity-weighted ones; both are needed because (a) high-severity drift is the real risk signal, (b) NIT inflation should not mask a missed BLOCKER.

### 1.2 Required visual-defect subcategories

Every `/fig_critique` pass must explicitly check `label_placement`, even when
the rendered PDF compiled without geometric text-bbox collisions. The current
visual-clash checker can surface these as `text_on_path`, `text_on_fill`,
`near_miss`, or `clipped_text`, but the critique rubric owns the reader-facing
classification.

Required subcategories:

| Subcategory | Count as issue when | Default severity |
|---|---|---|
| `label_placement.text_on_line` | A label, equation fragment, or callout text visually sits on a plotted data trace, axis line, dashed reference line, or arrow so the reader cannot cleanly separate annotation from geometry. | MAJOR if semantic label or curve identity is affected; NIT if readable with backing/clearance. |
| `label_placement.label_clipped` | Any intended label is cut by a plot box, figure boundary, scope clip, or export crop. | MAJOR; BLOCKER if the missing part changes the equation/label meaning. |
| `label_placement.annotation_crosses_data` | A leader arrow or evidence arrow traverses a data curve, lobe, or dense glyph region when it could start at the plot edge or route through whitespace. | MAJOR if it obscures data; MINOR if only visually noisy. |

Accepted or ship-blessed fixtures may not treat these as cosmetic simply
because `check_collisions.py` reports zero bbox collisions. A critique that
misses any reader-visible instance is recorded as an FN under this rubric.

## 2. Adjudication protocol

### 2.1 Single-author baseline (current state)

For v0.3 development, the figure author is the sole adjudicator. Each finding gets one label by the author. Inter-rater agreement is **not measurable at N=1 author** and is acknowledged as the v0.3 metric's main weakness.

### 2.2 Multi-rater target (post-v0.3)

When figure-agent matures past the dogfood phase, the calibration target tightens:
- ≥2 independent raters per fixture
- weighted κ or Krippendorff's α reported
- ≥0.75 inter-rater agreement before any auto-apply gate is opened

Until that infrastructure exists, single-rater scores are explicitly labeled as such.

### 2.3 Adjudication output format

Per fixture, write `examples/<name>/critique_adjudication.yaml`:

```yaml
schema: figure-agent.critique_adjudication.v1
fixture: <name>
adjudicated_at: <ISO-8601>
adjudicator: author
critique_run_id: <iter or session id>

findings_produced:    # one entry per finding from /fig_critique
  - id: C001
    category: TP | FP | AMB
    severity: BLOCKER | MAJOR | MINOR | NIT
    note: "<one-line author rationale>"

findings_missed:      # one entry per FN — issue critique did not produce
  - id: FN001
    severity: BLOCKER | MAJOR | MINOR | NIT
    description: "<what was wrong, observable in PNG>"
    note: "<one-line>"
```

## 3. Primary metrics

Given a critique run with adjudicated labels:

```
P_unweighted = TP / (TP + FP + 0.5 * AMB)
R_unweighted = TP / (TP + FN)
F1           = 2 * P * R / (P + R)

P_weighted   = Σ severity(TP) / Σ severity(TP+FP+0.5·AMB)
R_weighted   = Σ severity(TP) / Σ severity(TP+FN)
F1_weighted  = 2 * P_w * R_w / (P_w + R_w)
```

Reported as a 6-tuple: `(P_uw, R_uw, F1_uw, P_w, R_w, F1_w)`.

### 3.1 What replaces "18% accuracy"

The original 18% number = reference-match rate = (kept-after-revert) / (proposed). It conflated two failure modes (drift away from reference, vs. reference-was-wrong) and ignored a third (FNs). The new replacement reports `(P, R, F1)` triples plus the AMB count separately. Direct comparison: 18% had no R component at all.

## 4. Pass/fail gates

### 4.1 Per-fixture critique run

| Gate | Threshold | Severity-weighted? | Failure means |
|---|---|---|---|
| Useful precision | `P_w ≥ 0.6` | yes | Findings cause more drift than improvement; critique is net-negative |
| Coverage | `R_w ≥ 0.4` | yes | Critique misses too many real issues; not catching major defects |
| BLOCKER FN count | `0` | strict | Any missed BLOCKER is automatic gate fail regardless of other scores |

These are v0.3 gates — looser than v0.2's §7 (≥80%) because the underlying capability is being built. Tighten only when calibrated.

### 4.2 Across-fixture stability

A single fixture's score isn't enough. Stability requirement:
- N≥3 fixtures must report `(P_w, R_w)` independently
- Variance of `F1_w` across fixtures `< 0.15` (i.e., critique behaves consistently)

If high variance, schema or critique brief is overfit to one fixture.

## 5. N=1 baseline: `golden_trap_depth_picture` (v0.2 ungrounded)

This section adjudicates the N=1 dogfood findings under the new rubric.

### 5.1 Findings produced (11)

| ID | Category | Severity | Note |
|---|---|---|---|
| C001 (remove bottom g(E_t)) | **TP** | MINOR | Author override: reference was wrong, removal is correct |
| C002 (shorten Debye text) | FP | MINOR | Reference has full text intentionally; shortening drifts |
| C003 (caption lift) | FP | NIT | Original position matched reference; tweak unnecessary |
| C004 (lobe label peak align) | FP | NIT | Original anchor matched reference |
| C005 (Energy axis extension) | FP | NIT | Original short axis matched reference |
| C006 (drop inline Debye) | FP | MINOR | Compounds C002 drift; reference has annotation |
| C007 (arrow re-route to brace) | **TP** | MINOR | Improves parallelism with Row 2/3 arrows |
| C008 (title outside box) | **TP** | NIT | Matches reference convention + Row 3 pattern |
| C009 (add Σ=∫ chain arrow) | **AMB** | MINOR | Reference has no arrow but author intent (intentional gap vs oversight) is unverified |
| C010 (add `(single τ)` clarifier) | FP | MINOR | Reference has plain τ_d; clarifier adds noise |
| C011 (add shallow ellipsis) | FP | NIT | Asymmetry was deliberate per reference |

### 5.2 Missed issues (FN, observed by author 2026-05-04)

| ID | Severity | Description |
|---|---|---|
| FN001 | MAJOR | x-axis tick label overlap on power-law and Debye plots — L6 reports 39 collision candidates, critique didn't surface |
| FN002 | BLOCKER | Polymer chains read as featureless waves, not chemical structure (reader cannot infer "S-rich polymer") |
| FN003 | MAJOR | "S-rich segments" dashed-box highlight does not communicate semantic meaning |
| FN004 | MINOR | Arrow overlap near band-gap region |
| FN005 | MINOR | shallow/deep lobes have wrinkled/irregular shape from poor TikZ control points |

### 5.3 v0.2 ungrounded baseline scores

```
TP  = 3   (C001, C007, C008)
FP  = 7   (C002, C003, C004, C005, C006, C010, C011)
AMB = 1   (C009)
FN  = 5   (FN001-FN005)

P_uw  = 3 / (3 + 7 + 0.5)     = 3 / 10.5  = 0.286
R_uw  = 3 / (3 + 5)            = 3 / 8     = 0.375
F1_uw = 2·0.286·0.375 / (0.286+0.375) = 0.324

severity weights:
  TP  : C001 (1) + C007 (1) + C008 (0.5)            = 2.5
  FP  : C002 (1) + C003 (0.5) + C004 (0.5) + C005 (0.5) + C006 (1) + C010 (1) + C011 (0.5) = 5.0
  AMB : C009 (1)                                     = 1.0
  FN  : FN001 (2) + FN002 (4) + FN003 (2) + FN004 (1) + FN005 (1) = 10.0

P_w   = 2.5 / (2.5 + 5.0 + 0.5)        = 2.5 / 8.0  = 0.313
R_w   = 2.5 / (2.5 + 10.0)             = 2.5 / 12.5 = 0.200
F1_w  = 2·0.313·0.200 / (0.313+0.200) = 0.244
```

Baseline 6-tuple: `(P_uw=0.29, R_uw=0.38, F1_uw=0.32, P_w=0.31, R_w=0.20, F1_w=0.24)`.

**One BLOCKER FN exists (FN002 polymer chains).** Per § 4.1, this alone is an automatic gate fail under v0.3 rules.

### 5.4 Comparison to old "18% accuracy"

| Metric | Value | What it captures |
|---|---|---|
| Old reference-match | 18% (2/11) | "How many findings survived reference comparison" — confounds drift with reference defects |
| New `P_uw` | 28.6% | "Of findings produced, how many are useful" |
| New `R_uw` | 37.5% | "Of issues that exist, how many critique caught" |
| New `F1_uw` | 32.4% | Combined balance |
| New `F1_w` | 24.4% | Severity-weighted — penalizes BLOCKER FN heavily |

The new metrics are **less alarming** than the old (28.6% vs 18%) on the precision axis but **more alarming** when severity weighting is applied (24.4% F1_w). The BLOCKER FN on polymer chains is now visible — it was invisible to the old metric.

## 6. Implications for the cheap experiment

The cheap experiment (advisor recommendation: richer briefing + reference attached) will produce a new critique run. Adjudicate findings using this rubric, score against the same 5.3 categories, compute the new 6-tuple. Compare:

```
v0.2 ungrounded: (P_uw=0.29, R_uw=0.38, F1_uw=0.32, P_w=0.31, R_w=0.20, F1_w=0.24)
v0.2 + briefing addendum + reference attached: (?, ?, ?, ?, ?, ?)
```

Decision rule:
- If `F1_w` improves by ≥0.15 absolute (≈60% relative): the cheap intervention closes most of the gap. v0.3 schema layer NOT justified by current evidence.
- If `F1_w` improves by 0.05–0.15: partial improvement. v0.3 schema may still help but priority drops.
- If `F1_w` improvement <0.05: cheap intervention insufficient. v0.3 schema layer justified. **And** BLOCKER FN must be addressed regardless (it's an L0 / L1 problem, not L4.5).

### 6.1 Plateau criterion — v0.3.0 ship vs schema-layer trigger (added 2026-05-08)

The cheap experiment outcome on `golden_trap_depth_picture` (recorded in `examples/golden_trap_depth_picture/critique_adjudication.yaml:280-303`) was `grounded_F1_w = 0.981` (4.9× the §6 threshold). Per the adjudication's `decision_outcome`, the cheap intervention ships as v0.3.0 and the schema layer (briefing_semantic.yaml) is deferred until N≥2 plateau is verified.

**Plateau definition (single fixture, second occurrence):**

```
Run /fig_critique on a second fixture (≠ golden_trap_depth_picture) with cheap intervention active
(briefing §7 + spec.yaml.reference_image).
Adjudicate per §1, score per §3.

  grounded_F1_w  ≥ 0.9       → plateau confirmed
                                v0.3.0 ship declared complete
                                schema layer permanently deferred
                                (architecture-v0.3-briefing-semantic-grounding.md may close)

  grounded_F1_w  < 0.9       → cheap intervention insufficient on archetype-2
                                schema layer trigger active
                                advisor pass to determine whether gap is content-specific
                                (one-off, document and re-test on archetype-3)
                                or methodology-level (open schema layer for implementation)
```

**Why `F1_w ≥ 0.9` (not 0.85, not improvement-relative):**

- `golden_trap_depth_picture` set the bar at 0.981. A 0.9 floor is conservative against that established margin while leaving 0.08 headroom for archetype-specific noise.
- `F1_w ≥ 0.85` would risk false-positive plateau when the second fixture is on a downward trend (e.g., 0.981 → 0.86 hides a real degradation).
- Reusing `improvement_absolute ≥ 0.15` (§6 rule) lacks an absolute floor; it allows e.g. `0.244 → 0.40` to qualify as plateau, masking poor performance on the downstream-comparable metric.
- The user-confirmed threshold (advisor option α, recorded in memory `project_v0_3_figure_quality_spec_rejected`).

**Open: which fixture is N=2?**

Not decided in this rubric. Candidates with archetype diversity from `golden_trap_depth_picture` (band/trap-depth):

- `n3_trial_02_actuation_sequence` — process / temporal-flow archetype
- `dogfood_power_law_trap_pipeline` — quantitative plot archetype
- `fig1_overview_v2` — composite overview archetype (active session work)

Selection deferred to next session. Whichever is chosen requires briefing §7 retrofit before `/fig_critique` runs (cheap-intervention payload).

**Trigger flow (when `F1_w < 0.9`):**

1. Author records the metric in fixture's `critique_adjudication.yaml` under `gate_status_grounded`
2. Advisor pass: classify gap as content-specific or methodology-level
3. If methodology: re-open `architecture-v0.3-briefing-semantic-grounding.md` and proceed to implementation plan via `superpowers:writing-plans`
4. If content-specific: document the divergence, re-test on a third archetype before promoting any architecture change

This criterion replaces the rejected `architecture-v0.3-llm-figure-quality-judgment.md` decision rule. The rejected spec proposed targeting the same vision-LLM judgment problem with a heavier 4-layer pipeline; the §6.1 criterion makes the lighter cheap-intervention path the v0.3.0 ship target with an explicit trigger for the heavy path if it fails.

## 7. Open issues

1. **Single-rater limitation acknowledged.** All v0.3 scores are author-self-adjudicated. Real industry calibration requires ≥2 raters. v0.3 isn't claiming statistical defensibility; it's claiming directional honesty.

2. **AMB threshold subjective.** "Author intent unverified" is itself a judgment. Consider a richer 5-step Likert ("definitely TP" → "leaning TP" → "ambiguous" → "leaning FP" → "definitely FP") if AMB count grows >20% of findings.

3. **FN identification depends on reader review.** Critique doesn't know what it doesn't know. If author/reader doesn't catch FN at adjudication time, it stays uncounted. Cross-reference against L6 collision report and lint output to surface candidate FNs that critique missed.

4. **Severity assignment subjective.** BLOCKER vs MAJOR is a judgment call; document the reasoning in the adjudication YAML.

5. **`Correct Skip` not enumerated.** A "perfect critique" would skip 100s of non-issues per fixture. Without enumerating CS, precision is biased upward. Practical compromise: don't enumerate; note as known confounder.

---

_v1 rubric authored after advisor review of v0.2 N=1 dogfood. Calibrates the cheap-experiment decision rule. Industry alignment: rubric-first methodology per Evidently AI, Monte Carlo Data, Anthropic 2026 guidance, and the RubricEval / Prometheus / JudgeBench line of 2024–2026 research._
