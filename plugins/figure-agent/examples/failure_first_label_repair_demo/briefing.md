# Failure-first label repair demo

This synthetic fixture tests the control system, not drawing quality. The raw
variant contains one deliberate label/leader collision. The verified variant
binds it to `panel_a.label.repulsion` without changing source. The repaired
variant moves only that label and preserves the two declared relation labels.

Machine evidence may report the defect reduction. It must not claim publication
acceptance or general visual-quality improvement.
