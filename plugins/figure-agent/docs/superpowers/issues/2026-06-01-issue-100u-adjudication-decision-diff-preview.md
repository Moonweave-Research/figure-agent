# Issue 100U - Adjudication Decision Diff Preview

Status: completed

Type: adjudication safety, human-decision preservation

## Problem

`critique_adjudication.py sync` preserves existing human decisions when the
current finding IDs and resolved/not-resolved shape still match. `--force`
correctly recreates the scaffold when the shape changed, but it is a sharp tool:
operators do not get a structured preview of which human decisions would be
preserved, dropped, added, or reset before choosing force.

## Scope

Add a read-only decision diff preview for the current `critique.md` and
`critique_adjudication.yaml`.

In scope:

- structured `figure-agent.adjudication-decision-diff.v1` output;
- preserved decision IDs;
- dropped existing decision IDs;
- newly added critique finding IDs;
- same-ID resolved/not-resolved shape changes;
- old/new `source_critique_hash` visibility;
- CLI `sync --preview` that prints the diff and writes nothing.

Out of scope:

- no adjudication mutation in preview mode;
- no policy change to `sync` or `--force`;
- no auto-resolution of human decisions;
- no loop/status/export behavior changes.

## Public Behavior

`critique_adjudication.py sync <fixture> --preview` should:

- require the same fresh critique metadata as normal sync;
- return a controlled error for malformed existing adjudication;
- emit a deterministic YAML preview;
- leave `critique_adjudication.yaml` unchanged.

The preview tells operators whether normal `sync` is safe, and what would be
lost or reset if they choose `--force`.

## Review Notes

- The diff uses the same resolved/not-resolved shape that existing sync already
  enforces, so it explains current behavior instead of inventing a new policy.
- The preview is intentionally advisory and read-only.
- `sync --preview` requires the same fresh critique metadata as normal `sync`
  and leaves `critique_adjudication.yaml` byte-for-byte unchanged.
