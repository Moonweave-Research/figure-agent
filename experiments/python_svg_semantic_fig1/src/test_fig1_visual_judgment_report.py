from __future__ import annotations

import unittest

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

    def test_markdown_uses_cautious_human_review_language(self) -> None:
        markdown = markdown_for_report(build_visual_judgment_report(build_scene(), SVG))

        self.assertIn("report-only", markdown)
        self.assertIn("Human visual review remains required", markdown)
        self.assertIn("possible issue", markdown)
        self.assertNotIn("publication-ready", markdown)
        self.assertNotIn("complete approval", markdown.lower())

    def test_report_is_not_added_to_strict_gate_runner(self) -> None:
        from run_fig1_gates import GATES

        self.assertNotIn("report_fig1_visual_judgment.py", {gate.script for gate in GATES})


if __name__ == "__main__":
    unittest.main()
