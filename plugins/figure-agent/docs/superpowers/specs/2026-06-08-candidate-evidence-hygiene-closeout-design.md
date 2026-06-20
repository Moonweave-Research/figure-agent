# Candidate Evidence Hygiene and Closeout Gate Design

Status: Draft after dogfood apply
Date: 2026-06-08
Owner: figure-agent
Target release: post-evidence-gated-apply

## Problem

The figure-agent candidate loop can now generate candidates, render evidence,
require explicit human acceptance, mutate source under gates, and run
post-apply compile/export/status verification. The dogfood run on
`fig1_overview_v2_pair_001_vault` proved the loop works, but it also exposed
the next operational weakness: evidence truth is scattered.

After a candidate render, `render_manifest.json` may correctly say
`rendered_needs_human_review`, while the original `candidate_manifest.json` and
candidate set can still carry stale `visual_review: missing_render` metadata.
After apply, `apply_result.json`, tracked exports, `status`, `critique.md`, and
golden roll-forward state each tell part of the story. Operators can work
through this manually, but a production figure system needs one explicit
closeout surface that says what is current, what is stale, what is human-gated,
and what command is safe next.

One safety correction is required before this spec is implemented:
`apply-candidate` post-apply verification must not run export with
`--force-golden`. Candidate acceptance approves source mutation only; golden
roll-forward approval is a separate closeout decision.

## Goals

- Add an evidence hygiene layer that reconciles candidate set, candidate
  manifest, render manifest, acceptance, apply result, and status into one
  fixture-local evidence index.
- Prevent operator-facing surfaces from showing stale candidate review metadata
  as if it were current evidence, without rewriting acceptance-hashed candidate
  manifests after acceptance.
- Extend closeout reporting so candidate application evidence, critique state,
  export/golden state, and final release readiness are visible in one JSON
  packet.
- Add an explicit golden/closeout acceptance artifact rather than treating
  `--force-golden` as an implicit approval.
- Preserve existing safety boundaries:
  - default closeout inspection is read-only;
  - candidate source apply remains governed by `accept-candidate` and
    `apply-candidate`;
  - golden/export roll-forward remains explicit and human-gated;
  - no MCP tool mutates source or promotes golden state.
- Keep new artifacts inside `examples/<name>/build/evidence/`,
  `examples/<name>/build/closeout/`, or the existing candidate sandbox.

## Non-Goals

- No automatic golden promotion from candidate score, render score, or LLM
  judgment.
- No automatic rewrite of `critique.md`.
- No mutation of user manuscript/caption files.
- No change to the existing `fig-agent apply-candidate` gate.
- No candidate post-apply command may force golden export roll-forward.
- No new third-party runtime dependency.
- No write access to Google Drive, CloudStorage, or paths outside the resolved
  `FIGURE_AGENT_WORKSPACE`.

## Public Interfaces

### `fig-agent evidence-sync`

Read-only by default. With `--write`, it updates only generated evidence
metadata in fixture-local build directories.

```bash
fig-agent evidence-sync <name> \
  [--candidate-id <candidate_id>] \
  [--candidate-set build/candidates/<set>.json] \
  [--write] \
  --json
```

Behavior:

- Without `--write`, emit `figure-agent.evidence-sync.v1` and do not modify the
  workspace.
- With `--write`, update
  `examples/<name>/build/evidence/evidence_index.json`.
- Candidate manifests, render manifests, acceptance artifacts, apply results,
  source `.tex`, captions, briefing, critique, exports, and accepted/golden
  state are immutable from this command.
- Candidate set and candidate manifest files are not rewritten by this command.
  The evidence index carries the current overlay truth instead.
- Use `render_manifest.json` as the authoritative render evidence when it
  exists and passes schema checks. Do not rewrite `candidate_manifest.json` to
  mirror render state after candidate acceptance, because acceptance hashes bind
  the original manifest.
- If candidate set or manifest hashes do not match the render manifest, report
  `hash_mismatch` and refuse all writes.

### `fig-agent closeout-ready`

Read-only closeout readiness summary. This is a compact operator surface over
the existing `fig-agent closeout <name> --json` report plus the new evidence
index.

```bash
fig-agent closeout-ready <name> --json
```

Behavior:

- Emit `figure-agent.closeout-readiness.v1`.
- Include a deterministic checklist:
  - `candidate_apply`
  - `compile`
  - `critique`
  - `adjudication`
  - `export`
  - `golden_acceptance`
  - `final_artifact`
  - `release`
