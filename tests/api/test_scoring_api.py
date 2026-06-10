from __future__ import annotations

import pytest

from app.application.scoring.commands import CreateScoreResultCommand
from app.application.scoring.use_cases import ScoringUseCases
from app.domain.scoring.policies import CANONICAL_RUBRIC_VERSION, ScoringPolicy
from app.infrastructure.db.repositories.scoring import SqlAlchemyScoringRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import create_app
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from tests.api.asgi_client import call_json, call_json_response


USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"
USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "scoring-user-b@example.com")


def test_scoring_policy_validates_canonical_rubric_and_derives_bottleneck_action() -> None:
    dimensions = _dimensions(
        substance=80,
        structure=72,
        relevance=61,
        credibility=91,
        differentiation=61,
    )

    validated = ScoringPolicy.validate_dimensions(
        rubric_version=CANONICAL_RUBRIC_VERSION,
        dimensions=dimensions,
    )
    overall_score = ScoringPolicy.compute_overall_score(validated)
    primary_bottleneck = ScoringPolicy.select_primary_bottleneck(validated)
    next_action_type = ScoringPolicy.derive_next_action_type(
        target_type="mock_turn_answer",
        target_parent_type="mock_session",
        source_module="mock_interview",
        primary_bottleneck=primary_bottleneck,
    )

    assert overall_score == 73
    assert primary_bottleneck == "relevance"
    assert next_action_type == "mock_reentry_relevance"
    assert "training" not in next_action_type


def test_scoring_usecase_repository_persists_mock_turn_answer_parent_contract() -> None:
    session_factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=session_factory)
    use_cases = ScoringUseCases(repository=SqlAlchemyScoringRepository(session_factory))

    result = use_cases.create(
        CreateScoreResultCommand(
            owner_id="owner_scoring_repo",
            actor_id="actor_scoring_repo",
            score_type="polish_answer",
            target_type="mock_turn_answer",
            target_id="turn_repo_001",
            target_parent_type="mock_session",
            target_parent_id="sess_repo_001",
            source_module="mock_interview",
            source_event="answer_submitted",
            rubric_version=CANONICAL_RUBRIC_VERSION,
            dimensions=_dimensions(
                substance=84,
                structure=76,
                relevance=66,
                credibility=88,
                differentiation=66,
            ),
            evidence_links=({"resource_type": "mock_turn_answer", "resource_id": "turn_repo_001"},),
        )
    )

    assert result.is_success
    created = result.value
    assert created is not None
    assert created["overall_score"] == 76
    assert created["target_type"] == "mock_turn_answer"
    assert created["target_parent_type"] == "mock_session"
    assert created["target_parent_id"] == "sess_repo_001"
    assert created["primary_bottleneck"] == "relevance"
    assert created["next_action_type"] == "mock_reentry_relevance"

    listed = use_cases.list_for_target_parent(
        owner_id="owner_scoring_repo",
        target_parent_type="mock_session",
        target_parent_id="sess_repo_001",
    )
    assert listed.is_success
    assert [item["score_result_id"] for item in listed.value or ()] == [created["score_result_id"]]


