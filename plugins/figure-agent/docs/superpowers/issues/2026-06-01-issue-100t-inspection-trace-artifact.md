# Issue 100T - Optional Inspection Trace Artifact

Status: completed

Type: evidence trace, host/subagent audit accountability

## Problem

`crop_audit_log` records what the critique says about each crop, but it does not
record a durable transcript-level trace of which host, subagent, human, or tool
actually inspected which artifacts. Milestones often carry this evidence in
prose, which makes later review harder than it needs to be.

## Scope

Add a small optional artifact contract:

```yaml
schema: figure-agent.inspection-trace.v1
fixture: <name>
source: host_llm | subagent | human | external_tool
inspected_artifacts:
  - id: <crop-or-artifact-id>
    path: build/audit_crops/full_q1.png
    sha256: sha256:<artifact-content-hash>
    verdict: inspected | skipped | unavailable
    note: "<short rationale>"
```

In scope:

- parser/validator support for `inspection_trace.yaml`;
- a small `inspection_trace.py validate <fixture-dir>` CLI;
- optional `critique_lint.py` validation when the artifact is present;
- hash validation against the referenced local artifact;
- controlled errors for malformed YAML, missing required fields, duplicate IDs,
  missing artifacts, and stale hashes;
- missing trace remains `not_applicable`, not a blocker.

Out of scope:

- no host transcript scraping;
- no requirement that every fixture must provide this artifact;
- no gate changes in status, loop, driver, export, or release;
- no generated build artifact commits.

## Public Behavior

The contract is optional. When present, it can be loaded and validated as
evidence that a host/subagent/human/tool inspection claimed specific artifact
reads against specific content hashes. It is not a substitute for
`crop_audit_log`; it is an accountability sidecar for reviews.

Validation command:

```bash
uv run python3 scripts/inspection_trace.py validate examples/<name>
```

`critique_lint.py <name>` also validates the trace when it exists. Missing trace
remains non-blocking.

## Review Notes

- This should not pretend to prove that a model truly "looked" at pixels; it
  only makes the claimed read list durable and hash-bound.
- The trace is deliberately separate from critique freshness so old critiques
  remain parseable and existing gates do not change.
- Existing gates remain unchanged: missing trace is `not_applicable`, while an
  invalid present trace is surfaced by `critique_lint.py`.
