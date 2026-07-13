# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v21/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v20/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: local_reposition
- Machine finding: {"bbox_px": [132, 834, 451, 884], "id": "VC003", "kind": "text_on_path", "metric": {"dark": 0.09, "edge": 0.004}, "tex_lines": null, "text": "sign-agnostic"}
- Change content only between the exact anchor lines [\node[carrier, fill=cBlue!18] at (3.02,3.02) {};] and [\node[compact label, align=center, fill=white, inner sep=1pt] at (1.70,2.18)].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [sign-agnostic].
- Preserve the exact token [carrier].
- Preserve the exact token [capture].
- Preserve the exact token [release].
- Preserve the exact token [retained].

## Bound editable source bytes
```tex
\node[compact label, align=center, anchor=north] at (1.10,1.42)
  {sign-agnostic\\carrier};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
