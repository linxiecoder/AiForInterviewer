import io
import json
import shutil
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.testing.temp_artifacts import ManagedTempArtifacts


FIXTURES_REPO = Path(__file__).parent / "fixtures" / "repo" / "prose_contamination"


def _base_state() -> dict:
    subtask_state = schema.make_default_confirmed_state("subtask")
    subtask_state["implementation_doc_state"] = "active_working_doc"
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
        "requirements": {},
        "modules": {},
        "subtasks": {},
    }


def _requirement_entry(
    requirement_id: str,
    *,
    module_ids: list[str] | None = None,
    task_ids: list[str] | None = None,
) -> dict:
    compliance = schema.make_default_compliance_state()
    compliance["naming_ok"] = True
    compliance["path_ok"] = True
    compliance["relations_ok"] = True
    compliance["language_ok"] = True
    return {
        "meta": {
            "path": ".",
            "scope_kind": "root_requirement_cluster",
        },
        "facts": {
            "module_ids": module_ids or [],
            "task_ids": task_ids or [],
            "asset_slots": {
                "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                "task_index": {"exists": True, "path": "TASK_INDEX.md"},
            },
            "compliance": compliance,
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("requirement"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _module_entry(module_id: str) -> dict:
    module_docs = {
        slot: {"exists": True, "template_like": False} for slot in schema.MODULE_DOC_SLOTS
    }
    return {
        "meta": {"path": f"docs/modules/{module_id}-name/"},
        "facts": {
            "upstream_module_ids": [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "docs": module_docs,
        },
        "state": {"confirmed": schema.make_default_confirmed_state("module")},
    }


def _subtask_entry(subtask_id: str, module_id: str) -> dict:
    return {
        "meta": {"module_id": module_id, "path": f"docs/modules/{module_id}/sub_modules/{subtask_id}-name/"},
        "facts": {
            "upstream_module_ids": [module_id],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": True, "template_like": False},
        },
        "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
    }


def _subtask_implementation_missing_entry(subtask_id: str, module_id: str) -> dict:
    entry = _subtask_entry(subtask_id, module_id)
    entry["facts"]["implementation_doc"] = {"exists": False, "template_like": False}
    return entry


def _write_state(state: dict, root: Path) -> Path:
    path = root / "DOC_STATE.bootstrap.yaml"
    path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    return path


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_design_doc(*, goal: str = "补齐当前子任务的设计目标。") -> str:
    return f"""# 子任务设计文档

## 3. 子任务目标

- 本子任务要解决的问题：{goal}
"""


def _build_implementation_doc(
    *,
    goal: str = "补齐当前子任务的最小实现。",
    allowed_paths: list[str] | None = None,
    forbidden_paths: list[str] | None = None,
    required_tests: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
) -> str:
    allowed_paths = ["apps/api/app/main.py"] if allowed_paths is None else allowed_paths
    forbidden_paths = (
        ["docs/governance/DOC_STATE.yaml"] if forbidden_paths is None else forbidden_paths
    )
    required_tests = (
        ["python -m pytest tests/doc_governor/test_evaluate.py -q"]
        if required_tests is None
        else required_tests
    )
    acceptance_criteria = (
        ["目标行为已实现并通过最小验证。"]
        if acceptance_criteria is None
        else acceptance_criteria
    )

    def _render_items(title: str, items: list[str]) -> str:
        if not items:
            return f"- {title}：\n"
        return "".join(f"- {title}：`{item}`\n" for item in items)

    return (
        "# 子任务实施文档\n\n"
        "## 3. 本轮实施目标\n\n"
        f"- 本轮准备完成什么：{goal}\n\n"
        "## 5. 允许修改范围\n\n"
        "### 5.1 允许修改\n"
        f"{_render_items('允许修改的文件', allowed_paths)}\n"
        "### 5.2 禁止修改\n"
        f"{_render_items('本轮不应修改的目录 / 文件', forbidden_paths)}\n"
        "## 7. 测试与验证\n\n"
        "### 7.1 自动化验证\n"
        f"{_render_items('计划运行的测试', required_tests)}\n"
        "## 8. 完成判定\n\n"
        f"{_render_items('满足哪些条件可视为本轮完成', acceptance_criteria)}"
    )


def _write_subtask_docs(
    root: Path,
    state: dict,
    subtask_id: str,
    *,
    design_content: str | None = None,
    implementation_content: str | None = None,
) -> None:
    subtask = state["subtasks"][subtask_id]
    base_path = Path(str(subtask["meta"]["path"]))
    design_path = (base_path / "SUBTASK_DESIGN.md").as_posix()
    implementation_path = (base_path / "SUBTASK_IMPLEMENTATION.md").as_posix()
    _write_text(root, design_path, design_content or _build_design_doc())
    _write_text(
        root,
        implementation_path,
        implementation_content or _build_implementation_doc(),
    )


class EvaluateStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_artifacts = ManagedTempArtifacts(
            test_id=self.id(),
            watch_roots=[Path(__file__).parent],
        )
        self.temp_root = self.temp_artifacts.make_temp_dir("evaluate")

    def tearDown(self) -> None:
        self.temp_artifacts.cleanup()

    def run_cli(self, *args: str) -> tuple[int, dict]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(list(args))
        payload = json.loads(stdout.getvalue())
        return exit_code, payload

    def test_gate_level_and_resolution_policy_matrix(self) -> None:
        state = _base_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "observe-review",
                "status": "open",
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
            },
            "OQ-02": {
                "title": "candidate-review-1",
                "status": "proposed-default",
                "gate_level": "candidate_gate",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
            },
            "OQ-03": {
                "title": "candidate-review-2",
                "status": "open",
                "gate_level": "candidate_gate",
                "resolution_policy": "confirmed_only",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
            },
            "OQ-04": {
                "title": "readiness-block",
                "status": "open",
                "gate_level": "readiness_gate",
                "resolution_policy": "manual_override_only",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
            },
        }
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        oqs = payload["oqs"]
        self.assertEqual(oqs["OQ-01"]["derived_enforcement"], "review_only")
        self.assertEqual(oqs["OQ-02"]["derived_enforcement"], "review_only")
        self.assertEqual(oqs["OQ-03"]["derived_enforcement"], "candidate_blocker")
        self.assertEqual(oqs["OQ-04"]["derived_enforcement"], "readiness_blocker")
        self.assertEqual(
            payload["summary"]["oq_gate_counts"]["observe_only.review_only"], 1
        )
        self.assertEqual(payload["summary"]["oq_gate_counts"]["candidate_gate.review_only"], 1)
        self.assertEqual(payload["summary"]["oq_gate_counts"]["candidate_gate.candidate_blocker"], 1)
        self.assertEqual(payload["summary"]["oq_gate_counts"]["readiness_gate.readiness_blocker"], 1)

    def test_requirement_gate_outputs_pass_result_when_assets_and_compliance_clear(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01"],
                task_ids=["ST01_01"],
            )
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        requirement_derived = payload["requirements"]["RQ01"]["derived"]
        self.assertEqual(requirement_derived["current_gate"], "module_decomposition_ready")
        self.assertEqual(requirement_derived["gate_result"], "pass")
        self.assertEqual(requirement_derived["blocker_refs"], [])
        self.assertEqual(requirement_derived["module_ids"], ["M01"])
        self.assertEqual(requirement_derived["task_ids"], ["ST01_01"])
        self.assertTrue(requirement_derived["review_required"])
        self.assertTrue(requirement_derived["ready_for_next_step"])
        self.assertFalse(requirement_derived["implementation_ready"])

    def test_requirement_gate_blocks_missing_asset_and_language_violation(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01"],
                task_ids=["ST01_01"],
            )
        }
        requirement = state["requirements"]["RQ01"]
        requirement["facts"]["asset_slots"]["plan_latest"]["exists"] = False
        requirement["facts"]["compliance"]["language_ok"] = False
        requirement["facts"]["compliance"]["violations"] = [
            "language_non_compliant_missing_zh_cn",
        ]
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        requirement_derived = payload["requirements"]["RQ01"]["derived"]
        self.assertEqual(requirement_derived["gate_result"], "blocked")
        self.assertFalse(requirement_derived["ready_for_next_step"])
        self.assertIn("policy:asset_missing_plan_latest", requirement_derived["blocker_refs"])
        self.assertIn(
            "policy:language_non_compliant_missing_zh_cn",
            requirement_derived["blocker_refs"],
        )

    def test_module_gate_propagates_requirement_blockers(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"])
        }
        state["requirements"]["RQ01"]["facts"]["asset_slots"]["module_index"]["exists"] = False
        state["modules"] = {"M01": _module_entry("M01")}
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        module_derived = payload["modules"]["M01"]["derived"]
        self.assertEqual(module_derived["current_gate"], "task_design_ready")
        self.assertEqual(module_derived["gate_result"], "blocked")
        self.assertIn("policy:asset_missing_module_index", module_derived["blocker_refs"])
        self.assertFalse(module_derived["ready_for_next_step"])

    def test_task_gate_sets_implementation_ready_only_when_all_conditions_pass(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01"],
                task_ids=["ST01_01", "ST01_02"],
            )
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", "M01"),
            "ST01_02": _subtask_entry("ST01_02", "M01"),
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        state["subtasks"]["ST01_02"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        _write_subtask_docs(self.temp_root, state, "ST01_01")
        _write_subtask_docs(self.temp_root, state, "ST01_02")
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        task_ready = payload["subtasks"]["ST01_01"]["derived"]
        task_blocked = payload["subtasks"]["ST01_02"]["derived"]
        self.assertEqual(task_ready["current_gate"], "implementation_ready")
        self.assertEqual(task_ready["gate_result"], "pass")
        self.assertEqual(task_ready["blocker_refs"], [])
        self.assertTrue(task_ready["ready_for_next_step"])
        self.assertTrue(task_ready["implementation_ready"])
        self.assertEqual(payload["modules"]["M01"]["derived"]["requirement_ids"], ["RQ01"])
        self.assertEqual(task_ready["requirement_ids"], ["RQ01"])
        self.assertEqual(task_ready["implementation_packet_inputs"]["requirement_id"], "RQ01")
        self.assertEqual(
            task_ready["implementation_packet_inputs"]["allowed_modify_paths"],
            ["apps/api/app/main.py"],
        )
        self.assertEqual(task_blocked["gate_result"], "blocked")
        self.assertFalse(task_blocked["implementation_ready"])

    def test_review_required_truth_table(self) -> None:
        state = _base_state()
        state["modules"] = {
            "M01": _module_entry("M01"),
            "M02": _module_entry("M02"),
        }
        state["subtasks"] = {
            "ST01_01": _subtask_implementation_missing_entry("ST01_01", "M01")
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "inactive_template"
        state["oqs"] = {
            "OQ-01": {
                "title": "observe-review",
                "status": "open",
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
            }
        }
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        state["modules"]["M02"]["facts"]["related_oq_ids"] = []
        state["subtasks"]["ST01_01"]["facts"]["related_oq_ids"] = ["OQ-01"]

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        modules = payload["modules"]
        subtasks = payload["subtasks"]

        self.assertEqual(modules["M01"]["derived"]["review_reasons"], ["downstream_ready_no_hard_blocker", "oq_review_only"])
        self.assertTrue(modules["M01"]["derived"]["assessed_downstream_ready"])
        self.assertEqual(
            modules["M02"]["derived"]["review_reasons"],
            ["downstream_ready_no_hard_blocker"],
        )

        self.assertEqual(
            subtasks["ST01_01"]["derived"]["review_reasons"],
            ["implementation_doc_activation_recommended", "oq_review_only"],
        )
        self.assertTrue(subtasks["ST01_01"]["derived"]["implementation_doc_activation_recommended"])

    def test_legacy_lock_adds_blockers(self) -> None:
        state = _base_state()
        state["modules"] = {
            "M01": _module_entry("M01"),
        }
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["modules"]["M01"]["facts"]["legacy_locked"] = True
        state["subtasks"]["ST01_01"]["facts"]["legacy_locked"] = True
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))

        module_blockers = payload["modules"]["M01"]["derived"]["downstream_blockers"]
        subtask_blockers = payload["subtasks"]["ST01_01"]["derived"]["downstream_blockers"]
        self.assertTrue(any(item["reason_code"] == "legacy_locked" for item in module_blockers))
        self.assertTrue(any(item["reason_code"] == "legacy_locked" for item in subtask_blockers))

    def test_required_doc_and_template_like_blockers(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["modules"]["M01"]["facts"]["docs"]["requirements"]["exists"] = False

        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["facts"]["design_doc"]["template_like"] = True

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))

        module_blockers = payload["modules"]["M01"]["derived"]["downstream_blockers"]
        subtask_blockers = payload["subtasks"]["ST01_01"]["derived"]["downstream_blockers"]
        self.assertTrue(any(item["reason_code"] == "missing_required_doc_slot" for item in module_blockers))
        self.assertTrue(
            any(
                item["reason_code"] == "template_like_required_doc_slot"
                for item in subtask_blockers
            )
        )

    def test_upstream_module_blocking_propagates(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01"), "M02": _module_entry("M02")}
        state["modules"]["M01"]["facts"]["docs"]["schema"]["exists"] = False
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M02")}
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = ["M01"]

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        blockers = payload["subtasks"]["ST01_01"]["derived"]["downstream_blockers"]
        self.assertTrue(any(item["reason_code"] == "upstream_module_not_ready" for item in blockers))

    def test_implementation_related_blockers(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        _write_subtask_docs(self.temp_root, state, "ST01_01")
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "inactive_template"
        state_path = _write_state(state, self.temp_root)

        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        blockers = payload["subtasks"]["ST01_01"]["derived"]["implementation_blockers"]
        self.assertTrue(
            any(item["reason_code"] == "implementation_doc_not_active" for item in blockers)
        )

        state["global_policy"]["formal_window_open"] = False
        state_path = _write_state(state, self.temp_root)
        _, payload_closed = self.run_cli("evaluate-state", "--input", str(state_path))
        blockers_closed = payload_closed["subtasks"]["ST01_01"]["derived"]["implementation_blockers"]
        self.assertTrue(
            any(item["reason_code"] == "formal_window_closed" for item in blockers_closed)
        )

    def test_task_gate_blocks_when_requirement_resolution_is_not_unique(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"], task_ids=["ST01_01"]),
            "RQ02": _requirement_entry("RQ02", module_ids=["M01"], task_ids=["ST01_01"]),
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        _write_subtask_docs(self.temp_root, state, "ST01_01")
        state_path = _write_state(state, self.temp_root)

        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        derived = payload["subtasks"]["ST01_01"]["derived"]
        self.assertFalse(derived["implementation_ready"])
        self.assertIn("gate:requirement_id_ambiguous", derived["blocker_refs"])

    def test_task_gate_blocks_when_packet_inputs_are_missing(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01"],
                task_ids=["ST01_01", "ST01_02", "ST01_03"],
            )
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", "M01"),
            "ST01_02": _subtask_entry("ST01_02", "M01"),
            "ST01_03": _subtask_entry("ST01_03", "M01"),
        }
        for task_id in ("ST01_01", "ST01_02", "ST01_03"):
            state["subtasks"][task_id]["state"]["confirmed"]["implementation_doc_state"] = (
                "active_working_doc"
            )
        _write_subtask_docs(
            self.temp_root,
            state,
            "ST01_01",
            implementation_content=_build_implementation_doc(allowed_paths=[]),
        )
        _write_subtask_docs(
            self.temp_root,
            state,
            "ST01_02",
            implementation_content=_build_implementation_doc(required_tests=[]),
        )
        _write_subtask_docs(
            self.temp_root,
            state,
            "ST01_03",
            implementation_content=_build_implementation_doc(acceptance_criteria=[]),
        )
        state_path = _write_state(state, self.temp_root)

        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        st01 = payload["subtasks"]["ST01_01"]["derived"]
        st02 = payload["subtasks"]["ST01_02"]["derived"]
        st03 = payload["subtasks"]["ST01_03"]["derived"]
        self.assertIn("gate:implementation_scope_unclear", st01["blocker_refs"])
        self.assertIn("gate:required_tests_missing", st02["blocker_refs"])
        self.assertIn("gate:acceptance_criteria_missing", st03["blocker_refs"])

    def test_task_gate_blocks_when_language_policy_is_non_compliant(self) -> None:
        state = _base_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"], task_ids=["ST01_01"])
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        _write_subtask_docs(
            self.temp_root,
            state,
            "ST01_01",
            design_content="# API Overview\n\nUse the API to fetch records.\n",
            implementation_content=(
                "# Implementation Packet\n\n"
                "## 3. Goal\n\n"
                "- Build the implementation packet.\n\n"
                "## 5. Allowed Changes\n\n"
                "### 5.1 Allowed\n"
                "- Files: `apps/api/app/main.py`\n\n"
                "### 5.2 Forbidden\n"
                "- Files: `docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. Tests\n\n"
                "### 7.1 Automated\n"
                "- Run: `python -m pytest tests/doc_governor/test_evaluate.py -q`\n\n"
                "## 8. Acceptance\n\n"
                "- Done: behavior works.\n"
            ),
        )
        state_path = _write_state(state, self.temp_root)

        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        derived = payload["subtasks"]["ST01_01"]["derived"]
        self.assertFalse(derived["implementation_ready"])
        self.assertTrue(
            any(item["reason_code"] == "language_non_compliant" for item in derived["implementation_blockers"])
        )

    def test_implementation_doc_activation_recommendation(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", "M01"),
            "ST01_02": _subtask_entry("ST01_02", "M01"),
        }
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"] = {
            "exists": True,
            "template_like": True,
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []
        state["subtasks"]["ST01_02"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_02"]["facts"]["implementation_doc"] = {
            "exists": True,
            "template_like": False,
        }
        state["subtasks"]["ST01_02"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertTrue(
            payload["subtasks"]["ST01_01"]["derived"][
                "implementation_doc_activation_recommended"
            ]
        )
        self.assertFalse(
            payload["subtasks"]["ST01_02"]["derived"][
                "implementation_doc_activation_recommended"
            ]
        )

    def test_candidate_and_near_ready_facts_are_document_layer_only(self) -> None:
        state = _base_state()
        state["global_policy"]["formal_window_open"] = False
        state["requirements"] = {
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01"],
                task_ids=["ST13_20", "ST13_21", "ST13_24", "ST13_25"],
            )
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {
            "ST13_24": _subtask_entry("ST13_24", "M01"),
            "ST13_25": _subtask_entry("ST13_25", "M01"),
            "ST13_21": _subtask_entry("ST13_21", "M01"),
            "ST13_20": _subtask_entry("ST13_20", "M01"),
        }
        for task_id in ("ST13_24", "ST13_25"):
            facts = state["subtasks"][task_id]["facts"]
            facts["formal_window_candidate_recommended"] = True
            facts["formal_window_candidate_source"] = "facts-preview"
            facts["formal_window_candidate_review_status"] = "pending_confirmation"
            facts["formal_window_candidate_state"] = "document_layer_recommended"
            facts["formal_window_candidate_notes"] = "facts-only candidate preview"
        for task_id in ("ST13_21", "ST13_20"):
            facts = state["subtasks"][task_id]["facts"]
            facts["near_ready_for_formal_window_candidate"] = True
            facts["near_ready_reason"] = "仍有 blocker"
            facts["near_ready_blockers"] = ["gate:implementation_doc_not_active"]
            facts["near_ready_state"] = "document_layer_only"
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))

        self.assertEqual(exit_code, 0)
        st13_24 = payload["subtasks"]["ST13_24"]["derived"]
        st13_21 = payload["subtasks"]["ST13_21"]["derived"]
        self.assertEqual(
            st13_24["formal_window_candidate_recommendation"]["state"],
            "document_layer_recommended",
        )
        self.assertEqual(st13_24["formal_window_candidate_recommendation"]["tool_effect"], "facts_only")
        self.assertEqual(st13_21["near_ready_for_formal_window_candidate"]["state"], "document_layer_only")
        self.assertFalse(st13_21["formal_window_candidate_recommendation"]["recommended"])
        self.assertFalse(st13_24["implementation_ready"])
        self.assertFalse(st13_21["implementation_ready"])

    def test_summary_fields_and_counts(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01"), "M02": _module_entry("M02")}
        state["modules"]["M02"]["facts"]["docs"]["requirements"]["exists"] = False

        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", "M01"),
            "ST01_02": _subtask_implementation_missing_entry("ST01_02", "M01"),
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = ["M02"]
        state["subtasks"]["ST01_02"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        state["subtasks"]["ST01_02"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        summary = payload["summary"]
        self.assertIn("modules_review_required", summary)
        self.assertIn("subtasks_review_required", summary)
        self.assertIn("modules_blocked_count", summary)
        self.assertIn("subtasks_blocked_count", summary)
        self.assertIn("blocked_by_reason_code", summary)
        self.assertIn("oq_gate_counts", summary)
        self.assertEqual(summary["modules_blocked_count"], 1)
        self.assertEqual(summary["subtasks_blocked_count"], 2)

    def test_baseline_delta_summary(self) -> None:
        baseline_state = _base_state()
        baseline_state["modules"] = {"M01": _module_entry("M01")}
        baseline_state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        baseline_state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []
        baseline_state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )

        baseline_path = _write_state(baseline_state, self.temp_root)
        _, baseline_payload = self.run_cli("evaluate-state", "--input", str(baseline_path))
        baseline_json_path = self.temp_root / "baseline-evaluate.json"
        baseline_json_path.write_text(
            json.dumps(baseline_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        current_state = _base_state()
        current_state["modules"] = {"M01": _module_entry("M01")}
        current_state["modules"]["M01"]["facts"]["docs"]["requirements"]["exists"] = False
        current_state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        current_state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []
        current_state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        current_path = _write_state(current_state, self.temp_root)

        exit_code, payload = self.run_cli(
            "evaluate-state",
            "--input",
            str(current_path),
            "--baseline-evaluate-json",
            str(baseline_json_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("delta_summary", payload)
        delta_summary = payload["delta_summary"]
        self.assertGreaterEqual(delta_summary["blocker_changes"]["added_count"], 1)
        self.assertEqual(delta_summary["blocker_changes"]["closed_count"], 0)
        self.assertEqual(
            delta_summary["review_required_changes"]["modules"]["after_true_count"],
            0,
        )
        self.assertEqual(
            delta_summary["readiness_changes"]["modules_downstream"]["before_true_count"],
            1,
        )
        self.assertEqual(
            delta_summary["readiness_changes"]["modules_downstream"]["after_true_count"],
            0,
        )

    def test_evaluate_state_does_not_write_back_state(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_implementation_missing_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"]["exists"] = False
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"]["template_like"] = False

        state_path = _write_state(state, self.temp_root)
        before = state_path.read_bytes()

        self.run_cli("evaluate-state", "--input", str(state_path))
        after = state_path.read_bytes()
        self.assertEqual(before, after)

    def test_empty_state_is_successful(self) -> None:
        state = _base_state()
        state["modules"] = {}
        state["subtasks"] = {}
        state["oqs"] = {}
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["summary"]["modules_review_required"], 0)
        self.assertEqual(payload["summary"]["subtasks_review_required"], 0)
        self.assertEqual(payload["summary"]["modules_blocked_count"], 0)
        self.assertEqual(payload["summary"]["subtasks_blocked_count"], 0)
        self.assertEqual(payload["modules"], {})
        self.assertEqual(payload["subtasks"], {})

    def test_real_repo_evaluate_summary(self) -> None:
        repo_root = self.temp_root / "real_repo"
        shutil.copytree(FIXTURES_REPO, repo_root)
        exit_code, payload_bootstrap = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(repo_root),
            "--overwrite",
        )
        self.assertEqual(exit_code, 0)
        exit_code, payload = self.run_cli(
            "evaluate-state",
            "--input",
            str(repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("summary", payload)
        self.assertIn("modules", payload)
        self.assertIn("subtasks", payload)
        self.assertIn("summary", payload)
        self.assertIn("modules_review_required", payload["summary"])
        self.assertIn("subtasks_review_required", payload["summary"])
        self.assertGreaterEqual(payload["summary"]["modules_review_required"], 0)

    def test_evaluate_does_not_apply_oq_defaults(self) -> None:
        state = _base_state()
        state["oqs"] = {
            "OQ-201": {
                "title": "missing policy fields",
                "status": "open",
                "affects": {"modules": ["M01"], "subtasks": []},
            }
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        exit_code, payload = self.run_cli(
            "evaluate-state",
            "--input",
            str(state_path),
        )
        self.assertEqual(exit_code, 1)
        self.assertTrue(
            any(
                item["code"] == "SCHEMA_MISSING_REQUIRED_FIELD"
                and item["field_path"] == "oqs.OQ-201.gate_level"
                for item in payload["diagnostics"]
            )
        )


if __name__ == "__main__":
    unittest.main()