- Return exit `0` only when all required checks are `passed` or
  `not_required`.
- Return exit `1` when any check is `needs_action` or `blocked`.

### `fig-agent closeout-accept`

Explicit human acceptance for final closeout/golden roll-forward.

```bash
fig-agent closeout-accept <name> \
  --decision accept \
  --reviewer <name-or-id> \
  --rationale <text> \
  [--accept-golden] \
  --json
```

Behavior:

- Writes `examples/<name>/build/closeout/golden_acceptance.json`.
- Requires current `closeout-ready` checks to be complete except for
  `golden_acceptance`.
- Requires `--accept-golden` when `export_state` is `TRACKED_GOLDEN`.
- Records hashes of the current source, exports, critique, the canonical
  closeout-readiness payload, and latest candidate apply result when present.
- Does not run export by itself. The operator still runs
  `fig-agent export <name> --force-golden` after acceptance when the closeout
  packet recommends it.

### Existing `fig-agent closeout`

Keep existing read-only behavior. Extend its JSON output additively with:

```json
{
  "evidence_index_path": "build/evidence/evidence_index.json",
  "candidate_apply": {
    "status": "applied",
    "candidate_id": "CAND001",
    "apply_result_path": "build/candidates/CAND001/apply_result.json",
    "post_apply": {
      "compile": "success",
      "export": "success",
      "status": "success"
    }
  },
  "golden_acceptance": {
    "state": "missing",
    "path": "build/closeout/golden_acceptance.json"
  }
}
```

### MCP

MCP remains non-mutating.

- Add read-only `figure_agent_evidence_sync_preview`.
- Add read-only `figure_agent_closeout_ready`.
- Do not add an MCP closeout-accept or force-golden tool.
- MCP responses may include CLI commands for local explicit acceptance.

## Data Contracts

### Evidence Index

Path:

```text
examples/<name>/build/evidence/evidence_index.json
```

Schema:

```json
{
  "schema": "figure-agent.evidence-index.v1",
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "generated_at": "2026-06-08T00:00:00Z",
  "source": {
    "tex_path": "fig1_overview_v2_pair_001_vault.tex",
    "tex_sha256": "sha256:..."
  },
  "candidate": {
    "candidate_id": "CAND001",
    "candidate_hash": "sha256:...",
    "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
    "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
    "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
    "acceptance_path": "build/candidates/CAND001/acceptance.json",
    "apply_result_path": "build/candidates/CAND001/apply_result.json",
    "render_status": "rendered_needs_human_review",
    "apply_status": "applied",
    "post_apply": {
      "compile": "success",
      "export": "success",
      "status": "success"
    }
  },
  "status": {
    "render_state": "FRESH",
    "critique_state": "STALE",
    "export_state": "TRACKED_GOLDEN",
    "workflow_ready": false,
    "release_ready": false
  },
  "diagnostics": []
}
```

Required invariants:

- All paths are fixture-relative.
- Missing candidate/apply evidence is represented with `state: "missing"` or
  `null`; it is not an error for fixtures that have never used candidates.
- If `apply_result.status` is `applied`, `candidate.apply_status` must be
  `applied` and post-apply stage summaries must be copied from the result.
- If source hash differs from `apply_result.changed_files[].after_sha256`,
  candidate apply evidence is stale and closeout must block with
  `candidate_apply_stale`.

### Evidence Sync Result

```json
{
  "schema": "figure-agent.evidence-sync.v1",
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "mode": "preview",
  "writes": [],
  "blocking_reasons": [],
  "evidence_index": {}
}
```

With `--write`, `mode` is `write` and `writes` lists fixture-relative paths
that were updated.

### Closeout Readiness

Optional persistence path for future work:

```text
examples/<name>/build/closeout/closeout_packet.json
```

The first implementation emits the packet to stdout only and does not add a
`--write` flag. If a future slice persists the packet, it must use this schema:

```json
{
  "schema": "figure-agent.closeout-readiness.v1",
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "status": "blocked",
  "checks": [
    {
      "id": "candidate_apply",
      "state": "passed",
      "reason": "latest candidate apply result is applied and post-apply checks passed",
      "command": null,
      "evidence_path": "build/candidates/CAND001/apply_result.json"
    },
    {
      "id": "critique",
      "state": "needs_action",
      "reason": "critique_state is STALE",
      "command": "/fig_critique fig1_overview_v2_pair_001_vault",
      "evidence_path": "critique.md"
    }
  ],
  "next_action": "/fig_critique fig1_overview_v2_pair_001_vault",
  "evidence_index_path": "build/evidence/evidence_index.json"
}
```

