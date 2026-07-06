# Architecture v0.13 — Experience Loop and Reward Integrity

**Date**: 2026-07-04
**Status**: accepted direction; spec only, no implementation in this pass
**Supersedes nothing** — amends the slice ordering of
`architecture-v0.12-quality-search-execution-plan.md` and supplies the
prerequisite layer that `architecture-v0.11-global-quality-search-loop.md`
silently assumes.

## Decision

The owner's direction decision (2026-07-04): the per-figure human gate is the
bottleneck; the loop running well — and learning from its own outcomes — is the
product. The loop must accumulate experience across iterations, runs, and
fixtures, change its future behavior from that experience, and surface its own
systemic defects (loop defects, tool defects, missing layers).

v0.11 already frames this correctly ("the memory ledger is the learned
prior"). A four-track audit on 2026-07-04 (learning-substrate, loop-policy,
reward-labels, prior-art) established that the substrate this framing assumes
is inert. Therefore v0.13 fixes the ordering:

**Reward truth → durable experience → learning wiring → self-diagnosis →
gate replacement → exploration.**

No slice may be built on top of a reward signal that the audit classified as
degenerate or gameable. A learning loop wired to today's signals would learn
compilability, not figure quality.

## Audit Facts (constraints this spec is built on)

| # | Fact | Evidence |
| --- | --- | --- |
| A1 | Only live cross-run feedback is the basin circuit-breaker, and it only forces stop | `scripts/loop/fig_loop_basin.py:97-163`, `scripts/fig_loop.py:202-214` |
| A2 | The prior spine exists end-to-end but is starved: rank hook present, index never auto-persisted, production callers pass `None`, generator reads zero memory | `scripts/candidates/candidate_rank.py:93-114,182`; `scripts/quality/quality_memory_index.py:77-88`; `mcp/server_impl.py:1173` |
| A3 | The event builder emits only `improved`; `neutral`/`regressed` are never produced, so the ≥3-attempt floor is unreachable and the prior can only move positive | `scripts/quality/quality_memory_events.py:279` |
| A4 | `improved` means "recompiled + status passed", not "figure got better" — a compilability signal masquerading as a quality reward | `scripts/quality/quality_memory_events.py:279` |
| A5 | Rejects are structurally discarded: acceptance writers raise unless `decision=="accept"`; zero reject decision-records exist on disk | `scripts/candidates/candidate_acceptance.py:299`; `scripts/golden_acceptance.py:133` |
| A6 | No durable join spine: nothing carries `{fixture, subregion_key, edit_family, candidate_hash, verification_outcome, human_decision}` together; the pieces live in git-cleaned `build/`; subregion keys fall back to unstable ordinals | `scripts/quality/quality_defect_ledger.py:147-152` |
| A7 | Stop machinery is measure-only: `diagnose_run` has no production caller; `route_stop_cause` has zero callers; plumbing stops print command strings instead of executing them | `scripts/loop/fig_loop_stop_router.py:26`; `scripts/loop/fig_loop_decision.py:82-189` |
| A8 | Four candidate families silently fall through to a 0.10 cm no-op nudge | `scripts/candidates/candidate_families.py:25-38,231` |
| A9 | `contextual_bandit_beam_v0` is a descriptor label over rule-based selection; `quality_next_experiment` returns a constant | `scripts/quality/quality_search.py:568`; `scripts/quality/quality_next_experiment.py:38` |
| A10 | Detector telemetry has writers and zero readers, while its docstring promises demotion/pruning governance | `scripts/detector_log.py:46`; `scripts/detector_feedback_ledger.py` |
| A11 | The acceptance "human gate" is two nonempty agent-writable strings; one decision-record check passes on the substring `"evidence"` | `scripts/candidates/candidate_acceptance.py:299-302`; `scripts/human_decision_record.py:199` |
| A12 | Prior art: the ML advisory sidecar was sunset (2026-06-11, `d39ad75c`) because labels were missing, not model capacity. Reopen bar: 100+ reviewed labels | `docs/milestones/2026-06-11-ml-advisory-sunset-decision.md` |
| A13 | Counterfactuals already survive: `candidate_set.json` retains unchosen candidates with operations/selectors/hashes; Pipeline-A rank scores are stdout-only | `bin/fig-agent:822` |
| A14 | Longitudinal substrate absent: `benchmarks/` is one YAML, no CI run, no trend history | `benchmarks/quality_suites.yaml` |

## Slice Plan (amends v0.12 §Implementation Slices)

v0.12 Slices 0-5 are built. v0.12 Slice 6 (cross-fixture benchmark) is
deferred until after E3 below. New slices E1-E6 are ordered and blocking:
a slice must not start until the previous slice's stop condition holds,
because each consumes the previous one's signal.

### Slice E1 — Reward Integrity

Make the recorded outcome mean what a learner needs it to mean.

Deliverables:

