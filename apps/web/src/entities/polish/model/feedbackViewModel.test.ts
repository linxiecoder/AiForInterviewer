import {
  buildFeedbackResponseContractViewModel,
  buildFeedbackTimeoutRefreshViewModel,
  type FeedbackResponseContractViewModel,
} from "./feedbackViewModel";
import type { PolishFeedbackPayload, PolishSessionAnswer, PolishSessionDetail } from "./types";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type Step8ResponseMetadataFields = keyof Pick<
  PolishFeedbackPayload,
  | "policy_signed_next_action"
  | "follow_up_intent_classification"
  | "same_node_follow_up_contract"
  | "same_node_next_question_contract"
  | "next_question_response_contract"
>;

type Step8ResponseMetadataFieldsArePresent = Expect<
  Equal<
    Step8ResponseMetadataFields,
    | "policy_signed_next_action"
    | "follow_up_intent_classification"
    | "same_node_follow_up_contract"
    | "same_node_next_question_contract"
    | "next_question_response_contract"
  >
>;

const step8Payload: PolishFeedbackPayload = {
  status: "generated",
  contract_ids: ["step8.response", "step8.response"],
  feedback_text: "同节点追问反馈",
  score_delta: 12,
  mastery_status: "improving",
  policy_signed_next_action: {
    action_type: "continue_same_question",
    policy_signature: "policy_sig_step8",
    raw_prompt: "must_drop",
  },
  follow_up_intent_classification: {
    intent: "same_node_follow_up",
    provider_payload: "must_drop",
  },
  same_node_follow_up_contract: {
    contract_id: "same_node_follow_up.v1",
  },
  same_node_next_question_contract: {
    contract_id: "same_node_next_question.v1",
  },
  next_question_response_contract: {
    contract_id: "next_question_response.v1",
  },
};

const generatedContractView = buildFeedbackResponseContractViewModel(buildAnswer(step8Payload));
expectEqual(generatedContractView.status, "generated", "generated status");
expectEqual(generatedContractView.hasTerminalFeedback, true, "generated is terminal");
expectEqual(generatedContractView.shouldKeepPendingCopy, false, "generated clears pending copy");
expectEqual(generatedContractView.policySignedNextAction.isTrusted, true, "signed next action is trusted");
expectEqual(generatedContractView.policySignedNextAction.action, "continue_same_question", "signed action type");
expectEqual(generatedContractView.policySignedNextAction.label, "继续打磨本题", "signed action label");
expectEqual(generatedContractView.progress.scoreDelta, 12, "score delta");
expectEqual(generatedContractView.progress.masteryStatus, "improving", "mastery status");
expectIncludes(
  generatedContractView.responseContractItems.flatMap((section) => section.items),
  "contract_id：same_node_follow_up.v1",
  "same node follow-up contract id",
);
expectExcludes(
  generatedContractView.responseContractItems.flatMap((section) => section.items),
  "must_drop",
  "provider payload and raw prompt are hidden",
);

const failedContractView = buildFeedbackResponseContractViewModel(buildAnswer({
  status: "validation_failed",
  retryable: true,
  validation_errors: ["validation_failed", "raw_prompt"],
  error: {
    code: "provider_payload_leak",
    message: "must never render",
  },
}));
expectEqual(failedContractView.status, "failed", "failed status");
expectEqual(failedContractView.hasTerminalFeedback, true, "failed is terminal");
expectEqual(failedContractView.shouldKeepPendingCopy, false, "failed clears pending copy");
expectEqual(failedContractView.card.title, "反馈生成失败", "failed card title");
expectEqual(failedContractView.card.sections.length, 1, "failed card section count");
expectIncludes(failedContractView.card.sections[0]?.items ?? [], "错误码：validation_failed", "safe error code");
expectExcludes(failedContractView.card.sections[0]?.items ?? [], "raw_prompt", "raw prompt hidden");
expectExcludes(failedContractView.card.sections[0]?.items ?? [], "provider_payload_leak", "provider payload code hidden");

const pendingContractView = buildFeedbackResponseContractViewModel(buildAnswer({ status: "pending" }));
expectEqual(pendingContractView.status, "pending", "pending status");
expectEqual(pendingContractView.hasTerminalFeedback, false, "pending is not terminal");
expectEqual(pendingContractView.shouldKeepPendingCopy, true, "pending keeps copy");

const failedRefreshView = buildFeedbackTimeoutRefreshViewModel(
  buildSessionDetail(buildAnswer({ status: "generation_failed", validation_errors: ["generation_failed"] })),
  "question-1",
  "answer-1",
);
expectEqual(failedRefreshView.hasTerminalFeedback, true, "failed refresh terminal");
expectEqual(failedRefreshView.shouldKeepPendingCopy, false, "failed refresh clears pending copy");
expectEqual(failedRefreshView.feedbackCard?.status, "failed", "failed refresh feedback card");

const responseContractShape: FeedbackResponseContractViewModel = generatedContractView;
expectEqual(responseContractShape.card.status, "generated", "response contract shape");

function buildAnswer(feedbackPayload: PolishFeedbackPayload): PolishSessionAnswer {
  return {
    answer_id: "answer-1",
    answer_round: 2,
    answer_text: "我的回答",
    answer_created_at: "2026-06-26T00:00:00Z",
    feedback_text: feedbackPayload.feedback_text ?? "",
    feedback_id: feedbackPayload.status === "pending" ? null : "feedback-1",
    score_result_id: null,
    feedback_created_at: feedbackPayload.status === "pending" ? null : "2026-06-26T00:01:00Z",
    feedback_payload: feedbackPayload,
  };
}

function buildSessionDetail(answer: PolishSessionAnswer): PolishSessionDetail {
  return {
    session_id: "session-1",
    mode: "polish",
    session_status: "active",
    resume_job_binding_id: "binding-1",
    resume_id: "resume-1",
    resume_version_id: "resume-version-1",
    job_id: "job-1",
    job_version_id: "job-version-1",
    job_title: "后端工程师",
    job_company: "示例公司",
    resume_title: "示例简历",
    binding_label: "示例绑定",
    turns: [{
      question_id: "question-1",
      question_text: "解释一次失败折叠",
      question_sources: [],
      question_created_at: "2026-06-26T00:00:00Z",
      answers: [answer],
    }],
    progress_tree_status: "ready",
    progress_percent: 50,
    progress_tree_plan: {
      status: "ready",
      context_digest: "digest-1",
      nodes: [],
    },
    progress_tree_state: {
      status: "ready",
      node_states: [],
      updated_from_turns_count: 1,
      progress: {
        progress_percent: 50,
      },
    },
    created_at: "2026-06-26T00:00:00Z",
    updated_at: "2026-06-26T00:01:00Z",
  };
}

function expectEqual<Value>(actual: Value, expected: Value, label: string): void {
  if (!Object.is(actual, expected)) {
    throw new Error(`${label}: expected ${String(expected)}, got ${String(actual)}`);
  }
}

function expectIncludes(items: readonly string[], expected: string, label: string): void {
  if (!items.some((item) => item.includes(expected))) {
    throw new Error(`${label}: expected item containing ${expected}`);
  }
}

function expectExcludes(items: readonly string[], forbidden: string, label: string): void {
  if (items.some((item) => item.includes(forbidden))) {
    throw new Error(`${label}: forbidden item containing ${forbidden}`);
  }
}
