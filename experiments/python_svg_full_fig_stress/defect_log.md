# Python SVG Full-Figure Stress Defect Log

Source render inspected: `full_figure.png`

## Fixed During Stress Test

| id | region | severity | observation | action |
| --- | --- | --- | --- | --- |
| D001 | TL | MAJOR | `S8` and `S60` labels collided near the composition swatch. | Moved `S8` upward and `S60` farther left. |
| D002 | BL | MAJOR | `tau_d` math label was visually too large for its flow box. | Added per-box math width tuning. |
| D003 | BL | MINOR | Bottom `g(E_t)` axis label was oversized in the mini DOS plot. | Reduced dvisvgm width. |
| D004 | BR | MINOR | Cantilever label was too close to the clamp/beam. | Moved label left of the clamp. |
| D005 | CENTER | MINOR | `E_t` annotation sat too close to the lobe and deep label. | Moved and slightly reduced label. |

## Remaining Defects / Risks

| id | region | severity | observation |
| --- | --- | --- | --- |
| R001 | TL | MAJOR | Chemistry is illustrative, not chemically robust. It communicates S8 and a sulfur chain but is not a scalable molecule-rendering solution. |
| R002 | CENTER | MINOR | Math labels are crisp but placement remains hand-tuned; no collision-aware solver exists. |
| R003 | TR | MINOR | Log axes are schematic and manually ticked; not a reusable plot grammar yet. |
| R004 | BL | MINOR | Multiple dvisvgm snippets make the source SVG large and require deterministic cleanup. |
| R005 | FULL | MAJOR | The figure is complex and readable, but still below final Nature Communications polish without a human visual refinement pass. |
