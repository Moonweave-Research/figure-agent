from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
SVG = ROOT / "fig1_reference_semantic.svg"
README = ROOT / "README.md"
PHYSICS_INVENTORY = ROOT / "physics_sanity_inventory_v20.md"
PHYSICS_CONTRACT = ROOT / "physics_sanity_contract_v20.md"
PHYSICS_HANDBACK = ROOT / "physics_sanity_gate_handback_v20.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


EXPECTED_CAUSAL_CHAIN = (
    "I(t) ~ t^-n",
    "n",
    "Debye exp(-t/tau)",
    "tau_d",
    "g(Et)",
)

CLAIM_TEXT_PATHS = (SVG, README, PHYSICS_HANDBACK)

OVERCLAIM_PATTERNS = (
    re.compile(
        r"\b(proves?|confirms?|validates?)\b.{0,80}\b(exact|measured|quantitative|true)\b.{0,80}\bg\(Et\)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(exact|measured|quantitative|true)\b.{0,80}\bg\(Et\).{0,80}\b(distribution|profile|DOS)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\bg\(Et\).{0,80}\b(is|as|equals)\b.{0,40}\b(exact|measured|quantitative|true)\b",
        re.IGNORECASE | re.DOTALL,
    ),
)


def physics_sanity_failures(scene: object, *, extra_claim_text: str = "") -> list[str]:
    failures: list[str] = []
    failures.extend(_check_reference_authority(scene))
    failures.extend(_check_band_and_traps(scene))
    failures.extend(_check_dos_parameters(scene))
    failures.extend(_check_power_law_decay(scene))
    failures.extend(_check_causal_chain(scene))
    failures.extend(_check_probe_charge_relation(scene))
    failures.extend(_check_probe_force_target_contract(scene))
    failures.extend(_check_probe_geometry(scene))
    failures.extend(_check_maxwell_cue(scene))
    failures.extend(_check_overclaim_text(extra_claim_text))
    return failures


def physics_sanity_warnings(scene: object) -> list[str]:
    warnings: list[str] = []
    try:
        force_arrow = scene.object_by_id("repulsion_arrow").payload
    except KeyError:
        return [
            "probe force target cannot be checked because repulsion_arrow is missing"
        ]

    if not getattr(force_arrow, "force_target", ""):
        warnings.append(
            "probe ForceArrow has no force_target/acted_on semantics; "
            "strict vector physics remains contract-deferred"
        )
    return warnings


def _check_reference_authority(scene: object) -> list[str]:
    authority = getattr(scene.reference, "authority", "")
    if authority == "ground_truth":
        return ["reference authority must not become ground_truth"]
    return []


def _check_band_and_traps(scene: object) -> list[str]:
    failures: list[str] = []
    band = scene.object_by_id("band_diagram").payload
    traps = scene.object_by_id("trap_level_set").payload

    if band.lumo.label != "LUMO" or band.homo.label != "HOMO":
        failures.append("LUMO/HOMO labels must remain bound to the correct band edges")
    if not band.lumo.y < band.homo.y:
        failures.append(
            "LUMO/HOMO vertical order must keep LUMO above HOMO on the energy schematic"
        )

    trap_positions = tuple(traps.shallow_positions) + tuple(traps.deep_positions)
    if not trap_positions:
        failures.append("trap level set must contain at least one trap position")
    if not all(band.lumo.y < position < band.homo.y for position in trap_positions):
        failures.append("trap positions must stay inside the LUMO/HOMO bandgap")
    if (
        traps.shallow_positions
        and traps.deep_positions
        and max(traps.shallow_positions) >= min(traps.deep_positions)
    ):
        failures.append(
            "shallow/deep trap ordering must keep deep traps deeper than shallow traps"
        )
    if traps.energy_reference != "normalized_bandgap_lumo_to_homo":
        failures.append(f"unexpected trap energy reference: {traps.energy_reference}")
    if traps.quantitative_status != "schematic_placeholder_until_fig3_ispd":
        failures.append(
            f"unexpected trap quantitative status: {traps.quantitative_status}"
        )
    if (
        not _positive_pair(traps.deep_depth_range_ev)
        or traps.deep_depth_range_ev[0] >= traps.deep_depth_range_ev[1]
    ):
        failures.append(f"invalid deep trap depth range: {traps.deep_depth_range_ev}")
    return failures


