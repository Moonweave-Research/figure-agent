# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v51/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v50/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "g(E) floats above-left of the ordinate and should be centered directly over the y-axis arrow without touching it", "id": "HF033", "subject": "panel_b_ge_axis_ownership"}
- Change content only between the exact anchor lines [  \draw[axis] (0,0)--(0,2.77);] and [  % S60 is represented as one narrow, discrete state.].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [$g(E)$].
- Preserve the exact token [(0,2.77)].

## Bound editable source bytes
```tex
  \node[compact label, anchor=south east] at (-0.05,2.82) {$g(E)$};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