### Golden Acceptance

Path:

```text
examples/<name>/build/closeout/golden_acceptance.json
```

Schema:

```json
{
  "schema": "figure-agent.golden-acceptance.v1",
  "figure_name": "fig1_overview_v2_pair_001_vault",
  "decision": "accept",
  "reviewer": "local-user",
  "reviewed_at": "2026-06-08T00:00:00Z",
  "rationale": "Current exports reviewed after candidate apply and critique refresh.",
  "accept_golden": true,
  "source_sha256": "sha256:...",
  "exports": {
    "pdf": "sha256:...",
    "svg": "sha256:...",
    "png": "sha256:...",
    "tif": "sha256:..."
  },
  "critique_sha256": "sha256:...",
  "closeout_readiness_sha256": "sha256:...",
  "latest_apply_result_sha256": "sha256:..."
}
```

## Required Gates

### Evidence Sync Gates

- Fixture name is a safe single path component.
- Candidate ID, when provided, is a safe single path component.
- Candidate sandbox ancestors are not symlinks.
- Candidate set path resolves inside `examples/<name>/`.
- Render manifest, when present, has a matching candidate ID and candidate hash.
- Candidate manifest, candidate set, and render manifest disagreeing on
  candidate hash blocks `--write`.
- `--write` refuses absolute paths, `..`, symlinked candidate set, symlinked
  candidate manifest, and symlinked evidence index.
- `--write` writes only `build/evidence/evidence_index.json`.

### Closeout Gates

`closeout-ready` must block release when any of these are true:

- latest candidate apply result is `applied_with_failed_verification`;
- latest candidate apply result is stale against current source;
- `status.render_state` is not `FRESH`;
- `status.critique_state` is `MISSING`, `STALE`, or `REFERENCE_MISSING`;
- critique adjudication is required but missing, invalid, or stale;
- `status.export_state` is not `FRESH` or `TRACKED_GOLDEN`;
- `status.export_state` is `TRACKED_GOLDEN` and no current
  `golden_acceptance.json` exists;
- final artifact state is `MISSING`, `INVALID`, `STALE`, or `BLOCKED`;
- publication gate reports failures.

`closeout-ready` may pass a tracked-golden closeout check only after current
`golden_acceptance.json` exists. This is separate from the existing
`status.release_ready` flag, which currently requires `EXPORT_FRESH`; the
closeout packet must report both values instead of pretending they are the same
gate.

## Implementation Plan

### Task 1: Evidence Index Builder

Files:

- Create `plugins/figure-agent/scripts/evidence_index.py`
- Test `plugins/figure-agent/tests/test_evidence_index.py`

Responsibilities:

- Resolve fixture paths through `runtime_paths`.
- Load source hash, status payload, latest candidate evidence, acceptance, and
  apply result.
- Prefer `render_manifest.json` over stale manifest `visual_review` fields.
- Emit `figure-agent.evidence-index.v1`.
- Provide `build_evidence_index(name, candidate_id=None, candidate_set_path=None,
  workspace_root=None, plugin_root=None)`.

Key tests:

- Render manifest overrides stale `candidate_manifest.visual_review`.
- Applied candidate with matching current source is `candidate.apply_status:
  applied`.
- Source drift after apply yields diagnostic `candidate_apply_stale`.
- Fixture with no candidate evidence still emits a valid index.
- Symlinked candidate sandbox is rejected.

### Task 2: Candidate Apply Golden Export Boundary

Files:

- Modify `plugins/figure-agent/scripts/candidate_apply.py`
- Test `plugins/figure-agent/tests/test_candidate_apply.py`

Responsibilities:

- Remove `--force-golden` from candidate post-apply export verification.
- Keep post-apply compile/export/status verification enabled.
- Treat tracked golden roll-forward as a closeout concern, not a candidate
  source-apply side effect.

Key tests:

- Post-apply export command includes `--skip-critique`.
- Post-apply export command does not include `--force-golden`.
- Candidate apply still records post-apply export status.

### Task 3: Evidence Sync CLI

Files:

- Modify `plugins/figure-agent/bin/fig-agent`
- Create `plugins/figure-agent/scripts/evidence_sync.py`
- Test `plugins/figure-agent/tests/test_evidence_sync.py`
- Extend `plugins/figure-agent/tests/test_candidate_cli_contract.py`

Responsibilities:

- Add `fig-agent evidence-sync`.
- Default preview mode is read-only.
- `--write` updates `build/evidence/evidence_index.json`.
- Evidence index render fields are updated from `render_manifest.json` only
  when hashes match.
- Candidate set files are never rewritten by evidence sync.
- Candidate manifest files are never rewritten by evidence sync.

Key tests:

- Preview mode does not change workspace tree.
- Write mode records an evidence-index overlay where stale
  `visual_review: missing_render` is superseded by
  `rendered_needs_human_review`.
- Write mode does not modify `candidate_manifest.json` or candidate set files.
- Write mode refuses hash mismatch.
- Write mode refuses symlinked evidence output.
- CLI JSON has stable schema and fixture-relative paths.

### Task 4: Closeout Readiness

Files:

- Create `plugins/figure-agent/scripts/closeout_readiness.py`
- Modify `plugins/figure-agent/scripts/fig_closeout.py`
- Modify `plugins/figure-agent/bin/fig-agent`
- Test `plugins/figure-agent/tests/test_closeout_readiness.py`
- Extend `plugins/figure-agent/tests/test_fig_closeout.py`

Responsibilities:

- Add `fig-agent closeout-ready <name> --json`.
- Build deterministic checklist from status, evidence index, existing
  closeout report, and publication gate.
- Preserve every existing `fig_closeout` blocker, including
  `text_boundary_checks` and `loop_rerun`, either as native checks or mapped
  checks.
- Extend existing `fig-agent closeout` JSON additively with candidate apply and
  golden acceptance sections.
- Return non-zero when readiness is incomplete.

Key tests:

- Current dogfood state blocks on `critique_stale`.
- Existing `text_boundary_checks` and `loop_rerun` blockers remain visible.
- Applied candidate with failed post-apply verification blocks on
  `candidate_apply_failed_verification`.
- Applied candidate with source drift blocks on `candidate_apply_stale`.
- `TRACKED_GOLDEN` without golden acceptance blocks on
  `golden_acceptance_missing`.
- `TRACKED_GOLDEN` with current golden acceptance passes the closeout golden
  check while still reporting existing `status.release_ready` truthfully.
- Non-candidate fixture can still close out without candidate evidence.

### Task 5: Golden Acceptance

Files:

- Create `plugins/figure-agent/scripts/golden_acceptance.py`
- Modify `plugins/figure-agent/bin/fig-agent`
- Test `plugins/figure-agent/tests/test_golden_acceptance.py`

Responsibilities:

- Add `fig-agent closeout-accept`.
- Allow the existing `fig_closeout` tracked-golden export block as the one
  expected pre-acceptance blocker when all earlier checks are complete.
- Require complete closeout checks except `golden_acceptance` and that
  tracked-golden export block.
- Require `--accept-golden` when export state is `TRACKED_GOLDEN`.
- Write `build/closeout/golden_acceptance.json`.
- Record hashes for source, exports, critique, canonical closeout readiness
  payload, and latest apply result.

Key tests:

- Missing reviewer or rationale is rejected.
- `TRACKED_GOLDEN` without `--accept-golden` is rejected.
- Stale critique prevents acceptance.
- Golden acceptance path symlink is rejected.
- Written artifact hashes current source/export/critique inputs.

### Task 6: MCP Read-Only Surfaces

Files:

- Modify `plugins/figure-agent/mcp/figure_agent_server.py`
- Test `plugins/figure-agent/tests/test_mcp_facade.py`

Responsibilities:

- Add `figure_agent_evidence_sync_preview`.
- Add `figure_agent_closeout_ready`.
- Ensure both tools are read-only and never write artifacts.
- Return local CLI commands for `fig-agent evidence-sync --write` and
  `fig-agent closeout-accept` when appropriate.

Key tests:

- MCP tool schemas have `additionalProperties: false`.
- MCP preview does not change workspace tree.
- MCP closeout ready reports same blocking check IDs as CLI readiness.
- MCP does not expose a mutating golden acceptance tool.

### Task 7: Release Gate and Dogfood

Files:

- Modify `plugins/figure-agent/scripts/release_gate.py`
- Add focused dogfood note under
  `plugins/figure-agent/docs/milestones/`
- Test `plugins/figure-agent/tests/test_release_contract.py`

Responsibilities:

- Add the new tests to the release contract.
- Dogfood on `fig1_overview_v2_pair_001_vault`.
- Do not package or commit user dirty `caption.md`.

Commands:

