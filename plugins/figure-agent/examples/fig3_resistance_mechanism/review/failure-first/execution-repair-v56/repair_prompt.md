# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v56/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v53/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "the bottom discrete-to-continuous sentence duplicates the title arrow and distribution labels while occupying the only safe external dimension lane", "id": "HF038", "subject": "remove_redundant_panel_b_bottom_summary"}
- Change content only between the exact anchor lines [  \node[compact label, text=cBrown, rotate=90] at (4.58,0.765) {magnitude};] and [\end{tikzpicture}].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [magnitude].

## Bound editable source bytes
```tex
\end{scope}

\node[label, align=center] at (8.94,0.18)
  {discrete S60 $\longrightarrow$ continuous broad S80};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
