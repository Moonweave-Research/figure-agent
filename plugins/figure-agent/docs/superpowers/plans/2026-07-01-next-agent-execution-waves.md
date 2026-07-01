# Next Agent Execution Waves

Date: 2026-07-01

Status: active handoff plan for the next agent or OMX team

Primary objective: continue figure-agent development from the current verified
state without reopening completed work, bypassing human release gates, or
starting broad style redesign without benchmark evidence.

## Current Truth

Branch:

- `work/review-auto-fixes-2026-06-25`

Latest relevant commits:

- `3ca0f14 Add fig3 acceptance decision packet`
- `f571fc1 Refresh fig3 critique artifacts`
- `74ef9b1 Harden fig3 strict visual gates`
- `de2fecb Apply bounded TikZ candidate for fig3`

Latest verified fixture state for `fig3_trapping_concept`:

- `render_state=FRESH`
- `critique_state=FRESH`
- `export_state=FRESH`
- `workflow_ready=true`
- `closeout_complete=true`
- `release_ready=false`
- `acceptance_state=NOT_DECLARED`
- `final_artifact_state=NONE`
- first blocker: explicit release acceptance or final-artifact decision

New decision packet:

- `docs/decision-packets/2026-07-01-acceptance/fig3_trapping_concept_acceptance_packet.json`

That packet recommends `accept_current_generated_export`, but it is not itself
human acceptance. Do not set `accepted: true` unless the release operator
explicitly chooses that option.

## Total Diagnosis

The main blocker is no longer mechanical compile/export/critique failure.

The system can now:

- render and export the target fixture;
- refresh critique evidence against current detector and crop manifests;
- pass strict visual gates;
- produce a release decision packet with concrete choices;
- complete closeout after loop rerun.

The remaining weakness is the decision and authoring layer around the quality
kernel:

- Human gates still need durable decision records, not raw "please inspect"
  prompts.
- Release acceptance must remain explicit and separate from style preference.
- Style discomfort must be routed into benchmarked alternatives, not direct
  source mutation.
- SVG polish needs positive readiness evidence and semantic backport rules.
- Full redesign needs comparison packets and cannot be the default patch route.
- Queue/driver surfaces should show these distinctions compactly enough for a
  worker to act without re-reading every artifact.

## Hard Boundaries

- Do not mutate `accepted`, golden artifacts, final artifacts, or publication
  state without explicit human authority.
- Do not mutate fixture source in Wave 0 or Wave 1.
- Do not use SVG polish as a semantic repair path.
- Do not call external vision/image APIs from plugin-side code.
- Do not treat detector silence as proof of aesthetic quality.
- Do not ask the human to judge from scratch; present recommendation,
  alternatives, evidence, risks, and next action.
- Keep generated exports, `.scratch/`, and user-owned dirty work out of commits
  unless the wave explicitly opens them.

## Wave 0: Preflight And State Freeze

Outcome: prove the next agent is starting from the current state and not from a
stale queue or stale memory.

Files:

- No planned edits.

Steps:

1. Run:

   ```bash
   git status --short --untracked-files=all
   git log --oneline -6
   plugins/figure-agent/bin/fig-agent status fig3_trapping_concept --json
   plugins/figure-agent/bin/fig-agent closeout fig3_trapping_concept --json
   ```

2. Confirm:

   - worktree is clean or any dirty files are unrelated and explicitly named;
   - latest commit includes `3ca0f14`;
   - status has render/critique/export fresh;
   - closeout is complete;
   - release remains blocked only by `acceptance_state=NOT_DECLARED`.

Stop condition:

- If status or closeout regressed, repair that regression before Wave 1.
- If accepted/final-artifact state was externally changed, recompute the plan
  before continuing.

## Wave 1: Human Decision Digest And Record Contract

Outcome: turn release/style packets into durable decision records without
mutating figure source or release state.

Files likely touched:

