import type { PolishRecommendedAction } from "./types";

export const NEXT_RECOMMENDED_ACTION_LABELS: Record<string, string> = {
  answer_again: "再答一版",
  continue_same_question: "继续打磨本题",
  retry_same_question: "重答同题",
  generate_reference_answer: "查看参考回答",
  explain_knowledge_point: "查看考点解析",
  expand_technical_principle: "展开技术原理",
  generate_next_round_suggestion: "生成下一轮建议",
  provide_more_answer_detail: "补充回答细节",
};

export const FEEDBACK_CODE_DISPLAY_MAP: Record<string, string> = {
  pending: "待处理",
  generated: "已生成",
  failed: "生成失败",
  generation_failed: "生成失败",
  validation_failed: "生成失败",
  timed_out: "生成失败",
  cancelled: "生成失败",
  source_unavailable: "生成失败",
  conflict: "冲突",
  ambiguous: "不确定",
  consistent: "一致",
  polish_answer: "回答打磨",
  retry_same_question: "重答同题",
  continue_same_question: "继续本题",
  provide_more_answer_detail: "补充回答细节",
  answer_again: "重新作答",
  major: "主要失分",
  minor: "轻微失分",
  critical: "严重失分",
};

export const FEEDBACK_LOSS_POINTS_TABLE_COLUMNS = ["序号", "严重程度", "扣分", "问题", "修正建议"] as const;
export const FALLBACK_FEEDBACK_TEXT = "本轮反馈尚未生成";
export const FEEDBACK_REFERENCE_SECTION_FALLBACK = "暂无参考回答";
export const CODE_NOT_AVAILABLE_TEXT = "未知状态";
export const LOSS_POINT_SUGGESTION_FALLBACK = "建议补充该点的设计依据、关键步骤和验证方式。";

export type NormalizedPolishFeedbackStatus = "pending" | "generated" | "failed";

export type FeedbackSectionKey =
  | "failed_status"
  | "feedback"
  | "score"
  | "positive_evidence_points"
  | "loss_points"
  | "reference_answer"
  | "weight_explanation"
  | "interview_intent"
  | "technical_gaps"
  | "communication_gaps"
  | "p7_reference_answer"
  | "oral_script"
  | "retry_delta"
  | "next_retry_focus"
  | "next_polish_suggestions"
  | "asset_consistency_check";

export type FeedbackLossPointTableRow = {
  readonly index: number;
  readonly severity: string;
  readonly deduction: string;
  readonly issue: string;
  readonly suggestion: string;
};

export type FeedbackCardSectionViewModel = {
  readonly key: FeedbackSectionKey;
  readonly title: string;
  readonly items: readonly string[];
  readonly defaultOpen: boolean;
  readonly tone?: "default" | "warning";
  readonly tableColumns?: readonly string[];
  readonly tableRows?: readonly FeedbackLossPointTableRow[];
};

export type FeedbackCardViewModel = {
  readonly title: string;
  readonly status: NormalizedPolishFeedbackStatus;
  readonly contractId: string | null;
  readonly contractIds: readonly string[];
  readonly sections: readonly FeedbackCardSectionViewModel[];
  readonly nextActions: readonly PolishRecommendedAction[];
  readonly traceItems: readonly string[];
};

export type WorkbenchFixedNextActionBarViewModel = {
  readonly placement: "fixed_above_current_question_composer";
  readonly actions: readonly {
    readonly action: PolishRecommendedAction;
    readonly label: string;
  }[];
};
