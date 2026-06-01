# Issue 100V - SVG Polish Positive Harness

Status: completed; merged to main in `fb57028`

Type: SVG polish positive path, deterministic harness, final-artifact workflow

Depends on:

- Issue 90 - SVG polish aesthetic gate hardening
- Issue 100D - SVG polish positive-route recipe template
- Issue 100S - final warning budgets and audit-evidence surfacing

## Problem

The SVG polish route has strong negative gates: it refuses semantic repair,
human art-direction ambiguity, stale evidence, unbounded edit classes, and
release/golden mutation. The missing positive proof is narrower: the repository
needs a durable checked-in harness that shows the route can actually close when
all required evidence is present.

Real fixtures are not suitable for this proof because `ready_for_svg_polish`
is an art-direction judgment and may correctly remain rare. The harness must
prove plumbing closure without claiming that any real figure should enter SVG
polish.

## Goal

Create a deterministic fixture-shaped SVG polish harness that exercises:

1. bounded recipe generation;
2. recipe execution into `polish/<name>.polished.svg`;
3. aesthetic delta pack generation;
4. semantic diff generation;
5. handoff audit and manifest writing;
6. status final-artifact classification as `FRESH`;
7. `/fig_drive --mode polish` closure with `action: complete`;
8. audit-evidence completeness, including zero-candidate reports.

## Scope

In scope:

- checked-in fixture seed under `tests/fixtures/svg_polish_positive_demo`;
- reusable script `scripts/svg_polish_positive_harness.py`;
- focused pytest coverage for success and destructive-safety failure modes;
- README and Issue 100 inventory updates.

Out of scope:

- real paper-figure SVG editing;
- host-vision critique generation;
- accepted, golden, export, or publication mutation;
- any claim that SVG polish improves a real fixture aesthetically;
- external renderer dependencies.

## Public Contract

Run:

```bash
uv run python3 scripts/svg_polish_positive_harness.py --force
```

Expected core JSON:

```yaml
schema: figure-agent.svg-polish-positive-harness.v1
fixture: svg_polish_positive_demo
status:
  final_artifact_kind: polished_svg
  final_artifact_state: FRESH
driver:
  action: complete
  safe_command: null
  stop_boundary: null
```

The default work directory is `.scratch/svg-polish-positive-harness`. The
harness refuses to replace an existing directory unless `--force` is supplied
and the directory is marked as one of its own previous outputs.

## Acceptance Criteria

- [x] Harness exits 0 and prints schema
      `figure-agent.svg-polish-positive-harness.v1`.
- [x] Generated artifacts stay under an ignored harness work directory.
- [x] Source export SVG is not overwritten by polish execution.
- [x] `final_artifact_state` reaches `FRESH`.
- [x] Polish driver reaches `action: complete` and `stop_boundary: null`.
- [x] Driver reason does not leak `audit_evidence missing_input`.
- [x] Forced replacement refuses unmarked directories.
- [x] Focused tests cover success and safety failure modes.

## Review Questions

1. Does this prove workflow closure without claiming aesthetic quality?
2. Does it avoid mutating real examples or tracked generated artifacts?
3. Does it reuse existing SVG polish modules instead of inventing another state
   machine?
4. Does it materialize the same audit-evidence inputs required by current
   status/driver contracts?

## Result

The harness is a plumbing proof, not a production promotion policy. It closes
the gap between a recipe starter and a complete SVG polish final-artifact
handoff while preserving the rule that real fixtures need their own
`ready_for_svg_polish` evidence before entering SVG editing.
