import io
import json
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

import yaml

from tools.doc_governor.cli import main
from tools.doc_governor.diagnostics import make_diagnostic, make_evidence

from tools.doc_governor.render import RENDER_OUTPUT_DIR_NAME

REAL_REPO_FIXTURE = Path(__file__).parent / "fixtures" / "repo" / "prose_contamination"


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class RenderCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-render-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)
        (self.temp_root / "docs" / "governance").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _run_cli(
        self,
        *args: str,
        cwd: Path | None = None,
    ) -> tuple[int, dict]:
        original = Path.cwd()
        if cwd is None:
            cwd = self.temp_root
        os.chdir(cwd)
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(list(args))
            payload = json.loads(stdout.getvalue())
        finally:
            os.chdir(original)
        return exit_code, payload

    def _section_lines(self, text: str, heading: str) -> list[str]:
        lines = text.splitlines()
        if heading not in lines:
            return []
        start = lines.index(heading) + 1
        end = len(lines)
        for idx in range(start + 1, len(lines)):
            if lines[idx].startswith("## "):
                end = idx
                break
        return lines[start + 1 : end]

    def test_empty_result(self) -> None:
        payload = {
            "summary": {},
            "modules": {},
            "subtasks": {},
            "oqs": {},
            "diagnostics": [],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)

        exit_code, _ = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)

        report_path = self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME
        text = report_path.read_text(encoding="utf-8")
        self.assertIn("# DOC_GOVERNOR_REPORT", text)
        self.assertIn("## Summary", text)
        self.assertIn("## Modules Requiring Review", text)
        self.assertIn("## Subtasks Requiring Review", text)
        self.assertIn("## Candidate blockers by layer", text)
        self.assertIn("## OQ gate summary", text)
        self.assertIn("- none", text)
        self.assertNotIn("render_input_incomplete=1", text)
        self.assertIn("modules_review_required: 0", text)
        self.assertIn("subtasks_review_required: 0", text)

    def test_non_empty_render_and_section_order(self) -> None:
        payload = {
            "summary": {
                "modules_review_required": 1,
                "subtasks_review_required": 1,
                "modules_blocked_count": 2,
                "subtasks_blocked_count": 3,
                "blocked_by_reason_code": {"legacy_locked": 1},
                "oq_gate_counts": {
                    "observe_only.clear": 0,
                    "observe_only.review_only": 2,
                    "candidate_gate.clear": 0,
                    "candidate_gate.review_only": 3,
                    "candidate_gate.candidate_blocker": 1,
                    "readiness_gate.clear": 0,
                    "readiness_gate.review_only": 0,
                    "readiness_gate.readiness_blocker": 1,
                },
            },
            "modules": {
                "M02": {"derived": {"review_required": True, "review_reasons": ["oq_review_only"]}},
                "M01": {"derived": {"review_required": True, "review_reasons": ["downstream_ready_no_hard_blocker"]}},
            },
            "subtasks": {
                "ST01_10": {
                    "derived": {
                        "review_required": True,
                        "review_reasons": ["implementation_doc_activation_recommended"],
                        "candidate_blockers": [
                            {"ref": "gate:placeholder", "kind": "gate", "reason_code": "legacy_locked", "message": "legacy"},
                        ],
                    }
                },
                "ST01_02": {"derived": {"review_required": False, "review_reasons": []}},
            },
            "oqs": {
                "OQ-01": {"derived_enforcement": "review_only"},
            },
            "diagnostics": [
                {
                    "code": "DUMMY_WARNING",
                    "severity": "warning",
                    "entity_type": "render",
                    "entity_id": "GLOBAL",
                    "field_path": "noop",
                    "message": "ok",
                    "evidence": [{"type": "file_scan", "path": "evaluate.json", "ref": "noop"}],
                }
            ],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)

        exit_code, payload = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])

        report_path = self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME
        report = report_path.read_text(encoding="utf-8")
        expected_sections = [
            "## Summary",
            "## Modules Requiring Review",
            "## Subtasks Requiring Review",
            "## Candidate blockers by layer",
            "## Downstream blockers by layer",
            "## Implementation blockers by layer",
            "## OQ gate summary",
            "## Next Round Agenda",
            "## Notes / interpretation boundary",
        ]
        positions = [report.index(section) for section in expected_sections]
        self.assertEqual(positions, sorted(positions))

        module_rows = [
            line.strip()
            for line in self._section_lines(report, "## Modules Requiring Review")
            if line.startswith("- ")
        ]
        self.assertEqual(module_rows[0], "- `M01`: review_required=true reason=[downstream_ready_no_hard_blocker]")
        self.assertEqual(module_rows[1], "- `M02`: review_required=true reason=[oq_review_only]")

        subtask_rows = [
            line.strip()
            for line in self._section_lines(report, "## Subtasks Requiring Review")
            if line.startswith("- ")
        ]
        self.assertEqual(subtask_rows[0], "- `ST01_10`: review_required=true reason=[implementation_doc_activation_recommended]")

    def test_default_path_and_sorted_blockers(self) -> None:
        payload = {
            "summary": {"modules_review_required": 0, "subtasks_review_required": 0, "modules_blocked_count": 0, "subtasks_blocked_count": 0, "oq_gate_counts": {}},
            "modules": {
                "M01": {
                    "derived": {
                        "candidate_blockers": [
                            {"ref": "module:M01", "kind": "slot", "reason_code": "missing_required_doc_slot", "message": "slot"},
                            {"ref": "module:M01", "kind": "slot", "reason_code": "missing_required_doc_slot", "message": "schema"},
                            {"ref": "module:M02", "kind": "slot", "reason_code": "template_like_required_doc_slot", "message": "slot"},
                        ]
                    }
                }
            },
            "subtasks": {},
            "oqs": {},
            "diagnostics": [],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        exit_code, payload_out = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
            "--report-path",
            str(self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME),
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload_out["ok"])

        report_path = self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME
        report = report_path.read_text(encoding="utf-8")
        module_blocker_lines = [
            line
            for line in self._section_lines(report, "### Modules")
            if line.startswith("- [")
        ]
        self.assertEqual(
            module_blocker_lines[:3],
            [
                "- [module:M01] reason_code=missing_required_doc_slot ref=module:M01 kind=slot message=slot",
                "- [module:M01] reason_code=missing_required_doc_slot ref=module:M01 kind=slot message=schema",
                "- [module:M01] reason_code=template_like_required_doc_slot ref=module:M02 kind=slot message=slot",
            ],
        )

    def test_oq_gate_summary_fixed_order(self) -> None:
        summary = {
            "modules_review_required": 0,
            "subtasks_review_required": 0,
            "modules_blocked_count": 0,
            "subtasks_blocked_count": 0,
            "oq_gate_counts": {
                "observe_only.clear": 1,
                "observe_only.review_only": 2,
                "candidate_gate.clear": 3,
                "candidate_gate.review_only": 4,
                "candidate_gate.candidate_blocker": 5,
                "readiness_gate.clear": 6,
                "readiness_gate.review_only": 7,
                "readiness_gate.readiness_blocker": 8,
            },
        }
        payload = {
            "summary": summary,
            "modules": {},
            "subtasks": {},
            "oqs": {},
            "diagnostics": [],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        exit_code, _ = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
        )
        self.assertEqual(exit_code, 0)
        report = (self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME).read_text(encoding="utf-8")
        lines = report.splitlines()
        idx = {key: lines.index(f"- {key}: {summary['oq_gate_counts'][key]}") for key in summary["oq_gate_counts"]}
        expected = [
            "- observe_only.clear: 1",
            "- observe_only.review_only: 2",
            "- candidate_gate.clear: 3",
            "- candidate_gate.review_only: 4",
            "- candidate_gate.candidate_blocker: 5",
            "- readiness_gate.clear: 6",
            "- readiness_gate.review_only: 7",
            "- readiness_gate.readiness_blocker: 8",
        ]
        idxs = [lines.index(item) for item in expected]
        self.assertEqual(idxs, sorted(idxs))

    def test_invalid_path_forbidden(self) -> None:
        payload = {"summary": {}, "modules": {}, "subtasks": {}, "oqs": {}}
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        exit_code, result = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
            "--report-path",
            str(self.temp_root / "outside.md"),
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(result["diagnostics"][0]["code"], "RENDER_REPORT_PATH_FORBIDDEN")

    def test_official_state_path_rejected(self) -> None:
        payload = {"summary": {}, "modules": {}, "subtasks": {}, "oqs": {}}
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        official = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        official.write_text("KEEP", encoding="utf-8")
        exit_code, result = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
            "--report-path",
            str(official),
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(official.read_text(encoding="utf-8"), "KEEP")

        bootstrap = self.temp_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        bootstrap.write_text("KEEP", encoding="utf-8")
        exit_code, _ = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
            "--report-path",
            str(bootstrap),
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(bootstrap.read_text(encoding="utf-8"), "KEEP")

    def test_input_diagnostics_error_marked(self) -> None:
        payload = {
            "summary": {},
            "modules": {},
            "subtasks": {},
            "oqs": {},
            "diagnostics": [
                {
                    "code": "X",
                    "severity": "error",
                    "entity_type": "eval",
                    "entity_id": "GLOBAL",
                    "field_path": "x",
                    "message": "bad",
                    "evidence": [{"type": "render", "path": "x", "ref": "x", "value": "1"}],
                }
            ],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        exit_code, _ = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
        )
        report = (self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME).read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertIn("render_input_invalid=1", report)

    def test_state_wrapper_calls_evaluate_state(self) -> None:
        stub_path = self.temp_root / "state.yaml"
        stub_path.write_text(yaml.safe_dump({"schema_version": 1}), encoding="utf-8")

        payload = {
            "summary": {},
            "modules": {},
            "subtasks": {},
            "oqs": {},
            "diagnostics": [
                {
                    "code": "STATE_ERR",
                    "severity": "error",
                    "entity_type": "state",
                    "entity_id": "GLOBAL",
                    "field_path": "x",
                    "message": "state diagnostic",
                    "evidence": [{"type": "file_scan", "path": "x", "ref": "x", "value": "1"}],
                }
            ],
        }
        report_path = self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME
        with patch("tools.doc_governor.cli.evaluate_state_file") as eval_state:
            eval_state.return_value = (
                [make_diagnostic(
                    code="STATE_ERR",
                    severity="error",
                    entity_type="state",
                    entity_id="GLOBAL",
                    field_path="x",
                    message="state diagnostic",
                    evidence=[make_evidence(type="file_scan", path=str(stub_path), ref="x", value="1")],
                )],
                payload,
            )
            exit_code, result = self._run_cli(
                "render-report",
                "--state",
                str(stub_path),
                "--report-path",
                str(report_path),
            )

        eval_state.assert_called_once_with(stub_path)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertIn("render_input_invalid=1", report_path.read_text(encoding="utf-8"))

    def test_next_round_agenda_snapshot(self) -> None:
        payload = {
            "summary": {},
            "modules": {
                "M01": {"derived": {"review_required": True, "candidate_blockers": []}},
                "M02": {
                    "derived": {
                        "review_required": False,
                        "candidate_blockers": [
                            {"reason_code": "missing_required_doc_slot"},
                        ],
                    }
                },
            },
            "subtasks": {
                "ST01_01": {
                    "derived": {
                        "review_required": False,
                        "candidate_blockers": [{"reason_code": "oq_candidate_gate"}],
                        "downstream_blockers": [],
                        "implementation_blockers": [],
                    }
                }
            },
            "oqs": {
                "OQ-100": {
                    "derived_status_class": "unresolved",
                    "derived_enforcement": "candidate_blocker",
                    "derived_reason_code": "oq_candidate_gate",
                }
            },
            "diagnostics": [],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        exit_code, _ = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
            "--agenda-limit",
            "3",
        )
        self.assertEqual(exit_code, 0)

        report = (self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME).read_text(encoding="utf-8")
        lines = self._section_lines(report, "## Next Round Agenda")
        snapshot = "\n".join([line for line in lines if line.strip()])
        expected = """### Agenda 1: 必须先决策的 OQ（candidate/readiness gate）
- entity: oq:OQ-100
- current_state: status_class=unresolved, enforcement=candidate_blocker
- blocking_reason_codes: oq_candidate_gate
- required_evidence: confirm OQ decision evidence (confirmed/manual override)
- suggested_owner: governance-owner
### Agenda 2: review_required 的 near-open 实体
- entity: module:M01
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: none
- required_evidence: review confirmation evidence
- suggested_owner: module-owner
### Agenda 3: hard blocker 最少、最接近可推进的实体
- entity: subtask:ST01_01
- current_state: review_required=false, hard_blocker_count=1
- blocking_reason_codes: oq_candidate_gate
- required_evidence: resolve blocker evidence, review confirmation evidence
- suggested_owner: subtask-owner"""
        self.assertEqual(snapshot, expected)

    def test_next_round_agenda_safe_degrade_when_fields_missing(self) -> None:
        payload = {
            "summary": {},
            "modules": {"M01": {"derived": {"review_required": True}}},
            "subtasks": {"ST01_01": {"derived": {"candidate_blockers": ["bad-data"]}}},
            "oqs": {"OQ-1": {"derived_enforcement": "candidate_blocker"}},
            "diagnostics": [],
        }
        json_path = _write_json(self.temp_root / "evaluate.json", payload)
        exit_code, _ = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(json_path),
            "--agenda-limit",
            "5",
        )
        self.assertEqual(exit_code, 0)
        report = (self.temp_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME).read_text(encoding="utf-8")
        self.assertIn("## Next Round Agenda", report)
        self.assertIn("- current_state: status_class=unknown, enforcement=candidate_blocker", report)
        self.assertIn("- blocking_reason_codes: none", report)

    def test_real_repo_render_summary(self) -> None:
        repo_root = self.temp_root / "real_repo"
        shutil.copytree(REAL_REPO_FIXTURE, repo_root)
        bootstrap = repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        exit_code, _ = self._run_cli(
            "bootstrap-state",
            "--repo-root",
            str(repo_root),
            "--overwrite",
            cwd=repo_root,
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(bootstrap.exists())

        exit_code, evaluate_payload = self._run_cli(
            "evaluate-state",
            "--input",
            str(bootstrap),
            cwd=repo_root,
        )
        self.assertEqual(exit_code, 0)
        result_json_path = repo_root / "evaluate.json"
        _write_json(result_json_path, evaluate_payload)

        exit_code, render_payload = self._run_cli(
            "render-report",
            "--evaluate-json",
            str(result_json_path),
            "--report-path",
            str(repo_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME),
            cwd=repo_root,
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(render_payload["ok"])

        report_path = repo_root / "docs" / "governance" / RENDER_OUTPUT_DIR_NAME
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("## Summary", report_text)
        self.assertIn("## OQ gate summary", report_text)
        self.assertIn("modules_review_required", report_text)
        self.assertIn("subtasks_review_required", report_text)
