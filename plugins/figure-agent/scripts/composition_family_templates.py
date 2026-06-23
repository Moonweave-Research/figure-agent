from __future__ import annotations

from typing import Final

FAMILY_DATA: Final = (
    (
        "carrier_walk_morphology",
        "carrier_walk",
        "smooth_trap_walk",
        ("path_mechanicalness", "arrow_clutter"),
        ("carrier_sign_agnostic", "repeated_trapping"),
        ("trap_contact_ambiguity",),
        ("path_mechanicalness", "segmented_walk_count"),
        "replace segmented walk with smoother repeated-trapping path",
        (
            r"\draw[walk] (0.45,3.70) .. controls (0.9,3.25) and (1.55,3.05) "
            r".. (2.45,2.75);",
            r"\draw[walk, -] (2.45,2.75) .. controls (1.25,2.45) and "
            r"(2.35,2.15) .. (1.65,1.85);",
            r"\node[trapx] at (1.65,1.85) {$\times$};",
        ),
    ),
    (
        "carrier_walk_morphology",
        "carrier_walk",
        "direction_cues_only",
        ("path_mechanicalness", "arrow_clutter"),
        ("carrier_sign_agnostic", "repeated_trapping"),
        ("directionality_understated",),
        ("arrow_clutter", "arrowhead_count"),
        "keep only sparse direction cues on the carrier path",
        (
            r"\draw[walk, -] (0.45,3.70) .. controls (1.1,3.15) and "
            r"(2.45,3.25) .. (2.65,2.55);",
            r"\draw[walk] (2.65,2.55) .. controls (1.35,2.15) and "
            r"(2.25,1.75) .. (1.55,1.35);",
            r"\draw[cRed!60!black, line width=0.7pt] (1.55,1.35) circle (1.55mm);",
        ),
    ),
    (
        "sparkline_anchor",
        "current_sparkline",
        "cell_readout_leader",
        ("orphan_plot", "floating_annotation"),
        ("current_decay_power_law",),
        ("cell_plot_collision",),
        ("orphan_plot", "unanchored_plot_count"),
        "anchor current sparkline to cell readout with a leader",
        (
            r"\begin{scope}[shift={(3.35,2.15)}]",
            r"  \draw[cGray!45!black, line width=0.35pt] (-0.35,0.45) -- (0.05,0.45);",
            r"  \draw[-{Stealth[length=0.9mm]}, line width=0.4pt] (0,0) -- "
            r"(1.9,0) node[right]{$t$};",
            r"  \draw[-{Stealth[length=0.9mm]}, line width=0.4pt] (0,0) -- "
            r"(0,1.85) node[above]{$I$};",
            r"  \draw[cBlue!65!black, line width=0.85pt] plot[smooth, "
            r"domain=0.16:1.85, samples=36] (\x, {0.25 + 1.45/(1+3.2*\x)});",
            r"\end{scope}",
        ),
    ),
    (
        "sparkline_anchor",
        "current_sparkline",
        "inline_decay_label",
        ("orphan_plot", "floating_annotation"),
        ("current_decay_power_law",),
        ("label_density",),
        ("floating_annotation", "unanchored_annotation_count"),
        "move decay label into the sparkline readout",
        (
            r"\begin{scope}[shift={(3.40,2.00)}]",
            r"  \draw[-{Stealth[length=0.9mm]}, line width=0.4pt] (0,0) -- "
            r"(1.8,0) node[right]{$t$};",
            r"  \draw[-{Stealth[length=0.9mm]}, line width=0.4pt] (0,0) -- "
            r"(0,1.65) node[above]{$I$};",
            r"  \draw[cBlue!65!black, line width=0.9pt] plot[smooth, "
            r"domain=0.16:1.75, samples=36] (\x, {0.20 + 1.35/(1+3.1*\x)});",
            r"  \node[anchor=west, cBlue!60!black] at (0.65,1.15) {$I\propto t^{-n}$};",
            r"\end{scope}",
        ),
    ),
    (
        "arrow_clutter_reduction",
        "n_breadth",
        "under_axis_breadth_bracket",
        ("arrow_clutter", "measurement_arrow_crosses_data"),
        ("distribution_breadth_not_density",),
        ("breadth_association_weakened",),
        ("arrow_clutter", "arrow_like_object_count"),
        "move breadth marker below the axis as a non-crossing bracket",
        (
            r"\draw[line width=0.35pt, cRed!60!black] (1.2,-0.25) -- (3.8,-0.25);",
            r"\draw[line width=0.35pt, cRed!60!black] (1.2,-0.14) -- (1.2,-0.36);",
            r"\draw[line width=0.35pt, cRed!60!black] (3.8,-0.14) -- (3.8,-0.36);",
            r"\node[lbl, cRed!60!black] at (2.5,-0.55) {$n$ = breadth};",
        ),
    ),
    (
        "arrow_clutter_reduction",
        "n_breadth",
        "bracket_label_span",
        ("arrow_clutter", "measurement_arrow_crosses_data"),
        ("distribution_breadth_not_density",),
        ("label_length",),
        ("arrow_clutter", "arrow_like_object_count"),
        "replace crossing arrow with bracketed breadth label",
        (
            r"\draw[line width=0.35pt, cRed!60!black] (1.15,1.05) -- (1.15,0.92) "
            r"-- (3.85,0.92) -- (3.85,1.05);",
            r"\node[lbl, cRed!60!black] at (2.5,0.58) {$n$ tracks distribution breadth};",
        ),
    ),
)
