export interface ApiResourceRef {
  resource_type: string;
  resource_id: string;
}

export interface ApiSuccessEnvelope<TData = unknown> {
  request_id: string;
  trace_id: string;
  status: string;
  resource_type: string;
  resource_ref?: ApiResourceRef | null;
  data: TData | null;
  meta?: Record<string, unknown> | null;
  candidate_refs?: ApiResourceRef[];
  suggestion_refs?: ApiResourceRef[];
  confirmation_required?: boolean | null;
  ai_task_id?: string | null;
  validation_result_ref?: ApiResourceRef | null;
  low_confidence_flags?: unknown[];
  source_availability?: string | null;
  evidence_refs?: unknown[];
  trace_refs?: unknown[];
  score_version?: string | null;
  rubric_version?: string | null;
  confidence_level?: string | null;
  pass_tendency_level?: string | null;
  risk_level?: string | null;
  next_actions?: string[];
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
  retryable: boolean;
  user_action?: string | null;
  audit_event_ref?: ApiResourceRef | null;
}

export interface ApiErrorEnvelope {
  request_id: string;
  trace_id: string;
  error: ApiErrorPayload;
}

export const DEFAULT_UNAUTHENTICATED_ERROR_CODE = "unauthenticated";
export const DEFAULT_INTERNAL_ERROR_CODE = "internal_error";
