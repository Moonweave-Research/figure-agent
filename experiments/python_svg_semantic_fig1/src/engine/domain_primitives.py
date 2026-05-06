from __future__ import annotations

from dataclasses import dataclass

from engine.scene import Point, Rect


@dataclass(frozen=True)
class CompositionSwatch:
    label: str
    color: str


@dataclass(frozen=True)
class SulfurPolymerOrigin:
    s8_atom_count: int
    chain_atom_count: int
    heat_label: str
    chain_label: str
    swatches: tuple[CompositionSwatch, ...]
    footer_label: str
    causal_segments: tuple[str, ...] = ()
    trap_origin_mechanisms: tuple[str, ...] = ()


@dataclass(frozen=True)
class BandEdge:
    label: str
    y: float


@dataclass(frozen=True)
class BandDiagram:
    energy_axis_label: str
    lumo: BandEdge
    homo: BandEdge
    gap_label: str


@dataclass(frozen=True)
class TrapLevelSet:
    shallow_positions: tuple[float, ...]
    deep_positions: tuple[float, ...]
    shallow_radius: float
    deep_radius: float
    shallow_label: str
    deep_label: str
    depth_label: str
    energy_reference: str
    deep_depth_range_ev: tuple[float, float]
    quantitative_status: str


@dataclass(frozen=True)
class DOSLobes:
    model: str
    shallow_center_y: float
    deep_center_y: float
    shallow_width: float
    deep_width: float
    shallow_height: float
    deep_height: float
    shallow_area: float
    deep_area: float
    min_deep_to_shallow_ratio: float
    shallow_sigma: tuple[float, float]
    deep_sigma: tuple[float, float]
    samples: int


@dataclass(frozen=True)
class DeepTrapHero:
    title: str
    subtitle: str
    hero_ratio: float
    band_object_id: str
    trap_object_id: str
    dos_object_id: str
    message: str
    causal_role: str = ""
    converged_picture_label: str = ""


@dataclass(frozen=True)
class EvidenceModality:
    label: str
    object_kind: str
    object_id: str
    title: str
    accent: str


@dataclass(frozen=True)
class EvidenceTrio:
    title: str
    modalities: tuple[EvidenceModality, ...]
    badge_gap: float


@dataclass(frozen=True)
class PEHysteresisPlot:
    title: str
    model: str
    loop_width: float
    loop_height: float
    remanence: float
    samples_per_branch: int
    color: str


@dataclass(frozen=True)
class PowerLawDecayPlot:
    title: str
    model: str
    slope: float
    log_t_min: float
    log_t_max: float
    log_i_top: float
    log_i_bottom: float
    samples: int
    label: str
    color: str
    causal_role: str = ""
    extracted_parameter: str = ""


@dataclass(frozen=True)
class ISPDPlot:
    title: str
    model: str
    shallow_width: float
    deep_width: float
    shallow_height: float
    deep_height: float
    shallow_sigma: tuple[float, float]
    deep_sigma: tuple[float, float]
    samples: int
    color: str
    trap_depth_output: str = ""


@dataclass(frozen=True)
class TrapModelFlow:
    title: str
    steps: tuple[str, ...]
    conclusion: str
    causal_chain: tuple[str, ...] = ()
    debye_reference_label: str = ""
    delay_parameter: str = ""
    output_distribution: str = ""


@dataclass(frozen=True)
class MacroscopicProbe:
    title: str
    frames: tuple[str, str]
    cantilever_object_id: str
    electrode_object_id: str
    force_object_id: str


@dataclass(frozen=True)
class PolymerCantilever:
    charge_sign: str
    initial_bend: str
    repulsive_bend: str
    charge_positions: tuple[Point, ...]
    frame_bounds: tuple[Rect, Rect]


@dataclass(frozen=True)
class Electrode:
    sign: str
    label: str
    center: Point
    bounds: Rect


@dataclass(frozen=True)
class ForceArrow:
    start: Point
    end: Point
    label: str
    sign_condition: str


@dataclass(frozen=True)
class MaxwellAttractionCue:
    start: Point
    end: Point
    label: str
    role: str


@dataclass(frozen=True)
class LayoutFlow:
    title: str
    arrow_pairs: tuple[tuple[Point, Point], ...]
    direction: str
