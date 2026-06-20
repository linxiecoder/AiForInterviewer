from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
API_APP_DIR = ROOT_DIR / "apps" / "api"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8001


@dataclass(frozen=True)
class ApiRunSettings:
    host: str
    port: int


def ensure_api_import_path() -> None:
    api_path = str(API_APP_DIR)
    if api_path not in sys.path:
        sys.path.insert(0, api_path)

    existing = os.environ.get("PYTHONPATH")
    if existing:
        paths = existing.split(os.pathsep)
        if api_path not in paths:
            os.environ["PYTHONPATH"] = os.pathsep.join([api_path, existing])
    else:
        os.environ["PYTHONPATH"] = api_path


def load_project_dotenv(*, override: bool = False) -> None:
    dotenv_path = ROOT_DIR / ".env"
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_dotenv_assignment(raw_line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value


def _parse_dotenv_assignment(raw_line: str) -> tuple[str, str] | None:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None

    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()

    key, value = stripped.split("=", maxsplit=1)
    key = key.strip()
    if not key:
        return None

    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def resolve_api_run_settings(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    *,
    default_host: str = DEFAULT_API_HOST,
    default_port: int = DEFAULT_API_PORT,
) -> ApiRunSettings:
    values = environ if environ is not None else os.environ
    parser = argparse.ArgumentParser(description="Start the local API dev server.")
    parser.add_argument("--host", default=_env_text(values, "API_HOST", default_host))
    parser.add_argument("--port", type=int, default=_env_int(values, "API_PORT", default_port))
    args = parser.parse_args(argv)
    return ApiRunSettings(host=args.host, port=args.port)


def apply_api_run_settings_to_env(settings: ApiRunSettings) -> None:
    os.environ["API_HOST"] = settings.host
    os.environ["API_PORT"] = str(settings.port)


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
    except ValueError:
        return default
