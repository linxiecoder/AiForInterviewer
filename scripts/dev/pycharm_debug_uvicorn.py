"""Start the API under PyCharm remote debugging.

This wrapper is used by `npm run dev debug`. It connects the current Python
process to a PyCharm Python Debug Server before starting uvicorn, so breakpoints
are hit in the API worker process.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import importlib
import inspect
import os
import sys

import uvicorn

try:
    from scripts.dev.dev_env import (
        apply_api_run_settings_to_env,
        ensure_api_import_path,
        load_project_dotenv,
        resolve_api_run_settings,
    )
except ModuleNotFoundError:
    from dev_env import (
        apply_api_run_settings_to_env,
        ensure_api_import_path,
        load_project_dotenv,
        resolve_api_run_settings,
    )


DEFAULT_DEBUG_HOST = "127.0.0.1"
DEFAULT_DEBUG_PORT = 5678
TRUTHY_VALUES = {"1", "true", "yes", "y", "on"}
FALSY_VALUES = {"0", "false", "no", "n", "off"}


@dataclass(frozen=True)
class PyCharmDebugSettings:
    host: str
    port: int
    suspend: bool
    stdout_to_server: bool
    stderr_to_server: bool


def resolve_pycharm_debug_settings(environ: Mapping[str, str] | None = None) -> PyCharmDebugSettings:
    values = environ if environ is not None else os.environ
    return PyCharmDebugSettings(
        host=_env_text(values, "PYCHARM_DEBUG_HOST", DEFAULT_DEBUG_HOST),
        port=_env_int(values, "PYCHARM_DEBUG_PORT", DEFAULT_DEBUG_PORT),
        suspend=_env_bool(values, "PYCHARM_DEBUG_SUSPEND", True),
        stdout_to_server=_env_bool(values, "PYCHARM_DEBUG_STDOUT", True),
        stderr_to_server=_env_bool(values, "PYCHARM_DEBUG_STDERR", True),
    )


def attach_pycharm_debugger(
    settings: PyCharmDebugSettings,
    *,
    importer: Callable[[str], object] = importlib.import_module,
) -> None:
    try:
        pydevd_pycharm = importer("pydevd_pycharm")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pydevd-pycharm is not installed. Run `python3 -m pip install -r requirements.txt` "
            "inside the project virtualenv, then start PyCharm's Python Debug Server first."
        ) from exc

    settrace = pydevd_pycharm.settrace  # type: ignore[attr-defined]
    settrace(
        settings.host,
        **_settrace_kwargs(settrace, settings),
    )


def main() -> None:
    load_project_dotenv()
    api_settings = resolve_api_run_settings()
    apply_api_run_settings_to_env(api_settings)
    ensure_api_import_path()
    settings = resolve_pycharm_debug_settings()
    print(
        "[dev] connecting PyCharm debug server at "
        f"{settings.host}:{settings.port} (suspend={str(settings.suspend).lower()})",
        flush=True,
    )
    attach_pycharm_debugger(settings)
    uvicorn.run(
        "app.main:app",
        host=api_settings.host,
        port=api_settings.port,
        log_level="debug",
        reload=False,
    )


def _settrace_kwargs(settrace: Callable[..., object], settings: PyCharmDebugSettings) -> dict[str, object]:
    parameters = inspect.signature(settrace).parameters
    stdout_key = "stdout_to_server" if "stdout_to_server" in parameters else "stdoutToServer"
    stderr_key = "stderr_to_server" if "stderr_to_server" in parameters else "stderrToServer"
    return {
        "port": settings.port,
        "suspend": settings.suspend,
        stdout_key: settings.stdout_to_server,
        stderr_key: settings.stderr_to_server,
        "trace_only_current_thread": False,
        "patch_multiprocessing": True,
    }


def _env_text(values: Mapping[str, str], name: str, default: str) -> str:
    raw = values.get(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return stripped or default


def _env_int(values: Mapping[str, str], name: str, default: int) -> int:
    raw = values.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {raw!r}.") from exc


def _env_bool(values: Mapping[str, str], name: str, default: bool) -> bool:
    raw = values.get(name)
    if raw is None or not raw.strip():
        return default
    normalized = raw.strip().lower()
    if normalized in TRUTHY_VALUES:
        return True
    if normalized in FALSY_VALUES:
        return False
    raise RuntimeError(f"{name} must be a boolean-like value, got {raw!r}.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"[dev] {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
