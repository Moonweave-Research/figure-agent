# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v40/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v38/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "retry y-axis ownership from the clean v38 source with enough offset to avoid the new g(E)-axis path collision", "id": "HF022", "subject": "panel_b_ge_axis_clearance_retry"}
- Change content only between the exact anchor lines [    {trap energy, $E$};] and [  % S60 is represented as one narrow, discrete state.].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [$g(E)$].
- Preserve the exact token [(0,2.77)].
- Preserve the exact token [trap energy, $E$].

## Bound editable source bytes
```tex
  \draw[axis] (0,0)--(0,2.77) node[compact label, above right=0pt]
    {$g(E)$};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
