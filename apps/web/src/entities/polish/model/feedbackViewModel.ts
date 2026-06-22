import type { PolishSessionAnswer, PolishSessionDetail } from "./types";
import { buildFailedFeedbackSection, buildGeneratedFeedbackSections } from "./feedbackCardSections";
import {
  getAnswerNextRecommendedActions,
  hasPolishGeneratedFeedback,
  resolvePolishFeedbackStatus,
  toNextRecommendedActionLabel,
  toOptionalText,
} from "./feedbackViewModelUtils";
import type {
  FeedbackCardViewModel,
  WorkbenchFixedNextActionBarViewModel,
} from "./feedbackViewModelTypes";

export type {
  FeedbackCardSectionViewModel,
  FeedbackCardViewModel,
  FeedbackLossPointTableRow,
  NormalizedPolishFeedbackStatus,
  WorkbenchFixedNextActionBarViewModel,
} from "./feedbackViewModelTypes";

export {
  getAnswerNextRecommendedActions,
  getPolishAnswerFeedbackScoreValue,
  getPolishFeedbackGeneratedAt,
  getPolishFeedbackPayloadId,
  getPolishFeedbackPayloadText,
  getPolishFeedbackScoreValue,
  getPolishFeedbackStatusLabel,
  hasPolishFeedbackPayload,
  hasPolishGeneratedFeedback,
  resolvePolishFeedbackStatus,
  toNextRecommendedActionLabel,
} from "./feedbackViewModelUtils";

export function buildWorkbenchFixedNextActionBarViewModel(
  answer: PolishSessionAnswer | null | undefined,
): WorkbenchFixedNextActionBarViewModel | null {
  if (answer === null || answer === undefined) {
    return null;
  }
  const actions = getAnswerNextRecommendedActions(answer).map((action) => ({
    action,
    label: toNextRecommendedActionLabel(action),
  }));
  return actions.length === 0 ? null : {
    placement: "fixed_above_current_question_composer",
    actions,
  };
}

export function buildFeedbackCardViewModel(answer: PolishSessionAnswer): FeedbackCardViewModel {
  const payload = answer.feedback_payload;
  const contractIds = Array.from(new Set((payload?.contract_ids ?? []).map(toOptionalText).filter(isText)));
  const contractId = contractIds[0] ?? null;
  const status = resolvePolishFeedbackStatus(payload?.status);
  if (status === "failed") {
    return {
      title: "反馈生成失败",
      status,
      contractId,
      contractIds,
      sections: [buildFailedFeedbackSection(payload)],
      nextActions: getAnswerNextRecommendedActions(answer),
      traceItems: [],
    };
  }
  return {
    title: buildFeedbackRoundMetaLabel(answer.answer_round),
    status,
    contractId,
    contractIds,
    sections: buildGeneratedFeedbackSections(payload, answer.feedback_text, answer.score_result_id),
    nextActions: getAnswerNextRecommendedActions(answer),
    traceItems: [],
  };
}

export interface FeedbackTimeoutRefreshViewModel {
  readonly selectedQuestionId: string;
  readonly selectedAnswerId: string;
  readonly hasTerminalFeedback: boolean;
  readonly shouldKeepPendingCopy: boolean;
  readonly feedbackCard: FeedbackCardViewModel | null;
}

export function buildFeedbackTimeoutRefreshViewModel(
  refreshed: PolishSessionDetail,
  submittedQuestionId: string,
  submittedAnswerId: string,
): FeedbackTimeoutRefreshViewModel {
  const answerContext = findFeedbackTimeoutAnswerContext(refreshed, submittedAnswerId);
  const hasTerminalFeedback = hasPolishGeneratedFeedback(answerContext?.answer);
  return {
    selectedQuestionId: answerContext?.questionId ?? submittedQuestionId,
    selectedAnswerId: submittedAnswerId,
    hasTerminalFeedback,
    shouldKeepPendingCopy: !hasTerminalFeedback,
    feedbackCard:
      hasTerminalFeedback && answerContext !== null
        ? buildFeedbackCardViewModel(answerContext.answer)
        : null,
  };
}

interface FeedbackTimeoutAnswerContext {
  readonly questionId: string;
  readonly answer: PolishSessionAnswer;
}

function findFeedbackTimeoutAnswerContext(
  session: PolishSessionDetail,
  answerId: string,
): FeedbackTimeoutAnswerContext | null {
  for (const turn of session.turns) {
    const answer = turn.answers.find((item) => item.answer_id === answerId);
    if (answer !== undefined) {
      return {
        questionId: turn.question_id,
        answer,
      };
    }
  }
  return null;
}

function buildFeedbackRoundMetaLabel(round: number | null | undefined): string {
  return `反馈 #${normalizeRoundNumber(round)}`;
}

function normalizeRoundNumber(round: number | null | undefined): number {
  return typeof round === "number" && Number.isFinite(round) && round >= 1 ? Math.floor(round) : 1;
}

function isText(value: string | null): value is string {
  return value !== null;
}
