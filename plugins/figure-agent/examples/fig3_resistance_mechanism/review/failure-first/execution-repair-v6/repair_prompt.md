# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v6/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v8/treatment_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"id": "LH001", "message": "hyphenated line break 're-': a fixed-width node wrapped a word; widen text width or reword the label", "source_mapping": null, "text": "re-", "xmax": 112.71808, "xmin": 105.412281, "ymax": 103.245292, "ymin": 97.710053}
- Change content only between the exact anchor lines [    at (3.36,1.52) {};] and [  \begin{scope}[shift={(4.78,0.84)}]].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [sign-agnostic carrier: repeated dispersive trapping].
- Preserve the exact token [applied trapping\\during conduction].
- Preserve the exact token [disordered sulfur polymer film].
- Preserve the exact token [$I \propto t^{-n}$].
- Preserve the exact token [S60 $\rightarrow$ S80].
- Preserve the exact token [$n$ = breadth].
- Preserve the exact token [$\rho_{60s}$\\magnitude].

## Bound editable source bytes
```tex
  \node[note, anchor=north, text width=3.40cm] at (2.32,0.82)
    {sign-agnostic carrier: repeated dispersive trapping};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
