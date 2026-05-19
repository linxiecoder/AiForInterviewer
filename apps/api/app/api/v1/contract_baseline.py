"""F5-M0 contract baseline endpoint."""

from fastapi import APIRouter

from app.api.envelope import success_envelope

router = APIRouter(prefix="/contract-baseline", tags=["contract-baseline"])


@router.get("")
async def get_contract_baseline():
    data = {
        "api_version": "v1",
        "enabled_modules": [
            "resumes",
            "jobs",
            "bindings",
            "ai_tasks",
            "scoring",
            "polish",
            "pressure",
            "reports",
            "reviews",
            "assets",
            "weaknesses",
            "training",
        ],
        "ddd_layer_status": {
            "api": "auth_foundation_ready",
            "application": "auth_foundation_ready",
            "domain": "auth_foundation_ready",
            "infrastructure": "auth_in_memory_baseline",
            "schemas": "contract_baseline_ready",
            "shared": "low_coupling_helpers_only",
        },
        "auth_baseline_status": "in_memory_cookie_session_ready",
        "contract_baseline_status": "ready_for_f5_m1",
        "fake_llm_status": "deterministic_fake_only",
        "f5_m0_status": "implemented",
        "safety_boundaries": [
            "no_file_export_or_download",
            "no_file_upload_parsing",
            "no_exact_probability_fields",
            "no_provider_payload_or_completion_exposure",
            "no_system_prompt_exposure",
            "no_hidden_scoring_rules_exposure",
            "candidate_and_suggestion_are_not_formal_objects",
        ],
    }
    return success_envelope(resource_type="contract_baseline", data=data)
