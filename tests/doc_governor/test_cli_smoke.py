import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main


REPO_ROOT = Path(__file__).resolve().parents[2]


def _build_state() -> dict:
    requirement_state = schema.make_default_confirmed_state("requirement")
    module_state = schema.make_default_confirmed_state("module")
    task_state = schema.make_default_confirmed_state("subtask")
    task_state["implementation_doc_state"] = "active_working_doc"
    return {
        "schema_version": schema.SCHEMA_VERSION,
        "global_policy": {
            "auto_open_enabled": False,
            "require_confirmation_for_state_writeback": True,
            "strict_template_gate": True,
            "formal_window_open": True,
            "paths": {
                "modules_root": "docs/modules",
                "open_questions_doc": "OPEN_QUESTIONS.md",
                "task_index_doc": "TASK_INDEX.md",
            },
        },
        "oqs": {},
        "requirements": {
            "RQ01": {
                "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
                "facts": {
                    "module_ids": ["M01"],
                    "task_ids": ["ST01_01"],
                    "asset_slots": {
                        "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                        "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                        "task_index": {"exists": True, "path": "TASK_INDEX.md"},
                    },
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": requirement_state,
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
        "modules": {
            "M01": {
                "meta": {"path": "docs/modules/M01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": {
                        slot: {"exists": True, "template_like": False}
                        for slot in schema.MODULE_DOC_SLOTS
                    },
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": module_state,
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
        "subtasks": {
            "ST01_01": {
                "meta": {
                    "module_id": "M01",
                    "path": "docs/modules/M01-test/sub_modules/ST01_01-test/",
                },
                "facts": {
                    "upstream_module_ids": ["M01"],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": False},
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": task_state,
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
    }


class CliSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-cli-smoke-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)
        self.state_path = self.temp_root / "DOC_STATE.yaml"
        self.state_path.write_text(
            yaml.safe_dump(_build_state(), sort_keys=False),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _run_cli(self, *args: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            try:
                exit_code = main(list(args))
            except SystemExit as exc:
                exit_code = int(exc.code)
        return exit_code, stdout.getvalue()

    def _run_subprocess(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            stdin=subprocess.DEVNULL,
        )

    def test_cli_help_runs(self) -> None:
        exit_code, output = self._run_cli("--help")
        self.assertEqual(exit_code, 0)
        self.assertIn("evaluate-state", output)
        self.assertIn("confirm-transition", output)

    def test_module_entrypoint_help(self) -> None:
        result = self._run_subprocess("-m", "tools.doc_governor.cli", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doc-governor", result.stdout)

    def test_script_entrypoint_help(self) -> None:
        result = self._run_subprocess("tools/doc_governor/cli.py", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doc-governor", result.stdout)

    def test_evaluate_state_supports_entity_type_and_entity_id(self) -> None:
        requirement_code, requirement_output = self._run_cli(
            "evaluate-state",
            "--input",
            str(self.state_path),
            "--entity-type",
            "requirement",
        )
        self.assertEqual(requirement_code, 0)
        requirement_payload = json.loads(requirement_output)
        self.assertEqual(sorted(requirement_payload["requirements"].keys()), ["RQ01"])
        self.assertEqual(requirement_payload["modules"], {})
        self.assertEqual(requirement_payload["subtasks"], {})

        task_code, task_output = self._run_cli(
            "evaluate-state",
            "--input",
            str(self.state_path),
            "--entity-type",
            "task",
            "--entity-id",
            "ST01_01",
        )
        self.assertEqual(task_code, 0)
        task_payload = json.loads(task_output)
        self.assertEqual(sorted(task_payload["subtasks"].keys()), ["ST01_01"])
        self.assertEqual(task_payload["requirements"], {})
        self.assertEqual(task_payload["modules"], {})


if __name__ == "__main__":
    unittest.main()
