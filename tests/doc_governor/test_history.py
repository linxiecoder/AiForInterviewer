import io
import json
import os
import shutil
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import redirect_stdout

from tools.doc_governor.cli import main
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _build_entry(
    *,
    transition_id: str,
    timestamp: datetime,
    entity_type: str = "module",
    entity_id: str = "M01",
    actor: str = "smoke-bot",
    dry_run: bool = False,
    changed_fields: list[str] | None = None,
    result: str | None = None,
    mode: str | None = None,
) -> dict[str, object]:
    return {
        "transition_id": transition_id,
        "timestamp": timestamp.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "actor": actor,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "dry_run": dry_run,
        "changed_fields": [] if changed_fields is None else changed_fields,
        "mode": mode,
        "result": result,
    }


class HistoryCommandTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "history"

    def setUp(self) -> None:
        super().setUp()
        (self.temp_root / "docs" / "governance").mkdir(parents=True, exist_ok=True)
        self.history_path = self.temp_root / "docs" / "governance" / "transition_history.jsonl"
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.bootstrap_path = self.temp_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"
        self.state_path.write_text("STATE_SENTINEL", encoding="utf-8")
        self.bootstrap_path.write_text("BOOTSTRAP_SENTINEL", encoding="utf-8")

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(list(args))
            payload = json.loads(stdout.getvalue())
        finally:
            os.chdir(original)
        return exit_code, payload

    def _write_history(self, records: list[dict[str, object]]) -> None:
        lines = [json.dumps(record, ensure_ascii=False) for record in records]
        self.history_path.write_text("\n".join(lines), encoding="utf-8")

    def _write_raw_lines(self, lines: list[str]) -> None:
        self.history_path.write_text("\n".join(lines), encoding="utf-8")

    def test_empty_history_file(self) -> None:
        self.history_path.write_text("", encoding="utf-8")
        exit_code, payload = self._run_cli("show-history")

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["records"], [])
        self.assertEqual(payload["parse_errors"], [])
        self.assertEqual(payload["counts"], {"approved": 0, "rejected": 0, "blocked": 0, "failed": 0})
        self.assertEqual(payload["total_matched"], 0)
        self.assertEqual(payload["returned"], 0)

    def test_missing_history_file(self) -> None:
        if self.history_path.exists():
            self.history_path.unlink()
        exit_code, payload = self._run_cli("show-history")

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["records"], [])
        self.assertEqual(payload["parse_errors"], [])
        self.assertEqual(payload["counts"], {"approved": 0, "rejected": 0, "blocked": 0, "failed": 0})

    def test_illegal_json_line_skipped(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_raw_lines(
            [
                json.dumps(
                    _build_entry(
                        transition_id="t1",
                        timestamp=base,
                        entity_id="M01",
                        actor="alice",
                        changed_fields=["a"],
                    ),
                    ensure_ascii=False,
                ),
                "{broken-json-line",
                json.dumps(
                    _build_entry(
                        transition_id="t2",
                        timestamp=base + timedelta(minutes=1),
                        entity_id="M02",
                        actor="bob",
                        changed_fields=[],
                    ),
                    ensure_ascii=False,
                ),
            ]
        )
        exit_code, payload = self._run_cli("show-history", "--history", str(self.history_path))

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["total_matched"], 2)
        self.assertEqual(payload["returned"], 2)
        self.assertEqual(len(payload["parse_errors"]), 1)
        self.assertEqual(payload["counts"]["approved"], 1)
        self.assertEqual(payload["counts"]["rejected"], 1)

    def test_query_by_entity(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(transition_id="m1", timestamp=base, entity_type="module", entity_id="M01", changed_fields=["a"]),
                _build_entry(transition_id="m2", timestamp=base + timedelta(minutes=1), entity_type="module", entity_id="M02", changed_fields=["a"]),
                _build_entry(transition_id="s1", timestamp=base + timedelta(minutes=2), entity_type="subtask", entity_id="ST01", changed_fields=[]),
            ]
        )
        exit_code, payload = self._run_cli("show-history", "--entity-type", "module", "--entity-id", "M01")

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_matched"], 1)
        self.assertEqual(payload["records"][0]["entity_id"], "M01")

    def test_query_by_actor(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(transition_id="m1", timestamp=base, actor="alice", changed_fields=["a"]),
                _build_entry(transition_id="m2", timestamp=base + timedelta(minutes=1), actor="bob", changed_fields=["a"]),
                _build_entry(transition_id="m3", timestamp=base + timedelta(minutes=2), actor="alice", changed_fields=["a"]),
            ]
        )
        exit_code, payload = self._run_cli("show-history", "--actor", "alice")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_matched"], 2)
        self.assertTrue(all(item["actor"] == "alice" for item in payload["records"]))

    def test_query_by_result_with_alias(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(transition_id="m1", timestamp=base, changed_fields=["a"], result="approve"),
                _build_entry(transition_id="m2", timestamp=base + timedelta(minutes=1), changed_fields=["a"], result="rejected"),
            ]
        )
        exit_code, payload = self._run_cli("show-history", "--result", "reject")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_matched"], 1)
        self.assertEqual(payload["records"][0]["result"], "rejected")

    def test_result_inference_rules(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(
                    transition_id="t1",
                    timestamp=base,
                    dry_run=True,
                    changed_fields=["x"],
                    result=None,
                ),
                _build_entry(
                    transition_id="t2",
                    timestamp=base + timedelta(minutes=1),
                    dry_run=False,
                    changed_fields=["y"],
                    result=None,
                ),
                _build_entry(
                    transition_id="t3",
                    timestamp=base + timedelta(minutes=2),
                    dry_run=False,
                    changed_fields=[],
                    result=None,
                ),
            ]
        )
        exit_code, payload = self._run_cli("show-history", "--history", str(self.history_path))
        self.assertEqual(exit_code, 0)
        self.assertEqual([item["result"] for item in payload["records"]], ["rejected", "approved", "blocked"])

    def test_limit_truncates_latest_first(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(transition_id="m1", timestamp=base, changed_fields=["a"]),
                _build_entry(transition_id="m2", timestamp=base + timedelta(minutes=1), changed_fields=["a"]),
                _build_entry(transition_id="m3", timestamp=base + timedelta(minutes=2), changed_fields=["a"]),
                _build_entry(transition_id="m4", timestamp=base + timedelta(minutes=3), changed_fields=["a"]),
            ]
        )
        exit_code, payload = self._run_cli("show-history", "--limit", "2")

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["returned"], 2)
        self.assertEqual(payload["records"][0]["transition_id"], "m4")
        self.assertEqual(payload["records"][1]["transition_id"], "m3")

    def test_order_descending_time(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(transition_id="m1", timestamp=base),
                _build_entry(transition_id="m2", timestamp=base + timedelta(minutes=2)),
                _build_entry(transition_id="m3", timestamp=base + timedelta(minutes=1)),
            ]
        )
        exit_code, payload = self._run_cli("show-history")
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [item["transition_id"] for item in payload["records"]],
            ["m2", "m3", "m1"],
        )

    def test_latest_attempt_by_entity(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(
                    transition_id="m1",
                    timestamp=base,
                    entity_type="module",
                    entity_id="M01",
                    actor="alice",
                    changed_fields=["a"],
                ),
                _build_entry(
                    transition_id="m2",
                    timestamp=base + timedelta(minutes=2),
                    entity_type="module",
                    entity_id="M01",
                    actor="alice",
                    changed_fields=[],
                ),
                _build_entry(
                    transition_id="s1",
                    timestamp=base + timedelta(minutes=1),
                    entity_type="subtask",
                    entity_id="ST01",
                    actor="bob",
                    changed_fields=["a"],
                ),
            ]
        )
        exit_code, payload = self._run_cli("summarize-history")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["ok"], True)
        latest = {item["entity_id"]: item for item in payload["latest_attempt_by_entity"]}
        self.assertEqual(latest["M01"]["transition_id"], "m2")
        self.assertEqual(latest["ST01"]["transition_id"], "s1")

    def test_top_rejected_entities(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history(
            [
                _build_entry(
                    transition_id="m1",
                    timestamp=base,
                    entity_type="module",
                    entity_id="M01",
                    changed_fields=[],
                ),
                _build_entry(
                    transition_id="m2",
                    timestamp=base + timedelta(minutes=1),
                    entity_type="module",
                    entity_id="M01",
                    changed_fields=[],
                ),
                _build_entry(
                    transition_id="m3",
                    timestamp=base + timedelta(minutes=2),
                    entity_type="module",
                    entity_id="M02",
                    changed_fields=["x"],
                ),
                _build_entry(
                    transition_id="s1",
                    timestamp=base + timedelta(minutes=3),
                    entity_type="subtask",
                    entity_id="ST01",
                    changed_fields=[],
                ),
                _build_entry(
                    transition_id="s2",
                    timestamp=base + timedelta(minutes=4),
                    entity_type="subtask",
                    entity_id="ST01",
                    changed_fields=[],
                ),
            ]
        )
        exit_code, payload = self._run_cli("summarize-history", "--top-rejected", "2")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["top_rejected_entities"][0], {"entity_type": "subtask", "entity_id": "ST01", "rejected_count": 2})
        self.assertEqual(payload["top_rejected_entities"][1], {"entity_type": "module", "entity_id": "M01", "rejected_count": 2})
        self.assertEqual(payload["counts"]["rejected"], 4)

    def test_default_history_path_is_used(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history([_build_entry(transition_id="m1", timestamp=base, changed_fields=["a"])])
        exit_code, payload = self._run_cli("show-history")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_matched"], 1)
        self.assertEqual(payload["records"][0]["transition_id"], "m1")

    def test_state_files_are_not_modified(self) -> None:
        base = datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc)
        self._write_history([_build_entry(transition_id="m1", timestamp=base, changed_fields=["a"])])
        before_state = self.state_path.read_text(encoding="utf-8")
        before_bootstrap = self.bootstrap_path.read_text(encoding="utf-8")

        exit_code, payload = self._run_cli("show-history", "--history", str(self.history_path))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["ok"], True)
        exit_code, payload = self._run_cli("summarize-history", "--history", str(self.history_path))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["ok"], True)

        self.assertEqual(self.state_path.read_text(encoding="utf-8"), before_state)
        self.assertEqual(self.bootstrap_path.read_text(encoding="utf-8"), before_bootstrap)
