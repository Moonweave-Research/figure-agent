# Instrumented Dogfood-Driven Ceiling-Raising Meta-Loop — Design Spec v1

**Status:** Proposed (design-only). Supersedes the framing in [[session_holistic_review_2026_06_25]]. Backed by [[project_techstack_direction_2026_06_21]] canonical spec.
**Branch context:** builds on Slice 0 + Slice 1 (candidate_generator geometry-aware candidates; `line_weight_tier.py` / `gradient_depth_fill.py` value-preserving levers).
**Authoring rule applied:** Every adversarial-critic correction overrides the conflicting lens. The 10 corrections are integrated and each is flagged inline as **[CORR-n]**.

---

## 1. Thesis

This is a **meta-loop that sits on top of the existing verify-only figure loop and makes "why it stopped" a first-class, code-proven, per-sub-region output** — so that the dominant cause of premature stopping ("적당히 멈춤") is *measured on real figures*, not assumed, then dispatched to the faculty (eye / hand / gate) that can actually move it. The single sentence of intent: **push the autonomy frontier outward and the quality ceiling upward at the same time — by killing premature stopping and weak judgment — where the human gate is a moving frontier that retreats only behind a deterministic verifier that fails loud, and every claim of "improved" or "safe-to-auto-apply" is empirically earned through dogfooding rather than declared.**

---

## 2. Principles / Non-Negotiables

