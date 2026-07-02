# Authoring Design Layer Waves Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next layer that lets `figure-agent` propose concrete visual/style directions with evidence, without pretending to replace human taste or bypassing source/release gates.

**Architecture:** Keep the existing quality kernel as the authority for state, compile, export, queue, and release boundaries. Add a thin authoring/design layer above the current style benchmark, candidate, and human-decision packet surfaces so agents can generate bounded proposal packets, compare them against benchmark criteria, and ask humans to judge specific choices instead of raw artifacts.

**Tech Stack:** Python scripts under `plugins/figure-agent/scripts`, existing fixture contracts under `plugins/figure-agent/examples`, pytest, ruff, compileall, and the `plugins/figure-agent/bin/fig-agent` wrapper from the plugin cwd.

---

## Current Truth This Plan Assumes

`figure-agent` is a paper-figure quality kernel, not a general image-generation orchestrator. The durable parts are Style Lock, compile/export reliability, deterministic QA, state inference, queue routing, context packs, benchmark packets, decision records, and explicit human/release gates.

The recent work already added these building blocks:

- Five-bucket queue bottleneck taxonomy: `mechanical_tool`, `host_critique`, `human_acceptance`, `reference_context`, `template_style`.
- Human-gate decision packet policy: the agent must recommend a bounded choice before asking for feedback.
- Style benchmark candidate packs and comparison packets.
- Typography Style Lock rule for benchmark packets.
- SVG polish readiness evidence surfaced in polish queues.
- Candidate sandbox, candidate review packet, candidate acceptance, and semantic review surfaces.

The remaining gap is not "more loop automation." The gap is a repeatable authoring/design layer that can say:

- keep the current style;
- apply a bounded TikZ refinement;
- escalate to a broader editorial redesign;
- prepare SVG polish only when positive evidence says that is the right route;
- stop for human judgment with a concrete recommendation and alternatives.

## Hard Boundaries

These boundaries are product contracts, not optional implementation preferences.

- Do not mutate `accepted`, tracked golden exports, final artifacts, or release state from this plan.
- Do not use SVG polish as a semantic or source repair path.
- Do not add plugin-side image-generation or vision API calls.
- Do not make `/fig_loop` or queue execution silently patch source.
- Do not ask the human to inspect from scratch; always produce a decision, choice, or patch proposal packet.
- Do not treat detector silence as proof of good taste. Detector pass only means "no known deterministic blocker."
- Do not promote a candidate unless its source hash, candidate hash, render evidence, and semantic review state are fresh.
- Do not run commands from repo root when the plan says plugin cwd; use `cd plugins/figure-agent`.

## File Responsibility Map

Expected files to modify or create:

- Modify `plugins/figure-agent/scripts/fig_queue.py`
  - Surface design-layer readiness in queue rows and summaries.
  - Keep queue read-only.
- Modify `plugins/figure-agent/scripts/style_benchmark_pack.py`
  - Tighten pack schema only when needed for design-layer decisions.
- Modify `plugins/figure-agent/scripts/style_benchmark_comparison.py`
  - Carry design recommendation state and candidate-family decision reasons.
- Modify or create `plugins/figure-agent/scripts/design_direction_packet.py`
  - Build a normalized human-facing packet from queue state, benchmark pack, comparison packet, candidate review packet, and SVG polish readiness.
- Modify `plugins/figure-agent/scripts/human_decision_record.py`
  - Accept only explicit design-direction decisions that do not authorize mutation.
- Modify candidate modules under `plugins/figure-agent/scripts/candidates/`
  - Reuse candidate sandbox/review/semantic review for bounded TikZ candidates.
  - Do not introduce broad freeform patching.
- Create or update tests:
  - `plugins/figure-agent/tests/test_design_direction_packet.py`
  - `plugins/figure-agent/tests/test_fig_queue.py`
  - `plugins/figure-agent/tests/test_style_benchmark_pack.py`
  - `plugins/figure-agent/tests/test_quality_benchmark_compare.py`
  - `plugins/figure-agent/tests/test_candidate_review_packet.py`
