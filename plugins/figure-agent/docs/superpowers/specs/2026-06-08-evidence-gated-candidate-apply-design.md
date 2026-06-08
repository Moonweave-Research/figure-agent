# Evidence-Gated Candidate Apply Design

Status: Draft for user review
Date: 2026-06-08
Owner: figure-agent
Target release: post-candidate-render-evaluation-loop

## Problem

The current candidate workflow can generate a panel-level candidate, render it
inside `build/candidates/<candidate_id>/`, export before/after evidence, compute
deterministic visual deltas, and expose that evidence through CLI and MCP review
surfaces. The workflow still stops before controlled source mutation.

That is the correct safety boundary for the render/evaluation slice, but it
also means the tool cannot yet complete the practical loop from "this candidate
looks good" to "the fixture source was updated, rebuilt, verified, and can be
rolled back." The next upgrade must add an explicit evidence-gated apply path
that keeps human approval mandatory and makes every source mutation auditable.

## Goals

- Add an explicit candidate acceptance artifact that records the human decision
  required before source mutation.
- Add a CLI apply path that applies one rendered candidate to the fixture source
  only when the acceptance artifact, candidate manifest, render manifest, and
  current source state all match.
- Rebuild the fixture after apply and produce a post-apply verification report.
  Post-apply verification is allowed to write the normal fixture `build/` and
  `exports/` artifacts owned by `fig-agent compile`, `fig-agent export`, and
  `fig-agent status`.
- Create a reversible rollback patch before mutating source.
- Keep MCP/Cowork in review mode: MCP can prepare acceptance packets and report
  apply readiness, but it must not apply source changes.
- Preserve the existing workspace/plugin-root separation and candidate sandbox
  guarantees.

## Non-Goals

- No automatic apply from ranking score alone.
- No MCP apply tool that mutates source.
- No golden promotion.
- No broad multi-candidate merge.
- No LLM-only approval.
- No new third-party runtime dependency.
- No write access to Google Drive, CloudStorage, or paths outside the resolved
  `FIGURE_AGENT_WORKSPACE`.

## Public Interfaces

### CLI

Add readiness and apply commands:

```bash
fig-agent apply-candidate-ready <name> <candidate_id> \
  --candidate-set <path> \
  --json
```

```bash
fig-agent accept-candidate <name> <candidate_id> \
  --candidate-set <path> \
  --decision accept \
  --reviewer <name-or-id> \
  --rationale <text> \
  --json \
  [--output build/candidates/<candidate_id>/acceptance.json]
```

```bash
fig-agent apply-candidate <name> <candidate_id> \
  --candidate-set <path> \
  --acceptance build/candidates/<candidate_id>/acceptance.json \
  --json
```

Required behavior:

- `apply-candidate-ready` is read-only.
- `accept-candidate` writes only the acceptance artifact in the candidate
  sandbox.
- `apply-candidate` is the only new command that is allowed to mutate fixture
  source.
- `apply-candidate` must fail closed unless all hard gates pass.
- All stable JSON paths must be fixture-relative.

### MCP

MCP remains non-applying.

- `figure_agent_apply_candidate` continues to refuse source mutation.
- Add `figure_agent_candidate_apply_readiness` as a read-only MCP tool.
- Extend `figure_agent_compare_candidate` with an additive `apply_readiness`
  section that uses the same readiness evaluator as the MCP tool.
- MCP returns the exact CLI commands needed for local explicit apply.
- MCP must not create `acceptance.json`; acceptance is a local CLI act.

MCP tool schema:

```json
{
  "name": "figure_agent_candidate_apply_readiness",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["name", "candidate_id", "candidate_set"],
    "properties": {
      "name": {"type": "string"},
      "candidate_id": {"type": "string"},
      "candidate_set": {"type": "string"}
    }
  }
}
```

The MCP response embeds the same
`figure-agent.candidate-apply-readiness.v1` payload returned by
`fig-agent apply-candidate-ready`.

## Required Gates

`apply-candidate` must verify all gates before editing any source file:

- Fixture name and candidate ID are safe single path components.
- Candidate manifest exists under
  `examples/<name>/build/candidates/<candidate_id>/candidate_manifest.json`.
- Render manifest exists under
  `examples/<name>/build/candidates/<candidate_id>/render_manifest.json`.
- Acceptance artifact exists under the same candidate sandbox.
- Acceptance artifact has `decision: accept`, reviewer, timestamp, rationale,
  candidate hash, candidate set path, and render manifest hash.
- Candidate hash in acceptance, candidate manifest, and candidate set match.
- Render manifest status has:
  - `stages.compile.status: success`
  - `stages.export.status: success`
  - `stages.crop.status: success`
  - `stages.evaluate.status: rendered_needs_human_review`
- Candidate effective apply authority remains `review_only` before acceptance;
  acceptance grants one explicit source mutation, not ongoing auto-apply. The
  apply engine must use a new accepted-state evaluator and must not rely on the
  existing `effective_apply_authority()` result as the final permission check.
