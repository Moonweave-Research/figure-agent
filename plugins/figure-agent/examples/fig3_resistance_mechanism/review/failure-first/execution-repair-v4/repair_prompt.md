# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v4/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v6/treatment_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: local_reposition
- Machine finding: {"a": {"bbox_pdf": [236.544, 13.302712, 260.15911, 18.09992], "text": "increasing"}, "b": {"bbox_pdf": [232.292, 12.670397, 272.851721, 19.497193], "text": "trap-energy"}, "id": "TC001", "iou": 0.409135, "source_mapping": null, "texts": ["increasing", "trap-energy"]}
- Change content only between the exact anchor lines [\begin{scope}[shift={(7.82,0.35)}]] and [  \draw[draw=cAmber, line width=0.48pt, -{Stealth[length=3.0pt,width=2.2pt]}]].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [S60 $\rightarrow$ S80].
- Preserve the exact token [$n$ = breadth].
- Preserve the exact token [$\rho_{60s}$\\magnitude].

## Bound editable source bytes
```tex
  \node[small note, anchor=west] at (0.26,3.50) {increasing sulfur content};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
