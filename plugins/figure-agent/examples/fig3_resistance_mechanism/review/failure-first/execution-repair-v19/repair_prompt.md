# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v19/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v18/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"bbox_px": [124, 317, 379, 367], "id": "VC014", "kind": "text_on_path", "metric": {"dark": 0.167, "edge": 0.006}, "tex_lines": null, "text": "disordered"}
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
\node[compact label, anchor=north] at (1.92,3.61)
  {disordered sulfur--polymer film};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
