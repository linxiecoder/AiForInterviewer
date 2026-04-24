import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.basic_memory_guard.bm_cli import BmCommandError
from tools.basic_memory_guard.cli import main
from tools.basic_memory_guard.guard import MemoryGuardService, SafeWriteRequest
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


class FakeBmClient:
    def __init__(self) -> None:
        self.search_calls: list[tuple[str, str, str]] = []
        self.write_calls: list[dict] = []
        self.edit_calls: list[dict] = []
        self.read_calls: list[tuple[str, str]] = []
        self.search_responses: dict[tuple[str, str], dict | Exception] = {}
        self.notes: dict[str, dict] = {}
        self.fail_write: Exception | None = None
        self.fail_edit: Exception | None = None

    def seed_note(self, *, title: str, folder: str, content: str) -> None:
        permalink = f"ai-for-interviewer/{folder}/{title.lower().replace(' ', '-')}"
        note = {
            "title": title,
            "permalink": permalink,
            "file_path": f"{folder}/{title}.md",
            "content": content,
        }
        self.notes[title] = note
        self.notes[permalink] = note

    def _find_note(self, identifier: str) -> dict | None:
        exact = self.notes.get(identifier)
        if exact is not None:
            return exact
        for note in self.notes.values():
            if note.get("file_path") == identifier:
                return note
        return None

    def search_notes(
        self,
        query: str,
        *,
        mode: str,
        project: str,
        page_size: int,
    ) -> dict:
        self.search_calls.append((mode, query, project))
        configured = self.search_responses.get((mode, query))
        if isinstance(configured, Exception):
            raise configured
        if configured is not None:
            return configured

        lowered = query.lower()
        results = []
        for key, note in self.notes.items():
            if key != note.get("title"):
                continue
            haystacks = [
                (note.get("title") or "").lower(),
                (note.get("content") or "").lower(),
                (note.get("permalink") or "").lower(),
            ]
            if any(lowered in item for item in haystacks):
                results.append(
                    {
                        "title": note.get("title"),
                        "permalink": note.get("permalink"),
                        "file_path": note.get("file_path"),
                        "content": note.get("content"),
                    }
                )
        return {"results": results[:page_size]}

    def write_note(
        self,
        *,
        title: str,
        folder: str,
        content: str,
        project: str,
        tags: list[str] | None = None,
    ) -> dict:
        if self.fail_write is not None:
            raise self.fail_write
        self.write_calls.append(
            {
                "title": title,
                "folder": folder,
                "content": content,
                "project": project,
                "tags": tags or [],
            }
        )
        self.seed_note(title=title, folder=folder, content=content)
        return {"title": title}

    def edit_note(
        self,
        identifier: str,
        *,
        operation: str,
        content: str,
        project: str,
    ) -> dict:
        if self.fail_edit is not None:
            raise self.fail_edit
        self.edit_calls.append(
            {
                "identifier": identifier,
                "operation": operation,
                "content": content,
                "project": project,
            }
        )
        note = self._find_note(identifier)
        if note is None:
            raise BmCommandError(
                ["bm", "tool", "edit-note", identifier],
                1,
                "",
                f"missing note: {identifier}",
            )
        note["content"] = f"{note['content']}\n{content}"
        return {"identifier": identifier}

    def read_note(
        self,
        identifier: str,
        *,
        project: str,
        include_frontmatter: bool,
    ) -> dict:
        self.read_calls.append((identifier, project))
        note = self._find_note(identifier)
        if note is None:
            raise BmCommandError(
                ["bm", "tool", "read-note", identifier],
                1,
                "",
                f"missing note: {identifier}",
            )
        return note

    def recent_activity(
        self,
        *,
        project: str,
        timeframe: str,
        page_size: int,
    ) -> list[dict]:
        return list(self.notes.values())[:page_size]


