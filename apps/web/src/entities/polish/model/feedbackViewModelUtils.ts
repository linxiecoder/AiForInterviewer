import type { PolishFeedbackPayload, PolishRecommendedAction, PolishSessionAnswer } from "./types";
import {
  CODE_NOT_AVAILABLE_TEXT,
  FEEDBACK_CODE_DISPLAY_MAP,
  NEXT_RECOMMENDED_ACTION_LABELS,
  type NormalizedPolishFeedbackStatus,
} from "./feedbackViewModelTypes";

export function toNextRecommendedActionLabel(action: PolishRecommendedAction): string {
  return NEXT_RECOMMENDED_ACTION_LABELS[action] ?? action;
}

export function resolvePolishFeedbackStatus(status: string | null | undefined): NormalizedPolishFeedbackStatus {
  const normalizedStatus = status?.trim().toLowerCase();
  if (normalizedStatus === "pending" || normalizedStatus === "generated") {
    return normalizedStatus;
  }
  if (
    normalizedStatus === "failed" ||
    normalizedStatus === "generation_failed" ||
    normalizedStatus === "validation_failed" ||
    normalizedStatus === "timed_out" ||
    normalizedStatus === "cancelled" ||
    normalizedStatus === "source_unavailable" ||
    normalizedStatus?.includes("failed") === true ||
    normalizedStatus?.includes("timeout") === true ||
    normalizedStatus?.includes("cancelled") === true
  ) {
    return "failed";
  }
  return "pending";
}

export function getPolishFeedbackStatusLabel(answer: PolishSessionAnswer | null | undefined): string {
  return mapFeedbackCodeToDisplay(resolvePolishFeedbackStatus(answer?.feedback_payload?.status));
}

export function getPolishFeedbackPayloadText(answer: PolishSessionAnswer): string | null {
  return answer.feedback_text || answer.feedback_payload?.feedback_text || null;
}

export function getPolishFeedbackPayloadId(answer: PolishSessionAnswer | null | undefined): string | null {
  return answer?.feedback_id ?? answer?.feedback_payload?.feedback_id ?? null;
}

export function hasPolishFeedbackPayload(answer: PolishSessionAnswer | null | undefined): boolean {
  return answer?.feedback_payload !== undefined;
}

export function hasPolishGeneratedFeedback(answer: PolishSessionAnswer | null | undefined): boolean {
  const feedbackStatus = resolvePolishFeedbackStatus(answer?.feedback_payload?.status);
  return Boolean(answer?.feedback_id || answer?.feedback_created_at || feedbackStatus !== "pending");
}

export function getAnswerNextRecommendedActions(answer: PolishSessionAnswer): PolishRecommendedAction[] {
  const actions = answer.feedback_payload?.next_recommended_actions ?? [];
  return actions.filter((action, index) => actions.indexOf(action) === index);
}

export function getPolishFeedbackScoreValue(payload: PolishFeedbackPayload | undefined): number | null {
  const scoreRecord = toRecord(payload?.score_result);
  const rawScore = scoreRecord?.score_value ?? scoreRecord?.score ?? scoreRecord?.total_score;
  const score = typeof rawScore === "number" ? rawScore : Number(toOptionalText(rawScore));
  return Number.isFinite(score) ? Math.round(score) : null;
}

export function getPolishAnswerFeedbackScoreValue(answer: PolishSessionAnswer): number | null {
  return getPolishFeedbackScoreValue(answer.feedback_payload);
}

export function getPolishFeedbackGeneratedAt(answer: PolishSessionAnswer): string | null {
  return answer.feedback_created_at ?? toOptionalText(toRecord(answer.feedback_payload)?.generated_at);
}

export function mapFeedbackCodeToDisplay(code: string | null | undefined): string {
  const text = toOptionalText(code);
  if (text === null) {
    return CODE_NOT_AVAILABLE_TEXT;
  }
  return FEEDBACK_CODE_DISPLAY_MAP[text.trim().toLowerCase()] ?? text;
}

export function compactTextList(value: string | readonly string[] | null | undefined): string[] {
  if (typeof value === "string" || value === null || value === undefined) {
    return dedupeTextItems([value]);
  }
  return dedupeTextItems([...value]);
}

export function pickFirstRecordText(record: Readonly<Record<string, unknown>>, fieldNames: readonly string[]): string | null {
  for (const field of fieldNames) {
    const text = toOptionalText(record[field]);
    if (text !== null) {
      return text;
    }
  }
  return null;
}

export function sanitizeFeedbackDisplayText(value: string | null | undefined, fallback: string): string {
  const text = value?.trim();
  if (!text) {
    return fallback;
  }
  const normalized = text.toLowerCase();
  return text === "-" || text === "修正建议待补充" || normalized === "undefined" || normalized === "null" ? fallback : text;
}

export function toRecord(value: unknown): Readonly<Record<string, unknown>> | null {
  return isRecord(value) ? value : null;
}

export function toOptionalText(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed || null;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return null;
}

export function dedupeTextItems(values: readonly (string | null | undefined)[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const text = toOptionalText(value);
    if (!text || seen.has(text)) {
      continue;
    }
    seen.add(text);
    result.push(text);
  }
  return result;
}

export function isText(value: string | null): value is string {
  return value !== null;
}

export function isSection<T>(value: T | null): value is T {
  return value !== null;
}

export function isUserVisibleFeedbackRecordKey(key: string): boolean {
  const normalized = key.toLowerCase();
  return !["trace", "internal", "fake", "raw", "prompt", "completion", "provider", "candidate", "private", "secret", "hidden", "token", "api_key", "cookie"]
    .some((privateMarker) => normalized.includes(privateMarker));
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