def test_create_get_and_list_score_results_for_mock_turn_answer_owner_scoped() -> None:
    app = _app_with_two_users()
    owner_a_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "scoring-user-b@example.com", USER_B_PASSWORD)

    first = _create_score_result(
        app,
        owner_a_cookie,
        target_id="turn_mock_001",
        target_parent_id="sess_mock_001",
        dimensions=_dimensions(
            substance=82,
            structure=72,
            relevance=62,
            credibility=88,
            differentiation=62,
        ),
    )
    second = _create_score_result(
        app,
        owner_a_cookie,
        target_id="turn_mock_002",
        target_parent_id="sess_mock_001",
        dimensions=_dimensions(
            substance=78,
            structure=70,
            relevance=64,
            credibility=84,
            differentiation=64,
        ),
    )

    assert first["overall_score"] == 73
    assert first["score_value"] == 73
    assert first["rubric_version"] == CANONICAL_RUBRIC_VERSION
    assert [item["dimension_key"] for item in first["dimension_scores"]] == [
        "substance",
        "structure",
        "relevance",
        "credibility",
        "differentiation",
    ]
    assert first["primary_bottleneck"] == "relevance"
    assert first["next_action_type"] == "mock_reentry_relevance"
    assert first["target_type"] == "mock_turn_answer"
    assert first["target_parent_type"] == "mock_session"
    assert first["target_parent_id"] == "sess_mock_001"

    status_code, body = call_json(
        app,
        f"/api/v1/scoring-results/{first['score_result_id']}",
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    assert body["data"]["score_result_id"] == first["score_result_id"]

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results?target_parent_type=mock_session&target_parent_id=sess_mock_001",
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    assert body["meta"] == {
        "target_parent_type": "mock_session",
        "target_parent_id": "sess_mock_001",
    }
    assert [item["score_result_id"] for item in body["data"]] == [
        first["score_result_id"],
        second["score_result_id"],
    ]

    status_code, _body = call_json(
        app,
        f"/api/v1/scoring-results/{first['score_result_id']}",
        headers={"cookie": owner_b_cookie},
    )
    assert status_code == 404

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results?target_parent_type=mock_session&target_parent_id=sess_mock_001",
        headers={"cookie": owner_b_cookie},
    )
    assert status_code == 200
    assert body["data"] == []


def test_list_score_results_filters_target_pair_and_owner_scope() -> None:
    app = _app_with_two_users()
    owner_a_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "scoring-user-b@example.com", USER_B_PASSWORD)

    target_match = _create_score_result(
        app,
        owner_a_cookie,
        target_id="turn_target_pair_001",
        target_parent_id="sess_target_pair_001",
        dimensions=_dimensions(
            substance=82,
            structure=72,
            relevance=62,
            credibility=88,
            differentiation=62,
        ),
    )
    same_owner_other_target = _create_score_result(
        app,
        owner_a_cookie,
        target_id="turn_target_pair_002",
        target_parent_id="sess_target_pair_001",
        dimensions=_dimensions(
            substance=78,
            structure=70,
            relevance=64,
            credibility=84,
            differentiation=64,
        ),
    )
    other_owner_same_target = _create_score_result(
        app,
        owner_b_cookie,
        target_id="turn_target_pair_001",
        target_parent_id="sess_target_pair_001",
        dimensions=_dimensions(
            substance=90,
            structure=90,
            relevance=90,
            credibility=90,
            differentiation=90,
        ),
    )

    list_path = (
        "/api/v1/scoring-results"
        "?target_type=mock_turn_answer&target_id=turn_target_pair_001"
    )
    status_code, body = call_json(
        app,
        list_path,
        headers={"cookie": owner_a_cookie},
    )

    assert status_code == 200
    assert body["resource_type"] == "score_result_list"
    returned_ids = [item["score_result_id"] for item in body["data"]]
    assert returned_ids == [target_match["score_result_id"]]
    assert same_owner_other_target["score_result_id"] not in returned_ids
    assert other_owner_same_target["score_result_id"] not in returned_ids
    assert body["data"][0]["target_type"] == "mock_turn_answer"
    assert body["data"][0]["target_id"] == "turn_target_pair_001"


