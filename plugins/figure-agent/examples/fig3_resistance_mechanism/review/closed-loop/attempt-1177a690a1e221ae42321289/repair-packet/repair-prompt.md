# Attempt-local bounded repair: fig3_resistance_mechanism

Return one JSON object with replacement_utf8 and change_summary only.
Do not use filesystem, shell, compile, render, host, or review tools.
Do not modify any source; this is a packet-only planning boundary.
Repair family: panel_rebalance
Selected initial finding: C001
Editable selector: panel-c-composition-sample-fields
Anchor start: % S60 and S80 are separate comparison units, sharing the same energy orientation.
Anchor end: \end{scope}
\end{tikzpicture}
Protected invariants:
- preserve all state-mark coordinates unless explicitly declared
- do not create a density-of-states curve or symmetric envelope
- do not alter Panels A or B
Semantic object references:
- panel_c.s60_sample
- panel_c.s80_sample
- panel_c.s60_discrete_states
- panel_c.s80_continuous_support
Semantic relation references:
- each_state_field_remains_grouped_with_its_composition_sample
- both_samples_share_one_energy_orientation
- s80_support_remains_qualitative_non_dos
- panels_a_and_b_remain_unchanged

```tex
\begin{scope}
  \node[label, text=cBlue!60!black] at (10.85,3.55) {S60\\discrete states};
  % fig-agent:start object=s60_discrete_states panel=C kind=energy_landscape truth_bearing=true
  \foreach \y/\len in {2.77/0.46,2.38/0.67,1.97/0.39,1.62/0.74}{
    \draw[cBlue!65!black, line width=0.85pt, line cap=round] (10.85-\len/2,\y) -- (10.85+\len/2,\y);
  }
  % fig-agent:end object=s60_discrete_states
\end{scope}
\begin{scope}
  \node[label, text=cRed!65!black] at (13.25,3.55) {S80\\continuous support};
  % fig-agent:start object=s80_continuous_support panel=C kind=energy_landscape truth_bearing=true
  % Dense, irregular state marks indicate continuous qualitative support;
  % they do not encode a fitted density-of-states envelope or numeric count.
  \foreach \y/\x/\len in {
    1.43/12.58/0.27,1.55/13.62/0.41,1.67/13.04/0.31,1.79/13.93/0.24,
    1.91/12.77/0.43,2.03/13.41/0.26,2.15/12.48/0.33,2.27/13.78/0.38,
    2.39/13.14/0.24,2.51/12.69/0.40,2.63/13.56/0.29,2.75/12.92/0.35,
    2.87/13.89/0.25,2.99/13.28/0.44,3.11/12.60/0.28,3.23/13.70/0.34}{
    \draw[cRed!62!black, opacity=0.82, line width=0.46pt, line cap=round]
      (\x-\len/2,\y) -- (\x+\len/2,\y);
  }
  % fig-agent:end object=s80_continuous_support
  \draw[cRed!60!black, line width=0.35pt] (14.54,1.46) -- (14.54,3.07);
  \draw[cRed!60!black, line width=0.35pt] (14.40,1.46) -- (14.68,1.46);
  \draw[cRed!60!black, line width=0.35pt] (14.40,3.07) -- (14.68,3.07);
  \node[label, text=cRed!60!black, anchor=west] at (14.73,2.27) {broader\\energy support};
```

publication_acceptance: not_claimed