def _check_dos_parameters(scene: object) -> list[str]:
    failures: list[str] = []
    band = scene.object_by_id("band_diagram").payload
    lobes = scene.object_by_id("dos_lobes").payload
    ispd = scene.object_by_id("ispd_plot").payload

    if lobes.model != "gaussian_mixture":
        failures.append(f"DOS model must remain gaussian_mixture: {lobes.model}")
    numeric_values = (
        lobes.shallow_width,
        lobes.deep_width,
        lobes.shallow_height,
        lobes.deep_height,
        lobes.shallow_area,
        lobes.deep_area,
        lobes.min_deep_to_shallow_ratio,
    )
    if not all(value > 0 for value in numeric_values):
        failures.append(
            "DOS widths, heights, areas, and dominance ratio must be positive"
        )
    if not _positive_pair(lobes.shallow_sigma) or not _positive_pair(lobes.deep_sigma):
        failures.append("DOS sigma values must be positive pairs")
    if lobes.samples < 8:
        failures.append(
            f"DOS sample count is too small for schematic geometry: {lobes.samples}"
        )
    if (
        lobes.shallow_area > 0
        and lobes.deep_area / lobes.shallow_area < lobes.min_deep_to_shallow_ratio
    ):
        failures.append("DOS deep area must dominate shallow area")
    if (
        lobes.shallow_width > 0
        and lobes.deep_width / lobes.shallow_width < lobes.min_deep_to_shallow_ratio
    ):
        failures.append("DOS deep width must dominate shallow width")
    if not (band.lumo.y < lobes.shallow_center_y < lobes.deep_center_y < band.homo.y):
        failures.append("DOS shallow/deep centers must follow LUMO-to-HOMO order")

    if ispd.model != "gaussian_mixture":
        failures.append(f"ISPD model must remain gaussian_mixture: {ispd.model}")
    if not all(
        value > 0
        for value in (
            ispd.shallow_width,
            ispd.deep_width,
            ispd.shallow_height,
            ispd.deep_height,
        )
    ):
        failures.append("ISPD widths and heights must be positive")
    if not _positive_pair(ispd.shallow_sigma) or not _positive_pair(ispd.deep_sigma):
        failures.append("ISPD sigma values must be positive pairs")
    if ispd.samples < 8:
        failures.append(
            f"ISPD sample count is too small for schematic geometry: {ispd.samples}"
        )
    if ispd.trap_depth_output != "g(Et)":
        failures.append(
            f"ISPD trap-depth output must remain g(Et): {ispd.trap_depth_output}"
        )
    return failures


def _check_power_law_decay(scene: object) -> list[str]:
    decay = scene.object_by_id("power_law_decay").payload
    failures: list[str] = []
    if decay.model != "power_law_loglog":
        failures.append(
            f"power-law decay model must remain power_law_loglog: {decay.model}"
        )
    if decay.slope >= 0:
        failures.append("power-law decay slope must be negative for n > 0")
    if "t^-n" not in decay.label and "t^{-n}" not in decay.label:
        failures.append(f"power-law label must retain t^-n notation: {decay.label}")
    if decay.extracted_parameter != "n":
        failures.append(
            f"power-law extracted parameter must remain n: {decay.extracted_parameter}"
        )
    if decay.log_t_min >= decay.log_t_max:
        failures.append("power-law log-time bounds must increase")
    if decay.log_i_top <= decay.log_i_bottom:
        failures.append("power-law log-current bounds must keep top above bottom")
    if decay.samples < 8:
        failures.append(f"power-law sample count is too small: {decay.samples}")
    return failures


