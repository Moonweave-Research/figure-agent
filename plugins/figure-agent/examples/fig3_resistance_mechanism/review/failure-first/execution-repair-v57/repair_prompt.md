# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v57/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v53/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: relation_restore
- Machine finding: {"finding": "the jagged polyline and four equal carrier glyphs read as multiple simultaneous carriers rather than one time-ordered capture and release trajectory", "id": "HF039", "subject": "panel_a_single_carrier_temporal_path"}
- Change content only between the exact anchor lines [% The walk changes direction repeatedly and has no electrode-polarity assignment.] and [% Qualitative inset only: no ticks, values, or sampled data markers.].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [capture].
- Preserve the exact token [release].
- Preserve the exact token [retained].

## Bound editable source bytes
```tex
\draw[draw=cBlue, line width=0.95pt, rounded corners=2.5pt]
  (1.08,1.62) -- (1.34,2.02) -- (1.07,2.42) -- (1.61,3.03)
  -- (2.02,2.72) -- (2.31,2.59) -- (2.02,2.18) -- (2.68,1.98)
  -- (2.49,1.52) -- (3.02,3.02);

\node[carrier] at (1.08,1.62) {};
\node[carrier] at (1.34,2.02) {};
\node[carrier] at (2.31,2.59) {};
\node[carrier, fill=cBlue!18] at (3.02,3.02) {};
\node[compact label, align=center, anchor=north] at (1.92,1.03)
  {capture $\leftrightarrow$ release repeats\\filled endpoint: retained};
% Transition and endpoint semantics share one external key.
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
