import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.dev.pycharm_debug_uvicorn import (
    PyCharmDebugSettings,
    attach_pycharm_debugger,
    resolve_pycharm_debug_settings,
)


def resolve_git_bash_for_dev_script_tests() -> str | None:
    candidates = [
        os.environ.get("OMO_CODEX_GIT_BASH_PATH"),
        r"C:\Program Files\Git\bin\bash.exe",
        shutil.which("bash"),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = Path(candidate)
        normalized = str(candidate_path).replace("/", "\\").lower()
        if "\\windows\\system32\\bash.exe" in normalized:
            continue
        if candidate_path.exists():
            return str(candidate_path)
    return None


def test_start_api_debug_uses_pycharm_wrapper_without_uvicorn_reload() -> None:
    script = Path("scripts/dev/start-api.sh").read_text(encoding="utf-8")

    assert 'API_HOST="${API_HOST:-127.0.0.1}"' in script
    assert 'API_PORT="${API_PORT:-8001}"' in script
    assert "export API_PORT" in script
    assert 'PYTHON_BIN="$(resolve_python "$ROOT_DIR")"' in script
    assert 'scripts/dev/check_auth_dev_user.py' in script
    assert 'exec "$PYTHON_BIN" scripts/dev/pycharm_debug_uvicorn.py --host "$API_HOST" --port "$API_PORT"' in script
    assert 'exec "$PYTHON_BIN" scripts/dev/run_api.py --host "$API_HOST" --port "$API_PORT"' in script
    assert 'exec "$PYTHON_BIN" -m uvicorn' not in script
    assert script.index("scripts/dev/check_auth_dev_user.py") < script.index(
        'exec "$PYTHON_BIN" scripts/dev/run_api.py --host "$API_HOST" --port "$API_PORT"'
    )
    debug_exec_index = script.index(
        'exec "$PYTHON_BIN" scripts/dev/pycharm_debug_uvicorn.py --host "$API_HOST" --port "$API_PORT"'
    )
    normal_exec_index = script.index(
        'exec "$PYTHON_BIN" scripts/dev/run_api.py --host "$API_HOST" --port "$API_PORT"'
    )
    debug_branch_start = script.rindex('if [ "$MODE" = "debug" ]; then', 0, debug_exec_index)
    debug_branch = script[debug_branch_start:debug_exec_index]
    assert debug_exec_index < normal_exec_index
    assert "--reload" not in debug_branch


def test_shell_python_resolver_supports_posix_and_windows_venv() -> None:
    helper = Path("scripts/lib/python.sh").read_text(encoding="utf-8")

    assert "${root_dir}/.venv/bin/python" in helper
    assert "${root_dir}/.venv/Scripts/python.exe" in helper
    assert "${PYTHON:-}" in helper


def test_shell_dotenv_loader_preserves_explicit_environment() -> None:
    helper = Path("scripts/lib/env.sh").read_text(encoding="utf-8")
    start_script = Path("scripts/dev/start.sh").read_text(encoding="utf-8")
    api_script = Path("scripts/dev/start-api.sh").read_text(encoding="utf-8")

    assert "load_dotenv_preserving_explicit_env" in helper
    assert "remember_explicit_env" in helper
    assert "restore_explicit_env" in helper
    assert "source \"${ROOT_DIR}/scripts/lib/env.sh\"" in start_script
    assert "source \"${ROOT_DIR}/scripts/lib/env.sh\"" in api_script
    assert (
        "load_dotenv_preserving_explicit_env .env API_HOST API_PORT WEB_PORT "
        "VITE_API_PROXY_TARGET API_LOG_FILE API_LOG_FILE_ENABLED"
    ) in start_script
    assert (
        "load_dotenv_preserving_explicit_env .env API_HOST API_PORT API_LOG_FILE "
        "API_LOG_FILE_ENABLED PYCHARM_DEBUG_HOST"
    ) in api_script


def test_db_scripts_use_resolved_python() -> None:
    for path in ("scripts/db/migrate.sh", "scripts/db/revision.sh"):
        script = Path(path).read_text(encoding="utf-8")

        assert 'source "${ROOT_DIR}/scripts/lib/python.sh"' in script
        assert 'PYTHON_BIN="$(resolve_python "$ROOT_DIR")"' in script
        assert 'exec "$PYTHON_BIN"' in script
        assert ".venv/bin/python" not in script


def test_kill_ports_clears_windows_listeners_for_wsl_web_runtime() -> None:
    script = Path("scripts/dev/kill-ports.sh").read_text(encoding="utf-8")

    assert "find_pids_with_ss" in script
    assert "is_wsl_shell" in script
    assert "find_wsl_pids" in script
    assert "kill_wsl_pids" in script
    assert "find_windows_pids" in script
    assert "find_windows_pids_with_netstat" in script
    assert "kill_windows_pids" in script
    assert "windows_pid_exists" in script
    assert "filter_existing_windows_pids" in script
    assert "filter_missing_windows_pids" in script
    assert "describe_windows_pids" in script
    assert "normalize_pids" in script
    assert "pause_after_kill" in script
    assert "local seen=\" \"" in script
    assert "fallback_pid_list" in script
    assert "powershell.exe" in script
    assert "Start-Sleep -Seconds 1" in script
    assert "cmd.exe" in script
    assert "ForEach-Object" in script
    assert "netstat -ano -p tcp" in script
    assert "wsl.exe sh -lc" in script
    assert "ss -ltnp" in script
    assert "Get-NetTCPConnection" in script
    assert "Get-CimInstance Win32_Process" in script
    assert "Stop-Process" in script
    assert "taskkill.exe" in script
    assert 'MSYS2_ARG_CONV_EXCL="*" taskkill.exe /F /PID "$process_id"' in script
    assert "taskkill.exe /F /PID" in script
    assert "taskkill.exe //F //PID" not in script
    assert "taskkill failed for Windows PID" in script
    assert "Stop-Process failed for Windows PID" in script
    assert "unable to inspect process details" in script
    assert "stale Windows TCP listener PID(s)" in script
    assert "not attached to a live Windows process" in script
    assert "failed to free port" in script
    assert "the listener is likely owned by System or the virtualization network layer" in script
    assert "blocking port reuse" in script
    assert "xargs" not in script
    assert "tr -d" not in script


def test_kill_ports_blocks_windows_tcp_listener_when_process_cannot_be_verified(tmp_path) -> None:
    bash = resolve_git_bash_for_dev_script_tests()
    if bash is None:
        pytest.skip("Git Bash is required for Windows dev shell script tests")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_powershell = fake_bin / "powershell.exe"
    fake_powershell.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "command_text=\"$*\"",
                "if [[ \"$command_text\" == *\"Win32_Process\"* ]]; then exit 1; fi",
                "if [[ \"$command_text\" == *\"Get-Process\"* ]]; then exit 1; fi",
                "if [[ \"$command_text\" == *\"Get-NetTCPConnection\"* ]]; then echo 26188; exit 0; fi",
                "if [[ \"$command_text\" == *\"netstat -ano\"* ]]; then echo 26188; exit 0; fi",
                "exit 0",
            ]
        ),
        encoding="utf-8",
    )
    fake_powershell.chmod(0o755)
    fake_taskkill = fake_bin / "taskkill.exe"
    fake_taskkill.write_text(
        "#!/usr/bin/env bash\n"
        "echo 'taskkill should not run for a ghost PID' >&2\n"
        "exit 7\n",
        encoding="utf-8",
    )
    fake_taskkill.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    result = subprocess.run(
        [bash, "scripts/dev/kill-ports.sh", "49213"],
        cwd=Path.cwd(),
        env=env,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "stale Windows TCP listener PID(s): 26188" in result.stdout
    assert "not attached to a live Windows process" in result.stdout
    assert "blocking port reuse" in result.stdout
    assert "taskkill should not run" not in result.stderr


def test_auth_dev_user_preflight_accepts_configured_dev_credentials(monkeypatch) -> None:
    from scripts.dev import check_auth_dev_user

    monkeypatch.setenv("API_AUTH_DEV_USER_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_DEV_USER_IDENTIFIER", "developer")
    monkeypatch.setenv("API_AUTH_DEV_USER_EMAIL", "developer@example.com")
    monkeypatch.setenv("API_AUTH_DEV_USER_USERNAME", "developer")
    monkeypatch.setenv("API_AUTH_DEV_USER_PASSWORD", "local-test-password")

    assert check_auth_dev_user.main() == 0


def test_auth_dev_user_preflight_fails_when_enabled_without_password(monkeypatch) -> None:
    from scripts.dev import check_auth_dev_user

    monkeypatch.setenv("API_AUTH_DEV_USER_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_DEV_USER_IDENTIFIER", "developer")
    monkeypatch.delenv("API_AUTH_DEV_USER_PASSWORD", raising=False)

    assert check_auth_dev_user.main() == 2


def test_auth_dev_user_preflight_script_bootstraps_api_path_without_pythonpath() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(
        {
            "API_AUTH_DEV_USER_ENABLED": "true",
            "API_AUTH_DEV_USER_IDENTIFIER": "developer",
            "API_AUTH_DEV_USER_EMAIL": "developer@example.com",
            "API_AUTH_DEV_USER_USERNAME": "developer",
            "API_AUTH_DEV_USER_PASSWORD": "local-test-password",
        }
    )

    result = subprocess.run(
        [sys.executable, "scripts/dev/check_auth_dev_user.py"],
        cwd=Path.cwd(),
        env=env,
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "[dev] auth dev user ready: developer" in result.stdout


def test_dev_python_entrypoints_load_project_dotenv_and_api_path() -> None:
    for path in (
        "scripts/dev/check_auth_dev_user.py",
        "scripts/dev/pycharm_debug_uvicorn.py",
        "scripts/dev/run_api.py",
    ):
        script = Path(path).read_text(encoding="utf-8")

        assert "load_project_dotenv" in script
        assert "ensure_api_import_path" in script


def test_dev_env_loader_preserves_explicit_environment(monkeypatch) -> None:
    from scripts.dev import dev_env

    monkeypatch.setenv("API_AUTH_DEV_USER_PASSWORD", "explicit-password")
    monkeypatch.setenv("API_PORT", "8003")
    dev_env.load_project_dotenv()

    assert os.environ["API_AUTH_DEV_USER_PASSWORD"] == "explicit-password"
    assert os.environ["API_PORT"] == "8003"


def test_api_run_settings_prefer_cli_port_over_dotenv_environment(monkeypatch) -> None:
    from scripts.dev import dev_env

    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8001")
    monkeypatch.delenv("API_LOG_FILE", raising=False)

    settings = dev_env.resolve_api_run_settings(["--host", "127.0.0.1", "--port", "8003"])
    dev_env.apply_api_run_settings_to_env(settings)

    assert settings == dev_env.ApiRunSettings(
        host="127.0.0.1",
        port=8003,
        log_file_path="tmp/logs/api-dev.log",
    )
    assert os.environ["API_HOST"] == "127.0.0.1"
    assert os.environ["API_PORT"] == "8003"
    assert os.environ["API_LOG_FILE"] == "tmp/logs/api-dev.log"
    os.environ.pop("API_LOG_FILE", None)


def test_start_script_resolves_web_runtime_before_starting_processes() -> None:
    script = Path("scripts/dev/start.sh").read_text(encoding="utf-8")

    assert 'source "${ROOT_DIR}/scripts/lib/node.sh"' in script
    assert 'API_PORT="${API_PORT:-8001}"' in script
    assert 'WEB_PORT="${WEB_PORT:-5173}"' in script
    assert "resolve_api_port()" in script
    assert 'resolve_api_port' in script
    assert 'bash scripts/dev/kill-ports.sh "$port"' in script
    assert "API_PORT_WAS_EXPLICIT" in script
    assert "VITE_API_PROXY_TARGET_WAS_EXPLICIT" in script
    assert 'if [ "$API_PORT_WAS_EXPLICIT" = "1" ]; then' in script
    assert "API_PORT ${port} is unavailable; using ${candidate}" in script
    assert 'VITE_API_PROXY_TARGET="http://127.0.0.1:${API_PORT}"' in script
    assert 'bash scripts/dev/kill-ports.sh "$WEB_PORT"' in script
    assert 'start_web_dev "$ROOT_DIR" &' in script
    assert "npm --workspace apps/web run dev &" not in script
    assert script.index("select_web_runtime") < script.index("bash scripts/dev/kill-ports.sh")


def test_start_script_cleanup_clears_orphan_dev_port_listeners() -> None:
    script = Path("scripts/dev/start.sh").read_text(encoding="utf-8")
    cleanup_start = script.index("cleanup()")
    cleanup_end = script.index("trap cleanup", cleanup_start)
    cleanup_body = script[cleanup_start:cleanup_end]

    assert 'kill "$API_PID"' in cleanup_body
    assert 'kill "$WEB_PID"' in cleanup_body
    assert 'bash scripts/dev/kill-ports.sh "$API_PORT" "$WEB_PORT"' in cleanup_body


def test_start_web_script_uses_shared_node_resolver() -> None:
    script = Path("scripts/dev/start-web.sh").read_text(encoding="utf-8")
    root_package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert 'source "${ROOT_DIR}/scripts/lib/node.sh"' in script
    assert "select_web_runtime" in script
    assert 'start_web_dev "$ROOT_DIR"' in script
    assert root_package["scripts"]["dev:web"] == "bash scripts/dev/kill-ports.sh 5173 && bash scripts/dev/start-web.sh"


def test_node_resolver_falls_back_to_windows_npm_for_bash_on_windows() -> None:
    helper = Path("scripts/lib/node.sh").read_text(encoding="utf-8")

    assert 'WEB_NODE_MIN_VERSION="20.19.0"' in helper
    assert "node_version_supports_web_dev" in helper
    assert "is_wsl_shell" in helper
    assert "cygpath -w" in helper
    assert "powershell.exe" in helper
    assert "powershell_single_quoted_literal" in helper
    assert "if command -v powershell.exe >/dev/null 2>&1; then" in helper
    assert "if is_wsl_shell && command -v powershell.exe" not in helper
    assert 'Set-Location -LiteralPath ${powershell_root}' in helper
    assert 'powershell_api_proxy_target="$(powershell_single_quoted_literal "$VITE_API_PROXY_TARGET")"' in helper
    assert '$env:VITE_API_PROXY_TARGET=${powershell_api_proxy_target}' in helper
    assert "npm.cmd --workspace apps/web run dev" in helper
    assert 'VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:${API_PORT:-8001}}"' in helper
    assert "$args[0]" not in helper


def test_package_engines_match_vite_node_floor() -> None:
    root_package = json.loads(Path("package.json").read_text(encoding="utf-8"))
    web_package = json.loads(Path("apps/web/package.json").read_text(encoding="utf-8"))
    lockfile = json.loads(Path("package-lock.json").read_text(encoding="utf-8"))

    assert root_package["engines"]["node"] == ">=20.19.0"
    assert web_package["engines"]["node"] == ">=20.19.0"
    assert lockfile["packages"][""]["engines"]["node"] == ">=20.19.0"
    assert lockfile["packages"]["apps/web"]["engines"]["node"] == ">=20.19.0"


def test_resolve_pycharm_debug_settings_defaults_to_local_debug_server() -> None:
    settings = resolve_pycharm_debug_settings({})

    assert settings == PyCharmDebugSettings(
        host="127.0.0.1",
        port=5678,
        suspend=True,
        stdout_to_server=True,
        stderr_to_server=True,
    )


def test_requirements_include_pycharm_debugger_dependency() -> None:
    requirements = Path("requirements.txt").read_text(encoding="utf-8").splitlines()

    assert any(line.startswith("pydevd-pycharm") for line in requirements)


def test_attach_pycharm_debugger_calls_snake_case_pydevd_settrace() -> None:
    calls: list[dict[str, object]] = []

    class FakePydevd:
        @staticmethod
        def settrace(
            host: str,
            *,
            port: int,
            suspend: bool,
            stdout_to_server: bool,
            stderr_to_server: bool,
            trace_only_current_thread: bool,
            patch_multiprocessing: bool,
        ) -> None:
            calls.append(
                {
                    "host": host,
                    "port": port,
                    "suspend": suspend,
                    "stdout_to_server": stdout_to_server,
                    "stderr_to_server": stderr_to_server,
                    "trace_only_current_thread": trace_only_current_thread,
                    "patch_multiprocessing": patch_multiprocessing,
                }
            )

    def fake_importer(name: str) -> object:
        assert name == "pydevd_pycharm"
        return FakePydevd

    attach_pycharm_debugger(
        PyCharmDebugSettings(
            host="192.0.2.10",
            port=12345,
            suspend=False,
            stdout_to_server=False,
            stderr_to_server=True,
        ),
        importer=fake_importer,
    )

    assert calls == [
        {
            "host": "192.0.2.10",
            "port": 12345,
            "suspend": False,
            "stdout_to_server": False,
            "stderr_to_server": True,
            "trace_only_current_thread": False,
            "patch_multiprocessing": True,
        }
    ]


def test_attach_pycharm_debugger_keeps_camel_case_pydevd_compatibility() -> None:
    calls: list[dict[str, object]] = []

    class FakePydevd:
        @staticmethod
        def settrace(
            host: str,
            *,
            port: int,
            suspend: bool,
            stdoutToServer: bool,
            stderrToServer: bool,
            trace_only_current_thread: bool,
            patch_multiprocessing: bool,
        ) -> None:
            calls.append(
                {
                    "host": host,
                    "port": port,
                    "suspend": suspend,
                    "stdoutToServer": stdoutToServer,
                    "stderrToServer": stderrToServer,
                    "trace_only_current_thread": trace_only_current_thread,
                    "patch_multiprocessing": patch_multiprocessing,
                }
            )

    attach_pycharm_debugger(
        PyCharmDebugSettings(
            host="127.0.0.1",
            port=5678,
            suspend=True,
            stdout_to_server=True,
            stderr_to_server=False,
        ),
        importer=lambda name: FakePydevd,
    )

    assert calls == [
        {
            "host": "127.0.0.1",
            "port": 5678,
            "suspend": True,
            "stdoutToServer": True,
            "stderrToServer": False,
            "trace_only_current_thread": False,
            "patch_multiprocessing": True,
        }
    ]
