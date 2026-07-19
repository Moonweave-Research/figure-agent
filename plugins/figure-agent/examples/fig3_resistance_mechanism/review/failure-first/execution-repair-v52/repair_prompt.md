# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v52/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v51/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "single discrete state extends left into the y-axis lane; stack it on two centered lines above the S60 peak", "id": "HF034", "subject": "panel_b_single_state_axis_clearance"}
- Change content only between the exact anchor lines [  \node[label, text=cBlue, font=\sffamily\bfseries\footnotesize] at (0.965,2.06) {S60};] and [  % S80 is a broad continuous distribution; width, not depth, carries n.].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [single discrete state].
- Preserve the exact token [S60].

## Bound editable source bytes
```tex
  \node[compact label] at (0.965,1.68) {single discrete state};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
