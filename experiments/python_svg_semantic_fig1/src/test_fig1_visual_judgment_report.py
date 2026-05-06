from __future__ import annotations

import unittest
from dataclasses import replace

from fig1_l1_scene import build_scene
from report_fig1_visual_judgment import (
    SVG,
    build_visual_judgment_report,
    markdown_for_report,
)


class Fig1VisualJudgmentReportTests(unittest.TestCase):
    def test_report_exposes_expected_report_only_categories(self) -> None:
        report = build_visual_judgment_report(build_scene(), SVG)

        self.assertTrue(report["report_only"])
        self.assertEqual([], report["blocking_failures"])
        self.assertEqual(
            [
                "Panel Density",
                "Text / Text Near-Collision",
                "Text / Shape Conflict",
                "Visual Hierarchy",
                "Reading Order",
                "Reference Divergence",
                "Human Review Prompts",
            ],
            [category["name"] for category in report["categories"]],
        )
        self.assertGreaterEqual(len(report["panels"]), 5)
        self.assertGreater(len(report["text_boxes"]), 20)
        self.assertGreater(len(report["semantic_boxes"]), 10)

    def test_report_documents_v21_cantilever_reference_divergence(self) -> None:
        report = build_visual_judgment_report(build_scene(), SVG)
        divergence = next(category for category in report["categories"] if category["name"] == "Reference Divergence")
        joined = "\n".join(item["message"] for item in divergence["items"])

        self.assertIn("force_target=cantilever", joined)
        self.assertIn("cantilever_leftward_repulsion", joined)
        self.assertIn("intentional", joined.lower())

    def test_reference_divergence_reflects_force_target_mutation(self) -> None:
        scene = build_scene()
        force = scene.object_by_id("repulsion_arrow").payload
        drifted_scene = scene.replace_payload("repulsion_arrow", replace(force, force_target="electrode"))

        report = build_visual_judgment_report(drifted_scene, SVG)
        divergence = next(category for category in report["categories"] if category["name"] == "Reference Divergence")
        joined = "\n".join(item["message"] for item in divergence["items"])

        self.assertIn("force_target=electrode", joined)
        self.assertIn("leftward=True", joined)
        self.assertIn("v21 contract expects force_target=cantilever and leftward=True", joined)
        self.assertNotIn("intentional v21 divergence retained", joined)
        self.assertTrue(any(item["severity"] == "possible issue" for item in divergence["items"]))

    def test_reference_divergence_reflects_direction_mutation(self) -> None:
        scene = build_scene()
        force = scene.object_by_id("repulsion_arrow").payload
        rightward_force = replace(force, start=force.end, end=force.start)
        drifted_scene = scene.replace_payload("repulsion_arrow", rightward_force)

        report = build_visual_judgment_report(drifted_scene, SVG)
        divergence = next(category for category in report["categories"] if category["name"] == "Reference Divergence")
        joined = "\n".join(item["message"] for item in divergence["items"])

        self.assertIn("force_target=cantilever", joined)
        self.assertIn("leftward=False", joined)
        self.assertIn("arrow_direction=force_target_mismatch", joined)
        self.assertNotIn("intentional v21 divergence retained", joined)
        self.assertTrue(any(item["severity"] == "possible issue" for item in divergence["items"]))

    def test_markdown_uses_cautious_human_review_language(self) -> None:
        markdown = markdown_for_report(build_visual_judgment_report(build_scene(), SVG))

        self.assertIn("report-only", markdown)
        self.assertIn("Human visual review remains required", markdown)
        self.assertIn("candidate visual risks", markdown)
        self.assertNotIn("publication-ready", markdown)
        self.assertNotIn("complete approval", markdown.lower())

    def test_expected_composite_labels_are_not_reported_as_text_collisions(self) -> None:
        report = build_visual_judgment_report(build_scene(), SVG)
        text_collision = next(category for category in report["categories"] if category["name"] == "Text / Text Near-Collision")
        joined = "\n".join(item["message"] for item in text_collision["items"])

        self.assertNotIn("'Et ~' near '0.5-1.0 eV'", joined)
        self.assertNotIn("'I(t) ~' near 't^-n'", joined)
        self.assertNotIn("'Debye' near 'exp(-t/tau)'", joined)

    def test_human_review_prompts_include_multiple_risk_categories(self) -> None:
        report = build_visual_judgment_report(build_scene(), SVG)
        prompts = next(category for category in report["categories"] if category["name"] == "Human Review Prompts")
        joined = "\n".join(item["message"] for item in prompts["items"])

        self.assertIn("reference divergence", joined)
        self.assertIn("force_target=cantilever", joined)
        self.assertIn("text / text near-collision", joined)
        self.assertIn("text / shape conflict", joined)
        self.assertIn("visual hierarchy", joined)
        self.assertLessEqual(joined.count("panel density"), 2)

    def test_visual_hierarchy_bbox_salience_proxy_is_evidence_only(self) -> None:
        report = build_visual_judgment_report(build_scene(), SVG)
        hierarchy = next(category for category in report["categories"] if category["name"] == "Visual Hierarchy")
        salience_items = [item for item in hierarchy["items"] if "bbox salience proxy" in item["message"]]

        self.assertEqual(1, len(salience_items))
        self.assertEqual("evidence", salience_items[0]["severity"])

    def test_json_sidecar_is_not_required_by_docs_manifest(self) -> None:
        from check_fig1_docs_manifest import REQUIRED_MANIFEST_TOKENS, REQUIRED_V22_VISUAL_REPORT_TOKENS

        self.assertNotIn("fig1_visual_judgment_report.json", REQUIRED_MANIFEST_TOKENS)
        self.assertNotIn("fig1_visual_judgment_report.json", REQUIRED_V22_VISUAL_REPORT_TOKENS)

    def test_report_is_not_added_to_strict_gate_runner(self) -> None:
        from run_fig1_gates import GATES

        self.assertNotIn("report_fig1_visual_judgment.py", {gate.script for gate in GATES})


if __name__ == "__main__":
    unittest.main()