```bash
uv run ruff check \
  plugins/figure-agent/scripts/evidence_index.py \
  plugins/figure-agent/scripts/evidence_sync.py \
  plugins/figure-agent/scripts/closeout_readiness.py \
  plugins/figure-agent/scripts/golden_acceptance.py \
  plugins/figure-agent/bin/fig-agent \
  plugins/figure-agent/mcp/figure_agent_server.py \
  plugins/figure-agent/tests/test_evidence_index.py \
  plugins/figure-agent/tests/test_evidence_sync.py \
  plugins/figure-agent/tests/test_closeout_readiness.py \
  plugins/figure-agent/tests/test_golden_acceptance.py \
  plugins/figure-agent/tests/test_mcp_facade.py
```

```bash
uv run pytest -q \
  plugins/figure-agent/tests/test_evidence_index.py \
  plugins/figure-agent/tests/test_evidence_sync.py \
  plugins/figure-agent/tests/test_closeout_readiness.py \
  plugins/figure-agent/tests/test_golden_acceptance.py \
  plugins/figure-agent/tests/test_candidate_cli_contract.py \
  plugins/figure-agent/tests/test_fig_closeout.py \
  plugins/figure-agent/tests/test_mcp_facade.py \
  plugins/figure-agent/tests/test_release_contract.py
```

Dogfood commands:

```bash
FIGURE_AGENT_PLUGIN_ROOT="$PWD/plugins/figure-agent" \
FIGURE_AGENT_WORKSPACE="$PWD/plugins/figure-agent" \
plugins/figure-agent/bin/fig-agent evidence-sync \
  fig1_overview_v2_pair_001_vault \
  --candidate-id CAND001 \
  --candidate-set build/candidates/panel_C_candidate_set.json \
  --write --json
```

```bash
FIGURE_AGENT_PLUGIN_ROOT="$PWD/plugins/figure-agent" \
FIGURE_AGENT_WORKSPACE="$PWD/plugins/figure-agent" \
plugins/figure-agent/bin/fig-agent closeout-ready \
  fig1_overview_v2_pair_001_vault --json
```

Expected dogfood result before critique refresh:

- `candidate_apply` check passes.
- `compile` check passes.
- `critique` check is `needs_action` with command
  `/fig_critique fig1_overview_v2_pair_001_vault`.
- `golden_acceptance` is blocked or not yet reachable until critique is fresh.

## Acceptance Criteria

- Stale candidate `visual_review` metadata cannot mislead review packet,
  evidence sync, closeout, or MCP surfaces, and fixing the presentation layer
  does not rewrite acceptance-hashed candidate manifests.
- A fixture with an applied candidate has one evidence index that links
  candidate manifest, render manifest, acceptance, apply result, source hash,
  status, and export state.
- Closeout readiness produces one deterministic next action.
- Golden roll-forward requires an explicit acceptance artifact with reviewer
  and rationale.
- MCP remains read-only.
- The full focused test suite passes.
- Dogfood on `fig1_overview_v2_pair_001_vault` reports the correct next blocker:
  stale critique before golden closeout.

## Review

### Coverage Review

- Evidence scatter problem: covered by `evidence_index.py` and
  `evidence-sync`.
- Stale candidate visual metadata: covered by sync gates and review packet
  dependency on render manifest truth.
- Candidate apply closeout: covered by `candidate_apply` check and source hash
  drift gate.
- Critique/golden closeout: covered by closeout readiness and golden
  acceptance.
- MCP safety: covered by read-only MCP tools only.
- Dogfood path: covered by explicit commands and expected pre-critique blocker.

### Risk Review

- Risk: `evidence-sync --write` could become a hidden mutation path or break
  acceptance hashes.
  Mitigation: restrict writes to `build/evidence/evidence_index.json` after
  acceptance/apply exists; candidate manifests are immutable and tests assert
  source/caption/export plus accepted candidate manifests remain unchanged.
- Risk: closeout acceptance could be treated as export itself.
  Mitigation: `closeout-accept` records approval only and returns the explicit
  follow-up export command when `TRACKED_GOLDEN`.
- Risk: fixtures without candidate history could regress.
  Mitigation: evidence index treats candidate evidence as optional.
- Risk: duplicate truth between `fig_closeout.py` and new readiness module.
  Mitigation: `closeout_readiness.py` consumes existing closeout/status helpers
  and emits a compact checklist; it does not reimplement freshness logic.

### Open Decisions

- Whether golden acceptance should live under ignored `build/closeout/` only or
  have an optional tracked promotion file in a future release. This spec keeps
  it generated and fixture-local.
