from pathlib import Path
import unittest


FIXTURES = Path(__file__).parent / "fixtures" / "docs"


class TemplateDetectionTests(unittest.TestCase):
    def test_empty_subtask_implementation_template_is_detected(self) -> None:
        from tools.doc_governor.template_detection import detect_template_signals

        text = (FIXTURES / "empty_subtask_implementation.md").read_text(encoding="utf-8")
        template_like, diagnostics = detect_template_signals(
            path="SUBTASK_IMPLEMENTATION.md",
            text=text,
            doc_kind="subtask_implementation",
        )

        self.assertTrue(template_like)
        self.assertEqual(
            {diag["code"] for diag in diagnostics},
            {
                "TEMPLATE_EMPTY_SUBTASK_IMPLEMENTATION",
                "TEMPLATE_UNIFORM_IMPLEMENTATION_TEMPLATE",
            },
        )

    def test_placeholder_residue_is_detected(self) -> None:
        from tools.doc_governor.template_detection import detect_template_signals

        text = (FIXTURES / "placeholder_subtask_design.md").read_text(encoding="utf-8")
        template_like, diagnostics = detect_template_signals(
            path="SUBTASK_DESIGN.md",
            text=text,
            doc_kind="subtask_design",
        )

        self.assertTrue(template_like)
        self.assertEqual(
            [diag["code"] for diag in diagnostics],
            ["TEMPLATE_PLACEHOLDER_RESIDUE"],
        )

    def test_normal_module_design_is_not_misdetected(self) -> None:
        from tools.doc_governor.template_detection import detect_template_signals

        text = (FIXTURES / "real_module_design.md").read_text(encoding="utf-8")
        template_like, diagnostics = detect_template_signals(
            path="MODULE_DESIGN.md",
            text=text,
            doc_kind="module_design",
        )

        self.assertFalse(template_like)
        self.assertEqual(diagnostics, [])


if __name__ == "__main__":
    unittest.main()
