import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class CliSmokeTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            stdin=subprocess.DEVNULL,
        )

    def test_module_entrypoint_help(self) -> None:
        result = self._run("-m", "tools.doc_governor.cli", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doc-governor", result.stdout)

    def test_script_entrypoint_help(self) -> None:
        result = self._run("tools/doc_governor/cli.py", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doc-governor", result.stdout)