- Create dogfood docs under `plugins/figure-agent/docs/milestones/`.
  - Each dogfood doc records exact commands, current fixture state, recommendation, human question, and stop condition.

## Implementation Waves

### Wave 0: Preflight And State Freeze

**Outcome:** The implementing agent proves it is working from the current plugin state before editing code.

**Files:**
- No planned file edits.

- [ ] **Step 1: Confirm worktree state**

Run:

```bash
git status --short
git rev-parse --show-toplevel
```

Expected:

- The repo root is `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]`.
- Any dirty files are named in the implementation log before Wave 1 starts.
- Dirty fixture source under `plugins/figure-agent/examples/**` is treated as user-owned unless this plan or a newer human instruction explicitly opens that file.

- [ ] **Step 2: Confirm plugin command surface from plugin cwd**

Run:

```bash
cd plugins/figure-agent
./bin/fig-agent queue --mode review --goal design-layer-preflight --json
./bin/fig-agent queue --mode polish --goal design-layer-preflight --json
```

Expected:

- Both commands exit `0`.
- Both JSON payloads have `errors: 0`.
- If either command reports workspace diagnostics or missing examples, stop and fix the workspace/cwd contract before Wave 1.

- [ ] **Step 3: Record preflight evidence**

Add a short implementation note to the first Wave 1 commit message body or to the dogfood milestone doc created in Wave 5:

```text
Preflight:
- git status before Wave 1: <summarize dirty files or clean>
- review queue preflight: errors=0
- polish queue preflight: errors=0
- fixture source mutation opened by human: no
```

### Wave 1: Design Direction Packet Schema

**Outcome:** A read-only packet can summarize the agent's recommendation and alternatives for one fixture.

**Files:**
- Create: `plugins/figure-agent/scripts/design_direction_packet.py`
- Create: `plugins/figure-agent/tests/test_design_direction_packet.py`
- Modify: `plugins/figure-agent/scripts/human_decision_record.py`
- Modify: `plugins/figure-agent/tests/test_human_decision_record.py`

- [ ] **Step 1: Write failing tests for packet shape**

Create tests that expect this minimum packet:

```json
{
  "schema": "figure-agent.design-direction-packet.v1",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "state": "ready_for_human_choice",
  "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
  "alternatives": [
    "current_style",
    "bounded_tikz_refinement",
    "editorial_redesign",
    "svg_polish_handoff"
  ],
  "mutation_boundary": "no_source_mutation",
  "human_question": "I recommend keeping the current style unless a candidate beats the benchmark. Which direction should I prepare next?",
  "next_agent_action": "prepare_bounded_candidate_or_stop_for_human_choice"
}
```

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_design_direction_packet.py tests/test_human_decision_record.py
```

Expected before implementation: at least one failure because `design_direction_packet.py` does not exist or the decision kind is unsupported.

- [ ] **Step 2: Implement minimal packet builder**

Implement a pure function:

```python
def build_design_direction_packet(
    fixture: str,
    *,
    queue_row: dict[str, object],
    style_pack: dict[str, object] | None,
    comparison: dict[str, object] | None,
    svg_polish_state: dict[str, object] | None = None,
) -> dict[str, object]:
    fixture_identity.validate_fixture_name(fixture)
    if not style_pack or style_pack.get("state") != "present":
        return {
            "schema": "figure-agent.design-direction-packet.v1",
            "fixture": fixture,
            "state": "blocked_missing_style_pack",
            "mutation_boundary": "no_source_mutation",
            "alternatives": [],
            "blocking_reasons": ["style_benchmark_pack_missing"],
            "next_agent_action": "create_style_benchmark_pack",
        }
    if not comparison or comparison.get("state") != "present":
        return {
            "schema": "figure-agent.design-direction-packet.v1",
            "fixture": fixture,
            "state": "blocked_missing_comparison",
            "mutation_boundary": "no_source_mutation",
            "alternatives": [],
            "blocking_reasons": ["style_benchmark_comparison_missing"],
            "next_agent_action": "create_style_benchmark_comparison",
        }
    return {
        "schema": "figure-agent.design-direction-packet.v1",
        "fixture": fixture,
        "state": "ready_for_human_choice",
        "default_recommendation": comparison.get(
            "default_recommendation",
            "keep_current_style_until_candidate_beats_benchmark",
        ),
        "alternatives": [
            "current_style",
            "bounded_tikz_refinement",
            "editorial_redesign",
            "svg_polish_handoff",
        ],
        "mutation_boundary": "no_source_mutation",
        "human_question": (
            "I recommend keeping the current style unless a candidate beats the "
            "benchmark. Which direction should I prepare next?"
        ),
        "next_agent_action": "prepare_bounded_candidate_or_stop_for_human_choice",
        "source_queue_action": queue_row.get("action"),
        "svg_polish_state": (svg_polish_state or {}).get("state", "not_checked"),
    }
