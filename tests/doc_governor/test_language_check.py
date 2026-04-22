from __future__ import annotations

import re
import unittest

from tools.doc_governor.language_check import LanguagePolicy, check_markdown_language


class LanguageCheckTests(unittest.TestCase):
    def _codes(self, diagnostics: list) -> set[str]:
        return {item.code for item in diagnostics}

    def _assert_common_diagnostic_shape(self, diagnostics: list) -> None:
        self.assertTrue(diagnostics)
        for item in diagnostics:
            self.assertTrue(item.code)
            self.assertTrue(item.severity)
            self.assertTrue(item.entity_type)
            self.assertIsNotNone(item.entity_id)
            self.assertTrue(item.field_path)
            self.assertTrue(item.message)
            self.assertTrue(item.evidence)

    def test_heading_without_chinese_is_reported(self) -> None:
        diagnostics = check_markdown_language(
            path="docs/sample.md",
            text="""
            # API Overview

            本文档继续使用中文说明 `HTTP API` 的上下文。
            """,
        )

        self.assertIn("LANG_HEADING_NOT_CHINESE_BY_DEFAULT", self._codes(diagnostics))
        self._assert_common_diagnostic_shape(diagnostics)

    def test_body_without_chinese_dominance_is_reported(self) -> None:
        diagnostics = check_markdown_language(
            path="docs/sample.md",
            text="""
            # 中文标题

            Use the API to fetch records for the current user.
            Return the merged result after validation.
            """,
        )

        self.assertIn("LANG_BODY_NOT_CHINESE_DOMINANT", self._codes(diagnostics))

    def test_commands_paths_and_identifiers_are_ignored(self) -> None:
        diagnostics = check_markdown_language(
            path="docs/sample.md",
            text="""
            # 中文标题

            - `python -m pytest tests/doc_governor -q`
            - `apps/api/app/main.py`
            - `UserService.getById`
            - `APP_ENV=prod`
            """,
        )

        self.assertEqual(diagnostics, [])

    def test_explicit_heading_whitelist_can_suppress_warning(self) -> None:
        diagnostics = check_markdown_language(
            path="docs/sample.md",
            text="""
            # API Overview

            本文档仍然以中文为主，只保留必要技术名词。
            """,
            policy=LanguagePolicy(
                heading_exact_whitelist=("API Overview",),
                heading_pattern_whitelist=(re.compile(r"^HTTP API$"),),
            ),
        )

        self.assertEqual(diagnostics, [])


if __name__ == "__main__":
    unittest.main()
