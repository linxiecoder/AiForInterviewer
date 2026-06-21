from __future__ import annotations

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


def main() -> None:
    load_project_dotenv()
    settings = resolve_api_run_settings()
    apply_api_run_settings_to_env(settings)
    ensure_api_import_path()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=True,
        reload=True,
        reload_dirs=["apps/api"],
    )


if __name__ == "__main__":
    main()