- `plugins/figure-agent/scripts/human_decision_record.py`
- `plugins/figure-agent/tests/test_human_decision_record.py`
- `plugins/figure-agent/tests/test_human_decision_record_examples.py`
- new or updated docs under `plugins/figure-agent/docs/decision-records/`

Required behavior:

- Validate explicit decision kinds:
  - `accept_current_generated_export`
  - `declare_separate_final_artifact`
  - `reject_current_artifact`
  - `defer_for_dogfood`
  - `request_full_style_redesign`
  - `keep_current_style`
  - `request_bounded_tikz_source_polish`
  - `request_svg_polish_handoff_evidence`
- A decision record must cite the packet path and packet recommendation.
- A style decision must not imply release acceptance.
- A release acceptance decision must be distinguishable from the packet itself.
- Unknown decision ids fail validation.

Agent task split:

- Worker A: inspect current `human_decision_record.py` schema and tests.
- Worker B: inspect existing decision records and packet examples.
- Worker C: implement the smallest schema/test update and example record.

Verification:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_human_decision_record.py \
  tests/test_human_decision_record_examples.py
uv run ruff check scripts/human_decision_record.py \
  tests/test_human_decision_record.py tests/test_human_decision_record_examples.py
python3 -m compileall -q scripts/human_decision_record.py
```

Stop condition:

- The repo can record "defer for dogfood" or "accept current generated export"
  as a decision record without changing source or `accepted`.

## Wave 2: Release Acceptance Execution Surface

Outcome: make the release-state mutation path explicit, auditable, and blocked
unless a valid human decision record authorizes it.

Files likely touched:

- `plugins/figure-agent/scripts/status.py`
- `plugins/figure-agent/scripts/status_explanation.py`
- `plugins/figure-agent/scripts/golden_acceptance.py`
- `plugins/figure-agent/scripts/fig_closeout.py`
- tests under `plugins/figure-agent/tests/`

Required behavior:

- If a valid decision record says `accept_current_generated_export`, the next
  action may name the exact release-state mutation surface.
- The mutation still must not happen automatically from status, queue, loop, or
  closeout.
- If no valid decision record exists, status remains at
  `acceptance_not_declared`.
- If the record requests redesign or dogfood, release remains blocked and the
  next action routes to the requested non-release wave.

Verification:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_status.py tests/test_status_next_policy.py \
  tests/test_status_readiness_policy.py tests/test_golden_acceptance.py
uv run ruff check scripts/status.py scripts/status_explanation.py \
  scripts/golden_acceptance.py scripts/fig_closeout.py
```

Stop condition:

- The tool can explain "decision exists, but mutation still requires explicit
  release operation" without ambiguity.

## Wave 3: Design Direction Packet In Queue

Outcome: queue rows expose the concrete authoring decision layer so humans and
agents see recommended style direction, alternatives, and boundaries.

Files likely touched:

- `plugins/figure-agent/scripts/fig_queue.py`
- `plugins/figure-agent/scripts/design_direction_packet.py`
- `plugins/figure-agent/scripts/style_benchmark_pack.py`
- `plugins/figure-agent/scripts/style_benchmark_comparison.py`
- tests under `plugins/figure-agent/tests/`

Required behavior:

- For fixtures with style benchmark/comparison evidence, queue rows include a
  compact design-direction summary.
- Missing style packs are non-fatal and surfaced as
  `style_benchmark_pack_state=missing`.
- The summary must include:
  - default recommendation;
  - alternatives;
  - human question;
  - mutation boundary;
  - evidence refs.
- It must not include commands that mutate source, SVG, exports, acceptance, or
  golden state.

Verification:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_queue.py tests/test_design_direction_packet.py \
  tests/test_style_benchmark_pack_loader.py