1. Split `improved` into two orthogonal fields: `pipeline_ok`
   (compile/export/status, the current meaning) and `quality_movement`
   (`improved|neutral|regressed`), where `quality_movement` is derived only
   from trustworthy machine signals: detector_recheck movement, class-verifier
   verdicts, rollback occurrence. A candidate that merely recompiles is
   `neutral`, never `improved` (fixes A3/A4).
2. Persist non-accept decisions: `write_acceptance` and
   `write_golden_acceptance` gain `reject`/`defer` writers instead of raising
   (fixes A5). Reject records carry the same candidate identity fields as
   accepts.
3. Rollback (`apply_status=="rolled_back"`) is recorded as an earned
   `regressed` label automatically.

Reward taxonomy (normative):

- **Usable as reward**: apply verdict fields (`applied`/`rolled_back`,
  per-verifier pass/fail, `detector_recheck`), structured `decision_kind`
  enums, compile/export return codes, detector count deltas.
- **Forbidden as reward**: free-text `rationale`/`human_note`, the legacy
  `improved` flag, any rank-score component the ranker itself produced
  (circularity), substring checks over prose (A11).

Stop condition: on a real fixture run, the event stream contains at least one
`neutral` or `regressed` outcome produced by machinery (not hand-edited), and
a rejected candidate's identity is on disk.

### Slice E2 — Durable Experience Record

One append-only, git-tracked JSONL row per candidate decision, outside
git-cleaned `build/` (proposed: `docs/experience-log/<fixture>.jsonl`).
Schema `figure-agent.experience-record.v1`:

```json
{
  "schema": "figure-agent.experience-record.v1",
  "record_id": "<canonical_hash>",
  "fixture": "...",
  "created_at": "...Z",
  "state": {
    "base_tex_hash": "sha256:...",
    "target": {"panel": "...", "subregion_key": "..."},
    "pre_apply_defects": ["..."],
    "critique_finding_id": null
  },
  "action": {
    "candidate_id": "...", "edit_family": "...",
    "params": {"operations": ["..."]},
    "candidate_hash": "sha256:...",
    "rank_score": 0.0, "rank": 1, "n_candidates": 1
  },
  "outcome": {
    "pipeline_ok": true,
    "apply_status": "applied|rolled_back|blocked|unchosen",
    "quality_movement": "improved|neutral|regressed|null",
    "verifiers": {"...": "pass|fail"},
    "detector_recheck": {"status": "...", "reason": "..."},
    "pixel_delta": {"changed_pixel_ratio": 0.0},
    "human_label": "accept|reject|defer|null",
    "human_decision_kind": null
  }
}
```

Requirements:

- Emitted at apply/decision time by joining artifacts that already exist
  (A13); nothing new is measured.
- One `apply_status:"unchosen"` row per non-selected ranked candidate
  (counterfactuals), sourced from `candidate_set.json` plus persisted rank
  results (fixes the stdout-only gap, A13).
- `subregion_key` must be the stable `selector_text_hash`; the ordinal
  fallback (A6) is forbidden in this record — if no stable key exists, the
  row says so explicitly (`"subregion_key": "unstable:<ordinal>"`) so the
  learner can exclude it.
- Records are append-only; correction is a new row, never an edit.

Stop condition: after one loop run, `candidate → verification → human
decision → subregion` is answerable across runs by reading one file, and the
row count survives `git clean`.

### Slice E3 — Learning Wiring

Connect the starved spine (A2) to production, fed by E1/E2 signals only.

Deliverables:

1. `quality_memory_index` is rebuilt from the experience log (not from
   transient `build/` artifacts) and persisted automatically at
   apply/closeout time — no `--write` flag dependency.
2. Production ranking passes the persisted index into
   `candidate_rank.score_manifest` (MCP `rank_candidates` included).
   The existing ±0.25 clamp and ≥3-attempt floor stay.
3. The proposer reads history: `candidate_generator` consults the experience
   log and suppresses (or down-ranks with an explicit
   `suppressed_by_history` marker) an `edit_family` already `rejected` or
   `regressed` on the same `subregion_key`.

Fail-loud requirement: when a family is suppressed by history, the candidate
set must say so; silent shrinkage of the proposal space is forbidden.

Stop condition: a family that produced `regressed`/`rejected` on a subregion
in run N is demoted or suppressed in run N+1, demonstrated on a real fixture,
and the demotion is visible in the emitted candidate set.

### Slice E4 — Self-Diagnosis Wiring

Turn measure-only stop machinery into routed behavior (A7).

Deliverables:

1. `run_loop` calls `diagnose_run`; `route_stop_cause` gains its first
   production caller. Stop cause becomes part of the loop result contract,
   not a test-only artifact.
2. Self-fixable plumbing stops execute their remedy instead of printing it:
   critique MISSING/STALE regenerates critique evidence;
   `stale_detector_evidence` re-runs detectors/compile. Each auto-remedy is
   followed by a fail-loud re-classification — if the same cause recurs
   immediately, stop hard with `remedy_ineffective` instead of looping.
