import type { PolishFeedbackPayload } from "./types";
import {
  CODE_NOT_AVAILABLE_TEXT,
  FEEDBACK_LOSS_POINTS_TABLE_COLUMNS,
  FALLBACK_FEEDBACK_TEXT,
  LOSS_POINT_SUGGESTION_FALLBACK,
  type FeedbackCardSectionViewModel,
  type FeedbackLossPointTableRow,
} from "./feedbackViewModelTypes";
import {
  buildOptionalFeedbackSection,
  buildOptionalRecordListItems,
  buildReferenceAnswerItems,
  normalizeLossPointDeductionValue,
} from "./feedbackCardSectionHelpers";
import {
  compactTextList,
  dedupeTextItems,
  isSection,
  isText,
  isUserVisibleFeedbackRecordKey,
  mapFeedbackCodeToDisplay,
  pickFirstRecordText,
  sanitizeFeedbackDisplayText,
  toOptionalText,
  toRecord,
} from "./feedbackViewModelUtils";

export function buildGeneratedFeedbackSections(
  payload: PolishFeedbackPayload | undefined,
  answerFeedbackText: string,
  fallbackScoreResultId: string | null,
): FeedbackCardSectionViewModel[] {
  return [
    { key: "feedback", title: "总体点评", items: buildOverallFeedbackItems(payload, answerFeedbackText), defaultOpen: true },
    { key: "score", title: "打分", items: buildScoreResultItems(payload, fallbackScoreResultId), defaultOpen: true },
    ...buildStructuredEvidenceSections(payload),
    {
      key: "loss_points",
      title: "失分点",
      items: [],
      tableColumns: FEEDBACK_LOSS_POINTS_TABLE_COLUMNS,
      tableRows: buildLossPointRows(payload),
      defaultOpen: false,
    },
    { key: "reference_answer", title: "参考回答", items: buildReferenceAnswerItems(payload?.reference_answer), defaultOpen: false },
    ...buildAssetConsistencySections(payload),
    ...buildThemeFeedbackSections(payload),
    ...buildRetryFeedbackSections(payload),
    ...buildNextPolishFeedbackSections(payload),
  ];
}

export function buildFailedFeedbackSection(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel {
  return {
    key: "failed_status",
    title: "失败状态",
    items: buildFailedFeedbackItems(payload),
    defaultOpen: true,
    tone: "warning",
  };
}

function buildOverallFeedbackItems(payload: PolishFeedbackPayload | undefined, answerFeedbackText: string): string[] {
  if (payload?.status === "pending") {
    return [FALLBACK_FEEDBACK_TEXT];
  }
  const mainGaps = Array.isArray(payload?.answer_summary?.main_gaps)
    ? payload.answer_summary.main_gaps.map(toOptionalText).filter(isText)
    : [];
  const items = dedupeTextItems([
    payload?.feedback_text || answerFeedbackText,
    payload?.answer_summary?.coverage ? `覆盖情况：${payload.answer_summary.coverage}` : null,
    ...mainGaps.map((gap) => `主要缺口：${gap}`),
  ]);
  return items.length > 0 ? items : [FALLBACK_FEEDBACK_TEXT];
}

function buildStructuredEvidenceSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  const section = buildOptionalFeedbackSection("positive_evidence_points", "得分点", buildOptionalRecordListItems(payload?.positive_evidence_points, [
    ["title", "得分点"],
    ["evidence_excerpt", "回答证据"],
    ["dimension_id", "关联维度"],
    ["related_dimension", "关联维度"],
    ["evidence_source", "证据来源"],
  ]), false);
  return section === null ? [] : [section];
}

function buildAssetConsistencySections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  const check = payload?.asset_consistency_check;
  if (check === null || check === undefined) {
    return [];
  }
  const status = toOptionalText(check.status);
  const needsClarification = status === "conflict" || status === "ambiguous";
  return [{
    key: "asset_consistency_check",
    title: "项目一致性检查",
    items: dedupeTextItems([
      status ? `状态：${mapFeedbackCodeToDisplay(status)}` : null,
      check.matched_project_name ? `匹配项目：${check.matched_project_name}` : null,
      needsClarification ? "需要澄清后再沉淀为资产" : null,
      ...buildOptionalRecordListItems(check.conflicts, [
        ["title", "冲突"],
        ["field", "字段"],
        ["current_value", "当前记录"],
        ["proposed_value", "本轮回答"],
        ["reason", "原因"],
      ]).map((item) => `冲突项：${item}`),
      ...compactTextList(check.clarification_questions).map((item) => `澄清问题：${item}`),
    ]),
    defaultOpen: needsClarification,
    tone: needsClarification ? "warning" : "default",
  }];
}

function buildThemeFeedbackSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  if (!payload) {
    return [];
  }
  return [
    buildOptionalFeedbackSection("weight_explanation", "权重说明", dedupeTextItems([
      payload.polish_theme_label ? `主题：${payload.polish_theme_label}` : null,
      typeof payload.explicit_weight === "number" ? `显性技术权重：${payload.explicit_weight}%` : null,
      typeof payload.implicit_weight === "number" ? `隐性表达权重：${payload.implicit_weight}%` : null,
      payload.weight_explanation,
    ]), true),
    buildOptionalFeedbackSection("interview_intent", "面试意图", compactTextList(payload.interview_intent), false),
    buildOptionalFeedbackSection("technical_gaps", "技术短板", compactTextList(payload.technical_gaps), false),
    buildOptionalFeedbackSection("communication_gaps", "表达短板", compactTextList(payload.communication_gaps), false),
    buildOptionalFeedbackSection("p7_reference_answer", "高阶参考答案", compactTextList(payload.p7_reference_answer), false),
    buildOptionalFeedbackSection("oral_script", "口语化范本", compactTextList(payload.oral_script), false),
  ].filter(isSection);
}

function buildRetryFeedbackSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  if (!payload) {
    return [];
  }
  return [
    buildOptionalFeedbackSection("retry_delta", "多次回答改进", buildRetryDeltaItems(payload), false),
    buildOptionalFeedbackSection("next_retry_focus", "下一轮重答重点", buildOptionalRecordListItems(payload.next_retry_focus, [
      ["focus_area", "重点"],
      ["priority", "优先级"],
      ["related_dimension", "关联维度"],
      ["suggested_action", "建议动作"],
    ]), false),
  ].filter(isSection);
}

function buildNextPolishFeedbackSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  const section = buildOptionalFeedbackSection(
    "next_polish_suggestions",
    "下一轮打磨建议",
    compactTextList(payload?.next_polish_suggestions ?? payload?.next_training_suggestions),
    false,
  );
  return section === null ? [] : [section];
}

function buildLossPointRows(payload: PolishFeedbackPayload | undefined): FeedbackLossPointTableRow[] {
  const values = payload?.loss_points;
  if (!Array.isArray(values) || values.length === 0) {
    return [];
  }
  return values.map((value, index) => {
    const record = toRecord(value);
    if (record === null) {
      return {
        index: index + 1,
        severity: CODE_NOT_AVAILABLE_TEXT,
        deduction: "0",
        issue: sanitizeFeedbackDisplayText(toOptionalText(value), "问题待补充"),
        suggestion: resolveLossPointSuggestion(null, payload),
      };
    }
    return {
      index: index + 1,
      severity: mapFeedbackCodeToDisplay(pickFirstRecordText(record, ["severity", "level", "criticality"])),
      deduction: normalizeLossPointDeductionValue(pickFirstRecordText(record, ["deduction", "deducted_points"]) ?? record.score_delta),
      issue: sanitizeFeedbackDisplayText(pickFirstRecordText(record, ["reason", "description", "content", "message"]), "问题待补充"),
      suggestion: resolveLossPointSuggestion(record, payload),
    };
  });
}

function resolveLossPointSuggestion(record: Readonly<Record<string, unknown>> | null, payload: PolishFeedbackPayload | undefined): string {
  const directSuggestion = record === null ? null : pickFirstRecordText(record, ["suggestion", "fix", "recommendation", "improvement"]);
  const retryFocus = Array.isArray(payload?.next_retry_focus)
    ? payload.next_retry_focus.map(toRecord).find((item) => item !== null) ?? null
    : null;
  const retryFocusSuggestion = retryFocus === null ? null : pickFirstRecordText(retryFocus, ["suggested_action", "suggestion", "action", "focus"]);
  const referenceSuggestion = sanitizeFeedbackDisplayText(buildReferenceAnswerItems(payload?.reference_answer)[0], "");
  return sanitizeFeedbackDisplayText(directSuggestion, "")
    || sanitizeFeedbackDisplayText(retryFocusSuggestion, "")
    || (referenceSuggestion ? `可参考：${referenceSuggestion}` : LOSS_POINT_SUGGESTION_FALLBACK);
}

function buildFailedFeedbackItems(payload: PolishFeedbackPayload | undefined): string[] {
  const validationErrors = Array.isArray(payload?.validation_errors) ? payload.validation_errors.map(toOptionalText).filter(isText) : [];
  const errorCode = toOptionalText(payload?.error?.code);
  const codes = Array.from(new Set([...(errorCode ? [errorCode] : []), ...validationErrors]));
  return dedupeTextItems([
    "反馈生成超时或失败，可重试",
    payload?.retryable === true ? "可重试：是" : null,
    ...codes.map((code) => `错误码：${code}`),
  ]);
}

function buildRetryDeltaItems(payload: PolishFeedbackPayload): string[] {
  const dimensionDeltaItems = Object.entries(payload.dimension_delta ?? {})
    .filter(([key]) => isUserVisibleFeedbackRecordKey(key))
    .map(([key, value]) => {
      const text = toOptionalText(value);
      return text ? `维度变化：${key} ${text}` : null;
    });
  return dedupeTextItems([
    typeof payload.score_delta === "number" ? `分数变化：${payload.score_delta > 0 ? "+" : ""}${payload.score_delta}` : null,
    payload.mastery_status ? `掌握状态：${payload.mastery_status}` : null,
    ...compactTextList(payload.improved_points).map((item) => `已改进：${item}`),
    ...compactTextList(payload.remaining_gaps).map((item) => `仍需补齐：${item}`),
    ...compactTextList(payload.repeated_loss_points).map((item) => `重复失分：${item}`),
    ...compactTextList(payload.regressed_points).map((item) => `退步点：${item}`),
    ...dimensionDeltaItems,
  ]);
}

function buildScoreResultItems(payload: PolishFeedbackPayload | undefined, fallbackScoreResultId: string | null): string[] {
  const score = payload?.score_result;
  if (!score) {
    return fallbackScoreResultId ? [`score_result_id：${fallbackScoreResultId}`] : ["暂无打分结果"];
  }
  return dedupeTextItems([
    typeof score.score_value === "number" ? `总分 ${score.score_value} / 100` : null,
    score.score_type ? `评分类型：${mapFeedbackCodeToDisplay(score.score_type)}` : null,
    score.confidence_level ? `置信度：${score.confidence_level}` : null,
    score.score_result_id ? `score_result_id：${score.score_result_id}` : fallbackScoreResultId ? `score_result_id：${fallbackScoreResultId}` : null,
    score.rubric_version ? `rubric_version：${score.rubric_version}` : null,
  ]);
}
