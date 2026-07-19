# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v38/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v37/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "I(t) and t are attached to arrow endpoints instead of reading as owned y- and x-axis labels", "id": "HF020", "subject": "panel_a_inset_axis_label_ownership"}
- Change content only between the exact anchor lines [\begin{scope}[shift={(4.05,1.40)}]] and [  \draw[draw=cTeal, line width=1.00pt]].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [$I(t)$].
- Preserve the exact token [$t$].
- Preserve the exact token [(0,1.65)].

## Bound editable source bytes
```tex
  \draw[axis] (0,0)--(1.62,0) node[compact label, below left=0pt] {$t$};
  \draw[axis] (0,0)--(0,1.65) node[compact label, above right=0pt] {$I(t)$};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
