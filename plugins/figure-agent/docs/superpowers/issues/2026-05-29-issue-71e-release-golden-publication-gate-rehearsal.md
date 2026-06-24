# Issue 71E - Release, Golden, And Publication Gate Rehearsal

Status: completed

Depends on: Issue 71B, Issue 71C, and Issue 71D evidence

Type: HITL

## Problem

The plugin has accepted/golden/publication gates, but the operator flow needs a
real rehearsal after the guided-autonomy work. These boundaries are supposed to
stop, not auto-mutate. A release rehearsal should prove that the stop is clear
and that an operator can see exactly what would be required without accidental
golden or publication changes.

## Goal

Exercise release, accepted, tracked-golden, force-golden, and publication
provenance boundaries on selected real fixtures and record the safe operator
workflow.

## Scope

In scope:

- Run `/fig_status`, `/fig_drive --mode release --dry-run`, and relevant
  golden/publication check scripts on selected fixtures.
- Record which decisions require human approval.
- Verify that `/fig_run` does not execute accepted/golden/force-golden/release
  mutation.
- Document the exact human approval inputs needed before any future release
  artifact update.

Out of scope:

- Changing `accepted`.
- Running `--force-golden` without explicit user approval.
- Editing `QUALITY_AUDIT.md` as a silent fix.
- Publishing a release.
- Mutating SVG polish or source figure content.

## Acceptance

- A milestone records every release candidate, current gate state, dry-run
  driver action, and human approval requirement.
- `/fig_run` refuses release-only mutation paths.
- Golden/publication checks produce controlled output.
- No accepted/golden/publication file is changed unless the user explicitly
  authorizes that exact mutation.
- Full pytest, ruff, diff check, and plugin validation pass.

## Review Questions

1. Are release decisions explicit enough for a human operator?
2. Does the plugin prevent accidental golden roll-forward?
3. Are publication/provenance failures visible but non-fabricated?
4. Does the rehearsal identify the next release-hardening issue, if any?

## Closeout

Completed in milestone:

- `docs/milestones-archive/2026-05-29-release-golden-publication-gate-rehearsal.md`

Outcome:

- Release/golden/publication mutation containment passed.
- `/fig_run --execute --no-record` executed zero shell commands for every
  release rehearsal row.
- No accepted, golden, export, publication, source, SVG, or `.scratch` artifact
  was mutated.
- Several real release candidates are now correctly blocked first by stale
  host critiques after Issue 73 changed the critique generator hash. That is a
  freshness precondition, not a release-boundary defect.