- Every operation is supported by the apply engine.
- For every `replace_text` operation, the exact `original` text appears once in
  the current source file.
- The target source path resolves inside the fixture and is not a symlink.
- Every target source file has a drift hash. The hash is read from
  `operation.source_sha256` when present, otherwise from exactly one
  `tex_selector.v1` selector whose `path` matches the operation path and whose
  `source_hash` is present. Readiness is blocked when a target operation has no
  drift hash.
- The current target source hash matches the drift hash before mutation.
- `apply_result.json` does not already record `status: applied` or
  `status: applied_with_failed_verification`.
- The fixture tree has no active mutation lock at:
  - `build/.candidate-apply-locks/mutation.lock`
  - `build/.mcp-locks/mutation.lock`
  - `build/.quality-locks/mutation.lock`

## Data Contracts

### Acceptance Artifact

Path:

```text
examples/<name>/build/candidates/<candidate_id>/acceptance.json
```

Required fields:

```json
{
  "schema": "figure-agent.candidate-acceptance.v1",
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "candidate_id": "CAND001",
  "candidate_hash": "sha256:...",
  "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
  "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
  "candidate_manifest_sha256": "sha256:...",
  "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
  "render_manifest_sha256": "sha256:...",
  "decision": "accept",
  "reviewer": "local-user",
  "reviewed_at": "2026-06-08T00:00:00Z",
  "rationale": "Panel C label offset improves mobility-edge readability.",
  "human_review_required": true
}
```

### Apply Result

Path:

```text
examples/<name>/build/candidates/<candidate_id>/apply_result.json
```

Required fields:

```json
{
  "schema": "figure-agent.candidate-apply-result.v1",
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "candidate_id": "CAND001",
  "status": "applied",
  "changed_files": [
    {
      "path": "fig1_overview_v2_pair_001_vault.tex",
      "before_sha256": "sha256:...",
      "after_sha256": "sha256:..."
    }
  ],
  "rollback_patch": "build/candidates/CAND001/rollback.patch",
  "post_apply": {
    "compile": {"status": "success"},
    "export": {"status": "success"},
    "status": {"status": "success"}
  },
  "diagnostics": []
}
```

## Architecture

### `candidate_acceptance.py`

Responsibilities:

- Build acceptance artifacts from an existing candidate manifest and render
  manifest.
- Hash candidate and render manifests.
- Validate decision metadata.
- Write only under the candidate sandbox.
- Reject symlinked acceptance paths and sandbox ancestor symlinks.

### `candidate_apply.py`

The existing apply module becomes the source mutation engine for explicit
candidate application.

Responsibilities:

- Load candidate set, candidate manifest, render manifest, and acceptance
  artifact.
- Verify every required gate.
- Create a rollback patch before mutation.
- Apply supported operations to source files.
- Re-run compile/export/status after mutation.
- Write `apply_result.json` in the candidate sandbox.

Hard constraints:

- It must not read from or write to plugin cache resources except bundled
  scripts/styles.
- It must not write into candidate render artifacts after apply except
  `apply_result.json` and rollback metadata.
- It must not mutate source when any gate fails.
- It must use exact text replacement only; fuzzy replacement is forbidden in
  this slice.

### `candidate_review_packet.py`

Extend review packets with an additive `apply_readiness` section:

```json
{
  "status": "ready_for_local_acceptance",
  "blocking_reasons": [],
  "required_commands": [
    "fig-agent accept-candidate ...",
    "fig-agent apply-candidate ..."
  ]
}
```

Status values:

- `not_rendered`
- `blocked`
- `ready_for_local_acceptance`
- `accepted_ready_to_apply`
- `applied`

### `candidate_rank.py`

Ranking remains advisory.

- Ranking can mark a rendered candidate as `ready_for_human_acceptance`.
- Ranking must not mark a candidate as accepted or applied.
- Ranking must surface blocking reasons when apply readiness fails.

## Safety Boundaries

- Apply writes are limited to fixture source files under `examples/<name>/`.
- Candidate sandbox writes are limited to
  `build/candidates/<candidate_id>/acceptance.json`,
  `build/candidates/<candidate_id>/rollback.patch`, and
  `build/candidates/<candidate_id>/apply_result.json`.
- Post-apply verification writes are limited to the normal fixture-owned
  `build/` and `exports/` outputs created by `fig-agent compile`,
  `fig-agent export`, and `fig-agent status`.
- Source path symlinks, candidate sandbox symlinks, and ancestor symlink escapes
  are rejected.
- Acceptance and apply paths reject absolute paths and `..`.
- The command must acquire `build/.candidate-apply-locks/mutation.lock` before
  mutation and must refuse to run when existing MCP or quality mutation locks
  are present.
- If post-apply compile/export fails, the source remains changed but the result
  must be `applied_with_failed_verification` and the rollback patch must be
  present. The command must not silently roll back because that hides state from
  the operator.
