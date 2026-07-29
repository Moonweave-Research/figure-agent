# Bound repair execution: fig1_failure_first_panel_f_pilot

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig1_failure_first_panel_f_pilot/review/failure-first/execution-repair-v4/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v3/verified_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: relation_restore
- Machine finding: {"finding": "Panel F visually draws the Coulomb-force arrow but omits the declared panelFCoulombRepulsionArrow style, and the bottom sample/source labels collide. Add the assertion style to the existing force draw and reposition only the bottom circuit labels while preserving the floating sample, driven electrode, source return ground, force direction, and all panel geometry.", "id": "HF002", "subject": "panel_f_relation_address_and_bottom_label_collision"}
- Change content only between the exact anchor lines [% F: floating cantilever and source-ground circuit] and [\end{tikzpicture}].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [floating cantilever].
- Preserve the exact token [driven electrode].
- Preserve the exact token [sample has no electrical contact].
- Preserve the exact token [source return].
- Preserve the exact token [air gap].

## Bound editable source bytes
```tex
\begin{scope}[shift={(12.10,0)}]
  \node[paneltitle, anchor=north west] at (0.18,5.62) {F};
  \node[label, anchor=north] at (2.90,5.56) {Trapped-charge Coulomb repulsion};

  % Restrained mechanical support, with no electrical connection
  \path[draw=cGray, fill=cLGray!45, line width=0.58pt]
    (0.44,3.23) rectangle (1.18,4.45);
  \foreach \y in {3.38,3.68,3.98,4.28}{
    \draw[cGray, line width=0.30pt] (0.49,\y) -- (0.77,\y+0.14);
  }
  \node[smalllabel, align=center, anchor=north] at (0.81,3.10) {mechanical\\support};

  % Electrically floating cantilever held only by the support
  \path[draw=cBrown, fill=cAmberSphere!32, line width=0.72pt, rounded corners=1pt]
    (1.18,3.72) -- (4.86,4.19) -- (4.91,3.91) -- (1.18,3.46) -- cycle;
  \node[smalllabel, text=cBrown, anchor=south] at (3.15,4.14) {floating cantilever};
  \foreach \x/\y in {2.22/3.72,2.83/3.80,3.44/3.88,4.05/3.96,4.58/4.03}{
    \node[charge] at (\x,\y) {$-$};
  }

  % Driven electrode and visible air gap
  \path[draw=cGray, fill=cBlue!20, line width=0.66pt]
    (1.65,2.12) rectangle (5.00,2.43);
  \node[smalllabel, text=cBlue, anchor=north] at (3.33,2.04) {driven electrode};
  \draw[cGray, {Stealth[length=2.4pt,width=1.8pt]}-{Stealth[length=2.4pt,width=1.8pt]},
    line width=0.36pt] (4.70,2.52) -- (4.70,3.70);
  \node[note, anchor=east] at (4.50,3.04) {air gap};

  % Coulomb force points away from the electrode
  \draw[cRed, -{Stealth[length=4.0pt,width=3.0pt]}, line width=1.0pt]
    (3.60,3.56) -- (3.60,4.88);
  \node[label, text=cRed, anchor=west] at (3.72,4.72) {$F_{\mathrm C}$};

  % Compact source circuit: source drives electrode, return terminates at ground
  \draw[cGray, line width=0.58pt] (3.34,2.12) -- (3.34,1.44) -- (2.55,1.44);
  \draw[cGray, line width=0.58pt] (1.75,1.44) -- (1.25,1.44) -- (1.25,0.72);
  \draw[cGray, fill=white, line width=0.58pt] (2.15,1.44) circle[radius=0.40];
  \node[label, text=cRed] at (2.15,1.58) {$+$};
  \node[label, text=cBlue] at (2.15,1.29) {$-$};
  \node[smalllabel, anchor=north] at (2.15,0.96) {voltage source};
  \draw[cGray, line width=0.58pt] (0.88,0.72) -- (1.62,0.72);
  \draw[cGray, line width=0.48pt] (0.98,0.57) -- (1.52,0.57);
  \draw[cGray, line width=0.38pt] (1.08,0.43) -- (1.42,0.43);
  \node[smalllabel, anchor=west] at (1.66,0.60) {source return};
  \node[note, anchor=east] at (5.15,0.80) {sample has no electrical contact};
\end{scope}
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
