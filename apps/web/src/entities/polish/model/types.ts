export type PolishSessionMode = "polish";
export type PolishTheme = "technical" | "communication" | "mixed";
export type PolishProgressTreeStatus =
  | "pending"
  | "generating"
  | "ready"
  | "failed"
  | "refresh_failed"
  | "insufficient_context"
  | string;

export type PolishSessionContinuityStatus = "ready" | "partial" | "stale" | "blocked" | "unknown";
export type PolishContextHygieneStatus = "clean" | "partial" | "fallback" | "blocked" | "unknown";

export interface PolishSessionSummary {
  id: string;
  session_id: string;
  title: string;
  mode: PolishSessionMode;
  status: string;
  resume_job_binding_id: string;
  resume_id: string;
  resume_version_id: string;
  job_id: string;
  job_version_id: string;
  job_title: string;
  job_company: string;
  resume_title: string;
  binding_label: string;
  polish_theme?: PolishTheme | null;
  polish_theme_label?: string | null;
  explicit_weight?: number | null;
  implicit_weight?: number | null;
  topic_id?: string | null;
  subtopic_id?: string | null;
  custom_topic_text_summary?: string | null;
  report_id?: string | null;
  report_status?: string | null;
  report_generated_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type PolishRecommendedAction =
  | "answer_again"
  | "continue_same_question"
  | "generate_reference_answer"
  | "explain_knowledge_point"
  | "expand_technical_principle"
  | "generate_next_round_suggestion"
  | "provide_more_answer_detail"
  | string;

export interface PolishResourceRef {
  resource_type: string;
  resource_id: string;
}

export interface PolishLowConfidenceFlag {
  flag_id?: string;
  reason?: string;
  impact_scope?: string;
  recommended_action?: PolishRecommendedAction;
}

export interface PolishFeedbackResourceRef {
  resource_type: string;
  resource_id: string;
}

export type PolishCandidateType =
  | "weakness_candidate"
  | "asset_candidate"
  | "oral_script_candidate"
  | "polished_answer_candidate"
  | string;

export type PolishCandidateStatus =
  | "candidate"
  | "confirmed"
  | "dismissed"
  | "merged"
  | "archived"
  | string;

export interface PolishCandidate {
  candidate_id: string;
  owner_id?: string;
  candidate_type: PolishCandidateType;
  status: PolishCandidateStatus;
  source_type?: string | null;
  source_refs?: Array<Record<string, unknown>>;
  evidence_refs?: Array<Record<string, unknown>>;
  trace_refs?: Array<Record<string, unknown>>;
  session_id?: string | null;
  question_id?: string | null;
  answer_id?: string | null;
  feedback_id?: string | null;
  title?: string | null;
  summary?: string | null;
  evidence_excerpt?: string | null;
  reason?: string | null;
  confidence_level?: "low" | "medium" | "high" | string | null;
  merge_key?: string | null;
  merge_target_candidate_id?: string | null;
  target_formal_ref?: PolishFeedbackResourceRef | Record<string, unknown> | null;
  candidate_payload?: Record<string, unknown> | null;
  user_confirmation_required?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  dismissed_at?: string | null;
  confirmed_at?: string | null;
  archived_at?: string | null;
}

export interface PolishCandidateActionResult {
  action: string;
  candidate: PolishCandidate;
  formal_ref?: PolishFeedbackResourceRef | Record<string, unknown> | null;
  asset_version_ref?: PolishFeedbackResourceRef | Record<string, unknown> | null;
}

export interface PolishScoreResultPayload {
  score_result_id?: string;
  score_type?: "polish_answer" | string;
  score_value?: number;
  score_version?: string;
  rubric_version?: string;
  confidence_level?: "low" | "medium" | "high" | string;
}

export interface PolishFeedbackAnswerSummary {
  coverage?: string | null;
  main_gaps?: string[];
}

export interface PolishLossPointPayload extends Record<string, unknown> {
  loss_point_id?: string;
  title?: string;
  severity?: string;
  deduction?: number;
  deducted_points?: number;
  reason?: string;
  answer_excerpt?: string;
  related_dimension?: string;
  related_answer_ref?: PolishFeedbackResourceRef | null;
}

export interface PolishReferenceAnswerSection extends Record<string, unknown> {
  section_id?: string;
  title?: string;
  content?: string;
  addresses_loss_point_ids?: string[];
}

export interface PolishReferenceAnswerPayload extends Record<string, unknown> {
  summary?: string;
  outline?: string[];
  sections?: PolishReferenceAnswerSection[];
}

export interface PolishGeneratedReferenceAnswer extends PolishReferenceAnswerPayload {}

export interface PolishStructuredFeedbackRecordPayload extends Record<string, unknown> {}

export interface PolishProjectAssetConflict extends Record<string, unknown> {
  title?: string | null;
  field?: string | null;
  current_value?: string | null;
  proposed_value?: string | null;
  reason?: string | null;
}

export interface PolishProjectAssetConsistencyCheck extends Record<string, unknown> {
  status?: "consistent" | "conflict" | "ambiguous" | string;
  matched_project_name?: string | null;
  conflicts?: PolishProjectAssetConflict[];
  clarification_questions?: string[];
}

export interface PolishFeedbackPayload {
  contract_ids?: string[];
  status?:
    | "pending"
    | "generated"
    | "failed"
    | "generation_failed"
    | "validation_failed"
    | "timed_out"
    | "cancelled"
    | "source_unavailable"
    | string;
  feedback_id?: string | null;
  feedback_text?: string | null;
  answer_summary?: PolishFeedbackAnswerSummary | null;
  polish_theme?: PolishTheme | string | null;
  polish_theme_label?: string | null;
  explicit_weight?: number | null;
  implicit_weight?: number | null;
  weight_explanation?: string | null;
  interview_intent?: string | null;
  technical_gaps?: string[];
  communication_gaps?: string[];
  answer_diagnosis?: Record<string, unknown> | null;
  positive_evidence_points?: PolishStructuredFeedbackRecordPayload[];
  missing_answer_dimensions?: PolishStructuredFeedbackRecordPayload[];
  p7_reference_answer?: string | null;
  reference_answer_requirements?: PolishStructuredFeedbackRecordPayload[];
  oral_script?: string | null;
  oral_script_requirements?: PolishStructuredFeedbackRecordPayload[];
  next_polish_suggestions?: string[];
  next_training_suggestions?: string[];
  mastery_status?: string | null;
  score_delta?: number | null;
  dimension_delta?: Record<string, unknown> | null;
  improved_points?: string[];
  remaining_gaps?: string[];
  repeated_loss_points?: string[];
  regressed_points?: string[];
  next_retry_focus?: PolishStructuredFeedbackRecordPayload[];
  score_result?: PolishScoreResultPayload | null;
  loss_points?: PolishLossPointPayload[];
  reference_answer?: PolishGeneratedReferenceAnswer | null;
  asset_consistency_check?: PolishProjectAssetConsistencyCheck | null;
  next_recommended_actions?: PolishRecommendedAction[];
  validation_result_ref?: PolishFeedbackResourceRef | null;
  trace_refs?: Array<Record<string, unknown>>;
  low_confidence_flags?: PolishLowConfidenceFlag[];
  retryable?: boolean;
  user_visible_status?: string | null;
  validation_errors?: string[];
  feedback_metadata?: PolishContextHygieneMetadata | null;
  error?: {
    code?: string | null;
    message?: string | null;
    metadata?: Record<string, unknown> | null;
  } | null;
}

export interface PolishContextHygieneMetadata extends Record<string, unknown> {
  context_hygiene_status?: PolishContextHygieneStatus;
  safe_context_metadata?: Record<string, unknown>;
  fallback_reason?: string | null;
  validation_signals?: Record<string, unknown>;
}

export interface PolishSessionAnswer {
  answer_id: string;
  answer_round: number;
  answer_text: string;
  answer_created_at: string;
  feedback_text: string;
  feedback_id: string | null;
  score_result_id: string | null;
  feedback_created_at: string | null;
  feedback_payload?: PolishFeedbackPayload;
  low_confidence_flags?: PolishLowConfidenceFlag[];
  trace_refs?: Array<Record<string, unknown>>;
}

export type PolishQuestionSourceType =
  | "job_requirement"
  | "resume_evidence"
  | "progress_node"
  | "missing_point"
  | "history_feedback";

export type PolishQuestionSourceAvailability = "available" | "partial" | "unavailable";

export interface PolishQuestionSource {
  index: number;
  source_type: PolishQuestionSourceType;
  title: string;
  excerpt: string;
  ref_id: string | null;
  availability: PolishQuestionSourceAvailability;
}

export interface PolishSessionTurn {
  question_id: string;
  question_text: string;
  question_sources: PolishQuestionSource[];
  question_created_at: string;
  question_metadata?: PolishContextHygieneMetadata | null;
  progress_node_ref?: string | null;
  evidence_refs?: string[];
  context_digest?: string | null;
  answers: PolishSessionAnswer[];
}

export interface PolishSessionContinuitySummary extends Record<string, unknown> {
  restored_turn_count: number;
  has_progress_plan: boolean;
  has_progress_state: boolean;
  progress_tree_status: PolishProgressTreeStatus;
  fallback_reason?: string | null;
  warnings?: string[];
  computed_at?: string;
}

export interface PolishSessionRestoredRefs extends Record<string, unknown> {
  current_question_id?: string | null;
  current_progress_node_ref?: string | null;
  evidence_refs?: Array<PolishResourceRef | string>;
  context_digest?: string | null;
}

export interface PolishProgressTreeNode {
  progress_node_ref: string;
  title: string;
  expected_capability: string;
  related_job_requirements: string[];
  related_resume_evidence: string[];
  missing_points: string[];
  evidence_chunk_ids?: string[];
  children: PolishProgressTreeNode[];
}

export interface PolishProgressTreePlan {
  status: PolishProgressTreeStatus;
  context_digest: string;
  nodes: PolishProgressTreeNode[];
  failure_reason?: string | null;
}

export interface PolishProgressTreeNodeState {
  progress_node_ref: string;
  status: "completed" | "in_progress" | "pending" | string;
  completed_questions_count: number;
  latest_feedback_summary?: string | null;
}

export interface PolishCompletedFocusRef {
  question_id?: string | null;
  progress_node_ref?: string | null;
  focus_key?: string | null;
  focus_dimension?: string | null;
  template_signature?: string | null;
  blueprint_signature?: string | null;
  completed_at?: string | null;
  source?: string | null;
}

export interface PolishCurrentPriority {
  progress_node_ref: string;
  title: string;
  expected_capability: string;
}

export interface PolishProgressTreeState {
  status: "ready" | "insufficient_context" | string;
  node_states: PolishProgressTreeNodeState[];
  current_priority?: PolishCurrentPriority | null;
  updated_from_turns_count: number;
  progress: {
    progress_percent: number;
  };
  completed_focus_refs?: PolishCompletedFocusRef[];
  session_ended_at?: string | null;
  summary?: string | null;
  failure_reason?: string | null;
}

export interface PolishSubtopic {
  subtopic_id: string;
  topic_id: string;
  title: string;
  description?: string | null;
  disabled_reason?: string | null;
}

export interface PolishTopic {
  topic_id: string;
  title: string;
  description?: string | null;
  requires_job_binding: boolean;
  disabled_reason?: string | null;
  subtopics: PolishSubtopic[];
}

export interface CreatePolishSessionRequest {
  resume_job_binding_id: string;
  polish_theme?: PolishTheme | null;
  topic_id?: string | null;
  subtopic_id?: string | null;
  custom_topic_text?: string | null;
}

export interface CreatePolishFeedbackNextQuestionIntentRequest {
  exclude_question_refs?: string[];
}

export interface CreatePolishQuestionTaskRequest {
  exclude_question_refs?: string[];
}

export interface CreatePolishAnswerRequest {
  question_id: string;
  answer_text: string;
  base_question_version_ref?: {
    resource_type: string;
    resource_id: string;
    version_id: string;
  } | null;
}

export interface CreatePolishFeedbackTaskRequest {
  answer_id: string;
}

export interface PolishSessionDetail {
  session_id: string;
  mode: PolishSessionMode;
  session_status: string;
  resume_job_binding_id: string;
  resume_id: string;
  resume_version_id: string;
  job_id: string;
  job_version_id: string;
  job_title: string;
  job_company: string;
  resume_title: string;
  binding_label: string;
  polish_theme?: PolishTheme | null;
  polish_theme_label?: string | null;
  explicit_weight?: number | null;
  implicit_weight?: number | null;
  turns: PolishSessionTurn[];
  current_question_ref?: PolishResourceRef | null;
  active_question_ref?: PolishResourceRef | null;
  progress_position_ref?: PolishResourceRef | null;
  current_node_ref?: PolishResourceRef | null;
  current_node_progress_node_ref?: string | null;
  active_question_refs?: PolishResourceRef[];
  active_question_progress_node_ref?: string | null;
  active_question_evidence_refs?: Array<PolishResourceRef | string>;
  active_question_context_digest?: string | null;
  continuity_status?: PolishSessionContinuityStatus;
  continuity_summary?: PolishSessionContinuitySummary;
  restored_refs?: PolishSessionRestoredRefs;
  progress_tree_status: PolishProgressTreeStatus;
  progress_percent: number;
  progress_tree_plan: PolishProgressTreePlan;
  progress_tree_state: PolishProgressTreeState;
  topic_ref?: {
    topic_id: string;
    title?: string | null;
  } | null;
  subtopic_ref?: {
    subtopic_id: string;
    topic_id: string;
    title?: string | null;
  } | null;
  custom_topic_text_summary?: string | null;
  report_id?: string | null;
  report_status?: string | null;
  report_generated_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolishTraceRef {
  trace_ref_id: string;
  trace_type: string;
  created_at: string;
}

export interface PolishTaskStatus {
  ai_task_id: string;
  task_type: string;
  status: "queued" | "running" | "succeeded" | "failed" | string;
  contract_ids: string[];
  retryable: boolean;
  result_ref?: PolishTraceRef | null;
  user_visible_status: string;
  score_type?: "polish_answer" | string | null;
  candidate_refs: Array<{ resource_type: string; resource_id: string }>;
  suggestion_refs: Array<{ resource_type: string; resource_id: string }>;
  feedback_id?: string | null;
  feedback_status?: string;
  session_id?: string;
  question_id?: string;
  answer_id?: string;
  answer_round?: number;
  feedback_text?: string;
  feedback_created_at?: string | null;
  score_result_id?: string | null;
  feedback_payload?: PolishFeedbackPayload;
  provider_payload?: null;
}

export interface PolishAiTaskResult {
  ai_task_id: string;
  status: "queued" | "running" | "succeeded" | "partial" | "low_confidence" | "validation_failed" | "source_unavailable" | "generation_failed" | "timed_out" | "cancelled" | string;
  result_ref?: PolishTraceRef | null;
  candidate_refs: Array<{ resource_type: string; resource_id: string }>;
  suggestion_refs: Array<{ resource_type: string; resource_id: string }>;
  validation_result_ref?: { resource_type: string; resource_id: string } | null;
  validation_errors?: string[] | null;
  result_payload?: PolishFeedbackPayload | null;
  provider_payload: null;
}

export interface PolishAnswer {
  answer_id: string;
  session_id: string;
  question_id: string;
  answer_round: number;
  answer_text: string;
  status?: string;
  created_at: string;
  updated_at: string;
  feedback_payload?: PolishFeedbackPayload;
  feedback_text?: string;
  feedback_id?: string | null;
}
