# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v47/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v43/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "retain the right-side rho lane but protect its label background from nearby metric geometry", "id": "HF029", "subject": "panel_b_magnitude_value_protected_lane_retry"}
- Change content only between the exact anchor lines [  \draw[draw=cBrown, line width=0.65pt, {Stealth}-{Stealth}] (4.78,0.18)--(4.78,1.35);] and [\node[label, align=center] at (8.94,0.18)].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [$\rho_{60\mathrm{s}}$].
- Preserve the exact token [magnitude].
- Preserve the exact token [(4.78,1.35)].

## Bound editable source bytes
```tex
  \node[compact label, text=cBrown, anchor=south, align=center, fill=white, inner sep=1.0pt] at (4.78,1.42) {$\rho_{60\mathrm{s}}$\\magnitude};
\end{scope}
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