```

Rules:

- Validate fixture names with `fixture_identity.validate_fixture_name`.
- Return `state="blocked_missing_style_pack"` when the pack is missing.
- Return `state="blocked_missing_comparison"` when the pack exists but comparison evidence is missing.
- Return `mutation_boundary="no_source_mutation"` for all states in this wave.
- Include `human_question` only when the packet has enough evidence for a choice.
- Never return a command that mutates source, export, accepted state, golden state, or SVG.

- [ ] **Step 3: Add decision record compatibility**

Allow `human_decision_record.py` to validate a design-direction decision record only when:

- `packet_schema == "figure-agent.design-direction-packet.v1"`;
- `mutation_boundary == "no_source_mutation"`;
- decision is one of:
  - `keep_current_style`;
  - `prepare_bounded_tikz_refinement`;
  - `prepare_editorial_redesign_candidates`;
  - `prepare_svg_polish_handoff`;
  - `defer_design_decision`.

- [ ] **Step 4: Verify**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_design_direction_packet.py tests/test_human_decision_record.py
uv run ruff check scripts/design_direction_packet.py scripts/human_decision_record.py tests/test_design_direction_packet.py tests/test_human_decision_record.py
python3 -m compileall -q scripts/design_direction_packet.py scripts/human_decision_record.py
```

Commit:

```bash
git add scripts/design_direction_packet.py scripts/human_decision_record.py tests/test_design_direction_packet.py tests/test_human_decision_record.py
git commit -m "feat: add design direction packets"
```

### Wave 2: Queue Surfacing For Design Decisions

**Outcome:** `/fig_queue` exposes when a fixture needs design-direction evidence versus human taste judgment versus real mutation work.

**Files:**
- Modify: `plugins/figure-agent/scripts/fig_queue.py`
- Modify: `plugins/figure-agent/tests/test_fig_queue.py`
- Modify: `plugins/figure-agent/docs/milestones/2026-06-29-wave0-queue-bottleneck-plan.md` only if taxonomy text changes.

- [ ] **Step 1: Add failing queue tests**

Test rows for at least four cases:

- style pack missing;
- comparison missing;
- design packet ready for human choice;
- SVG polish requested but readiness evidence missing.

Expected row fields:

```json
{
  "design_direction_state": "ready_for_human_choice",
  "design_direction_packet_schema": "figure-agent.design-direction-packet.v1",
  "design_direction_default": "keep_current_style_until_candidate_beats_benchmark",
  "bottleneck_category": "template_style",
  "required_actor": "human"
}
```

- [ ] **Step 2: Wire packet builder into queue read-only path**

Add queue fields without changing command execution:

- `design_direction_state`;
- `design_direction_packet_schema`;
- `design_direction_default`;
- `design_direction_human_question`;
- `design_direction_next_agent_action`;
- `design_direction_blocker_reason`.

Rules:

- Missing benchmark/comparison remains `template_style`, not `mechanical_tool`.
- Human choice rows remain blocked in `/fig_queue_run`.
- Ready human-choice rows must not appear in executable command plans.
- Existing release/golden gates remain protected and should not be reclassified as design-only.

