import io
import json
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from contextlib import redirect_stdout

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _base_docs() -> dict[str, dict[str, bool]]:
    return {name: {"exists": True, "template_like": False} for name in schema.MODULE_DOC_SLOTS}


def _default_state() -> dict:
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
        "modules": {},
        "subtasks": {},
    }


def _module_entry(module_id: str, readiness: str = "downstream_ready") -> dict:
    confirmed = schema.make_default_confirmed_state("module")
    confirmed["maturity"] = "L4"
    confirmed["readiness"] = readiness
    return {
        "meta": {"path": f"docs/modules/{module_id}-test/"},
        "facts": {
            "upstream_module_ids": [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "docs": _base_docs(),
        },
        "state": {"confirmed": confirmed},
    }


def _requirement_entry(*, module_ids: list[str], task_ids: list[str]) -> dict:
    confirmed = schema.make_default_confirmed_state("requirement")
    return {
        "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
        "facts": {
            "module_ids": module_ids,
            "task_ids": task_ids,
            "asset_slots": {
                "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                "task_index": {"exists": True, "path": "TASK_INDEX.md"},
            },
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": confirmed,
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _subtask_entry(
    subtask_id: str,
    module_id: str,
    readiness: str = "downstream_ready",
    implementation_state: str = "active_working_doc",
) -> dict:
    confirmed = schema.make_default_confirmed_state("subtask")
    confirmed["maturity"] = "L4"
    confirmed["readiness"] = readiness
    confirmed["implementation_doc_state"] = implementation_state
    return {
        "meta": {"module_id": module_id, "path": f"docs/modules/{module_id}/sub_modules/{subtask_id}-test/"},
        "facts": {
            "upstream_module_ids": [module_id],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": True, "template_like": False},
        },
        "state": {"confirmed": confirmed},
    }


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class PreflightOpenWindowTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "preflight"

    def setUp(self) -> None:
        super().setUp()
        self.governance_root = self.temp_root / "docs" / "governance"
        self.governance_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.governance_root / "DOC_STATE.yaml"
        self.bootstrap_state_path = self.governance_root / "DOC_STATE.bootstrap.yaml"
        self.history_path = self.governance_root / "transition_history.jsonl"

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )

    def _write_evaluate_json(self, payload: dict) -> Path:
        path = self.temp_root / "evaluate.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _write_history(self, lines: list[dict]) -> None:
        content = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in lines)
        self.history_path.write_text(content, encoding="utf-8")

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["preflight-open-window", *args])
            payload = json.loads(output.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def test_missing_official_state_fails(self) -> None:
        exit_code, payload = self._run_cli("--state", str(self.state_path))
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["parse_errors"][0]["code"], "PRE_FLIGHT_STATE_NOT_FOUND")

    def test_no_blocker_positive_example(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        exit_code, payload = self._run_cli("--state", str(self.state_path))

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["eligible_count"], 1)
        self.assertEqual(payload["summary"]["blocked_count"], 0)
        self.assertEqual(payload["eligible_entities"][0]["entity_id"], "M01")
        self.assertEqual(payload["eligible_entities"][0]["entity_type"], "module")
        self.assertFalse(payload["review_required_before_open"])

    def test_formal_window_closed_blocks(self) -> None:
        state = _default_state()
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"] = _subtask_entry("ST01_01", "M01")
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        exit_code, payload = self._run_cli("--state", str(self.state_path))

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["blocked_count"], 1)
        self.assertEqual(payload["summary"]["eligible_count"], 1)
        self.assertEqual(payload["blocked_entities"][0]["entity_id"], "ST01_01")
        self.assertEqual(payload["blocked_entities"][0]["entity_type"], "subtask")
        self.assertTrue(payload["eligible_entities"])
        self.assertTrue(
            any(entity["entity_id"] == "M01" and entity["entity_type"] == "module" for entity in payload["eligible_entities"])
        )
        self.assertTrue(
            any(
                item["code"] == "formal_window_closed"
                for item in payload["blocked_entities"][0]["blockers"]
            )
        )

    def test_bootstrap_default_oq_policy_cannot_auto_enable_open(self) -> None:
        state = _default_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "Bootstrap default",
                "status": "open",
                "gate_level": "candidate_gate",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
                "gate_policy_source": schema.OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
            }
        }
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        self._write_state(state)

        exit_code, payload = self._run_cli("--state", str(self.state_path))
        self.assertEqual(payload["evaluation_source"], "live-evaluate")
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["eligible_count"], 0)
        self.assertEqual(payload["summary"]["blocked_count"], 1)
        self.assertEqual(payload["blocked_entities"][0]["entity_id"], "M01")
        self.assertEqual(payload["blocked_entities"][0]["entity_type"], "module")
        self.assertTrue(
            any(
                item["code"] == "bootstrap_default_oq_policy_requires_confirmation"
                for item in payload["blocked_entities"][0]["blockers"]
            )
        )

    def test_review_required_unconfirmed_near_open_and_blocked(self) -> None:
        state = _default_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "Review required by policy",
                "status": "open",
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
            }
        }
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        self._write_state(state)
        exit_code, payload = self._run_cli("--state", str(self.state_path))

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["blocked_count"], 1)
        self.assertEqual(payload["summary"]["eligible_count"], 0)
        self.assertEqual(payload["review_required_before_open"][0]["entity_id"], "M01")
        blocked = payload["blocked_entities"][0]
        self.assertEqual(blocked["proximity"], "near-open")
        self.assertEqual(blocked["entity_type"], "module")
        self.assertTrue(
            any(
                item["code"] == "review_required_unconfirmed"
                for item in blocked["blockers"]
            )
        )

    def test_evaluate_json_priority_over_state(self) -> None:
        state = _default_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "Hard OQ",
                "status": "open",
                "gate_level": "candidate_gate",
                "resolution_policy": "confirmed_only",
                "affects": {"kind": "module", "ids": ["M01"]},
                "gate_policy_source": schema.OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
            }
        }
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        self._write_state(state)

        evaluate_payload = {
            "summary": {},
            "modules": {
                "M01": {
                    "derived": {
                        "candidate_blocker_refs": [],
                        "downstream_blocker_refs": [],
                        "implementation_blocker_refs": [],
                        "oq_review_only_refs": [],
                    }
                }
            },
            "subtasks": {},
            "oqs": {},
        }
        evaluate_path = self._write_evaluate_json(evaluate_payload)

        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--evaluate-json", str(evaluate_path),
        )
        self.assertEqual(payload["evaluation_source"], "json")
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["eligible_count"], 1)
        self.assertEqual(payload["summary"]["blocked_count"], 0)

    def test_missing_history_does_not_block(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        if self.history_path.exists():
            self.history_path.unlink()

        exit_code, payload = self._run_cli("--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["blocked_count"], 0)
        self.assertEqual(payload["summary"]["eligible_count"], 1)
        history_absent_in_missing_requirements = any(
            item["code"] == "history_absent" for item in payload["missing_requirements"]
        )
        history_absent_in_parse_errors = any(
            item.get("code") == "HISTORY_PATH_NOT_FOUND" for item in payload["parse_errors"]
        )
        self.assertTrue(history_absent_in_missing_requirements or history_absent_in_parse_errors)

    def test_history_only_enhances_not_change_eligibility(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        self._write_history(
            [
                {
                    "transition_id": "T-001",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "entity_type": "module",
                    "entity_id": "M01",
                    "result": "rejected",
                    "actor": "alice",
                }
            ]
        )

        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["summary"]["eligible_count"], 1)
        self.assertEqual(payload["summary"]["blocked_count"], 0)
        self.assertEqual(payload["history_signals"]["recent_reject_count"]["module::M01"], 1)
        self.assertEqual(len(payload["history_signals"]["parse_errors"]), 0)
        self.assertTrue(
            any(
                item["code"] == "history_recent_reject"
                for item in payload["blocker_reasons"]
            )
        )

    def test_history_failed_warning_explanation_added_without_classification_change(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        self._write_history(
            [
                {
                    "transition_id": "T-002",
                    "timestamp": "2025-01-02T00:00:00Z",
                    "entity_type": "module",
                    "entity_id": "M01",
                    "result": "failed",
                    "actor": "bob",
                }
            ]
        )

        exit_code, payload = self._run_cli(
            "--state",
            str(self.state_path),
            "--history",
            str(self.history_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["eligible_count"], 1)
        self.assertEqual(payload["summary"]["blocked_count"], 0)
        self.assertEqual(payload["history_signals"]["recent_reject_count"]["module::M01"], 0)
        reasons = {item["code"] for item in payload["blocker_reasons"]}
        self.assertIn("history_recent_failed", reasons)

    def test_preflight_does_not_write_any_state_file(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        self.bootstrap_state_path.write_text("bootstrap-content", encoding="utf-8")
        self._write_history(
            [
                {
                    "transition_id": "T-001",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "entity_type": "module",
                    "entity_id": "M01",
                    "result": "approved",
                    "actor": "alice",
                }
            ]
        )

        before_state = self.state_path.read_bytes()
        before_bootstrap = self.bootstrap_state_path.read_bytes()
        before_history = self.history_path.read_bytes()

        exit_code, payload = self._run_cli(
            "--state",
            str(self.state_path),
            "--evaluate-json",
            str(self._write_evaluate_json({"summary": {}, "modules": {"M01": {"derived": {}}}, "subtasks": {}})),
        )
        self.assertEqual(payload["evaluation_source"], "json")
        self.assertEqual(exit_code, 0)
        self.assertEqual(before_state, self.state_path.read_bytes())
        self.assertEqual(before_bootstrap, self.bootstrap_state_path.read_bytes())
        self.assertEqual(before_history, self.history_path.read_bytes())

    def test_formal_window_open_consumes_task_candidate_bridge(self) -> None:
        state = _default_state()
        state["global_policy"]["formal_window_open"] = True
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M02"] = _module_entry("M02")
        state["modules"]["M09"] = _module_entry("M09")
        state["requirements"] = {
            "RQ01": _requirement_entry(
                module_ids=["M01", "M02", "M09"],
                task_ids=["ST01_01", "ST02_03", "ST09_03"],
            )
        }
        state["modules"]["M02"]["facts"]["docs"]["api"] = {"exists": False, "template_like": True}
        state["modules"]["M02"]["facts"]["docs"]["open_questions"] = {"exists": False, "template_like": True}
        state["subtasks"]["ST09_03"] = _subtask_entry("ST09_03", "M09", "downstream_ready", "active_working_doc")
        state["subtasks"]["ST01_01"] = _subtask_entry("ST01_01", "M01", "downstream_ready", "active_working_doc")
        state["subtasks"]["ST02_03"] = _subtask_entry("ST02_03", "M02", "downstream_ready", "active_working_doc")
        self._write_state(state)

        _write_text(
            self.temp_root,
            "docs/modules/M09/sub_modules/ST09_03-test/SUBTASK_DESIGN.md",
            "# 子任务设计文档\n\n## 3. 子任务目标\n- 进入 preflight 候选。\n\n## 5. 技术方案\n- formal window 已满足。\n",
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md",
            "# 子任务实施文档\n\n## 3. 本轮实施目标\n- 进入 preflight 候选。\n\n## 5. 允许修改范围\n### 5.1 允许修改\n- 文件：`tools/doc_governor/preflight.py`\n\n### 5.2 禁止修改\n- 文件：`docs/governance/DOC_STATE.yaml`\n\n## 7. 测试与验证\n### 7.1 自动化验证\n- 运行：`python -m pytest tests/doc_governor/test_preflight.py -q`\n\n## 8. 完成判定\n- implementation packet 所需字段完整可读。\n",
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01/sub_modules/ST01_01-test/SUBTASK_DESIGN.md",
            "# 子任务设计文档\n\n## 3. 子任务目标\n- 仍保留内容缺口。\n\n## 5. 技术方案\n- 故意不补 tests 与 acceptance。\n",
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
            "# 子任务实施文档\n\n## 3. 本轮实施目标\n- 故意不补 tests 与 acceptance。\n\n## 5. 允许修改范围\n\n### 5.1 允许修改\n- `tools/doc_governor/preflight.py`\n\n### 5.2 禁止修改\n- `docs/governance/DOC_STATE.yaml`\n",
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02/sub_modules/ST02_03-test/SUBTASK_DESIGN.md",
            "# 子任务设计文档\n\n## 3. 子任务目标\n- 保持模块继承 blocker。\n\n## 5. 技术方案\n- task 自身结构完整，但模块层未闭合。\n",
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02/sub_modules/ST02_03-test/SUBTASK_IMPLEMENTATION.md",
            "# 子任务实施文档\n\n## 3. 本轮实施目标\n- 保持模块 blocker。\n\n## 5. 允许修改范围\n### 5.1 允许修改\n- 文件：`tools/doc_governor/preflight.py`\n\n### 5.2 禁止修改\n- 文件：`docs/governance/DOC_STATE.yaml`\n\n## 7. 测试与验证\n### 7.1 自动化验证\n- 运行：`python -m pytest tests/doc_governor/test_preflight.py -q`\n\n## 8. 完成判定\n- implementation packet 所需字段完整可读。\n",
        )

        exit_code, payload = self._run_cli("--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])

        bridge_summary = payload["task_candidate_bridge"]["summary"]
        self.assertEqual(bridge_summary["ready_for_preflight_open_window_count"], 1)
        candidate_ids = [item["task_id"] for item in payload["task_candidate_bridge"]["candidate_tasks"]]
        self.assertEqual(candidate_ids, ["ST09_03"])

        eligible_subtasks = {
            item["entity_id"]: item
            for item in payload["eligible_entities"]
            if item["entity_type"] == "subtask"
        }
        self.assertEqual(list(eligible_subtasks.keys()), ["ST09_03"])
        self.assertEqual(
            eligible_subtasks["ST09_03"]["task_candidate_bridge"]["classification"],
            "ready_for_preflight_open_window",
        )

        blocked_subtasks = {
            item["entity_id"]: item
            for item in payload["blocked_entities"]
            if item["entity_type"] == "subtask"
        }
        self.assertEqual(
            blocked_subtasks["ST01_01"]["task_candidate_bridge"]["dependency_stage"],
            "stay_in_content_layer",
        )
        self.assertEqual(
            blocked_subtasks["ST02_03"]["task_candidate_bridge"]["dependency_stage"],
            "should_not_enter_open_window",
        )
        self.assertTrue(
            any(item["code"] == "task_not_in_open_window_candidate_pool" for item in blocked_subtasks["ST01_01"]["blockers"])
        )
        self.assertTrue(
            any(item["code"] == "task_not_in_open_window_candidate_pool" for item in blocked_subtasks["ST02_03"]["blockers"])
        )


if __name__ == "__main__":
    unittest.main()
