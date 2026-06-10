from __future__ import annotations

import json
from urllib.parse import quote

from sqlalchemy import delete, inspect, text

from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.infrastructure.db.models.asset import Asset, AssetVersion
from app.infrastructure.db.models.reference import UserConfirmation
from app.infrastructure.db.models.weakness import Weakness
from app.infrastructure.db.session import get_session_factory
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import create_app
from tests.api.asgi_client import call_json, call_json_response


USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "asset-user-b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"


def test_asset_list_detail_archive_and_owner_scope() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    other_cookie = _login_cookie(app, "asset-user-b", USER_B_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    _seed_asset(owner_id=owner_id, asset_id="asset_f5_m7_story")

    status_code, body = call_json(app, "/api/v1/assets", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["resource_type"] == "asset_list"
    assert [item["asset_id"] for item in body["data"]] == ["asset_f5_m7_story"]
    assert body["data"][0]["asset_type"] == "project_story"
    assert body["data"][0]["status"] == "asset_confirmed"
    assert body["data"][0]["source_refs"] == [{"resource_type": "review", "resource_id": "review_001"}]

    status_code, body = call_json(
        app,
        "/api/v1/assets/asset_f5_m7_story",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "asset_detail"
    assert body["data"]["content"] == "用 STAR 结构讲清楚搜索性能优化。"
    assert body["data"]["versions"][0]["version_number"] == 1
    assert body["data"]["evidence_refs"] == [{"resource_type": "answer", "resource_id": "answer_001"}]

    status_code, body = call_json(
        app,
        "/api/v1/assets/asset_f5_m7_story/archive",
        "POST",
        json_body={},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["status"] == "asset_archived"
    assert body["data"]["user_confirmation_ref"]["resource_type"] == "user_confirmation"

    status_code, body = call_json(
        app,
        "/api/v1/assets/asset_f5_m7_story/unarchive",
        "POST",
        json_body={},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["status"] == "asset_confirmed"

    status_code, body = call_json(
        app,
        "/api/v1/assets/asset_f5_m7_story",
        headers={"cookie": other_cookie},
    )
    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_asset_filters_reject_unknown_values() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)

    for query in ("asset_type=unknown", "asset_type=", "status=ASSET_CONFIRMED"):
        status_code, body = call_json(
            app,
            f"/api/v1/assets?{query}",
            headers={"cookie": owner_cookie},
        )

        assert status_code == 422
        assert body["error"]["code"] == "validation_failed"


def test_asset_search_matches_owned_title_summary_content_and_source_only() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    other_cookie = _login_cookie(app, "asset-user-b", USER_B_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    _seed_asset(owner_id=owner_id, asset_id="asset_owned_story")
    _seed_asset(
        owner_id=owner_id,
        asset_id="asset_owned_note",
        title="Redis 缓存击穿复盘",
        summary="说明缓存雪崩和降级策略。",
        content="包含 Redis 热点 key、互斥锁和限流方案。",
        asset_type="technical_note",
        source_ref_id="review_redis",
    )
    _seed_asset(
        owner_id=USER_B_ID,
        asset_id="asset_other_story",
        title="Redis 他人资产",
        summary="不应被 owner A 搜索到。",
        content="Redis owner scope test",
        asset_type="technical_note",
    )

    status_code, body = call_json(app, "/api/v1/assets?q= redis ", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert [item["asset_id"] for item in body["data"]] == ["asset_owned_note"]

    status_code, body = call_json(app, "/api/v1/assets?q=review_001", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert [item["asset_id"] for item in body["data"]] == ["asset_owned_story"]

    status_code, body = call_json(app, "/api/v1/assets?q=Redis", headers={"cookie": other_cookie})
    assert status_code == 200
    assert [item["asset_id"] for item in body["data"]] == ["asset_other_story"]


def test_create_asset_persists_asset_version_rag_chunks_and_calls_embedding_provider() -> None:
    embedding_provider = FakeEmbeddingProvider(dimension=4)
    app = _app_with_two_users(embedding_provider=embedding_provider)
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/assets",
        "POST",
        json_body={
            "title": "支付削峰项目表达",
            "asset_type": "project_story",
            "summary": "用于项目深挖的 STAR 素材。",
            "content": (
                "# 项目经历\n\n"
                "支付系统在大促峰值下出现队列堆积，我负责设计削峰方案。\n\n"
                "## 技术方案\n\n"
                "- 使用 Redis 令牌桶控制入口流量。\n"
                "- 用消息队列异步化库存扣减。\n\n"
                "```python\n"
                "def reserve(order_id):\n"
                "    return order_id\n"
                "```\n\n"
                "最终 P99 延迟下降 35%，失败率保持在 0.1% 以下。"
            ),
        },
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["resource_type"] == "asset_detail"
    asset = body["data"]
    assert asset["owner_id"] == owner_id
    assert asset["status"] == "asset_confirmed"
    assert asset["asset_type"] == "project_story"
    assert asset["title"] == "支付削峰项目表达"
    assert asset["versions"][0]["version_number"] == 1
    assert asset["versions"][0]["content"].startswith("# 项目经历")

    rag_documents, rag_chunks = _rag_counts_for_asset(asset["asset_id"])
    assert rag_documents == 1
    assert rag_chunks >= 2
    assert len(embedding_provider.calls) == 1
    assert len(embedding_provider.calls[0]) == rag_chunks
    assert any("项目经历 > 技术方案" in value for value in embedding_provider.calls[0])

    chunk_rows = _rag_chunk_rows(asset["asset_id"])
    assert {row["owner_id"] for row in chunk_rows} == {owner_id}
    assert {row["embedding_model"] for row in chunk_rows} == {"fake-embedding-v1"}
    assert {row["embedding_dimension"] for row in chunk_rows} == {4}
    assert any(row["heading_path"] == ["项目经历", "技术方案"] for row in chunk_rows)
    assert any("```python" in row["content"] and "```" in row["content"].rstrip() for row in chunk_rows)
    assert len({row["char_count"] for row in chunk_rows}) > 1


def test_create_asset_rejects_invalid_or_blank_payloads() -> None:
    app = _app_with_two_users(embedding_provider=FakeEmbeddingProvider(dimension=4))
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)

    invalid_payloads = [
        {"title": "有效标题", "asset_type": "unknown", "content": "有效内容"},
        {"title": "   ", "asset_type": "project_story", "content": "有效内容"},
        {"title": "有效标题", "asset_type": "project_story", "content": "   "},
    ]

    for payload in invalid_payloads:
        status_code, body = call_json(
            app,
            "/api/v1/assets",
            "POST",
            json_body=payload,
            headers={"cookie": owner_cookie},
        )

        assert status_code == 422
        assert body["error"]["code"] == "validation_failed"


def test_create_asset_fails_closed_when_embedding_dimension_mismatches() -> None:
    app = _app_with_two_users(embedding_provider=FakeEmbeddingProvider(dimension=4, actual_vector_size=3))
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/assets",
        "POST",
        json_body={
            "title": "维度错误资产",
            "asset_type": "project_story",
            "content": "这段内容会触发 fake embedding 维度不一致。",
        },
        headers={"cookie": owner_cookie},
    )

    assert status_code == 502
    assert body["error"]["code"] == "provider_unavailable"
    assert _asset_count_by_title("维度错误资产") == 0
    assert _table_count("assets") == 0
    assert _table_count("asset_versions") == 0
    assert _rag_total_counts() == (0, 0)


def test_create_asset_rolls_back_when_rag_chunk_insert_fails() -> None:
    app = _app_with_two_users(embedding_provider=BadEmbeddingProvider())
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/assets",
        "POST",
        json_body={
            "title": "Chunk 入库失败资产",
            "asset_type": "project_story",
            "content": "这段内容会在 rag chunk embedding 绑定阶段失败。",
        },
        headers={"cookie": owner_cookie},
    )

    assert status_code == 500
    assert body["error"]["code"] == "internal_error"
    assert _asset_count_by_title("Chunk 入库失败资产") == 0
    assert _table_count("assets") == 0
    assert _table_count("asset_versions") == 0
    assert _rag_total_counts() == (0, 0)


def test_asset_archive_rejects_unsupported_status_transition() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)
    _seed_asset(owner_id=owner_id, asset_id="asset_disabled_story", status="disabled")

    status_code, body = call_json(
        app,
        "/api/v1/assets/asset_disabled_story/archive",
        "POST",
        json_body={},
        headers={"cookie": owner_cookie},
    )

    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"


def test_asset_delete_soft_deletes_without_physical_delete() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    other_cookie = _login_cookie(app, "asset-user-b", USER_B_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)
    _seed_asset(owner_id=owner_id, asset_id="asset_soft_delete_story")

    other_status, other_body = call_json(
        app,
        "/api/v1/assets/asset_soft_delete_story",
        "DELETE",
        headers={"cookie": other_cookie},
    )
    assert other_status == 404
    assert other_body["error"]["code"] == "not_found_or_inaccessible"
    assert _record_status("assets", "asset_soft_delete_story") == "asset_confirmed"

    status_code, body = call_json(
        app,
        "/api/v1/assets/asset_soft_delete_story",
        "DELETE",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["status"] == "deleted"

    list_status, list_body = call_json(app, "/api/v1/assets", headers={"cookie": owner_cookie})
    assert list_status == 200
    assert list_body["data"] == []

    detail_status, detail_body = call_json(
        app,
        "/api/v1/assets/asset_soft_delete_story",
        headers={"cookie": owner_cookie},
    )
    assert detail_status == 404
    assert detail_body["error"]["code"] == "not_found_or_inaccessible"

    assert _record_status("assets", "asset_soft_delete_story") == "deleted"
    assert _record_count("assets", "asset_soft_delete_story") == 1
    assert _record_count("asset_versions", "asset_soft_delete_story_ver_001") == 1

    repeat_status, repeat_body = call_json(
        app,
        "/api/v1/assets/asset_soft_delete_story",
        "DELETE",
        headers={"cookie": owner_cookie},
    )
    assert repeat_status == 404
    assert repeat_body["error"]["code"] == "not_found_or_inaccessible"


def test_weakness_list_detail_status_and_owner_scope() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    other_cookie = _login_cookie(app, "asset-user-b", USER_B_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    _seed_weakness(owner_id=owner_id, weakness_id="weak_communication_depth")

    status_code, body = call_json(
        app,
        "/api/v1/weaknesses?status=weakness_confirmed",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "weakness_list"
    assert [item["weakness_id"] for item in body["data"]] == ["weak_communication_depth"]
    assert body["data"][0]["severity"] == "high"
    assert body["data"][0]["suggested_training_actions"] == ["enter_polish_mode", "mark_for_training"]

    status_code, body = call_json(
        app,
        "/api/v1/weaknesses/weak_communication_depth",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "weakness_detail"
    assert body["data"]["source_refs"] == [{"resource_type": "report", "resource_id": "report_001"}]
    assert body["data"]["evidence_refs"] == [{"resource_type": "feedback", "resource_id": "feedback_001"}]
    assert body["data"]["related_refs"]["sessions"] == [{"resource_type": "interview_session", "resource_id": "session_001"}]

    status_code, body = call_json(
        app,
        "/api/v1/weaknesses/weak_communication_depth/status",
        "POST",
        json_body={"status": "resolved"},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["status"] == "resolved"
    assert body["data"]["user_confirmation_ref"]["resource_type"] == "user_confirmation"

    status_code, body = call_json(
        app,
        "/api/v1/weaknesses/weak_communication_depth/status",
        "POST",
        json_body={"status": "unsupported"},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"

    status_code, body = call_json(
        app,
        "/api/v1/weaknesses/weak_communication_depth",
        headers={"cookie": other_cookie},
    )
    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_weakness_delete_soft_deletes_without_physical_delete() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    other_cookie = _login_cookie(app, "asset-user-b", USER_B_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)
    _seed_weakness(owner_id=owner_id, weakness_id="weak_soft_delete")

    other_status, other_body = call_json(
        app,
        "/api/v1/weaknesses/weak_soft_delete",
        "DELETE",
        headers={"cookie": other_cookie},
    )
    assert other_status == 404
    assert other_body["error"]["code"] == "not_found_or_inaccessible"
    assert _record_status("weaknesses", "weak_soft_delete") == "weakness_confirmed"

    status_code, body = call_json(
        app,
        "/api/v1/weaknesses/weak_soft_delete",
        "DELETE",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["status"] == "deleted"
    assert body["data"]["user_confirmation_ref"]["resource_type"] == "user_confirmation"

    list_status, list_body = call_json(app, "/api/v1/weaknesses", headers={"cookie": owner_cookie})
    assert list_status == 200
    assert list_body["data"] == []

    detail_status, detail_body = call_json(
        app,
        "/api/v1/weaknesses/weak_soft_delete",
        headers={"cookie": owner_cookie},
    )
    assert detail_status == 404
    assert detail_body["error"]["code"] == "not_found_or_inaccessible"

    assert _record_status("weaknesses", "weak_soft_delete") == "deleted"
    assert _record_count("weaknesses", "weak_soft_delete") == 1

    repeat_status, repeat_body = call_json(
        app,
        "/api/v1/weaknesses/weak_soft_delete",
        "DELETE",
        headers={"cookie": owner_cookie},
    )
    assert repeat_status == 404
    assert repeat_body["error"]["code"] == "not_found_or_inaccessible"


def test_weakness_search_matches_owned_title_summary_evidence_dimension_and_actions() -> None:
    app = _app_with_two_users()
    _reset_asset_weakness_tables()
    owner_cookie = _login_cookie(app, "asset-user-a@example.com", USER_A_PASSWORD)
    other_cookie = _login_cookie(app, "asset-user-b", USER_B_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    _seed_weakness(owner_id=owner_id, weakness_id="weak_communication_depth")
    _seed_weakness(
        owner_id=owner_id,
        weakness_id="weak_system_design",
        title="系统设计容量估算薄弱",
        summary="需要加强容量估算、限流和降级推导。",
        severity="medium",
        evidence_label="容量估算证据",
        dimension="system_design",
    )
    _seed_weakness(
        owner_id=USER_B_ID,
        weakness_id="weak_other_system_design",
        title="系统设计他人薄弱项",
        summary="不应被 owner A 搜索到。",
        severity="medium",
        evidence_label="容量估算证据",
        dimension="system_design",
    )

    status_code, body = call_json(app, f"/api/v1/weaknesses?q={quote(' 容量估算 ')}", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert [item["weakness_id"] for item in body["data"]] == ["weak_system_design"]

    status_code, body = call_json(app, "/api/v1/weaknesses?q=communication_depth", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert [item["weakness_id"] for item in body["data"]] == ["weak_communication_depth"]

    status_code, body = call_json(app, "/api/v1/weaknesses?q=enter_polish_mode", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert {item["weakness_id"] for item in body["data"]} == {"weak_communication_depth", "weak_system_design"}

    status_code, body = call_json(app, f"/api/v1/weaknesses?q={quote('容量估算')}", headers={"cookie": other_cookie})
    assert status_code == 200
    assert [item["weakness_id"] for item in body["data"]] == ["weak_other_system_design"]


def _app_with_two_users(*, embedding_provider=None):
    runtime = build_auth_runtime(
        AuthRuntimeSettings(
            dev_user_password=USER_A_PASSWORD,
            dev_user_identifier="asset-user-a@example.com",
            dev_user_email="asset-user-a@example.com",
            dev_username="asset-user-a",
            dev_display_name="Asset User A",
            seed_dev_user=True,
        ),
        cookie_path="/api/v1",
    )
    runtime.user_store.add_user(
        user_id=USER_B_ID,
        email="asset-user-b@example.com",
        username="asset-user-b",
        display_name="Asset User B",
        password_hash=Pbkdf2PasswordHasher().hash_password(USER_B_PASSWORD),
    )
    app = create_app(auth_runtime=runtime, initialize_schema=True)
    if embedding_provider is not None:
        app.state.embedding_provider = embedding_provider
    return app


def _login_cookie(app, identifier: str, password: str) -> str:
    status_code, _body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": identifier, "password": password},
    )
    assert status_code == 200
    values = headers["set-cookie"]
    assert len(values) == 1
    token = values[0].split("aifi_session=", 1)[1].split(";", 1)[0]
    return f"aifi_session={token}"


def _current_owner_id(app, cookie: str) -> str:
    status_code, body = call_json(app, "/api/v1/auth/me", headers={"cookie": cookie})
    assert status_code == 200
    return body["data"]["owner_id"]


def _reset_asset_weakness_tables() -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        session.execute(delete(UserConfirmation))
        _delete_table_if_exists(session, "rag_chunks")
        _delete_table_if_exists(session, "rag_documents")
        session.execute(delete(AssetVersion))
        session.execute(delete(Asset))
        session.execute(delete(Weakness))
        session.commit()


def _seed_asset(
    *,
    owner_id: str,
    asset_id: str,
    status: str = "asset_confirmed",
    title: str = "搜索性能优化项目表达",
    summary: str = "可复用的项目经历表达资产。",
    content: str = "用 STAR 结构讲清楚搜索性能优化。",
    asset_type: str = "project_story",
    source_ref_id: str = "review_001",
) -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        session.add(
            Asset(
                id=asset_id,
                owner_id=owner_id,
                actor_id=owner_id,
                record_version=1,
                status=status,
                trace_ref_ids=["trace_asset_001"],
                evidence_ref_ids=["answer_001"],
                normalized_title="search-performance-story",
                asset_type=asset_type,
                title=title,
                summary=summary,
                content=content,
                current_version_id=f"{asset_id}_ver_001",
                source_refs_json=[{"resource_type": "review", "resource_id": source_ref_id}],
                evidence_refs_json=[{"resource_type": "answer", "resource_id": "answer_001"}],
                trace_refs_json=[{"resource_type": "trace", "resource_id": "trace_asset_001"}],
                resume_version_ref_json={"resource_type": "resume", "resource_id": "resume_001", "version_id": "resv_001"},
                job_version_ref_json={"resource_type": "job", "resource_id": "job_001", "version_id": "jobv_001"},
                question_pattern="project_deep_dive",
                fact_source="user_confirmed_review",
            )
        )
        session.add(
            AssetVersion(
                id=f"{asset_id}_ver_001",
                owner_id=owner_id,
                actor_id=owner_id,
                record_version=1,
                status="current",
                trace_ref_ids=["trace_asset_001"],
                evidence_ref_ids=["answer_001"],
                asset_id=asset_id,
                version_number=1,
                content=content,
                edit_summary="首版归档",
                created_by_actor_id=owner_id,
                created_from_candidate_id="asset_candidate_001",
            )
        )
        session.commit()


def _seed_weakness(
    *,
    owner_id: str,
    weakness_id: str,
    title: str = "项目表达缺少取舍细节",
    summary: str = "回答能说明结果，但缺少技术取舍、指标和证据。",
    severity: str = "high",
    evidence_label: str | None = None,
    dimension: str = "communication_depth",
) -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        session.add(
            Weakness(
                id=weakness_id,
                owner_id=owner_id,
                actor_id=owner_id,
                record_version=1,
                status="weakness_confirmed",
                trace_ref_ids=["trace_weak_001"],
                evidence_ref_ids=["feedback_001"],
                normalized_title="communication-depth",
                title=title,
                summary=summary,
                severity_hint=severity,
                confidence_level="medium",
                source_refs_json=[{"resource_type": "report", "resource_id": "report_001"}],
                session_refs_json=[{"resource_type": "interview_session", "resource_id": "session_001"}],
                feedback_refs_json=[{"resource_type": "feedback", "resource_id": "feedback_001"}],
                question_refs_json=[{"resource_type": "question", "resource_id": "question_001"}],
                answer_refs_json=[{"resource_type": "answer", "resource_id": "answer_001"}],
                loss_point_refs_json=[{"dimension": dimension, "label": "表达深度不足"}],
                evidence_refs_json=[_evidence_ref(evidence_label)],
                trace_refs_json=[{"resource_type": "trace", "resource_id": "trace_weak_001"}],
                occurrence_count=2,
            )
        )
        session.commit()


def _rag_counts_for_asset(asset_id: str) -> tuple[int, int]:
    session_factory = get_session_factory()
    with session_factory() as session:
        documents = session.execute(
            text("SELECT COUNT(*) FROM rag_documents WHERE source_id = :asset_id"),
            {"asset_id": asset_id},
        ).scalar_one()
        chunks = session.execute(
            text("SELECT COUNT(*) FROM rag_chunks WHERE asset_id = :asset_id"),
            {"asset_id": asset_id},
        ).scalar_one()
    return int(documents), int(chunks)


def _rag_total_counts() -> tuple[int, int]:
    session_factory = get_session_factory()
    with session_factory() as session:
        documents = session.execute(text("SELECT COUNT(*) FROM rag_documents")).scalar_one()
        chunks = session.execute(text("SELECT COUNT(*) FROM rag_chunks")).scalar_one()
    return int(documents), int(chunks)


def _rag_chunk_rows(asset_id: str) -> list[dict]:
    session_factory = get_session_factory()
    with session_factory() as session:
        rows = session.execute(
            text(
                "SELECT owner_id, heading_path_json, content, char_count, embedding_model, embedding_dimension "
                "FROM rag_chunks WHERE asset_id = :asset_id ORDER BY chunk_index"
            ),
            {"asset_id": asset_id},
        ).mappings().all()
    return [
        {
            "owner_id": row["owner_id"],
            "heading_path": _json_value(row["heading_path_json"]),
            "content": row["content"],
            "char_count": row["char_count"],
            "embedding_model": row["embedding_model"],
            "embedding_dimension": row["embedding_dimension"],
        }
        for row in rows
    ]


def _asset_count_by_title(title: str) -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        return int(
            session.execute(
                text("SELECT COUNT(*) FROM assets WHERE title = :title"),
                {"title": title},
            ).scalar_one()
        )


def _record_count(table_name: str, record_id: str) -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        return int(
            session.execute(
                text(f"SELECT COUNT(*) FROM {table_name} WHERE id = :record_id"),
                {"record_id": record_id},
            ).scalar_one()
        )


def _table_count(table_name: str) -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        return int(session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one())


def _record_status(table_name: str, record_id: str) -> str | None:
    session_factory = get_session_factory()
    with session_factory() as session:
        return session.execute(
            text(f"SELECT status FROM {table_name} WHERE id = :record_id"),
            {"record_id": record_id},
        ).scalar_one_or_none()


def _evidence_ref(label: str | None) -> dict[str, str]:
    ref = {"resource_type": "feedback", "resource_id": "feedback_001"}
    if label is not None:
        ref["label"] = label
    return ref


def _json_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def _delete_table_if_exists(session, table_name: str) -> None:
    if table_name in inspect(session.bind).get_table_names():
        session.execute(text(f"DELETE FROM {table_name}"))


class FakeEmbeddingResult:
    def __init__(self, *, model: str, dimension: int, vectors: tuple[tuple[float, ...], ...]) -> None:
        self.model = model
        self.dimension = dimension
        self.vectors = vectors


class FakeEmbeddingProvider:
    def __init__(self, *, dimension: int, actual_vector_size: int | None = None) -> None:
        self.dimension = dimension
        self.actual_vector_size = actual_vector_size or dimension
        self.calls: list[tuple[str, ...]] = []

    def embed_texts(self, texts) -> FakeEmbeddingResult:
        values = tuple(str(text) for text in texts)
        self.calls.append(values)
        vectors = tuple(
            tuple(float(index + offset + 1) / 10 for offset in range(self.actual_vector_size))
            for index, _text in enumerate(values)
        )
        return FakeEmbeddingResult(model="fake-embedding-v1", dimension=self.dimension, vectors=vectors)


class BadEmbeddingProvider:
    def embed_texts(self, texts) -> FakeEmbeddingResult:
        values = tuple(str(text) for text in texts)
        vectors = tuple(("not-a-number", "not-a-number", "not-a-number") for _text in values)
        return FakeEmbeddingResult(model="bad-embedding-v1", dimension=3, vectors=vectors)
