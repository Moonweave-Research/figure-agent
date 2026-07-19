# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v36/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v35/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "the three-line filled external key is structurally safe but visually too heavy relative to the Panel A sample", "id": "HF018", "subject": "panel_a_external_key_proportion"}
- Change content only between the exact anchor lines [\node[carrier, fill=cBlue!18] at (3.02,3.02) {};] and [% Qualitative inset only: no ticks, values, or sampled data markers.].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [capture $\leftrightarrow$ release repeats].
- Preserve the exact token [filled endpoint: retained].
- Preserve the exact token [(3.02,3.02)].

## Bound editable source bytes
```tex
\node[compact label, align=center, anchor=north, fill=cAmberSphere!22,
      inner xsep=1.5pt, inner ysep=2pt] at (1.92,1.03)
  {sign-agnostic carrier path\\capture $\leftrightarrow$ release repeats\\filled endpoint: retained};
% Transition and endpoint semantics share one external key.
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
