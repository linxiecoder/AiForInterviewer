export type PolishSessionMode = "polish";

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
  topic_id?: string | null;
  subtopic_id?: string | null;
  custom_topic_text_summary?: string | null;
  created_at: string;
  updated_at: string;
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
}

export interface PolishSessionTurn {
  question_id: string;
  question_text: string;
  question_created_at: string;
  answers: PolishSessionAnswer[];
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
  turns: PolishSessionTurn[];
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
}

export interface PolishAnswer {
  answer_id: string;
  session_id: string;
  question_id: string;
  answer_round: number;
  answer_text: string;
  created_at: string;
  updated_at: string;
}
