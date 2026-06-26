import json
import os
from pathlib import Path

from app.infrastructure.observability.logging import LogUtil
from app.main import ApiSettings, _startup_log_lines, create_app
from scripts.dev import dev_env
from tests.api.asgi_client import call_json_response


def test_startup_log_reports_api_log_file_path() -> None:
    lines = _startup_log_lines(
        ApiSettings(log_file_path="tmp/logs/api-dev.log", log_file_enabled=True)
    )

    assert "API log file: tmp/logs/api-dev.log" in lines


def test_dev_start_scripts_preserve_and_show_api_log_file() -> None:
    start_script = Path("scripts/dev/start.sh").read_text(encoding="utf-8")
    api_script = Path("scripts/dev/start-api.sh").read_text(encoding="utf-8")

    assert "API_LOG_FILE API_LOG_FILE_ENABLED" in start_script
    assert "API_LOG_FILE API_LOG_FILE_ENABLED" in api_script
    assert 'API_LOG_FILE="${API_LOG_FILE:-tmp/logs/api-dev.log}"' in api_script
    assert 'echo "[dev] api log file ${API_LOG_FILE}"' in api_script
    assert 'echo "[dev] VITE_API_PROXY_TARGET=${VITE_API_PROXY_TARGET}"' in start_script


def test_dev_python_runner_defaults_api_log_file(monkeypatch) -> None:
    monkeypatch.delenv("API_LOG_FILE", raising=False)

    settings = dev_env.resolve_api_run_settings([])
    dev_env.apply_api_run_settings_to_env(settings)

    assert settings.log_file_path == "tmp/logs/api-dev.log"
    assert os.environ["API_LOG_FILE"] == "tmp/logs/api-dev.log"
    os.environ.pop("API_LOG_FILE", None)


def test_dev_python_runner_preserves_explicit_api_log_file(monkeypatch) -> None:
    monkeypatch.setenv("API_LOG_FILE", "tmp/logs/custom-api.log")

    settings = dev_env.resolve_api_run_settings([])
    dev_env.apply_api_run_settings_to_env(settings)

    assert settings.log_file_path == "tmp/logs/custom-api.log"
    assert os.environ["API_LOG_FILE"] == "tmp/logs/custom-api.log"


def test_api_log_file_env_captures_access_and_program_logs(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "api-dev.log"
    monkeypatch.setenv("API_LOG_FILE", str(log_path))
    monkeypatch.delenv("API_LOG_FILE_ENABLED", raising=False)

    app = create_app()
    status_code, body, _headers = call_json_response(app, "/api/v1/health")
    LogUtil.api_runtime_ready(message="test program log visible")

    assert status_code == 200
    assert body == {"status": "ok"}

    records = _json_log_records(log_path)
    events = {record["event"] for record in records}
    assert "http_access" in events
    assert any(
        record["event"] == "api_runtime_ready"
        and record["message"] == "test program log visible"
        for record in records
    )


def _json_log_records(log_path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
