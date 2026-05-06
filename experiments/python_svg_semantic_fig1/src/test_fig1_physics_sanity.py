from __future__ import annotations

import unittest
from dataclasses import replace

from fig1_l1_scene import build_scene
from verify_fig1_physics_sanity import physics_sanity_failures, physics_sanity_warnings


class Fig1PhysicsSanityTests(unittest.TestCase):
    def assert_physics_failure(self, scene: object, token: str, *, extra_claim_text: str = "") -> None:
        failures = physics_sanity_failures(scene, extra_claim_text=extra_claim_text)
        self.assertTrue(
            any(token in failure for failure in failures),
            f"expected failure containing {token!r}; got {failures}",
        )

    def test_current_scene_passes_hard_failures_but_reports_probe_target_gap(self) -> None:
        scene = build_scene()

        self.assertEqual([], physics_sanity_failures(scene))
        warnings = physics_sanity_warnings(scene)
        self.assertTrue(
            any("force_target" in warning for warning in warnings),
            f"expected force_target warning; got {warnings}",
        )

    def test_rejects_ground_truth_reference_authority(self) -> None:
        scene = build_scene()
        bad_scene = replace(scene, reference=replace(scene.reference, authority="ground_truth"))

        self.assert_physics_failure(bad_scene, "ground_truth")

    def test_rejects_lumo_homo_label_or_position_inversion(self) -> None:
        scene = build_scene()
        band = scene.object_by_id("band_diagram").payload
        bad_label_band = replace(band, lumo=replace(band.lumo, label="HOMO"))
        bad_position_band = replace(band, lumo=replace(band.lumo, y=0.90))

        self.assert_physics_failure(scene.replace_payload("band_diagram", bad_label_band), "LUMO/HOMO")
        self.assert_physics_failure(scene.replace_payload("band_diagram", bad_position_band), "LUMO/HOMO")

    def test_rejects_invalid_dos_numeric_parameters(self) -> None:
        scene = build_scene()
        lobes = scene.object_by_id("dos_lobes").payload
        bad_lobes = replace(lobes, shallow_width=0.0)

        self.assert_physics_failure(scene.replace_payload("dos_lobes", bad_lobes), "DOS")

    def test_rejects_invalid_pe_hysteresis_parameters(self) -> None:
        scene = build_scene()
        pe = scene.object_by_id("pe_hysteresis").payload
        bad_pe = replace(pe, remanence=1.25)

        self.assert_physics_failure(scene.replace_payload("pe_hysteresis", bad_pe), "P-E")

    def test_rejects_invalid_power_law_decay_semantics(self) -> None:
        scene = build_scene()
        decay = scene.object_by_id("power_law_decay").payload

        bad_slope = replace(decay, slope=0.2)
        bad_label = replace(decay, label="I(t) increases with t")
        bad_parameter = replace(decay, extracted_parameter="tau")

        self.assert_physics_failure(scene.replace_payload("power_law_decay", bad_slope), "power-law")
        self.assert_physics_failure(scene.replace_payload("power_law_decay", bad_label), "t^-n")
        self.assert_physics_failure(scene.replace_payload("power_law_decay", bad_parameter), "extracted parameter")

    def test_rejects_invalid_causal_chain_claim(self) -> None:
        scene = build_scene()
        flow = scene.object_by_id("trap_model_flow").payload
        bad_flow = replace(flow, causal_chain=("I(t) ~ t^-n", "Debye exp(-t/tau)", "n", "tau_d", "g(Et)"))

        self.assert_physics_failure(scene.replace_payload("trap_model_flow", bad_flow), "causal chain")

    def test_rejects_overclaim_text_for_schematic_distribution(self) -> None:
        scene = build_scene()

        self.assert_physics_failure(
            scene,
            "overclaim",
            extra_claim_text="Fig1 proves the exact measured g(Et) distribution.",
        )

    def test_rejects_like_charge_sign_condition_mismatch(self) -> None:
        scene = build_scene()
        electrode = scene.object_by_id("electrode").payload
        bad_electrode = replace(electrode, sign="-")

        self.assert_physics_failure(scene.replace_payload("electrode", bad_electrode), "like-charge")


if __name__ == "__main__":
    unittest.main()
