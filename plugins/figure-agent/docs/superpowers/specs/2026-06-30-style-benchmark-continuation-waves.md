# Style Benchmark Continuation Waves

Date: 2026-06-30

Status: continuation handoff for the next agent

Primary objective: continue the human-guided style benchmark work without
starting uncontrolled figure edits, SVG polish, release mutation, or golden
mutation.

## Current Truth

Working branch:

- `work/review-auto-fixes-2026-06-25`

Recent completed commits:

- `c2e9d78 docs: add wave c decision packets`
- `2a3f8bd docs: add wave c style benchmark pack`
- `d6bc45f test: validate style benchmark packs`

Known dirty file outside this work:

- `plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`

Do not touch, stage, commit, or normalize that file unless the user explicitly
assigns the fig5 hygiene slice.

Completed Wave C artifacts:

- `docs/decision-packets/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json`
- `docs/decision-packets/2026-06-30-wave-c/fig3_trapping_concept.json`
- `docs/decision-packets/2026-06-30-wave-c/smoke_panel_spacing_demo.json`
- `docs/decision-records/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json`
- `docs/decision-records/2026-06-30-wave-c/fig3_trapping_concept.json`
- `docs/decision-records/2026-06-30-wave-c/smoke_panel_spacing_demo.json`
- `docs/style-benchmark-packs/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json`
- `scripts/style_benchmark_pack.py`
- `tests/test_style_benchmark_pack_loader.py`

Latest known verification:

```bash
cd plugins/figure-agent
uv run ruff check scripts/style_benchmark_pack.py \
  tests/test_style_benchmark_pack_loader.py \
  tests/test_wave_c_style_benchmark_pack.py
uv run pytest -q tests/test_style_benchmark_pack_loader.py \
  tests/test_wave_c_style_benchmark_pack.py
uv run pytest -q tests/test_human_decision_record.py \
  tests/test_human_decision_record_examples.py \
  tests/test_wave_c_dogfood_packets.py \
  tests/test_wave_c_smoke_panel_spacing_packet.py \
  tests/test_wave_c_style_benchmark_pack.py \
  tests/test_style_benchmark_pack_loader.py \
  tests/test_fig_queue.py
```

Expected result from the broader suite at handoff time: `79 passed`.

## Strategic Boundary

The next work is not "make the figure prettier".

The next work is to make the agent show concrete style/release choices to a
human, record the human's decision, and only then open a bounded implementation
slice.

Hard boundaries:

- no fixture source mutation by default;
- no accepted-state mutation;
- no final-artifact mutation;
- no release-state mutation;
- no golden/export mutation;
- no SVG polish as a default repair path;
- no broad redesign until a benchmark comparison packet asks for it.

Human gate meaning:

- the agent must give a recommendation, alternatives, risks, and follow-up;
- the human judges those proposals;
- the human should not be asked to inspect raw artifacts from scratch.

## Wave D: Surface Style Benchmark Pack in Queue

Goal: make `/fig_queue` expose style benchmark context when a fixture has a
validated style benchmark pack.

Inputs:

- `scripts/style_benchmark_pack.py`
- `docs/style-benchmark-packs/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json`
- existing `/fig_queue` decision packet and handoff surfaces

Required behavior:

- If `style_benchmark_pack.load_pack(fixture)` returns `state: present`, add a
  read-only style benchmark summary to the relevant queue row, decision packet,
  or operator handoff.
- If the pack is missing, surface `style_benchmark_pack_state: missing` without
  failing the queue.
- Include only compact fields:
  - `target_style_class`;
  - `default_recommendation`;
  - candidate slot ids;
  - safety boundary;
  - linked benchmark/aesthetic files;
  - top human-only questions.
- Do not copy the full benchmark JSON into every row.

Likely files:

- `scripts/fig_queue.py`
- `scripts/style_benchmark_pack.py` only if the loader needs a small API helper
- `tests/test_fig_queue.py`
- `tests/test_style_benchmark_pack_loader.py` if loader behavior changes

Tests to add or update:

- fixture with pack exposes `style_benchmark_pack_state: present`;
- fixture without pack exposes `style_benchmark_pack_state: missing`;
- malformed pack does not silently become a recommendation;
- style benchmark summary never implies source, SVG, release, or golden
  mutation.

Verification:

```bash
cd plugins/figure-agent
uv run ruff check scripts/fig_queue.py scripts/style_benchmark_pack.py \
  tests/test_fig_queue.py tests/test_style_benchmark_pack_loader.py
uv run pytest -q tests/test_fig_queue.py tests/test_style_benchmark_pack_loader.py
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode release --goal style-benchmark-surface --json
```

Stop condition:

- the fig1 queue/handoff path can show the style benchmark summary;
- missing packs remain non-fatal;
- no fixture source or release artifacts changed.

## Wave E: Decision Record Style Choice Contract

Goal: make the human's style decision durable without confusing it with release
acceptance.

Inputs:

- `scripts/human_decision_record.py`
- `docs/decision-records/2026-06-30-wave-c/*.json`
- queue decision packets from Wave D

Required behavior:

- Add or confirm explicit style-choice decision ids:
  - `keep_current_style`;
  - `request_restrained_tikz_refinement`;
  - `request_editorial_redesign_benchmark`;
  - `request_svg_polish_handoff_evidence`.
- Recording a style decision must not authorize:
  - source mutation;
  - accepted-state mutation;
  - release mutation;
  - golden mutation;
  - SVG artifact mutation.
- A later implementation slice may read the record, but the record itself is
  policy state, not an edit.

Likely files:

- `scripts/human_decision_record.py`
- `tests/test_human_decision_record.py`
- `tests/test_human_decision_record_examples.py`
- optional new examples under `docs/decision-records/2026-06-30-wave-d/`

Tests to add or update:

- all style-choice ids validate;
- unknown style-choice id fails;
- release acceptance and style preference remain distinct;
- SVG handoff choice requires evidence language, not direct artifact mutation.

Verification:

```bash
cd plugins/figure-agent
uv run ruff check scripts/human_decision_record.py \
  tests/test_human_decision_record.py tests/test_human_decision_record_examples.py
uv run pytest -q tests/test_human_decision_record.py \
  tests/test_human_decision_record_examples.py
```

Stop condition:

- next agent can record "keep current style" or "request bounded style work"
  without touching figure source.

## Wave F: Candidate Comparison Packet

Goal: prepare for a possible style overhaul without starting source mutation.

Inputs:

- style benchmark pack for `fig1_overview_v2_pair_001_vault`
- any human style-choice decision from Wave E

Required behavior:

- Create a read-only comparison packet schema for candidate families:
  - current style;
  - restrained TikZ refinement;
  - editorial redesign;
  - SVG polish handoff.
- The packet must compare candidates against:
  - forbidden semantic changes;
  - benchmark measurable checks;
  - human-only art-direction questions;
  - mutation boundary.
- The packet can be created before any candidate source patch exists.

Likely files:

- new helper under `scripts/`, if executable;
- new docs under `docs/style-benchmark-comparisons/`;
- tests if executable schema is added.

Acceptance criteria:

- A future candidate can be rejected for being prettier but semantically worse.
- "Keep current style" remains a valid winner.
- No candidate family authorizes source/SVG mutation by itself.

Stop condition:

- comparison packet exists and validates;
- no source files changed.

## Wave G: Style Lock Extraction From Real Findings

Goal: add deterministic style checks only after a repeated failure class is
observed in Wave C-F artifacts.

Allowed rule families:

- local font-size override bans and hierarchy limits;
- stroke and arrow weight consistency;
- panel whitespace and title/caption density;
- semantic color economy;
- print-scale label readability.

Rules:

- Do not add a broad style score.
- Do not encode taste-only judgments as deterministic failures.
- Every new rule needs a fixture-backed or synthetic regression test.

Stop condition:

- at least one real repeated style issue becomes a narrow lint/test;
- non-measurable art direction remains in human decision packets.

## Wave H: SVG Polish Positive Evidence

Goal: keep SVG polish evidence-gated and find a true positive only if a human
decision asks for it.

Required behavior:

- `ready_for_svg_polish` remains the positive prerequisite.
- Negative cases must explain missing prerequisite evidence.
- SVG polish must not repair scientific, semantic, or label-target defects that
  belong in TikZ/source review.

Do not start this wave before Wave D/E surfaces the human decision clearly.

Stop condition:

- one candidate has explicit positive SVG-polish readiness evidence, or the
  queue explains why no current fixture qualifies.

## Wave I: Dirty Fig5 Hygiene

Goal: isolate the existing dirty fixture file from strategic style-benchmark
work.

Only run this wave if the user explicitly assigns it.

Required behavior:

1. inspect the dirty diff;
2. compile `fig5_actuation_mechanism`;
3. refresh status;
4. decide whether critique/export needs refresh;
5. commit separately from all decision-loop work.

Stop condition:

- either the dirty source is intentionally preserved, or fig5 is reconciled with
  compile/status evidence in a separate commit.

## Recommended Next Agent Start

Start with Wave D.

Suggested first prompt to self:

```text
Implement Wave D from
plugins/figure-agent/docs/superpowers/specs/2026-06-30-style-benchmark-continuation-waves.md.
Keep fig5 dirty file untouched. Surface style benchmark pack summary in
/fig_queue read-only outputs. Add tests for present, missing, and mutation-safe
behavior. Verify with ruff, targeted pytest, and one fig_queue JSON smoke.
```

Before editing:

```bash
git status --short
```

Expected pre-existing dirty line:

```text
 M plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex
```

If additional unrelated dirty files exist, do not overwrite them. Work around
them or stop only if they block the requested wave.

## Final Reporting Template

Each wave final report should include:

- wave completed;
- commit hash;
- files changed;
- verification commands and results;
- whether fixture source changed;
- whether accepted/final/release/golden/export state changed;
- remaining next wave.
