from __future__ import annotations

import sys

try:
    from scripts.dev.dev_env import ensure_api_import_path, load_project_dotenv
except ModuleNotFoundError:
    from dev_env import ensure_api_import_path, load_project_dotenv

load_project_dotenv()
ensure_api_import_path()

from app.application.auth.commands import LoginCommand
from app.infrastructure.env_reader import EnvReader
from app.infrastructure.security.auth import build_auth_runtime_from_env


def main() -> int:
    env = EnvReader()
    seed_enabled = env.bool("API_AUTH_DEV_USER_ENABLED", _default_seed_enabled(env))
    identifier = env.str("API_AUTH_DEV_USER_IDENTIFIER", "developer")

    if not seed_enabled:
        print("[dev] auth dev user seed disabled")
        return 0

    password = env.optional("API_AUTH_DEV_USER_PASSWORD")
    if password is None:
        print("[dev] API_AUTH_DEV_USER_PASSWORD is required when dev auth seed is enabled", file=sys.stderr)
        return 2

    runtime = build_auth_runtime_from_env()
    result = runtime.auth_service.login(LoginCommand(identifier=identifier, password=password))
    if result is None:
        print(f"[dev] auth dev user preflight failed for identifier {identifier!r}", file=sys.stderr)
        return 1

    print(f"[dev] auth dev user ready: {identifier}")
    return 0


def _default_seed_enabled(env: EnvReader) -> bool:
    return (env.first_of("API_AUTH_ENV", "API_ENV") or "local").lower() in {
        "local",
        "test",
        "development",
        "dev",
    }


if __name__ == "__main__":
    raise SystemExit(main())
