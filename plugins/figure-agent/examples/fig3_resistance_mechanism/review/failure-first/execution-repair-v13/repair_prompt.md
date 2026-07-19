# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v13/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/comparable-v2/verified_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: local_reposition
- Machine finding: {"a": {"bbox_pdf": [188.723, 19.715401, 208.213107, 27.095723], "text": "sulfur"}, "b": {"bbox_pdf": [193.9, 24.668559, 209.201205, 29.976651], "text": "g(E)"}, "id": "TC001", "iou": 0.182533, "source_mapping": null, "texts": ["sulfur", "g(E)"]}
- Change content only between the exact anchor lines [% Panel B: composition-dependent trap-energy distribution.] and [\begin{scope}[shift={(6.58,0.86)}]].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [I(t)\propto t^{-n}].
- Preserve the exact token [$n$: distribution breadth].
- Preserve the exact token [$\rho_{60\mathrm{s}}$: magnitude].
- Preserve the exact token [S60].
- Preserve the exact token [S80].

## Bound editable source bytes
```tex
\node[panel title] at (6.37,4.42) {(b) Trap-energy landscape};
\node[label, anchor=west] at (6.40,4.03) {sulfur content increases};
\draw[draw=cAmber, line width=0.55pt, -{Stealth}] (8.18,4.03)--(11.36,4.03);
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
