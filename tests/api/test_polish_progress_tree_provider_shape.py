from app.application.llm.types import LlmTransportResult
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
)
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from tests.api.test_polish_api import (
    ACTOR_A,
    OWNER_A,
    _create_ready_polish_session,
    _isolated_polish_app,
    _leaf_nodes,
    _quality_first_payload,
    _quality_first_standard_nodes,
    _seed_progress_snippet_sources,
    _session_factory,
)
from tests.fakes.llm_transport import FakeLlmTransport


class _QualityFirstChineseCategoryProviderTransport(FakeLlmTransport):
    def generate(self, request):
        if request.task_type != POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE:
            return super().generate(request)
        standard_nodes = _quality_first_standard_nodes()
        payload = _quality_first_payload(standard_nodes)
        resume_nodes = [
            node for node in standard_nodes if node["category"] == "resume_deep_dive"
        ]
        jd_nodes = [
            node for node in standard_nodes if node["category"] == "jd_gap_learning"
        ]
        payload.update(
            {
                "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
                "task_type": POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
                "model_name": "deepseek-v4-pro",
                "menu_categories": [
                    {
                        "category": "深度打磨类",
                        "display_category_title": "深度打磨类",
                        "nodes": resume_nodes[:2],
                    },
                    {
                        "category": "简历深挖",
                        "display_category_title": "简历深挖",
                        "nodes": resume_nodes[2:],
                    },
                    {
                        "category": "补齐学习类",
                        "display_category_title": "补齐学习类",
                        "nodes": jd_nodes[:1],
                    },
                    {
                        "category": "岗位缺口核验",
                        "display_category_title": "岗位缺口核验",
                        "nodes": jd_nodes[1:],
                    },
                ],
            }
        )
        return LlmTransportResult(
            result=payload,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_quality_first_chinese_categories",),
            evidence_refs=(),
        )


def test_quality_first_accepts_real_provider_category_aliases_without_fallback() -> None:
    session_factory = _session_factory()
    binding_id = _seed_progress_snippet_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(
        session_factory,
        ACTOR_A,
        llm_transport=_QualityFirstChineseCategoryProviderTransport(),
    )

    status_code, body = _create_ready_polish_session(
        app,
        {"resume_job_binding_id": binding_id, "topic_id": "topic_technical_depth"},
    )

    assert status_code == 200
    session_data = body["data"]
    assert session_data["progress_tree_status"] == "ready"
    leaves = _leaf_nodes(session_data["progress_tree_plan"]["nodes"])
    metadata = session_data["progress_tree_plan"]["v2_metadata"]
    assert leaves
    assert {node["category"] for node in leaves} >= {
        "resume_deep_dive",
        "jd_gap_learning",
    }
    assert "quality_first_category_alias_normalized" in metadata["low_confidence_flags"]
    assert "provider_payload" not in str(body)
    assert "deepseek-v4-pro" not in str(body)
    assert POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID == metadata["planner_schema_id"]
