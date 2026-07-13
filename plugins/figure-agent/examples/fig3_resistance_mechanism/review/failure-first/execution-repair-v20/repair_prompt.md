# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v20/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v19/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: local_reposition
- Machine finding: {"a": {"bbox_pdf": [75.306136, 45.463384, 85.377176, 51.459901], "text": "film"}, "b": {"bbox_pdf": [61.393, 46.423384, 84.796252, 52.419901], "text": "retained"}, "id": "TC001", "iou": 0.312538, "source_mapping": null, "texts": ["film", "retained"]}
- Change content only between the exact anchor lines [  at (3.515,2.44) {electrode};] and [\draw[draw=cGray, line width=0.45pt]].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [disordered].
- Preserve the exact token [sulfur--polymer film].
- Preserve the exact token [electrode].
- Preserve the exact token [retained].

## Bound editable source bytes
```tex
\node[compact label, align=center, anchor=north] at (1.92,3.61)
  {disordered\\sulfur--polymer film};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
