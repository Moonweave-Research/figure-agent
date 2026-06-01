# Issue 100K - Optional Second-Opinion Route

Status: completed

Type: external review evidence, operator UX, non-mutating route

## Problem

Issue 61 made `external_vision_review.yaml` a controlled evidence input, but
operators still had to author the file manually. That made the route feel ad hoc
when the loop suggested a second opinion for subjective or repeated visual
defects.

## Decision

Keep external review provider-agnostic and local. Do not call Gemini, Claude,
OpenAI, web search, or any other external API from the plugin.

Add a starter-template command to the existing local validator:

```bash
uv run python3 scripts/external_vision_review.py --template examples/<name> --write-template
```

The generated file binds the review to the current rendered artifact and, when
available, the current `build/audit_crops/manifest.json` crop set. The external
reviewer or outer agent then fills findings and conflicts manually.

## Implemented Contract

- `external_vision_review_template(example_dir)` emits reloadable
  `figure-agent.external-vision-review.v1` YAML.
- The template hashes `build/<name>.png` and every crop listed in
  `build/audit_crops/manifest.json`.
- Missing build PNG is a controlled error that tells the operator to compile
  first.
- Malformed or missing crop-manifest crop entries fail closed instead of
  producing stale evidence.
- `--write-template` writes `examples/<name>/external_vision_review.yaml` and
  refuses overwrite unless `--force` is passed.
- Existing validation, freshness, critique-lint, quality-manifest, and
  `/fig_loop` conflict behavior remain unchanged.

## Safety Rules

- No provider API or network dependency.
- No source, critique, adjudication, export, accepted, golden, publication, or
  SVG mutation.
- The external evidence remains optional and opt-in through
  `spec.yaml.external_vision_review: true`.
- External conflicts route to human review; they do not become automatic truth.

## Tests

Covered in `tests/test_external_vision_review.py`:

- template uses current render hash and manifest crop hashes;
- emitted YAML reloads through the existing validator and is fresh;
- CLI prints reloadable YAML;
- CLI can write the canonical file;
- CLI refuses overwrite without `--force`.
