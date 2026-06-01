# Issue 100R - Diagnostic Artifact Provenance Rule

Status: completed on main in commit `49cb61d`; merged by `14c5b64`

Type: evidence provenance, operator safety, long-session friction

## Problem

Long figure-polish sessions often create ad hoc screenshots, temporary crops,
or scratch diagnostics while chasing a local visual issue. Those files can stay
on disk after the figure has been recompiled. If a later host or human treats
one of those old images as current evidence, the loop can chase a defect that
exists only in the stale diagnostic artifact.

The plugin already has a strong authoritative crop path:

- current build render: `examples/<name>/build/<name>.png|pdf`;
- manifest-bound audit crops listed in
  `examples/<name>/build/audit_crops/manifest.json`;
- hash validation for required crop ids in audit evidence and critique lint.

The missing contract was the negative rule: scratch/debug crops outside that
manifest are not plugin truth.

## Implemented Behavior

Added `scripts/diagnostic_artifact_provenance.py`.

The script classifies user-supplied image/artifact paths for a fixture:

```bash
uv run python3 scripts/diagnostic_artifact_provenance.py <name> <path>...
```

It emits:

```yaml
schema: figure-agent.diagnostic-artifact-provenance.v1
fixture: <name>
rule: "Only current build renders and manifest-bound build/audit_crops entries are authoritative plugin truth..."
authoritative_count: <int>
diagnostic_count: <int>
artifacts:
  - path: <repo-relative-or-absolute>
    example_relative_path: <relative-to-example>
    classification: manifest_bound_current | build_render_current | diagnostic_only | stale_or_unbound | stale_or_mismatched | missing
    authoritative: true | false
    reason: <why>
```

Authoritative classifications are limited to:

- `build_render_current`: the fixture's official build PNG/PDF;
- `manifest_bound_current`: a crop listed in
  `build/audit_crops/manifest.json` whose current file hash matches the
  manifest.

`build_render_current` means the path is the fixture's official build artifact.
It does not replace `/fig_status` or `critique_brief.py` render-freshness
checks against source files.

Non-authoritative classifications:

- `diagnostic_only`: an existing artifact that is not manifest-bound;
- `stale_or_unbound`: a diagnostic artifact older than the current build
  render;
- `stale_or_mismatched`: a manifest-listed artifact whose current file hash no
  longer matches the manifest;
- `missing`: the supplied path does not exist.

`commands/fig_critique.md` now tells host operators not to use manual crops or
scratch screenshots as current evidence unless this checker classifies them as
authoritative.

## Non-Goals

- Do not scan arbitrary filesystem locations.
- Do not auto-delete scratch artifacts.
- Do not add a new release/acceptance gate.
- Do not mutate build, export, accepted, golden, SVG, source, or critique
  state.
- Do not make diagnostic-only artifacts unusable as context; they are just not
  allowed to override current manifest-bound evidence.

## Tests

Added `tests/test_diagnostic_artifact_provenance.py` covering:

- matching manifest crop is authoritative;
- manifest crop hash mismatch is non-authoritative;
- scratch crop older than current render is stale/unbound;
- unmanifested current crop is diagnostic-only;
- report summary counts authoritative vs diagnostic artifacts.

## Design Review

### Review 1 - Contract Correctness

The rule follows the existing audit-crop manifest contract instead of creating
a second source of truth. `build/audit_crops/manifest.json` remains the only
authoritative crop inventory, and current build PNG/PDF remain the only
authoritative full-render artifacts.

### Review 2 - Scope Containment

The checker is read-only and path-explicit. It does not walk `.scratch/`, does
not rewrite manifests, and does not infer truth from filenames. This avoids
both surprise filesystem scanning and accidental cleanup of user diagnostics.

### Review 3 - Operational Readiness

The command is intended for the common failure mode: a user, host LLM, or agent
mentions a crop/screenshot that is not in the brief. The operator can classify
that file before using it as evidence. If it is `diagnostic_only` or
`stale_or_unbound`, rerun `/fig_compile` and rely on
`build/audit_crops/manifest.json` evidence instead.

### Review 4 - Freshness Boundary Fix

Initial implementation wording implied that `build_render_current` alone proved
render freshness. The classifier only proves that a path is the official build
render artifact; source freshness remains owned by `/fig_status` and
`critique_brief.py`. The reason string, report rule, docs, and tests were
updated to make that boundary explicit.
