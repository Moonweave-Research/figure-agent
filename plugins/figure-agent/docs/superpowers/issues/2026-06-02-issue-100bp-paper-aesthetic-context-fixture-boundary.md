# Issue 100BP - Paper Aesthetic Context Fixture Identity Boundary

Status: implemented

Type: paper-wide aesthetic context safety, fixture identity hardening

## Problem

`paper_aesthetic_context.py` is the starter and validator for optional
paper-wide aesthetic context packs. Those packs bind shared style language to
specific fixture names through `figure_roles[].fixture`.

Before this issue, the CLI accepted:

```bash
scripts/paper_aesthetic_context.py \
  --template paper-demo \
  --fixture ../outside \
  --write-template
```

and wrote a reloadable YAML pack with `fixture: ../outside`. A hand-authored
pack with the same unsafe role fixture also passed the loader. This did not
write outside the examples tree, but it allowed traversal syntax or non-fixture
identity to become a normal paper-wide design contract target.

## Decision

Reuse the shared fixture identity validator for paper-wide role fixtures.

The contract now requires:

- template `--fixture` values to be valid fixture names;
- `figure_roles[].fixture` values in existing packs to be valid fixture names;
- paper IDs to keep their existing safe-id contract;
- pack paths and explicit `--examples-dir` behavior to remain unchanged.

The change is intentionally narrower than a path resolver rewrite. Paper-wide
context packs are stored under `examples/_paper_aesthetic_contexts/<paper>.yaml`,
so the relevant safety boundary is the role fixture identity inside the pack.

## Tests

Covered by:

- `tests/test_paper_aesthetic_context.py::test_paper_aesthetic_context_template_cli_rejects_unsafe_fixture`
- `tests/test_paper_aesthetic_context.py::test_load_paper_aesthetic_context_rejects_unsafe_figure_role_fixture`
- existing template, overwrite, optional-load, and anchor tests

Both new tests were red before implementation: the CLI returned exit code `0`
and wrote a pack for `--fixture ../outside`, while the loader accepted a pack
whose role fixture was `../outside`.

## Review Notes

- The template writer now fails before output path allocation when the requested
  role fixture is unsafe.
- Existing valid fixture names are unchanged.
- Existing paper ID validation is unchanged.
- The change does not auto-edit `spec.yaml`, critique, export, accepted, golden,
  SVG polish, or publication state.
- No schema bump is needed because the previous documented intent already
  treated `figure_roles[].fixture` as fixture identity; this slice enforces that
  contract.
