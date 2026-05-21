export type PolishSessionMode = "polish";
export type PolishTheme = "technical" | "communication" | "mixed";

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
  | "generate_next_question"
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

export interface PolishScoreResultPayload {
  score_result_id?: string;
  score_type?: "polish_answer" | string;
  score_value?: number;
  score_version?: string;
  rubric_version?: string;
  contract_id?: string;
  confidence_level?: "low" | "medium" | "high" | string;
}

export interface PolishLossPointPayload extends Record<string, unknown> {
  loss_point_id?: string;
  title?: string;
  deducted_points?: number;
  reason?: string;
  answer_excerpt?: string;
  related_answer_ref?: PolishFeedbackResourceRef | null;
}

export interface PolishReferenceAnswerPayload extends Record<string, unknown> {
  contract_id?: string;
  summary?: string;
  outline?: string[];
}

export interface PolishExplanationPayload extends Record<string, unknown> {
  title?: string;
  explanation?: string;
}

export interface PolishFeedbackPayload {
  contract_id?: string;
  contract_ids?: string[];
  status: "pending" | "generated" | string;
  feedback_id?: string | null;
  feedback_text: string;
  feedback_summary?: string | null;
  polish_theme?: PolishTheme | string | null;
  polish_theme_label?: string | null;
  explicit_weight?: number | null;
  implicit_weight?: number | null;
  weight_explanation?: string | null;
  interview_intent?: string | null;
  explicit_score?: number | null;
  implicit_score?: number | null;
  technical_gaps?: string[];
  communication_gaps?: string[];
  p7_reference_answer?: string | null;
  oral_script?: string | null;
  next_training_suggestions?: string[];
  score_result?: PolishScoreResultPayload | null;
  loss_points?: PolishLossPointPayload[];
  reference_answer?: PolishReferenceAnswerPayload | null;
  knowledge_points?: PolishExplanationPayload[];
  technical_principles?: PolishExplanationPayload[];
  next_recommended_actions: PolishRecommendedAction[];
  candidate_refs?: PolishFeedbackResourceRef[];
  validation_result_ref?: PolishFeedbackResourceRef | null;
  trace_refs?: Array<Record<string, unknown>>;
  low_confidence_flags?: PolishLowConfidenceFlag[];
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
  next_recommended_actions?: PolishRecommendedAction[];
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
  progress_node_ref?: string | null;
  evidence_refs?: string[];
  context_digest?: string | null;
  answers: PolishSessionAnswer[];
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
  status: "ready" | "insufficient_context" | string;
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

export interface CreatePolishQuestionTaskRequest {
  progress_node_ref?: string | null;
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
  progress_tree_status: "ready" | "insufficient_context" | string;
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
  contract_shaped_fake?: Record<string, unknown> | PolishFeedbackPayload | null;
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
  next_recommended_actions?: PolishRecommendedAction[];
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
  next_recommended_actions?: PolishRecommendedAction[];
  feedback_text?: string;
  feedback_id?: string | null;
}
