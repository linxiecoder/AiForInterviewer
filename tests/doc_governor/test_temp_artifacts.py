import shutil
import tempfile
import unittest
from pathlib import Path

from tools.testing.temp_artifacts import (
    DirectoryLeakGuard,
    DirectoryWatchSpec,
    ManagedTempArtifacts,
    ManagedTempArtifactsTestCase,
)


class ManagedTempArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox_root = Path(tempfile.gettempdir()) / "ai-for-interviewer-temp-artifacts-tests"
        shutil.rmtree(self.sandbox_root, ignore_errors=True)
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.watch_root = self.sandbox_root / "watch-root"
        self.watch_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.sandbox_root, ignore_errors=True)

    def test_workspace_is_created_under_fixed_root_and_cleanup_prunes_owner_shell(self) -> None:
        manager = ManagedTempArtifacts(
            test_id="tests.doc_governor.test_temp_artifacts.workspace_cleanup",
            temp_root=self.sandbox_root / "managed-root",
        )
        workspace = manager.make_temp_dir("workspace")
        owner_root = workspace.parent
        marker = workspace / "marker.txt"
        marker.write_text("ok", encoding="utf-8")

        self.assertTrue(workspace.exists())
        self.assertEqual(owner_root.parent, self.sandbox_root / "managed-root")

        manager.cleanup()

        self.assertFalse(workspace.exists())
        self.assertFalse(owner_root.exists())
        self.assertTrue((self.sandbox_root / "managed-root").exists())

    def test_cleanup_can_keep_artifacts_for_debugging(self) -> None:
        manager = ManagedTempArtifacts(
            test_id="tests.doc_governor.test_temp_artifacts.keep_debug",
            temp_root=self.sandbox_root / "managed-root",
            keep_artifacts=True,
        )
        workspace = manager.make_temp_dir("workspace")

        manager.cleanup()

        self.assertTrue(workspace.exists())

    def test_watch_root_detects_unexpected_new_directory(self) -> None:
        manager = ManagedTempArtifacts(
            test_id="tests.doc_governor.test_temp_artifacts.leak_guard",
            temp_root=self.sandbox_root / "managed-root",
            watch_roots=[self.watch_root],
        )
        manager.make_temp_dir("workspace")
        leaked_dir = self.watch_root / "_tmp-leaked"
        leaked_dir.mkdir()

        with self.assertRaisesRegex(AssertionError, "_tmp-leaked"):
            manager.cleanup()

    def test_directory_leak_guard_ignores_allowed_new_directory_names(self) -> None:
        guard = DirectoryLeakGuard(
            [
                DirectoryWatchSpec(
                    root=self.watch_root,
                    ignore_name_patterns=("pytest-cache-files-*",),
                )
            ]
        )
        (self.watch_root / "pytest-cache-files-demo").mkdir()

        self.assertEqual(guard.find_unexpected_directories(), [])

    def test_directory_leak_guard_reports_unexpected_new_directory_names(self) -> None:
        guard = DirectoryLeakGuard([DirectoryWatchSpec(root=self.watch_root)])
        leaked_dir = self.watch_root / "_tmp-session-leak"
        leaked_dir.mkdir()

        leaks = guard.find_unexpected_directories()
        self.assertEqual(len(leaks), 1)
        self.assertIn("_tmp-session-leak", leaks[0])


class ManagedTempArtifactsTestCaseTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "case-root"
    managed_watch_roots = ()

    def test_base_case_creates_temp_root(self) -> None:
        self.assertTrue(self.temp_root.exists())
        self.assertIn("case-root-", self.temp_root.name)


if __name__ == "__main__":
    unittest.main()