- [ ] **Step 3: Verify queue behavior**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_queue.py
./bin/fig-agent queue --mode review --goal design-direction-surfacing --json
./bin/fig-agent queue --mode polish --goal design-direction-surfacing --json
```

Expected:

- JSON output has `errors: 0`.
- Rows with human design choices are visible but not executable.
- SVG polish rows still require positive readiness evidence.

Commit:

```bash
git add scripts/fig_queue.py tests/test_fig_queue.py docs/milestones/2026-06-29-wave0-queue-bottleneck-plan.md
git commit -m "feat: surface design direction queue state"
```

### Wave 3: Bounded TikZ Candidate Family Expansion

**Outcome:** The tool can prepare narrow TikZ refinement candidates for known defect classes without jumping to broad redesign.

**Files:**
- Modify: `plugins/figure-agent/scripts/candidates/candidate_families.py`
- Modify: `plugins/figure-agent/scripts/candidates/candidate_generator.py`
- Modify: `plugins/figure-agent/scripts/candidates/candidate_review_packet.py`
- Modify: `plugins/figure-agent/tests/test_candidate_review_packet.py`
- Create or modify: `plugins/figure-agent/tests/test_candidate_generator.py`

- [ ] **Step 1: Add failing tests for supported design-safe families**

Add tests for these candidate families:

- `label_offset`;
- `text_width_refit`;
- `panel_spacing_adjustment`;
- `stroke_hierarchy_adjustment`;
- `nonsemantic_background_quieting`.

Each candidate must include:

- source hash;
- selector hash;
- rollback strategy;
- expected delta;
- semantic risks;
- required verification commands;
- `apply_authority` derived from fixture intent, never assumed.

- [ ] **Step 2: Implement one family at a time**

Start with `panel_spacing_adjustment` because it is the least semantically risky and matches `smoke_panel_spacing_demo`.

Candidate operations must be limited to marker-delimited or selector-hash-bound text replacement. Do not add raw line-number-only patches.

- [ ] **Step 3: Review packet must explain why the candidate is bounded**

Extend packet narrative fields so the human sees:

- what changes;
- what does not change;
- which semantic claims are protected;
- which command proves render freshness;
- why this is not SVG polish.

- [ ] **Step 4: Verify**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_candidate_review_packet.py tests/test_candidate_generator.py tests/test_semantic_candidate_review.py
uv run ruff check scripts/candidates tests/test_candidate_review_packet.py tests/test_candidate_generator.py
python3 -m compileall -q scripts/candidates
```

Commit:

```bash
git add scripts/candidates tests/test_candidate_review_packet.py tests/test_candidate_generator.py
git commit -m "feat: add bounded design candidate families"
```

### Wave 4: Editorial Redesign Is A Handoff, Not Auto-Patch

**Outcome:** Broad style redesign becomes a documented candidate-request packet with explicit semantic guardrails, not an automatic source mutation path.

**Files:**
- Create: `plugins/figure-agent/scripts/editorial_redesign_packet.py`
- Create: `plugins/figure-agent/tests/test_editorial_redesign_packet.py`
- Modify: `plugins/figure-agent/scripts/style_benchmark_comparison.py`
- Modify: `plugins/figure-agent/tests/test_quality_benchmark_compare.py`

- [ ] **Step 1: Add tests for handoff-only behavior**

Expected schema:

```json
{
  "schema": "figure-agent.editorial-redesign-packet.v1",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "mutation_boundary": "no_source_mutation",
  "candidate_request": {
    "target_style_class": "restrained editorial multipanel scientific schematic",
    "must_preserve": ["panel roles", "required labels", "semantic colors"],
    "must_not_do": ["semantic rewrite", "SVG polish as repair", "accepted/golden mutation"]
  },
  "human_question": "I can prepare editorial redesign candidates under these guardrails. Should I proceed with candidate preparation?"
}
```

- [ ] **Step 2: Implement packet builder**

The builder reads style benchmark pack and comparison evidence, then emits a request packet. It must not call a model, generate images, patch source, or create render artifacts.

- [ ] **Step 3: Link comparison result to handoff packet**

