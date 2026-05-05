# Capability Matrix

| Capability | Required evidence | Status | Notes |
| --- | --- | --- | --- |
| Linear gradients | `linearGradient` in SVG and visible material shading | Pass | Polymer beam, metal sheen, and energy plane use SVG-native gradients. |
| Radial gradients | `radialGradient` in SVG and visible trap glow | Pass | Trap and charge halos are visible in panels A, B, and D. |
| Filters | `filter` in SVG and visible soft shadow | Pass | Cards, device parts, and color markers use restrained SVG drop shadows. |
| Clip paths | `clipPath` in SVG and clipped plot or texture | Pass | Energy-plane texture and plot overlay are clipped to fixed regions. |
| Masks | `mask` in SVG and masked surface highlight | Pass | Trap-dot texture fades across the energy surface. |
| Patterns | `pattern` in SVG and visible metal/polymer texture | Pass | Brushed metal, polymer grain, trap dots, and line textures are vector patterns. |
| Pseudo-3D | Isometric device or beam with shaded faces | Pass | Device stack uses semantic isometric boxes with shaded top/side faces. |
| Matplotlib nesting | Nested `<svg x=` plot block | Pass | Panel D embeds a matplotlib log-log plot as nested SVG. |
| dvisvgm math | Embedded dvisvgm path content | Pass | Math labels are generated through `pdflatex` + `dvisvgm` and embedded as SVG paths. |
