# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v5/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v7/treatment_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: local_reposition
- Machine finding: {"a": {"bbox_pdf": [45.13, 24.925712, 69.610265, 29.72292], "text": "disordered"}, "b": {"bbox_pdf": [46.089996, 21.437397, 85.812218, 28.264193], "text": "conduction"}, "id": "TC001", "iou": 0.253223, "source_mapping": null, "texts": ["disordered", "conduction"]}
- Change content only between the exact anchor lines [  \node[small note, rotate=90] at (3.94,2.04) {electrode};] and [  \foreach \x/\y/\r in {].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [applied trapping\\during conduction].
- Preserve the exact token [sign-agnostic carrier: repeated dispersive trapping].
- Preserve the exact token [S60 $\rightarrow$ S80].
- Preserve the exact token [$n$ = breadth].
- Preserve the exact token [$\rho_{60s}$\\magnitude].

## Bound editable source bytes
```tex
  \node[small note, text=cBrown] at (2.30,3.18) {disordered sulfur polymer film};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
