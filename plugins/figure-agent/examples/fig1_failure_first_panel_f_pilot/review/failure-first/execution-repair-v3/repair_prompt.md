# Bound repair execution: fig1_failure_first_panel_f_pilot

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig1_failure_first_panel_f_pilot/review/failure-first/execution-repair-v3/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v2/verified_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: style_normalization
- Machine finding: {"finding": "Two prose labels use single-backslash control words (distribution and support), causing undefined-control-sequence failures. Repair only the preamble boundary, preserve an explicit word space at both call sites, and do not change panel geometry or scientific semantics.", "id": "HF001", "subject": "undefined_prose_control_sequences"}
- Change content only between the exact anchor lines [\documentclass[tikz,border=4pt]{standalone}] and [\begin{document}].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [\usepackage{tikz}].
- Preserve the exact token [\usepackage{polymer-paper-preamble}].
- Preserve the exact token [derived trap-energy].
- Preserve the exact token [mechanically held].
- Preserve the exact token [electrically floating cantilever].

## Bound editable source bytes
```tex
\usepackage{tikz}
\usepackage{polymer-paper-preamble}
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
