import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERVIEW_PAGE = Path("apps/web/src/pages/interview/InterviewPage.tsx")
POLISH_API = Path("apps/web/src/entities/polish/api/polishApi.ts")
POLISH_TYPES = Path("apps/web/src/entities/polish/model/types.ts")
FEEDBACK_VIEW_MODEL = Path("apps/web/src/entities/polish/model/feedbackViewModel.ts")


def _source(path: Path) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _assert_feedback_timeout_refresh_view_model_scenario() -> None:
    script = r"""
const ts = require("typescript");

function assertScenario(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const source = require("node:fs").readFileSync(filename, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      jsx: ts.JsxEmit.ReactJSX,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  });
  module._compile(output.outputText, filename);
};

const {
  buildFeedbackTimeoutRefreshViewModel,
} = require("./apps/web/src/entities/polish/model/feedbackViewModel.ts");

const submittedQuestionId = "q_timeout_original";
const submittedAnswerId = "ans_timeout_terminal";
const refreshed = {
  turns: [
    {
      question_id: submittedQuestionId,
      answers: [
        {
          answer_id: submittedAnswerId,
          answer_round: 1,
          answer_text: "Submitted answer kept in focus",
          feedback_id: null,
          feedback_created_at: null,
          feedback_text: "",
          score_result_id: null,
          feedback_payload: {
            status: "generation_failed",
            feedback_text: "Backend terminal failure from refreshed detail",
            retryable: true,
            validation_errors: ["feedback_generation_failed"],
            error: {
              code: "feedback_generation_failed",
            },
            next_recommended_actions: ["continue_same_question"],
          },
        },
      ],
    },
  ],
};

const viewModel = buildFeedbackTimeoutRefreshViewModel(
  refreshed,
  submittedQuestionId,
  submittedAnswerId,
);
const card = viewModel.feedbackCard;
const visibleCopy = [
  card?.title,
  card?.status,
  ...(card?.sections ?? []).flatMap((section) => [
    section.title,
    ...(section.items ?? []),
  ]),
].filter(Boolean).join("\n");

assertScenario(viewModel.selectedQuestionId === submittedQuestionId, "submitted question focus must be kept");
assertScenario(viewModel.selectedAnswerId === submittedAnswerId, "submitted answer focus must be kept");
assertScenario(viewModel.hasTerminalFeedback === true, "terminal refreshed payload must be detected");
assertScenario(viewModel.shouldKeepPendingCopy === false, "pending copy must stop when terminal payload exists");
assertScenario(card?.title === "反馈生成失败", "terminal payload must build failure feedback card title");
assertScenario(card?.status === "failed", "generation_failed must normalize to failed card status");
assertScenario(card?.sections[0]?.title === "失败状态", "failure feedback section must be rendered");
assertScenario(visibleCopy.includes("反馈生成超时或失败，可重试"), "failure feedback card copy must be visible");
assertScenario(!visibleCopy.includes("本轮反馈尚未生成"), "terminal payload must not render pending-only copy");
"""
    subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _assert_failed_feedback_summary_sections_scenario() -> None:
    script = r"""
const ts = require("typescript");
const Module = require("node:module");

function assertScenario(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function compileTypeScript(module, filename) {
  const source = require("node:fs").readFileSync(filename, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      jsx: ts.JsxEmit.ReactJSX,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  });
  module._compile(output.outputText, filename);
}

require.extensions[".ts"] = compileTypeScript;
require.extensions[".tsx"] = compileTypeScript;
require.extensions[".css"] = function compileCssModule(module) {
  module.exports = new Proxy({}, {
    get: (_target, property) => String(property),
  });
};

const originalLoad = Module._load;
Module._load = function loadPageDependency(request, parent, isMain) {
  if (request.includes("entities/job/api/jobApi") || request.includes("entities/polish/api/polishApi")) {
    return new Proxy({}, {
      get: (_target, property) => {
        if (property === "__esModule") {
          return true;
        }
        return function noopApiDependency() {
          throw new Error(`Unexpected API dependency call: ${String(property)}`);
        };
      },
    });
  }
  if (request.includes("app/routes/router")) {
    return {
      useRouteController: () => ({
        navigate: () => undefined,
        params: {},
      }),
    };
  }
  if (request.includes("shared/api/errors")) {
    return { isApiHttpError: () => false };
  }
  if (
    request.includes("shared/ui/EmptyState") ||
    request.includes("shared/ui/ErrorState") ||
    request.includes("shared/ui/LoadingState") ||
    request.includes("widgets/app-shell/AppShell")
  ) {
    return new Proxy({}, {
      get: (_target, property) => function noopComponent() {
        return property === "AppShell" ? null : null;
      },
    });
  }
  return originalLoad.call(this, request, parent, isMain);
};

const {
  buildFeedbackCardViewModel,
  buildFeedbackSummarySections,
} = require("./apps/web/src/pages/interview/InterviewPage.tsx");

const failedAnswer = {
  answer_id: "ans_failed_summary",
  answer_round: 1,
  answer_text: "Submitted answer has terminal feedback failure",
  feedback_id: null,
  feedback_created_at: null,
  feedback_text: "",
  score_result_id: null,
  feedback_payload: {
    status: "generation_failed",
    retryable: true,
    validation_errors: ["feedback_generation_failed"],
    error: {
      code: "feedback_generation_failed",
    },
  },
};

const feedbackCard = buildFeedbackCardViewModel(failedAnswer);
const summarySections = buildFeedbackSummarySections(feedbackCard);
const visibleCopy = summarySections.flatMap((section) => [
  section.key,
  section.title,
  ...(section.items ?? []),
]).join("\n");

assertScenario(feedbackCard?.title === "反馈生成失败", "failed payload must build a failure feedback card");
assertScenario(summarySections.some((section) => section.key === "failed_status"), "summary must include failed_status section");
assertScenario(visibleCopy.includes("失败状态"), "summary must include failed section title");
assertScenario(visibleCopy.includes("反馈生成超时或失败，可重试"), "summary must include failed retry copy");
assertScenario(!visibleCopy.includes("当前回答暂无总评内容"), "summary must not fall back to empty-summary copy");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


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


def test_interview_workbench_uses_question_task_adapter_for_composer_generation() -> None:
    page_source = _source(INTERVIEW_PAGE)
    api_source = _source(POLISH_API)

    assert "createPolishQuestionTask" not in page_source
    assert "const createQuestion" not in page_source
    assert "await createQuestion" not in page_source
    assert "createPolishNodeQuestionTask" in page_source
    assert "questionTask: (sessionId: string)" in api_source
    assert "/questions`" in api_source


def test_interview_workbench_waits_for_running_question_task_before_refresh() -> None:
    source = _source(INTERVIEW_PAGE)

    current_node_flow = re.search(
        r"const createCurrentNodeQuestion = async .*?"
        r"const task = await createPolishNodeQuestionTask\(sessionId\);"
        r".*?let focusTask: .*? = task;"
        r".*?if \(isPolishAiTaskRunningStatus\(task\.status\)\) \{"
        r".*?focusTask = await waitForPolishAiTaskFinalStatus\(task\.ai_task_id,"
        r".*?assertPolishQuestionTaskCanFocus\(focusTask,"
        r".*?focusGeneratedQuestionTask\(focusTask, null\);"
        r".*?await loadSession\(\);"
        r".*?await loadCandidateRecords\(\);",
        source,
        re.S,
    )
    feedback_next_flow = re.search(
        r"const createFeedbackNextQuestion = async .*?"
        r"const task = await createPolishFeedbackNextQuestionTask\(sessionId, feedbackId\);"
        r".*?let focusTask: .*? = task;"
        r".*?if \(isPolishAiTaskRunningStatus\(task\.status\)\) \{"
        r".*?focusTask = await waitForPolishAiTaskFinalStatus\(task\.ai_task_id,"
        r".*?assertPolishQuestionTaskCanFocus\(focusTask,"
        r".*?focusGeneratedQuestionTask\(focusTask, null\);"
        r".*?await loadSession\(\);"
        r".*?await loadCandidateRecords\(\);",
        source,
        re.S,
    )

    assert current_node_flow is not None
    assert feedback_next_flow is not None
    assert "题目生成仍在进行中，请稍后刷新查看结果。" in source
    assert "下一题生成仍在进行中，请稍后刷新查看结果。" in source


def test_interview_workbench_failed_question_task_stops_before_focus() -> None:
    source = _source(INTERVIEW_PAGE)

    assert "POLISH_QUESTION_TASK_FAILURE_STATUSES" in source
    assert "export function isPolishQuestionTaskFailureStatus" in source
    for status in (
        "validation_failed",
        "source_unavailable",
        "generation_failed",
        "timed_out",
        "cancelled",
    ):
        assert status in source

    assert "function buildPolishQuestionTaskFailureMessage" in source
    assert "task.validation_errors" in source
    assert "assertPolishQuestionTaskCanFocus(focusTask, \"题目生成失败，可重试。\")" in source
    assert "assertPolishQuestionTaskCanFocus(focusTask, \"下一题生成失败，可重试。\")" in source

    current_node_flow = re.search(
        r"const createCurrentNodeQuestion = async .*?"
        r"assertPolishQuestionTaskCanFocus\(focusTask, \"题目生成失败，可重试。\"\);"
        r"\s*focusGeneratedQuestionTask\(focusTask, null\);",
        source,
        re.S,
    )
    feedback_next_flow = re.search(
        r"const createFeedbackNextQuestion = async .*?"
        r"assertPolishQuestionTaskCanFocus\(focusTask, \"下一题生成失败，可重试。\"\);"
        r"\s*focusGeneratedQuestionTask\(focusTask, null\);",
        source,
        re.S,
    )

    assert current_node_flow is not None
    assert feedback_next_flow is not None


def test_interview_workbench_question_failure_does_not_consume_provider_or_result_payload() -> None:
    source = _source(INTERVIEW_PAGE)
    helper_match = re.search(
        r"function buildPolishQuestionTaskFailureMessage\(.*?\n\}",
        source,
        re.S,
    )

    assert helper_match is not None
    helper_source = helper_match.group(0)
    assert "validation_errors" in helper_source
    assert "provider_payload" not in helper_source
    assert "result_payload" not in helper_source


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


def test_interview_workbench_feedback_timeout_reloads_terminal_feedback_payload() -> None:
    source = _source(INTERVIEW_PAGE)
    view_model_source = _source(FEEDBACK_VIEW_MODEL)
    timeout_marker = (
        "if (feedbackError instanceof Error && feedbackError.message === POLISH_AI_TASK_FEEDBACK_PENDING_MESSAGE) {"
    )
    next_failure_marker = 'setWorkbenchFailureState("feedbackFailedAnswerSaved");'

    assert timeout_marker in source
    assert next_failure_marker in source
    timeout_start = source.index(timeout_marker)
    timeout_end = source.index(next_failure_marker, timeout_start)
    branch_body = source[timeout_start:timeout_end]
    assert "await fetchPolishSession(sessionId);" in branch_body
    assert "setSession(refreshed);" in branch_body
    assert "buildFeedbackTimeoutRefreshViewModel(" in branch_body
    assert "setSelectedQuestionId(timeoutRefresh.selectedQuestionId);" in branch_body
    assert "setSelectedAnswerId(timeoutRefresh.selectedAnswerId);" in branch_body
    assert "timeoutRefresh.hasTerminalFeedback" in branch_body
    assert "setAnswerError(null);" in branch_body
    assert "setAnswerError(INTERVIEW_WORKBENCH_FEEDBACK_PENDING_AFTER_SAVE_COPY);" in branch_body
    assert "buildFeedbackCardViewModel(answerContext.answer)" in view_model_source
    assert "hasPolishGeneratedFeedback(answerContext?.answer)" in view_model_source

    assert branch_body.index("await fetchPolishSession(sessionId);") < branch_body.index(
        "buildFeedbackTimeoutRefreshViewModel("
    )
    assert branch_body.index("timeoutRefresh.hasTerminalFeedback") < branch_body.index(
        "setAnswerError(INTERVIEW_WORKBENCH_FEEDBACK_PENDING_AFTER_SAVE_COPY);"
    )
    assert "await loadSession();" not in branch_body
    assert "feedbackTask.status" not in branch_body
    assert "feedbackTask.result" not in branch_body

    _assert_feedback_timeout_refresh_view_model_scenario()


def test_interview_workbench_failed_feedback_summary_sections_include_failed_status_copy() -> None:
    _assert_failed_feedback_summary_sections_scenario()


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
