import unittest

from tools.doc_governor.document_scan import scan_document
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


class DocumentScanTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "document-scan"

    def test_scan_document_collects_repo_truth_and_narrative_signals(self) -> None:
        repo_root = self.temp_root
        document_path = repo_root / "docs" / "spec.md"
        existing_path = repo_root / "tools" / "doc_governor" / "validate.py"
        existing_path.parent.mkdir(parents=True, exist_ok=True)
        existing_path.write_text("# stub\n", encoding="utf-8")
        document_path.parent.mkdir(parents=True, exist_ok=True)
        document_path.write_text(
            (
                "# Spec\n\n"
                "## Scope\n\n"
                "Current references: `tools/doc_governor/validate.py` and `apps/api/app/main.py`.\n\n"
                "This still assumes a monorepo target.\n\n"
                "doc-governor validate-state evaluate-state confirm-transition open-window\n"
            ),
            encoding="utf-8",
        )

        facts = scan_document(
            repo_root=repo_root,
            path="docs/spec.md",
            required_sections=[{"section_id": "scope", "heading": "## Scope"}],
            document_registry={},
        )

        self.assertEqual(
            facts["repo_truth"]["referenced_paths"],
            ["apps/api/app/main.py", "tools/doc_governor/validate.py"],
        )
        self.assertEqual(
            facts["repo_truth"]["missing_paths"],
            ["apps/api/app/main.py"],
        )
        self.assertEqual(
            facts["repo_truth"]["existing_paths"],
            ["tools/doc_governor/validate.py"],
        )
        self.assertEqual(
            facts["direction_drift"]["future_blueprint_terms"],
            ["apps/api", "monorepo"],
        )
        self.assertEqual(
            facts["direction_drift"]["governance_term_count"],
            5,
        )


if __name__ == "__main__":
    unittest.main()
