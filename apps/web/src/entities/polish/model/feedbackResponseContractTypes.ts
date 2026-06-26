import type { PolishRecommendedAction } from "./types";

export interface PolishStep8ResponseMetadataRecord extends Record<string, unknown> {
  readonly contract_id?: string | null;
  readonly policy_signature?: string | null;
}

export interface PolishPolicySignedNextActionPayload extends PolishStep8ResponseMetadataRecord {
  readonly action_type?: PolishRecommendedAction | null;
  readonly requires_consumed_grant?: boolean | null;
  readonly grant_lifecycle_state?: string | null;
}

export interface PolishFollowUpIntentClassificationPayload extends PolishStep8ResponseMetadataRecord {
  readonly intent?: string | null;
}

export type PolishResponseCandidatePayload = Readonly<Record<string, unknown>>;

declare module "./types" {
  interface PolishFeedbackPayload {
    readonly policy_signed_next_action?: PolishPolicySignedNextActionPayload | null;
    readonly follow_up_intent_classification?: PolishFollowUpIntentClassificationPayload | null;
    readonly same_node_follow_up_contract?: PolishStep8ResponseMetadataRecord | null;
    readonly same_node_next_question_contract?: PolishStep8ResponseMetadataRecord | null;
    readonly next_question_response_contract?: PolishStep8ResponseMetadataRecord | null;
    readonly weakness_candidates?: readonly PolishResponseCandidatePayload[];
    readonly asset_candidates?: readonly PolishResponseCandidatePayload[];
    readonly oral_script_candidates?: readonly PolishResponseCandidatePayload[];
    readonly polished_answer_candidates?: readonly PolishResponseCandidatePayload[];
  }
}