1. **Dogfood-diagnoses, never assumes.** The four stop-causes are a *diagnostic vocabulary*, not an answer. The system emits `dominant_premature_cause` as an empirical argmax over real runs. No facet may presuppose its own faculty is the bottleneck. *(Hand facet's own open-question — "is lever-exhaustion even dominant?" — is structurally honored: lever modules are gated on a measured `lever_exhausted` count.)*

2. **Every autonomy advance rides a loud verifier.** A class/region only moves from human-required to auto-apply when a *deterministic* check (compile rc==0, semantic recheck, value-preserving verifiers, palette lint) passed on real applies and a demotion fires automatically on the next failure. No env-var, no flag, no in-memory channel — autonomy is sourced only from a human-counter-signed artifact validated like `semantic_review.json` (`semantic_candidate_review._invalid_reasons`). **[CORR-3]**

3. **No fake autonomy.** A green test cannot create evidence. Evidence rows are built only from real `apply_result.json` artifacts that themselves required a real compile + export + *semantic* recheck on a real figure. **[CORR-2]**

4. **~18% is a floor to beat, not a cap.** Reference-free absolute LLM taste measured ~18% ([[session_dogfood_n1_critique_failure]]). The eye fix-mode replaces *absolute scoring* with *anchored pairwise* judgment whose winner must survive a deterministic recheck — and reports `pairwise-winner-survival-rate` against the 18% baseline so the grounding's value is measured, not asserted.

5. **Build what dogfood reveals.** The diagnoser ships first. Fix-modes (Facet C ratchet, Hand lever-breadth, amortize bank) ship as **evidence-gated stubs**: a read-only counter measures the cause; the heavy machinery is built only after the counter proves the cause material. **[CORR-9]** This matches how Plan 4 was quarantined ([[project_plan4_roadmap]]).

6. **Clean ≠ done; within-threshold ≠ done.** `evaluation_state == "passed"` means only "measured, no warning/severe divergence" (`reference_aesthetic_metrics.py:444`). The ceiling metric must measure distance-to-*premium* (anchored to the one accepted figure fig1), not distance-to-warning. **[CORR-6]**

7. **A real per-sub-region unit must exist before any per-region facet ships.** `quality_defect_ledger._explicit_target` collapses everything to the literal `"label-a"` (`scripts/quality/quality_defect_ledger.py:122,126,127,304`). This is a **Slice-0 blocker**, not a deferred question. **[CORR-1]**

---

## 3. Architecture

```
                         ┌───────────────────────────────────────────────────────┐
                         │  EXISTING verify-only loop  (scripts/fig_loop.py)       │
                         │  run_loop → loop_decision → _apply_*_stop chain          │
                         │  → iteration_001.json + run_manifest.json                │
                         └───────────────────────────┬───────────────────────────┘
                                                     │ (read-only over loaded state)
                              ┌──────────────────────▼─────────────────────────┐
   SLICE-0 PRECONDITION ───▶  │  REAL SUB-REGION KEY  [CORR-1]                    │
   quality_defect_ledger      │  _explicit_target → (panel, selector_sha256)     │
   _explicit_target           │  else (panel, defect_class, ordinal)             │
                              └──────────────────────┬─────────────────────────┘
                                                     │
        ┌────────────────────────────────────────────▼────────────────────────────────────────┐
        │  STOP-POINT DIAGNOSER   scripts/loop/stop_cause_classify.py + fig_loop_stop_diagnoser  │
        │  runs on TERMINAL_STOPS superset (incl. aesthetic-lever & basin-rerouted)  [CORR-5]    │
        │  per sub-region S → classify_stop_cause(S, bundle)                                      │
        │  ONE lowercase enum: {gate_capped, lever_exhausted, decision_weak,                     │
        │                       headroom_blind, settled_verified, plumbing_stop, not_stopped}    │
        └───────────────────────────────────────────┬───────────────────────────────────────────┘
                                                     │ stop_report.json (v1)
                              ┌──────────────────────▼─────────────────────────┐
                              │  ROUTER  scripts/loop/fig_loop_stop_router.py    │
                              │  pure cause → fix-mode dispatch (data-only)      │
                              └───┬──────────┬──────────┬──────────┬────────────┘
                  gate_capped │   lever_exh. │  decision_weak │  headroom_blind │
                              ▼              ▼                ▼                 ▼
                   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                   │ GATE fix-mode│ │ HAND fix-mode│ │ EYE fix-mode │ │ EYE fix-mode │
                   │ (frontier    │ │ (lever       │ │ (pairwise +  │ │ (raise       │
                   │  ratchet, C) │ │  registry)   │ │  reference,B)│ │  ceiling, B) │
                   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                          │ all applies route through ▼                       │
                   ┌──────────────────────────────────────────────────────────────┐
                   │ APPLY SPINE  candidate_apply.apply_candidate                    │
                   │ sha256-drift + O_EXCL + rollback.patch + compile +             │
                   │ SEMANTIC recheck [CORR-2] + CLASS_VERIFIERS [CORR-3]           │
                   └──────────────────────────┬───────────────────────────────────┘
                                              │ apply_result.json
                   ┌──────────────────────────▼───────────────────────────────────┐
                   │ METRICS + DOGFOOD HARNESS  scripts/dogfood_metrics.py          │
                   │ stop_report → series.json → success-bar --check (exit-code)    │
                   │ ceiling-distance / human-touch / autonomy-fraction /          │
                   │ per-cause stop trend / regression guard                       │
                   └──────────────────────────┬───────────────────────────────────┘
                                              │  re-dogfood (next run)
                                              └──────────────► back to diagnoser
```

**Interface separation (load-bearing):** the diagnoser *measures and classifies*; the router *dispatches data*; the fix-modes *act*; the harness *re-measures*. No unit both classifies and acts. The router never recomputes a cause and never applies anything. `classify_stop_cause` lives in **one** module, `scripts/loop/stop_cause_classify.py`, imported by both diagnoser and harness. **[CORR-4]**

---

## 4. The Stop-Point Diagnoser

### 4.1 The single enum **[CORR-4]**

One lowercase enum, one module, imported everywhere:

```
StopCause = {
  gate_capped,       # real improvement exists, policy/bounds blocked it
  lever_exhausted,   # eye decided a better state exists, hand has no op
  decision_weak,     # eye senses off, cannot decide the better state
  headroom_blind,    # loop declared clean but figure is below premium
  settled_verified,  # genuinely done — positive evidence, no headroom
  plumbing_stop,     # pipeline-state stop (status_action_required, reference_input_missing) — NOT a quality stop
  not_stopped        # loop is mid-iteration / escalated correctly
}
```

The lens A `settled_verified` (5th) and lens E `plumbing_stop`/`not_stopped` are **all retained** — the critic's contradiction was two incompatible enums; the resolution is the union, lowercase, in one place. `plumbing_stop` is mandatory: the only live run cited (`20260621-121013-978819-fig2_trap_design_space`) stopped at `status_action_required`, a plumbing stop. The quality apparatus must never count plumbing as a quality cause. **[CORR + omission "plumbing dominance"]**

### 4.2 Trigger set **[CORR-5]**

The diagnoser runs when `loop_decision["stop_reason"]` lands in a **superset** `TERMINAL_STOPS`:

```
TERMINAL_STOPS = {
  no_actionable_findings,      # fig_loop_decision.py:172
  verify_only_complete,        # :179
  human_gate_required,         # incl. aesthetic-lever reroute (fig_loop.py:105)
  basin_detected,              # fig_loop.py:205
}
```

The original lens-A trigger `{verify_only_complete, no_actionable_findings}` was self-contradictory: `_apply_aesthetic_lever_stop` (`fig_loop.py:96-105`) rewrites to `human_gate_required`, and `_apply_basin_stop` (`:199-205`) to `basin_detected` — both *outside* the original trigger, making `gate_capped`(iii) and `decision_weak`(basin) **unreachable**. Fix: include both, and tag the rewritten decisions with the originating signal (aesthetic-lever bottleneck → carries `aesthetic_lever_id`; basin → carries the recurring `patch_target`/aesthetic signal) so the diagnoser can attribute the sub-region.

Plumbing reasons (`status_action_required`, `reference_input_missing`) → `plumbing_stop`, excluded from the four quality causes but counted separately.

### 4.3 Sub-region enumeration **[CORR-1, blocking]**

**Slice-0 prerequisite:** change `quality_defect_ledger._explicit_target` to emit a stable composite id:
- `(panel, selector_sha256)` when a selector exists,
- else `(panel, defect_class, ordinal)`.

Verify on fig2/fig3 that the ledger emits **distinct** regions before any per-region facet ships. The canonical join key for cross-run trending is this same id (resolves lens-A open-question #1 as a hard requirement). The enumeration source is the union of (a) Active Target Set rows (`subregion_active_set.parse_active_target_rows`, used by `fig_loop_subregion.active_subregion_target`) and (b) ledger defect targets keyed on the new composite id.

### 4.4 Signal bundle (per sub-region S)

Assembled from already-loaded run state plus one re-read of the ledger. **[CORR — candidate_set NOT in scope]:** the original lens-A claim that `candidate_generator.build_candidate_set` output is "in scope" in `run_loop` is **false** — `fig_loop.py` is `MODE="verify-only"` (`:70`) and never calls `build_candidate_set` (verified: no call in the tail `:296-420`). Therefore the diagnoser **invokes `build_candidate_set` itself** (read-only, no apply) as part of bundle assembly, or consumes a candidate-set artifact if one exists for the run. This is an explicit, named step — not an assumed-in-scope variable.

Bundle = `{status_result, quality_defect_ledger (re-read), candidate_set (diagnoser-invoked), aesthetic_lever_summary, audit_evidence_summary, basin_summary, reference_aesthetic_metrics_summary}`.

### 4.5 The classifier (precedence order)

`classify_stop_cause(S, bundle)` evaluates in faculty-precedence so each S lands in exactly one cause. **[CORR-4]:** the classifier consumes **both** the candidate/refusal signal (lens A) **and** the reference ceiling signal (lens E) — neither alone disambiguates `lever_exhausted` from `headroom_blind`.

1. **`plumbing_stop`** — `stop_reason ∈ {status_action_required, reference_input_missing}`.

2. **`gate_capped`** — a real improvement exists but policy/bounds blocked it:
   - (i) a defect for S has `patchability.state == "safe_candidate"` AND a candidate exists, but `semantic_candidate_review.build_semantic_review_state` returns `blocks_apply == True` (`semantic_candidate_review.py:65`); OR
   - (ii) the candidate's `edit_family` is a Slice-1 value-preserving lever NOT in `PURE_MECHANICAL_FAMILIES` (`:15`); OR
   - (iii) the stop was rerouted from `_apply_aesthetic_lever_stop` and the `needs_human` bottleneck `lever_id` maps to S. *(Now reachable because `human_gate_required` is in `TERMINAL_STOPS`.)* **[CORR-5]**

3. **`decision_weak`** — eye senses off, can't decide:
   - (i) `audit_evidence_summary` `uncertain_crop_ids` contains a crop bound to S, or `unadjudicated_candidate_count > 0`;
   - (ii) a critique finding for S adjudicated `needs_human`, or `aesthetic_lever` verdict `weak` with no linked lever;
   - (iii) `basin_detected` was rerouted in and the recurring signal targets S. *(Now reachable.)* **[CORR-5]**
   - **Refusal-code disambiguation [CORR — interface gap]:** if S carries a refusal code in `ACTIONABILITY_REFUSAL_CODES` (`candidate_generator.py:24-29` — `stale_detector_evidence`, `unknown_panel`, `missing_selector_hash`), classify as `decision_weak` (stale/uncertain evidence), **not** `lever_exhausted`. The actionability-refusals are an evidence-quality problem, not a missing-lever problem.

4. **`lever_exhausted`** — eye decided a better state exists but hand has no op. Triggered **only** by the *lever-absence* refusal codes, which are ad-hoc inline, not the named frozenset: `no_bounded_operation` (`candidate_generator.py:441`) and `no_supported_candidate` (`:572`), plus `unsupported_candidate_family` (the one member shared with `ACTIONABILITY_REFUSAL_CODES`). **[CORR — interface gap]:** because the refusal vocabulary is split across a frozenset and two inline literals, the design adds a **single canonical `REFUSAL_CODE → cause` table** owned by `stop_cause_classify.py` (the contract both A and E reference), and a follow-up promotes the two inline codes into a named `LEVER_REFUSAL_CODES` frozenset in `candidate_generator.py` so the contract is stable.

5. **`headroom_blind`** — loop declared S clean but it's below premium. Asserted **only from positive evidence**, never absence:
   - (i) all detectors pass for S AND `aesthetic_lever_summary` is `None`/`passed` AND a concrete unapplied higher-tier value-preserving lever exists (a `line_weight_tier`/`gradient_depth_fill` candidate whose tier > current); OR
   - (ii) `reference_aesthetic_metrics` shows S below the **premium band** (not merely above warning) while no detector/critique flagged it. **[CORR-6]:** the premium band is anchored to fig1's measured metrics, so "within warning" no longer counts as at-ceiling.
   - **[CORR — wrong-thinking trap "assumed-cause leakage"]:** the original design dumped *no-mechanical-lever* premium-blindness into `settled_verified`. Corrected: a reference-free deterministic headroom proxy (unaccounted-but-residual audit counts via `audit_evidence_summary` `candidate_count` vs `accounted_count`, plus presence of *any* unused premium lever) supplies a non-detector headroom signal. If that proxy fires with no lever, S is `headroom_blind` routed to the eye for art-direction, **not** silently `settled_verified`.

6. **`settled_verified`** — none of the above AND no positive headroom signal of any kind. Genuinely done.

Ties broken by the precedence list; the chosen branch and every signal are recorded in `evidence[]` for auditability.

### 4.6 Stop-report schema (`figure-agent.stop-report.v1`)

Written by `fig_loop_records.write_json` into the run dir, additive, never mutates the run:

```json
{
  "schema": "figure-agent.stop-report.v1",
  "fixture": "...", "run_dir": "...", "commit": "...", "branch": "...", "generated_at": "...",
  "raw_stop_reason": "no_actionable_findings",
  "subregions": [
    { "subregion_id": "F::sha256:ab12…", "panel": "F", "stop_cause": "headroom_blind",
      "settled": false,
      "evidence": [ {"signal_class":"reference_metric","signal_key":"edge_density_delta",
                     "source_module":"reference_aesthetic_metrics","source_ref":"reference_aesthetic_metrics.py:461"} ],
      "candidate_ref": null, "refusal_codes": [], "aesthetic_lever_id": null,
      "route": {"fix_mode":"eye","target_faculty":"eye","action":"raise_critique_ceiling",
                "payload":{"unused_lever_id":"line_weight_tier:hero"}, "blocked_by": null} }
  ],
  "cause_histogram": {"gate_capped":0,"lever_exhausted":1,"decision_weak":2,
                      "headroom_blind":3,"settled_verified":1,"plumbing_stop":0,"not_stopped":0},
  "dominant_premature_cause": "headroom_blind",
  "dominant_premature_count": 3
}
```

Every `evidence[]` entry cites a real `source_module:source_ref`, so a stop-report is **falsifiable by re-derivation** — no LLM judgment enters classification. Mirrored as a read-only row per non-settled sub-region into `subregion_iteration_log.md` via `append_iteration_row`, using the existing 7-column table (`Iteration | Sub-region ID | Problem | Patch Summary | Result | Why | Follow-up`, `subregion_iteration_log.py:54`) — `Why` = `stop_cause` + one-line evidence. **[CORR — flood guard]:** on large figures, write only `dominant_premature_cause` rows to the human log; the full per-region report lives in the run dir (resolves lens-A open-question #4).

### 4.7 Router

`route_stop_cause(subregion_report) → Route` — a **pure** function, writes a dispatch descriptor only, never applies:

| cause | fix_mode | action | payload |
|---|---|---|---|
| `gate_capped` | GATE (C) | `evaluate_gate_lift` | `blocked_by` (the specific gate) |
| `lever_exhausted` | HAND | `extend_candidate_family` OR `human_art_direction` | `missing_family` (the refusal code = spec) |
| `decision_weak` | EYE+B | `ground_decision_against_reference` | `reference_handle`, recurring basin signal |
| `headroom_blind` | EYE+B | `raise_critique_ceiling` | `unused_lever_id` or reference-free proxy |
| `settled_verified` | none | — | — |
| `plumbing_stop` | none (pipeline) | — | — |

**[CORR — interface gap, Hand payload mismatch]:** the Hand dispatches on `anti_pattern_id`, but `candidate_families.py` has **zero** `anti_pattern_id` fields (verified: `grep -c` = 0) and the router emitted refusal codes, not anti-pattern ids. Resolution: the **first Hand deliverable** is the `anti_pattern_id → edit_class` mapping (§5.2). Until it exists, the router carries the refusal code, and the Hand's `has_lever()` query is keyed on `edit_class` (which *does* exist via `CANONICAL_FAMILY_EDIT_CLASS`), with `anti_pattern_id` added once the mapping lands.

**[CORR — missing feedback paths]:**
- `lever_exhausted` with no buildable lever → terminal **`human_art_direction`** arm. *(The sink already exists: `AESTHETIC_ANTIPATTERN_ROUTES` and `AESTHETIC_GATE_ROUTES` both contain `human_art_direction`/`needs_human_art_direction` — `critique_schema_vocab.py:249,290`.)*
- `basin_detected` → reachable `decision_weak` route (fixed by the trigger superset).
- A fix-mode applied but `ceiling_distance` did **not** move (measured by the harness diff across runs) → the harness flips the region's route to escalation (`human_art_direction`) to prevent thrash (anti-thrash loop, resolves the missing "ineffective→reclassify" path).

---

## 5. Fix-Modes

### 5.1 EYE — fix-mode for `headroom_blind` + `decision_weak`

**Problem in code:** judgment is structurally forbidden from driving continuation. `critique_brief_sections.journal_grade_assessment` states "not a progress score"; `fig_loop_assessments.py` stamps `score_policy=advisory_fresh_reaudit_not_gate`; reference-free mode hard-sets `score_is_gateable:false`. So `no_actionable_findings` (`fig_loop_decision.py:172`) is reached with **no headroom check** — the headroom-blind premature stop, by construction.

**Three components:**

1. **Headroom estimator** (`headroom.json`, `figure-agent.headroom.v1`, host-vision-filled, schema-validated like `critique.md`). Per active sub-region × the 10 axes (`critique_brief_sections.journal_quality_axes`), emit `ceiling_distance_band ∈ {at_ceiling, near, mid, far}` plus a **mandatory** `anchor_kind ∈ {reference_crop, principle_rubric, paper_context_must_avoid, detector_id, theory_guard}`. An unanchored band is a lint error: extend `critique_lint.py` with `_headroom_anchor_violations` (mirror of `_aesthetic_lever_accounting_violations`). **[CORR-6]:** the band's `at_ceiling`/`near` admissibility is rejected if `reference_aesthetic_metrics_summary` returns `severe_divergence` — the deterministic metric overrides eye optimism. Crucially, the **premium band** (not the warning band) defines `at_ceiling`, anchored to fig1's measured metrics.

2. **Pairwise better-state proposer** (`decision_weak` fix). Replace absolute scoring (the ~18% failure) with **anchored pairwise** comparison over ≥2 *rendered* candidate states (`candidate_render.py` + `candidate_visual_eval.py`). The eye answers the strictly easier "is A better than B, anchored to X" and emits a partial order with per-edge anchor — not a float. **Verifiable:** the winner must also clear the semantic recheck (§6) and not worsen any `reference_aesthetic_metric` beyond WARNING; a winner that regresses a detector is rejected loud. **[CORR — echo-chamber]:** a second judge (`external_vision_review.py` / `external-question` skill) is required when the two states are reference-free; 2-judge disagreement escalates to `needs_human` (resolves lens-eye open-question #5).

3. **Accumulating Why-ledger as prior.** New reader `narrative_judgment_prior()` (sibling to `narrative_context.build_narrative_context`) parses prior `Why` rows for the same fixture/axis into the critique brief as "prior decisions on this axis." A human-signed `Why` becomes an admissible `anchor_kind=principle_rubric` — this is exactly how the auto line moves outward (banks judgment, the cheap-iteration analogue of the primitive bank).

**Continuation contract (the single line that kills clean=done):** `fig_loop_decision.loop_decision` must **not** return `no_actionable_findings` while any active sub-region has band ∈ `{far, mid}` unless human-signed (`accept_headroom`, a new adjudication decision in `critique_adjudication`). **[CORR — interface gap]:** this requires threading the `headroom.json` artifact into `loop_decision`'s inputs — it is **not** a "single line," it is a new artifact in the decision-function signature plus a precedence-chain insertion at the `no_actionable_findings` branch. Scoped honestly as such.

**Reference-free non-permanence [CORR — defensive-cap trap]:** for figures with no `reference_aesthetic` anchor, headroom rests on (a) `principle_rubric` from the Why-ledger and (b) the deterministic reference-free residual proxy (§4.5.5). Reference-free auto-continuation is OFF *only until* the Why-ledger seeds rubric anchors with logged agreement — and the residual proxy lets the frontier move *now*, not "park it forever." This is framed as earned advancement, not a permanent human gate.

**Verifier:** `_headroom_anchor_violations` (build fails on unanchored band); severe-divergence floor; pairwise winner must render + clear semantic recheck + not regress metrics; the continuation precondition is unit-testable (headroom present → loop must continue to a hand/gate action, asserted, so a fake-autonomy green test is caught).

### 5.2 HAND — fix-mode for `lever_exhausted`

**Verified state [CORR-8]:** the lens claim "2 of 13 anti-patterns have a lever" is corrected to: **2 distinct transforms** (`line_weight_tier`, `gradient_depth_fill`), with **5 families aliasing** `bounded_coordinate_offset.offset_first_coordinate` via the else-branch (`candidate_families.py:216`), and **zero** `anti_pattern_id` fields linking families to the 13 `AESTHETIC_ANTIPATTERN_IDS`. The 13 ids are verified verbatim (`critique_schema_vocab.py:231-244`); the existing 2 levers plausibly cover ~4 of them (`uniform_line_weight_monotony`, `weak_hero_anchor`, `dead_flat_vector_finish`, `poster_gradient_decoration`) but **the mapping does not exist in code**.

**First deliverable (the measurement substrate):** the `anti_pattern_id → edit_class` mapping + a **LeverSpec registry** that `CANONICAL_FAMILY_EDIT_CLASS`, `_apply_edit_transform`, and `_semantic_risks_for` become derived views over. This makes `lever_exhausted` *computable*: `has_lever(anti_pattern_id, panel_model) → bool` returns True iff a `LeverSpec.primitive_fn` returns non-None on any selector in the panel. The diagnoser's `lever_exhausted` verdict becomes a function call, not a guess.

**[CORR-9 / scope]:** new lever *modules* (stroke_join_polish, whitespace, typography_authority, hero) and the amortize bank (PIECE 5/6) are **gated** on a measured `lever_exhausted` count ≥ threshold from real dogfood. Only the **registry refactor + `has_lever()` query** ship in this facet's first slice. This directly honors the Hand's own open-question and the build-what-dogfood-says principle.

**Hero-tier calibration [verified, CORR-8]:** `line_weight_tier.TIERS = {primary:0.9, annotation:0.7, secondary:0.55}`, `FLOOR_PT=0.5`, **no ceiling**. The preamble body band is real and matches the cited numbers: `axis 0.38pt`, `bond 0.85pt`, `every axis plot 0.92pt` (`styles/polymer-paper-preamble.sty:43,62,52`). Examples contain genuine hero strokes at **1.4pt (11×), 1.6pt (12×)**, up to 5.0pt. So `primary:0.9` sits *inside* the body band and **cannot lift a hero above the body** — the under-weight bug is real. Fix (gated on measured demand): extend to a calibratable 4-tier set adding `hero`, add `CEILING_PT`, and compute hero **relative to the figure's own body band** (`hero = body_max × ratio`, clamped). The calibration source is the B-fix-mode's stroke histogram. The tier becomes a parameter, never a hardcoded `1.4pt` idiom — avoiding the falsified snippet-lock.

**Anti-snippet-lock invariant:** every `LeverSpec.primitive_fn` MUST be a pure `(str, **params) → str|None` transform over an *existing* line; a spec is rejected at registry-load if its replacement is multi-line or contains `\input` (the `composition_family_templates.FAMILY_DATA` shape). Composition stays its own gated path, never folded into the hand registry.

**Amortize bank [CORR-9, quarantined]:** PIECE 5/6 (bank ratios across figures, cross-figure promotion) is deferred behind a dogfood gate, matching the amortize-probe result ([[project_dev_closure_2026_06_22]]: bare primitive has no premium direction without context). When un-gated: store **ratios/relative params only** (hero_ratio transfers; absolute tokens like `cAmber!28` do not — resolves lens-hand open-question #5), next to `quality_memory_events.py`.

**Interface:** Hand emits the existing `figure-agent.candidate-set.v1` schema with `apply_authority=review_only` — `candidate_apply` and `semantic_candidate_review` consume it unchanged.
**Verifier:** registry load-time test (every `primitive_fn` returns None on out-of-bound input); apply-time semantic recheck + CLASS_VERIFIERS; hero clamped to `[FLOOR_PT, CEILING_PT]` and a hero that doesn't exceed `body_max` refuses (no-op surfaced as refusal, not fake apply).

### 5.3 GATE — autonomy-frontier ratchet, fix-mode for `gate_capped`

**[CORR-9 — trimmed to evidence-gated stub for v1]:** ship only (1) the read-only frontier ledger + (2) the `gate_capped` counter. Defer the graduation promoter, signed schemas, and bound-loosening until the counter proves `gate_capped` material on real figures.

**v1 (ships):**
- `autonomy_frontier_ledger.py` — read-only aggregator over `build/candidates/*/apply_result.json` + `semantic_review.json`. Per class `(defect_class | edit_family)`: `confirmed_apply_count`, `human_pass_count`, `regression_count`, `distinct_fixtures`, bound-utilization histogram. Pure read; no mutation surface; cannot fake progress.
- `gate_capped` counter (in the stop-report cause_histogram) — the empirical measure of how much premature stopping this gate is responsible for.

**Deferred (built only if the counter shows gate_capped material):**
- `autonomy_graduation.py::evaluate_graduation` + the two signed schemas + bound-loosening.

**The may_edit contradiction [CORR — verified, contradiction]:** `classify_patchability` returns `"may_edit": False` **unconditionally** (`quality_patch_policy.py:66`) on every path — flipping `state` to `safe_candidate` while `may_edit` stays False does nothing, because consumers gate on `may_edit`. Resolution: graduation must make **`may_edit` itself conditional**, sourced from the counter-signed `graduation.json` validated via `_invalid_reasons`-style discipline (wrong schema / stale `evidence_sha256` / forbidden `apply_authority` field / fixture mismatch ⇒ fail-closed, class reverts to human-required). `HUMAN_CLASSES` (`semantic_meaning`, `taste_decision`, `publication_gate`) **never** graduate — the permanent frontier.

**Graduation criterion (when un-gated):** promote class C to `auto_eligible` iff `confirmed_apply_count(C) ≥ N` (start N=5) AND `distinct_fixtures(C) ≥ M` (start M=3) AND `regression_count(C) == 0` AND `human_pass_count == confirmed_apply_count` AND C never tripped its `CLASS_VERIFIERS`. Demote on any later regression.

**[CORR — cold-start]:** with ~1 accepted figure (fig1) and a 3-fixture cohort, M=3 cross-fixture evidence is unreachable for most classes initially. The bootstrap path: (a) **same-fixture repeated applies** seed `confirmed_apply_count` while `distinct_fixtures` stays 0, holding the class at `graduation_candidate` (visible, not yet auto); (b) N/M are themselves the **variable being dogfooded** in Slice 4 — start deliberately conservative (effectively human-only) so the first campaign *measures* the true agreement distribution before any class auto-enables. The frontier moves via the **bound-utilization** signal and per-fixture `graduation_candidate` visibility long before cross-fixture promotion is possible.

**[CORR — missing demotion re-audit]:** demotion-on-regression must trigger a **re-audit of all figures that received that class's auto-applies** (the cantilever "silent error survived for days" failure, [[project_cantilever_fix_2026_06_10]]). The ledger records which figures received each class's auto-applies; demotion enqueues them for re-verification.

---

## 6. Verification Spine

The spine is what lets autonomy advance safely and fail loud. **[CORR-2, CORR-3 — the largest corrections.]**

**What already exists and is reused unchanged (per-apply, loud):** `candidate_apply.apply_candidate` — sha256 source-drift block (`:256`), `original_text_count != 1` refusal (`:264-267`), `O_EXCL` mutation lock (`:176`), `rollback_patch` written before mutation (`:286`), post-apply compile + export + status (`_post_apply_checks`). Three terminal statuses exist: `applied`, `applied_unverified`, `applied_with_failed_verification` (`:22-26`).

**[CORR-2 — the recheck is fingerprint-equality and is gameable.]** `_post_apply_detector_recheck` (`:375-417`) only checks that the *exact* `source_fingerprint` is absent from the rebuilt ledger (`:406`). A fingerprint hashes geometry/selector; **a bounded coordinate nudge changes the fingerprint, so the old one is trivially "not detected" even if the defect visually persists under a new fingerprint.** This sits under the system's main verification claim. **Mandatory correction:** replace fingerprint-equality with **semantic-defect recheck** — compare by `(panel, defect_class, sub_region_key)` membership, AND assert **no new defect of equal-or-higher severity appeared anywhere** (whole-ledger before/after diff). Only this stronger result may count toward real-improvement / graduation evidence. Until wired, **no autonomy advance may cite the recheck.**

**[CORR-3 — the value-preserving verifiers are NOT wired into apply.]** Verified: `grep` for `check_semantic_assertions|check_undeclared_geometry|lint_tex|diff_pdf_content` in `candidate_apply.py` returns **nothing**. The lens claim "rides EVERY apply, reused as-is" is false. **Mandatory correction:** add these into `candidate_apply` post-mutation, gated by a per-class `CLASS_VERIFIERS` list, with auto-rollback on any violation. This is **net-new apply-time wiring**, scoped and tested as such — not "reused." Per-class verifiers:
- coordinate/label classes: `check_semantic_assertions` (`semantic_assertions.py:105`) + pdftotext word-set identity + `check_undeclared_geometry` (`check_undeclared_geometry.py:102`, topology preserved);
- style classes (`line_weight_tier`, `gradient_depth_fill`): `lint_tex` (palette lock — no `definecolor`/raw-hex/cross-hue) + `diff_pdf_content` where a baseline exists.

**[CORR-7 — `applied_unverified` handled explicitly everywhere.]** Status is `applied_unverified` whenever post-apply recheck is skipped (`:577`). It counts as **neither** real-improvement (harness) **nor** graduation evidence (gate) — it is a loud "verification-skipped" that must be re-run, never silently dropped or counted as clean.

**How autonomy advances safely:** a `gate_capped` region converts to auto-apply only when (a) the class's `CLASS_VERIFIERS` passed on real applies, (b) the **semantic** recheck (not fingerprint) cleared, (c) no new defect appeared, (d) a human counter-signed `graduation.json`. A single later verifier trip auto-demotes (reversible, fails loud). A green unit test cannot manufacture an evidence row because rows are built only from real `apply_result.json` requiring a real compile + semantic recheck on a real figure.

---

## 7. Metrics & Dogfood Harness

**Three live data planes** (verified on disk): the **stop plane** (`fig_loop_decision` stop_reason vocabulary, persisted to `run_manifest.json[final_stop_reason]` + `iteration_001.json`); the **ceiling plane** (`reference_aesthetic_metrics` six deterministic deltas + `audit_evidence_summary` candidate/accounted counts); the **autonomy/value plane** (semantic recheck + `semantic_candidate_review.blocks_apply` + `PURE_MECHANICAL_FAMILIES`).

**Net-new (3 read-only files):** `scripts/loop/stop_cause_classify.py` (the shared enum + classifier), `scripts/loop/fig_loop_stop_diagnoser.py` (enumeration + builder), `scripts/dogfood_metrics.py` (cross-run roller + `--check` success bar). Plus `scripts/dogfood_cohort.json`.

**Emitted series** (`figure-agent.dogfood-series.v1`, into `.scratch/dogfood_metrics/series.json`):

1. **ceiling_distance** — **[CORR-6]** distance-to-**premium**, NOT distance-to-warning. Weighted normalized sum over the six deltas relative to the **premium-target band anchored to fig1's measured metrics**, not `WARNING_THRESHOLDS`. `passed` does NOT imply at-ceiling. Reference-free figures get the deterministic residual proxy (§4.5.5), never silent 0; `anchor_missing` rises if anchors are deleted (cannot game by deletion).
2. **human_touch_count** — Why-rows authored since last accept (parsed from the 7-column `subregion_iteration_log.md`) + `gate_capped` stops with `human_gate_status==required` + human-signed `semantic_review.json` count.
3. **autonomy_fraction** — `auto_applied_real_improvements / (auto + human)`. Auto counted **only** when `blocks_apply==False` AND **semantic** recheck success (rode a verifier). `applied_unverified` excluded. **[CORR-7]**
4. **per_cause_stop_counts** — time series over the four quality causes; `plumbing_stop`/`not_stopped` tracked separately so plumbing churn never masquerades as a quality win. **dominant_premature_cause = argmax over the four** — the empirical answer to "why does it stop partway," never assumed.
5. **regression_count** — prior-good fixtures whose ceiling_distance rose or detector count rose after an advance. Target permanently 0.

**[CORR — unverifiable trending claim]:** the original lens-E plan recomputed live ceiling_distance "at head" for every historical run point, which would make every point show the same head value (no real history). Corrected: each run point uses **its own committed `commit` from the run manifest** (`fig_loop.py` writes `commit` into the manifest) checked out or read from that run's stored metrics, so the series is a true history. Live-at-head recompute is used only for the *current* regression-guard comparison, not the trend.

**Cross-run trending** globs `runs_root` (196 dirs verified) bounded by `--since` / per-fixture-latest cap so roll-up stays cheap (resolves lens-E open-question #5).

**Dogfood protocol:** (1) run the loop on the cohort; (2) `stop_report.py` writes per-run reports; (3) `dogfood_metrics.py roll_up` → `series.json`; (4) `--check` returns **non-zero** on any regression or success-bar miss (exit-code-backed; a rich report cannot be mistaken for a pass).

**Ungameable honest success bar:** (a) `dominant_premature_cause` is trending down for at least one cause as its fix-mode lands; (b) `autonomy_fraction` rises at **non-rising** ceiling_distance (frontier moved without quality loss); (c) `regression_count == 0`; (d) `pairwise-winner-survival-rate` beats the 18% baseline. No metric trusts a self-reported success string.

**Cohort** (`scripts/dogfood_cohort.json`): `fig1_overview_v2_pair_001_vault` (prior-good **regression anchor**) + `fig2_trap_design_space` + `fig3_resistance_mechanism` (active-improvement set). All verified to exist.

---

## 8. Phased Roadmap

Slices are **evidence-driven**: each has a concrete dogfood gate; later slices are gated by what dogfood reveals. **Diagnoser first.** Namespace reconciled to the existing Slice 0/1 ([[session_slice0_execution_2026_06_21]]): this spec opens at **Slice 2**.

| Slice | Deliverable | Dogfood gate (must pass to proceed) |
|---|---|---|
| **Slice 2 — Real sub-region key** **[CORR-1, blocker]** | `quality_defect_ledger._explicit_target` → `(panel, selector_sha256)` / `(panel, defect_class, ordinal)` | Ledger emits **distinct** regions on fig2 AND fig3 (no `label-a` collapse). |
| **Slice 3 — Diagnoser + harness (measure only)** | `stop_cause_classify.py` (unified enum), `fig_loop_stop_diagnoser.py`, `fig_loop_stop_router.py` (pure), `dogfood_metrics.py`, `stop_report.v1`, Why-row mirror; trigger superset incl. aesthetic-lever + basin **[CORR-5]**. No fix-mode acts yet. | On the 3-fixture cohort, `dominant_premature_cause` is emitted and **non-degenerate** (not 100% plumbing). If plumbing dominates → fix plumbing first; the quality apparatus is dormant by design until quality stops appear. **[CORR — plumbing dominance]** |
| **Slice 4 — Verification spine hardening** **[CORR-2,3,7]** | Semantic recheck (replace fingerprint-equality) + no-new-defect delta; wire `CLASS_VERIFIERS` into `candidate_apply`; `applied_unverified` handled everywhere; `autonomy_frontier_ledger` (read-only) + `gate_capped` counter. | A deliberate fingerprint-shifting edit that leaves the defect visible is now caught (was passing). A palette-breaking variant trips `lint_tex` + auto-rollback. |
| **Slice 5 — Fix-mode #1 (driven by Slice-3 dominant cause)** | Build **only** the fix-mode for the measured dominant cause. If `headroom_blind` dominates → EYE headroom estimator + continuation precondition. If `lever_exhausted` → HAND registry refactor + `has_lever()`. If `gate_capped` → GATE graduation un-gated. | Per-cause stop count for the dominant cause trends **down** across ≥2 runs at non-rising ceiling_distance, regression_count 0. |
| **Slice 6+ — Subsequent fix-modes** | EYE pairwise proposer; HAND lever modules + hero calibration; GATE graduation + bound-loosening; amortize bank. Each gated on its cause being material. | Same gate, per cause. Amortize bank gated on cross-fixture transfer measured ≥ baseline. |

No pre-commitment past Slice 3: which fix-mode is Slice 5 is an **output of dogfood**, not a plan.

---

## 9. Risks & Wrong-Thinking Guards

| Trap | How the design structurally prevents it |
|---|---|
| **(a) Faking autonomy** (green tests / rich envelopes, no real improvement) | Evidence rows built only from real `apply_result.json` requiring real compile + **semantic** recheck on a real figure. The continuation precondition is unit-tested to assert the loop *continued to a real action*. **[CORR-2,3]** |
| **(a′) Fingerprint-drift gaming** | Fingerprint-equality recheck replaced with semantic `(panel, defect_class, sub_region_key)` recheck + no-new-defect whole-ledger delta. A coordinate nudge can no longer trivially "clear" a defect. **[CORR-2]** |
| **(b) Accepting ~18% as a cap** | Absolute taste removed from the diagnoser entirely (classification is deterministic). Eye uses anchored pairwise whose winner must survive a deterministic recheck; `pairwise-winner-survival-rate` is reported against the 18% baseline — measured, not asserted. |
| **(c) Settling at clean=done** | `no_actionable_findings` is necessary but no longer sufficient — blocked while any sub-region has `far/mid` headroom unsigned. ceiling_distance measures distance-to-**premium**, not distance-to-warning; `passed ≠ at_ceiling`. `headroom_blind` is a first-class routed cause. **[CORR-6]** |
| **(c′) Premium-blind with no lever mislabeled "done"** | A reference-free residual proxy supplies a non-detector headroom signal so no-mechanical-lever premium-blindness routes to `headroom_blind` → eye art-direction, never silently `settled_verified`. **[CORR — assumed-cause leakage]** |
| **(d) YOLO past verification** | Every autonomy advance rides a verifier; graduation needs a human-counter-signed artifact validated fail-closed; demotion is automatic + re-audits prior auto-applied figures. `may_edit` conditional only via signed artifact. **[CORR-3, demotion re-audit]** |
| **Plumbing masquerading as quality** | `plumbing_stop`/`not_stopped` are separate enum members, excluded from the four quality causes; Slice-3 gate explicitly checks the dominant cause is non-degenerate. |
| **Cold-start (low-N)** | Same-fixture applies seed `graduation_candidate` visibility; N/M start conservative and are themselves the dogfooded variable; bound-utilization moves the frontier before cross-fixture promotion is possible. |
| **Thrash (fix-mode applied, needle didn't move)** | Harness diffs ceiling_distance across runs; a region whose fix-mode failed to move it is rerouted to `human_art_direction`. |

---

## 10. What Exists vs Net-New

| Concern | Existing (reused) | Status | Net-new / Extended |
|---|---|---|---|
| Sub-region key | `quality_defect_ledger._explicit_target` (`:112`) defaults `label-a` | **BROKEN — must fix** | Extend to composite id **[CORR-1, Slice 2]** |
| Stop vocabulary | `fig_loop_decision.loop_decision` (11 reasons) | Reused as-is | `stop_cause_classify.py` adds 7-member quality enum **[CORR-4]** |
| Diagnoser trigger | `_apply_aesthetic_lever_stop`/`_apply_basin_stop` (`fig_loop.py:96,199`) | Reroutes must carry sub-region tag | `TERMINAL_STOPS` superset **[CORR-5]** |
| Candidate set in loop | `build_candidate_set` | **NOT in verify-only scope** | Diagnoser invokes it itself (read-only) **[CORR]** |
| Apply spine | `candidate_apply` sha256/O_EXCL/rollback/compile (`:176,256,286`) | Reused as-is | — |
| Recheck | `_post_apply_detector_recheck` (`:375`) | **Fingerprint-equality, gameable** | Replace w/ semantic recheck + no-new-defect delta **[CORR-2]** |
| Value-preserving verifiers | `check_semantic_assertions`, `check_undeclared_geometry`, `lint_tex`, `diff_pdf_content` | **NOT wired into apply** | Net-new `CLASS_VERIFIERS` apply-time wiring **[CORR-3]** |
| `applied_unverified` | `candidate_apply.py:22-26,577` | Reused | Handled explicitly (counts as neither) **[CORR-7]** |
| Gate tables | `PURE_MECHANICAL_FAMILIES` (`:15`), `SAFE/HUMAN_CLASSES`, `classify_patchability` | `may_edit:False` unconditional | Make `may_edit` conditional via signed artifact **[CORR — contradiction]** |
| Frontier ledger | `apply_result.json`, `semantic_review.json`, `quality_memory_events` | Substrate reused | `autonomy_frontier_ledger.py` (read-only) + `gate_capped` counter; graduation **deferred [CORR-9]** |
| Levers | `line_weight_tier` (TIERS 0.9/0.7/0.55, no ceiling), `gradient_depth_fill`, `candidate_families` (5 families alias offset, 0 anti_pattern_id) | Reused; under-weight bug real | Registry refactor + `anti_pattern_id` mapping + `has_lever()`; new modules **gated [CORR-8,9]** |
| Eye | `critique_brief_sections.journal_quality_axes`, `reference_aesthetic_metrics`, `critique_lint`, `critique_adjudication`, `candidate_render/visual_eval` | Reused | `headroom.json`, `_headroom_anchor_violations`, pairwise proposer, `narrative_judgment_prior`, `accept_headroom` decision |
| Ceiling metric | `reference_aesthetic_metrics` (WARNING/SEVERE) | **Measures within-warning** | Premium band anchored to fig1 + reference-free proxy **[CORR-6]** |
| Harness | `fig_loop_records.json_stdout_summary`, `status.py --json`, 196 run dirs | Reused | `stop_report.py`, `dogfood_metrics.py --check`, `dogfood_cohort.json` |
| Why column | `subregion_iteration_log.py:54` (7-col, capture-only) | Reused | Programmatic Why=stop_cause row writer (no schema change) |
| Human art-direction sink | `AESTHETIC_ANTIPATTERN_ROUTES`/`AESTHETIC_GATE_ROUTES` contain `human_art_direction` (`critique_schema_vocab.py:249,290`) | Reused as terminal arm | `lever_unbuildable` route wired to it **[CORR — missing feedback path]** |

---

### Verification footnotes (grounding)

- `label-a` default: `scripts/quality/quality_defect_ledger.py:122,126,127,304` — verified.
- Fingerprint-equality recheck, no new-defect check: `scripts/candidates/candidate_apply.py:386,406,415` — verified.
- Verifiers not wired into apply: `grep check_semantic_assertions|check_undeclared_geometry|lint_tex|diff_pdf_content scripts/candidates/candidate_apply.py` → empty — verified.
- Three apply statuses incl. `applied_unverified`: `candidate_apply.py:22-26,571-577` — verified.
- `may_edit:False` unconditional: `scripts/quality/quality_patch_policy.py:66` — verified.
- Aesthetic-lever → `human_gate_required` / basin → `basin_detected` (outside original trigger): `scripts/fig_loop.py:105,205` — verified.
- `candidate_set` not generated in verify-only `run_loop`: tail `:296-420` has no `build_candidate_set` call — verified.
- Refusal codes split: `ACTIONABILITY_REFUSAL_CODES` frozenset `candidate_generator.py:24-29`; `no_bounded_operation` `:441`, `no_supported_candidate` `:572` inline — verified.
- Ceiling = within-warning: `reference_aesthetic_metrics.py:444,461`; thresholds `:21-34` — verified.
- Lever count: 2 distinct transforms; 5 families alias `offset_first_coordinate` `candidate_families.py:216`; 0 `anti_pattern_id` fields (`grep -c` = 0) — verified.
- Hero under-weight: TIERS `line_weight_tier.py:12` (max 0.9) vs preamble `axis 0.38 / bond 0.85 / every-axis-plot 0.92` (`polymer-paper-preamble.sty:43,62,52`) and example hero strokes 1.4pt(11×)/1.6pt(12×) — verified.
- 13 `AESTHETIC_ANTIPATTERN_IDS`, `human_art_direction` route exists: `critique_schema_vocab.py:231-244,249,290` — verified.
- 196 run dirs, cohort fixtures exist: `.scratch/fig-loop-runs/` count 196; `examples/{fig1_overview_v2_pair_001_vault,fig2_trap_design_space,fig3_resistance_mechanism}` — verified.
- Why column 7-col template: `subregion_iteration_log.py:54` — verified.

All 10 adversarial corrections are integrated and flagged; where a lens conflicted with a correction, the correction won (noted inline). The spec is internally consistent: one enum, one classifier consuming both candidate and reference signals, one apply spine with real verifiers, a premium (not warning) ceiling, and every autonomy advance riding a fail-loud verifier sourced only from human-counter-signed artifacts.