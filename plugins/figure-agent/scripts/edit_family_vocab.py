"""Controlled vocabulary for experience-record edit families.

A family names the KIND of edit — object class x operation. Location belongs
in ``state.target`` and intent in the rationale; families that encoded either
(``panel_f_qtr_label_lane``) produced one-off names that never reached the
learning prior floor. The 2026-08-28 corpus audit found 45 names across 169
rows with 27 single-use, which is why ranking priors stayed at zero.

Write paths fold legacy aliases to canonical and reject unknown names.
Read paths (memory index) fold aliases but pass unknown historical names
through unchanged — the log is append-only provenance and is never rewritten.
"""

from __future__ import annotations

# Canonical families, grounded in three evidence sources: the accepted-edit
# corpus (docs/experience-log), the figura TikZ defect catalog's
# composition-level repairs, and the SciDiagramEdit measured distribution of
# real author edits (relabel 22.8%, add element 21.4%, rewire 4.2%).
CANONICAL_EDIT_FAMILIES: dict[str, str] = {
    "label_reposition": "move a label or annotation to clear a collision, lane, or crossing",
    "relabel": "change label text content, wording, or notation",
    "label_restyle": "change label size, weight, or color without moving or rewording it",
    "element_add": "add a visual element (apparatus substance, marker, guide)",
    "element_remove": "remove an element that is wrong or unwanted on its own",
    "density_reduce": "remove redundancy or crowding to lower visual density",
    "element_reposition": "move a non-label element or adjust spacing between elements",
    "element_resize": "change an element's size or extent",
    "element_restyle": "change one element's stroke, fill, opacity, or pattern",
    "style_hierarchy": "re-encode relative emphasis between elements (A must read weaker than B)",
    "bounded_coordinate_offset": "capped coordinate nudge produced by the bounded-offset engine",
    "vector_clearance_offset": "offset a vector to restore clearance from a neighbour",
    "path_reroute": "reroute an arrow, lead, or leader line via waypoints, anchors, or bends",
    "connection_rewire": "change what an arrow or connector attaches to (topology)",
    "semantic_correction": "fix physical or semantic meaning (direction, ownership, sign)",
    "panel_layout": "panel skeleton work: separators, frames, margins, panel boxes",
    "subregion_redraw": "bounded redraw of one sub-region when no narrower operator fits",
}

# Historical names folded into the canonical set. Keys must never collide
# with canonical names; values must be canonical.
LEGACY_EDIT_FAMILY_ALIASES: dict[str, str] = {
    # generator / repair-packet layers
    "label_reflow": "label_reposition",
    "local_reposition": "element_reposition",
    "clipping_repair": "element_reposition",
    "contour_contact": "element_reposition",
    "panel_rebalance": "panel_layout",
    "relation_restore": "connection_rewire",
    "salience_adjustment": "style_hierarchy",
    "style_normalization": "element_restyle",
    "hierarchy_rebalance": "style_hierarchy",
    "apparatus_strengthen": "element_add",
    "mechanism_redraw": "subregion_redraw",
    # fig1 Panel-F campaign names (location/intent baked into the family)
    "panel_f_qtr_label_lane": "label_reposition",
    "panel_f_qtr_apparatus_lane": "element_reposition",
    "panel_f_electrode_lead_lane": "path_reroute",
    "panel_f_leader_left_lane": "path_reroute",
    "panel_f_auto_composite_lane": "subregion_redraw",
    "panel_f_force_gap_lane": "element_reposition",
    "panel_f_mechanical_anchor_lane": "element_reposition",
    "panel_f_source_cue_demote": "style_hierarchy",
    "panel_f_current_label_sanitize": "relabel",
    "panel_f_boundary_polish": "panel_layout",
    "panel_f_final_finish": "subregion_redraw",
    "panel_c_hero_finish": "subregion_redraw",
    "panel_f_label_route_finish": "label_reposition",
    "panel_f_density_relief": "density_reduce",
    "panel_f_air_gap_drift_repair": "element_reposition",
    "panel_f_bias_label_cleanup": "relabel",
    "panel_f_source_cue_readability": "label_restyle",
    "panel_f_source_title_settle": "label_reposition",
    "panel_f_post_boundary_force_balance": "element_reposition",
    "panel_f_post_force_source_connector": "path_reroute",
    "panel_f_post_source_label_scale": "label_restyle",
    "panel_f_post_label_force_cleanup": "density_reduce",
    "panel_f_post_force_spacing_finish": "element_reposition",
    "panel_f_post_spacing_source_finish": "element_reposition",
    "panel_f_post_source_trap_hierarchy": "style_hierarchy",
    "panel_f_post_trap_gap_readability": "element_reposition",
    "panel_f_post_gap_label_relief": "density_reduce",
    "panel_f_post_label_relief_source_settle": "label_reposition",
    "panel_f_trap_label_left_rail": "label_reposition",
    # fig5 manual one-offs (2026-08-02)
    "editorial_separator_refinement": "panel_layout",
    "charge_marker_containment_and_force_ownership": "semantic_correction",
    "cross_state_force_hierarchy": "style_hierarchy",
    "editorial-semantic-redraw": "subregion_redraw",
    "event-label-ownership-and-editorial-economy": "density_reduce",
    "clip-attached-manual-lead-separation": "path_reroute",
    "composition_evidence_boundary": "panel_layout",
    "cross_family_semantic_contract_transfer": "semantic_correction",
    "vector_style_hierarchy": "style_hierarchy",
}


def canonical_edit_family(name: str) -> str:
    """Fold a family name to canonical; unknown historical names pass through."""
    if name in CANONICAL_EDIT_FAMILIES:
        return name
    return LEGACY_EDIT_FAMILY_ALIASES.get(name, name)


def validate_edit_family(name: str) -> str:
    """Return the canonical family for a write path, rejecting unknown names."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("edit_family must be a non-empty string")
    folded = canonical_edit_family(name.strip())
    if folded not in CANONICAL_EDIT_FAMILIES:
        allowed = ", ".join(sorted(CANONICAL_EDIT_FAMILIES))
        raise ValueError(
            f"unknown edit_family {name!r}; use one of the controlled vocabulary: {allowed}"
        )
    return folded