- Rollback execution is out of scope for this slice. This slice creates the
  rollback patch and reports its path.
- `rollback.patch` is a fixture-relative unified diff generated before source
  mutation from in-memory before/after source snapshots. For each changed file,
  the rollback diff direction is candidate-applied text back to original text:
  `fromfile` is `a/<relative-path>` for the candidate-applied version and
  `tofile` is `b/<relative-path>` for the original version. Multi-file rollback
  patches concatenate file diffs in operation order.
- Applying a candidate is not idempotent. A second apply attempt against a
  candidate sandbox with an applied apply result must fail with
  `already_applied`.

## Dogfood Scenario

Primary scenario:

```bash
fig-agent candidates fig1_overview_v2_pair_001_vault \
  --panel C \
  --family energy-trap-alignment \
  --json \
  --output build/candidates/panel_C_candidate_set.json

fig-agent render-candidates fig1_overview_v2_pair_001_vault \
  --candidate-set build/candidates/panel_C_candidate_set.json \
  --candidate-id CAND001 \
  --compile \
  --export \
  --crop-panel C \
  --evaluate \
  --json

fig-agent apply-candidate-ready fig1_overview_v2_pair_001_vault CAND001 \
  --candidate-set build/candidates/panel_C_candidate_set.json \
  --json

fig-agent accept-candidate fig1_overview_v2_pair_001_vault CAND001 \
  --candidate-set build/candidates/panel_C_candidate_set.json \
  --decision accept \
  --reviewer local-user \
  --rationale "Panel C mobility-edge label offset improves readability." \
  --json

fig-agent apply-candidate fig1_overview_v2_pair_001_vault CAND001 \
  --candidate-set build/candidates/panel_C_candidate_set.json \
  --acceptance build/candidates/CAND001/acceptance.json \
  --json
```

Pass condition:

- Acceptance and apply result artifacts are created in the candidate sandbox.
- The fixture source changes exactly once at the candidate operation target.
- Post-apply compile/export/status run and are recorded.
- Rollback patch exists.
- `compare-candidate` reports `applied` or
  `applied_with_failed_verification` with exact changed file hashes.
- No generated package or plugin cache includes user manuscript artifacts.

## Test Plan

### Contract Tests

- CLI help exposes readiness, acceptance, and apply commands.
- JSON schema validates acceptance and apply result fields.
- Stable JSON paths are fixture-relative.
- MCP schema exposes apply readiness but not source mutation.

### Safety Tests

- Reject candidate ID path traversal.
- Reject candidate set path escape.
- Reject acceptance path outside candidate sandbox.
- Reject symlinked source file.
- Reject symlinked candidate sandbox, acceptance, rollback, and apply result
  paths.
- Reject source mutation when render manifest is missing or failed.
- Reject source mutation when acceptance hash does not match current manifests.
- Reject source mutation when target source drift hash is absent.
- Reject source mutation when target source drift hash does not match.
- Reject source mutation when `original` text is missing or appears more than
  once.
- Reject source mutation when `apply_result.json` already records an applied
  state.
- Reject source mutation when candidate, MCP, or quality mutation locks exist.

### Runtime Tests

- Use a temp fixture with one `replace_text` operation.
- Generate acceptance artifact.
- Apply candidate and verify source text changed once.
- Verify rollback patch is created before source mutation.
- Verify rollback patch uses fixture-relative unified diff paths and reverses
  candidate-applied text back to original text.
- Mock compile/export/status for deterministic unit coverage.
- Verify failed post-apply compile records failure without deleting source
  evidence or hiding the changed state.
- Rewrite the existing refusal-only candidate apply tests so they assert the
  new gated apply contract instead of
  `apply_not_implemented_for_non_refusal_path`.

### Dogfood Verification

Run the primary scenario against
`fig1_overview_v2_pair_001_vault` after manually reviewing the before/after
Panel C crops.

## Risks

- Source files can drift between render and apply. Mitigation: hash and exact
  text gates fail closed.
- A rendered candidate can still be semantically wrong. Mitigation: human
  acceptance remains mandatory and review packet keeps semantic invariant
  checks visible.
- Post-apply compile can fail after source mutation. Mitigation: rollback patch
  is created first and failure is explicit in `apply_result.json`.
- Operators can accept the wrong candidate. Mitigation: acceptance includes
  candidate hash, render manifest hash, reviewer, timestamp, rationale, and
  candidate set path.

## Acceptance Criteria

- A rendered candidate cannot be applied without an explicit acceptance
  artifact.
- Applying a candidate mutates only fixture source files targeted by the
  candidate operations.
- Every apply attempt produces either a failed readiness diagnostic or a
  candidate-sandbox apply result.
- The operator can inspect source hashes, rollback patch, post-apply status,
  and visual evidence after apply.
- MCP remains non-mutating for source apply.