def _check_causal_chain(scene: object) -> list[str]:
    failures: list[str] = []
    flow = scene.object_by_id("trap_model_flow").payload

    if tuple(flow.causal_chain) != EXPECTED_CAUSAL_CHAIN:
        failures.append(
            "causal chain must remain I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)"
        )
    if flow.debye_reference_label != "Discharge Debye reference":
        failures.append(
            f"Debye reference label must remain a reference bridge: {flow.debye_reference_label}"
        )
    if flow.delay_parameter != "tau_d":
        failures.append(f"delay parameter must remain tau_d: {flow.delay_parameter}")
    if flow.output_distribution != "g(Et)":
        failures.append(
            f"output distribution must remain g(Et): {flow.output_distribution}"
        )
    return failures


def _check_probe_charge_relation(scene: object) -> list[str]:
    failures: list[str] = []
    cantilever = scene.object_by_id("polymer_cantilever").payload
    electrode = scene.object_by_id("electrode").payload
    force_arrow = scene.object_by_id("repulsion_arrow").payload

    if cantilever.charge_sign not in {"+", "-"}:
        failures.append(f"invalid trapped charge sign: {cantilever.charge_sign}")
    if electrode.sign not in {"+", "-"}:
        failures.append(f"invalid electrode sign: {electrode.sign}")
    if electrode.sign not in electrode.label:
        failures.append(
            f"electrode label must include electrode sign: {electrode.label}"
        )

    sign_condition = force_arrow.sign_condition.lower()
    if "equals" in sign_condition and cantilever.charge_sign != electrode.sign:
        failures.append(
            "like-charge force condition requires trapped charge and electrode signs to match"
        )
    if "repulsion" not in force_arrow.label.lower() and "qE" not in force_arrow.label:
        failures.append(
            f"force arrow label must remain a Coulomb/repulsion cue: {force_arrow.label}"
        )
    return failures


def _check_probe_force_target_contract(scene: object) -> list[str]:
    force_arrow = scene.object_by_id("repulsion_arrow").payload
    if not getattr(force_arrow, "force_target", ""):
        return []

    target = getattr(force_arrow, "force_target")
    valid_targets = {"cantilever", "electrode", "interaction_cue"}
    if target not in valid_targets:
        return [f"unknown ForceArrow force_target: {target}"]
    if target == "interaction_cue":
        return []

    cantilever = scene.object_by_id("polymer_cantilever").payload
    electrode = scene.object_by_id("electrode").payload
    charge_positions = tuple(cantilever.charge_positions)
    if not charge_positions:
        return [
            f"force_target={target} cannot be checked without trapped charge positions"
        ]

    arrow_dx = force_arrow.end.x - force_arrow.start.x
    if arrow_dx == 0:
        return [f"force_target={target} requires a nonzero horizontal force vector"]

    charge_center_x = sum(point.x for point in charge_positions) / len(charge_positions)
    electrode_dx = electrode.center.x - charge_center_x
    if electrode_dx == 0:
        return [
            f"force_target={target} cannot resolve electrode side relative to trapped charges"
        ]

    same_sign = cantilever.charge_sign == electrode.sign
    electrode_is_right = electrode_dx > 0
    actual_rightward = arrow_dx > 0
    if target == "cantilever":
        expected_rightward = (
            electrode_is_right if not same_sign else not electrode_is_right
        )
    else:
        expected_rightward = electrode_is_right if same_sign else not electrode_is_right

    if actual_rightward != expected_rightward:
        direction = "rightward" if expected_rightward else "leftward"
        relation = (
            "like-charge repulsion" if same_sign else "opposite-charge attraction"
        )
        return [f"force_target={target} vector must be {direction} for {relation}"]
    return []


