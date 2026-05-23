from pathlib import Path

from scripts.dev.pycharm_debug_uvicorn import (
    PyCharmDebugSettings,
    attach_pycharm_debugger,
    resolve_pycharm_debug_settings,
)


def test_start_api_debug_uses_pycharm_wrapper_without_uvicorn_reload() -> None:
    script = Path("scripts/dev/start-api.sh").read_text(encoding="utf-8")

    assert "exec .venv/bin/python scripts/dev/pycharm_debug_uvicorn.py" in script
    assert "exec .venv/bin/python -m uvicorn" in script
    debug_exec_index = script.index("exec .venv/bin/python scripts/dev/pycharm_debug_uvicorn.py")
    normal_exec_index = script.index("exec .venv/bin/python -m uvicorn")
    debug_branch_start = script.rindex('if [ "$MODE" = "debug" ]; then', 0, debug_exec_index)
    debug_branch = script[debug_branch_start:debug_exec_index]
    assert debug_exec_index < normal_exec_index
    assert "--reload" not in debug_branch


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
