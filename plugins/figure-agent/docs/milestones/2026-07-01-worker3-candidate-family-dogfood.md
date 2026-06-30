# Worker 3 Candidate Family Dogfood

Date: 2026-07-01

## Scope

Bounded candidate-family, review-packet, docs, and verification slice for the
candidate/design-safe surface. This slice expands and dogfoods read-only
candidate proposal metadata only.

Hard boundaries preserved:

- No accepted-state mutation.
- No tracked golden, release-state, final-artifact, or generated-export mutation.
- No fixture source mutation under `examples/`.
- No hidden fixture edits and no plugin-side image/vision API calls.
- Candidate operations remain sandbox proposals until a separate explicit apply
  path is invoked.

## Implemented slice

The candidate family surface now accepts design-safe family aliases through the
existing `fig-agent candidates --panel <id> --family <name>` path:

- `label_offset`
- `text_width_refit`
- `panel_spacing_adjustment`
- `stroke_hierarchy_adjustment`
- `nonsemantic_background_quieting`

Generated candidates carry boundedness metadata so review packets can explain:
what changes, what does not change, whether human review is required, and that
the candidate is not SVG polish.

Candidate render manifests preserve this boundedness, expected-delta, and
semantic-risk context, and `fig-agent review-candidate` surfaces it in
`manifest_summary`.

## Dogfood commands

All commands were run from plugin cwd:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_candidate_cli_contract.py tests/test_candidate_review_packet.py tests/test_candidate_generator.py
uv run ruff check scripts/candidates/candidate_families.py scripts/candidates/candidate_render.py scripts/candidates/candidate_review_packet.py tests/test_candidate_cli_contract.py tests/test_candidate_review_packet.py
python3 -m compileall -q scripts/candidates/candidate_families.py scripts/candidates/candidate_render.py scripts/candidates/candidate_review_packet.py
./bin/fig-agent queue --mode review --goal worker3-candidate-family-dogfood --json fig1_overview_v2_pair_001_vault fig3_trapping_concept smoke_panel_spacing_demo
./bin/fig-agent queue --mode polish --goal worker3-candidate-family-dogfood --json fig1_overview_v2_pair_001_vault fig3_trapping_concept smoke_panel_spacing_demo
git status --short -- examples
git diff -- examples
```

## Observed evidence

- Focused candidate tests: `56 passed`.
- Ruff on modified files: passed.
- Compileall on modified candidate modules: passed.
- Review queue dogfood: schema `figure-agent.fixture-driver-queue.v1`, three
  requested rows returned, no command execution was requested.
- Polish queue dogfood: schema `figure-agent.fixture-driver-queue.v1`, three
  requested rows returned, no command execution was requested.
- Both dogfood queue scans reported current clean-worktree compile freshness as
  the visible bottleneck for the three fixtures: `run_compile`,
  `mechanical_tool`, `workflow_agent`.
- `git status --short -- examples` and `git diff -- examples` produced no
  output; fixture sources and artifacts were not mutated by this slice.

## Stop condition

This slice stops at bounded candidate proposal metadata and review-packet
visibility. Applying candidates, accepting candidates, exporting, forcing golden,
or changing release/accepted state remains outside this worker slice.
