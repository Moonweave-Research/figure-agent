# v0.9 Release Notes And Operator Playbook

**Date:** 2026-05-30 KST
**Issue:** 89D - Release Notes And Operator Playbook
**Status:** completed on `codex/issue70-guided-autonomy-roadmap`

## Deliverable

Added `docs/v0.9-operator-playbook.md`.

The playbook records the current release-candidate operating model:

- single-fixture traffic control with `/fig_status` and `/fig_drive`;
- bounded mechanical execution with `/fig_run`;
- multi-fixture routing with `/fig_queue`;
- plan-first batch execution with `/fig_queue_run`;
- host critique refresh closeout;
- read-only closeout after patch/export;
- release/golden gate boundaries;
- explicit list of what v0.9 still does not automate.

## Why This Exists

By Issue 89C, the plugin behavior was already implemented and smoke-tested. The
remaining risk was operator confusion: a new user could still read scattered
command docs and miss the intended sequence. The playbook is the one-page route
through the release candidate.

## Guardrails Preserved

- No new runtime behavior.
- No source drawing changes.
- No generated export, build, SVG, accepted, golden, or publication mutation.
- No automatic host critique authoring.
- No hidden SVG polish.
- No external provider requirement.

## Verification

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

- Diff whitespace check: clean.
- Claude plugin validation: manifest, plugin directory, and marketplace passed.

## Review Notes

1. Usability: the playbook starts with command choice rather than architecture
   history.
2. Safety: every host/human/release/SVG/source-patch boundary remains explicit.
3. Scope: the document does not imply automatic journal acceptance, top-tier
   design certification, hidden patching, or automatic SVG polish.

No known Issue 89D blocker remains.
