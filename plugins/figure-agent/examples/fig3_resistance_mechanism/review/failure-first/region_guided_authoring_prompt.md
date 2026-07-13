# Clean-room Fig3 region-guided authoring prompt

Create one standalone editable TikZ/LaTeX source at
`region_guided_generated.tex` using only the files declared authoritative in
`region_guided_authority_packet.yaml`.

Do not inspect or imitate any forbidden source or render. Do not use SVG or
Python as an authoring medium. Import `polymer-paper-preamble` and use its
palette. Keep non-panel text at 5.5--7 pt and avoid `\tiny`/`\scriptsize`.

The result must preserve the two-panel scientific narrative and every binding
semantic rule in the authority packet. In addition, treat these context-pack
directives as hard authoring constraints:

- Keep text group [Applied, bias, trapping, during, conduction] inside region
  [panel_a] with at least 0.005 normalized page inset.
- Keep text group [current, decays] at least 0.01 page-diagonal units clear of
  region [panel_a_plot_with_axes].

Use a clear two-column composition with explicit panel ownership. Do not solve
the rules by deleting required labels, shrinking text below the typography
floor, or moving scientific content into the wrong panel. Do not claim
publication acceptance.
