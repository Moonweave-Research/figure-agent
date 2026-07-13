# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v27/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v26/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: panel_rebalance
- Machine finding: {"finding": "two-line descriptor overlaps S60 after axis-clearance repair", "id": "HF011", "subject": "panel_b_single_discrete_state_label"}
- Change content only between the exact anchor lines [  \draw[draw=cBlue!70, line width=0.35pt, dashed] (0.965,0)--(0.965,1.30);] and [  % S80 is a broad continuous distribution; width, not depth, carries n.].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [single].
- Preserve the exact token [discrete].
- Preserve the exact token [state].
- Preserve the exact token [S60].
- Preserve the exact token [S80].
- Preserve the exact token [continuous broad].
- Preserve the exact token [magnitude].

## Bound editable source bytes
```tex
  \node[label, text=cBlue, font=\sffamily\bfseries\footnotesize] at (0.965,1.76) {S60};
  \node[compact label, align=center, anchor=south] at (0.965,1.36)
    {single discrete\\state};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
