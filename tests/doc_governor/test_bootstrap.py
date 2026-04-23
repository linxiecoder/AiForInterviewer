import io
import json
import textwrap
import subprocess
import shutil
from contextlib import redirect_stdout
from pathlib import Path
import unittest
import sys

from tools.testing.temp_artifacts import ManagedTempArtifacts


FIXTURES = Path(__file__).parent / "fixtures"


class BootstrapStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_artifacts = ManagedTempArtifacts(
            test_id=self.id(),
            watch_roots=[Path(__file__).parent],
        )
        self.temp_root = self.temp_artifacts.make_temp_dir("bootstrap")
        self.repo_root = self.temp_root / "repo"
        shutil.copytree(FIXTURES / "repo" / "prose_contamination", self.repo_root)
        for cleanup_file in [
            self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml",
            self.repo_root / "docs" / "governance" / "BOOTSTRAP_REPORT.md",
        ]:
            cleanup_file.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.temp_artifacts.cleanup()

    def _write_open_questions(self, text: str) -> None:
        (self.repo_root / "OPEN_QUESTIONS.md").write_text(
            text.strip() + "\n",
            encoding="utf-8",
        )

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

    def test_bootstrap_imports_explicit_oq_policy_fields(self) -> None:
        self._write_open_questions(
            textwrap.dedent(
                """
                # OQ Policies

                | OQ ID | 问题 | 状态 | 关联模块 | 当期建议 | 需要回写文档 | gate_level | resolution_policy |
                | --- | --- | --- | --- | --- | --- | --- | --- |
                | OQ-101 | OQ with explicit gate | open | M04 | 建议保留 | `REQ-001` | candidate_gate | confirmed_only |
                | OQ-102 | OQ for module+subtask | resolved | M04, ST04_01 | 建议评审 | `REQ-002` | readiness_gate | manual_override_only |
                """
            ),
            )
        exit_code, _payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )
        self.assertEqual(exit_code, 0)

        import yaml

        state_path = self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["oqs"]["OQ-101"]["gate_level"], "candidate_gate")
        self.assertEqual(
            state["oqs"]["OQ-101"]["resolution_policy"],
            "confirmed_only",
        )
        self.assertEqual(state["oqs"]["OQ-102"]["gate_level"], "readiness_gate")
        self.assertEqual(
            state["oqs"]["OQ-102"]["resolution_policy"],
            "manual_override_only",
        )
        self.assertEqual(state["oqs"]["OQ-101"]["status"], "open")
        self.assertIn("modules", state["oqs"]["OQ-101"]["affects"])

    def test_bootstrap_defaults_missing_oq_policy_fields_with_single_aggregated_warning(self) -> None:
        self._write_open_questions(
            textwrap.dedent(
                """
                # OQ Policies

                | OQ ID | 问题 | 状态 | 关联模块 | 当期建议 | 需要回写文档 |
                | --- | --- | --- | --- | --- | --- |
                | OQ-201 | Missing fields 1 | open | M04 | 说明 | `REQ-001` |
                | OQ-202 | Missing fields 2 | open | ST04_01 | 说明 | `REQ-002` |
                """
            )
        )
        exit_code, payload = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(self.repo_root),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["ok"], True)

        import yaml

        state = yaml.safe_load(
            (self.repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml").read_text(
                encoding="utf-8",
            )
        )
        self.assertIn("BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED", [item["code"] for item in payload["diagnostics"]])
        self.assertEqual(
            1,
            len(
                [
                    item
                    for item in payload["diagnostics"]
                    if item["code"] == "BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED"
                ]
            ),
        )

        default_item = [
            item for item in payload["diagnostics"] if item["code"] == "BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED"
        ][0]
        self.assertEqual(default_item["evidence"][0]["value"]["count"], 2)
        self.assertIn("OQ-201", default_item["evidence"][0]["value"]["oq_ids"])
        self.assertIn("OQ-202", default_item["evidence"][0]["value"]["oq_ids"])

        self.assertEqual(state["oqs"]["OQ-201"]["gate_level"], "observe_only")
        self.assertEqual(state["oqs"]["OQ-201"]["resolution_policy"], "proposed_default_ok")
        self.assertEqual(state["oqs"]["OQ-202"]["gate_level"], "observe_only")
        self.assertEqual(state["oqs"]["OQ-202"]["resolution_policy"], "proposed_default_ok")

        report_text = (self.repo_root / "docs" / "governance" / "BOOTSTRAP_REPORT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("OQ policy defaults applied:", report_text)
        self.assertIn("count=2", report_text)
        self.assertIn("sample_oq_ids=['OQ-201', 'OQ-202']", report_text)

        # 聚合告警不应出现 per-OQ 细分告警
        oq_warnings = [item for item in payload["diagnostics"] if "OQ-" in item.get("entity_id", "")]
        self.assertFalse(any(item["code"] == "SCAN_OPEN_QUESTIONS_ROW_PARSE_FAILED" for item in oq_warnings))

    def test_bootstrap_state_script_entrypoint_works(self) -> None:
        try:
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
        except OSError as exc:  # pragma: no cover - environment-specific CI handles
            self.skipTest(str(exc))

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
