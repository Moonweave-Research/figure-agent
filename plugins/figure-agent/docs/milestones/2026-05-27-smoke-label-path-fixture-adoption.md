# Smoke Trap Demo Label-Path Fixture Adoption

**Date:** 2026-05-27  
**Scope:** Issue 54  
**Status:** completed

## Target

Adopt `spec.yaml.label_path_proximity_checks` for `smoke_trap_demo` without
creating false-positive compile noise.

## Contract Added

The fixture now declares three narrow horizontal-line checks:

| id | role | PDF-cm y | PDF-cm x-range | clearance |
| --- | --- | ---: | --- | ---: |
| `smoke_cb_reference_line` | `reference_line` | 2.30 | `[1.72, 7.02]` | 3.0 pt |
| `smoke_deep_trap_line` | `semantic_line` | 4.62 | `[2.99, 5.94]` | 3.0 pt |
| `smoke_vb_reference_line` | `reference_line` | 6.87 | `[1.72, 7.02]` | 3.0 pt |

The ranges cover the semantic line bodies and deliberately exclude the
right-edge endpoint labels (`CB`, `E_t`, `VB`), which are intentional
band-diagram labels.

## TDD Evidence

Red test:

```bash
uv run pytest -q tests/test_label_path_proximity.py::test_smoke_trap_demo_declares_band_diagram_label_path_checks
```

Result before the spec change:

```text
FAILED ... assert set() == {'smoke_cb_reference_line', ...}
```

Green test after the spec change:

```text
1 passed
```

The test file also locks the current endpoint-label geometry as a zero-candidate
case so future coordinate edits do not turn the intended `CB`, `E_t`, and `VB`
labels into silent false positives.

## Compile Evidence

Command:

```bash
bash scripts/compile.sh examples/smoke_trap_demo/smoke_trap_demo.tex
```

Relevant result:

```text
OK: no label-path proximity candidates found in smoke_trap_demo.pdf (12 words)
```

`build/label_path_proximity.json` was emitted with:

```text
schema=figure-agent.label-path-proximity.v1
fixture=smoke_trap_demo
total=0
source=spec.yaml:label_path_proximity_checks
```

## Critical Review

1. Contract correctness: the checks use the same PDF-cm top-left convention as
   the existing detector and do not require a schema change.
2. False-positive containment: endpoint labels stay outside the monitored
   x-ranges, so the normal band-diagram idiom remains clean.
3. Workflow fit: this fixture is critique-not-required, so the adoption must
   keep compile evidence clean rather than requiring host-vision accounting.

No generated build artifacts are intended for commit.