3. Tool-defect attribution: `lever_exhausted` and repeated
   `decision_weak` emit rows into the v0.12 Slice 5 tool-defect ledger, so
   "my tooling is the problem" becomes repo work, not silence.
4. Detector demotion loop (second independent loop, cheap): a reader for
   `detector_log.jsonl` that computes per-detector false-positive rates from
   adjudication outcomes and emits demotion recommendations (fulfills the
   docstring promise in A10). Recommendation-only in this slice.

Stop condition: a run that previously ended with a printed command string now
either progresses past that stop without human action, or stops with
`remedy_ineffective` and a tool-defect row.

### Slice E5 — Gate Replacement (not gate removal)

The human gate is replaced by verifier evidence, per gate, only where the
evidence exists. The current string gate is weaker than any verifier gate
(A11), so this slice increases safety while increasing autonomy.

| Gate | Today | Replacement evidence |
| --- | --- | --- |
| Candidate acceptance | two nonempty strings | auto-accept iff: all class verifiers pass + detector_recheck non-regressing + `quality_movement != regressed` + rollback available. Otherwise route to human with the failing evidence named |
| Adjudication `decision:apply` | human file edit | auto-promote iff detector geometry confirms the finding AND the finding class has ≥3 historical `improved` outcomes in the experience log for the same family (E3 data) |
| `needs_human` aesthetic/external/reference overrides | always human | stays human. Taste remains out of scope for autonomy in v0.13 |
| accepted/golden/final, release exports | human | stays human, unchanged from v0.11/v0.12 safety boundaries. Additionally: attestation must be machine-verifiable (HMAC path, `human_attestation.py`), never prose (closes the A11 substring hole) |
| Mislabeled families (A8) | silent no-op nudge | fail-loud: either a real transform or an explicit `unsupported_candidate_family` refusal. Silent fallthrough is a spec violation |

Normative rule: **no gate is deleted; every gate is either automated by named
verifier evidence or kept human.** An autonomy step without a fail-loud
verifier is out of spec (per the 2026-06-25 direction correction).

Stop condition: a full propose→apply→verify cycle completes on a real fixture
with zero human strings written, and a forced-regression test shows the same
cycle auto-rolling back and recording `regressed`.

### Slice E6 — Exploration and Cross-Fixture Generalization

Absorbs v0.12 Slice 6 and v0.11 v3. Requires ≥1 fixture with a populated
experience log (E2) — the ml-advisory lesson (A12) forbids building policy
before labels exist.

Deliverables:

1. Replace the `contextual_bandit_beam_v0` label with a real ε-greedy or
   Thompson-sampling arm selection over edit families, with arm statistics
   computed from the experience log. Explicit JSON decisions; no opaque model
   dependency (v0.12 rule stands).
2. `quality_next_experiment` stops returning a constant: it proposes the
   highest-information next run (fixture × family) from arm uncertainty.
3. Cross-fixture: `build_suite_index` runs over all experience logs;
   family priors transfer across fixtures with a provenance field so a
   fixture-local signal can be distinguished from a transferred one.
4. Longitudinal substrate (A14): benchmark runs append to a trend file;
   a regression in loop capability (e.g., auto-accept precision drops) is
   itself a tool defect.

Stop condition: `quality_next_experiment` output changes as the experience
log grows, and a suite-level report shows per-family win rates across ≥2
fixtures.

## Metrics for the loop itself

The system must be able to answer, from persisted data only:

- auto-accept precision: fraction of auto-accepted candidates later reverted
  by human or rollback (target: measured first, then bounded);
- wasted-iteration rate: fraction of iterations whose candidate was a
  historical repeat or a no-op nudge (A8 detector);
- stop-cause histogram per week and the fraction of stops auto-remedied (E4);
- experience-log growth per run (a run that learns nothing is itself a
  finding).

These four are the dashboard v0.11 v3 promised; they are the loop's own
critique surface.

## Non-Goals

- No revival of the ML advisory sidecar (A12) and no opaque learned model
  anywhere in the decision path. Arm statistics and priors are explicit JSON.
- No autonomy over taste-class decisions (aesthetic direction, reference
  balance) in this version.
- No removal of release-boundary human authority (accepted/golden/final).
- No new measurement instruments; v0.13 only joins, persists, and routes
  signals the pipeline already produces.

## Risks

- **Reward remains too sparse**: with rejects persisted and negatives emitted,
  the ≥3-attempt floor may still be slow to cross on a single fixture.
  Mitigation: counterfactual `unchosen` rows and cross-fixture transfer (E6).
- **Auto-remedy loops**: E4 remedies must be idempotent and
  once-per-cause-per-run (`remedy_ineffective` backstop).
- **Gaming pressure moves upstream**: once strings stop gating, the incentive
  shifts to detector/verifier outputs. Verifiers stay subprocess/byte-derived;
  any LLM-text-derived field is annotation, never gate input.