`style_benchmark_comparison.py` should allow `editorial_redesign` to be `eligible` only as a handoff. It must reject any comparison packet that marks editorial redesign as `winner_candidate` without a real rendered candidate and separate approval.

- [ ] **Step 4: Verify**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_editorial_redesign_packet.py tests/test_quality_benchmark_compare.py
uv run ruff check scripts/editorial_redesign_packet.py scripts/style_benchmark_comparison.py tests/test_editorial_redesign_packet.py tests/test_quality_benchmark_compare.py
python3 -m compileall -q scripts/editorial_redesign_packet.py scripts/style_benchmark_comparison.py
```

Commit:

```bash
git add scripts/editorial_redesign_packet.py scripts/style_benchmark_comparison.py tests/test_editorial_redesign_packet.py tests/test_quality_benchmark_compare.py
git commit -m "feat: add editorial redesign handoff packets"
```

### Wave 5: Dogfood On Three Fixture Classes

**Outcome:** Prove the design layer on protected, manuscript, and demo fixtures without hidden mutation.

**Files:**
- Create: `plugins/figure-agent/docs/milestones/2026-07-01-design-layer-dogfood.md`
- No fixture source edits unless a later human-approved implementation wave explicitly opens mutation.

- [ ] **Step 1: Run read-only queue scans**

Run:

```bash
cd plugins/figure-agent
./bin/fig-agent queue --mode review --goal design-layer-dogfood --json fig1_overview_v2_pair_001_vault fig3_trapping_concept smoke_panel_spacing_demo
./bin/fig-agent queue --mode polish --goal design-layer-dogfood --json fig1_overview_v2_pair_001_vault fig3_trapping_concept smoke_panel_spacing_demo
```

Record:

- design direction state;
- style benchmark state;
- comparison state;
- SVG polish evidence state;
- whether row is executable;
- exact human-facing question.

- [ ] **Step 2: Build dogfood decision packets**

For each fixture, record one packet:

- `fig1_overview_v2_pair_001_vault`: protected benchmark/release anchor. Default should be keep current style unless a candidate beats benchmark.
- `fig3_trapping_concept`: manuscript accept-current candidate. Default should be accept current generated export unless user wants extra typography polish.
- `smoke_panel_spacing_demo`: demo bounded-polish lane. Default should be prepare a bounded TikZ spacing candidate, not broad redesign.

- [ ] **Step 3: Review dogfood result for false confidence**

The doc must explicitly state whether any recommendation is based only on detector pass. Detector pass alone cannot justify "best style"; it can only justify "no known deterministic blocker."

- [ ] **Step 4: Verify no accidental mutation**

Run:

```bash
git status --short
git diff -- plugins/figure-agent/examples
```

Expected:

- No fixture source mutation from this wave.
- Only docs and code/test changes from earlier waves should be dirty or committed.

Commit:

```bash
git add docs/milestones/2026-07-01-design-layer-dogfood.md
git commit -m "docs: dogfood design direction packets"
```

### Wave 6: Operator Documentation And Stop Conditions

**Outcome:** Future agents know exactly when to keep going, ask the human, or stop.

**Files:**
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`
- Modify: `plugins/figure-agent/commands/fig_queue.md`
- Modify: `plugins/figure-agent/commands/fig_improve.md`
- Modify: `plugins/figure-agent/docs/architecture-overview.md`
- Create: `plugins/figure-agent/docs/milestones/2026-07-01-design-layer-operator-playbook.md`

- [ ] **Step 1: Add docs rule**

Document this operating rule:

```text
When a row reaches a human design gate, the agent must produce a decision packet
with recommendation, alternatives, evidence, risks, and exact next action.
The agent must not ask for open-ended inspection.
```

- [ ] **Step 2: Update command docs**

`fig_queue.md` and `fig_improve.md` must name the design-layer stop states:

- `blocked_missing_style_pack`;
- `blocked_missing_comparison`;
- `ready_for_human_choice`;
- `candidate_render_required`;
- `candidate_semantic_review_required`;
- `svg_polish_evidence_missing`;
- `release_or_golden_boundary`.

