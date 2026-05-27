# Journal Art-Direction Playbook Dogfood

Status: completed in branch `codex/journal-art-direction-playbook`

Related issue:
`../superpowers/issues/2026-05-27-issue-56-journal-art-direction-playbook.md`

## Scope

This dogfood pass verifies the Issue 56A-D contract without mutating real
figure source, export, accepted, golden, or publication artifacts. Evidence uses
synthetic opted-in fixtures from the test suite so the playbook contract can be
exercised deterministically.

## Evidence

Command:

```bash
uv run pytest -q \
  tests/test_critique_brief.py::test_critique_brief_includes_journal_art_direction_playbook \
  tests/test_critique_lint.py::test_lint_critique_rejects_missing_journal_playbook_anchors \
  tests/test_quality_manifest.py::test_critique_manifest_includes_declared_journal_art_direction_playbook \
  tests/test_fig_loop.py::test_loop_surfaces_v1_12_journal_art_direction_playbook_summary
```

Result:

```text
4 passed in 0.24s
```

## Findings

1. Brief forcing works.
   The opted-in synthetic fixture emits `## Journal Art-Direction Playbook`,
   schema `figure-agent.critique.v1.12`, rubric
   `figure-agent.critique-rubric.v1.12`, exact playbook anchors, and
   `journal_art_direction_playbook_audit`.

2. Generic art-direction prose is rejected.
   A critique that falls back to generic polished-figure prose instead of
   citing exact playbook anchors is rejected by `critique_lint.py` under
   `journal_art_direction_playbook_accounting`.

3. Playbook edits participate in freshness.
   The declared playbook path is part of the critique manifest path set, and an
   edit to the pack changes the manifest hash. This means old critiques cannot
   remain fresh after the journal art-direction contract changes.

4. Loop surfacing is read-only.
   `/fig_loop` surfaces `journal_art_direction_playbook_summary` for v1.12
   critiques in `iteration_001.json` and the `--json` summary. A playbook
   summary does not create a new stop boundary or mutate source/export/golden
   state.

## Closeout

Issue 56E does not add a drawing path, SVG mutation path, score gate, or release
gate. It closes the playbook slice as a contract and evidence layer. Further
real-fixture adoption should be a separate fixture-specific issue because it
will intentionally change `spec.yaml` opt-ins and future critique freshness.

No known Issue 56 blocker remains.
