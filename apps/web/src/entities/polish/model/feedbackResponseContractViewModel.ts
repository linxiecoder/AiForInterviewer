import type { FeedbackCardViewModel, NormalizedPolishFeedbackStatus } from "./feedbackViewModelTypes";
import type {} from "./feedbackResponseContractTypes";
import {
  compactTextList,
  dedupeTextItems,
  isText,
  isUserVisibleFeedbackRecordKey,
  mapFeedbackCodeToDisplay,
  toNextRecommendedActionLabel,
  toOptionalText,
  toRecord,
} from "./feedbackViewModelUtils";
import type { PolishFeedbackPayload, PolishRecommendedAction, PolishSessionAnswer } from "./types";

type FeedbackResponseContractItemKey =
  | "follow_up_intent_classification"
  | "same_node_follow_up_contract"
  | "same_node_next_question_contract"
  | "next_question_response_contract";

type FieldLabel = readonly [field: string, label: string];

interface ResponseContractDefinition {
  readonly key: FeedbackResponseContractItemKey;
  readonly title: string;
  readonly fieldLabels: readonly FieldLabel[];
}

export type FeedbackPolicySignedNextActionViewModel = {
  readonly action: PolishRecommendedAction | null;
  readonly label: string | null;
  readonly policySignature: string | null;
  readonly isTrusted: boolean;
};

export type FeedbackProgressProjectionViewModel = {
  readonly masteryStatus: string | null;
  readonly scoreDelta: number | null;
  readonly remainingGapCount: number;
};

export type FeedbackResponseContractItemViewModel = {
  readonly key: FeedbackResponseContractItemKey;
  readonly title: string;
  readonly items: readonly string[];
};

export type FeedbackResponseContractViewModel = {
  readonly status: NormalizedPolishFeedbackStatus;
  readonly hasTerminalFeedback: boolean;
  readonly shouldKeepPendingCopy: boolean;
  readonly card: FeedbackCardViewModel;
  readonly policySignedNextAction: FeedbackPolicySignedNextActionViewModel;
  readonly progress: FeedbackProgressProjectionViewModel;
  readonly responseContractItems: readonly FeedbackResponseContractItemViewModel[];
};

const RESPONSE_CONTRACT_DEFINITIONS = [
  {
    key: "follow_up_intent_classification",
    title: "追问意图",
    fieldLabels: [
      ["intent", "意图"],
      ["confidence", "置信度"],
    ],
  },
  {
    key: "same_node_follow_up_contract",
    title: "同节点追问契约",
    fieldLabels: [
      ["contract_id", "contract_id"],
      ["policy_signature", "policy_signature"],
    ],
  },
  {
    key: "same_node_next_question_contract",
    title: "同节点下一题契约",
    fieldLabels: [
      ["contract_id", "contract_id"],
      ["policy_signature", "policy_signature"],
    ],
  },
  {
    key: "next_question_response_contract",
    title: "下一题响应契约",
    fieldLabels: [
      ["contract_id", "contract_id"],
      ["policy_signature", "policy_signature"],
    ],
  },
] satisfies readonly ResponseContractDefinition[];

export function buildFeedbackResponseContractProjection(
  answer: PolishSessionAnswer,
  card: FeedbackCardViewModel,
): FeedbackResponseContractViewModel {
  const payload = answer.feedback_payload;
  return {
    status: card.status,
    hasTerminalFeedback: card.status !== "pending",
    shouldKeepPendingCopy: card.status === "pending",
    card,
    policySignedNextAction: buildPolicySignedNextActionViewModel(payload),
    progress: buildProgressProjectionViewModel(payload),
    responseContractItems: buildResponseContractItems(payload),
  };
}

function buildPolicySignedNextActionViewModel(
  payload: PolishFeedbackPayload | undefined,
): FeedbackPolicySignedNextActionViewModel {
  const policy = toRecord(payload?.policy_signed_next_action);
  const action = toOptionalText(policy?.action_type);
  const policySignature = toOptionalText(policy?.policy_signature);
  const isTrusted = action !== null && policySignature !== null;
  return {
    action: isTrusted ? action : null,
    label: isTrusted ? toNextRecommendedActionLabel(action) : null,
    policySignature,
    isTrusted,
  };
}

function buildProgressProjectionViewModel(
  payload: PolishFeedbackPayload | undefined,
): FeedbackProgressProjectionViewModel {
  const scoreDelta = typeof payload?.score_delta === "number" ? payload.score_delta : null;
  return {
    masteryStatus: toOptionalText(payload?.mastery_status),
    scoreDelta,
    remainingGapCount: compactTextList(payload?.remaining_gaps).length,
  };
}

function buildResponseContractItems(
  payload: PolishFeedbackPayload | undefined,
): FeedbackResponseContractItemViewModel[] {
  return RESPONSE_CONTRACT_DEFINITIONS
    .map((definition) => buildResponseContractItem(definition, toRecord(payload?.[definition.key])))
    .filter(isResponseContractItem);
}

function buildResponseContractItem(
  definition: ResponseContractDefinition,
  record: Readonly<Record<string, unknown>> | null,
): FeedbackResponseContractItemViewModel | null {
  if (record === null) {
    return null;
  }
  const items = buildResponseContractRecordItems(record, definition.fieldLabels);
  return items.length === 0 ? null : {
    key: definition.key,
    title: definition.title,
    items,
  };
}

function buildResponseContractRecordItems(
  record: Readonly<Record<string, unknown>>,
  fieldLabels: readonly FieldLabel[],
): string[] {
  const preferredItems = fieldLabels
    .map(([field, label]) => {
      const text = mapContractRecordText(field, toOptionalText(record[field]));
      return text === null ? null : `${label}：${text}`;
    })
    .filter(isText);
  if (preferredItems.length > 0) {
    return preferredItems;
  }
  return dedupeTextItems(Object.entries(record)
    .filter(([key]) => isUserVisibleFeedbackRecordKey(key))
    .map(([key, value]) => {
      const text = mapContractRecordText(key, toOptionalText(value));
      return text === null ? null : `${key}：${text}`;
    }));
}

function mapContractRecordText(fieldName: string, rawText: string | null): string | null {
  if (rawText === null) {
    return null;
  }
  return ["action_type", "intent", "status", "type"].includes(fieldName.toLowerCase())
    ? mapFeedbackCodeToDisplay(rawText)
    : rawText;
}

function isResponseContractItem(
  value: FeedbackResponseContractItemViewModel | null,
): value is FeedbackResponseContractItemViewModel {
  return value !== null;
}