def _check_probe_geometry(scene: object) -> list[str]:
    failures: list[str] = []
    cantilever = scene.object_by_id("polymer_cantilever").payload
    electrode = scene.object_by_id("electrode").payload
    force_arrow = scene.object_by_id("repulsion_arrow").payload
    charge_positions = tuple(cantilever.charge_positions)

    if (
        cantilever.initial_bend != "toward_electrode"
        or cantilever.repulsive_bend != "away_from_electrode"
    ):
        failures.append(
            "probe bend states must remain initial_bend=toward_electrode and repulsive_bend=away_from_electrode"
        )
    if cantilever.initial_bend == cantilever.repulsive_bend:
        failures.append(
            "probe bend states must distinguish initial and repulsive bends"
        )

    if not charge_positions:
        failures.append("probe geometry requires trapped charge positions")
        return failures

    if any(_point_in_rect(charge, electrode.bounds) for charge in charge_positions):
        failures.append(
            "charge/electrode separation violated: trapped charge overlaps electrode bounds"
        )

    charge_center_x = sum(point.x for point in charge_positions) / len(charge_positions)
    if electrode.center.x > charge_center_x and charge_center_x >= electrode.bounds.x:
        failures.append(
            "charge/electrode separation violated: charge cluster is not left of the right electrode"
        )
    if (
        electrode.center.x < charge_center_x
        and charge_center_x <= electrode.bounds.right
    ):
        failures.append(
            "charge/electrode separation violated: charge cluster is not right of the left electrode"
        )

    nearest_start_distance = min(
        _distance(force_arrow.start, charge) for charge in charge_positions
    )
    if nearest_start_distance > 105.0:
        failures.append(
            f"force arrow start is too far from trapped charge cluster: {nearest_start_distance:.1f}"
        )

    frame = cantilever.frame_bounds[-1]
    if not _point_in_rect(force_arrow.start, frame) or not _point_in_rect(
        force_arrow.end, frame
    ):
        failures.append("force arrow endpoints must remain inside the probe frame")
    return failures


def _check_maxwell_cue(scene: object) -> list[str]:
    maxwell = scene.object_by_id("maxwell_attraction_cue").payload
    failures: list[str] = []
    if maxwell.role != "secondary_reference_cue":
        failures.append(
            f"Maxwell attraction cue must remain secondary_reference_cue: {maxwell.role}"
        )
    if not maxwell.start.x < maxwell.end.x:
        failures.append(
            "Maxwell attraction cue must remain rightward toward the electrode"
        )
    return failures


def _check_overclaim_text(extra_claim_text: str) -> list[str]:
    claim_text = _read_claim_text(extra_claim_text)
    failures: list[str] = []
    for pattern in OVERCLAIM_PATTERNS:
        match = pattern.search(claim_text)
        if match:
            snippet = " ".join(match.group(0).split())
            failures.append(
                f"overclaim detected for schematic g(Et) distribution: {snippet}"
            )
            break
    return failures


def _read_claim_text(extra_claim_text: str) -> str:
    chunks = [extra_claim_text]
    for path in CLAIM_TEXT_PATHS:
        if path.exists():
            chunks.append(path.read_text())
    return "\n".join(chunks)


def _positive_pair(values: tuple[float, float]) -> bool:
    return len(values) == 2 and all(value > 0 for value in values)


def _point_in_rect(point: object, rect: object) -> bool:
    return rect.x <= point.x <= rect.right and rect.y <= point.y <= rect.bottom


def _distance(start: object, end: object) -> float:
    return ((start.x - end.x) ** 2 + (start.y - end.y) ** 2) ** 0.5


def main() -> int:
    try:
        from fig1_l1_scene import build_scene
    except ModuleNotFoundError as exc:
        print(f"missing Fig1 scene module: {exc}", file=sys.stderr)
        return 1

    scene = build_scene()
    failures = physics_sanity_failures(scene)
    warnings = physics_sanity_warnings(scene)

    for warning in warnings:
        print(f"[WARN] {warning}")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}", file=sys.stderr)
        print(f"fig1 physics sanity failed: {len(failures)} issue(s)", file=sys.stderr)
        return 1

    if warnings:
        print(f"fig1 physics sanity passed with {len(warnings)} warning(s)")
    else:
        print("fig1 physics sanity passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
