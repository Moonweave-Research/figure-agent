# SVG Polish Audit Handoff Protocol

**Date:** 2026-05-19
**Issue:** `docs/superpowers/issues/2026-05-19-issue-7c-svg-polish-audit-handoff.md`
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## Purpose

This protocol lets a human or outer agent polish one generated SVG as the
declared final artifact without turning SVG editing into the semantic source of
truth.

The contract is intentionally conservative:

- TikZ, briefing, spec, references, critique, and adjudication remain the
  semantic source and loop evidence.
- `exports/<name>.svg` remains generated output and must not be hand-edited.
- `polish/<name>.polished.svg` is allowed only as a presentation artifact with
  manifest hashes, audit prose, provenance, and a reviewer decision.
- `/fig_status` is the current validation surface for the final-artifact state.

## Preconditions

Start SVG polish only when all of the following are true:

- The fixture has a current generated SVG at `examples/<name>/exports/<name>.svg`.
- The remaining work is optical presentation cleanup, not scientific or
  structural correction.
- Any blocking critique/adjudication loop for semantic defects has been closed
  before final promotion. Non-blocking unresolved findings may remain visible,
  but SVG polish must not relabel them as resolved.
- The polisher has the current generated SVG hash and knows the target path:
  `examples/<name>/polish/<name>.polished.svg`.

If source, briefing, spec, reference, or critique content changes before polish,
rerun compile/export and refresh critique when freshness requires it before
creating or updating the polished SVG manifest. Add the final-artifact opt-in
and write the audit before hashing the manifest; both files are part of the
freshness contract.

## Allowed Writes

The SVG polish handoff may write only:

- `examples/<name>/polish/<name>.polished.svg`
- `examples/<name>/polish/svg_polish_manifest.yaml`
- `examples/<name>/polish/svg_polish_audit.md`
- `examples/<name>/spec.yaml`, only to add or confirm:

```yaml
final_artifact:
  kind: polished_svg
  manifest: polish/svg_polish_manifest.yaml
```

The opt-in must be added only when the polished SVG is intended to become the
declared final artifact. A draft polish file without this opt-in is not
release-relevant.

## Forbidden Writes

The SVG polish handoff must not write:

- `examples/<name>/exports/`
- `examples/<name>/build/`
- `examples/<name>/critique.md`
- `accepted` or `golden_contract` state in `spec.yaml`
- unrelated fixtures
- generated preview/export artifacts
- broad source refactors
- multiple fixture polish targets in one handoff

SVG polish must not hide unresolved critique findings or mutate evidence files
to make status appear clean.

## Allowed Visual-Only Edit Classes

Each polished SVG edit must fit one of these bounded classes:

- `label_micro_position`
- `leader_line_micro_position`
- `stroke_polish`
- `icon_detail`
- `spacing_balance`
- `color_opacity_polish`
- `typography_cleanup`
- `export_cleanup`

These classes cover optical cleanup only: label nudges, preserved leader-line
targets, stroke normalization, icon edge cleanup, spacing balance, contrast or
opacity polish that preserves identity, typography cleanup that preserves
wording, and removal of export noise.

## Must-Backport Classes

Set `backport_required: true` and return to the semantic source loop when the
polish would:

- add, remove, rename, or retarget a scientific component
- change material identity or label meaning
- change mechanism arrows, charge/current/force direction, or physics cues
- change panel order, panel role, storyline, scale, or proximity meaning
- add apparatus parts that critique marked as structural defects
- fix a root cause that belongs in TikZ, briefing, or `spec.yaml`
- require a reviewer guess about whether the change is visual-only

A must-backport change can later be polished only after the source loop is
refreshed and the generated SVG is regenerated.

## Manifest Requirements

`polish/svg_polish_manifest.yaml` must use schema
`figure-agent.svg-polish-manifest.v1` and include:

- fixture name
- base source-set hash
- base hashes for source TeX, briefing, spec, generated SVG, export PDF, and
  critique
- polished SVG path and hash
- `svg_polish_audit.md` hash
- editor class
- toolchain entries
- non-empty bounded edit classes
- `semantic_change_declared`
- `backport_required`
- reviewer provenance
- review timestamp

Unknown future mapping fields may be preserved, but they cannot replace the
required fields above.

Create or update the manifest last, after `spec.yaml`, the polished SVG, and
`svg_polish_audit.md` are final for the current handoff. Otherwise `/fig_status`
will correctly report the manifest as stale.

## Audit Closeout Template

`polish/svg_polish_audit.md` should answer:

```markdown
# SVG Polish Audit: <name>

## Base Artifact

- generated_svg: exports/<name>.svg
- generated_svg_hash: sha256:<hash>
- export_pdf_hash: sha256:<hash>
- source_set_hash: sha256:<hash>

## Polished Artifact

- polished_svg: polish/<name>.polished.svg
- polished_svg_hash: sha256:<hash>
- manifest: polish/svg_polish_manifest.yaml

## Edit Classes

- <allowed edit class>: <what changed and why it is visual-only>

## Semantic Preservation

- semantic_change_declared: false
- backport_required: false
- reviewer_decision: <why the polished SVG preserves the TikZ/source meaning>

## Must-Backport Review

- components: pass/fail + note
- labels/material identity: pass/fail + note
- mechanism directions: pass/fail + note
- panel/storyline meaning: pass/fail + note
- scale/proximity meaning: pass/fail + note
- unresolved critique findings: visible/preserved + note

## Provenance

- reviewer: <name or accountable role>
- reviewed_at: <ISO-8601 timestamp>
- editor: human | external_tool | agent_assisted
- toolchain: <tool names and versions, or unknown>

## Closeout

- compile/export refreshed if needed: yes/no/N-A
- critique refreshed if needed: yes/no/N-A
- manifest recreated or validated: yes/no
- /fig_status final artifact state: <state>
```

The audit is not optional. The manifest records its hash, and `/fig_status`
reports the polished artifact as stale when the audit content changes without a
matching manifest refresh.

## Required Commands

After polish, opt-in, audit writing, and manifest refresh, run from the plugin
root:

```bash
uv run python3 scripts/status.py <name>
```

The closeout target is:

```text
Final artifact: polished_svg FRESH polish/<name>.polished.svg
```

If status reports `MISSING`, `INVALID`, `STALE`, or `BLOCKED`, do not promote
the polished SVG. Fix the manifest/audit/hash issue, or return to semantic
backport when status is blocked.

Run compile, export, and critique commands before this status check whenever
their freshness rules require it.

## Review Checklist

- Exactly one fixture and one polished SVG target were touched.
- Generated exports were not hand-edited.
- No accepted/golden state was changed by the polish handoff.
- Every SVG edit is in an allowed visual-only class.
- Any semantic or uncertain edit is marked `backport_required: true`.
- `svg_polish_manifest.yaml` hashes current source, generated export, critique,
  polished SVG, and audit content.
- `svg_polish_audit.md` records semantic preservation, unresolved-finding
  visibility, reviewer, timestamp, and toolchain.
- `/fig_status` reports `Final artifact: polished_svg FRESH ...` before the
  polished SVG is considered release-ready.

No automatic SVG editing, automatic acceptance, or publication-safety promotion
is part of this protocol.
