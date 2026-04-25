export interface QuestionGenerationInputState {
  isJobDescriptionMissing: boolean;
  isResumeMarkdownMissing: boolean;
}

export interface FeedbackGenerationInputState {
  hasFirstQuestion: boolean;
  hasAnswer: boolean;
}

export const getMissingInputLabels = ({
  isJobDescriptionMissing,
  isResumeMarkdownMissing,
}: QuestionGenerationInputState) =>
  [
    isJobDescriptionMissing ? "岗位 JD" : undefined,
    isResumeMarkdownMissing ? "简历 Markdown" : undefined,
  ].filter((label): label is string => Boolean(label));

export const getQuestionGenerationHint = (state: QuestionGenerationInputState) => {
  const missingInputLabels = getMissingInputLabels(state);
  const missingInputText =
    missingInputLabels.length === 2
      ? `${missingInputLabels[0]} 和${missingInputLabels[1]}`
      : missingInputLabels[0];

  return missingInputLabels.length > 0
    ? `请先填写${missingInputText}。`
    : "已填写岗位 JD 和简历 Markdown，可以生成 3 条 mock 首轮问题。";
};

export const getFeedbackGenerationHint = ({
  hasFirstQuestion,
  hasAnswer,
}: FeedbackGenerationInputState) => {
  if (!hasFirstQuestion) {
    return "请先生成首轮问题。";
  }

  return hasAnswer
    ? "第 1 题回答已就绪，可以生成简版反馈。"
    : "请填写第 1 题回答后再生成简版反馈。";
};