uv run ruff check scripts/fig_queue.py scripts/design_direction_packet.py \
  scripts/style_benchmark_pack.py scripts/style_benchmark_comparison.py
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode release --goal design-direction-surface --json
```

Stop condition:

- `fig3_trapping_concept` and at least one benchmark fixture show a compact
  design/release decision summary in queue output.

## Wave 4: Bounded Candidate Or Redesign Benchmark Pack

Outcome: if the human decision requests dogfood or redesign, create evidence
packs before any source mutation.

Files likely touched:

- new docs under `plugins/figure-agent/docs/style-benchmark-comparisons/`
- optional helper under `plugins/figure-agent/scripts/`
- tests only if an executable helper/schema is added

Required behavior:

- Compare at least these families:
  - current generated export;
  - bounded TikZ source polish;
  - editorial redesign;
  - SVG polish handoff.
- Each family must state:
  - what can improve;
  - what semantic changes are forbidden;
  - what evidence would prove it is better;
  - what human-only question remains.
- "Keep current style" must remain a valid winner.

Stop condition:

- A future candidate can be rejected for being prettier but semantically worse.
- No source files changed.

## Wave 5: Bounded TikZ Candidate Only If Authorized

Outcome: implement one local source-polish candidate only when a decision record
or packet explicitly authorizes bounded TikZ work.

Files likely touched:

- target fixture `.tex`
- candidate/review artifacts under existing candidate directories
- focused tests or detector fixtures if behavior changes

Rules:

- Patch one local issue only.
- Preserve physics assertions and semantic layout.
- Run strict compile before claiming progress.
- Refresh critique/export/closeout if source changes.
- Do not combine with release acceptance mutation.

Verification:

```bash
plugins/figure-agent/bin/fig-agent compile <fixture> --strict
plugins/figure-agent/bin/fig-agent helper critique_lint.py examples/<fixture>
plugins/figure-agent/bin/fig-agent export <fixture> --skip-critique
plugins/figure-agent/bin/fig-agent closeout <fixture> --json
git diff --check
```

Stop condition:

- The candidate either improves benchmark evidence or is rejected with a
  durable reason.

## Wave 6: SVG Polish Readiness And Semantic Backport

Outcome: prepare SVG polish only for fixtures with positive evidence that
source-level TikZ work is no longer the right route.

Files likely touched:

- SVG polish readiness scripts and tests
- polish handoff/audit docs
- no generated polished SVG unless the wave explicitly authorizes it

Required behavior:

- `ready_for_svg_polish` requires positive evidence, not absence of defects.
- Any SVG change that alters semantic geometry must route to semantic backport.
- SVG polish cannot be used to hide source defects.

Stop condition:

- Queue/polish surfaces can explain why SVG polish is ready or not ready for
  the target fixture.

## Wave 7: System Hardening From Dogfood

Outcome: convert repeated dogfood pain into deterministic contracts.

Candidates:

- fix wrapper/path inconsistencies where direct scripts see `critique_state` as
  `NOT_REQUIRED` while `fig-agent status` sees `FRESH`;
- add tests for reference-free grounded critiques with
  `aesthetic_intent.yaml`;
- strengthen decision packet schema validation;
- add queue regression tests for `acceptance_not_declared` versus
  `closeout_complete`.

Verification:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_status.py tests/test_critique_adjudication.py \
  tests/test_fig_closeout.py tests/test_fig_queue.py
uv run ruff check scripts tests
python3 -m compileall -q scripts
```

Stop condition:

- A future agent cannot accidentally regress the current fig3 state into stale
  critique, stale adjudication, or ambiguous acceptance routing.

## Recommended Immediate Next Move

Start with Wave 1.

Reason:

- Wave 0 evidence is already green in this session, but the next agent should
  rerun it.
- Wave 1 is the missing product layer: it records the human-style/release
  decision without confusing that record with source edits or acceptance
  mutation.
- Wave 2 can then make release mutation safe and explicit.
- Waves 3-7 should not start before Wave 1 has a durable decision record
  contract.

## Completion Report Template

When a wave completes, report:

```text
Wave: <number and name>
Changed files:
- <path>
Validation:
- <command>: <result>
State:
- render_state=<value>
- critique_state=<value>
- export_state=<value>
- workflow_ready=<value>
- release_ready=<value>
Remaining blocker:
- <one line>
Next recommended wave:
- <number and reason>
```

