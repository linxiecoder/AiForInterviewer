from app.main import create_app
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