class MemoryGuardServiceTests(ManagedTempArtifactsTestCase):
    managed_watch_roots = (Path(__file__).parent,)

    def setUp(self) -> None:
        super().setUp()
        self.memory_root = self.temp_root / "basic-memory" / "AiForInterviewer"
        self.memory_root.mkdir(parents=True, exist_ok=True)
        self.client = FakeBmClient()
        self.service = MemoryGuardService(
            bm_client=self.client,
            memory_root=self.memory_root,
        )

    def test_safe_write_allows_whitelist_directory_and_triggers_readback(self) -> None:
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="BaseTopic A",
                content="# BaseTopic A\n\n- allow whitelist directory",
            )
        )
        self.assertTrue(result.ok)
        self.assertEqual("created", result.action)
        self.assertEqual(1, len(self.client.write_calls))
        self.assertGreaterEqual(len(self.client.search_calls), 1)
        self.assertGreaterEqual(len(self.client.read_calls), 1)
        self.assertTrue(result.verification is not None)
        self.assertTrue(result.verification.ok)

    def test_safe_write_rejects_root_directory(self) -> None:
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="/",
                title="forbidden-dir-title",
                content="should reject root",
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual("rejected", result.action)
        self.assertIn("根目录", result.reason or "")
        self.assertEqual([], self.client.write_calls)

    def test_safe_write_rejects_notes_directory(self) -> None:
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="notes",
                title="forbidden-dir-title",
                content="should reject notes",
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual("rejected", result.action)
        self.assertIn("notes", result.reason)
        self.assertEqual([], self.client.write_calls)

    def test_safe_write_rejects_unconfirmed_decision(self) -> None:
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="20-decisions",
                title="unconfirmed decision",
                content="unconfirmed decision should be blocked",
                decision_status="proposed",
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual("rejected", result.action)
        self.assertIn("confirmed", result.reason)
        self.assertEqual([], self.client.write_calls)

    def test_safe_write_updates_existing_topic_instead_of_creating_new_note(self) -> None:
        self.client.seed_note(
            title="same-title-update",
            folder="90-session-summaries",
            content="# same-title-update\n\n- existing content",
        )
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="same-title-update",
                content="- append content",
            )
        )
        self.assertTrue(result.ok)
        self.assertEqual("updated", result.action)
        self.assertEqual([], self.client.write_calls)
        self.assertEqual(1, len(self.client.edit_calls))
        self.assertIn("- append content", self.client.notes["same-title-update"]["content"])
        self.assertIsNotNone(result.verification)
        self.assertTrue(result.verification.ok)

    def test_safe_write_rejects_same_title_in_other_directory(self) -> None:
        self.client.seed_note(
            title="same-title-cross-dir",
            folder="00-project",
            content="# same-title-cross-dir",
        )
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="same-title-cross-dir",
                content="should be blocked to different directory same title",
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual("rejected", result.action)
        self.assertEqual("title_conflict_different_directory", result.reason)
        self.assertIsNotNone(result.fallback_package)
        self.assertEqual(0, len(self.client.write_calls))

    def test_safe_write_allows_creation_with_approximate_hit_and_warns(self) -> None:
        self.client.seed_note(
            title="2026-04-24 doc_governance session-flow round one",
            folder="90-session-summaries",
            content="# 2026-04-24 doc_governance session-flow round one\n\n- context content",
        )
        self.client.search_responses[(
            "hybrid",
            "2026-04-24 Basic Memory Guard temp-write validation",
        )] = {
            "results": [
                {
                    "title": "2026-04-24 doc_governance session-flow round one",
                    "permalink": "ai-for-interviewer/90-session-summaries/2026-04-24-doc_governance-session-flow-round-one",
                    "file_path": "90-session-summaries/2026-04-24-doc_governance-session-flow-round-one.md",
                    "content": "# 2026-04-24 doc_governance session-flow round one",
                }
            ]
        }
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="2026-04-24 Basic Memory Guard temp-write validation",
                content="this is approximate title test",
            )
        )
        self.assertTrue(result.ok)
        self.assertEqual("created", result.action)
        self.assertIn("related_hits_found", result.warnings)
        self.assertEqual(1, len(self.client.write_calls))
        self.assertIsNotNone(result.related_hits)
        self.assertGreaterEqual(len(result.related_hits or []), 1)

    def test_safe_write_rejects_stale_search_hit(self) -> None:
        self.client.search_responses[(
            "hybrid",
            "incomplete-test-topic",
        )] = {
            "results": [
                {
                    "title": "incomplete-test-topic",
                    "permalink": None,
                    "file_path": None,
                    "content": "only used to test stale fields",
                }
            ]
        }
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="incomplete-test-topic",
                content="allow create and warn",
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual("stale_or_unreadable_existing_note", result.reason)
        self.assertIn("stale_search_hit_found", result.warnings)
        self.assertIsNotNone(result.stale_hit)

    def test_safe_write_handles_read_note_content_none_without_crash(self) -> None:
        stale_title = "null-content-topic"
        note_file = self.memory_root / "90-session-summaries" / f"{stale_title}.md"
        note_file.parent.mkdir(parents=True, exist_ok=True)
        note_file.write_text("exists for stale-readability check", encoding="utf-8")
        self.client.notes[stale_title] = {
            "title": stale_title,
            "permalink": f"ai-for-interviewer/90-session-summaries/{stale_title}",
            "file_path": "90-session-summaries/null-content-topic.md",
            "content": None,
        }
        self.client.search_responses[(
            "hybrid",
            stale_title,
        )] = {
            "results": [self.client.notes[stale_title]]
        }

        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title=stale_title,
                content="- append segment",
            )
        )
        self.assertTrue(result.ok)
        self.assertEqual("updated", result.action)
        self.assertTrue(result.verification is not None)
        self.assertTrue(result.verification.ok)

    def test_safe_write_created_verification_with_fragment_check(self) -> None:
        class TruncatingWriteClient(FakeBmClient):
            def write_note(
                self,
                *,
                title: str,
                folder: str,
                content: str,
                project: str,
                tags: list[str] | None = None,
            ) -> dict:
                response = super().write_note(
                    title=title,
                    folder=folder,
                    content=content,
                    project=project,
                    tags=tags,
                )
                note = self._find_note(title)
                assert note is not None
                note["content"] = content[:120]
                return response

        service = MemoryGuardService(
            bm_client=TruncatingWriteClient(),
            memory_root=self.memory_root,
        )
        long_content = "# " + ("x" * 180) + "\n- created fragment"
        result = service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="fragment-check-created",
                content=long_content,
            )
        )
        self.assertTrue(result.ok)
        self.assertEqual("created", result.action)
        self.assertTrue(result.verification is not None)
        self.assertTrue(result.verification.ok)

    def _set_partial_edit_behavior(self, append_text: str) -> None:
        original_edit = self.client.edit_note

        def edit_note(
            identifier: str,
            *,
            operation: str,
            content: str,
            project: str,
        ) -> dict:
            note = self.client._find_note(identifier)
            if note is None:
                return original_edit(identifier, operation=operation, content=content, project=project)
            note["content"] = f"{note.get('content', '')}\n{append_text}"
            return {"identifier": identifier}

        self.client.edit_note = edit_note

    def test_safe_write_updated_verification_checks_append_fragment(self) -> None:
        update_title = "updated-fragment-check"
        self.client.seed_note(
            title=update_title,
            folder="90-session-summaries",
            content="# existing\n- old content",
        )
        append_text = "- append-only-segment"
        self._set_partial_edit_behavior(append_text)
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title=update_title,
                content=append_text,
            )
        )
        self.assertTrue(result.ok)
        self.assertEqual("updated", result.action)
        self.assertTrue(result.verification is not None)
        self.assertTrue(result.verification.ok)

    def test_verify_readback_missing_note_returns_structured_failure(self) -> None:
        result = self.service.verify_readback(
            title="missing-topic",
            directory="90-session-summaries",
            expected_fragments=["any-fragment"],
        )
        self.assertFalse(result.ok)
        self.assertEqual("verify_failed", result.action)
        self.assertEqual("note_not_found", result.reason)
        self.assertIsNotNone(result.fallback_package)
        self.assertEqual("90-session-summaries", result.fallback_package["directory"])
        self.assertEqual("missing-topic", result.fallback_package["title"])
        self.assertEqual("any-fragment", result.fallback_package["expected_fragment"])
        self.assertIn("manual_recommended_action", result.fallback_package)

    def test_verify_readback_content_none_does_not_crash(self) -> None:
        self.client.notes["content-none"] = {
            "title": "content-none",
            "permalink": "ai-for-interviewer/90-session-summaries/content-none",
            "file_path": "90-session-summaries/content-none.md",
            "content": None,
        }
        result = self.service.verify_readback(
            title="content-none",
            directory="90-session-summaries",
            expected_fragments=["should-not-crash"],
        )
        self.assertFalse(result.ok)
        self.assertEqual("verify_failed", result.action)
        self.assertIn("expected fragment missing", result.reason)

    def test_verify_readback_expected_fragment_mismatch(self) -> None:
        self.client.write_note(
            title="expected-fragment-check",
            folder="90-session-summaries",
            content="full-content",
            project="AiForInterviewer",
        )
        result = self.service.verify_readback(
            title="expected-fragment-check",
            directory="90-session-summaries",
            expected_fragments=["missing-fragment"],
        )
        self.assertFalse(result.ok)
        self.assertEqual("verify_failed", result.action)
        self.assertIn("expected fragment missing: missing-fragment", result.reason)
        self.assertIsNotNone(result.fallback_package)
        self.assertIn("expected fragment missing", result.fallback_package.get("reason", ""))

    def test_safe_write_emits_fallback_when_bm_write_fails(self) -> None:
        self.client.fail_write = BmCommandError(
            ["bm", "tool", "write-note"],
            1,
            "",
            "boom",
        )
        result = self.service.safe_write(
            SafeWriteRequest(
                directory="90-session-summaries",
                title="write-fail-test",
                content="write fail should return fallback",
            )
        )
        self.assertFalse(result.ok)
        self.assertIsNotNone(result.fallback_package)
        self.assertEqual("90-session-summaries", result.fallback_package["directory"])
        self.assertEqual("write-fail-test", result.fallback_package["title"])

    def test_preflight_read_degrades_when_vector_search_fails(self) -> None:
        self.client.seed_note(
            title="preflight-topic-c",
            folder="90-session-summaries",
            content="# preflight-topic-c\n\n- hybrid fallback available",
        )
        self.client.search_responses[("vector", "preflight-topic-c")] = BmCommandError(
            ["bm", "tool", "search-notes", "--vector"],
            1,
            "",
            "vector backend unavailable",
        )
        self.client.search_responses[("hybrid", "preflight-topic-c")] = {"results": []}
        self.client.search_responses[("default", "preflight-topic-c")] = {"results": []}

        result = self.service.preflight_read(queries=["preflight-topic-c"])
        self.assertTrue(result.ok)
        self.assertTrue(any(item.mode == "vector" and not item.ok for item in result.attempts))
        self.assertTrue(any(item.mode == "title" and item.ok for item in result.attempts))
        self.assertGreaterEqual(len(result.hits), 1)


class MemoryGuardCliSmokeTests(unittest.TestCase):
    def test_help_lists_expected_commands(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--help"])

        output = buffer.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("preflight-read", output)
        self.assertIn("safe-write", output)
        self.assertIn("verify-readback", output)
        self.assertIn("emit-fallback", output)

    def test_subcommand_accepts_shared_options_after_command_name(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "emit-fallback",
                    "--project",
                    "AiForInterviewer",
                    "--memory-root",
                    "D:/.basic-memory/AiForInterviewer",
                    "--directory",
                    "90-session-summaries",
                    "--title",
                    "CLI fallback title",
                    "--content",
                    "content",
                    "--reason",
                    "manual",
                ]
            )
        output = buffer.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("CLI fallback title", output)


if __name__ == "__main__":
    unittest.main()
