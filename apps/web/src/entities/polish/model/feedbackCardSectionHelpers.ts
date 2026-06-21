import {
  FEEDBACK_REFERENCE_SECTION_FALLBACK,
  type FeedbackCardSectionViewModel,
  type FeedbackSectionKey,
} from "./feedbackViewModelTypes";
import {
  dedupeTextItems,
  isText,
  isUserVisibleFeedbackRecordKey,
  mapFeedbackCodeToDisplay,
  toOptionalText,
  toRecord,
} from "./feedbackViewModelUtils";

export function buildReferenceAnswerItems(value: unknown): string[] {
  const record = toRecord(value);
  if (record === null) {
    return [FEEDBACK_REFERENCE_SECTION_FALLBACK];
  }
  const summary = toOptionalText(record.summary);
  const sectionsValue = Array.isArray(record.sections)
    ? record.sections
    : Array.isArray(record.reference_answer_sections)
      ? record.reference_answer_sections
      : [];
  const sectionItems = sectionsValue.flatMap(buildReferenceAnswerSectionItems);
  if (sectionItems.length > 0) {
    return summary === null ? sectionItems : [summary, ...sectionItems];
  }
  const outline = Array.isArray(record.outline) ? record.outline.map(toOptionalText).filter(isText) : [];
  const paragraphItems = dedupeTextItems([summary, ...outline]);
  return paragraphItems.length > 0 ? paragraphItems : [FEEDBACK_REFERENCE_SECTION_FALLBACK];
}

export function buildOptionalFeedbackSection(
  key: FeedbackSectionKey,
  title: string,
  items: readonly string[],
  defaultOpen: boolean,
  tone?: "default" | "warning",
): FeedbackCardSectionViewModel | null {
  return items.length > 0 ? { key, title, items, defaultOpen, tone } : null;
}

export function buildOptionalRecordListItems(values: unknown, fieldLabels: readonly (readonly [string, string])[]): string[] {
  if (!Array.isArray(values) || values.length === 0) {
    return [];
  }
  return dedupeTextItems(values.flatMap((value) => buildRecordItems(value, fieldLabels)));
}

export function normalizeLossPointDeductionValue(value: unknown): string {
  const numericValue = Number(toOptionalText(value));
  return Number.isFinite(numericValue) ? String(Math.trunc(Math.abs(numericValue))) : "0";
}

function buildReferenceAnswerSectionItems(value: unknown): string[] {
  const section = toRecord(value);
  if (section === null) {
    const text = toOptionalText(value);
    return text ? [text] : [];
  }
  const title = toOptionalText(section.title);
  const content = toOptionalText(section.content);
  if (title === null && content === null) {
    return [];
  }
  if (title === null) {
    return [content ?? FEEDBACK_REFERENCE_SECTION_FALLBACK];
  }
  return content === null ? [title] : [`${title}：${content}`];
}

function buildRecordItems(value: unknown, fieldLabels: readonly (readonly [string, string])[]): string[] {
  const record = toRecord(value);
  if (record === null) {
    const text = toOptionalText(value);
    return text ? [text] : [];
  }
  const preferredItems = fieldLabels
    .map(([field, label]) => {
      const text = mapFeedbackRecordText(field, toOptionalText(record[field]));
      return text ? `${label}：${text}` : null;
    })
    .filter(isText);
  if (preferredItems.length > 0) {
    return preferredItems;
  }
  return Object.entries(record)
    .filter(([key]) => isUserVisibleFeedbackRecordKey(key))
    .map(([key, item]) => {
      const text = mapFeedbackRecordText(key, toOptionalText(item));
      return text ? `${key}：${text}` : null;
    })
    .filter(isText)
    .slice(0, 6);
}

function mapFeedbackRecordText(fieldName: string, rawText: string | null): string | null {
  if (rawText === null) {
    return null;
  }
  return ["severity", "status", "score_type", "type", "action", "result_type"].includes(fieldName.toLowerCase())
    ? mapFeedbackCodeToDisplay(rawText)
    : rawText;
}