- [ ] **Step 3: Verify docs drift**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_queue.py tests/test_fig_improve.py
uv run ruff check scripts tests
python3 -m compileall -q scripts mcp tests
```

Commit:

```bash
git add skills/figure-agent/SKILL.md commands/fig_queue.md commands/fig_improve.md docs/architecture-overview.md docs/milestones/2026-07-01-design-layer-operator-playbook.md
git commit -m "docs: document design layer operator flow"
```

## End-To-End Verification

After all waves:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_design_direction_packet.py tests/test_editorial_redesign_packet.py tests/test_fig_queue.py tests/test_quality_benchmark_compare.py tests/test_candidate_review_packet.py tests/test_semantic_candidate_review.py
uv run ruff check scripts tests
python3 -m compileall -q scripts mcp tests
./bin/fig-agent queue --mode review --goal design-layer-final --json
./bin/fig-agent queue --mode polish --goal design-layer-final --json
```

Expected final evidence:

- Tests pass.
- Ruff passes.
- Compileall passes.
- Review and polish queues emit JSON with `errors: 0`.
- Design rows are visible but not executable when they need human choice.
- No release/golden/accepted mutation occurred unless a later human-approved wave explicitly opened it.

## First Review: Spec Coverage And Hidden Assumptions

Findings from the first review:

1. The original next-step framing could accidentally make "better style" mean "auto-generate new figure." This plan fixes that by making editorial redesign a handoff packet, not an auto-patch lane.
2. The human gate could regress into "please inspect." This plan requires a packet with recommendation, alternatives, evidence, risks, and exact next action.
3. SVG polish could become a shortcut for source defects. This plan keeps SVG polish behind positive readiness evidence and separate approval.
4. Queue rows could become executable by mistake. This plan requires human design rows to stay out of executable command plans.
5. Detector pass could be overclaimed as aesthetic quality. This plan states detector pass is only absence of known deterministic blocker.

Changes applied after review:

- Added hard boundaries.
- Added queue non-executable rule.
- Added detector false-confidence dogfood step.
- Added explicit editorial-redesign handoff wave.

## Second Review: Edge Cases And Failure Modes

Edge cases the implementation must preserve:

1. **Missing pack:** A fixture with no style benchmark pack must show `blocked_missing_style_pack`, not pretend no style issue exists.
2. **Missing comparison:** A fixture with a pack but no comparison must show `blocked_missing_comparison`.
3. **Protected golden fixture:** Tracked golden/release rows stay release-protected even if design packets exist.
4. **Accepted current fixture:** An accept-current recommendation must not mutate `accepted` or final artifacts.
5. **Dirty source:** Candidate and comparison evidence must fail closed if source hashes do not match current source.
6. **Symlink/path escape:** New packet builders must reject absolute paths, `..`, fixture symlinks, build/candidates symlinks, and plugin-local path escapes.
7. **Stale render evidence:** Candidate review packets must not imply a candidate is visually comparable without fresh render evidence.
8. **Semantic risk:** Any candidate with semantic risk requires semantic review and cannot be ranked as safe by detector deltas alone.
9. **Broad redesign:** Editorial redesign can be eligible only as a request/handoff until rendered candidates and separate human approval exist.
10. **SVG polish:** SVG handoff remains blocked unless `ready_for_svg_polish` evidence is present and source-level semantic defects are absent.
11. **Mode mismatch:** Authoring, review, polish, release, and final modes must not share mutation authority.
12. **Human wording:** Human questions must ask for a bounded choice, not a blank inspection.

Changes applied after review:

- Added explicit state names for command docs.
- Added source-hash and semantic-review requirements.
- Added symlink/path escape requirements for packet builders.
- Added protected golden and accepted-current constraints.

## Stop Condition

This plan is complete when the repo can produce design-direction packets that:

- are read-only by default;
- explain current recommendation and alternatives;
- name the next safe agent action;
- surface through `/fig_queue`;
- are backed by tests;
- preserve source/release/SVG/human gates;
- are dogfooded on protected, manuscript, and demo fixture classes.
