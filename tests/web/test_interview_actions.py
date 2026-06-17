import re
from pathlib import Path


INTERVIEW_PAGE = Path("apps/web/src/pages/interview/InterviewPage.tsx")
POLISH_API = Path("apps/web/src/entities/polish/api/polishApi.ts")
POLISH_TYPES = Path("apps/web/src/entities/polish/model/types.ts")


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_interview_workbench_end_uses_system_modal_not_native_dialog() -> None:
    source = _source(INTERVIEW_PAGE)

    assert "INTERVIEW_WORKBENCH_END_CONFIRM_COPY" in source
    assert "open={endConfirmOpen}" in source
    assert "setEndConfirmOpen(true)" in source
    assert "Modal.confirm" not in source
    assert re.search(r"(?:window\.)?(?:alert|confirm|prompt)\s*\(", source) is None


def test_interview_workbench_top_actions_are_icon_only_buttons() -> None:
    source = _source(INTERVIEW_PAGE)
    match = re.search(
        r"<div className=\{styles\.heroActions\}>(?P<body>.*?)</div>\s*</div>\s*</section>",
        source,
        re.S,
    )

    assert match is not None
    hero_actions = match.group("body")
    assert hero_actions.count("shape=\"circle\"") == 3
    assert "CopyOutlined" in hero_actions
    assert "CloseCircleOutlined" in hero_actions
    assert "ArrowLeftOutlined" in hero_actions
    assert "type=\"primary\"" in hero_actions
    assert "aria-label={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[0]}" in hero_actions
    assert "aria-label={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[1]}" in hero_actions
    assert "aria-label={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[2]}" in hero_actions
    assert re.search(r">\s*(?:复制|结束|返回)\s*</Button>", hero_actions) is None


def test_interview_list_actions_use_soft_delete_endpoint_without_delete_method() -> None:
    page_source = _source(INTERVIEW_PAGE)
    api_source = _source(POLISH_API)

    assert "INTERVIEW_LIST_ACTIONS" in page_source
    assert "generatePolishSessionReport(record.session_id)" in page_source
    assert "softDeletePolishSession(target.session_id)" in page_source
    assert "setListConfirmAction({ kind: \"delete\", session: record })" in page_source
    assert "softDeleteSession: (sessionId: string)" in api_source
    assert "/delete" in api_source
    assert "method: \"DELETE\"" not in api_source


def test_interview_workbench_does_not_call_question_task_endpoint_directly() -> None:
    source = _source(INTERVIEW_PAGE)

    assert "createPolishQuestionTask" not in source
    assert "const createQuestion" not in source
    assert "await createQuestion" not in source


def test_interview_workbench_next_recommendations_are_display_only() -> None:
    source = _source(INTERVIEW_PAGE)

    assert "resolveFeedbackNextRecommendedActionExecution" not in source
    assert "onNextRecommendedAction" not in source
    assert "feedback_next_question_intent" not in source


def test_interview_workbench_answer_submit_uses_stable_idempotency_key() -> None:
    page_source = _source(INTERVIEW_PAGE)
    api_source = _source(POLISH_API)

    assert "resolveAnswerSubmissionKeyDraft" in page_source
    assert "answerSubmissionKeyDraftRef" in page_source
    assert "idempotencyKey: keyDraft.idempotencyKey" in page_source
    assert "answerSubmissionKeyDraftRef.current = null" in page_source
    assert "\"Idempotency-Key\"" in api_source


def test_interview_workbench_has_no_grant_client_fields() -> None:
    combined_source = "\n".join(
        [
            _source(INTERVIEW_PAGE),
            _source(POLISH_API),
            _source(POLISH_TYPES),
        ]
    )

    for forbidden in (
        "NextQuestionExecutionGrant",
        "next_question_execution_grant",
        "grant_token",
        "grantId",
        "consumeGrant",
        "createGrant",
        "next_question_authorization",
    ):
        assert forbidden not in combined_source


def test_interview_workbench_progress_tree_does_not_trigger_question_execution() -> None:
    source = _source(INTERVIEW_PAGE)

    assert "\"generate_question\"" not in source