def test_get_nonexistent_score_result_returns_404() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results/nonexistent-score-result-id",
        headers={"cookie": owner_cookie},
    )

    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_create_and_get_review_transcript_score_result_contract() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body={
            "score_type": "polish_report",
            "target_type": "review_transcript",
            "target_id": "review_001",
            "target_parent_type": "review",
            "target_parent_id": "review_001",
            "source_module": "review",
            "source_event": "transcript_reviewed",
            "rubric_version": CANONICAL_RUBRIC_VERSION,
            "dimensions": _dimensions(
                substance=74,
                structure=68,
                relevance=68,
                credibility=80,
                differentiation=72,
            ),
            "evidence_links": [{"resource_type": "review", "resource_id": "review_001"}],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    data = body["data"]
    assert data["target_type"] == "review_transcript"
    assert data["target_id"] == "review_001"
    assert data["target_parent_type"] == "review"
    assert data["target_parent_id"] == "review_001"
    assert data["source_module"] == "review"
    assert data["source_event"] == "transcript_reviewed"
    assert data["primary_bottleneck"] == "relevance"
    assert data["next_action_type"] == "mock_reentry_relevance"

    status_code, body = call_json(
        app,
        f"/api/v1/scoring-results/{data['score_result_id']}",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["target_type"] == "review_transcript"


def test_create_score_result_persists_overall_score_and_confidence_average() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)
    dimensions = [
        {"name": "substance", "score": 80, "confidence": 1.0},
        {"name": "structure", "score": 80, "confidence": 0.8},
        {"name": "relevance", "score": 80, "confidence": 0.6},
        {"name": "credibility", "score": 80, "confidence": 0.4},
        {"name": "differentiation", "score": 80, "confidence": 0.2},
    ]
    payload = _score_payload(
        target_id="turn_confidence_average",
        target_parent_id="sess_confidence_average",
        dimensions=dimensions,
    )
    payload["overall_score"] = 80

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=payload,
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["resource_type"] == "score_result"
    data = body["data"]
    assert data["overall_score"] == 80
    assert data["score_value"] == 80
    assert data["confidence"] == 0.6
    assert data["confidence_level"] == "medium"
    assert [item["confidence"] for item in data["dimension_scores"]] == [
        1.0,
        0.8,
        0.6,
        0.4,
        0.2,
    ]

    status_code, body = call_json(
        app,
        f"/api/v1/scoring-results/{data['score_result_id']}",
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["data"]["score_result_id"] == data["score_result_id"]
    assert body["data"]["overall_score"] == 80
    assert body["data"]["confidence"] == 0.6


def test_scoring_api_rejects_invalid_strict_rubric_dimension() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body={
            "score_type": "polish_answer",
            "target_type": "mock_turn_answer",
            "target_id": "turn_invalid_dimension",
            "rubric_version": CANONICAL_RUBRIC_VERSION,
            "dimensions": (
                {"name": "substance", "score": 80, "confidence": 0.8},
                {"name": "structure", "score": 80, "confidence": 0.8},
                {"name": "relevance", "score": 80, "confidence": 0.8},
                {"name": "credibility", "score": 80, "confidence": 0.8},
                {"name": "delivery", "score": 80, "confidence": 0.8},
            ),
        },
        headers={"cookie": owner_cookie},
    )

    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"
    assert "canonical scoring dimensions" in body["error"]["message"]


@pytest.mark.parametrize("overall_score", [-1, 101])
def test_create_score_result_rejects_invalid_overall_score_range(
    overall_score: int,
) -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)
    payload = _score_payload(
        target_id=f"turn_invalid_overall_score_{overall_score}",
        dimensions=_dimensions(
            substance=80,
            structure=80,
            relevance=80,
            credibility=80,
            differentiation=80,
        ),
    )
    payload["overall_score"] = overall_score

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=payload,
        headers={"cookie": owner_cookie},
    )

    assert status_code == 422
    assert isinstance(body, dict)
    assert "detail" in body or "error" in body


def test_create_score_result_rejects_overall_score_mismatch() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)
    payload = _score_payload(
        target_id="turn_overall_score_mismatch",
        dimensions=_dimensions(
            substance=80,
            structure=80,
            relevance=80,
            credibility=80,
            differentiation=80,
        ),
    )
    payload["overall_score"] = 79

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=payload,
        headers={"cookie": owner_cookie},
    )

    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"
    assert "overall_score must match" in body["error"]["message"]


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_create_score_result_rejects_invalid_dimension_confidence(
    confidence: float,
) -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)
    dimensions = [
        dict(item)
        for item in _dimensions(
            substance=80,
            structure=80,
            relevance=80,
            credibility=80,
            differentiation=80,
        )
    ]
    dimensions[0]["confidence"] = confidence
    payload = _score_payload(
        target_id=f"turn_invalid_confidence_{confidence}",
        dimensions=dimensions,
    )

    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=payload,
        headers={"cookie": owner_cookie},
    )

    assert status_code == 422
    assert isinstance(body, dict)
    assert "detail" in body or "error" in body


