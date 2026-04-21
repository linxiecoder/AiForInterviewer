import io
import json
import subprocess
import shutil
from contextlib import redirect_stdout
from pathlib import Path
import unittest
import uuid
import sys


FIXTURES = Path(__file__).parent / "fixtures"


class BootstrapStateTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = Path(__file__).parent / "_tmp"
        temp_root.mkdir(exist_ok=True)
        self.repo_root = temp_root / f"repo_{uuid.uuid4().hex}"
        shutil.copytree(FIXTURES / "repo" / "prose_contamination", self.repo_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_root, ignore_errors=True)

    def run_cli(self, *args: str) -> tuple[int, dict]:
        from tools.doc_governor.cli import main

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(list(args))
        return exit_code, json.loads(stdout.getvalue())

    def test_bootstrap_state_generates_bootstrap_yaml_and_report(self) -> None:
        exit_code, payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )

        output_path = self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        report_path = self.repo_root / "docs" / "governance" / "BOOTSTRAP_REPORT.md"
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(output_path.exists())
        self.assertTrue(report_path.exists())
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("## Summary", report_text)
        self.assertIn("## Scan counts", report_text)
        self.assertIn("## Detected template-like docs", report_text)
        self.assertIn("## Ambiguous implementation docs", report_text)
        self.assertIn("## Diagnostics snapshot", report_text)

    def test_bootstrap_state_script_entrypoint_works(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/doc_governor/cli.py",
                "bootstrap-state",
                "--repo-root",
                str(self.repo_root),
            ],
            cwd=Path(__file__).resolve().parents[2],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(
            (self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml").exists()
        )

    def test_bootstrap_state_does_not_import_prose_claims(self) -> None:
        exit_code, _payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )

        self.assertEqual(exit_code, 0)
        import yaml

        state_path = self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        module_state = state["modules"]["M04"]["state"]["confirmed"]
        subtask_state = state["subtasks"]["ST04_01"]["state"]["confirmed"]
        self.assertIsNone(module_state["maturity"])
        self.assertEqual(module_state["candidate_status"], "none")
        self.assertEqual(module_state["review_status"], "unreviewed")
        self.assertEqual(module_state["readiness"], "blocked")
        self.assertIsNone(subtask_state["maturity"])
        self.assertEqual(subtask_state["candidate_status"], "none")
        self.assertEqual(subtask_state["review_status"], "unreviewed")
        self.assertEqual(subtask_state["readiness"], "blocked")
        self.assertEqual(subtask_state["implementation_doc_state"], "inactive_template")

    def test_existing_bootstrap_output_fails_without_overwrite(self) -> None:
        first_exit_code, _ = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )
        second_exit_code, payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )

        self.assertEqual(first_exit_code, 0)
        self.assertEqual(second_exit_code, 1)
        self.assertEqual(payload["diagnostics"][0]["code"], "BOOTSTRAP_OUTPUT_EXISTS")

    def test_overwrite_allows_replacing_bootstrap_outputs(self) -> None:
        first_exit_code, _ = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )
        second_exit_code, payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
            "--overwrite",
        )

        self.assertEqual(first_exit_code, 0)
        self.assertEqual(second_exit_code, 0)
        self.assertTrue(payload["ok"])

    def test_official_state_path_is_never_writable(self) -> None:
        exit_code, payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
            "--output",
            "docs/governance/DOC_STATE.yaml",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            payload["diagnostics"][0]["code"],
            "BOOTSTRAP_OFFICIAL_STATE_WRITE_FORBIDDEN",
        )
        self.assertFalse((self.repo_root / "docs" / "governance" / "DOC_STATE.yaml").exists())

    def test_ambiguous_implementation_doc_fails_without_writing_bootstrap(self) -> None:
        ambiguous_doc = (
            self.repo_root
            / "docs"
            / "modules"
            / "M04-match-analysis-and-evidence"
            / "sub_modules"
            / "ST04_01-bindings-and-input-contract"
            / "SUBTASK_IMPLEMENTATION.md"
        )
        ambiguous_doc.write_text(
            "\n".join(
                [
                    "# 子任务实施文档",
                    "",
                    "## 1. 文档定位",
                    "",
                    "- 这里已经开始写具体执行内容。",
                    "",
                    "## 2. 实施步骤",
                    "",
                    "### Step 1",
                    "- 修改 apps/api/app/services/match.py。",
                ]
            ),
            encoding="utf-8",
        )

        exit_code, payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )

        state_path = self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        self.assertEqual(exit_code, 1)
        self.assertFalse(state_path.exists())
        self.assertEqual(
            payload["diagnostics"][0]["code"],
            "BOOTSTRAP_IMPL_DOC_STATE_AMBIGUOUS",
        )


if __name__ == "__main__":
    unittest.main()
