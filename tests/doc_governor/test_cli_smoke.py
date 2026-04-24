import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.testing.temp_artifacts import ManagedTempArtifacts


REPO_ROOT = Path(__file__).resolve().parents[2]


def _build_state() -> dict:
    requirement_state = schema.make_default_confirmed_state("requirement")
    module_state = schema.make_default_confirmed_state("module")
    task_state = schema.make_default_confirmed_state("subtask")
    task_state["maturity"] = "L4"
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


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_task_docs(
    root: Path,
    *,
    english_only: bool = False,
    include_allowed_paths: bool = True,
) -> None:
    task_root = "docs/modules/M01-test/sub_modules/ST01_01-test"
    if english_only:
        design_text = "# API Overview\n\nUse the API to describe the task.\n"
        implementation_text = (
            "# Implementation Packet\n\n"
            "## 3. Goal\n\n"
            "- Build the task.\n\n"
            "## 5. Allowed Changes\n\n"
            "### 5.1 Allowed\n"
            "- Files: `apps/api/app/main.py`\n\n"
            "### 5.2 Forbidden\n"
            "- Files: `docs/governance/DOC_STATE.yaml`\n\n"
            "## 7. Tests\n\n"
            "### 7.1 Automated\n"
            "- Run: `python -m pytest tests/doc_governor/test_cli_smoke.py -q`\n\n"
            "## 8. Acceptance\n\n"
            "- Done: behavior works.\n"
        )
    else:
        allowed_block = (
            "- 鍏佽淇敼鐨勬枃浠讹細`apps/api/app/main.py`\n"
            if include_allowed_paths
            else "- 鍏佽淇敼鐨勬枃浠讹細\n"
        )
        design_text = (
            "# 瀛愪换鍔¤璁℃枃妗n\n"
            "## 3. 瀛愪换鍔＄洰鏍嘰n\n"
            "- 鏈瓙浠诲姟瑕佽В鍐崇殑闂锛氳ˉ榻?task-centered packet銆俓n"
        )
        implementation_text = (
            "# 瀛愪换鍔″疄鏂芥枃妗n\n"
            "## 3. 鏈疆瀹炴柦鐩爣\n\n"
            "- 鏈疆鍑嗗瀹屾垚浠€涔堬細鐢熸垚 implementation packet銆俓n\n"
            "## 5. 鍏佽淇敼鑼冨洿\n\n"
            "### 5.1 鍏佽淇敼\n"
            f"{allowed_block}\n"
            "### 5.2 绂佹淇敼\n"
            "- 鏈疆涓嶅簲淇敼鐨勭洰褰?/ 鏂囦欢锛歚docs/governance/DOC_STATE.yaml`\n\n"
            "## 7. 娴嬭瘯涓庨獙璇乗n\n"
            "### 7.1 鑷姩鍖栭獙璇乗n"
            "- 璁″垝杩愯鐨勬祴璇曪細`python -m pytest tests/doc_governor/test_cli_smoke.py -q`\n\n"
            "## 8. 瀹屾垚鍒ゅ畾\n\n"
            "- 婊¤冻鍝簺鏉′欢鍙涓烘湰杞畬鎴愶細packet 鎴愬姛鐢熸垚銆俓n"
        )
    _write_text(root, f"{task_root}/SUBTASK_DESIGN.md", design_text)
    _write_text(root, f"{task_root}/SUBTASK_IMPLEMENTATION.md", implementation_text)


def _write_packet_ready_task_docs(root: Path) -> None:
    task_root = "docs/modules/M01-test/sub_modules/ST01_01-test"
    design_text = (
        "# 子任务设计\n\n"
        "## 目标\n"
        "- 这是一个用于 CLI smoke 的受控样本。\n"
        "- 设计与实施文档均保持中文主结构。\n"
    )
    implementation_text = (
        "# 子任务实施文档\n\n"
        "## 3. 本轮实施目标\n"
        "- 产出一个可用于 implementation packet 的最小样本。\n\n"
        "## 5. 允许修改范围\n"
        "### 5.1 允许修改\n"
        "- 文件：`apps/api/app/main.py`\n\n"
        "### 5.2 禁止修改\n"
        "- 文件：`docs/governance/DOC_STATE.yaml`\n\n"
        "## 7. 测试与验证\n"
        "### 7.1 自动化验证\n"
        "- 运行：`python -m pytest tests/doc_governor/test_cli_smoke.py -q`\n\n"
        "## 8. 完成判定\n"
        "- implementation packet 所需字段完整可读。\n"
    )
    _write_text(root, f"{task_root}/SUBTASK_DESIGN.md", design_text)
    _write_text(root, f"{task_root}/SUBTASK_IMPLEMENTATION.md", implementation_text)


class CliSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_artifacts = ManagedTempArtifacts(
            test_id=self.id(),
            watch_roots=[Path(__file__).parent],
        )
        self.temp_root = self.temp_artifacts.make_temp_dir("cli-smoke")
        self.state_path = self.temp_root / "DOC_STATE.yaml"
        self.state_path.write_text(
            yaml.safe_dump(_build_state(), sort_keys=False),
            encoding="utf-8",
        )
        _write_task_docs(self.temp_root)

    def tearDown(self) -> None:
        self.temp_artifacts.cleanup()

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

    def test_generate_implementation_packet_writes_json_and_markdown(self) -> None:
        _write_packet_ready_task_docs(self.temp_root)
        output_dir = self.temp_root / "custom-packets"
        exit_code, output = self._run_cli(
            "generate-implementation-packet",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--output-dir",
            str(output_dir),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["task_id"], "ST01_01")
        self.assertEqual(payload["summary"]["acceptance_criteria_count"], 1)
        self.assertTrue((output_dir / "ST01_01.implementation.packet.json").exists())
        self.assertTrue((output_dir / "ST01_01.implementation.packet.md").exists())

    def test_generate_implementation_packet_rejects_and_does_not_write_files(self) -> None:
        _write_task_docs(self.temp_root, include_allowed_paths=False)
        output_dir = self.temp_root / "blocked-packets"
        exit_code, output = self._run_cli(
            "generate-implementation-packet",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--output-dir",
            str(output_dir),
        )
        self.assertEqual(exit_code, 1)
        payload = json.loads(output)
        self.assertFalse(payload["ok"])
        self.assertFalse(output_dir.exists())

    def test_plan_task_adaptation_command_supports_json_markdown_and_entity_filter(self) -> None:
        output_dir = self.temp_root / "adaptation"
        json_path = output_dir / "plan.json"
        exit_code, output = self._run_cli(
            "plan-task-adaptation",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "plan.md"
        exit_code, markdown_output = self._run_cli(
            "plan-task-adaptation",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务适配规划", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())

    def test_apply_task_skeleton_seed_supports_dry_run_and_apply(self) -> None:
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["subtasks"]["ST01_01"]["facts"]["design_doc"] = {"exists": False, "template_like": True}
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"] = {"exists": False, "template_like": True}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "missing"
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        task_root = self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test"
        for name in ("SUBTASK_DESIGN.md", "SUBTASK_IMPLEMENTATION.md"):
            path = task_root / name
            if path.exists():
                path.unlink()

        output_plan = self.temp_root / "task-skeleton-seed.json"
        exit_code, output = self._run_cli(
            "apply-task-skeleton-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["summary"]["planned_file_count"], 2)
        self.assertTrue(output_plan.exists())

        exit_code, output = self._run_cli(
            "apply-task-skeleton-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "apply")
        self.assertEqual(payload["summary"]["written_file_count"], 2)
        self.assertTrue((task_root / "SUBTASK_DESIGN.md").exists())
        self.assertTrue((task_root / "SUBTASK_IMPLEMENTATION.md").exists())

    def test_apply_task_doc_state_sync_supports_dry_run_and_apply(self) -> None:
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["subtasks"]["ST01_01"]["facts"]["design_doc"] = {"exists": False, "template_like": True}
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"] = {"exists": False, "template_like": True}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "missing"
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        task_root = self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test"
        for name in ("SUBTASK_DESIGN.md", "SUBTASK_IMPLEMENTATION.md"):
            path = task_root / name
            if path.exists():
                path.unlink()

        exit_code, output = self._run_cli(
            "apply-task-skeleton-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
        )
        self.assertEqual(exit_code, 0)
        seed_payload = json.loads(output)
        self.assertEqual(seed_payload["summary"]["written_file_count"], 2)

        output_plan = self.temp_root / "task-doc-state-sync.json"
        exit_code, output = self._run_cli(
            "apply-task-doc-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["summary"]["planned_slot_count"], 2)
        self.assertTrue(output_plan.exists())

        exit_code, output = self._run_cli(
            "apply-task-doc-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "apply")
        self.assertEqual(payload["summary"]["written_slot_count"], 2)

        synced_state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        synced_task = synced_state["subtasks"]["ST01_01"]
        self.assertEqual(synced_task["facts"]["design_doc"], {"exists": True, "template_like": False})
        self.assertEqual(
            synced_task["facts"]["implementation_doc"],
            {"exists": True, "template_like": False},
        )
        self.assertEqual(
            synced_task["state"]["confirmed"]["implementation_doc_state"],
            "missing",
        )

    def test_apply_task_implementation_state_sync_supports_dry_run_and_apply(self) -> None:
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "missing"
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        output_plan = self.temp_root / "task-implementation-state-sync.json"
        evaluate_payload_path = self.temp_root / "evaluate-task-implementation-state-sync.json"
        evaluate_payload = {
            "subtasks": {
                "ST01_01": {
                    "derived": {
                        "requirement_ids": ["RQ01"],
                        "implementation_blocker_refs": [],
                    }
                }
            }
        }
        evaluate_payload_path.write_text(
            json.dumps(evaluate_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        exit_code, output = self._run_cli(
            "apply-task-implementation-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--evaluate-json",
            str(evaluate_payload_path),
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["summary"]["planned_task_count"], 1)
        self.assertTrue(output_plan.exists())

        exit_code, output = self._run_cli(
            "apply-task-implementation-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--evaluate-json",
            str(evaluate_payload_path),
            "--apply",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "apply")
        self.assertEqual(payload["summary"]["written_task_count"], 1)
        synced_state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            synced_state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"],
            "active_working_doc",
        )


    def test_suggest_requirement_links_supports_json_markdown_and_entity_filter(self) -> None:
        output_dir = self.temp_root / "requirement-links"
        json_path = output_dir / "suggestions.json"
        exit_code, output = self._run_cli(
            "suggest-requirement-links",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "suggestions.md"
        exit_code, markdown_output = self._run_cli(
            "suggest-requirement-links",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("requirement", markdown_output.lower())
        self.assertTrue(md_path.exists())

    def test_plan_task_remediation_supports_json_markdown_and_entity_filter(self) -> None:
        output_dir = self.temp_root / "remediation"
        json_path = output_dir / "plan.json"
        exit_code, output = self._run_cli(
            "plan-task-remediation",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "plan.md"
        exit_code, markdown_output = self._run_cli(
            "plan-task-remediation",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务文档整改规划", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())


    def test_plan_task_readiness_supports_json_markdown_and_entity_filter(self) -> None:
        output_dir = self.temp_root / "readiness"
        json_path = output_dir / "plan.json"
        exit_code, output = self._run_cli(
            "plan-task-readiness",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "plan.md"
        exit_code, markdown_output = self._run_cli(
            "plan-task-readiness",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务 readiness 规划", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())


    def test_preview_task_readiness_fix_supports_json_markdown_and_entity_filter(self) -> None:
        output_dir = self.temp_root / "readiness-preview"
        json_path = output_dir / "preview.json"
        exit_code, output = self._run_cli(
            "preview-task-readiness-fix",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "preview.md"
        exit_code, markdown_output = self._run_cli(
            "preview-task-readiness-fix",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务 readiness 修复预览", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())

    def test_preview_task_patches_supports_json_markdown_and_entity_filter(self) -> None:
        output_dir = self.temp_root / "patch-preview"
        json_path = output_dir / "preview.json"
        exit_code, output = self._run_cli(
            "preview-task-patches",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "preview.md"
        exit_code, markdown_output = self._run_cli(
            "preview-task-patches",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务 patch 预览", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())

    def test_preview_task_state_writeback_supports_json_markdown_and_entity_filter(self) -> None:
        _write_packet_ready_task_docs(self.temp_root)
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "missing"
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        output_dir = self.temp_root / "state-writeback-preview"
        json_path = output_dir / "preview.json"
        exit_code, output = self._run_cli(
            "preview-task-state-writeback",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertEqual(payload["summary"]["activation_candidate_count"], 1)
        self.assertEqual(payload["tasks"][0]["task_id"], "ST01_01")
        self.assertTrue(payload["tasks"][0]["eligible_for_writeback"])
        self.assertTrue(json_path.exists())

        md_path = output_dir / "preview.md"
        exit_code, markdown_output = self._run_cli(
            "preview-task-state-writeback",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务 state 写回预览", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())

    def test_apply_task_state_writeback_supports_dry_run_and_apply_on_controlled_sample(self) -> None:
        _write_packet_ready_task_docs(self.temp_root)
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "missing"
        official_state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        official_state_path.parent.mkdir(parents=True, exist_ok=True)
        official_state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )
        history_path = official_state_path.parent / "transition_history.jsonl"

        exit_code, output = self._run_cli(
            "apply-task-state-writeback",
            "--input",
            str(official_state_path),
            "--entity-id",
            "ST01_01",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["summary"]["eligible_task_count"], 1)
        self.assertEqual(payload["tasks"][0]["task_id"], "ST01_01")
        self.assertTrue(payload["tasks"][0]["apply_allowed"])
        self.assertFalse(history_path.exists())

        exit_code, output = self._run_cli(
            "apply-task-state-writeback",
            "--input",
            str(official_state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
            "--actor",
            "alice",
            "--reason",
            "activate implementation doc state",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "apply")
        self.assertEqual(payload["summary"]["applied_task_count"], 1)
        self.assertEqual(payload["tasks"][0]["task_id"], "ST01_01")

        updated_state = yaml.safe_load(official_state_path.read_text(encoding="utf-8"))
        confirmed = updated_state["subtasks"]["ST01_01"]["state"]["confirmed"]
        self.assertEqual(confirmed["implementation_doc_state"], "active_working_doc")
        self.assertTrue(history_path.exists())

    def test_plan_task_window_candidates_supports_json_markdown_and_entity_filter(self) -> None:
        _write_packet_ready_task_docs(self.temp_root)
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "missing"
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        output_dir = self.temp_root / "task-window-candidates"
        json_path = output_dir / "bridge.json"
        exit_code, output = self._run_cli(
            "plan-task-window-candidates",
            "--input",
            str(self.state_path),
            "--format",
            "json",
            "--entity-id",
            "ST01_01",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertEqual(payload["summary"]["candidate_task_count"], 1)
        self.assertEqual(payload["summary"]["candidate_tasks_after_state_activation_count"], 1)
        self.assertEqual(payload["candidate_tasks_after_state_activation"][0]["task_id"], "ST01_01")
        self.assertTrue(json_path.exists())

        md_path = output_dir / "bridge.md"
        exit_code, markdown_output = self._run_cli(
            "plan-task-window-candidates",
            "--input",
            str(self.state_path),
            "--format",
            "markdown",
            "--entity-id",
            "ST01_01",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务开窗候选规划", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())

    def test_apply_task_readiness_fix_supports_dry_run_plan(self) -> None:
        output_plan = self.temp_root / "apply-plan.json"
        exit_code, output = self._run_cli(
            "apply-task-readiness-fix",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertTrue(output_plan.exists())

    def test_summarize_task_apply_result_supports_json_markdown_and_multi_task(self) -> None:
        execute_code, _ = self._run_cli(
            "apply-task-readiness-fix",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
        )
        self.assertEqual(execute_code, 0)

        output_dir = self.temp_root / "apply-summary"
        json_path = output_dir / "summary.json"
        exit_code, output = self._run_cli(
            "summarize-task-apply-result",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--format",
            "json",
            "--output",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertTrue(json_path.exists())

        md_path = output_dir / "summary.md"
        exit_code, markdown_output = self._run_cli(
            "summarize-task-apply-result",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--entity-id",
            "ST01_01",
            "--format",
            "markdown",
            "--output",
            str(md_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("# 任务 apply 结果总结", markdown_output)
        self.assertIn("ST01_01", markdown_output)
        self.assertTrue(md_path.exists())


    def test_preview_task_readiness_state_sync_supports_dry_run_and_apply(self) -> None:
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "blocked"
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "active_working_doc"
        official_state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        official_state_path.parent.mkdir(parents=True, exist_ok=True)
        official_state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        evaluate_payload_path = self.temp_root / "evaluate-readiness-state-sync.json"
        evaluate_payload_path.write_text(
            json.dumps(
                {
                    "subtasks": {
                        "ST01_01": {
                            "derived": {
                                "requirement_ids": ["RQ01"],
                                "blocker_refs": ["policy:formal_window_closed"],
                            }
                        }
                    },
                    "requirements": {},
                    "modules": {},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        exit_code, output = self._run_cli(
            "preview-task-readiness-state-sync",
            "--input",
            str(official_state_path),
            "--evaluate-json",
            str(evaluate_payload_path),
            "--entity-id",
            "ST01_01",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["summary"]["readiness_apply_candidate_count"], 1)

        exit_code, output = self._run_cli(
            "apply-task-readiness-state-sync",
            "--input",
            str(official_state_path),
            "--evaluate-json",
            str(evaluate_payload_path),
            "--entity-id",
            "ST01_01",
            "--apply",
            "--actor",
            "alice",
            "--reason",
            "advance task readiness",
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["mode"], "apply")
        self.assertEqual(payload["summary"]["applied_task_count"], 1)

        updated = yaml.safe_load(official_state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            updated["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"],
            "downstream_ready",
        )

if __name__ == "__main__":
    unittest.main()

