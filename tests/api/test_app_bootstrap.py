from app.main import ApiSettings, _startup_log_lines, create_app, get_settings
from tests.api.asgi_client import call_json


def test_create_app_and_health_endpoint_work() -> None:
    app = create_app()

    status_code, body = call_json(app, "/api/v1/health")

    assert status_code == 200
    assert body == {"status": "ok"}


def test_create_app_registers_auth_runtime() -> None:
    app = create_app()

    assert app.state.auth_runtime.cookie_policy.name == "aifi_session"
    assert app.state.auth_runtime.cookie_policy.path == "/api/v1"


def test_api_debug_env_enables_fastapi_debug(monkeypatch) -> None:
    monkeypatch.setenv("API_DEBUG", "true")

    app = create_app()

    assert app.debug is True


def test_api_port_env_configures_startup_settings(monkeypatch) -> None:
    monkeypatch.setenv("API_PORT", "9100")

    settings = get_settings()

    assert settings.port == 9100


def test_startup_log_reports_debug_mode() -> None:
    lines = _startup_log_lines(ApiSettings(debug=True))

    assert "API debug: enabled" in lines
