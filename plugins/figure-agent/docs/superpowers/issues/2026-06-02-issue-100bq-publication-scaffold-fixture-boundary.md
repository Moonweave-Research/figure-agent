# Issue 100BQ - Publication Scaffold Fixture Identity Boundary

Status: implemented

Type: publication provenance safety, fixture identity hardening

## Problem

`publication_gate.py` owns the conservative `QUALITY_AUDIT.md` scaffold used by
accepted/release-adjacent workflows. Before this issue, scaffold helpers accepted
unsafe fixture identity strings such as `../outside` and embedded them directly
into scaffold text:

```markdown
fixture: ../outside
```

This did not resolve a filesystem path by itself, but it made traversal syntax
look like normal publication provenance for a figure.

## Decision

Validate the fixture name at scaffold-render time using the shared fixture
identity helper. `write_publication_audit_scaffold()` already renders through
`publication_audit_scaffold_text()`, so it inherits the guard and fails before
writing when the fixture identity is unsafe.

The lower-level audit-path argument remains explicit. This slice protects the
identity field stored in the human-facing publication audit, not arbitrary
absolute path writes used by tests or controlled tooling.

## Tests

Covered by:

- `tests/test_publication_gate.py::test_publication_audit_scaffold_rejects_unsafe_fixture_name`
- `tests/test_publication_gate.py::test_write_publication_audit_scaffold_rejects_unsafe_fixture_before_write`
- existing scaffold defaults and overwrite tests

Both new tests were red before implementation: scaffold rendering returned text
for `../outside`, and the writer created a `QUALITY_AUDIT.md` file with the
unsafe fixture string.

## Review Notes

- Valid fixture scaffolds are unchanged.
- Unsafe fixture strings fail before scaffold text can be treated as provenance.
- The change does not alter publication-gate parsing, accepted state, export
  state, golden state, SVG polish, or source figure files.
- No schema bump is needed because `fixture:` was already intended to name a
  single declared fixture.