def test_scoring_api_rejects_invalid_score_range_missing_rubric_and_training_action() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "scoring-user-a@example.com", USER_A_PASSWORD)

    invalid_score_payload = _score_payload(
        target_id="turn_invalid_score",
        dimensions=_dimensions(
            substance=101,
            structure=80,
            relevance=80,
            credibility=80,
            differentiation=80,
        ),
    )
    status_code, _body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=invalid_score_payload,
        headers={"cookie": owner_cookie},
    )
    assert status_code == 422

    missing_rubric_payload = _score_payload(
        target_id="turn_missing_rubric",
        dimensions=_dimensions(
            substance=80,
            structure=80,
            relevance=80,
            credibility=80,
            differentiation=80,
        ),
    )
    missing_rubric_payload.pop("rubric_version")
    status_code, _body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=missing_rubric_payload,
        headers={"cookie": owner_cookie},
    )
    assert status_code == 422

    training_payload = _score_payload(
        target_id="turn_training_action",
        dimensions=_dimensions(
            substance=80,
            structure=80,
            relevance=80,
            credibility=80,
            differentiation=80,
        ),
    )
    training_payload["next_action_type"] = "training_plan"
    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=training_payload,
        headers={"cookie": owner_cookie},
    )
    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"


def _create_score_result(app, cookie: str, *, target_id: str, target_parent_id: str, dimensions):
    status_code, body = call_json(
        app,
        "/api/v1/scoring-results",
        "POST",
        json_body=_score_payload(
            target_id=target_id,
            target_parent_id=target_parent_id,
            dimensions=dimensions,
        ),
        headers={"cookie": cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "score_result"
    return body["data"]


def _score_payload(
    *,
    target_id: str,
    dimensions,
    target_parent_id: str = "sess_mock_001",
) -> dict:
    return {
        "score_type": "polish_answer",
        "target_type": "mock_turn_answer",
        "target_id": target_id,
        "target_parent_type": "mock_session",
        "target_parent_id": target_parent_id,
        "source_module": "mock_interview",
        "source_event": "answer_submitted",
        "rubric_version": CANONICAL_RUBRIC_VERSION,
        "dimensions": dimensions,
        "evidence_links": [{"resource_type": "mock_turn_answer", "resource_id": target_id}],
    }


def _dimensions(
    *,
    substance: int,
    structure: int,
    relevance: int,
    credibility: int,
    differentiation: int,
) -> tuple[dict, ...]:
    return (
        {"name": "substance", "score": substance, "confidence": 0.9},
        {"name": "structure", "score": structure, "confidence": 0.8},
        {"name": "relevance", "score": relevance, "confidence": 0.85},
        {"name": "credibility", "score": credibility, "confidence": 0.75},
        {"name": "differentiation", "score": differentiation, "confidence": 0.7},
    )


def _app_with_two_users():
    runtime = build_auth_runtime(
        AuthRuntimeSettings(
            dev_user_password=USER_A_PASSWORD,
            dev_user_identifier="scoring-user-a@example.com",
            dev_user_email="scoring-user-a@example.com",
            dev_username="scoring_user_a",
            dev_display_name="Scoring User A",
            seed_dev_user=True,
        ),
        cookie_path="/api/v1",
    )
    runtime.user_store.add_user(
        user_id=USER_B_ID,
        email="scoring-user-b@example.com",
        username="scoring_user_b",
        display_name="Scoring User B",
        password_hash=Pbkdf2PasswordHasher().hash_password(USER_B_PASSWORD),
    )
    return create_app(auth_runtime=runtime, initialize_schema=True)


def _login_cookie(app, identifier: str, password: str) -> str:
    status_code, _body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": identifier, "password": password},
    )
    assert status_code == 200
    cookie_value = headers["set-cookie"][0]
    token = cookie_value.split("aifi_session=", 1)[1].split(";", 1)[0]
    return f"aifi_session={token}"
