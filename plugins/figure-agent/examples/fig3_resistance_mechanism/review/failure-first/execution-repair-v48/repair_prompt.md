# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v48/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v47/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: relation_restore
- Machine finding: {"finding": "the label n: breadth directly equates a fitted CvS exponent with geometric distribution width even though that mapping is model-dependent; show only distribution breadth on the schematic span", "id": "HF030", "subject": "panel_b_n_breadth_semantic_boundary"}
- Change content only between the exact anchor lines [  % Orthogonal metrics: horizontal breadth and detached vertical magnitude.] and [  \draw[draw=cBrown, line width=0.65pt, {Stealth}-{Stealth}] (4.78,0.18)--(4.78,1.35);].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [cTeal].
- Preserve the exact token [(2.23,0.28)].
- Preserve the exact token [(4.50,0.28)].

## Bound editable source bytes
```tex
  \draw[draw=cTeal, line width=0.65pt, -{Stealth}] (2.75,0.28)--(2.23,0.28) (3.98,0.28)--(4.50,0.28);
  \node[compact label, text=cTeal, fill=white, inner sep=1.4pt] at (3.365,0.28)
    {$n$: breadth};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
