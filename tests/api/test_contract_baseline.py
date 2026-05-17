from app.main import create_app
from tests.api.asgi_client import call_json


FORBIDDEN_PROBABILITY_FIELDS = {
    "pass_probability",
    "offer_probability",
    "admission_probability",
    "pass_rate_percent",
}


def test_contract_baseline_endpoint_returns_reusable_envelope() -> None:
    status_code, body = call_json(create_app(), "/api/v1/contract-baseline")

    assert status_code == 200
    assert body["request_id"].startswith("trace_")
    assert body["trace_id"].startswith("trace_")
    assert body["status"] == "success"
    assert body["resource_type"] == "contract_baseline"
    assert body["data"]["api_version"] == "v1"
    assert body["data"]["contract_baseline_status"] == "ready_for_f5_m1"
    assert body["data"]["fake_llm_status"] == "deterministic_fake_only"
    assert "no_provider_payload_or_completion_exposure" in body["data"]["safety_boundaries"]


def test_contract_baseline_does_not_expose_exact_probability_fields() -> None:
    _, body = call_json(create_app(), "/api/v1/contract-baseline")

    seen_keys = _collect_keys(body)

    assert FORBIDDEN_PROBABILITY_FIELDS.isdisjoint(seen_keys)


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for item in value.values():
            keys.update(_collect_keys(item))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_collect_keys(item))
        return keys
    return set()
