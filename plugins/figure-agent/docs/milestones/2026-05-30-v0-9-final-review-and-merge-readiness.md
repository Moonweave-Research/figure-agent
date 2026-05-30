# v0.9 Final Review And Merge Readiness

**Date:** 2026-05-30 KST
**Issue:** 89E - Final Review And Merge Readiness
**Status:** completed on `codex/issue70-guided-autonomy-roadmap`

## Scope

Final release-candidate review for the v0.9 operator-grade workflow.

This closeout covers:

- full local verification;
- package audit;
- secret scan;
- three critical review passes;
- PR readiness for branch `codex/issue70-guided-autonomy-roadmap`.

## Verification

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
python3 scripts/plugin_package_audit.py /tmp/figure-agent-package-audit.U2GqZH --max-mib 300
```

Results:

- Full pytest: `1471 passed, 1 skipped, 1 xfailed, 6 warnings`.
- Ruff: clean.
- Diff whitespace check: clean.
- Claude plugin validation: manifest, plugin directory, and marketplace passed.
- Package audit: `package_size_mib=49.8`, no junk in the generated package
  candidate.

Secret scan was run over the changed release files. It found only ordinary
documentation words such as `API keys`, `Subscription tokens`, and `secret
scan`; no secret value or private key was present.

## Review 1 - Contract And Documentation Consistency

Finding: closeout status still said final full verification was pending after
the full suite had passed.

Fix: update `docs/milestones/2026-05-21-plugin-development-closeout-status.md`
with the exact v0.9 verification result.

Post-fix status: clean. Manifest, `pyproject.toml`, `uv.lock`, README,
changelog, release contract tests, issue roadmap, and closeout status all agree
on v0.9.0 release-candidate truth.

## Review 2 - Execution Safety And Mutation Boundaries

Finding: polish queue rows can carry a `safe_command` while also having
`stop_boundary: mode_forbidden_action`.

Assessment: not a mutation defect. `/fig_queue --command-plan` blocks those rows
and `/fig_queue_run --actor workflow_agent` reports `planned_executable: 0` and
`executed_commands: 0`. The v0.9 operator playbook now states that command-plan
output is the authoritative batch execution surface.

Post-review status: clean. Host critique, human decision, release/golden,
accepted, SVG polish, and source-patch boundaries remain non-automatic.

## Review 3 - Packaging, Release Notes, And Operator Usability

Finding: running package audit directly on the development checkout flags local
generated paths. That is correct behavior but not the right release-package
test.

Fix: audit an isolated package candidate copied with generated build/export,
cache, and virtualenv paths excluded. Record this distinction in the 89B
package metadata milestone.

Post-review status: clean. The package candidate is small enough and free of
generated package junk; the v0.9 operator playbook gives a single command
sequence for single-fixture, queue, host critique, closeout, and release gates.

## Additional Post-PR Critical Review

After PR #80 was marked ready for review, three more defects were found and
fixed:

1. Issue 89 status still said `in progress` even though 89A-E were completed
   and the PR was ready. The issue status now says `completed for PR #80;
   pending merge`, and release-contract coverage rejects stale `Status: in
   progress` for the v0.9 issue set.
2. `svg_polish_delta_command()` shell-quoted the command but embedded fixture
   names directly inside Python `-c` source. Fixture names containing an
   apostrophe could break the generated Python code. The helper now uses
   `repr` for the embedded path, with regression coverage.
3. Queue command-plan blocked reasons prioritized missing `safe_command` before
   explicit `stop_boundary`. Stop boundaries now win, so an operator sees the
   actual boundary reason first; regression coverage pins
   `mode_forbidden_action`.

Post-fix verification:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

- Full pytest: `1471 passed, 1 skipped, 1 xfailed, 6 warnings`.
- Ruff: clean.
- Diff whitespace check: clean.
- Claude plugin validation: manifest, plugin directory, and marketplace passed.

## Remaining Risks

- Some real fixtures still require host critique, human acceptance, or release
  operator action. These are true workflow gates, not plugin release blockers.
- No fixture currently routes to SVG editor in the 89C corpus smoke; SVG polish
  remains explicit opt-in/handoff, not a default release path.

No known Issue 89E blocker remains.
